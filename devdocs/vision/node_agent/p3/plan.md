# Node Agent — Phase 3 Plan: Interactive `nctl` entry point

Status: not started.
Input: [Phase 2 report](../p2/report.md), [roadmap Phase 3](../roadmap.md).

## Goal

Add `nctl agent status HOST` and `nctl agent attach HOST [--session ID]` so
the operator enters a node agent through nctl instead of remembering the
manual two-command workflow (SSH local forward + `opencode attach URL`).
Prove it live against both deployed nodes (`agstudio`, `agpc`).

## Scope and decisions

- **Commands**: `nctl agent status HOST` and `nctl agent attach HOST
  [--session SESSION_ID]` in a new `agent` Typer sub-app. A session-listing
  helper (to make `--session` usable without guessing IDs) may be added at
  the implementer's discretion; full programmatic delegation is Phase 5.
- **HOST resolution**: exact DesiredNode slug match against the Nautobot
  desired snapshot, exactly like `ssh_enroll._resolve_node` — no fuzzy
  matching, `unknown_host` structured error otherwise. HOST is never
  interpreted as a URL or address.
- **Endpoint resolution**: the agent is always reached as
  `127.0.0.1:<port>` *on the node* through an SSH local forward opened by
  nctl. The port defaults to 4096 (the `opencode_agent` role default) and
  comes from controlled nctl configuration (e.g. an optional `[agent]`
  section in `nctl.toml`), never from the command line.
- **SSH transport**: reuse the existing alias-keyed trust store policy —
  `HostKeyAlias`/`UserKnownHostsFile`/`StrictHostKeyChecking=yes` as in
  `ssh_trust.build_ansible_ssh_common_args`. An unenrolled host fails with
  the same guidance as reconcile (`nctl ssh enroll <slug> ...`).
- **attach = wrap the native client**: open the tunnel on an ephemeral
  local port, then run the controller-local `opencode attach
  http://127.0.0.1:<localport> --dir <workdir> [--session ID]` with an
  inherited TTY, so resize/keys/exit status are handled by the native TUI.
  No Python protocol client. The controller already has the pinned
  `opencode` 1.18.10 at `~/.local/bin/opencode`; how strictly to check the
  local binary/version is implementer's discretion.
- **Remote workdir** (`--dir`) differs per OS (`/Users/eiji/agent-work` vs
  `/home/eiji/agent-work`). Resolve it from configuration or by asking the
  node/service — implementer's choice; do not hard-code one platform.
- **status**: report at minimum reachability of the agent service (the
  `/doc` health endpoint through SSH) plus useful context (endpoint, and
  version/session info if cheap to obtain). Support `--json` with a normal
  nctl envelope. `attach` is interactive and needs no JSON mode.
- **Structure**: follow the nctl split — typed logic in `nctl_core`
  (e.g. `agent.py` / `agent_render.py`), thin CLI in `cli/main.py`,
  structured errors, OperationLog events for `status` (whether interactive
  `attach` writes an operation record is discretionary).
- **Out of scope**: reconcile/intent integration (Phase 4), `run`/`send`/
  `abort` and JSON session APIs (Phase 5), authentication beyond the
  loopback+SSH posture, multi-runtime abstraction.

## Minimum prohibitions (everything else is implementer's discretion)

1. No credentials, tokens, or key material committed or printed.
2. Never resolve HOST ambiguously or fall through to a different node;
   exact-slug match only.
3. Do not accept an arbitrary URL/address as the agent endpoint; it must
   come from nctl-controlled configuration plus the SSH tunnel.
4. Do not bypass the managed SSH trust store (no
   `StrictHostKeyChecking=no`).
5. Clean up the tunnel process when attach exits, and propagate the TUI's
   exit status.

## Deliverables

```text
nctl/src/nctl_core/agent.py            # slug->node, tunnel, status probe, attach exec
nctl/src/nctl_core/agent_render.py     # envelope + text render for status
nctl/src/nctl_core/cli/main.py         # agent sub-app wiring
nctl/tests/...                         # unit tests, mocked ssh/subprocess
nctl.toml / example.nctl.toml          # optional [agent] section (port, workdir map or equivalent)
devdocs/vision/node_agent/p3/report.md
```

## Steps

Usual style: one report section + commit per step; pause for user approval
before the live step.

### Step 1 — Core implementation (local only)

- Node resolution, config section, tunnel management (ephemeral port,
  startup wait, teardown), `status` probe, `attach` exec wrapper.
- CLI wiring for `nctl agent status|attach`.

### Step 2 — Tests and static checks

- Unit tests: slug resolution errors, ssh argument construction (trust
  store options present), tunnel lifecycle, attach command line,
  status envelope shape. Full `pytest` run stays green.

### Step 3 — Live verification on both nodes (approval required)

- `nctl agent status agstudio` / `agpc`: correct reachability report;
  also verify the failure shape against a stopped service or unknown slug.
- `nctl agent attach agstudio`: TUI opens, model responds, detach leaves
  no orphan tunnel process, exit status propagates.
- `nctl agent attach agpc --session <existing>`: resumes a prior session
  with history (Phase 2 left sessions on both nodes).

### Step 4 — Report and close

- `p3/report.md`: command surface, config shape, live evidence, and the
  carried limitation that TUI Ctrl-C does not interrupt the remote task
  (deliberate abort lands in Phase 5 via the interrupt API).
- Commit in nctl, bump the submodule pointer, update the roadmap status
  line.

## Completion criteria

- Operator reaches a working agent session on either node with one nctl
  command, without remembering ports, tunnels, or runtime commands.
- `status` gives a truthful reachable/unreachable answer with `--json`
  support; unknown slugs and unenrolled hosts fail with clear structured
  errors.
- nctl test suite passes; tunnel processes never outlive the attach.
