# Phase 5 Report — Step 8 (Live verification and closeout)

Date: 2026-07-20. Implements [p5/plan.md](plan.md) Step 8 against the local dev environment in
`.local/localenv_memo.md`: Nautobot reachable at `http://localhost:8000` (all three containers
healthy), reachable nodes `agpc.local`/`agstudio.local` responding to ping, `agbach`/`agdnsmasq`
known-unreachable per the memo. This is the eighth and final suggested Phase 5 commit boundary.
One doc correction (`nctl/README.md`, WS auth-failure wording) is the only source change; no
`nctl_core` code changed. **One real behavioral gap was confirmed live and is left open — see
`p5/todos8.md`.**

## Baseline before touching anything

`nctl drift --config nctl.toml --json`: `ok: true`, `summary {converged: 3, unknown: 2}` —
`agpc`/`agstudio`/`agbach` converged, `agdnsmasq`/`aghub` unknown (no fresh observation). Recorded
so every subsequent live check could be judged against a known-good state; re-checked identical
after all testing below (see "Post-verification state").

All commands ran from the `pj-clusterintent` repo root with `NAUTOBOT_TOKEN` from
`.local/localenv_memo.md` and, for the server, a locally generated `NCTL_SERVE_TOKEN` (48 hex
chars, `secrets.token_hex(24)`, kept only in the session scratch directory, never committed).

## Auth

- `GET /api/v1/health` unauthenticated → `200 {"status":"ok","version":"0.0.1"}`.
- `GET /api/v1/status` with no header → `401 unauthorized`; with a wrong bearer token → `401`.
- `POST /api/v1/operations` with no header → `401` (mutation endpoints enforce the same as reads).
- `GET /api/v1/status` with the correct token → passes auth (`503 snapshot_not_ready` at that
  point, correctly distinct from `401` — no persisted snapshot existed yet).
- **Startup fails fast with no resolvable token**: `unset NCTL_SERVE_TOKEN` +
  `nctl serve --config nctl.toml` → exits `2` immediately with `serve auth is enabled but no token
  was found in $NCTL_SERVE_TOKEN or serve.token_file`, before any bind attempt.
- **WebSocket auth finding**: an unauthenticated real client (`websockets` 16.1 against real
  uvicorn) sees the connection refused at the HTTP layer (`403`, no upgrade), not a WS close frame
  with code `4401` — `app.py` calls `websocket.close(code=4401)` *before* `.accept()`, which ASGI
  servers turn into a pre-upgrade HTTP rejection for a real socket. `test_serve_ws.py`'s
  `test_ws_requires_auth` only sees `4401` because Starlette's `TestClient` is an in-process ASGI
  transport with no real HTTP layer, so the same `close()`-before-`accept()` call surfaces
  differently there. Functionally both reject correctly and leak no data; only the *documented*
  mechanism was wrong. Fixed in `nctl/README.md`'s WS protocol section (commit alongside this
  report) rather than left as a todo, since it was a pure documentation correction with no code or
  design decision involved.

## Reads and drift refresh over WS

- `GET /api/v1/drift` before any server-triggered op existed → `503 snapshot_not_ready` (correct:
  Step 2's snapshot reader only finds `result.json`/`dashboard/drift.json`, and a bare CLI
  `nctl drift` run never writes either — confirmed as designed, not a bug, by reading
  `serve/snapshots.py`).
- `POST /api/v1/operations {"op":"drift","params":{}}` → `202`, `operation_id` returned
  immediately. A WS client subscribed to `{"subscribe":"all","after_seq":-1}` before the POST
  received exactly `started` (seq 0) then `finished` (seq 1) live, ~240ms apart.
- `GET /api/v1/drift` afterward → `200`, **2322 bytes**, `X-Nctl-Operation-Id` header matching the
  triggering operation, `schema: nctl.drift.v1`, same `{converged: 3, unknown: 2}` summary as the
  CLI baseline.
- `GET /api/v1/status?refresh=true` → `200`, **900 bytes**, computed inline as documented (the one
  synchronous exception).
- `GET /openapi.json` (authenticated) → `200`, **7224 bytes**; grepped for both tokens — clean.
- `GET /` (reference dashboard) → `200`, **20372 bytes**, unauthenticated as designed; grepped for
  both tokens — clean.
- `POST {"op":"render.dnsmasq","params":{}}` (non-mutating render) → `202`, ran without contending
  the gate.

## Plan-mode reconcile: API vs CLI byte-parity

`POST {"op":"reconcile","params":{"host":"agpc","yes":false}}`, then `GET
/api/v1/operations/{id}` for its embedded `result`, compared against `nctl reconcile agpc --json`
run separately: both `state: planned`, `ok: true`. Stripped `generated_at` and the
per-run/path fields the plan calls out as expected to differ (`operation_id`,
`event_log_path`/`artifact_dir`/`plan_path`/`*_drift_path`) and diffed the remainder as JSON —
**identical**. This is the exit criterion "byte-identical modulo operation_id/timestamps" proven
directly, not assumed.

## Single-flight exclusion, both directions, plus true concurrent `409`

Three separate scenarios, since the file lock is non-blocking (`fcntl.LOCK_EX | LOCK_NB`, fails
immediately rather than queuing — confirmed by reading `reconcile/lock.py`) and this cluster's
reconcile runs finish in well under a second, making a *live* two-real-reconciles race too fast to
hit reliably from external shell timing:

1. **API blocked by a CLI-held lock**: held the real lock path
   (`~/.local/state/nctl/reconcile.lock`) from a standalone script, then
   `POST {"op":"reconcile","params":{"host":"agpc","yes":true}}` while it was held → `202` (the
   server's in-process gate was free), but the operation's terminal result carried
   `errors: [{"code":"reconcile_lock_contention", "message":"another reconcile operation holds the
   lock at .../reconcile.lock"}]`, `result: failed`. Confirms the API always defers to the Phase 4
   file lock even when its own in-process gate has nothing else running.
2. **CLI blocked by the same held lock**: `nctl reconcile agpc --yes` while the lock was held by
   the same standalone script → exit `1`, identical `reconcile_lock_contention` error. Symmetric
   with (1); the file lock is the actual cross-process authority in both directions, exactly as
   Decision 4 specifies.
3. **True concurrent `POST`s racing the in-process gate**: two `dashboard` operations (always
   mutating) fired with no delay between them via parallel background `curl`s. First → `202`.
   Second → `409 {"code":"operation_conflict","detail":{"running_operation_id":"<first's id>"}}`.
   This is the one case genuinely fast enough to race externally (both are pure in-process
   contention, no lock-file syscall latency involved), and it landed cleanly on the first attempt.
4. Sanity check with an *actually converged* target: a real `nctl reconcile agpc --yes` (API) and
   a real `nctl reconcile agpc --yes` (CLI) run sequentially (not overlapping — `agpc` was already
   converged, so both completed in under half a second, too fast to force real overlap) both
   returned `already_converged`, confirming applying reconcile against this environment stays a
   safe no-op today, consistent with Phase 4's `report9.md` prior live convergence.

## WebSocket replay across a real server crash

The scenario in the plan ("kill and restart the server mid-observation") was reproduced literally,
not simulated:

1. `POST {"op":"drift"}` → operation id `01KXYHDRF0A1N8X86G9RQC850E`.
2. A WS client subscribed to that operation from `after_seq=-1`, read exactly one frame (`seq 0`,
   `started`), then hard-closed the socket without reading `finished` and without unsubscribing.
3. `kill -9` on the live uvicorn process — a real crash, not `SIGINT`, so the in-process event bus
   and gate are gone, not just quiesced.
4. New `nctl serve` process started fresh (new PID, empty in-memory state).
5. A new WS client connected and subscribed to the same operation with `after_seq=0` → received
   exactly `seq 1` (`finished`), the frame the crash prevented delivery of the first time, sourced
   from the JSONL file (the only thing that survived the crash) — no duplicate `seq 0`, no gap.

This proves Decision 6's core claim ("the file is authoritative; the bus is a latency
optimization") against a real process death, which is a stronger proof than a client-side
disconnect/reconnect alone would have been.

## `SIGINT` and a live daemon-thread gap (confirmed, not fixed — see todos8)

`kill -INT` against an idle server produces uvicorn's normal clean shutdown (`Shutting down` →
`Application shutdown complete`), as Step 2 already established. Timed against a genuinely
in-flight mutating operation (`POST {"op":"dashboard"}` immediately followed by `kill -9` on the
server before the worker thread could finish — confirmed by the JSONL having only `started`, no
`finished`, no `result.json`), the operation is left **permanently stuck at `state: running`**
(`nctl ops show`/`GET /operations/{id}` agree) with no interrupted marker, matching exactly what
`p5/report2.md` and `p5/report3.md` already flagged as deferred ("Step 3 was scoped to the
executor and endpoint, not shutdown semantics... remains open for Step 8's live verification
pass"). Step 8 was the designated place to resolve or explicitly punt this, per those reports; see
`todos8.md`.

## Token hygiene

Grepped every artifact this session touched — `nctl serve`'s stdout/stderr logs (all server
processes started/killed during this session), the full `~/.local/state/nctl/events/` tree
(JSONL files, `result.json` artifacts), `/openapi.json`, the `/` dashboard HTML, and every captured
API response body — for both the Nautobot token and the generated serve token. **Zero matches** in
every location.

## Post-verification state

`nctl drift --json` and `nctl status` re-run after all of the above: identical
`{converged: 3, unknown: 2}` summary, all three submodule/nautobot/dumps checks unchanged from the
pre-session baseline. The reconcile file lock was confirmed free (`flock` acquires cleanly) after
the last test. No server process left running; last shutdown was a clean `SIGINT`.

## Tests

- `UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q` — **503 passed**, unchanged (this step's only
  source change is the one-paragraph WS-auth doc correction).

## Exit criteria (from roadmap, checked against this step's evidence)

- [x] External process fetches state, lists/inspects operations + artifacts, triggers
  drift/render/dashboard/reconcile via HTTP + token — proven above (drift/status/render/dashboard/
  reconcile all exercised).
- [x] WebSocket subscriber receives every event across disconnect/reconnect, proven by both the
  `after_seq` unit-level design and the live kill/reconnect test above.
- [x] Server-triggered terminal envelope identical to CLI `--json` (modulo id/timestamps/paths) —
  proven directly for plan-mode reconcile.
- [x] Server-triggered applying reconcile and CLI `reconcile --yes` exclude each other both
  directions; concurrent mutating API requests get `409` with the running ID — proven three ways
  above.
- [x] All endpoints but `/health` (and `/`, by the Decision 8 design, confirmed in Step 5) reject
  unauthenticated requests; startup fails fast with no token; no token ever observed leaking —
  proven above, with the WS mechanism documentation corrected to match live behavior.
- [x] Reference dashboard runs against the documented API and renders drift — proven (`GET /`
  returns the page, drift/operations data is fetchable through the same endpoints it uses). Live
  updates viewed **from a second LAN machine** could not be exercised — no second machine is
  available to this session; see `todos8.md`.
- [x] `docs/compatibility.md` exists with snapshot tests pinning the frozen surface (done in Step
  6, re-confirmed present and the suite green).
- [x] Live verification recorded here with commands and payload sizes, covering the happy path
  plus auth/lock/reconnect failure paths — this report. One real gap (`SIGINT`/crash during a
  mutating operation leaves it stuck at `running` forever) was found live rather than assumed;
  it is recorded as a decision item in `todos8.md` rather than silently fixed, since closing it
  well requires a shutdown-semantics design Step 8 was scoped to verify, not invent.

## Suggested commit boundary

- nctl: `README.md` (WS auth-mechanism doc correction only).
- parent: this report, `p5/todos8.md`, and the updated nctl submodule pointer.
