from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from cagent_api import worker as worker_module
from cagent_api.server import build_server
from cagent_api.store import Store
from cagent_api.worker import Worker

from .fakes import FakeOpenCodeClient


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(worker_module, "POLL_INTERVAL_SECONDS", 0.01)


@pytest.fixture()
def running_server():
    store = Store()
    opencode = FakeOpenCodeClient()
    w = Worker(store, opencode)
    w.start()
    httpd = build_server("127.0.0.1", 0, store, opencode, w)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        yield f"http://127.0.0.1:{port}", opencode
    finally:
        httpd.shutdown()
        httpd.server_close()


def _call(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


NODE_HEADERS = {
    "X-Cluster-Agent-Identity-Class": "node",
    "X-Cluster-Agent-Identity-Name": "agpc",
    "Content-Type": "application/json",
}


def test_create_request_missing_identity_returns_400(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"})
    assert status == 400
    assert payload["error"]["code"] == "bad_request"


def test_create_request_bad_identity_class_returns_400(running_server):
    base, _ = running_server
    headers = {**NODE_HEADERS, "X-Cluster-Agent-Identity-Class": "robot"}
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, headers)
    assert status == 400


def test_create_and_poll_request_to_completion(running_server):
    base, opencode = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    assert status == 202
    assert payload["state"] == "queued"
    request_id = payload["request_id"]
    session_id = payload["session_id"]

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        status, get_payload = _call(f"{base}/requests/{request_id}")
        if get_payload["state"] == "running":
            break
        time.sleep(0.01)
    assert get_payload["state"] == "running"

    opencode.complete_latest_turn(session_id, text="the answer")
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        status, get_payload = _call(f"{base}/requests/{request_id}")
        if get_payload["state"] == "completed":
            break
        time.sleep(0.01)
    assert get_payload["state"] == "completed"
    assert get_payload["response"] == "the answer"
    assert get_payload["identity"] == {"class": "node", "name": "agpc"}


def test_get_unknown_request_returns_404(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests/req_missing")
    assert status == 404
    assert payload["error"]["request_id"] == "req_missing"


def test_continue_session_requires_matching_identity(running_server):
    base, _ = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]

    other_headers = {**NODE_HEADERS, "X-Cluster-Agent-Identity-Name": "someone-else"}
    status, payload = _call(f"{base}/sessions/{session_id}/requests", "POST", {"message": "again"}, other_headers)
    assert status == 403


def test_cancel_queued_request_is_immediate(running_server):
    base, opencode = running_server
    # Never complete the first turn so the queue backs up.
    status, first = _call(base + "/requests", "POST", {"message": "first"}, NODE_HEADERS)

    status, second = _call(base + "/requests", "POST", {"message": "second"}, NODE_HEADERS)
    request_id = second["request_id"]

    status, cancelled = _call(f"{base}/requests/{request_id}/cancel", "POST")
    assert status == 200
    assert cancelled["state"] == "cancelled"


def test_list_sessions_and_session_requests(running_server):
    base, opencode = running_server
    status, payload = _call(base + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    session_id = payload["session_id"]
    opencode.complete_latest_turn(session_id)

    time.sleep(0.05)
    status, sessions = _call(base + "/sessions")
    assert status == 200
    assert any(s["session_id"] == session_id for s in sessions)

    status, requests = _call(f"{base}/sessions/{session_id}/requests")
    assert status == 200
    assert len(requests) == 1
