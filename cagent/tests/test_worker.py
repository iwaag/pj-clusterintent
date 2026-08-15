from __future__ import annotations

import time

import pytest

from cagent_api.store import Identity, Store
from cagent_api.worker import Worker

from .fakes import FakeRunner

IDENTITY = Identity("node", "agpc-uuid", "agpc-serial")


def wait_for_state(store: Store, request_id: str, state: str, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.get_request(request_id).state == state:
            return
        time.sleep(0.01)
    raise AssertionError(f"request {request_id} did not reach state {state!r}; got "
                          f"{store.get_request(request_id).state!r}")


def started(runner: FakeRunner, held: bool = False):
    """A store, a started worker, and one queued request."""
    store = Store()
    worker = Worker(store, runner)
    worker.start()
    if held:
        runner.hold()
    session = runner.new_session_id()
    request = store.create_session_and_request(session, IDENTITY, "hello")
    worker.enqueue(request.request_id)
    return store, worker, session, request


def test_full_turn_completes():
    runner = FakeRunner()
    store, _, _, request = started(runner)

    wait_for_state(store, request.request_id, "completed")
    final = store.get_request(request.request_id)
    assert final.response == "hi there"
    assert final.error is None
    # Agent ≠ Model: the run record names what actually served the turn,
    # including the role and profile that selected it.
    assert final.backend == {
        "harness": "agcode", "provider": "ollama", "model": "ollama/test-model",
        "role": "node", "profile": "local",
    }


def test_agcode_turn_reports_no_cost_rather_than_zero():
    """agcode's backend reports no cost. `None` says "not measured"; a 0.0
    would say "this was free", which is a different and false claim."""
    runner = FakeRunner()
    store, _, _, request = started(runner)

    wait_for_state(store, request.request_id, "completed")
    assert store.get_request(request.request_id).cost_usd is None


def test_a_harness_that_reports_cost_keeps_it():
    runner = FakeRunner()
    store, _, _, request = started(runner, held=True)

    wait_for_state(store, request.request_id, "running")
    runner.charge(0.0041, text="an answer")
    wait_for_state(store, request.request_id, "completed")
    assert store.get_request(request.request_id).cost_usd == pytest.approx(0.0041)


def test_prior_turns_of_the_session_are_replayed_into_the_task():
    """agcode is stateless, so cagent is the memory: the second turn's task
    carries the first turn's question and answer."""
    runner = FakeRunner()
    store, worker, session, first = started(runner)
    wait_for_state(store, first.request_id, "completed")

    second = store.continue_session(session, IDENTITY, "and what about the other one?")
    worker.enqueue(second.request_id)
    wait_for_state(store, second.request_id, "completed")

    replayed = runner.tasks[1]
    assert "=== EARLIER IN THIS SESSION ===" in replayed
    assert "hello" in replayed and "hi there" in replayed
    assert replayed.endswith("and what about the other one?")
    # The first turn saw no history at all.
    assert runner.tasks[0] == "hello"


def test_a_failed_turn_is_not_replayed_as_an_unanswered_question():
    runner = FakeRunner()
    store, worker, session, first = started(runner, held=True)
    wait_for_state(store, first.request_id, "running")
    runner.fail()
    wait_for_state(store, first.request_id, "failed")

    runner.release.set()
    runner.result = type(runner.result)("ok", "completed", None, None, None)
    second = store.continue_session(session, IDENTITY, "again")
    worker.enqueue(second.request_id)
    wait_for_state(store, second.request_id, "completed")

    assert runner.tasks[1] == "again"


def test_a_failing_run_marks_failed_with_its_reason():
    runner = FakeRunner()
    store, _, _, request = started(runner, held=True)

    wait_for_state(store, request.request_id, "running")
    runner.fail("deadline_exceeded: out of time")
    wait_for_state(store, request.request_id, "failed")
    assert store.get_request(request.request_id).error == {
        "code": "agent_error", "message": "deadline_exceeded: out of time",
    }


def test_cancel_while_running_reaches_the_run_through_stop():
    """Cancellation is the runner's `stop` callable, not an abort call to a
    session API — there is no session to abort any more."""
    runner = FakeRunner()
    store, worker, _, request = started(runner, held=True)

    wait_for_state(store, request.request_id, "running")
    assert callable(runner.stops[0])
    assert runner.stops[0]() is False
    worker.request_cancel(request.request_id)
    wait_for_state(store, request.request_id, "cancelled")


def test_cancel_while_queued_never_dispatches():
    runner = FakeRunner()
    store = Store()
    worker = Worker(store, runner)
    # Do not start the worker thread — simulate cancel landing before dispatch.
    session = runner.new_session_id()
    request = store.create_session_and_request(session, IDENTITY, "hello")
    store.update_request(request.request_id, state="cancelled")
    worker.enqueue(request.request_id)

    worker.start()
    time.sleep(0.1)
    assert store.get_request(request.request_id).state == "cancelled"
    assert runner.tasks == []


def test_global_serialization_second_request_waits():
    runner = FakeRunner()
    store, worker, session_a, req1 = started(runner, held=True)
    session_b = runner.new_session_id()
    req2 = store.create_session_and_request(session_b, IDENTITY, "second")
    worker.enqueue(req2.request_id)

    wait_for_state(store, req1.request_id, "running")
    time.sleep(0.05)
    # second request must still be queued: one global worker, req1 not done yet
    assert store.get_request(req2.request_id).state == "queued"

    runner.finish("done-a")
    wait_for_state(store, req1.request_id, "completed")
    wait_for_state(store, req2.request_id, "completed")


def test_a_crashing_runner_is_a_failed_request_not_a_dead_worker():
    class Exploding(FakeRunner):
        def run(self, task, *, stop=None, transcript_path=None):
            raise RuntimeError("boom")

    runner = Exploding()
    store, _, _, request = started(runner)
    wait_for_state(store, request.request_id, "failed")
    assert store.get_request(request.request_id).error["code"] == "internal_error"
