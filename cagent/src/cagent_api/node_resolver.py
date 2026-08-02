"""Live DesiredNode validity check against Nautobot (p2/contract.md's
third connect-time check). nintent/Nautobot keeps owning DesiredNode
existence/validity; this module only reads it, never caches it across
requests — "check it live" per the roadmap's ledger/nintent separation, and
what makes `nctl prune` de-facto revocation actually true without any
extra step.

Uses stdlib `urllib.request` rather than `nctl_core`'s `httpx`-based
`NautobotClient`: cagent is a separate, independent project (not a
dependency of nctl, and not vice versa — see README_DEV's `nctl serve` note
on why cluster-agent-shaped code doesn't live inside nctl), and one GraphQL
POST doesn't warrant pulling in a new runtime dependency or importing
across project boundaries. Reads the same `nctl.toml` config file nctl
itself uses (`[nautobot] url`/`token_env`/`token_file`) so there is exactly
one Nautobot-connection config surface, not two.
"""

from __future__ import annotations

import json
import os
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

GRAPHQL_QUERY = "{ desired_nodes { id lifecycle } }"
INVALID_LIFECYCLES = {"retired"}


class NodeResolverError(Exception):
    pass


def load_nautobot_connection(nctl_toml_path: Path) -> tuple[str, str | None]:
    data = tomllib.loads(nctl_toml_path.read_text())
    nautobot = data["nautobot"]
    url = str(nautobot["url"]).rstrip("/")
    token = None
    token_env = nautobot.get("token_env")
    if token_env:
        token = os.environ.get(token_env)
    if not token:
        token_file = nautobot.get("token_file")
        if token_file:
            token = Path(token_file).expanduser().read_text().strip()
    return url, token


class NautobotNodeResolver:
    def __init__(self, url: str, token: str | None, timeout: float = 5.0) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout

    @classmethod
    def from_nctl_toml(cls, path: Path) -> "NautobotNodeResolver":
        url, token = load_nautobot_connection(path)
        return cls(url, token)

    def is_valid(self, node_uuid: str) -> bool:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        req = urllib.request.Request(
            f"{self.url}/api/graphql/",
            data=json.dumps({"query": GRAPHQL_QUERY}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise NodeResolverError(f"cannot reach Nautobot at {self.url}: {exc}") from exc
        if body.get("errors"):
            raise NodeResolverError(f"GraphQL errors from Nautobot: {body['errors']}")

        for node in body["data"]["desired_nodes"]:
            if node["id"] == node_uuid:
                return (node.get("lifecycle") or "").lower() not in INVALID_LIFECYCLES
        return False
