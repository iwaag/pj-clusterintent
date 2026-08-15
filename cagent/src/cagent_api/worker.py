"""Background worker: runs one turn to completion through an AgentRunner.

Serialization choice (recorded per p1/contract.md, which left this to the
implementation): **global** serialization — a single worker thread drains
one queue for every session, not one queue per session. The plan
(p1/plan.md Step 3) explicitly allows this as "acceptable and simpler for
now (all sessions share one working directory)"; it also trivially
satisfies the contract's weaker per-session serialization requirement.

The turn is synchronous now. The previous harness's session API forced a
poll loop — a message count, a `completed` flag, and a `finish == "tool-calls"` check to
tell an intermediate step from the turn's end. `AgentRunner.run()` returns
when the run is over, so all of that is gone. Cancellation and the timeout
are handed to the runner instead of enforced by this loop: agcode checks the
`stop` callable between turns and ends itself on `deadline_s`.
"""

from __future__ import annotations

import logging
import os
import queue
import threading

from .agent_runner import AgentRunner, compose_task
from .store import Store

logger = logging.getLogger("cagent_api.worker")

# Bounds how long one turn can wedge the single global queue. Multi-command
# compositions (e.g. a state bundle) can legitimately take minutes, so the
# bound is configurable. It reaches the model as agcode's `deadline_s`, which
# ends the run from inside rather than abandoning a subprocess.
TURN_TIMEOUT_SECONDS = float(os.environ.get("CAGENT_TURN_TIMEOUT_SECONDS", "300"))


class Worker:
    def __init__(self, store: Store, runner: AgentRunner) -> None:
        self._store = store
        self._runner = runner
        self._queue: queue.Queue[str] = queue.Queue()
        self._cancel_flags: set[str] = set()
        self._cancel_lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def enqueue(self, request_id: str) -> None:
        self._queue.put(request_id)

    def request_cancel(self, request_id: str) -> None:
        with self._cancel_lock:
            self._cancel_flags.add(request_id)

    def _is_cancel_requested(self, request_id: str) -> bool:
        with self._cancel_lock:
            return request_id in self._cancel_flags

    def _clear_cancel(self, request_id: str) -> None:
        with self._cancel_lock:
            self._cancel_flags.discard(request_id)

    def _run(self) -> None:
        while True:
            request_id = self._queue.get()
            try:
                self._process(request_id)
            except Exception:
                logger.exception("worker: unhandled error processing %s", request_id)
                self._store.update_request(
                    request_id,
                    state="failed",
                    error={"code": "internal_error", "message": "worker crashed processing this request"},
                )
            finally:
                self._clear_cancel(request_id)

    def _history(self, request_id: str, session_id: str) -> list[tuple[str, str | None]]:
        """Every earlier turn of this session, oldest first.

        agcode is stateless; the store is the memory. Only turns that actually
        answered are replayed — a failed or cancelled one contributes nothing
        the model can use, and replaying its message alone would read as an
        unanswered question.
        """
        try:
            requests = self._store.list_session_requests(session_id)
        except Exception:  # a session that vanished is a history of nothing
            return []
        return [
            (request.message, request.response)
            for request in requests
            if request.request_id != request_id and request.response
        ]

    def _process(self, request_id: str) -> None:
        request = self._store.get_request(request_id)
        if request.state != "queued":
            # Already terminal (e.g. cancelled while queued).
            return
        if self._is_cancel_requested(request_id):
            self._store.update_request(request_id, state="cancelled")
            return

        self._store.update_request(request_id, state="running")
        task = compose_task(request.message, self._history(request_id, request.session_id))
        result = self._runner.run(task, stop=lambda: self._is_cancel_requested(request_id))

        fields = {
            "state": result.state,
            "cost_usd": result.cost_usd,
            "backend": result.backend,
        }
        if result.state == "completed":
            fields["response"] = result.text
        if result.error is not None:
            fields["error"] = result.error
        self._store.update_request(request_id, **fields)
