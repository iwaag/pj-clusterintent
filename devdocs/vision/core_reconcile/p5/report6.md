# Phase 5 Report — Step 6 (Compatibility policy and schema pinning)

Date: 2026-07-20. Implements [p5/plan.md](plan.md) Step 6 — the Decision 7 policy freeze plus
snapshot tests that enforce it. This is the sixth suggested commit boundary; the reference
dashboard (Step 5) is untouched, and Step 7 (README/example-config documentation) remains open.

## What was built

### `docs/compatibility.md` (new)

States, from Phase 5 onward, exactly what is frozen and what "frozen" means (additive-only;
renames/removals require a documented major bump, never an in-place `v1`/`/api/v1` change):

1. `EventRecord` field set (`ts`/`operation_id`/`op`/`seq`/`event`/`level`/`message`/`data`).
2. The event vocabulary — core (`started`/`step_started`/`step_completed`/`warning`/`failed`/
   `finished`), `apply dnsmasq`'s four events, the Phase 4 `reconcile` vocabulary, and the shared
   observation events (`collection_started`/`reports_retrieved`) — 20 names total, gathered by
   grepping every `op.emit("...")` / `operation_log.emit("...")` call site in `src/nctl_core`
   rather than assumed from the existing docs, which turned up two events
   (`collection_started`, `reports_retrieved`) that `event-log.md` didn't previously enumerate
   by name.
3. The `Envelope`/`EnvelopeError` wrapper fields, and a table pinning every current
   `nctl.<command>.v1` schema to its `data` model (11 schemas: `status`, `drift`, `dashboard`,
   `apply.dnsmasq`, `render.dnsmasq`, `render.production`, `render.hosts_intent`, `reconcile`,
   `ops.list`, `ops.show`, `serve`).
4. The `/api/v1/*` HTTP surface plus `WS /api/v1/ws`, noting explicitly that FastAPI's
   `get_openapi()` does not enumerate WebSocket routes — so the WS path is pinned by name
   against the ASGI route table in tests, not the OpenAPI document.

### `tests/test_compatibility_snapshots.py` (new, 8 tests)

- `EventRecord` and `Envelope`/`EnvelopeError` field sets checked as `<=` (superset) against the
  frozen sets — additions pass, a rename/removal of any frozen field fails.
- Event vocabulary: since there is no in-code registry of event names (the vocabulary is
  intentionally open per `event-log.md`), the test greps every `.py` file under `src/nctl_core`
  for each frozen name as a quoted string literal. A rename at the call site (e.g.
  `"actuation_completed"` → `"actuation_done"`) makes the old literal disappear and fails the
  test with the missing name(s) named explicitly.
- Each schema's `data` model (imported directly, e.g. `ReconcileData`, `DriftData`) is checked
  against its frozen field set the same way — one dict literal in the test enumerates every
  schema-to-model-to-fields mapping from the compatibility doc's table. Building this dict
  required reading each `*_render.py`/`executor.py`/`ops_render.py`/`runtime.py` module directly
  (an initial guess at `DnsmasqApplyData`'s render-summary field name — `render` — was wrong;
  it's `render_summary`, caught immediately by running the test rather than assumed).
- OpenAPI: `get_openapi()` against a fresh `create_app()` instance, asserting the frozen
  `/api/v1/*` path set is a subset of what's registered (same pattern as the existing
  `test_openapi_contains_step2_read_surface` in `test_serve_app.py`, generalized into the
  frozen-surface list). A separate test confirms `POST` is registered on `/api/v1/operations`
  specifically (the one path with two methods). A third test walks `app.router.routes` directly
  to confirm `/api/v1/ws` exists, documenting in its body why this can't go through the OpenAPI
  document.
- `test_health_response_shape_is_stable` exercises `GET /api/v1/health` end-to-end via
  `httpx.ASGITransport` as a smoke test that the frozen surface is actually live, not just
  present in the route table.

### `docs/event-log.md` / `docs/output-format.md`

Each gained a one-paragraph callout at the top pointing to `compatibility.md` and stating that
external subscribers now read these formats over HTTP/WS, so the shapes below are subject to the
freeze — per the plan's explicit doc-update bullet.

## Tests

- New: `tests/test_compatibility_snapshots.py`, 8 tests, all passing.
- Full suite: **503 passed** (`UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q`, ~4.0s). Step 5
  had 495; this step adds 8.
- `git diff --check`: clean.

## Deliberate boundaries and notes for Step 7+

- This is a policy-and-tests deliverable per the plan's own scoping ("not a tooling project") —
  no JSON-Schema registry, no codegen, no runtime event-name registry in `src/nctl_core` itself.
  The event-vocabulary test intentionally works by grepping source text rather than adding a new
  production-code enum, so nothing about the runtime's actual behavior changed in this step.
- `GET /`, `GET /openapi.json` are explicitly called out in `compatibility.md` as
  server-infrastructure routes outside the versioned contract, matching how `app.py` already
  treats `/` (unauthenticated, alongside `/health`, for the reasons Step 5's report gave).
- Step 7 (README/example-config updates) and Step 8 (live verification closeout) are unaffected
  by and do not depend on any code change in this step — only on the doc now existing to link to.

## Suggested commit boundary

- nctl: `docs/compatibility.md`, `tests/test_compatibility_snapshots.py`, and the
  `docs/event-log.md`/`docs/output-format.md` callout edits.
- parent: this report plus the updated nctl submodule pointer after the nctl commit is created.
