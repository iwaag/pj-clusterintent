from __future__ import annotations

import time

import pytest

from cagent_api import worker as worker_module
from cagent_api.store import Identity, Store
from cagent_api.worker import Worker

from .fakes import FakeOpenCodeClient


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(worker_module, "POLL_INTERVAL_SECONDS", 0.01)


def wait_for_state(store: Store, request_id: str, state: str, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.get_request(request_id).state == state:
            return
        time.sleep(0.01)
    raise AssertionError(f"request {request_id} did not reach state {state!r}; got "
                          f"{store.get_request(request_id).state!r}")


def test_full_turn_completes():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    w.enqueue(request.request_id)

    wait_for_state(store, request.request_id, "running")
    opencode.complete_latest_turn(session_id, text="hi there")
    wait_for_state(store, request.request_id, "completed")

    final = store.get_request(request.request_id)
    assert final.response == "hi there"
    assert final.error is None


def test_multi_step_turn_does_not_complete_early():
    """A real multi-step tool-calling turn produces several assistant
    messages, only the last of which is the true end (OpenCode's
    `finish != "tool-calls"`). The worker must not treat an intermediate
    step's completion as the whole turn finishing."""
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    w.enqueue(request.request_id)

    wait_for_state(store, request.request_id, "running")
    opencode.push_intermediate_step(session_id)
    opencode.push_intermediate_step(session_id)
    time.sleep(0.1)
    assert store.get_request(request.request_id).state == "running"

    opencode.complete_latest_turn(session_id, text="final answer")
    wait_for_state(store, request.request_id, "completed")
    assert store.get_request(request.request_id).response == "final answer"


def test_opencode_error_marks_failed():
    store = Store()
    opencode = FakeOpenCodeClient()
    opencode.raise_on_prompt = True
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    w.enqueue(request.request_id)

    wait_for_state(store, request.request_id, "failed")
    assert store.get_request(request.request_id).error["code"] == "opencode_error"


def test_assistant_error_marks_failed():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    w.enqueue(request.request_id)

    wait_for_state(store, request.request_id, "running")
    opencode.fail_latest_turn(session_id, error_name="SomeModelError")
    wait_for_state(store, request.request_id, "failed")
    assert store.get_request(request.request_id).error["message"] == "SomeModelError"


def test_cancel_while_running_aborts_and_marks_cancelled():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    w.enqueue(request.request_id)

    wait_for_state(store, request.request_id, "running")
    w.request_cancel(request.request_id)
    wait_for_state(store, request.request_id, "cancelled")
    assert opencode.abort_calls == [session_id]


def test_cancel_while_queued_never_dispatches():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    # Do not start the worker thread — simulate cancel landing before dispatch.

    identity = Identity("node", "agpc")
    session_id = opencode.create_session("t")
    request = store.create_session_and_request(session_id, identity, "hello")
    store.update_request(request.request_id, state="cancelled")
    w.enqueue(request.request_id)

    w.start()
    time.sleep(0.1)
    assert store.get_request(request.request_id).state == "cancelled"
    assert opencode.prompt_calls == []


def test_turn_timeout_marks_failed():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()
    original_timeout = worker_module.TURN_TIMEOUT_SECONDS
    worker_module.TURN_TIMEOUT_SECONDS = 0.05
    try:
        identity = Identity("node", "agpc")
        session_id = opencode.create_session("t")
        request = store.create_session_and_request(session_id, identity, "hello")
        w.enqueue(request.request_id)
        # never complete the turn
        wait_for_state(store, request.request_id, "failed", timeout=2.0)
        assert store.get_request(request.request_id).error["code"] == "timeout"
        assert opencode.abort_calls == [session_id]
    finally:
        worker_module.TURN_TIMEOUT_SECONDS = original_timeout


def test_global_serialization_second_request_waits():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()

    identity = Identity("node", "agpc")
    session_a = opencode.create_session("a")
    session_b = opencode.create_session("b")
    req1 = store.create_session_and_request(session_a, identity, "first")
    req2 = store.create_session_and_request(session_b, identity, "second")
    w.enqueue(req1.request_id)
    w.enqueue(req2.request_id)

    wait_for_state(store, req1.request_id, "running")
    time.sleep(0.05)
    # second request must still be queued: one global worker, req1 not done yet
    assert store.get_request(req2.request_id).state == "queued"

    opencode.complete_latest_turn(session_a, text="done-a")
    wait_for_state(store, req1.request_id, "completed")
    wait_for_state(store, req2.request_id, "running")
    opencode.complete_latest_turn(session_b, text="done-b")
    wait_for_state(store, req2.request_id, "completed")
