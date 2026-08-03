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
import ssl
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cagent" / "src"))

from cagent_api import ca  # noqa: E402
from cagent_api.auth import CertAuthenticator  # noqa: E402
from cagent_api.ledger import Ledger  # noqa: E402
from cagent_api.opencode_client import AssistantMessage, OpenCodeError  # noqa: E402
from cagent_api.server import build_server  # noqa: E402
from cagent_api.store import Store  # noqa: E402
from cagent_api.worker import Worker  # noqa: E402

NODE_UUID = "27818c12-fe15-4c9f-83d0-7949523f6c33"
OTHER_NODE_UUID = "d3a4b6f0-6b41-4e6a-9a4a-1b2c3d4e5f60"
PRUNED_NODE_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class _FakeOpenCode:
    """Minimal stand-in so this gate never depends on a real OpenCode
    process — the conversation itself is out of scope here."""

    def create_session(self, title: str) -> str:
        return "ses_conformance"

    def prompt_async(self, session_id: str, text: str) -> None:
        pass

    def count_assistant_messages(self, session_id: str) -> int:
        return 1

    def latest_assistant_message(self, session_id: str):
        return AssistantMessage(completed=True, text="ok", error_name=None, is_final_step=True)

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

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

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
