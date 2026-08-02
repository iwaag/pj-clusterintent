from __future__ import annotations

import pytest

from cagent_api import ca, ca_cli


def test_init_then_sign_node_end_to_end(tmp_path, capsys):
    ca_dir = tmp_path / "ca"
    ca_cli.main(["init", "--dir", str(ca_dir), "--cn", "test-ca", "--days", "10"])
    assert (ca_dir / ca_cli.CA_KEY_NAME).exists()
    assert (ca_dir / ca_cli.CA_CERT_NAME).exists()

    node_key = ca.generate_key()
    csr = ca.generate_csr(node_key, "self-claimed")
    csr_path = tmp_path / "node.csr"
    csr_path.write_bytes(ca.csr_to_pem(csr))
    out_cert = tmp_path / "node_cert.pem"
    node_uuid = "c82421c3-c42a-4bea-91ce-7468ae8a249c"

    ca_cli.main([
        "sign-node", "--ca-dir", str(ca_dir), "--csr", str(csr_path),
        "--uuid", node_uuid, "--out", str(out_cert),
    ])
    capsys.readouterr()

    signed = ca.load_cert_pem(out_cert.read_bytes())
    assert ca.san_uri_to_node_uuid(
        signed.extensions.get_extension_for_class(
            __import__("cryptography.x509", fromlist=["SubjectAlternativeName"]).SubjectAlternativeName
        ).value.get_values_for_type(
            __import__("cryptography.x509", fromlist=["UniformResourceIdentifier"]).UniformResourceIdentifier
        )[0]
    ) == node_uuid


def test_init_refuses_to_overwrite_existing_ca_without_force(tmp_path):
    ca_dir = tmp_path / "ca"
    ca_cli.main(["init", "--dir", str(ca_dir)])
    with pytest.raises(SystemExit):
        ca_cli.main(["init", "--dir", str(ca_dir)])
    # --force does overwrite.
    ca_cli.main(["init", "--dir", str(ca_dir), "--force"])


def test_ca_key_file_is_written_owner_only(tmp_path):
    ca_dir = tmp_path / "ca"
    ca_cli.main(["init", "--dir", str(ca_dir)])
    mode = (ca_dir / ca_cli.CA_KEY_NAME).stat().st_mode & 0o777
    assert mode == 0o600


def test_sign_node_requires_existing_ca(tmp_path):
    node_key = ca.generate_key()
    csr = ca.generate_csr(node_key, "x")
    csr_path = tmp_path / "node.csr"
    csr_path.write_bytes(ca.csr_to_pem(csr))
    with pytest.raises(SystemExit):
        ca_cli.main([
            "sign-node", "--ca-dir", str(tmp_path / "missing"), "--csr", str(csr_path),
            "--uuid", "c82421c3-c42a-4bea-91ce-7468ae8a249c", "--out", str(tmp_path / "out.pem"),
        ])
