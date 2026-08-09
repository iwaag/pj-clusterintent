# cagent

The cluster-agent. See [`devdocs/vision/cluster_agent/`](../devdocs/vision/cluster_agent/)
for the roadmap and the frozen contracts this implements
(`devdocs/vision/cluster_agent/p1/contract.md` for resources/state machine,
`p2/contract.md` for the Phase 2 mTLS identity/authorization delta,
`p4/contract.md` for the Phase 4 human entrance delta — each is a breaking
change over the previous: Phase 2 dropped the Phase 1 identity-header stub,
Phase 4 reworked the identity shape to be class-tagged).

Three pieces:

- `opencode/` — a dedicated OpenCode instance, isolated from any node-agent
  instance. Loopback-only. Start with `./opencode/start.sh`.
  Edits to `opencode/AGENTS.md` take effect only for sessions created after
  restarting this OpenCode process — restart `./opencode/start.sh` after any
  instructions change, before testing. `cagent-api` itself does not need a
  restart (and `llms.txt` is re-read from disk per request).
- `src/cagent_api/` — the HTTP API server that proxies to the OpenCode
  instance above and implements the frozen contract, on **two listeners**:

  - **Node entrance** (`:8788` by default) — mTLS, unchanged since Phase 2.
    Every route needs a client certificate signed by the local CA below,
    registered in the auth ledger, **except** `GET /llms.txt` (see next
    bullet), which the TLS context deliberately accepts connections
    without one for (`CERT_OPTIONAL`) so an unenrolled node can still read
    where its certificate is supposed to come from.
  - **Human entrance** (`:8789` by default, Phase 4) — server-only TLS, no
    client cert. Authenticated by a single static bearer token instead
    (see below). Serves the chat UI at `GET /` in addition to the same
    `/requests`/`/sessions/...` routes the node entrance has.

  Run with:

  ```bash
  uv run --project cagent cagent-api
  ```

  Configuration is via environment variables (all optional):

  | variable | default | meaning |
  |---|---|---|
  | `CAGENT_API_HOST` | `0.0.0.0` | listen host for both entrances (moved off loopback in Phase 2 so LAN/VPN nodes can reach it) |
  | `CAGENT_API_PORT` | `8788` | node entrance (mTLS) listen port |
  | `CAGENT_HUMAN_PORT` | `8789` | human entrance (bearer token) listen port — Phase 4 |
  | `CAGENT_HUMAN_TOKEN_FILE` | `~/.local/state/cagent/human_token` | file holding the human bearer token, one line, mode `0600` — Phase 4. **The human listener refuses to start if this file is missing or empty**, same refuse-don't-fallback pattern as the OpenAI key below. |
  | `CAGENT_HUMAN_NAME` | `operator` | fixed operator label recorded in evidence for every human-authenticated request — Phase 4 |
  | `CAGENT_TURN_TIMEOUT_SECONDS` | `300` | per-turn wall-clock bound before the worker aborts the OpenCode turn and marks the request `failed` (`timeout`); raise for hosts where legitimate multi-command turns (e.g. composing a state bundle) exceed 5 minutes |
  | `CAGENT_OPENCODE_URL` | `http://127.0.0.1:4097` | the OpenCode instance (always loopback, never exposed) |
  | `CAGENT_DIRECTORY` | superproject root | working directory passed to OpenCode on every call |
  | `CAGENT_EVIDENCE_DIR` | `~/.local/state/cagent/evidence` | durable per-request evidence |
  | `CAGENT_LEDGER_PATH` | `~/.local/state/cagent/ledger/ledger.jsonl` | auth ledger (see below) |
  | `CAGENT_CA_DIR` | `<repo-root>/.local/cagent-ca` | where the local CA and default server cert/key live |
  | `CAGENT_TLS_SERVER_CERT` | `$CAGENT_CA_DIR/server_cert.pem` | server TLS cert, shared by both entrances |
  | `CAGENT_TLS_SERVER_KEY` | `$CAGENT_CA_DIR/server_key.pem` | server TLS key, shared by both entrances |
  | `CAGENT_NCTL_TOML` | `<repo-root>/nctl.toml` | Nautobot connection config, reused as-is for the live DesiredNode validity check |

  There is no plaintext/no-auth mode for any route that touches
  sessions/requests on either entrance — the node entrance always requires
  mTLS for those, the human entrance always requires the bearer token.
  (Implementer's choice per the plan; kept it this way so there is exactly
  one identity story per entrance to reason about.) The sole exception is
  `GET /llms.txt` on both entrances: a static, non-sensitive discovery doc,
  unauthenticated by design (same spirit as `robots.txt`) so an agent
  without credentials yet can still find out how to get them.

  `llms.txt` doubles as cagent's **entrance guide** (devpolicy/policy.md):
  it carries the cost/timing/side-effect answers as well as the endpoint
  list, and `opencode/AGENTS.md` instructs the agent to read it and answer
  capability and cost questions from it in-session — so "what can you do?"
  and "what does this cost?" work as ordinary messages, not only as a file
  fetch. Where the price is genuinely unknown the agent is told to say
  unknown rather than guess.

  **Backend model (Agent ≠ Model).** `CAGENT_OPENCODE_MODEL` selects the
  model the cluster-agent runs on; `cagent/opencode/start.sh` renders it into
  the committed `config.json.template` (default `openai/gpt-5.6-luna`) and
  prints it at startup. Like `AGENTS.md`, the model is fixed at process
  start — restart the script to change it. OpenCode reports no per-request
  price back to cagent-api, so nothing about cost is recorded; that is what
  `llms.txt` means when it says the price is unknown.

  **Human token setup** (once, on the command node):

  ```bash
  mkdir -p ~/.local/state/cagent
  python3 -c "import secrets; print(secrets.token_urlsafe(32))" > ~/.local/state/cagent/human_token
  chmod 600 ~/.local/state/cagent/human_token
  ```

  Then open `https://<command-node>:8789/` in a browser, paste the token
  into the login form once (it moves into `localStorage` and is attached
  to every request from then on).

- **Local CA + auth ledger** (`.local/cagent-ca/`, `~/.local/state/cagent/ledger/`,
  both gitignored — CA private key and node private keys are secrets and
  never leave their host):

  ```bash
  # once, on the command node:
  uv run --project cagent cagent-ca init
  uv run --project cagent cagent-ca sign-server \
    --out-key .local/cagent-ca/server_key.pem --out-cert .local/cagent-ca/server_cert.pem \
    --dns agstudio --dns agstudio.local --ip 192.168.0.100
    # one leaf cert serves both entrances: --dns agstudio is the bare
    # Tailscale MagicDNS hostname the phone dials (Phase 4), agstudio.local
    # is agpc's existing LAN dial (Phase 2/3, kept so its wrapper is
    # unaffected) — add/remove SANs for whatever addresses actually apply

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
setup and the human token file (once each), then `cagent-api` — which
brings up both entrances in one process (the human listener runs on its
own background thread; `cagent-api` logs both listening URLs at startup).
All are loopback/LAN/VPN dev processes with no process supervision
configured (see p1/plan.md Step 2 — "documented manual start command" is
the chosen option, unchanged through Phase 4).

Not built into `nctl` — `nctl serve` was built once, went unused, and was
removed together with both nctl dashboards (see
[`devdocs/big/braindump/roadmap.md`](../devdocs/big/braindump/roadmap.md)).

## OpenAI model backend

The dedicated cluster-agent OpenCode instance uses OpenAI's
`gpt-5.6-luna` model. It is intentionally separate from every node-agent's
local Ollama configuration, so node-agent work cannot queue behind a
cluster-agent turn (or vice versa).

Before starting `./opencode/start.sh`, supply an OpenAI API key by **one** of
these methods:

1. Export `OPENAI_API_KEY` in the shell that starts it. This is useful for a
   one-off run.
2. Preferred for the documented manual service: create the gitignored file
   `.local/cagent/openai_api_key`, containing only the key, with mode `0600`.
   The start script reads it only when `OPENAI_API_KEY` is unset. To store it
   elsewhere, set `CAGENT_OPENAI_API_KEY_FILE` to that file path.

For example, create the file with a local editor, then verify its permissions
without displaying its contents:

```bash
mkdir -p .local/cagent
chmod 700 .local/cagent
$EDITOR .local/cagent/openai_api_key
chmod 600 .local/cagent/openai_api_key
```

The start script refuses to run if neither source is available. It does not
fall back to Ollama. After authentication is provided, start the normal stack
and make one read-only `cagent ask --no-wait` request from agpc to verify the
provider end to end. Record the selected provider/model and timing in the
request evidence, but never the key.
