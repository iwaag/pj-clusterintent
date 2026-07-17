# Phase 5 Implementation Plan: Realtime API layer

Parent: [roadmap.md](../roadmap.md) — Phase 5: make it possible for advanced UIs (3D, voice,
etc.) to connect as "new subscribers": an HTTP API wrapping `nctl_core` (state snapshot, drift
fetch, reconcile trigger) plus a WebSocket for streaming events, with minimal single-token auth.

## Current state (as of 2026-07-17)

- Phases 0 through 4 are complete. The CLI surface is `status`, `drift`, `dashboard`,
  `render dnsmasq|production|hosts-intent`, `apply dnsmasq`, and `reconcile [HOST] [--yes]`.
  The Phase 4 exit criteria are live-proven (see `p4/report9.md`): the happy path converges via
  `nctl reconcile --yes` with no human/AI involvement, and every terminal reason
  (`converged`, `already_converged`, `non_converged`, `manual_intervention_required`, `failed`)
  has been observed against the real cluster.
- The design conventions Phase 5 depends on are already in place, exactly as the roadmap
  intended:
  - all logic lives in `nctl_core`; `cli/main.py` is a thin typer wrapper — the API server can
    be a second thin wrapper over the same functions;
  - every command returns a stable `nctl.<command>.v1` envelope
    (`nctl_core.output.Envelope`, pydantic v2), so HTTP responses can reuse the exact same
    documents;
  - long-running operations emit one JSONL file per run at
    `<events.log_dir>/<operation_id>.jsonl` via `nctl_core.events.OperationLog`, with a
    documented vocabulary (`docs/event-log.md`) and monotonically increasing `seq` — gaps mean
    loss, never reordering. `seq` is the natural WebSocket replay cursor.
  - `reconcile` writes its full artifact set under `<events.log_dir>/<operation_id>/`
    (`plan.json`, per-round drift, `result.json`), so "fetch the state of a past operation" is
    a filesystem read, not new bookkeeping.
- Relevant implementation facts that shape the server design:
  - `nctl_core` is **synchronous** throughout (sync `httpx`, blocking `subprocess` Ansible
    runs). An applying reconcile can legitimately run for many minutes. The server must not
    pretend this is async work; it must run operations on worker threads and stream progress,
    not block request handlers.
  - `OperationLog._write` appends straight to the JSONL file; there is no in-process
    subscription hook yet. Phase 5 adds one rather than having the server tail files with
    polling loops.
  - Mutating reconcile is protected by a **controller-local file lock**
    (`nctl_core.reconcile.lock`, `[reconcile].lock_path`). Phase 4's plan explicitly deferred
    "a server-side operation lock" to Phase 5. The correct move is not to replace the file
    lock but to build the server's single-flight queue **on top of it**, so a concurrent CLI
    invocation and a server-triggered run still exclude each other.
  - Config is strict pydantic (`extra="forbid"`); credentials come only from `token_env` /
    `token_file`, never inline in `nctl.toml`. The serve token follows the same convention.
  - The Phase 3 dashboard is a static, self-contained HTML page regenerated from a drift
    payload; Phase 4 factored dashboard generation into a function that accepts an
    already-built drift envelope. The Phase 5 live dashboard is a *separate* page served by
    the API — the static artifact and its file/LAN hosting remain untouched.
- Roadmap security posture (unchanged): experimental system, LAN-only, "minimal auth (roughly
  a single token) is enough." No TLS, no user accounts, no RBAC. But the existing hygiene
  rules still bind: no plaintext Nautobot token in Git, no token leakage into logs/output,
  and now no serve token in `nctl.toml` either.
- From this phase onward the roadmap says to **start caring about compatibility** ("start
  firming up the event schema toward a freeze") because external subscribers begin to exist.
  That is a documentation-and-policy deliverable, not just code.

## Decisions taken head-on

**1. The server is a third thin subscriber, not a new home for logic.** `nctl serve` lives in
the same package (`nctl_core.serve`), wraps the same library functions the CLI calls, and
returns the same `nctl.<command>.v1` envelope documents as JSON bodies. If an endpoint needs
behavior the library doesn't expose, the fix is to extend `nctl_core`, never to fork logic
into the server. A game-engine UI talking to this API and an operator running the CLI must be
indistinguishable to the rest of the system.

**2. FastAPI + uvicorn, as optional dependencies.** pydantic v2 is already the schema layer,
so FastAPI gives request/response validation and a generated OpenAPI document (the machine-
readable contract future UIs code against) for free. The server stack is an extra
(`nctl[serve]` / a `serve` dependency group); plain CLI installs don't grow ASGI dependencies.
Default bind is `127.0.0.1:8300`; exposing on the LAN requires explicitly configuring
`[serve].host`. WebSocket support comes from the same stack (`uvicorn` standard extras).

**3. Reads are snapshots; every computation or mutation is an operation.** GET endpoints never
trigger GraphQL fetches, Ansible, or Jobs — a fresh `build_drift` alone takes long enough that
hiding it behind a GET would make response times and side-effect boundaries unpredictable.
Instead:

- GET endpoints serve the **latest persisted artifacts**: last drift payload, last dashboard
  data, operation records and their artifact files.
- Anything that computes or changes state — drift refresh, dashboard regeneration, renders,
  reconcile plan/apply — is created with `POST /api/v1/operations`, returns `202` with an
  `operation_id` immediately, and reports progress through the event stream. This maps
  one-to-one onto the CLI's operation model, so `result.json`/event artifacts stay identical
  regardless of who triggered the run.

**4. One mutating operation at a time, enforced where it already is.** The server keeps an
in-process single-flight registry (one running mutating operation; additional mutating POSTs
get `409` with the running operation's ID — no hidden queue whose contents can go stale
between submission and execution). Underneath, the executor still acquires the Phase 4 file
lock, so a human running `nctl reconcile --yes` in a terminal and a server-triggered run
cannot race each other. Read-only operations (drift refresh, plan-mode reconcile, renders to
a scratch path) may run concurrently with each other but are also serialized against applying
runs — Phase 4's reasons (inventory replacement, Job races) apply to the server unchanged.

**5. Auth is one static bearer token, required by default, and boring.** `[serve]` config gets
`token_env = "NCTL_SERVE_TOKEN"` / `token_file` following the exact `NautobotConfig`
convention (inline token rejected by `extra="forbid"`). Every HTTP request requires
`Authorization: Bearer <token>`; the WebSocket handshake requires the same header (with a
`?token=` query fallback only for clients that cannot set headers, documented as such).
Startup fails fast if no token is resolvable — there is no accidental "auth off because
nothing was configured" mode; an explicit `auth = "none"` opt-out exists for loopback-only
experiments and refuses to combine with a non-loopback bind. Token comparison uses
`secrets.compare_digest`. The token never appears in logs, envelopes, events, or the OpenAPI
document.

**6. Event streaming = replay from file, then live from an in-process bus, joined by `seq`.**
`OperationLog` gains an optional subscriber callback (process-wide registry; emit stays
non-blocking and failure-isolated, same contract as the existing "never crash the command"
rule). A WebSocket client subscribes to one operation or to all operations, sends the last
`seq` it has (or `-1`), and the server replays newer records from the JSONL file before
switching to the live bus, deduplicating by (`operation_id`, `seq`). Because `seq` is
monotonic per operation and the file is the source of truth, a client can disconnect,
reconnect, and provably miss nothing. The JSONL file remains authoritative; the bus is a
latency optimization, not a second log.

**7. The event schema starts firming now: additive-only, with an explicit freeze document.**
Phase 5 writes `docs/compatibility.md` declaring, from this phase onward:

- the `EventRecord` shape (`ts`/`operation_id`/`op`/`seq`/`event`/`level`/`message`/`data`)
  is frozen; new information goes into `data` or new event names;
- the core event vocabulary (`started`/`step_*`/`warning`/`failed`/`finished`) and the
  reconcile vocabulary from Phase 4 are frozen in meaning; renames/removals require a
  documented major bump;
- `nctl.<command>.v1` envelopes may gain fields but never change/remove existing ones within
  `v1`; breaking changes mint `v2` alongside `v1` for a deprecation window;
- the HTTP/WS API carries `/api/v1/` in the path and follows the same additive rule.

This is deliberately a *policy freeze*, not a tooling project — schema snapshot tests pin the
current shapes so an accidental breaking change fails CI, and that is enough for this phase.

**8. The reference dynamic dashboard is a validation instrument, not a product.** One
build-toolchain-free HTML page (vanilla JS, inline assets, same visual language as the Phase 3
template) served by `nctl serve` at `/`. It fetches the latest drift snapshot over the REST
API, subscribes to the WebSocket, updates tiles when `finished`/`drift_resolved`/
`observation_completed` events arrive, and offers exactly two actions: "refresh drift" and
"reconcile (plan)" — both just POST operations. Applying reconcile stays CLI-only in this
phase; a mutation button on an unauthenticated-feeling LAN page is not worth the surprise
factor, and triggering mutation via the API remains proven by tests and `curl` instead. If
this page can be built against the documented API without touching the backend, the phase's
exit criterion ("a game-engine UI can be built on top without backend changes") is
demonstrated honestly.

## API contract (`/api/v1`)

All responses that correspond to CLI commands return the existing envelope documents
unchanged. Errors use HTTP status + the existing `EnvelopeError` shape
(`{code, message, detail}`); `401` unauthorized, `404` unknown ID, `409` single-flight
conflict, `422` validation, `503` not ready.

| Method & path | Meaning |
|---|---|
| `GET /api/v1/health` | liveness + version; the only unauthenticated endpoint |
| `GET /api/v1/status` | last `nctl.status.v1` snapshot (`?refresh=false` default) |
| `GET /api/v1/drift` | latest persisted `nctl.drift.v1` payload + its generated-at/operation ID |
| `GET /api/v1/operations` | recent operations (ID, op, state, timestamps), newest first |
| `GET /api/v1/operations/{id}` | one operation's record incl. terminal envelope/result if finished |
| `GET /api/v1/operations/{id}/events?after_seq=N` | historical events from the JSONL file |
| `GET /api/v1/operations/{id}/artifacts` / `.../artifacts/{name}` | list/fetch sanitized artifacts (`plan.json`, drift rounds, `result.json`); raw reports and anything mode `0600` are **not** served |
| `POST /api/v1/operations` | create an operation: `{"op": "drift" \| "dashboard" \| "render.dnsmasq" \| "render.production" \| "render.hosts_intent" \| "reconcile", "params": {...}}` → `202 {operation_id}` |
| `WS /api/v1/ws` | event stream; client sends `{"subscribe": "all" \| {"operation_id": ...}, "after_seq": N}` |
| `GET /` | the reference live dashboard page |
| `GET /openapi.json` | generated API description |

`POST` `params` mirror the CLI flags (`host`, `yes`, `max_rounds`, `out` confined below
configured directories). `op: "status"` with `refresh` is the one synchronous exception kept
cheap enough to compute inline. The drift snapshot answered by `GET /api/v1/drift` is whatever
the newest successful drift-producing operation (drift/dashboard/reconcile) persisted — the
server records that pointer; it never recomputes.

## Approach and implementation order

Steps 1–2 create the event-bus/operation-index groundwork inside `nctl_core` with no server
attached. Steps 3–5 build the server: skeleton + reads, then operation execution, then the
WebSocket. Step 6 adds the reference dashboard, Step 7 freezes schemas and documentation,
Step 8 proves everything live and closes out.

**Risks to verify first:**

- Confirm sync-in-thread execution of an applying reconcile under uvicorn on macOS behaves
  (signal handling, subprocess groups for Ansible, no event-loop starvation) before wiring
  mutation endpoints — prove it with a long fake operation first.
- Confirm the Phase 4 file lock's behavior when the acquirer is a server worker thread
  (flock semantics are per-process/fd; the in-process registry must prevent two server
  threads from both passing the file lock).
- Measure the size of a full-cluster `nctl.drift.v1` payload and a reconcile event log to
  sanity-check WS replay and artifact endpoints (expected well under a megabyte; if not,
  pagination gets designed before, not after, the dashboard consumes it).

## Step 1 — Event bus and operation index in `nctl_core`

- `nctl_core.events`: add a process-wide subscriber registry
  (`subscribe(callback) -> unsubscribe`), called from `OperationLog._write` after a
  successful file append. Callbacks run under the same isolation contract as the file write:
  an exception is reported once to stderr and swallowed; a slow subscriber must not block
  `emit` (bounded per-subscriber queue, drop-oldest with a `warning` counter — correctness
  comes from file replay, not the bus).
- `nctl_core.operations_index`: enumerate operations from `events.log_dir` (JSONL files +
  operation directories), parse first/last records for op/state/timestamps, locate
  `result.json`/`plan.json`/drift artifacts, and expose typed records. Pure filesystem reads,
  usable by CLI and server alike; add `nctl ops list` / `nctl ops show <id>` as a thin CLI
  view so the index is testable and useful before the server exists.
- Tests: subscriber isolation (raising/slow subscribers), ordering vs. file content, index
  over real Phase 4 operation directories (fixture copies), corrupted/partial JSONL lines.

## Step 2 — `[serve]` config and server skeleton with read endpoints

- Config: strict `[serve]` section — `host = "127.0.0.1"`, `port = 8300`,
  `token_env = "NCTL_SERVE_TOKEN"`, `token_file`, `auth = "token" | "none"` (with the
  non-loopback + `auth="none"` combination rejected at validation time), CORS origin list
  (empty default) for browser-based subscribers on other LAN hosts.
- `nctl_core.serve.app`: FastAPI app factory taking a loaded `Config`; auth dependency;
  `/health`, `/status`, `/drift`, `/operations*`, artifact endpoints. Artifact serving is
  allowlist-based (known filenames/patterns, path-confined below the operation directory,
  never following symlinks, never serving `reports/` or `probe-config/`).
- CLI: `nctl serve [--host] [--port] [--json]` — prints a startup envelope
  (`nctl.serve.v1`: bind address, auth mode, dashboard URL) then runs uvicorn in the
  foreground; SIGINT shuts down cleanly and refuses to interrupt a running mutating
  operation without logging its interrupted state (same semantics as CLI Ctrl-C in Phase 4).
- Tests: httpx `ASGITransport` against the app factory — auth required/rejected/none-mode,
  snapshot endpoints against fixture artifact trees, 404s, path-confinement attempts,
  OpenAPI generation.

## Step 3 — Operation executor and `POST /api/v1/operations`

- `nctl_core.serve.runner`: a worker that executes one operation callable on a thread,
  tracking state (`accepted → running → finished`), the resulting envelope, and exceptions.
  Mutating ops (`reconcile` with `yes=true`, dashboard with status push, renders writing to
  canonical inventory paths) register in the single-flight slot and acquire the Phase 4 file
  lock inside the thread; concurrent mutating POSTs get `409 {running_operation_id}`.
- Wire each supported `op` to its existing `nctl_core` build function, reusing the exact
  parameter validation the CLI performs (factor shared param models out of `cli/main.py`
  where needed rather than duplicating checks).
- The response of `POST` is intentionally minimal (`202`, `operation_id`, links to the
  events/WS endpoints); the terminal envelope is fetched from
  `GET /operations/{id}` after `finished`, and is byte-identical to what the CLI's `--json`
  would have printed for the same run.
- Tests: fake long/failing/lock-contending operations, 409 behavior, state transitions,
  server shutdown during a running op, param validation parity with the CLI.

## Step 4 — WebSocket event streaming

- `WS /api/v1/ws`: authenticate, accept one subscribe message, replay from JSONL
  (`after_seq` cursor per operation) via the Step 1 index, then attach to the live bus;
  dedupe on (`operation_id`, `seq`); heartbeat ping; a client that can't keep up is
  disconnected with a close code telling it to reconnect-and-replay (the file makes that
  lossless), rather than being buffered unboundedly.
- Frames are exactly the `EventRecord` JSON already written to the file — no second wire
  schema.
- Tests: replay-then-live continuity under concurrent emission (no gap, no dup), multi-client
  fanout, slow-client disconnect, auth on handshake, subscribe-all vs. one operation.

## Step 5 — Reference live dashboard

- One static page served at `/`: initial render from `GET /api/v1/drift` +
  `GET /api/v1/operations`, live updates over the WebSocket, tiles/prose reusing the Phase 3
  visual language, an operations sidebar showing running/recent operations and their event
  tail, and the two POST actions from Decision 8 (drift refresh, plan-only reconcile).
- Token entry: pasted once into the page, kept in `sessionStorage`, sent as the bearer
  header/WS query param; never embedded in the served HTML.
- The page must use only the documented API — building it is the test that the API is
  sufficient. Any missing capability discovered here is fixed API-side, keeping the "no
  backend changes for new subscribers" claim honest.
- The Phase 3 static dashboard artifact (`nctl dashboard`) is untouched and remains the
  no-server path for humans.

## Step 6 — Compatibility policy and schema pinning

- Write `docs/compatibility.md` per Decision 7 (frozen event record shape, frozen event
  vocabularies, additive-only `v1` envelopes, `/api/v1` path versioning, major-bump rules).
- Add snapshot tests pinning: `EventRecord` field set, the documented event vocabulary list,
  each `nctl.<command>.v1` envelope's field skeleton, and the OpenAPI operation/path set —
  so removing/renaming anything fails CI with a pointer to the policy.
- Update `docs/event-log.md` and `docs/output-format.md` to reference the policy; note in
  both that external subscribers exist from Phase 5 onward.

## Step 7 — Documentation and closeout surface

- nctl README: `serve` section (config, auth, endpoint table, WS protocol, replay cursor,
  single-flight semantics, dashboard page), plus the `ops` subcommands from Step 1.
- Parent README: add `nctl serve` to the command list and one paragraph positioning it
  (local CLI remains primary; serve is the subscriber API for UIs/external processes).
- Example config: `[serve]` block in `example.nctl.toml` with the token-env convention and a
  loopback default.

## Step 8 — Live verification and report

- Preflight on the local environment (`localhost` Nautobot, reachable nodes `agpc` /
  `agstudio` per `.local/localenv_memo.md`):
  - start `nctl serve` with a token; verify `401` without it and success with it;
  - `GET /drift` returns the latest persisted payload; POST a drift refresh operation and
    watch it stream over the WS from `started` to `finished`;
  - POST a plan-mode reconcile for a reachable node; confirm the terminal envelope matches a
    CLI `nctl reconcile <host> --json` run byte-for-byte (modulo `operation_id`/timestamps);
  - trigger an applying reconcile **via the API with `curl`** on a reachable node while
    attempting a concurrent CLI `reconcile --yes` — prove the `409`/file-lock exclusion both
    ways, and confirm the event stream carries the full Phase 4 vocabulary live;
  - open the dashboard page from a second machine on the LAN (explicit `[serve].host`),
    watch a running operation update it live;
  - kill and restart the server mid-observation and prove a reconnecting WS client replays
    the gap losslessly from `after_seq`.
- Confirm no token (Nautobot or serve) appears in any event, artifact, envelope, or server
  log line produced during the above.
- Record commands, payload sizes, test counts, and any deviations in `p5/report*.md`;
  update submodule pointers in the parent repository.

## Out of scope

- TLS, user accounts, RBAC, audit trails beyond the existing operation artifacts — the
  roadmap's single-token LAN posture stands.
- Cancelling a running operation over the API. Phase 4's SIGINT semantics remain the only
  interruption path; a cancel endpoint needs careful Ansible/Job interruption design and no
  current subscriber needs it.
- Operation queueing/scheduling (submit-and-wait beyond the single-flight `409`), parallel
  mutating operations, or distributed/multi-controller locking.
- Serving raw nodeutils reports, probe configs, or any `0600` artifact over HTTP.
- The 3D/voice UI itself, any game-engine integration code, and MCP or client-specific AI
  skills — AI and future UIs consume the neutral HTTP/WS/JSON surface.
- A full JSON-Schema registry or codegen pipeline for the freeze; policy + snapshot tests
  are this phase's deliberate scope.
- Pushing the server beyond a foreground process (daemonization, launchd/systemd units) —
  documented as an operator concern, one example unit at most.

## Exit criteria (from roadmap, made checkable)

- [ ] An external process, using only HTTP + the documented token, can fetch the current
  state snapshot (`status`, latest drift), list and inspect past operations including their
  plan/drift/result artifacts, and trigger drift/render/dashboard/reconcile operations.
- [ ] An external process can subscribe over WebSocket and receive every event of an
  operation — including across its own disconnect/reconnect, proven by the `after_seq`
  replay test and a live kill/reconnect check.
- [ ] The terminal envelope of a server-triggered operation is identical to the CLI's
  `--json` output for the same run; the JSONL/artifact layout on disk is identical
  regardless of trigger path.
- [ ] A server-triggered applying reconcile and a CLI `reconcile --yes` exclude each other
  in both directions; concurrent mutating API requests receive `409` with the running
  operation's ID.
- [ ] All endpoints except `/health` reject unauthenticated requests; startup with no
  resolvable token fails unless loopback-only `auth="none"` is explicit; no serve/Nautobot
  token appears in any log, event, artifact, or response.
- [ ] The reference live dashboard runs against the documented API only, renders cluster
  drift, and updates live during a real operation viewed from a second LAN machine —
  demonstrating that a future game-engine UI needs no backend changes.
- [ ] `docs/compatibility.md` exists; snapshot tests pin the event record shape, event
  vocabulary, `v1` envelopes, and the OpenAPI surface, and fail on breaking changes.
- [ ] Live verification on the local cluster covers the happy path and the
  auth/lock/reconnect failure paths above, recorded with commands and payload sizes in
  `p5/report*.md`.

## Suggested commit order

1. nctl: event subscriber bus + operations index + `ops` CLI + tests (Step 1).
2. nctl: `[serve]` config, app factory, auth, read endpoints + tests (Step 2).
3. nctl: operation runner, single-flight, POST endpoints + tests (Step 3).
4. nctl: WebSocket streaming + replay tests (Step 4).
5. nctl: reference live dashboard page (Step 5).
6. nctl: compatibility policy doc + schema snapshot tests + doc updates (Step 6).
7. nctl + parent: README/example-config updates (Step 7).
8. All: live verification fixes, submodule pointers, `p5/report*.md` (Step 8).
