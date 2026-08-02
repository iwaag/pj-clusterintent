"""Local CA + certificate signing (Phase 2, see p2/contract.md, p2/mtls_notes.md).

Pure functions over `cryptography` objects — no filesystem or CLI concerns
here (those live in `ca_cli.py`). Kept out of `cagent_api.server`'s import
graph deliberately: the running API server only needs stdlib `ssl` at
request time (see mtls_notes.md), so `cryptography` stays a dev-tooling
dependency, not a runtime one.

Identity encoding: a node's client certificate carries its DesiredNode UUID
as a URI SAN, `urn:clusterintent:node:<uuid>` (p2/contract.md). The UUID is
always an explicit caller-supplied argument to `sign_node_cert` — never
parsed from the CSR's self-claimed subject fields, per the plan's
enrollment rule.
"""

from __future__ import annotations

import datetime
import uuid as uuid_mod
from dataclasses import dataclass

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

NODE_URN_PREFIX = "urn:clusterintent:node:"

EllipticCurvePrivateKey = ec.EllipticCurvePrivateKey


class CaError(Exception):
    pass


def node_uuid_to_san_uri(node_uuid: str) -> str:
    # Round-trips through uuid.UUID so a malformed value fails loudly here,
    # not later inside a certificate nobody re-validates.
    return f"{NODE_URN_PREFIX}{uuid_mod.UUID(node_uuid)}"


def san_uri_to_node_uuid(san_uri: str) -> str:
    if not san_uri.startswith(NODE_URN_PREFIX):
        raise CaError(f"not a clusterintent node URI SAN: {san_uri!r}")
    return str(uuid_mod.UUID(san_uri[len(NODE_URN_PREFIX):]))


def generate_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@dataclass(frozen=True)
class SignedCert:
    certificate: x509.Certificate
    serial_hex: str
    fingerprint_hex: str
    not_before: datetime.datetime
    not_after: datetime.datetime


def _wrap(cert: x509.Certificate) -> SignedCert:
    return SignedCert(
        certificate=cert,
        serial_hex=format(cert.serial_number, "x"),
        fingerprint_hex=public_key_fingerprint(cert.public_key()),
        not_before=cert.not_valid_before_utc,
        not_after=cert.not_valid_after_utc,
    )


def public_key_fingerprint(public_key) -> str:
    """SHA-256 of the DER SubjectPublicKeyInfo, hex-encoded — a public,
    non-secret identifier suitable for ledger/evidence storage."""
    der = public_key.public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    digest = hashes.Hash(hashes.SHA256())
    digest.update(der)
    return digest.finalize().hex()


def build_ca(cn: str, valid_days: int) -> tuple[ec.EllipticCurvePrivateKey, SignedCert]:
    key = generate_key()
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=valid_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    return key, _wrap(cert)


def sign_server_cert(
    ca_key: ec.EllipticCurvePrivateKey,
    ca_cert: x509.Certificate,
    key: ec.EllipticCurvePrivateKey,
    cn: str,
    dns_sans: list[str],
    ip_sans: list[str],
    valid_days: int,
) -> SignedCert:
    import ipaddress

    san_entries: list[x509.GeneralName] = [x509.DNSName(name) for name in dns_sans]
    san_entries += [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ip_sans]
    return _wrap(_sign_leaf(
        ca_key, ca_cert, key.public_key(), cn, san_entries, valid_days,
        extended_key_usage=[x509.oid.ExtendedKeyUsageOID.SERVER_AUTH],
    ))


def sign_node_cert(
    ca_key: ec.EllipticCurvePrivateKey,
    ca_cert: x509.Certificate,
    csr: x509.CertificateSigningRequest,
    node_uuid: str,
    cn: str,
    valid_days: int,
) -> SignedCert:
    if not csr.is_signature_valid:
        raise CaError("CSR signature does not verify against its own public key")
    san_entries = [x509.UniformResourceIdentifier(node_uuid_to_san_uri(node_uuid))]
    return _wrap(_sign_leaf(
        ca_key, ca_cert, csr.public_key(), cn, san_entries, valid_days,
        extended_key_usage=[x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH],
    ))


def sign_node_cert_for_test(
    ca_key: ec.EllipticCurvePrivateKey,
    ca_cert: x509.Certificate,
    key: ec.EllipticCurvePrivateKey,
    node_uuid: str | None,
    cn: str,
    valid_days: int = 365,
    not_before: datetime.datetime | None = None,
    not_after: datetime.datetime | None = None,
) -> SignedCert:
    """Test/dev-only helper that skips the CSR round trip (mints directly
    from a keypair) and allows an explicit invalid validity window — used by
    the Step 5a conformance test to mint an expired certificate, which the
    CSR-based `sign_node_cert` path deliberately cannot do (real enrollment
    never wants an expired cert on purpose)."""
    san_entries = []
    if node_uuid is not None:
        san_entries = [x509.UniformResourceIdentifier(node_uuid_to_san_uri(node_uuid))]
    return _wrap(_sign_leaf(
        ca_key, ca_cert, key.public_key(), cn, san_entries, valid_days,
        extended_key_usage=[x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH],
        not_before=not_before, not_after=not_after,
    ))


def _sign_leaf(
    ca_key, ca_cert, public_key, cn, san_entries, valid_days,
    extended_key_usage, not_before=None, not_after=None,
) -> x509.Certificate:
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
        .issuer_name(ca_cert.subject)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before or (now - datetime.timedelta(minutes=5)))
        .not_valid_after(not_after or (now + datetime.timedelta(days=valid_days)))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage(extended_key_usage), critical=False)
    )
    if san_entries:
        builder = builder.add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
    return builder.sign(ca_key, hashes.SHA256())


def generate_csr(key: ec.EllipticCurvePrivateKey, cn: str) -> x509.CertificateSigningRequest:
    return (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
        .sign(key, hashes.SHA256())
    )


def key_to_pem(key: ec.EllipticCurvePrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def cert_to_pem(cert: x509.Certificate) -> bytes:
    return cert.public_bytes(serialization.Encoding.PEM)


def csr_to_pem(csr: x509.CertificateSigningRequest) -> bytes:
    return csr.public_bytes(serialization.Encoding.PEM)


def load_key_pem(data: bytes) -> ec.EllipticCurvePrivateKey:
    return serialization.load_pem_private_key(data, password=None)


def load_cert_pem(data: bytes) -> x509.Certificate:
    return x509.load_pem_x509_certificate(data)


def load_csr_pem(data: bytes) -> x509.CertificateSigningRequest:
    return x509.load_pem_x509_csr(data)
