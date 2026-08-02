"""Entrypoint: `uv run --project cagent cagent-api`.

See p1/contract.md for the API this serves and cagent/README.md for how to
run it together with the Step 2 OpenCode instance.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .evidence import EvidenceWriter
from .opencode_client import OpenCodeClient
from .server import build_server
from .store import scan_and_load
from .worker import Worker

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_DIR = Path.home() / ".local" / "state" / "cagent" / "evidence"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("cagent_api.main")

    host = os.environ.get("CAGENT_API_HOST", "127.0.0.1")
    port = int(os.environ.get("CAGENT_API_PORT", "8788"))
    opencode_url = os.environ.get("CAGENT_OPENCODE_URL", "http://127.0.0.1:4097")
    directory = os.environ.get("CAGENT_DIRECTORY", str(REPO_ROOT))
    evidence_dir = Path(os.environ.get("CAGENT_EVIDENCE_DIR", str(DEFAULT_EVIDENCE_DIR)))

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

    httpd = build_server(host, port, store, opencode, worker)
    log.info(
        "cluster-agent API listening on http://%s:%s (opencode=%s, directory=%s, evidence=%s)",
        host, port, opencode_url, directory, evidence_dir,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
