"""Entrypoint: `uv run --project cagent cagent-api`.

See p1/contract.md for the API this serves and cagent/README.md for how to
run it together with the Step 2 OpenCode instance.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .opencode_client import OpenCodeClient
from .server import build_server
from .store import Store
from .worker import Worker

REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    host = os.environ.get("CAGENT_API_HOST", "127.0.0.1")
    port = int(os.environ.get("CAGENT_API_PORT", "8788"))
    opencode_url = os.environ.get("CAGENT_OPENCODE_URL", "http://127.0.0.1:4097")
    directory = os.environ.get("CAGENT_DIRECTORY", str(REPO_ROOT))

    store = Store()
    opencode = OpenCodeClient(base_url=opencode_url, directory=directory)
    worker = Worker(store, opencode)
    worker.start()

    httpd = build_server(host, port, store, opencode, worker)
    logging.getLogger("cagent_api.main").info(
        "cluster-agent API listening on http://%s:%s (opencode=%s, directory=%s)",
        host, port, opencode_url, directory,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
