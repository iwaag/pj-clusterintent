"""Entrypoint: `uv run --project cagent cagent-api`.

See p2/contract.md for the API this serves (mTLS identity; p1/contract.md
for the resources/state-machine parts unchanged since Phase 1) and
cagent/README.md for how to run it together with the OpenCode instance and
the Step 2/3 CA + ledger tooling.
"""

from __future__ import annotations

import logging
import os
import ssl
from pathlib import Path

from .auth import CertAuthenticator
from .evidence import EvidenceWriter
from .ledger import Ledger
from .node_resolver import NautobotNodeResolver
from .opencode_client import OpenCodeClient
from .server import build_server
from .store import scan_and_load
from .worker import Worker

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_DIR = Path.home() / ".local" / "state" / "cagent" / "evidence"
DEFAULT_LEDGER_PATH = Path.home() / ".local" / "state" / "cagent" / "ledger" / "ledger.jsonl"
DEFAULT_CA_DIR = REPO_ROOT / ".local" / "cagent-ca"
DEFAULT_NCTL_TOML = REPO_ROOT / "nctl.toml"


def _build_ssl_context(ca_cert: Path, server_cert: Path, server_key: Path) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(server_cert), str(server_key))
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(str(ca_cert))
    return ctx


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("cagent_api.main")

    host = os.environ.get("CAGENT_API_HOST", "0.0.0.0")
    port = int(os.environ.get("CAGENT_API_PORT", "8788"))
    opencode_url = os.environ.get("CAGENT_OPENCODE_URL", "http://127.0.0.1:4097")
    directory = os.environ.get("CAGENT_DIRECTORY", str(REPO_ROOT))
    evidence_dir = Path(os.environ.get("CAGENT_EVIDENCE_DIR", str(DEFAULT_EVIDENCE_DIR)))
    ledger_path = Path(os.environ.get("CAGENT_LEDGER_PATH", str(DEFAULT_LEDGER_PATH)))
    ca_dir = Path(os.environ.get("CAGENT_CA_DIR", str(DEFAULT_CA_DIR)))
    server_cert = Path(os.environ.get("CAGENT_TLS_SERVER_CERT", str(ca_dir / "server_cert.pem")))
    server_key = Path(os.environ.get("CAGENT_TLS_SERVER_KEY", str(ca_dir / "server_key.pem")))
    nctl_toml = Path(os.environ.get("CAGENT_NCTL_TOML", str(DEFAULT_NCTL_TOML)))

    evidence = EvidenceWriter(evidence_dir)
    store, newly_interrupted = scan_and_load(evidence)
    if newly_interrupted:
        log.warning(
            "startup scan: marked %d non-terminal request(s) as interrupted: %s",
            len(newly_interrupted), ", ".join(newly_interrupted),
        )

    opencode = OpenCodeClient(base_url=opencode_url, directory=directory)
    worker = Worker(store, opencode)
    worker.start()

    ledger = Ledger(ledger_path)
    node_resolver = NautobotNodeResolver.from_nctl_toml(nctl_toml)
    authenticate = CertAuthenticator(ledger, node_resolver)
    ssl_context = _build_ssl_context(ca_dir / "ca_cert.pem", server_cert, server_key)

    httpd = build_server(host, port, store, opencode, worker, authenticate, ssl_context=ssl_context)
    log.info(
        "cluster-agent API listening on https://%s:%s (mTLS required; opencode=%s, "
        "directory=%s, evidence=%s, ledger=%s)",
        host, port, opencode_url, directory, evidence_dir, ledger_path,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
