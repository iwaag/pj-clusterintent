"""Entrypoint: `uv run --project cagent cagent-api`.

See p2/contract.md for the API this serves (mTLS identity; p1/contract.md
for the resources/state-machine parts unchanged since Phase 1) and
cagent/README.md for how to run it together with the Step 2/3 CA + ledger
tooling.

This is now the only cagent process. The three doors each resolve their own
role from `cagent/agents.toml`, so which backend serves which door is
configuration — and every answer's run record names it.
"""

from __future__ import annotations

import logging
import os
import ssl
import threading
from pathlib import Path

from .auth import CertAuthenticator, NoAuthenticator, TokenAuthenticator
from .evidence import EvidenceWriter
from .ledger import Ledger
from .agent_runner import AgentConfigError, build_runner
from .node_resolver import NautobotNodeResolver
from .server import build_server
from .store import scan_and_load
from .worker import TURN_TIMEOUT_SECONDS, Worker

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_DIR = Path.home() / ".local" / "state" / "cagent" / "evidence"
DEFAULT_LEDGER_PATH = Path.home() / ".local" / "state" / "cagent" / "ledger" / "ledger.jsonl"
DEFAULT_CA_DIR = REPO_ROOT / ".local" / "cagent-ca"
DEFAULT_NCTL_TOML = REPO_ROOT / "nctl.toml"
DEFAULT_HUMAN_TOKEN_FILE = Path.home() / ".local" / "state" / "cagent" / "human_token"
DEFAULT_WINDOW_GUIDE = REPO_ROOT / "cagent" / "window" / "GUIDE.md"
DEFAULT_AGENTS_CONFIG = REPO_ROOT / "cagent" / "agents.toml"
DEFAULT_AGENTS_OVERLAY = REPO_ROOT / "cagent" / ".local" / "agents.local.toml"
# Per-role instructions, read from disk on every request (agent_runner).
AGENT_INSTRUCTIONS = REPO_ROOT / "cagent" / "agent" / "AGENTS.md"
WINDOW_INSTRUCTIONS = REPO_ROOT / "cagent" / "window" / "AGENTS.md"


def _build_node_ssl_context(ca_cert: Path, server_cert: Path, server_key: Path) -> ssl.SSLContext:
    """CERT_OPTIONAL, not CERT_REQUIRED: the TLS handshake itself must not
    reject a certless client, so an unenrolled node can still reach the
    one unauthenticated route (`GET /llms.txt`, a bootstrap doc pointing at
    where its node certificate should live). Every other route is
    unaffected — `CertAuthenticator` (auth.py) still 401s a missing/invalid
    cert at the application layer, so nothing gets weaker access than
    before, only /llms.txt gets reachable without one."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(server_cert), str(server_key))
    ctx.verify_mode = ssl.CERT_OPTIONAL
    ctx.load_verify_locations(str(ca_cert))
    return ctx


def _build_human_ssl_context(server_cert: Path, server_key: Path) -> ssl.SSLContext:
    """Server-only TLS, no client cert required (p4/contract.md) — the
    human listener authenticates via bearer token instead."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(server_cert), str(server_key))
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _read_human_token(token_file: Path) -> str:
    """Refuse-don't-fallback: there is no plaintext/no-auth mode for the
    human listener."""
    if not token_file.exists():
        raise SystemExit(
            f"human token file not found: {token_file} — generate one before starting the "
            "human listener, e.g.:\n"
            f"  python3 -c \"import secrets; print(secrets.token_urlsafe(32))\" > {token_file}\n"
            f"  chmod 600 {token_file}"
        )
    token = token_file.read_text().strip()
    if not token:
        raise SystemExit(f"human token file is empty: {token_file}")
    return token


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("cagent_api.main")

    host = os.environ.get("CAGENT_API_HOST", "0.0.0.0")
    port = int(os.environ.get("CAGENT_API_PORT", "8788"))
    human_port = int(os.environ.get("CAGENT_HUMAN_PORT", "8789"))
    human_token_file = Path(os.environ.get("CAGENT_HUMAN_TOKEN_FILE", str(DEFAULT_HUMAN_TOKEN_FILE)))
    human_name = os.environ.get("CAGENT_HUMAN_NAME", "operator")
    window_port = int(os.environ.get("CAGENT_WINDOW_PORT", "8790"))
    window_guide = Path(os.environ.get("CAGENT_WINDOW_GUIDE", str(DEFAULT_WINDOW_GUIDE)))
    agents_config = Path(os.environ.get("CAGENT_AGENTS_CONFIG", str(DEFAULT_AGENTS_CONFIG)))
    agents_overlay = Path(os.environ.get("CAGENT_AGENTS_OVERLAY", str(DEFAULT_AGENTS_OVERLAY)))
    directory = Path(os.environ.get("CAGENT_DIRECTORY", str(REPO_ROOT)))
    evidence_dir = Path(os.environ.get("CAGENT_EVIDENCE_DIR", str(DEFAULT_EVIDENCE_DIR)))
    ledger_path = Path(os.environ.get("CAGENT_LEDGER_PATH", str(DEFAULT_LEDGER_PATH)))
    ca_dir = Path(os.environ.get("CAGENT_CA_DIR", str(DEFAULT_CA_DIR)))
    server_cert = Path(os.environ.get("CAGENT_TLS_SERVER_CERT", str(ca_dir / "server_cert.pem")))
    server_key = Path(os.environ.get("CAGENT_TLS_SERVER_KEY", str(ca_dir / "server_key.pem")))
    nctl_toml = Path(os.environ.get("CAGENT_NCTL_TOML", str(DEFAULT_NCTL_TOML)))

    human_token = _read_human_token(human_token_file)

    evidence = EvidenceWriter(evidence_dir)
    store, newly_interrupted = scan_and_load(evidence)
    if newly_interrupted:
        log.warning(
            "startup scan: marked %d non-terminal request(s) as interrupted: %s",
            len(newly_interrupted), ", ".join(newly_interrupted),
        )

    def runner_for(role: str, instructions: Path):
        return build_runner(
            role,
            config_path=agents_config,
            overlay_path=agents_overlay,
            working_dir=directory,
            instructions_path=instructions,
            turn_timeout=TURN_TIMEOUT_SECONDS,
        )

    # Resolution failures are fatal at startup rather than per request: a door
    # whose profile does not resolve has no backend, and answering "the agent
    # is misconfigured" once at boot beats discovering it on someone's message.
    try:
        node_runner = runner_for("node", AGENT_INSTRUCTIONS)
        human_runner = runner_for("human", AGENT_INSTRUCTIONS)
        window_runner = runner_for("window", WINDOW_INSTRUCTIONS)
    except AgentConfigError as error:
        raise SystemExit(f"agent configuration is unusable: {error}") from error

    worker = Worker(store, node_runner)
    worker.start()

    ledger = Ledger(ledger_path)
    node_resolver = NautobotNodeResolver.from_nctl_toml(nctl_toml)
    node_authenticate = CertAuthenticator(ledger, node_resolver)
    node_ssl_context = _build_node_ssl_context(ca_dir / "ca_cert.pem", server_cert, server_key)
    httpd = build_server(host, port, store, node_runner, worker, node_authenticate, ssl_context=node_ssl_context)

    human_authenticate = TokenAuthenticator(human_token, human_name)
    human_ssl_context = _build_human_ssl_context(server_cert, server_key)
    human_worker = Worker(store, human_runner)
    human_worker.start()
    human_httpd = build_server(
        host, human_port, store, human_runner, human_worker, human_authenticate,
        ssl_context=human_ssl_context, serve_ui=True,
    )
    human_thread = threading.Thread(target=human_httpd.serve_forever, daemon=True)
    human_thread.start()

    # Window entrance: no authentication and no TLS. There is no credential
    # to protect in transit and the guide is meant to be fetchable with a
    # bare curl; what keeps this door safe is the tool set its runner offers
    # (`agent_runner.window_tools`: read, list, read-only nctl, and the two
    # incident tools — no shell at all), not an identity check. It gets its
    # own runner and its own worker thread — a shared worker would run window
    # turns on the authenticated tool set — but the same store and evidence,
    # so a window answer leaves the same run record as any other request.
    window_worker = Worker(store, window_runner)
    window_worker.start()
    window_httpd = build_server(
        host, window_port, store, window_runner, window_worker, NoAuthenticator(),
        guide_path=window_guide,
    )
    window_thread = threading.Thread(target=window_httpd.serve_forever, daemon=True)
    window_thread.start()

    log.info(
        "cluster-agent API listening on https://%s:%s (node entrance, mTLS required), "
        "https://%s:%s (human entrance, bearer token) and http://%s:%s (window entrance, "
        "unauthenticated) — node/human=%s, window=%s, directory=%s, evidence=%s, ledger=%s",
        host, port, host, human_port, host, window_port,
        node_runner.identity(), window_runner.identity(),
        directory, evidence_dir, ledger_path,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
