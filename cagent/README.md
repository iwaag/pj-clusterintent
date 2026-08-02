# cagent

The cluster-agent. See [`devdocs/vision/cluster_agent/`](../devdocs/vision/cluster_agent/)
for the roadmap and the frozen contracts this implements
(`devdocs/vision/cluster_agent/p1/contract.md` for resources/state machine,
`p2/contract.md` for the Phase 2 mTLS identity/authorization delta —
Phase 2 is a breaking change: the Phase 1 identity-header stub is gone).

Three pieces:

- `opencode/` — a dedicated OpenCode instance, isolated from any node-agent
  instance. Loopback-only. Start with `./opencode/start.sh`.
- `src/cagent_api/` — the HTTP API server that proxies to the OpenCode
  instance above and implements the frozen contract. **As of Phase 2 this
  requires mTLS** — every request needs a client certificate signed by the
  local CA below, registered in the auth ledger. Run with:

  ```bash
  uv run --project cagent cagent-api
  ```

  Configuration is via environment variables (all optional):

  | variable | default | meaning |
  |---|---|---|
  | `CAGENT_API_HOST` | `0.0.0.0` | API listen host (moved off loopback in Phase 2 so LAN/VPN nodes can reach it) |
  | `CAGENT_API_PORT` | `8788` | API listen port |
  | `CAGENT_OPENCODE_URL` | `http://127.0.0.1:4097` | the OpenCode instance (always loopback, never exposed) |
  | `CAGENT_DIRECTORY` | superproject root | working directory passed to OpenCode on every call |
  | `CAGENT_EVIDENCE_DIR` | `~/.local/state/cagent/evidence` | durable per-request evidence |
  | `CAGENT_LEDGER_PATH` | `~/.local/state/cagent/ledger/ledger.jsonl` | auth ledger (see below) |
  | `CAGENT_CA_DIR` | `<repo-root>/.local/cagent-ca` | where the local CA and default server cert/key live |
  | `CAGENT_TLS_SERVER_CERT` | `$CAGENT_CA_DIR/server_cert.pem` | API server's own TLS cert |
  | `CAGENT_TLS_SERVER_KEY` | `$CAGENT_CA_DIR/server_key.pem` | API server's own TLS key |
  | `CAGENT_NCTL_TOML` | `<repo-root>/nctl.toml` | Nautobot connection config, reused as-is for the live DesiredNode validity check |

  There is no plaintext/loopback-only mode in Phase 2 — the server always
  requires mTLS. (Implementer's choice per the plan; kept it this way so
  there is exactly one identity story to reason about, not two.)

- **Local CA + auth ledger** (`.local/cagent-ca/`, `~/.local/state/cagent/ledger/`,
  both gitignored — CA private key and node private keys are secrets and
  never leave their host):

  ```bash
  # once, on the command node:
  uv run --project cagent cagent-ca init
  uv run --project cagent cagent-ca sign-server \
    --out-key .local/cagent-ca/server_key.pem --out-cert .local/cagent-ca/server_cert.pem \
    --dns agstudio.local --ip 192.168.0.100   # whatever address nodes actually dial

  # per node, after collecting its CSR over the SSH path (see p2/plan.md Step 5b):
  uv run --project cagent cagent-ca sign-node --csr node.csr --uuid <DesiredNode UUID> --out node_cert.pem
  uv run --project cagent cagent-ledger register --uuid <uuid> --serial <serial> --fingerprint <fp> --not-after <ts>
  # (cagent-ca sign-node prints the exact register command above)

  uv run --project cagent cagent-ledger list       # inspect
  uv run --project cagent cagent-ledger revoke <serial>
  uv run --project cagent cagent-ledger reactivate <serial>
  ```

  A node then calls the API with `curl --cacert ca_cert.pem --cert node_cert.pem --key node_key.pem ...`.

Start order: `./opencode/start.sh` first, then `cagent-ca`/`cagent-ledger`
setup (once), then `cagent-api`. All are loopback/LAN dev processes with no
process supervision configured (see p1/plan.md Step 2 — "documented manual
start command" is the chosen option, unchanged in Phase 2).

Not built into `nctl` — see `README_DEV.md`'s note that `nctl serve` was
built once, went unused, and was deleted.
