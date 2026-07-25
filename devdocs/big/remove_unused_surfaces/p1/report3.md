# Phase 1 Step 3 — Delete the server and subscriber bus

Parent: [plan.md](plan.md), Step 3.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Deletions

All 8 tracked files under `src/nctl_core/serve/` and all 7 dedicated serve/bus test files, matching
the plan's frozen §5.1 manifest exactly:

```text
src/nctl_core/serve/__init__.py
src/nctl_core/serve/app.py
src/nctl_core/serve/artifacts.py
src/nctl_core/serve/dashboard.py
src/nctl_core/serve/live_dashboard.html
src/nctl_core/serve/runner.py
src/nctl_core/serve/runtime.py
src/nctl_core/serve/snapshots.py
tests/test_cli_serve.py
tests/test_events_bus.py
tests/test_serve_app.py
tests/test_serve_dashboard.py
tests/test_serve_operations.py
tests/test_serve_runner.py
tests/test_serve_ws.py
```

## `events.py` reduced to the frozen durable contract

Removed `Subscriber`, `_SubscriberEntry`, `_subscribers`, `_subscribers_lock`, `subscribe()`,
`_publish()`, the `_publish(record)` call after a successful write, and the now-unused
`threading`/`deque`/`Callable` imports. `generate_ulid()`, `EventRecord` (exact frozen 8-field
shape), and `OperationLog.start()`/`emit()`/`finish()`/`_write()` are unchanged byte-for-byte
except for the deleted publish call.

## `test_compatibility_snapshots.py` edits

Removed:

- `import asyncio`, `import httpx`, `from fastapi.openapi.utils import get_openapi` (used only by
  the four deleted HTTP/WS tests);
- `from nctl_core.serve.app import create_app`, `from nctl_core.serve.runtime import ServeData`,
  and the now-unused `from nctl_core.config import Config`;
- the `"nctl.serve.v1": (ServeData, ...)` entry from `FROZEN_DATA_FIELDS`;
- the `FROZEN_API_V1_PATHS` set;
- the `_config()` helper (used only by the four removed tests); and
- `test_openapi_paths_are_a_superset_of_the_frozen_v1_surface`,
  `test_websocket_route_is_registered_even_though_openapi_omits_it`,
  `test_create_operation_post_is_registered_on_operations_path`, and
  `test_health_response_shape_is_stable`.

Retained unchanged: all dashboard/reconcile compatibility fields, including `ReconcileData`'s
`dashboard` field and `nctl.dashboard.v1`'s full field set — both stay frozen for Phase 2.

## Focused verification

- `uv run pytest -q tests/test_events.py tests/test_compatibility_snapshots.py
  tests/test_operations_index.py tests/test_cli_ops.py`: **33 passed**.
- Static dashboard scope guard — `uv run pytest -q tests/test_cli_dashboard.py
  tests/test_dashboard_render.py tests/test_dashboard_html.py tests/test_dashboard_push.py`:
  **29 passed**, unaffected.

## Full suite

`uv run pytest -q`: **980 passed**, zero failures/errors/collection issues.

980 reconciles exactly with the plan's expected arithmetic: 1029 baseline + 5 net new Step 1
regression tests (+3 `test_cli_surface.py`, +1 net in `test_config.py` after replacing 2 serve
tests with 1, +2 `test_events.py`, +1 `test_operations_index.py`) − 54 deleted (50 dedicated
serve/bus tests + 4 compatibility HTTP/WS tests) = 980.

## Gate

No server package/import/route/schema/test remains, durable event tests pass, `ops` remains
independent of the deleted server, and Phase 2 dashboard tests still pass. Proceeding to Step 4.
