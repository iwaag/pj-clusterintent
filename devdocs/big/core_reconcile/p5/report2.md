# Phase 5 Report — Step 2 (`[serve]` config and read-only server skeleton)

Date: 2026-07-18. Implements [p5/plan.md](plan.md) Step 2 — the strict server
configuration, FastAPI application factory, authenticated snapshot/history endpoints, safe
artifact view, and foreground `nctl serve` CLI. This is the second suggested commit boundary.
There is deliberately no operation executor, POST endpoint, or WebSocket yet; those belong to
Steps 3 and 4.

## What was built

### Strict `[serve]` configuration (`nctl_core/config.py`)

`Config` now includes a strict `ServeConfig` with:

- `host = "127.0.0.1"` and `port = 8300` defaults (`port` is constrained to `1..65535`);
- `auth = "token" | "none"`, defaulting to `token`;
- `token_env = "NCTL_SERVE_TOKEN"` or `token_file`; an inline `token` remains impossible because
  `extra="forbid"` rejects it;
- `cors_origins = []` by default;
- validation that rejects `auth="none"` on anything except `localhost`, an IPv4 loopback, or an
  IPv6 loopback. A CLI `--host` override is revalidated through the same model, so it cannot
  bypass this rule.

Token auth fails before server startup if neither the configured environment variable nor token
file resolves to a non-empty value. Token checks use `secrets.compare_digest`, and the resolved
token is held only by the app's auth dependency — it is absent from envelopes, OpenAPI, events,
and logs.

### Optional server dependencies

FastAPI and `uvicorn[standard]` are exposed through the `nctl[serve]` optional extra and included
in the development dependency group for ASGI tests. `uv.lock` was regenerated. Imports are kept
behind `nctl_core.serve.app` / the lazy runtime adapter, so ordinary CLI commands do not import
FastAPI or uvicorn merely by loading `cli/main.py`.

### FastAPI read surface (`nctl_core/serve/app.py`)

`create_app(cfg)` builds `/api/v1` from an already-loaded `Config`. It exposes:

| Endpoint | Step 2 behavior |
|---|---|
| `GET /api/v1/health` | Unauthenticated liveness and installed nctl version |
| `GET /api/v1/status` | Latest successful persisted `nctl.status.v1`; `?refresh=true` is the documented synchronous exception |
| `GET /api/v1/drift` | Latest successful persisted `nctl.drift.v1` |
| `GET /api/v1/operations` | Newest-first public operation summaries, optional bounded `limit` |
| `GET /api/v1/operations/{id}` | Public operation record plus persisted terminal `result.json`, when present |
| `GET /api/v1/operations/{id}/events` | JSONL replay using the existing `after_seq` cursor |
| `GET /api/v1/operations/{id}/artifacts` | Sanitized public artifact list |
| `GET /api/v1/operations/{id}/artifacts/{name}` | Allowlisted JSON artifact content |
| `GET /openapi.json` | Generated contract, bearer-protected like every endpoint except health |

The API never returns the operation index's controller-local absolute `log_path` / `artifact_dir`
or private artifact names in operation summaries. Errors use the existing `EnvelopeError` shape
directly for `401`, `404`, `422`, and `503`, including FastAPI request-validation failures.
CORS middleware is installed only when the configured origin list is non-empty.

GETs do not perform GraphQL, Ansible, or Job work. Snapshot lookup reads successful
`result.json` envelopes produced under operation directories; for drift it also accepts the
existing Phase 3 `[dashboard].out_dir/drift.json` as a pre-runner fallback. The response body is
the original `nctl.<command>.v1` envelope unchanged. When the snapshot came from an operation,
its ID is carried separately as `X-Nctl-Operation-Id`. If no successful persisted snapshot exists,
the endpoint returns `503 snapshot_not_ready` rather than computing one invisibly.

### Artifact boundary (`nctl_core/serve/artifacts.py`)

The HTTP view is narrower than the local Step 1 operation index:

- accepted names are `plan.json`, `result.json`, `drift.json`, and
  `round-NN/drift-before.json` / `drift-final.json`;
- path traversal, absolute paths, unknown patterns, and every symlink component are rejected;
- `reports`, `probe-config`, `slurp`, `jobs`, and `ansible` path components are always denied;
- mode `0600` files are never exposed by the artifact list/fetch endpoints.

This intentionally means existing private Phase 4 artifacts do not suddenly become network-
readable just because the server is installed. Step 3 can persist explicitly public terminal
documents with the appropriate mode while leaving raw diagnostics private.

### `nctl serve` CLI (`nctl_core/serve/runtime.py`, `cli/main.py`)

`nctl serve [--host HOST] [--port PORT] [--json]` validates configuration and token availability,
prints the `nctl.serve.v1` startup envelope (bind host, port, auth mode, dashboard URL), and runs
uvicorn in the foreground. Uvicorn's normal SIGINT path shuts down cleanly. There cannot yet be a
server-owned mutating operation to protect during shutdown; the stronger interrupted-operation
semantics become actionable with the Step 3 runner.

## Verification

- Full nctl suite: **462 passed** (`UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q`, 3.83s).
  Step 1 had 447 tests, so Step 2 adds 15 tests across `test_config.py`,
  `test_serve_app.py`, and `test_cli_serve.py`.
- Config/CLI coverage includes defaults, strict keys, port bounds, env/file token resolution,
  inline-token rejection, loopback-only no-auth, override revalidation, startup envelope, and
  fail-fast missing-token behavior.
- ASGITransport coverage includes health/auth/none mode, persisted status/drift snapshots,
  dashboard drift fallback, `503` before a snapshot exists, explicit status refresh, operation
  list/detail/event replay, malformed/unknown IDs, standardized `422`, artifact allowlist,
  private-mode/report/symlink/traversal denial, hidden local paths, and OpenAPI generation/auth.
- `git diff --check`: clean.
- Foreground smoke test against the real configured event directory:

  ```bash
  NCTL_SERVE_TOKEN=<temporary> uv run --project nctl nctl serve \
    --config nctl.toml --host 127.0.0.1 --port 18300 --json
  curl -i http://127.0.0.1:18300/api/v1/health
  curl -i http://127.0.0.1:18300/api/v1/operations
  curl -i -H 'Authorization: Bearer <temporary>' \
    'http://127.0.0.1:18300/api/v1/operations?limit=1'
  ```

  Observed `200` health (`version: 0.0.1`), `401 unauthorized` without a token, and `200` with a
  public one-record operation summary under bearer auth. SIGINT then produced uvicorn's complete
  application shutdown sequence and exit 0.

## Deliberate boundaries and notes for Step 3

- Phase 4 did not in fact persist terminal `result.json` documents, as noted in Step 1's report.
  Consequently status normally returns `503` and drift uses the Phase 3 dashboard snapshot until
  Step 3's runner starts persisting terminal envelopes. This is a readiness response, not a hidden
  live computation.
- Step 3 should write `result.json` atomically and record the successful drift-producing operation
  pointer. The Step 2 reader already prefers the newest matching successful envelope, so no API
  route needs to change.
- `POST /api/v1/operations`, accepted/running/finished server state, single-flight coordination,
  result persistence, and shutdown behavior while a mutation is active remain wholly Step 3.
- `/api/v1/ws` remains Step 4; `/` remains the Step 5 live dashboard. Their absence here is
  intentional.
- The full README endpoint/protocol section and checked-in example `[serve]` block remain the
  explicit Step 7 documentation deliverable. This report records the Step 2 contract without
  pulling later phase surfaces forward.

## Suggested commit boundary

- nctl: strict serve config, optional server dependencies, read-only FastAPI app, safe artifact
  view, serve CLI, lockfile, and tests.
- parent: this report plus the updated nctl submodule pointer after the nctl commit is created.
