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

from cagent_api.opencode_client import AssistantMessage, OpenCodeError


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

    def create_session(self, title: str) -> str:
        session_id = f"ses_fake{next(self._session_ids)}"
        self._sessions[session_id] = []
        return session_id

    def prompt_async(self, session_id: str, text: str) -> None:
        self.prompt_calls.append((session_id, text))
        if self.raise_on_prompt:
            raise OpenCodeError("simulated prompt_async failure")
        with self.lock:
            self._sessions[session_id].append({"completed": False, "text": "", "error_name": None})

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
            return AssistantMessage(completed=t["completed"], text=t["text"], error_name=t["error_name"])

    def abort(self, session_id: str) -> bool:
        self.abort_calls.append(session_id)
        with self.lock:
            turns = self._sessions.get(session_id, [])
            if turns and not turns[-1]["completed"]:
                turns[-1] = {"completed": True, "text": "", "error_name": "MessageAbortedError"}
        return True

    # --- test helpers, not part of the real client's interface ---

    def complete_latest_turn(self, session_id: str, text: str = "ok") -> None:
        with self.lock:
            self._sessions[session_id][-1] = {"completed": True, "text": text, "error_name": None}

    def fail_latest_turn(self, session_id: str, error_name: str = "SomeError") -> None:
        with self.lock:
            self._sessions[session_id][-1] = {"completed": True, "text": "", "error_name": error_name}
