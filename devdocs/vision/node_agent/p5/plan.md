# Node Agent — Phase 5 Plan: Programmatic delegation

Status: not started.
Input: [Phase 3 report](../p3/report.md), [Phase 4 report](../p4/report.md),
[roadmap Phase 5](../roadmap.md).

## Goal

Let a controller-side agent (or a script) delegate work to a node agent
without driving the TUI:

```bash
nctl agent run HOST --prompt "Inspect the failed service"
nctl agent sessions HOST --json
nctl agent send HOST SESSION_ID --prompt "Continue with the fix"
nctl agent abort HOST SESSION_ID
```

This also closes the limitation carried since Phase 1: TUI Ctrl-C does not
interrupt the remote task, so `abort` must call OpenCode's session interrupt
API deliberately.

## What already exists (reuse, do not rebuild)

- `nctl_core/agent.py` — `resolve_agent_target` (exact-slug resolution,
  workdir, SSH-enrollment check), `open_tunnel` (ephemeral loopback forward
  with teardown), `_probe_health`, `AgentError`, and the
  `build_agent_status` OperationLog/envelope pattern. All four new commands
  are "resolve target → open tunnel → HTTP calls → envelope" on top of these
  primitives.
- `nctl_core/config.py` — `AgentConfig` (`port`, `ssh_user`,
  `identity_file`, workdir maps, `connect_timeout_seconds`). Add any new
  knobs (e.g. a run/send wait timeout) here, controller-owned as before.
- `nctl_core/agent_render.py` + `tests/test_agent.py` /
  `tests/test_cli_agent.py` — existing render and test patterns (mocked
  `popen`, fake HTTP) to extend.
- Deployed runtime: OpenCode **1.18.10** pinned by the `ansible_agdev`
  `opencode_agent` role, loopback-only on port 4096, on `agstudio` (macOS,
  launchd) and `agpc` (Linux, systemd user unit `opencode-agent.service`),
  model `ollama/qwen3.6:35b-a3b-coding-nvfp4`.

## Scope and decisions

- **Adapter**: one small OpenCode HTTP client (e.g.
  `nctl_core/agent_api.py`) speaking to `http://127.0.0.1:<local_port>`
  through the existing tunnel. Typed methods for: list sessions, create
  session, send a prompt and wait for the reply, interrupt. Keep it a thin
  runtime adapter — Phase 6 may add other runtimes behind it, so don't leak
  OpenCode paths into the CLI layer, but don't build a plugin framework
  either.
- **Pin the API against reality first.** The exact endpoint shapes in
  1.18.10 are the single biggest unknown. `/doc` is the server's OpenAPI
  document — dump it through an `nctl`-managed tunnel as the first
  implementation step and derive the paths from that, not from memory or
  current upstream docs. Known evidence so far: Phase 1 verified
  `POST /api/session/{id}/interrupt` returns 204 and actually cancels;
  the old `/api/session/.../prompt` accepted a prompt but offered no wait;
  newer surfaces mentioned were `/session/{id}/message` and `prompt_async`;
  Phase 3 read sessions and message content via the node-local session API,
  so listing/reading definitely works. Note also that OpenCode scopes
  sessions by directory — expect a `directory` query/body parameter and pass
  the resolved workdir, the same value `attach --dir` uses.
- **run**: create a session, send the prompt, wait (bounded) for the
  assistant reply, print the reply text; `--json` returns an envelope with
  node, session ID, model, timing, outcome, and reply. Waiting strategy is
  implementer's choice: a synchronous message endpoint if 1.18.10 has one,
  otherwise async-send plus polling the session/message state, or the SSE
  event stream if it turns out to be the simplest reliable signal. Streaming
  partial output to the terminal is nice-to-have, not required — a blocking
  call that returns the final reply satisfies this phase.
- **send**: same as `run` but against an existing session ID
  (`session_not_found` structured error if the node doesn't know it).
- **sessions**: list session IDs with title/timestamps so `--session` and
  `send` are usable without guessing; `--json` is the primary consumer.
- **abort**: call the interrupt API; report whether the server accepted it
  (204). Verify with the Phase 1 probe pattern: a prompt that sleeps then
  writes a marker file — after abort, the marker must not appear.
- **Timeouts and failure**: every HTTP call gets a bounded timeout; the
  reply wait gets its own configurable, generous default (model responses
  were 4–8 s for trivial prompts, but real tool-using tasks run minutes —
  something like 300 s default plus a `--timeout` flag is reasonable). A
  timeout is a structured error (`agent_timeout`) that still reports the
  session ID so the operator can `send`/`abort`/`attach` the same session
  afterwards — an interrupted wait must not strand the work invisibly.
  Unreachable node keeps the existing `agent_unreachable` shape.
- **Envelopes and evidence**: stable `nctl.agent.run.v1`,
  `nctl.agent.sessions.v1`, etc.; OperationLog records for `run`, `send`,
  and `abort` (sessions listing is discretionary), capturing node, session
  ID, model, timing, and outcome. Runtime-specific detail may ride in a
  `detail`/`raw` field; keep prompt text and reply text out of the
  operation event log if they are long — record lengths/markers instead
  (transcripts live on the node, per the Phase 4 rule that conversation
  state stays out of desired-state and ledgers).
- **Out of scope**: MCP tools, scheduling, multi-node fan-out, additional
  runtimes, authentication beyond loopback+SSH (all Phase 6). No change to
  `attach`, reconciliation, or the deployed role.

## Minimum prohibitions (everything else is implementer's discretion)

1. No credentials, tokens, or key material committed or printed.
2. Exact-slug HOST resolution only; never fall through to a different node.
3. Agent endpoint comes only from nctl config + the managed SSH tunnel
   (trust store intact, no `StrictHostKeyChecking=no`); never from argv.
4. Tunnel processes must not outlive the command, including on timeout and
   abort paths.
5. Do not print raw session transcripts into operation event logs stored
   under the events dir; envelopes returned to the caller may carry them.

## Deliverables

```text
nctl/src/nctl_core/agent_api.py        # OpenCode HTTP adapter (sessions, message, interrupt)
nctl/src/nctl_core/agent.py            # run/send/sessions/abort operations + envelopes
nctl/src/nctl_core/agent_render.py     # text renders for the new envelopes
nctl/src/nctl_core/cli/...             # four new subcommands under `nctl agent`
nctl/tests/...                         # adapter + operation + CLI tests
nctl.toml / example.nctl.toml          # new [agent] timeout knob(s) if added
devdocs/vision/node_agent/p5/report.md
```

## Steps

Usual style: one report section + commit per step; pause for user approval
before the live steps.

### Step 0 — API pinning spike (read-only, live but harmless)

- Through `nctl`-style tunnels, fetch `/doc` from agstudio or agpc and
  record the exact 1.18.10 paths/schemas for session list/create, message
  send (sync or async), message/state read, and interrupt. Read-only GETs
  plus at most one throwaway session on one node; no approval gate needed
  beyond noting it in the report.

### Step 1 — Adapter and core operations (local only)

- `agent_api.py` against the pinned schemas; `run`/`send`/`sessions`/
  `abort` operations with envelopes, OperationLog, timeout handling.
- CLI wiring.

### Step 2 — Tests

- Adapter tests against a fake HTTP transport (httpx `MockTransport` or a
  loopback stub): happy paths, session-not-found, timeout-with-session-id,
  interrupt accepted/refused.
- Existing patterns cover tunnel/argv; don't re-test SSH policy beyond one
  assertion that the new commands go through the same target resolution.
- Full nctl suite green (was 1024 passing after Phase 4).

### Step 3 — Live verification (approval required)

On both nodes, or one node plus a spot check on the other:

- `nctl agent sessions agpc --json` lists the known Phase 2/3 sessions.
- `nctl agent run agstudio --prompt ...` — a small file-writing task;
  verify the file on the node and the envelope's session ID/outcome.
- `nctl agent send` continues that same session and shows context
  retention.
- `nctl agent abort` on the Phase 1 sleep-then-write probe: marker file
  absent, interrupt recorded. Clean up probe artifacts.
- One failure shape live: unknown slug or stopped service.

### Step 4 — Report and close

- `p5/report.md` with command surface, pinned API notes, live evidence,
  and any new carried limitations; mark the roadmap Phase 5 status line;
  commit in nctl and bump the submodule pointer.

## Completion criteria

- A controller-side agent can, with `--json` output only: start a task,
  list/find its session, continue it, and abort it — on either node.
- Timeouts and unreachable nodes fail with structured errors that keep the
  session addressable.
- Abort provably cancels remote work (marker-file evidence), retiring the
  Ctrl-C limitation.
- nctl suite passes; no orphan tunnels on any exit path.
