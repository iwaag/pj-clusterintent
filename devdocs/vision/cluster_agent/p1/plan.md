# cluster_agent Phase 1 Plan: contract freeze + loopback MVP

References: [roadmap.md](../roadmap.md), [refined_idea.txt](../refined_idea.txt),
[opinion.md](../opinion.md)

## Goal

Freeze the cluster-agent API contract in a short document, then exercise the
whole contract on the command node's loopback only: dedicated OpenCode
instance + small HTTP API + durable per-request evidence, driven end-to-end
with curl.

## Exit criteria (from the roadmap, restated)

1. A frozen contract document exists (`p1/contract.md`).
2. With curl alone on the command node: new request → response retrieval →
   session continuation (follow-up turn) → cancel all work.
3. Evidence remains on disk per request/turn, readable after the fact.
4. After killing the API process mid-turn and restarting it, the in-flight
   request is reported as `interrupted`, not `unknown`.

## Scope and freedom

This is an experimental cluster with no production workload. Loopback only,
no TLS, auth is a stub. Only the three roadmap-wide prohibitions apply:

1. No cluster mutation directly triggered by a node-originated request —
   Phase 1 responses are reads (status/drift/relations/guidance) and plan
   text only. In practice: the OpenCode instance's toolset/prompt must not be
   able to run `nctl reconcile --yes`, `nctl desired apply --yes`, or other
   writes on behalf of a request. Read-only `nctl` commands are fine and
   encouraged.
2. OpenCode binds to 127.0.0.1 only (this phase is loopback anyway).
3. No secrets in Git, binaries, or evidence.

Everything else — language, framework, storage layout, process supervision,
naming — is the implementer's choice. Backward compatibility is not a
concern; break anything in this repo's own new code freely between steps.

## Steps

Follow the house style: one step at a time, `p1/reportN.md` + one commit per
step. Nothing in this phase touches live cluster nodes, so no approval
pauses are expected.

### Step 0 — Research: OpenCode server-mode/session API

Run `opencode serve` locally and map the actual HTTP API of the pinned
version before writing the contract. Deliverable: a short
`p1/opencode_api_notes.md` recording the endpoints/shapes actually verified
(create session, send message, poll/stream result, abort, list sessions) and
how session data is stored on disk.

Hints:

- The proven sample is `ansible_agdev/roles/opencode_agent/` — version
  **1.18.10** pinned with per-platform archive SHA-256s in
  `roles/opencode_agent/defaults/main.yml`, launched as
  `opencode serve --hostname 127.0.0.1 --port 4096` (see
  `templates/opencode-agent.service.j2`). Use the same pinned version for the
  cluster-agent instance; don't research against a floating latest.
- Node-agents use an Ollama provider via `templates/opencode.json.j2`. The
  cluster-agent's model/provider is free choice — pick whatever is easiest to
  verify with (the contract does not depend on the model).
- Check where OpenCode persists sessions (likely under XDG data dirs). You
  will need that answer for Step 2's storage isolation.

### Step 1 — Contract freeze (`p1/contract.md`)

Write and freeze a short contract covering:

- **Resources**: request / session / turn. A request creates or continues a
  session; turns within a session are serialized.
- **State machine** per request, e.g.
  `queued → running → completed | failed | cancelled | interrupted`.
  `interrupted` is what a restart produces (see exit criterion 4).
- **Error shapes**: one JSON error envelope (code, message, request_id).
- **Identity classes**: `node` and `human` are distinct classes with
  different future authorization (humans will hold approval authority).
  Phase 1 only *represents* the class (stub, e.g. a header the caller sets);
  real authentication is Phase 2/4. Record the claimed identity in evidence.
- **Initial authorization rule**: all identities get reads + plan
  presentation only. Write one sentence stating that mutation requires human
  approval through a future entrance.
- **Endpoints**: create request (async — returns request ID immediately),
  get request status/response, continue session, cancel, list sessions.
  Async-by-default; the client polls. No SSE in this phase.

Keep it to a page or two. Freeze = commit it and treat later edits as
explicit contract changes noted in reports, not silent drift.

### Step 2 — Dedicated OpenCode instance for the cluster-agent

Stand up a cluster-agent-only `opencode serve` on loopback, on a different
port from any node-agent, with:

- working directory = this superproject root (`pj-clusterintent`), so the
  agent can run `uv run --project nctl nctl status/drift/relations` exactly
  as a human session does;
- its own config and session-storage area, fully separate from any
  node-agent instance (env-based data-dir isolation or a dedicated user dir —
  whatever the Step 0 research showed works);
- a system prompt / agent instruction file telling it its role: answer
  cluster resource/service questions using read-only `nctl` (drift,
  relations, status, ops show) and present plans without executing writes.

Supervision (launchd plist like the darwin node-agent template, or just a
documented manual start command) is implementer's choice — this is a
loopback dev process, keep it simple.

### Step 3 — cluster-agent API server (loopback MVP)

A small HTTP server on loopback implementing the frozen contract, proxying
to the OpenCode instance:

- Implementation language free. Python/uv matches the existing toolchain,
  but **do not build it into nctl** — `nctl serve` was built once, went
  unused, and was deleted (see `devdocs/big/remove_unused_surfaces/`). A new
  small top-level project directory (suggested name: `cagent/` or
  `cluster_agent_api/`) is the expected shape.
- Async by default: POST returns a request ID; a worker drives the OpenCode
  turn; GET returns state + response so far.
- Serialize turns within a session. Global serialization of all turns is
  acceptable and simpler for now (all sessions share one working directory);
  say in the report which you chose.
- Auth stub: accept a caller-declared identity (class + name), validate
  shape only, record it. Do not invent real auth here.
- Cancel maps to OpenCode's abort; if abort proves unreliable, marking the
  request `cancelled` and abandoning the turn is acceptable for Phase 1 —
  record the behavior honestly.

### Step 4 — Durable evidence

Same shape as `nctl ops`: an ID directory plus JSON/JSONL, e.g.
`<evidence_dir>/<request_id>/` containing received time, claimed identity,
request body (or its hash), state transitions with timestamps, session ID,
and the final response. Rules:

- **Request state lives on the evidence side**, not only in process memory.
  On startup, the API scans evidence for requests left in a non-terminal
  state and marks them `interrupted`. This is what makes exit criterion 4
  cheap instead of an afterthought.
- Public identifiers only in evidence — no tokens or keys (there are none in
  this phase anyway; keep the habit).
- A list/inspect surface for a human is required but minimal: a tiny CLI
  subcommand or even documented `ls`/`cat` conventions are enough for now.

This can be built inside Step 3 rather than as a separate commit if that is
more natural; keep the report boundary either way.

### Step 5 — End-to-end verification with curl

From the command node, with curl only (per roadmap hygiene, pass bodies via
`--data @file`, not inline arguments):

1. Create a request as identity class `node`: a realistic question, e.g.
   "I want S3-compatible storage — what exists in this cluster?" Verify the
   answer draws on real `nctl relations`/`drift` output.
2. Poll to completion; retrieve the response.
3. Continue the same session with a follow-up turn; verify the agent retains
   context.
4. Cancel an in-flight request; verify terminal state `cancelled`.
5. Kill the API server mid-turn, restart, query the request ID → state is
   `interrupted`.
6. Confirm evidence directories exist for all of the above and contain the
   contract-specified fields.

Save the transcript (commands + trimmed responses) as evidence referenced by
the final report. Automated tests are at the implementer's discretion; the
highest-value ones are the request state machine, the evidence writer, and
the interrupted-on-restart scan (Tier A-ish per README_DEV, but do not build
a big harness for a loopback MVP — this API will be broken again in Phase 2
when mTLS lands).

## Useful facts collected at planning time

- `nctl relations --json` is computed fresh on every call and already agrees
  with `nctl drift`; it is the intended raw material for "guidance to an
  existing service" answers. `nctl status`, `nctl drift --json`, and
  `nctl ops show` are the other read surfaces worth exposing to the agent.
- All `nctl` invocations must run from the superproject root with
  `uv run --project nctl nctl …`; token resolution comes from `nctl.toml`
  → `.local/secrets`, so no env var plumbing is needed as long as the
  OpenCode working directory is the repo root.
- Known cluster state: agpc/agstudio reachable, agbach/agdnsmasq
  unresponsive (expected). Irrelevant to loopback Phase 1 except that agent
  answers about drift will mention it — that's correct behavior, not a bug.
- Phase 2 will put mTLS in front of this API and bind identities to
  DesiredNode UUIDs. Nothing in Phase 1 needs to anticipate that beyond
  keeping the identity stub a distinct, replaceable layer.

## Out of scope for Phase 1

TLS, real authentication, the auth ledger, any distribution to nodes, SSE,
the smartphone/human UI, rate limits, session TTLs, and attachment upload.
