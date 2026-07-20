# Phase 5 Report — Step 7 (Documentation and closeout surface)

Date: 2026-07-20. Implements [p5/plan.md](plan.md) Step 7 — README/example-config documentation
for `nctl serve` and the Step 1 `ops` CLI, so the API surface frozen in `docs/compatibility.md`
(Step 6) is actually discoverable without reading source. This is the seventh suggested commit
boundary; no `nctl_core`/CLI behavior changed. Step 8 (live verification and closeout) remains
open.

## What was built

All changes are documentation-only; the full test suite (503 tests) was re-run afterward purely as
a sanity check that nothing was touched by accident — it passed unchanged.

### `nctl/README.md`

- Added `ops list` / `ops show` usage examples to the top `Usage` block, and a prose subsection
  under `reconcile` explaining that both are a filesystem-only, no-live-process view over
  `[events].log_dir` (`nctl.ops.list.v1` / `nctl.ops.show.v1`), backed by the same
  `nctl_core.operations_index` module the server's `/api/v1/operations*` endpoints use — written
  by reading `main.py`'s actual `ops_app` wiring and `ops_render.py`'s field names rather than
  assumed from the plan.
- New `## Serve (realtime API)` section, built by reading `serve/app.py`, `serve/runner.py`,
  `serve/runtime.py`, and `config.py`'s `ServeConfig` directly rather than restating the plan's
  Decisions 2–8 from memory (the plan predates the implementation and a couple of details drifted,
  caught here — see below):
  - **Config and auth**: the `[serve]` block, the `token_env`/`token_file` convention mirrored from
    `[nautobot]`, the fail-fast-on-missing-token startup check, and the loopback-only constraint on
    `auth = "none"`.
  - **Endpoints table**: all nine routes read directly off `app.py`'s route decorators (`/health`,
    `/status`, `/drift`, `/operations` list/show/events/artifacts, `POST /operations`, `WS /ws`,
    `/`, `/openapi.json`), with the actual `202` response shape
    (`operation_id`/`op`/`mutating`/`events_url`/`ws_url`) and error codes (`401`/`404`/`409`/
    `422`/`503`).
  - **Single-flight execution**: documented against `runner.py`'s actual `is_mutating()` rule —
    `dashboard` is unconditionally mutating (it always pushes statuses), `reconcile` only with
    `yes=true`, and the two renders only with `write=true` — plus the file-lock relationship to
    Phase 4. The plan's own Decision 4 text describes `dashboard regeneration` as an always-mutating
    example consistent with this, so no plan correction was needed here, but it was verified against
    code rather than assumed.
  - **WebSocket protocol and replay**: the actual subscribe message shape, `after_seq` semantics,
    replay-then-live dedup by `(operation_id, seq)`, and the three application close codes the code
    defines (`4400` bad subscribe, `4401` unauthorized, `4408` slow consumer) — the plan only
    mentioned "a close code telling it to reconnect," so the concrete codes are new information
    added here, not restated.
  - **Reference live dashboard**: what `GET /` actually offers today (refresh drift, plan-only
    reconcile), token handling via `sessionStorage`, and its relationship to the untouched static
    `nctl dashboard` artifact.
  - A closing pointer to `docs/compatibility.md` for the freeze policy.

### `nctl/example.nctl.toml`

Added a `[serve]` block (`host`, `port`, `token_env`, commented `token_file`, `auth`,
`cors_origins`) immediately after `[dashboard]`, matching `ServeConfig`'s actual field set and
defaults, with a one-line note that `nctl serve` requires the optional `serve` extra. Re-parsed
with `tomllib` after editing to confirm it stays valid TOML; no test references this file's exact
contents (`grep` for `example.nctl.toml` under `tests/` returned nothing), so no test changes were
needed.

### Parent `README.md`

- Added `uv run --project nctl --extra serve nctl serve` to the top-level command list.
- Added one paragraph after the existing `reconcile` paragraph positioning `nctl serve`: same
  `nctl_core` functions over HTTP/WebSocket with single-token LAN-only auth, for external
  processes/future UIs as "just another subscriber," CLI remains primary, with links to
  `nctl/README.md#serve-realtime-api` and `devdocs/vision/core_reconcile/p5/`.

## Verification

- `python3 -c "import tomllib; tomllib.load(open('example.nctl.toml','rb'))"` — valid TOML.
- `UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q` — **503 passed**, unchanged from Step 6 (this
  step touches no `src/`/`tests/` files).
- No behavior, schema, or config-parsing change; `git diff --stat` in `nctl/` touches only
  `README.md` and `example.nctl.toml`.

## Deliberate boundaries and notes for Step 8

- Nothing in this step required a plan correction beyond the two "written from code, not restated
  from the plan" call-outs above (the WS close codes, and confirming rather than assuming the
  dashboard-mutating rule) — the plan's Decisions 2–8 held up against the actual Step 2–5
  implementation.
- Step 8's live verification (real `nctl serve` run, `curl`/WS smoke tests, second-LAN-machine
  dashboard check, kill/reconnect replay proof) is unaffected by this step and is the only Phase 5
  work remaining before the roadmap's exit criteria can be checked off.

## Suggested commit boundary

- nctl: `README.md`, `example.nctl.toml` (this step).
- parent: `README.md` plus this report, with the updated nctl submodule pointer after the nctl
  commit is created.
