"""The window listener: one unauthenticated door, and nothing else on it.

Same style as test_server.py — the fakes replace the OpenCode boundary, and
`NoAuthenticator` is the real production authenticator here because "no
credential" is the actual contract, not a test seam.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from cagent_api import worker as worker_module
from cagent_api.auth import NoAuthenticator
from cagent_api.server import build_server
from cagent_api.store import Store
from cagent_api.worker import Worker

from .fakes import FakeAuthenticator, FakeOpenCodeClient

JSON = {"Content-Type": "application/json"}
NODE_HEADERS = {"X-Test-Node-Uuid": "agpc-uuid", "Content-Type": "application/json"}


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(worker_module, "POLL_INTERVAL_SECONDS", 0.01)


@pytest.fixture()
def guide(tmp_path):
    path = tmp_path / "GUIDE.md"
    path.write_text("# window guide\n\nfirst version\n", encoding="utf-8")
    return path


@pytest.fixture()
def running_window(guide):
    """Node listener + window listener sharing one store, each with its own
    OpenCode client and worker — the production wiring in main.py."""
    store = Store()
    node_opencode = FakeOpenCodeClient()
    node_worker = Worker(store, node_opencode)
    node_worker.start()
    window_opencode = FakeOpenCodeClient()
    window_worker = Worker(store, window_opencode)
    window_worker.start()

    node_httpd = build_server("127.0.0.1", 0, store, node_opencode, node_worker, FakeAuthenticator())
    window_httpd = build_server(
        "127.0.0.1", 0, store, window_opencode, window_worker, NoAuthenticator(),
        guide_path=guide,
    )
    for httpd in (node_httpd, window_httpd):
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield (
            f"http://127.0.0.1:{window_httpd.server_address[1]}",
            f"http://127.0.0.1:{node_httpd.server_address[1]}",
            window_opencode,
            node_opencode,
        )
    finally:
        for httpd in (node_httpd, window_httpd):
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


def _wait_for(window, request_id, state, timeout=2.0):
    deadline = time.monotonic() + timeout
    payload = None
    while time.monotonic() < deadline:
        _, payload = _call(f"{window}/requests/{request_id}")
        if payload["state"] == state:
            return payload
        time.sleep(0.01)
    return payload


def test_a_message_needs_no_credential_and_reaches_the_window_opencode(running_window):
    window, _, window_opencode, node_opencode = running_window
    status, payload = _call(window + "/window", "POST", {"text": "is agpc up?"}, JSON)
    assert status == 202
    assert payload["state"] == "queued"

    running = _wait_for(window, payload["request_id"], "running")
    assert running["identity"] == {"class": "window", "name": "window"}

    window_opencode.complete_latest_turn(payload["session_id"], text="it is up")
    completed = _wait_for(window, payload["request_id"], "completed")
    assert completed["response"] == "it is up"
    # The window's turn must not have gone to the authenticated instance.
    assert [text for _, text in window_opencode.prompt_calls] == ["is agpc up?"]
    assert node_opencode.prompt_calls == []


def test_the_window_rejects_an_empty_or_missing_text(running_window):
    window, _, _, _ = running_window
    for body in ({}, {"text": ""}, {"text": "   "}, {"message": "wrong key"}):
        status, payload = _call(window + "/window", "POST", body, JSON)
        assert status == 400, body
        assert payload["error"]["code"] == "bad_request"


def test_the_window_has_no_other_doors(running_window):
    window, _, _, _ = running_window
    for method, path, body in (
        ("POST", "/requests", {"message": "hi"}),
        ("GET", "/sessions", None),
        ("GET", "/", None),
        ("GET", "/llms.txt", None),
    ):
        status, payload = _call(window + path, method, body, JSON)
        assert status == 404, path
        assert payload["error"]["code"] == "not_found"


def test_the_guide_is_served_raw_and_re_read_per_request(running_window, guide):
    window, _, _, _ = running_window
    with urllib.request.urlopen(window + "/guide", timeout=5) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "text/plain; charset=utf-8"
        assert b"first version" in resp.read()

    guide.write_text("# window guide\n\nsecond version\n", encoding="utf-8")
    with urllib.request.urlopen(window + "/guide", timeout=5) as resp:
        assert b"second version" in resp.read()


def test_healthz_answers_without_a_credential(running_window):
    window, _, _, _ = running_window
    assert _call(window + "/healthz") == (200, {"ok": True})


def test_a_node_cannot_read_a_window_request(running_window):
    window, node, _, _ = running_window
    _, created = _call(window + "/window", "POST", {"text": "hello"}, JSON)
    status, payload = _call(f"{node}/requests/{created['request_id']}", headers=NODE_HEADERS)
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_the_window_cannot_read_a_node_request(running_window):
    window, node, _, _ = running_window
    _, created = _call(node + "/requests", "POST", {"message": "hi"}, NODE_HEADERS)
    status, payload = _call(f"{window}/requests/{created['request_id']}")
    assert status == 403
    assert payload["error"]["code"] == "forbidden"
