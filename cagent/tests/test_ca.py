from __future__ import annotations

import datetime

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from cagent_api import ca


def test_build_ca_is_self_signed_and_can_sign():
    key, signed = ca.build_ca("test-ca", valid_days=10)
    cert = signed.certificate
    key.public_key().verify(
        cert.signature, cert.tbs_certificate_bytes, ec.ECDSA(cert.signature_hash_algorithm)
    )
    assert cert.subject == cert.issuer


def test_sign_node_cert_carries_uuid_in_san_and_uses_csr_public_key():
    ca_key, ca_signed = ca.build_ca("test-ca", valid_days=10)
    node_key = ca.generate_key()
    csr = ca.generate_csr(node_key, "some-self-claimed-slug")
    node_uuid = "c82421c3-c42a-4bea-91ce-7468ae8a249c"

    signed = ca.sign_node_cert(ca_key, ca_signed.certificate, csr, node_uuid, "cagent-node", 30)

    san = signed.certificate.extensions.get_extension_for_class(
        __import__("cryptography.x509", fromlist=["SubjectAlternativeName"]).SubjectAlternativeName
    ).value
    uris = san.get_values_for_type(
        __import__("cryptography.x509", fromlist=["UniformResourceIdentifier"]).UniformResourceIdentifier
    )
    assert uris == [f"urn:clusterintent:node:{node_uuid}"]
    assert ca.san_uri_to_node_uuid(uris[0]) == node_uuid
    # The signed cert's public key must be the CSR's (never a self-claimed subject).
    assert signed.certificate.public_key().public_numbers() == node_key.public_key().public_numbers()


def test_sign_node_cert_ignores_csr_self_claimed_subject():
    ca_key, ca_signed = ca.build_ca("test-ca", valid_days=10)
    node_key = ca.generate_key()
    csr = ca.generate_csr(node_key, "attacker-claimed-cn")

    signed = ca.sign_node_cert(
        ca_key, ca_signed.certificate, csr, "c82421c3-c42a-4bea-91ce-7468ae8a249c", "cagent-node", 30
    )

    assert signed.certificate.subject.rfc4514_string() == "CN=cagent-node"


def test_sign_server_cert_carries_dns_and_ip_sans():
    ca_key, ca_signed = ca.build_ca("test-ca", valid_days=10)
    key = ca.generate_key()

    signed = ca.sign_server_cert(
        ca_key, ca_signed.certificate, key, "cagent-api",
        dns_sans=["agstudio.local"], ip_sans=["192.168.0.100"], valid_days=30,
    )

    from cryptography import x509
    san = signed.certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert san.get_values_for_type(x509.DNSName) == ["agstudio.local"]
    assert [str(ip) for ip in san.get_values_for_type(x509.IPAddress)] == ["192.168.0.100"]


def test_sign_node_cert_for_test_can_mint_an_expired_cert():
    ca_key, ca_signed = ca.build_ca("test-ca", valid_days=10)
    key = ca.generate_key()
    now = datetime.datetime.now(datetime.timezone.utc)

    signed = ca.sign_node_cert_for_test(
        ca_key, ca_signed.certificate, key, "c82421c3-c42a-4bea-91ce-7468ae8a249c", "expired-node",
        not_before=now - datetime.timedelta(days=10),
        not_after=now - datetime.timedelta(days=1),
    )

    assert signed.not_after < now


def test_node_uuid_to_san_uri_rejects_malformed_uuid():
    with pytest.raises(ValueError):
        ca.node_uuid_to_san_uri("not-a-uuid")


def test_san_uri_to_node_uuid_rejects_wrong_prefix():
    with pytest.raises(ca.CaError):
        ca.san_uri_to_node_uuid("urn:something-else:node:c82421c3-c42a-4bea-91ce-7468ae8a249c")


def test_public_key_fingerprint_is_stable_for_same_key_and_differs_across_keys():
    key1 = ca.generate_key()
    key2 = ca.generate_key()
    fp1a = ca.public_key_fingerprint(key1.public_key())
    fp1b = ca.public_key_fingerprint(key1.public_key())
    fp2 = ca.public_key_fingerprint(key2.public_key())
    assert fp1a == fp1b
    assert fp1a != fp2
    assert len(fp1a) == 64  # sha256 hex
