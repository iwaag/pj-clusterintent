"""`cagent-ca` console script: local CA init + signing (Phase 2).

CA private key and any signed node private key are secrets and never touch
this repo: CA material lives under `.local/cagent-ca/` (gitignored at the
superproject root). Node private keys are generated on-node and never leave
it (Step 5b) — this tool only ever sees a CSR (public key), never a node's
private key.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from . import ca

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CA_DIR = REPO_ROOT / ".local" / "cagent-ca"

CA_KEY_NAME = "ca_key.pem"
CA_CERT_NAME = "ca_cert.pem"


def _write_private(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _write_public(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _load_ca(ca_dir: Path) -> tuple[ca.EllipticCurvePrivateKey, "ca.x509.Certificate"]:
    key_path = ca_dir / CA_KEY_NAME
    cert_path = ca_dir / CA_CERT_NAME
    if not key_path.exists() or not cert_path.exists():
        raise SystemExit(f"no CA found at {ca_dir} — run `cagent-ca init` first")
    return ca.load_key_pem(key_path.read_bytes()), ca.load_cert_pem(cert_path.read_bytes())


def cmd_init(args: argparse.Namespace) -> None:
    ca_dir = Path(args.dir)
    key_path = ca_dir / CA_KEY_NAME
    cert_path = ca_dir / CA_CERT_NAME
    if (key_path.exists() or cert_path.exists()) and not args.force:
        raise SystemExit(
            f"CA already exists at {ca_dir} (use --force to overwrite — this invalidates "
            "every certificate signed by the old CA)"
        )
    key, signed = ca.build_ca(args.cn, args.days)
    _write_private(key_path, ca.key_to_pem(key))
    _write_public(cert_path, ca.cert_to_pem(signed.certificate))
    print(f"CA created at {ca_dir}")
    print(f"  serial={signed.serial_hex} not_after={signed.not_after.isoformat()}")


def cmd_sign_server(args: argparse.Namespace) -> None:
    ca_key, ca_cert = _load_ca(Path(args.ca_dir))
    key = ca.generate_key()
    signed = ca.sign_server_cert(
        ca_key, ca_cert, key, args.cn, args.dns or [], args.ip or [], args.days
    )
    _write_private(Path(args.out_key), ca.key_to_pem(key))
    _write_public(Path(args.out_cert), ca.cert_to_pem(signed.certificate))
    print(f"server cert written to {args.out_cert} (key: {args.out_key})")
    print(f"  serial={signed.serial_hex} not_after={signed.not_after.isoformat()}")


def cmd_sign_node(args: argparse.Namespace) -> None:
    ca_key, ca_cert = _load_ca(Path(args.ca_dir))
    csr = ca.load_csr_pem(Path(args.csr).read_bytes())
    signed = ca.sign_node_cert(ca_key, ca_cert, csr, args.uuid, args.cn, args.days)
    _write_public(Path(args.out), ca.cert_to_pem(signed.certificate))
    fingerprint = ca.public_key_fingerprint(csr.public_key())
    print(f"node cert written to {args.out}")
    print(f"  uuid={args.uuid}")
    print(f"  serial={signed.serial_hex}")
    print(f"  fingerprint={fingerprint}")
    print(f"  not_after={signed.not_after.isoformat()}")
    print(
        "Register this in the ledger:\n"
        f"  uv run --project cagent cagent-ledger register --uuid {args.uuid} "
        f"--serial {signed.serial_hex} --fingerprint {fingerprint} "
        f"--not-after {signed.not_after.isoformat()}"
    )


def cmd_show_ca(args: argparse.Namespace) -> None:
    _, ca_cert = _load_ca(Path(args.ca_dir))
    print(f"subject={ca_cert.subject.rfc4514_string()}")
    print(f"serial={format(ca_cert.serial_number, 'x')}")
    print(f"not_before={ca_cert.not_valid_before_utc.isoformat()}")
    print(f"not_after={ca_cert.not_valid_after_utc.isoformat()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cagent-ca", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create the local CA (once)")
    p_init.add_argument("--dir", default=str(DEFAULT_CA_DIR))
    p_init.add_argument("--cn", default="cagent-local-ca")
    p_init.add_argument("--days", type=int, default=1825)
    p_init.add_argument("--force", action="store_true", help="overwrite an existing CA")
    p_init.set_defaults(func=cmd_init)

    p_server = sub.add_parser("sign-server", help="mint the API server's own TLS cert")
    p_server.add_argument("--ca-dir", default=str(DEFAULT_CA_DIR))
    p_server.add_argument("--out-key", required=True)
    p_server.add_argument("--out-cert", required=True)
    p_server.add_argument("--cn", default="cagent-api")
    p_server.add_argument("--dns", action="append", help="DNS SAN (repeatable)")
    p_server.add_argument("--ip", action="append", help="IP SAN (repeatable)")
    p_server.add_argument("--days", type=int, default=365)
    p_server.set_defaults(func=cmd_sign_server)

    p_node = sub.add_parser("sign-node", help="sign a node's CSR bound to its DesiredNode UUID")
    p_node.add_argument("--ca-dir", default=str(DEFAULT_CA_DIR))
    p_node.add_argument("--csr", required=True, help="path to the node's CSR (PEM)")
    p_node.add_argument("--uuid", required=True, help="DesiredNode UUID (operator-supplied, never from the CSR)")
    p_node.add_argument("--cn", default="cagent-node")
    p_node.add_argument("--out", required=True, help="where to write the signed cert (PEM)")
    p_node.add_argument("--days", type=int, default=365)
    p_node.set_defaults(func=cmd_sign_node)

    p_show = sub.add_parser("show-ca", help="print CA cert details")
    p_show.add_argument("--ca-dir", default=str(DEFAULT_CA_DIR))
    p_show.set_defaults(func=cmd_show_ca)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    args.func(args)


if __name__ == "__main__":
    main()
