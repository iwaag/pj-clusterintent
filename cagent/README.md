# cagent

The cluster-agent, Phase 1 (loopback MVP). See
[`devdocs/vision/cluster_agent/`](../devdocs/vision/cluster_agent/) for the
roadmap and the frozen contract this implements
(`devdocs/vision/cluster_agent/p1/contract.md`).

Two independent pieces, both loopback-only:

- `opencode/` — a dedicated OpenCode instance, isolated from any node-agent
  instance. Start with `./opencode/start.sh` (see that directory's own
  notes in the Step 2 report for what it does).
- `src/cagent_api/` — the small HTTP API server that proxies to the
  OpenCode instance above and implements the frozen contract. Run with:

  ```bash
  uv run --project cagent cagent-api
  ```

  Configuration is via environment variables (all optional):

  | variable | default | meaning |
  |---|---|---|
  | `CAGENT_API_HOST` | `127.0.0.1` | API listen host |
  | `CAGENT_API_PORT` | `8788` | API listen port |
  | `CAGENT_OPENCODE_URL` | `http://127.0.0.1:4097` | the Step 2 OpenCode instance |
  | `CAGENT_DIRECTORY` | superproject root | working directory passed to OpenCode on every call |

Start order: `./opencode/start.sh` first, then `cagent-api` in another
terminal/process. Both are loopback dev processes with no process
supervision configured in Phase 1 (see plan.md Step 2 — "documented manual
start command" is the chosen option).

Not built into `nctl` — see `README_DEV.md`'s note that `nctl serve` was
built once, went unused, and was deleted.
