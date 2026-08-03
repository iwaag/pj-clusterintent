from __future__ import annotations

from cagent_api.evidence import EvidenceWriter
from cagent_api.store import Identity, Store, scan_and_load


def test_evidence_written_on_create_and_transitions(tmp_path):
    evidence = EvidenceWriter(tmp_path)
    store = Store(evidence=evidence)
    identity = Identity("node", "agpc-uuid", "agpc-serial")

    request = store.create_session_and_request("ses_1", identity, "hello")
    store.update_request(request.request_id, state="running")
    store.update_request(request.request_id, state="completed", response="the answer")

    record = evidence.read_request(request.request_id)
    assert record["session_id"] == "ses_1"
    assert record["identity"] == {"class": "node", "uuid": "agpc-uuid", "cert_serial": "agpc-serial"}
    assert record["message"] == "hello"

    events_path = tmp_path / request.request_id / "events.jsonl"
    lines = events_path.read_text().strip().splitlines()
    states = [__import__("json").loads(line)["state"] for line in lines]
    assert states == ["queued", "running", "completed"]

    latest = evidence.read_latest_event(request.request_id)
    assert latest["state"] == "completed"
    assert latest["detail"]["response"] == "the answer"


def test_scan_and_load_marks_non_terminal_as_interrupted(tmp_path):
    evidence = EvidenceWriter(tmp_path)
    store = Store(evidence=evidence)
    identity = Identity(identity_class="human", name="operator")

    stuck = store.create_session_and_request("ses_1", identity, "stuck one")
    store.update_request(stuck.request_id, state="running")

    done = store.continue_session("ses_1", identity, "already done")
    store.update_request(done.request_id, state="running")
    store.update_request(done.request_id, state="completed", response="fine")

    # Simulate a fresh process: rebuild purely from what is on disk.
    reloaded, newly_interrupted = scan_and_load(evidence)
    assert newly_interrupted == [stuck.request_id]

    stuck_reloaded = reloaded.get_request(stuck.request_id)
    assert stuck_reloaded.state == "interrupted"

    done_reloaded = reloaded.get_request(done.request_id)
    assert done_reloaded.state == "completed"
    assert done_reloaded.response == "fine"

    # The interrupted transition itself must also be durable.
    latest = evidence.read_latest_event(stuck.request_id)
    assert latest["state"] == "interrupted"

    session = reloaded.list_sessions()[0]
    assert session.session_id == "ses_1"
    assert session.identity.identity_class == "human"
    assert session.identity.name == "operator"
    requests = reloaded.list_session_requests("ses_1")
    assert [r.request_id for r in requests] == [stuck.request_id, done.request_id]


def test_scan_and_load_on_empty_evidence_dir_is_empty_store(tmp_path):
    evidence = EvidenceWriter(tmp_path / "does-not-exist-yet")
    store, newly_interrupted = scan_and_load(evidence)
    assert store.list_sessions() == []
    assert newly_interrupted == []


def test_scan_and_load_does_not_redouble_already_interrupted(tmp_path):
    evidence = EvidenceWriter(tmp_path)
    store = Store(evidence=evidence)
    identity = Identity("node", "agpc-uuid", "agpc-serial")
    request = store.create_session_and_request("ses_1", identity, "hi")
    store.update_request(request.request_id, state="running")

    _, first_pass = scan_and_load(evidence)
    assert first_pass == [request.request_id]

    _, second_pass = scan_and_load(evidence)
    assert second_pass == []
    events = (evidence.evidence_dir / request.request_id / "events.jsonl").read_text()
    assert events.count('"interrupted"') == 1


def test_queued_request_never_dispatched_is_marked_interrupted(tmp_path):
    """A request that never got past `queued` (process died before the
    worker even picked it up) must still resolve to `interrupted`, not
    `unknown` or a 404 — this is exit criterion 4's literal wording."""
    evidence = EvidenceWriter(tmp_path)
    store = Store(evidence=evidence)
    identity = Identity("node", "agpc-uuid", "agpc-serial")
    request = store.create_session_and_request("ses_1", identity, "never started")

    reloaded, newly_interrupted = scan_and_load(evidence)
    assert newly_interrupted == [request.request_id]
    assert reloaded.get_request(request.request_id).state == "interrupted"
