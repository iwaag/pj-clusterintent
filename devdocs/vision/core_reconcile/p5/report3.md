# Phase 5 Report — Step 3 (Operation executor and `POST /api/v1/operations`)

Date: 2026-07-19. Implements [p5/plan.md](plan.md) Step 3 — the worker-thread operation
executor, the single-flight/readers-writer coordination described in Decision 4, and
`POST /api/v1/operations` wired to all six documented ops. This is the third suggested commit
boundary. `/api/v1/ws` (Step 4) and the reference dashboard (Step 5) remain untouched.

## What was built

### `nctl_core.serve.runner` — the operation executor

- **Param models per op** (`DriftParams`, `DashboardParams`, `RenderDnsmasqParams`,
  `RenderProductionParams`, `RenderHostsIntentParams`, `ReconcileParams`), all strict
  (`extra="forbid"`) pydantic models. `parse_params(op, raw)` returns `RunnerError(
"unsupported_op", ...)` for an unknown `op` and `RunnerError("validation_error", ...)` (with
  the pydantic error list in `detail`) for bad params — both become `422`.
- **`out` becomes `write: bool`, not a path.** The plan's "`out` confined below configured
  directories" is implemented as a boolean flag rather than an accepted path: `render.production`
  / `render.hosts_intent` have exactly one canonical destination
  (`cfg.ansible.resolved_inventory(...).parent`, matching the CLI docstrings' "pass the directory
  containing the configured `ansible.inventory` path"), so `write=true` targets that directory and
  there is no arbitrary-path case to validate or reject. `render.dnsmasq` has no configured
  canonical destination (`apply dnsmasq` is the real deployment path), so it stays compute-only
  over the API — no write option is exposed for it at all.
- **Mutating classification** (`is_mutating`): `dashboard` is always mutating (it writes the
  configured out dir and, unless `no_push`, pushes statuses to Nautobot); `reconcile` only with
  `yes=true`; `render.production`/`render.hosts_intent` only with `write=true`; `drift` and
  `render.dnsmasq` are always read-only.
- **`_Gate`: a non-blocking readers-writer lock**, not a queue. Mutating ops hold the writer slot
  (exclusive against everything); read-only ops are readers (any number run together, excluded by
  an active writer). An op that cannot start immediately fails with
  `RunnerError("operation_conflict", ..., {"running_operation_id": ...})` — the caller gets `409`
  and an ID to poll, not a promise of a later slot, matching the file lock's own no-queue
  semantics.
- **`OperationRunner.submit(op, params)`**: parses params, classifies mutating-ness, generates the
  `operation_id` (`events.generate_ulid()`) and registers it with the gate *synchronously* — so a
  `409` is returned before any thread is spawned — then starts a daemon worker thread and returns
  an `OperationHandle` immediately (`202`-able). The gate is released in a `finally` block
  regardless of success/exception.
- **Two execution shapes**:
  - `reconcile` already owns its `OperationLog`/`OperationArtifacts` lifecycle (Phase 4); the
    runner only threads the pre-generated `operation_id` through so the ID in the `202` response
    matches the JSONL file the worker thread goes on to write (see `run_reconcile`'s new
    `operation_id` parameter below).
  - `drift`/`dashboard`/`render.*` have no such lifecycle under the CLI (deliberately: they are
    synchronous, side-effect-free-by-default reads/renders with no event log). `_wrapped` gives
    each a real one *for the duration of a server-triggered run only* — `OperationLog(op_label,
    log_dir, operation_id=...)`, `started`, call the existing build function unmodified, persist
    `result.json`, `finished` — so `nctl ops show`/`GET /operations/{id}` can see server-triggered
    drift/dashboard/render runs exactly like a reconcile run. The CLI paths for these commands are
    untouched: no operation ID, no event log, as before.
- **`result.json` is written before the `finished` event, not after.** Verified live (see below):
  emitting `finished` first left a real, observable window where a poller saw `state: "finished"`
  but `result: null` because the artifact directory hadn't been created yet on another thread.
  Both `_wrapped` and reconcile's `_finish` (see next section) now persist first and emit
  `finished` second, so any reader that observes the terminal event is guaranteed to find the
  result already in place.
- **`result.json` is public, not the private 0600 default.** `OperationArtifacts.write_json`
  writes 0600 by design (Phase 4's private-artifact default); the runner explicitly `chmod`s the
  written `result.json` to `0644` afterward, matching Step 2's artifact allowlist, which already
  expects `result.json` to be one of the servable names, and matching Step 2's own test fixture
  convention (`tests/test_serve_app.py::_write_result`).

### `nctl_core.reconcile.executor` — `result.json` persistence and a pre-assignable `operation_id`

Step 2's report flagged that Phase 4 never actually persisted a terminal `result.json`. This step
closes that gap **for both trigger paths at once**, in the library rather than only in the server:

- `run_reconcile(..., operation_id: str | None = None)`: the previous `OperationLog.start(...)`
  call is replaced with the equivalent explicit `OperationLog(..., operation_id=operation_id)` +
  `.emit("started", ...)` — behaviorally identical when `operation_id` is `None` (a new ULID is
  still generated), and lets the Step 3 runner control the ID for server-triggered runs.
- `_finish(...)` now calls a new `_persist_terminal_result(artifact_dir, envelope)` — writes the
  full terminal envelope as `result.json` (mode `0644`) into the run's existing
  `OperationArtifacts` directory, for every terminal state (`planned`, `already_converged`,
  `converged`, `manual_intervention_required`, `non_converged`, `failed`), before calling
  `op.finish(...)`. A write failure is swallowed (never turns a completed reconcile into a
  reported failure), matching the "never crash the command" contract already used for event-log
  writes.
- Net effect: `nctl reconcile` from the CLI now also gets a persisted `result.json`, so the exit
  criterion "the JSONL/artifact layout on disk is identical regardless of trigger path" holds by
  construction rather than needing separate server-side bookkeeping.

### `POST /api/v1/operations` (`nctl_core/serve/app.py`)

- Body: `{"op": "drift" | "dashboard" | "render.dnsmasq" | "render.production" |
  "render.hosts_intent" | "reconcile", "params": {...}}`. Missing/non-string `op`, a non-object
  `params`, or a non-JSON body all return `422 validation_error`.
- Delegates to `OperationRunner.submit`; `RunnerError` becomes an `ApiError` via a small
  `{code: status}` map (`operation_conflict` → `409`, everything else → `422`), reusing the
  existing `ApiError`/`EnvelopeError` machinery from Step 2 — no new error shape.
- Success: `202 {"operation_id", "op", "mutating", "events_url"}`. The terminal envelope is not
  echoed here by design (Decision 3): callers fetch `GET /api/v1/operations/{id}` once `state`
  reaches `"finished"`, which is now byte-identical to what the CLI's `--json` would have printed
  (Step 2's reader already prefers the newest persisted `result.json`; nothing there needed to
  change).
- The `OperationRunner` instance is created once per `create_app(cfg)` call and stored on
  `app.state.nctl_runner` (alongside the existing `app.state.nctl_config`) — one runner per running
  server process, matching the plan's in-process single-flight registry.

## Tests

- `tests/test_serve_runner.py` (13 tests): param parsing/validation per op, the mutating-ness
  rules, `_Gate` in isolation (writer-blocks-writer with the blocking ID reported, readers stack
  freely, writer blocks new readers and vice versa), `OperationRunner.submit` for a wrapped op
  (events written, `result.json` present at `0644` with the right schema/`ok`), a failing wrapped
  op (still finishes cleanly, `ok: false` persisted, no crash), `render.production` write-flag
  routing to the canonical directory vs. staying compute-only, and single-flight conflict
  detection with the correct `running_operation_id` surfaced to both a second mutating attempt and
  a concurrent read-only attempt.
- `tests/test_serve_operations.py` (4 tests, ASGI/`httpx.ASGITransport` against `create_app`):
  auth required, malformed-body/unsupported-op/extra-param `422`s, a full `202` → poll →
  `state: "finished"` → `GET .../events` round trip for a faked `drift` op, and a live `409` with
  `running_operation_id` from two concurrent `reconcile(yes=true)` POSTs against a fake
  `run_reconcile` gated by a `threading.Event`.
- `tests/test_reconcile_executor.py` (+2 tests): `result.json` is persisted at `0644` with the
  envelope's exact `schema`/`ok`/`state` for a plan-mode run, and a caller-supplied `operation_id`
  is honored end-to-end (JSONL file named accordingly).
- Full suite: **481 passed** (`UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q`, 3.5–4.4s). Step 2
  had 462; this step adds 19.
- `git diff --check`: clean.

## Live verification against the real cluster config

Started the real server against the checked-in `nctl.toml` (`NAUTOBOT_TOKEN` +
`NCTL_SERVE_TOKEN=smoke-test-token`, port 18301) and drove it with `curl`:

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"op":"drift","params":{}}' http://127.0.0.1:18301/api/v1/operations
# 202 {"operation_id":"01KXXFA304FGT4G64XWTFQNT5N","op":"drift","mutating":false,...}

curl -s -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:18301/api/v1/operations/01KXXFA304FGT4G64XWTFQNT5N
# state: "finished", artifacts: [{"name":"result.json","size_bytes":609}], result: {...}
```

Observed:

- `401` with no token, `422 unsupported_op` for `{"op":"bogus"}`, `422 validation_error` for an
  extra param.
- The drift operation ran end-to-end through the real worker thread and persisted a real
  `result.json`; it reported `ok: false` with `nautobot_fetch_failed` (`Connection reset by peer`
  talking to the dev environment's Redis via `host.docker.internal` — a pre-existing local infra
  issue unrelated to this change, not a code defect) rather than crashing the server or leaving
  the operation stuck.
- Two concurrent `POST {"op":"dashboard"}` requests: the first returned `202`; the second returned
  `409 operation_conflict` with `running_operation_id` equal to the first's `operation_id`, fired
  from a real second connection while the first was still running, on the actual configured
  Nautobot/dashboard code path (not a test double).
- This run is also what surfaced the `finished`-before-`result.json` race described above — caught
  live against real timing, not only in unit tests, before it shipped.
- Server shut down cleanly (`pkill` + confirmed the port stopped answering).

No applying (`yes=true`) reconcile was triggered against the live cluster in this step — Step 8 is
the designated place for a live mutating run with a concurrent-CLI lock-exclusion proof, per the
plan's own scoping. This step's live check deliberately stayed within read-only and
already-Phase-4-exercised (`dashboard`, whose push already degrades to a reported failure rather
than `ok: false` on error) operations.

## Deliberate boundaries and notes for Step 4+

- The `202` response omits `ws_url` — Step 4 adds `/api/v1/ws`; wiring a link to an endpoint that
  doesn't exist yet would be misleading. `events_url` alone is enough for a client to poll today.
- `write: bool` instead of an accepted `out` path (see above) is this step's explicit
  interpretation of "params.out confined below configured directories" — recorded here since the
  plan's API contract table describes `out` more generally; there is exactly one canonical
  destination per render, so a boolean is the simplest correct encoding and avoids ever having to
  validate an attacker-influenced path.
- A worker-thread exception that occurs *before* an op's own `OperationLog` would emit `finished`
  (a genuine bug in a build function, not a modeled failure path) leaves the JSONL file showing
  `"running"` forever from the filesystem's point of view, even though the in-memory
  `OperationHandle.error` records it. This mirrors what already happens if `nctl reconcile` itself
  raises uncaught from the CLI (a traceback, no clean terminal event) and is out of this step's
  scope; nothing in the currently wired build functions is expected to raise past its own
  try/except boundaries in normal operation.
- `nctl serve`'s SIGINT handling still doesn't know about an in-flight mutating operation (Step
  2's boundary note); Step 3 was scoped to the executor and endpoint, not shutdown semantics. That
  remains open for Step 8's live verification pass, which explicitly covers "kill and restart the
  server mid-observation."
- `/api/v1/ws` (Step 4) and the reference dashboard (Step 5) are still absent by design.

## Suggested commit boundary

- nctl: `reconcile.executor` `operation_id` param + `result.json` persistence,
  `nctl_core.serve.runner`, the `POST /api/v1/operations` endpoint, and tests.
- parent: this report plus the updated nctl submodule pointer after the nctl commit is created.
