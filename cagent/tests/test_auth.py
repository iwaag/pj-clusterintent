from __future__ import annotations

import pytest

from cagent_api.auth import AuthError, CertAuthenticator, extract_node_identity
from cagent_api.ledger import Ledger
from cagent_api.node_resolver import NodeResolverError

UUID = "c82421c3-c42a-4bea-91ce-7468ae8a249c"


def _peercert(uuid=UUID, serial="ABCDEF"):
    return {
        "subjectAltName": (("URI", f"urn:clusterintent:node:{uuid}"),),
        "serialNumber": serial,
    }


def test_extract_node_identity_parses_uri_san_and_lowercases_serial():
    node_uuid, serial = extract_node_identity(_peercert())
    assert node_uuid == UUID
    assert serial == "abcdef"


def test_extract_node_identity_rejects_missing_cert():
    with pytest.raises(AuthError) as exc_info:
        extract_node_identity(None)
    assert exc_info.value.status == 401


def test_extract_node_identity_rejects_cert_without_node_san():
    with pytest.raises(AuthError) as exc_info:
        extract_node_identity({"subjectAltName": (("DNS", "example.com"),), "serialNumber": "AB"})
    assert exc_info.value.status == 401


class _Handler:
    """Stand-in for a real `BaseHTTPRequestHandler`: only `.connection.getpeercert()` is used."""

    def __init__(self, peercert):
        self._peercert = peercert
        self.connection = self

    def getpeercert(self):
        return self._peercert


class FakeNodeResolver:
    def __init__(self, valid_uuids):
        self.valid_uuids = valid_uuids

    def is_valid(self, node_uuid):
        return node_uuid in self.valid_uuids


class FailingNodeResolver:
    def is_valid(self, node_uuid):
        raise NodeResolverError("nautobot down")


def test_cert_authenticator_accepts_registered_active_valid_node(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "abcdef", "fp", "2027-01-01T00:00:00+00:00")
    authenticator = CertAuthenticator(ledger, FakeNodeResolver({UUID}))

    identity = authenticator(_Handler(_peercert()))

    assert identity.identity_class == "node"
    assert identity.uuid == UUID
    assert identity.cert_serial == "abcdef"


def test_cert_authenticator_rejects_unregistered_serial(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    authenticator = CertAuthenticator(ledger, FakeNodeResolver({UUID}))

    with pytest.raises(AuthError) as exc_info:
        authenticator(_Handler(_peercert()))
    assert exc_info.value.status == 403


def test_cert_authenticator_rejects_revoked_serial(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "abcdef", "fp", "2027-01-01T00:00:00+00:00")
    ledger.revoke("abcdef")
    authenticator = CertAuthenticator(ledger, FakeNodeResolver({UUID}))

    with pytest.raises(AuthError) as exc_info:
        authenticator(_Handler(_peercert()))
    assert exc_info.value.status == 403


def test_cert_authenticator_rejects_invalid_desired_node(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "abcdef", "fp", "2027-01-01T00:00:00+00:00")
    authenticator = CertAuthenticator(ledger, FakeNodeResolver(set()))

    with pytest.raises(AuthError) as exc_info:
        authenticator(_Handler(_peercert()))
    assert exc_info.value.status == 403


def test_cert_authenticator_surfaces_node_resolver_failure_as_502(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "abcdef", "fp", "2027-01-01T00:00:00+00:00")
    authenticator = CertAuthenticator(ledger, FailingNodeResolver())

    with pytest.raises(AuthError) as exc_info:
        authenticator(_Handler(_peercert()))
    assert exc_info.value.status == 502
