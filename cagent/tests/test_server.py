from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from cagent_api.server import build_server
from cagent_api.store import Store
from cagent_api.worker import Worker

from .fakes import FakeAuthenticator, FakeHumanAuthenticator, FakeRunner


@pytest.fixture()
def running_server():
    store = Store()
    runner = FakeRunner()
    runner.hold()
    w = Worker(store, runner)
    w.start()
    httpd = build_server("127.0.0.1", 0, store, runner, w, FakeAuthenticator())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        yield f"http://127.0.0.1:{port}", runner
    finally:
        httpd.shutdown()
        httpd.server_close()


def _call_raw(url: str):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers.get("Content-Type"), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type"), exc.read()


@pytest.fixture()
def running_dual_server():
    """Node listener + human listener sharing one store/worker (p4/plan.md
    Step 1: 'a second build_server() call sharing the same
    store/worker/runner objects'), both plain HTTP here — the fakes
    replace the auth seam, real TLS is the Step 3 conformance test's job."""
    store = Store()
    runner = FakeRunner()
    runner.hold()
    w = Worker(store, runner)
    w.start()
    node_httpd = build_server("127.0.0.1", 0, store, runner, w, FakeAuthenticator())
    human_httpd = build_server(
        "127.0.0.1", 0, store, runner, w, FakeHumanAuthenticator(), serve_ui=True
    )
    node_thread = threading.Thread(target=node_httpd.serve_forever, daemon=True)
    human_thread = threading.Thread(target=human_httpd.serve_forever, daemon=True)
    node_thread.start()
    human_thread.start()
    node_port = node_httpd.server_address[1]
    human_port = human_httpd.server_address[1]
    try:
        yield f"http://127.0.0.1:{node_port}", f"http://127.0.0.1:{human_port}", runner
    finally:
        node_httpd.shutdown()
        node_httpd.server_close()
        human_httpd.shutdown()
        human_httpd.server_close()


HUMAN_HEADERS = {
    "X-Test-Human": "1",
    "Content-Type": "application/json",
}


def _call(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


NODE_HEADERS = {
    "X-Test-Node-Uuid": "agpc-uuid",
    "Content-Type": "application/json",
}


def test_create_request_missing_identity_returns_401(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"})
    assert status == 401
    assert payload["error"]["code"] == "unauthorized"


def test_create_and_poll_request_to_completion(running_server):
    base, runner = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    assert status == 202
    assert payload["state"] == "queued"
    request_id = payload["request_id"]
    session_id = payload["session_id"]

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        status, get_payload = _call(f"{base}/requests/{request_id}", headers=NODE_HEADERS)
        if get_payload["state"] == "running":
            break
        time.sleep(0.01)
    assert get_payload["state"] == "running"

    runner.finish("the answer")
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        status, get_payload = _call(f"{base}/requests/{request_id}", headers=NODE_HEADERS)
        if get_payload["state"] == "completed":
            break
        time.sleep(0.01)
    assert get_payload["state"] == "completed"
    assert get_payload["response"] == "the answer"
    assert get_payload["identity"] == {
        "class": "node", "uuid": "agpc-uuid", "cert_serial": "test-serial-agpc-uuid",
    }


def test_get_request_missing_identity_returns_401(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    request_id = payload["request_id"]

    status, payload = _call(f"{base}/requests/{request_id}")
    assert status == 401
    assert payload["error"]["code"] == "unauthorized"


def test_get_request_owned_by_another_uuid_is_rejected(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    request_id = payload["request_id"]

    other_headers = {**NODE_HEADERS, "X-Test-Node-Uuid": "someone-else-uuid"}
    status, payload = _call(f"{base}/requests/{request_id}", headers=other_headers)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_get_unknown_request_returns_404(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests/req_missing", headers=NODE_HEADERS)
    assert status == 404
    assert payload["error"]["request_id"] == "req_missing"


def test_continue_session_requires_matching_identity(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]

    other_headers = {**NODE_HEADERS, "X-Test-Node-Uuid": "someone-else-uuid"}
    status, payload = _call(f"{base}/sessions/{session_id}/requests", "POST", {"message": "again"}, other_headers)
    assert status == 403


def test_cancel_queued_request_is_immediate(running_server):
    base, runner = running_server
    # Never complete the first turn so the queue backs up.
    status, first = _call(base + "/requests", "POST", {"message": "first"}, NODE_HEADERS)

    status, second = _call(base + "/requests", "POST", {"message": "second"}, NODE_HEADERS)
    request_id = second["request_id"]

    status, cancelled = _call(f"{base}/requests/{request_id}/cancel", "POST", headers=NODE_HEADERS)
    assert status == 200
    assert cancelled["state"] == "cancelled"


def test_cancel_request_owned_by_another_uuid_is_rejected(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "first"}, NODE_HEADERS)
    request_id = payload["request_id"]

    other_headers = {**NODE_HEADERS, "X-Test-Node-Uuid": "someone-else-uuid"}
    status, payload = _call(f"{base}/requests/{request_id}/cancel", "POST", headers=other_headers)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_list_sessions_and_session_requests(running_server):
    base, runner = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]
    runner.finish()

    time.sleep(0.05)
    status, sessions = _call(base + "/sessions", headers=NODE_HEADERS)
    assert status == 200
    assert any(s["session_id"] == session_id for s in sessions)

    status, requests = _call(f"{base}/sessions/{session_id}/requests", headers=NODE_HEADERS)
    assert status == 200
    assert len(requests) == 1


def test_list_sessions_excludes_other_identities_sessions(running_server):
    base, runner = running_server
    _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)

    other_headers = {**NODE_HEADERS, "X-Test-Node-Uuid": "someone-else-uuid"}
    status, sessions = _call(base + "/sessions", headers=other_headers)
    assert status == 200
    assert sessions == []


def test_list_session_requests_owned_by_another_uuid_is_rejected(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]

    other_headers = {**NODE_HEADERS, "X-Test-Node-Uuid": "someone-else-uuid"}
    status, payload = _call(f"{base}/sessions/{session_id}/requests", headers=other_headers)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_human_request_identity_recorded_in_evidence(running_dual_server):
    _, human_base, _ = running_dual_server
    status, payload = _call(human_base + "/requests", "POST", {"message": "hi"}, HUMAN_HEADERS)
    assert status == 202
    request_id = payload["request_id"]

    status, get_payload = _call(f"{human_base}/requests/{request_id}", headers=HUMAN_HEADERS)
    assert status == 200
    assert get_payload["identity"] == {"class": "human", "name": "operator"}


def test_human_can_list_all_sessions_including_node_sessions(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, node_payload = _call(node_base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    node_session_id = node_payload["session_id"]

    status, human_payload = _call(human_base + "/requests", "POST", {"message": "hi"}, HUMAN_HEADERS)
    human_session_id = human_payload["session_id"]

    status, sessions = _call(human_base + "/sessions", headers=HUMAN_HEADERS)
    assert status == 200
    session_ids = {s["session_id"] for s in sessions}
    assert node_session_id in session_ids
    assert human_session_id in session_ids


def test_human_can_read_a_node_created_request(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, payload = _call(node_base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    request_id = payload["request_id"]

    status, payload = _call(f"{human_base}/requests/{request_id}", headers=HUMAN_HEADERS)
    assert status == 200
    assert payload["identity"]["class"] == "node"


def test_node_cannot_read_a_human_created_request(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, payload = _call(human_base + "/requests", "POST", {"message": "hi"}, HUMAN_HEADERS)
    request_id = payload["request_id"]

    status, payload = _call(f"{node_base}/requests/{request_id}", headers=NODE_HEADERS)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_human_cannot_continue_a_node_created_session(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, payload = _call(node_base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]

    status, payload = _call(
        f"{human_base}/sessions/{session_id}/requests", "POST", {"message": "again"}, HUMAN_HEADERS
    )
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_node_cannot_continue_a_human_created_session(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, payload = _call(human_base + "/requests", "POST", {"message": "hi"}, HUMAN_HEADERS)
    session_id = payload["session_id"]

    status, payload = _call(
        f"{node_base}/sessions/{session_id}/requests", "POST", {"message": "again"}, NODE_HEADERS
    )
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_human_cannot_cancel_a_node_created_request(running_dual_server):
    node_base, human_base, _ = running_dual_server
    status, payload = _call(node_base + "/requests", "POST", {"message": "first"}, NODE_HEADERS)
    request_id = payload["request_id"]

    status, payload = _call(f"{human_base}/requests/{request_id}/cancel", "POST", headers=HUMAN_HEADERS)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_human_can_cancel_own_queued_request(running_dual_server):
    node_base, human_base, _ = running_dual_server
    _call(human_base + "/requests", "POST", {"message": "first"}, HUMAN_HEADERS)
    status, payload = _call(human_base + "/requests", "POST", {"message": "second"}, HUMAN_HEADERS)
    request_id = payload["request_id"]

    status, cancelled = _call(f"{human_base}/requests/{request_id}/cancel", "POST", headers=HUMAN_HEADERS)
    assert status == 200
    assert cancelled["state"] == "cancelled"


def test_human_listener_serves_chat_ui_at_root_unauthenticated(running_dual_server):
    _, human_base, _ = running_dual_server
    status, content_type, body = _call_raw(human_base + "/")
    assert status == 200
    assert "text/html" in content_type
    assert b"cluster-agent" in body


def test_node_listener_does_not_serve_chat_ui(running_dual_server):
    node_base, _, _ = running_dual_server
    status, _, _ = _call_raw(node_base + "/")
    assert status == 404


def test_llms_txt_served_unauthenticated_on_both_listeners(running_dual_server):
    node_base, human_base, _ = running_dual_server
    for base in (node_base, human_base):
        status, content_type, body = _call_raw(base + "/llms.txt")
        assert status == 200
        assert "text/plain" in content_type
        assert b"cluster-agent" in body
