"""Tier A real-tool proof: cagent's mTLS policy agrees with a real TLS stack.

The mTLS analogue of `test_openssh_conformance.py`. This owns the TLS/ledger
connect-time boundary only (p2/contract.md): real keys, a real CA (minted
via `cagent_api.ca`), a real `ssl.SSLContext`-wrapped loopback server running
the actual `cagent_api.server`/`auth` code (not a stand-in), and a
throwaway ledger — all fixture-owned and cleaned up by pytest's `tmp_path`.
No mock-only mTLS test (README_DEV lesson 2): every case below drives a real
TLS handshake over a real socket, not a stubbed `ssl` module.

DesiredNode validity is faked (a fixed set of "currently valid" UUIDs), not
read from a live Nautobot: this gate must not read `nctl.toml` or a live
inventory (devtests/test_strategy/README.md), and DesiredNode
resolution is `node_resolver.py`'s own concern, not this boundary's — same
split the plan makes ("OpenCode side can be faked here; this test owns the
TLS/ledger boundary, not the agent conversation").

Run from the superproject root:

    uv run --project cagent pytest -q devtests/test_strategy/test_mtls_conformance.py
"""

from __future__ import annotations

import datetime
import http.client
import json
import os
import ssl
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cagent" / "src"))

from cagent_api import ca  # noqa: E402
from cagent_api.auth import CertAuthenticator, TokenAuthenticator  # noqa: E402
from cagent_api.ledger import Ledger  # noqa: E402
from cagent_api.opencode_client import AssistantMessage, OpenCodeError  # noqa: E402
from cagent_api.server import build_server  # noqa: E402
from cagent_api.store import Store  # noqa: E402
from cagent_api.worker import Worker  # noqa: E402

NODE_UUID = "27818c12-fe15-4c9f-83d0-7949523f6c33"
OTHER_NODE_UUID = "d3a4b6f0-6b41-4e6a-9a4a-1b2c3d4e5f60"
PRUNED_NODE_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
HUMAN_TOKEN = "conformance-test-token"

WRAPPER = ROOT / "ansible_agdev" / "roles" / "cagent_client" / "files" / "cagent"


class _FakeOpenCode:
    """Minimal stand-in so this gate never depends on a real OpenCode
    process — the conversation itself is out of scope here. Tracks a
    per-session message count so `worker.py`'s real `count >
    baseline`-based completion detection actually fires (needed by the
    Step 1 wrapper tests below, which wait for a real `completed`
    transition, not just the immediate post-create `queued` state the
    earlier connect/reject tests inspect)."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}
        self._lock = threading.Lock()

    def create_session(self, title: str) -> str:
        # uuid4, not a per-instance counter: the fixture builds one
        # _FakeOpenCode per listener (node + human), so a counter starting
        # at 1 in each would still collide across listeners.
        session_id = f"ses_conformance_{uuid.uuid4().hex[:8]}"
        with self._lock:
            self._sessions.setdefault(session_id, [])
        return session_id

    def prompt_async(self, session_id: str, text: str) -> None:
        def _complete() -> None:
            time.sleep(0.2)
            with self._lock:
                self._sessions.setdefault(session_id, []).append(
                    {"completed": True, "text": "ok", "error_name": None, "is_final_step": True}
                )

        threading.Thread(target=_complete, daemon=True).start()

    def count_assistant_messages(self, session_id: str) -> int:
        with self._lock:
            return len(self._sessions.get(session_id, []))

    def latest_assistant_message(self, session_id: str):
        with self._lock:
            turns = self._sessions.get(session_id, [])
            if not turns:
                return None
            t = turns[-1]
            return AssistantMessage(
                completed=t["completed"], text=t["text"], error_name=t["error_name"], is_final_step=t["is_final_step"],
            )

    def abort(self, session_id: str) -> bool:
        return True


class _FakeNodeResolver:
    """Test-owned stand-in for the live Nautobot DesiredNode check —
    `node_resolver.py`'s own real-HTTP behavior is covered by
    `cagent/tests/test_node_resolver.py`, not this gate."""

    def __init__(self, valid_uuids: set[str]) -> None:
        self._valid_uuids = valid_uuids

    def is_valid(self, node_uuid: str) -> bool:
        return node_uuid in self._valid_uuids


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)


class _Fixture:
    """Owns the CA, ledger, and running mTLS server for one test."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.ca_key, ca_signed = ca.build_ca("cagent-conformance-ca", valid_days=10)
        self.ca_cert = ca_signed.certificate
        _write(tmp_path / "ca.pem", ca.cert_to_pem(self.ca_cert))

        server_key = ca.generate_key()
        server_signed = ca.sign_server_cert(
            self.ca_key, self.ca_cert, server_key, "cagent-conformance-server",
            dns_sans=["localhost"], ip_sans=["127.0.0.1"], valid_days=10,
        )
        server_pem = tmp_path / "server.pem"
        _write(server_pem, ca.key_to_pem(server_key) + ca.cert_to_pem(server_signed.certificate))

        self.ledger = Ledger(tmp_path / "ledger.jsonl")
        self.node_resolver = _FakeNodeResolver({NODE_UUID, OTHER_NODE_UUID})
        authenticate = CertAuthenticator(self.ledger, self.node_resolver)

        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.load_cert_chain(str(server_pem))
        server_ctx.verify_mode = ssl.CERT_REQUIRED
        server_ctx.load_verify_locations(str(tmp_path / "ca.pem"))

        self.store = Store()
        self.worker = Worker(self.store, _FakeOpenCode())
        self.worker.start()
        self.httpd = build_server(
            "127.0.0.1", 0, self.store, _FakeOpenCode(), self.worker, authenticate, ssl_context=server_ctx
        )
        self.port = self.httpd.socket.getsockname()[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()

        # Human listener (p4/contract.md): server-only TLS on the same leaf
        # cert/key, no client cert required, bearer-token authenticated.
        # Shares self.store/self.worker with the node listener — same
        # wiring main.py uses in production, minus the process split.
        human_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        human_ctx.load_cert_chain(str(server_pem))
        human_ctx.verify_mode = ssl.CERT_NONE
        human_authenticate = TokenAuthenticator(HUMAN_TOKEN, human_name="operator")
        self.human_httpd = build_server(
            "127.0.0.1", 0, self.store, _FakeOpenCode(), self.worker, human_authenticate,
            ssl_context=human_ctx, serve_ui=True,
        )
        self.human_port = self.human_httpd.socket.getsockname()[1]
        self._human_thread = threading.Thread(target=self.human_httpd.serve_forever, daemon=True)
        self._human_thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.human_httpd.shutdown()
        self.human_httpd.server_close()

    def sign_node_cert(self, node_uuid: str, not_before=None, not_after=None):
        key = ca.generate_key()
        signed = ca.sign_node_cert_for_test(
            self.ca_key, self.ca_cert, key, node_uuid, "cagent-conformance-node",
            not_before=not_before, not_after=not_after,
        )
        key_path = self.tmp_path / f"node_{signed.serial_hex}_key.pem"
        cert_path = self.tmp_path / f"node_{signed.serial_hex}_cert.pem"
        _write(key_path, ca.key_to_pem(key))
        _write(cert_path, ca.cert_to_pem(signed.certificate))
        return signed, key_path, cert_path

    def register(self, signed, node_uuid: str):
        self.ledger.register(node_uuid, signed.serial_hex, "fp", signed.not_after.isoformat())

    def write_client_conf(self, cert_path: Path, key_path: Path) -> Path:
        conf_path = self.tmp_path / f"client_{cert_path.stem}.conf"
        conf_path.write_text(
            f"CAGENT_API_URL=https://127.0.0.1:{self.port}\n"
            f"CAGENT_CA_CERT={self.tmp_path / 'ca.pem'}\n"
            f"CAGENT_CLIENT_CERT={cert_path}\n"
            f"CAGENT_CLIENT_KEY={key_path}\n"
            "CAGENT_POLL_INTERVAL=1\n"
            "CAGENT_POLL_MAX=30\n"
        )
        return conf_path

    def run_wrapper(self, conf_path: Path, args: list[str], stdin_text: str = ""):
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "CAGENT_CONF": str(conf_path)}
        if "TMPDIR" in os.environ:
            env["TMPDIR"] = os.environ["TMPDIR"]
        return subprocess.run(
            [str(WRAPPER), *args], input=stdin_text, capture_output=True, text=True, env=env, timeout=30,
        )

    def request(self, cert_path: Path, key_path: Path, method: str, path: str, body: dict | None = None):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(str(self.tmp_path / "ca.pem"))
        ctx.load_cert_chain(str(cert_path), str(key_path))
        ctx.check_hostname = False
        conn = http.client.HTTPSConnection("127.0.0.1", self.port, context=ctx, timeout=5)
        try:
            data = json.dumps(body).encode() if body is not None else None
            conn.request(method, path, body=data, headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            return resp.status, json.loads(resp.read())
        finally:
            conn.close()

    def request_node_without_client_cert(self, method: str, path: str):
        """No client cert loaded at all — proves the node listener's
        `CERT_REQUIRED` actually rejects a cert-less connection at the TLS
        handshake, not just an untrusted one."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(str(self.tmp_path / "ca.pem"))
        ctx.check_hostname = False
        conn = http.client.HTTPSConnection("127.0.0.1", self.port, context=ctx, timeout=5)
        try:
            conn.request(method, path)
            conn.getresponse()
        finally:
            conn.close()

    def human_request(self, token: str | None, method: str, path: str, body: dict | None = None):
        """No client cert at all (server-only TLS) — proves the human
        listener genuinely does not require one."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(str(self.tmp_path / "ca.pem"))
        ctx.check_hostname = False
        conn = http.client.HTTPSConnection("127.0.0.1", self.human_port, context=ctx, timeout=5)
        try:
            data = json.dumps(body).encode() if body is not None else None
            headers = {"Content-Type": "application/json"}
            if token is not None:
                headers["Authorization"] = f"Bearer {token}"
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            content_type = resp.getheader("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(raw)
            return resp.status, raw
        finally:
            conn.close()


@pytest.fixture()
def fixture(tmp_path):
    f = _Fixture(tmp_path)
    try:
        yield f
    finally:
        f.close()


def test_valid_registered_active_cert_is_accepted_with_expected_identity(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 202
    assert payload["state"] == "queued"

    status, get_payload = fixture.request(cert_path, key_path, "GET", f"/requests/{payload['request_id']}")
    assert status == 200
    assert get_payload["identity"] == {
        "class": "node", "uuid": NODE_UUID, "cert_serial": signed.serial_hex,
    }


def test_revoked_serial_is_rejected(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    fixture.ledger.revoke(signed.serial_hex)

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 403
    assert payload["error"]["code"] == "forbidden"
    assert fixture.ledger.get(signed.serial_hex).state == "revoked"  # positive evidence, not just the response


def test_expired_cert_fails_at_the_tls_handshake(fixture):
    now = datetime.datetime.now(datetime.timezone.utc)
    signed, key_path, cert_path = fixture.sign_node_cert(
        NODE_UUID,
        not_before=now - datetime.timedelta(days=10),
        not_after=now - datetime.timedelta(days=1),
    )
    fixture.register(signed, NODE_UUID)

    with pytest.raises(ssl.SSLError) as exc_info:
        fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})
    assert "CERTIFICATE_EXPIRED" in str(exc_info.value) or "certificate has expired" in str(exc_info.value).lower()


def test_unregistered_cert_is_rejected(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    # Deliberately not registered in the ledger.

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 403
    assert payload["error"]["code"] == "forbidden"
    assert fixture.ledger.get(signed.serial_hex) is None  # positive evidence it was never registered


def test_uuid_with_no_valid_desired_node_is_rejected(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(PRUNED_NODE_UUID)
    fixture.register(signed, PRUNED_NODE_UUID)  # ledger trusts the key; DesiredNode resolution does not

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_revoked_serial_is_rejected_on_status_poll_not_just_creation(fixture):
    """Regression: p3 Step 0's live prototype found that GET /requests/{id}
    (and cancel/list) skipped the identity check entirely, so a revoked or
    otherwise deauthorized cert could still read/cancel/list requests after
    revocation. p2/contract.md requires the three checks on every request,
    not just session creation."""
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    status, created = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})
    assert status == 202
    request_id = created["request_id"]

    fixture.ledger.revoke(signed.serial_hex)

    status, payload = fixture.request(cert_path, key_path, "GET", f"/requests/{request_id}")
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_session_owned_by_another_uuid_is_rejected(fixture):
    owner_signed, owner_key, owner_cert = fixture.sign_node_cert(NODE_UUID)
    fixture.register(owner_signed, NODE_UUID)
    other_signed, other_key, other_cert = fixture.sign_node_cert(OTHER_NODE_UUID)
    fixture.register(other_signed, OTHER_NODE_UUID)

    status, created = fixture.request(owner_cert, owner_key, "POST", "/requests", {"message": "hi"})
    assert status == 202
    session_id = created["session_id"]

    status, payload = fixture.request(
        other_cert, other_key, "POST", f"/sessions/{session_id}/requests", {"message": "intrude"}
    )

    assert status == 403
    assert payload["error"]["code"] == "forbidden"
    # Positive evidence: the session is still owned by the original UUID, not silently reassigned.
    assert fixture.store.list_sessions()[0].identity.uuid == NODE_UUID


# --- p3/plan.md Step 1: drive the actual wrapper script, not curl, against
# this same real-TLS/ledger/OpenCode fixture. Covers the wrapper's whole
# job (TLS args, body-from-stdin, polling, error surfacing) with no
# mock-only TLS and no live node.


def test_wrapper_ask_with_wait_prints_answer_and_exits_zero(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    conf_path = fixture.write_client_conf(cert_path, key_path)

    result = fixture.run_wrapper(conf_path, ["ask"], stdin_text="what storage exists?")

    assert result.returncode == 0, result.stderr
    assert "state=completed" in result.stdout
    assert "ok" in result.stdout  # _FakeOpenCode.latest_assistant_message's text


def test_wrapper_status_fetches_a_created_requests_state(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    conf_path = fixture.write_client_conf(cert_path, key_path)

    created = fixture.run_wrapper(conf_path, ["ask", "--no-wait"], stdin_text="hi")
    assert created.returncode == 0, created.stderr
    request_id = json.loads(created.stdout)["request_id"]

    result = fixture.run_wrapper(conf_path, ["status", request_id])

    assert result.returncode == 0, result.stderr
    assert f"request_id={request_id}" in result.stdout


def test_wrapper_continue_reuses_the_session(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    conf_path = fixture.write_client_conf(cert_path, key_path)

    first = fixture.run_wrapper(conf_path, ["ask"], stdin_text="first turn")
    assert first.returncode == 0, first.stderr
    session_id = first.stdout.splitlines()[0].split("session_id=")[1].split(" ")[0]

    second = fixture.run_wrapper(conf_path, ["continue", session_id], stdin_text="second turn")

    assert second.returncode == 0, second.stderr
    assert f"session_id={session_id}" in second.stdout


def test_serial_hex_matches_getpeercert_even_when_top_byte_needs_zero_padding(fixture):
    """Regression: `ca._wrap` used to compute `serial_hex` with plain
    `format(cert.serial_number, "x")`, which drops a would-be leading zero
    nibble whenever the serial's most significant byte is < 0x10 (~1/16 of
    random serials). OpenSSL's `getpeercert()["serialNumber"]` never drops
    it (byte-aligned, even digit count), so `auth.CertAuthenticator`'s
    exact-string ledger lookup would then reject an otherwise valid,
    registered cert as "not registered" — found live during p3/plan.md
    Step 1 as an intermittently failing test, confirmed to be a real
    handshake-level mismatch, not test flakiness. Loops (bounded) until it
    reproduces the odd-length case, then proves that cert authenticates."""
    for _ in range(500):
        signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
        if len(format(signed.certificate.serial_number, "x")) % 2 == 1:
            break
    else:
        pytest.fail("did not generate a serial needing zero-padding in 500 tries")

    fixture.register(signed, NODE_UUID)

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 202, payload
    assert payload["state"] == "queued"


def test_wrapper_revoked_cert_call_fails_with_forbidden_envelope(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    fixture.ledger.revoke(signed.serial_hex)
    conf_path = fixture.write_client_conf(cert_path, key_path)

    result = fixture.run_wrapper(conf_path, ["ask", "--no-wait"], stdin_text="hi")

    assert result.returncode != 0
    assert "forbidden" in result.stderr


# --- p4/plan.md Step 3: the human listener under real TLS, alongside the
# node listener in the same process, sharing the same store/worker — same
# split main.py runs in production. Covers the README_DEV lesson-2 real-
# stack requirement for the new surface, not just the fake-authenticate
# unit tests in cagent/tests/test_server.py.


def test_node_mtls_path_still_works_unchanged_with_human_listener_present(fixture):
    """The human listener existing alongside the node listener must not
    perturb the node path at all — same assertion as the very first test
    in this file, re-run with both listeners up."""
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)

    status, payload = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})

    assert status == 202
    assert payload["state"] == "queued"


def test_node_listener_refuses_a_certless_connection(fixture):
    with pytest.raises(ssl.SSLError):
        fixture.request_node_without_client_cert("POST", "/requests")


def test_human_listener_accepts_the_good_token(fixture):
    status, payload = fixture.human_request(HUMAN_TOKEN, "POST", "/requests", {"message": "hi"})
    assert status == 202
    assert payload["state"] == "queued"


def test_human_listener_rejects_a_bad_token(fixture):
    status, payload = fixture.human_request("wrong-token", "POST", "/requests", {"message": "hi"})
    assert status == 401
    assert payload["error"]["code"] == "unauthorized"


def test_human_listener_rejects_an_absent_token(fixture):
    status, payload = fixture.human_request(None, "POST", "/requests", {"message": "hi"})
    assert status == 401
    assert payload["error"]["code"] == "unauthorized"


def test_human_listener_does_not_require_a_client_cert(fixture):
    """The connection itself (no client cert offered) must succeed at the
    TLS layer — the human_request helper never loads a client cert, so a
    non-401 HTTP response here (vs. request_node_without_client_cert's
    ssl.SSLError) is the proof."""
    status, payload = fixture.human_request(HUMAN_TOKEN, "GET", "/sessions")
    assert status == 200
    assert payload == []


def test_human_and_node_identities_land_in_evidence_in_contract_shapes(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    status, node_created = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})
    assert status == 202

    status, human_created = fixture.human_request(HUMAN_TOKEN, "POST", "/requests", {"message": "hi"})
    assert status == 202

    status, node_payload = fixture.request(cert_path, key_path, "GET", f"/requests/{node_created['request_id']}")
    assert node_payload["identity"] == {"class": "node", "uuid": NODE_UUID, "cert_serial": signed.serial_hex}

    status, human_payload = fixture.human_request(HUMAN_TOKEN, "GET", f"/requests/{human_created['request_id']}")
    assert human_payload["identity"] == {"class": "human", "name": "operator"}


def test_human_can_read_a_node_created_request_but_not_continue_it(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    status, node_created = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})
    assert status == 202

    status, payload = fixture.human_request(HUMAN_TOKEN, "GET", f"/requests/{node_created['request_id']}")
    assert status == 200
    assert payload["identity"]["class"] == "node"

    status, payload = fixture.human_request(
        HUMAN_TOKEN, "POST", f"/sessions/{node_created['session_id']}/requests", {"message": "intrude"}
    )
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_node_cannot_read_a_human_created_request(fixture):
    status, human_created = fixture.human_request(HUMAN_TOKEN, "POST", "/requests", {"message": "hi"})
    assert status == 202

    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    status, payload = fixture.request(cert_path, key_path, "GET", f"/requests/{human_created['request_id']}")
    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_human_lists_all_sessions_node_only_its_own(fixture):
    signed, key_path, cert_path = fixture.sign_node_cert(NODE_UUID)
    fixture.register(signed, NODE_UUID)
    status, node_created = fixture.request(cert_path, key_path, "POST", "/requests", {"message": "hi"})
    assert status == 202
    status, human_created = fixture.human_request(HUMAN_TOKEN, "POST", "/requests", {"message": "hi"})
    assert status == 202

    status, node_sessions = fixture.request(cert_path, key_path, "GET", "/sessions")
    assert {s["session_id"] for s in node_sessions} == {node_created["session_id"]}

    status, human_sessions = fixture.human_request(HUMAN_TOKEN, "GET", "/sessions")
    session_ids = {s["session_id"] for s in human_sessions}
    assert node_created["session_id"] in session_ids
    assert human_created["session_id"] in session_ids


def test_human_listener_serves_the_chat_ui_at_root(fixture):
    status, body = fixture.human_request(HUMAN_TOKEN, "GET", "/")
    assert status == 200
    assert b"cluster-agent" in body
