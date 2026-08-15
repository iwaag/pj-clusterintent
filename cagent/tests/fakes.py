"""Test doubles for the identity seam and the agent backend.

`FakeRunner` has `AgentRunner`'s call surface, so the request state machine
and worker orchestration can be exercised without a model. It is a much
smaller fake than the session-API one it replaces — there is no session API to
imitate, no message count to grow, and no `finish == "tool-calls"` step
distinction to get right. One `run()` call, one `TurnResult`.
"""

from __future__ import annotations

import itertools
import threading
import uuid

from cagent_api.agent_runner import TurnResult
from cagent_api.auth import AuthError
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


class FakeRunner:
    """An `AgentRunner` whose turns are released by the test.

    `run()` blocks on `self.release` until the test lets the turn finish, the
    way a real run blocks while the model works. That is what lets a test see
    the `running` state and cancel mid-turn.
    """

    def __init__(self, backend: dict | None = None) -> None:
        self._session_ids = itertools.count(1)
        self.release = threading.Event()
        self.release.set()
        self.tasks: list[str] = []
        self.stops: list[object] = []
        self.result = TurnResult("hi there", "completed", None, None, None)
        self.backend = backend or {
            "harness": "agcode", "provider": "ollama",
            "model": "ollama/test-model", "role": "node", "profile": "local",
        }

    def new_session_id(self) -> str:
        return f"ses_fake{next(self._session_ids)}"

    def identity(self) -> dict:
        return dict(self.backend)

    def run(self, task, *, stop=None, transcript_path=None) -> TurnResult:
        self.tasks.append(task)
        self.stops.append(stop)
        # A real run checks `stop` between turns; this one checks it while it
        # waits, so a cancel lands the same way.
        while not self.release.wait(timeout=0.01):
            if stop is not None and stop():
                return TurnResult("", "cancelled", None, None, self.identity())
        if stop is not None and stop():
            return TurnResult("", "cancelled", None, None, self.identity())
        return TurnResult(
            self.result.text, self.result.state, self.result.error,
            self.result.cost_usd, self.identity(),
        )

    # --- test helpers, not part of the real runner's interface ---

    def hold(self) -> None:
        self.release.clear()

    def finish(self, text: str = "hi there") -> None:
        self.result = TurnResult(text, "completed", None, None, None)
        self.release.set()

    def fail(self, message: str = "SomeModelError") -> None:
        self.result = TurnResult("", "failed", {"code": "agent_error", "message": message}, None, None)
        self.release.set()

    def charge(self, cost: float, text: str = "hi") -> None:
        """A claude_code-shaped turn: it reports what it cost."""
        self.result = TurnResult(text, "completed", None, cost, None)
        self.release.set()


def session_id() -> str:
    return f"ses_{uuid.uuid4().hex}"
