"""Background worker: dispatches turns to OpenCode and polls to completion.

Serialization choice (recorded per p1/contract.md, which left this to the
implementation): **global** serialization — a single worker thread drains
one queue for every session, not one queue per session. The plan
(p1/plan.md Step 3) explicitly allows this as "acceptable and simpler for
now (all sessions share one working directory)"; it also trivially
satisfies the contract's weaker per-session serialization requirement.
"""

from __future__ import annotations

import logging
import queue
import threading
import time

from .opencode_client import OpenCodeClient, OpenCodeError
from .store import Store

logger = logging.getLogger("cagent_api.worker")

POLL_INTERVAL_SECONDS = 1.0
# OpenCode can retry a broken backend connection indefinitely without ever
# settling a message (see p1/report2.md) — bound how long one turn can wedge
# the single global queue.
TURN_TIMEOUT_SECONDS = 300.0


class Worker:
    def __init__(self, store: Store, opencode: OpenCodeClient) -> None:
        self._store = store
        self._opencode = opencode
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

    def _process(self, request_id: str) -> None:
        request = self._store.get_request(request_id)
        if request.state != "queued":
            # Already terminal (e.g. cancelled while queued).
            return
        if self._is_cancel_requested(request_id):
            self._store.update_request(request_id, state="cancelled")
            return

        session_id = request.session_id
        self._store.update_request(request_id, state="running")

        try:
            baseline = self._opencode.count_assistant_messages(session_id)
            self._opencode.prompt_async(session_id, request.message)
        except OpenCodeError as exc:
            self._store.update_request(
                request_id,
                state="failed",
                error={"code": "opencode_error", "message": str(exc)},
            )
            return

        deadline = time.monotonic() + TURN_TIMEOUT_SECONDS
        while True:
            if self._is_cancel_requested(request_id):
                self._abort_and_mark_cancelled(request_id, session_id)
                return

            if time.monotonic() > deadline:
                self._abort_and_mark_failed(
                    request_id, session_id, "turn did not complete within timeout"
                )
                return

            try:
                count = self._opencode.count_assistant_messages(session_id)
                if count > baseline:
                    msg = self._opencode.latest_assistant_message(session_id)
                    if msg is not None and msg.completed:
                        if msg.error_name == "MessageAbortedError":
                            self._store.update_request(request_id, state="cancelled")
                        elif msg.error_name:
                            self._store.update_request(
                                request_id,
                                state="failed",
                                error={"code": "opencode_error", "message": msg.error_name},
                            )
                        else:
                            self._store.update_request(
                                request_id, state="completed", response=msg.text
                            )
                        return
            except OpenCodeError as exc:
                self._store.update_request(
                    request_id,
                    state="failed",
                    error={"code": "opencode_error", "message": str(exc)},
                )
                return

            time.sleep(POLL_INTERVAL_SECONDS)

    def _abort_and_mark_cancelled(self, request_id: str, session_id: str) -> None:
        try:
            self._opencode.abort(session_id)
        except OpenCodeError:
            logger.warning("worker: abort call failed for %s, marking cancelled anyway", request_id)
        self._store.update_request(request_id, state="cancelled")

    def _abort_and_mark_failed(self, request_id: str, session_id: str, message: str) -> None:
        try:
            self._opencode.abort(session_id)
        except OpenCodeError:
            pass
        self._store.update_request(
            request_id, state="failed", error={"code": "timeout", "message": message}
        )
