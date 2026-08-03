from __future__ import annotations

import ssl

from cagent_api import ca
from cagent_api.main import _build_node_ssl_context


def test_node_ssl_context_is_cert_optional_not_required(tmp_path):
    """CERT_REQUIRED would reject the TLS handshake itself before an
    unenrolled node could ever reach `GET /llms.txt`. CERT_OPTIONAL lets the
    handshake succeed without a client cert; `CertAuthenticator` (auth.py)
    still 401s every other route at the application layer."""
    ca_key, ca_signed = ca.build_ca("test-ca", valid_days=10)
    ca_cert_path = tmp_path / "ca_cert.pem"
    ca_cert_path.write_bytes(ca.cert_to_pem(ca_signed.certificate))

    server_key = ca.generate_key()
    signed = ca.sign_server_cert(
        ca_key, ca_signed.certificate, server_key, "cagent-api",
        dns_sans=["localhost"], ip_sans=["127.0.0.1"], valid_days=30,
    )
    server_cert_path = tmp_path / "server_cert.pem"
    server_key_path = tmp_path / "server_key.pem"
    server_cert_path.write_bytes(ca.cert_to_pem(signed.certificate))
    server_key_path.write_bytes(ca.key_to_pem(server_key))

    ctx = _build_node_ssl_context(ca_cert_path, server_cert_path, server_key_path)
    assert ctx.verify_mode == ssl.CERT_OPTIONAL
