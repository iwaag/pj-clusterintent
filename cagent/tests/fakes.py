"""A fake OpenCode client with the same call surface as OpenCodeClient.

Used so the request state machine and worker orchestration can be tested
without a real `opencode serve` process. README_DEV requires this to
verifiably replace the real HTTP boundary, not just assert on our own
assumptions of its behavior — see p1/opencode_api_notes.md for what the
real behavior being faked here was actually observed to be.
"""

from __future__ import annotations

import itertools
import threading

from cagent_api.auth import AuthError
from cagent_api.opencode_client import AssistantMessage, OpenCodeError
from cagent_api.store import Identity


class FakeAuthenticator:
    """Test-only stand-in for `auth.CertAuthenticator` (p2/contract.md's
    real identity source is a verified client cert's SAN, which unit tests
    have no reason to set up a real TLS handshake for — see
    p2/plan.md Step 4: 'keep the seam such that unit tests don't need real
    TLS'). Reads a test-only header instead of `getpeercert()`, entirely
    outside the real contract — no production code reads this header."""

    HEADER = "X-Test-Node-Uuid"

    def __call__(self, handler) -> Identity:
        node_uuid = handler.headers.get(self.HEADER)
        if not node_uuid:
            raise AuthError(401, "unauthorized", f"missing test header {self.HEADER}")
        return Identity(identity_class="node", uuid=node_uuid, cert_serial=f"test-serial-{node_uuid}")


class FakeHumanAuthenticator:
    """Test-only stand-in for `auth.TokenAuthenticator`: reads a test-only
    header instead of the real `Authorization: Bearer` header, so server
    tests can exercise the human read-all/continue-own rules without a real
    token comparison."""

    HEADER = "X-Test-Human"

    def __call__(self, handler) -> Identity:
        if not handler.headers.get(self.HEADER):
            raise AuthError(401, "unauthorized", f"missing test header {self.HEADER}")
        return Identity(identity_class="human", name="operator")


class FakeOpenCodeClient:
    def __init__(self) -> None:
        self._session_ids = itertools.count(1)
        self.lock = threading.Lock()
        # session_id -> list of "turns", each turn is a dict describing what
        # count_assistant_messages/latest_assistant_message should report.
        self._sessions: dict[str, list[dict]] = {}
        self.prompt_calls: list[tuple[str, str]] = []
        self.abort_calls: list[str] = []
        self.raise_on_prompt = False
        self.raise_on_poll = False
        # session_id -> cumulative USD, mirroring OpenCode's `GET /session/{id}`.cost.
        self.costs: dict[str, float] = {}

    def create_session(self, title: str) -> str:
        session_id = f"ses_fake{next(self._session_ids)}"
        self._sessions[session_id] = []
        self.costs[session_id] = 0.0
        return session_id

    def session_cost(self, session_id: str) -> float | None:
        with self.lock:
            return self.costs.get(session_id)

    def prompt_async(self, session_id: str, text: str) -> None:
        self.prompt_calls.append((session_id, text))
        if self.raise_on_prompt:
            raise OpenCodeError("simulated prompt_async failure")
        with self.lock:
            self._sessions[session_id].append(
                {"completed": False, "text": "", "error_name": None, "is_final_step": False}
            )

    def count_assistant_messages(self, session_id: str) -> int:
        if self.raise_on_poll:
            raise OpenCodeError("simulated poll failure")
        with self.lock:
            return len(self._sessions.get(session_id, []))

    def latest_assistant_message(self, session_id: str):
        with self.lock:
            turns = self._sessions.get(session_id, [])
            if not turns:
                return None
            t = turns[-1]
            return AssistantMessage(
                completed=t["completed"],
                text=t["text"],
                error_name=t["error_name"],
                is_final_step=t["is_final_step"],
            )

    def abort(self, session_id: str) -> bool:
        self.abort_calls.append(session_id)
        with self.lock:
            turns = self._sessions.get(session_id, [])
            if turns and not turns[-1]["completed"]:
                turns[-1] = {
                    "completed": True, "text": "", "error_name": "MessageAbortedError", "is_final_step": True,
                }
        return True

    # --- test helpers, not part of the real client's interface ---

    def push_intermediate_step(self, session_id: str) -> None:
        """Simulate a completed tool-calling step that is NOT the turn's end
        (OpenCode's `finish: "tool-calls"`) — appends a new assistant
        message so `count_assistant_messages` increases, same as a real
        multi-step turn."""
        with self.lock:
            self._sessions[session_id].append(
                {"completed": True, "text": "", "error_name": None, "is_final_step": False}
            )

    def complete_latest_turn(self, session_id: str, text: str = "ok") -> None:
        """Append (not overwrite) the turn's final assistant message — a real
        multi-step turn is a sequence of distinct messages; the last one is
        the only one with `finish` != "tool-calls"."""
        with self.lock:
            self._sessions[session_id].append(
                {"completed": True, "text": text, "error_name": None, "is_final_step": True}
            )

    def fail_latest_turn(self, session_id: str, error_name: str = "SomeError") -> None:
        with self.lock:
            self._sessions[session_id].append(
                {"completed": True, "text": "", "error_name": error_name, "is_final_step": True}
            )
