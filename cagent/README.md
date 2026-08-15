# cagent

The cluster-agent. See [`devdocs/vision/cluster_agent/`](../devdocs/vision/cluster_agent/)
for the roadmap and the frozen contracts this implements
(`devdocs/vision/cluster_agent/p1/contract.md` for resources/state machine,
`p2/contract.md` for the Phase 2 mTLS identity/authorization delta,
`p4/contract.md` for the Phase 4 human entrance delta — each is a breaking
change over the previous: Phase 2 dropped the Phase 1 identity-header stub,
Phase 4 reworked the identity shape to be class-tagged).

**One process.** `cagent-api` is the whole thing: three listeners, three
roles, and the agent itself running in-process. There is no agent server to
start first and nothing to restart after an instructions change.

Four pieces:

- `agents.toml` — the `ag.agent-config.v1` configuration: three roles
  (`node`, `human`, `window`), and the profiles behind them. Which backend
  serves which door is a machine-local choice in the ignored
  `.local/agents.local.toml` overlay (`[roles.window] profile = "sonnet"`
  switches one door), and every answer's run record names what actually
  served it. The default `local` profile is agcode on the local Ollama model:
  no account, no key, no separate process.
- `agent/AGENTS.md` — the authenticated doors' instructions, **read from disk
  on every request**. Edit it and the next answer changes; nothing restarts.
  Its tools are agcode's four built-ins, with `run` refusing destroy-class
  commands (guest destruction, storage erasure) before executing them.
- `window/` — the **unauthenticated window**: its own instructions
  (`window/AGENTS.md`, also re-read per request), its own capability card
  (`window/GUIDE.md`), and a strictly smaller tool set defined in
  `src/cagent_api/agent_runner.py:window_tools()` — `read`, `list`, a
  read-only `nctl` tool, and the two incident tools. **No shell at all.**
  The window is not offered a way to change anything, so there is no
  permission engine, no allow-list to escape, and no denial to argue with.
  `window/incident.py` is the human-facing CLI over the same recorder the
  window agent calls; one defect report becomes one file under
  `.local/cagent/incidents/`:

  ```bash
  uv run cagent/window/incident.py -i "you said node X was up; it is not" \
    --reporter "zulip:8" --source zulip-dm --ref "zulip message 41"
  uv run cagent/window/incident.py --list
  ```

  Added in `devdocs/episodes/better_communication/zulip_cagent_receive`, which
  is also where the empirical permission-denial evidence lives. The window is
  deliberately weaker than the entrances below; a request for a cluster change
  comes back as a refusal pointing at them.

- `src/cagent_api/` — the HTTP API server, the agent runner, and the frozen
  contract, on **three listeners**:

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
  - **Window entrance** (`:8790` by default) — **no authentication and no
    TLS**. `POST /window {"text": "..."}` is the only way in (there is no
    `/requests` POST, no `/sessions`, no UI there — it is a single
    entrance), plus `GET /guide`, `GET /healthz`, and `GET /requests/{id}`
    to poll the answer. It runs on the `window` role's runner, so what an
    anonymous caller can cause is bounded by that tool set rather than by an
    identity check. Its requests share the same store and evidence as the
    other two.

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
  | `CAGENT_HUMAN_TOKEN_FILE` | `~/.local/state/cagent/human_token` | file holding the human bearer token, one line, mode `0600` — Phase 4. **The human listener refuses to start if this file is missing or empty**, refuse-don't-fallback: there is no plaintext mode for it. |
  | `CAGENT_HUMAN_NAME` | `operator` | fixed operator label recorded in evidence for every human-authenticated request — Phase 4 |
  | `CAGENT_TURN_TIMEOUT_SECONDS` | `300` | per-turn wall-clock bound. It reaches agcode as `deadline_s`, so the run ends itself from inside and reports `deadline_exceeded` rather than being abandoned; raise it for hosts where legitimate multi-command turns (e.g. composing a state bundle) exceed 5 minutes |
  | `CAGENT_WINDOW_PORT` | `8790` | window entrance (unauthenticated, plain HTTP) listen port |
  | `CAGENT_WINDOW_GUIDE` | `<repo-root>/cagent/window/GUIDE.md` | file served at `GET /guide`, re-read per request |
  | `CAGENT_AGENTS_CONFIG` | `<repo-root>/cagent/agents.toml` | the committed `ag.agent-config.v1` file |
  | `CAGENT_AGENTS_OVERLAY` | `<repo-root>/cagent/.local/agents.local.toml` | machine-local harness/provider facts and per-role profile choice |
  | `CAGENT_DIRECTORY` | superproject root | the agent's single working directory — agcode resolves every tool path against it, and nothing else |
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
  list, and `agent/AGENTS.md` instructs the agent to read it and answer
  capability and cost questions from it in-session — so "what can you do?"
  and "what does this cost?" work as ordinary messages, not only as a file
  fetch. Where the price is genuinely unknown the agent is told to say
  unknown rather than guess.

  **Backend model (Agent ≠ Model).** The backend is a role's profile in
  `agents.toml`, overridable per machine and per door in the ignored
  `.local/agents.local.toml`. Whichever one served a turn is recorded on the
  request: `GET /requests/{id}` carries `backend`
  (`{harness, provider, model, role, profile}`) next to `cost_usd`.

  `cost_usd` is `null` on the default `local` profile. The backend reports no
  cost, and `null` means "not measured" — a different and true claim, where a
  `0.0` would assert the turn was free. A `claude_code` profile reports its
  own figure there.

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

Start order: `cagent-ca`/`cagent-ledger` setup and the human token file
(once each), then `cagent-api` — which brings up all three entrances and
their three agents in one process (the human and window listeners run on
their own background threads; `cagent-api` logs all three listening URLs and
the resolved backends at startup). Optionally `service/zulip_listener.py`,
the Cagent bot's chat entrance, which turns a Zulip DM into one
`POST /window` (credentials `.local/zulip/cagent.env`,
`CAGENT_ZULIP_LOG_ONLY=1` to watch without spending a turn).

A profile that does not resolve is fatal at startup rather than per request:
answering "the agent is misconfigured" once at boot beats discovering it on
someone's message.

On agstudio these run under launchd rather than by hand; the templates and
labels are in [`devenv/launchd/`](../devenv/launchd/README.md).

Not built into `nctl` — `nctl serve` was built once, went unused, and was
removed together with both nctl dashboards (see
[`devdocs/big/braindump/roadmap.md`](../devdocs/big/braindump/roadmap.md)).

## Backend

The default `local` profile is agcode — the single-file harness inside
`pyagag` — against the local Ollama endpoint declared in
`.local/agents.local.toml`:

```toml
schema = "ag.agent-config.v1"

[local.provider.ollama]
base_url = "http://127.0.0.1:11434"
```

No `/v1` suffix: agcode posts to `{base_url}/v1/messages`. No account and no
API key are involved, and there is no separate agent process to supervise.

To put a door on a paid backend instead, add its profile choice and secret
reference to the same ignored overlay:

```toml
[roles.human]
profile = "sonnet"

[local.harness.claude_code]
command = "/usr/local/bin/claude"

[local.secrets]
anthropic_api_key_file = "~/.secrets/anthropic_api_key"
```

The key value itself never enters `agents.toml`, the overlay, request
evidence, or Git — only the reference to where it lives.
