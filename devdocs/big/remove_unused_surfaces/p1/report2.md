# Phase 1 Step 2 — Remove CLI and configuration entry points

Parent: [plan.md](plan.md), Step 2.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Edits

- `src/nctl_core/cli/main.py`: removed `from nctl_core.serve.runtime import ...`, narrowed the
  `nctl_core.config` import to `Config, ConfigError` (dropped `ServeConfig`), and deleted the
  `serve` command function plus its `ServeHostOption`/`ServePortOption`/`ServeJsonOption`
  definitions. `ConfigInvalidError` had no remaining use outside the deleted command and was
  dropped from the import too.
- `src/nctl_core/config.py`: removed `ServeConfig`, `Config.serve`, and `_is_loopback_host()`.
  Removed now-unused imports `ipaddress`, `Literal`, and `model_validator` (checked actual
  remaining uses first — none of the three appear anywhere else in the file).
- `example.nctl.toml`: removed the `[serve]` section only; `[dashboard]` and every other section
  are untouched.
- `tests/test_cli_surface.py`: the Step 1 substring assertion (`"serve" not in result.stdout`)
  produced a false positive against `"observer"` in the `actual` command's help text. Replaced it
  with an exact-set comparison against Click's registered top-level command names
  (`typer.main.get_command(main.app).commands`), which is also a strictly stronger proof than a
  text search.

No other mixed test file required a Step 2 edit: `tests/test_config.py`'s serve cases were already
replaced in Step 1, and `tests/test_compatibility_snapshots.py`'s serve imports/schemas are Step 3
scope (still-present `nctl_core.serve` package).

## CLI/config contract results

- `uv run pytest -q tests/test_config.py`: **23 passed**, including
  `test_serve_section_is_rejected_as_unknown`, which now passes (was the Step 1 intentional
  failure).
- `uv run pytest -q tests/test_cli_surface.py`: **3 passed**, including both former Step 1
  intentional failures — `Config` has no `serve` field and no runtime `serve` command registration
  survives.
- `uv run nctl --help`: `serve` absent from the command table (verified both by the registered-set
  test above and manually — no exact `serve` command row).
- `uv run nctl serve`: exit code **2**, prints `Error: No such command 'serve'.` — Typer's ordinary
  unknown-command failure, not a custom retirement message or hidden compatibility path.
- Static dashboard scope guard: `uv run pytest -q tests/test_cli_dashboard.py
  tests/test_dashboard_render.py tests/test_dashboard_html.py tests/test_dashboard_push.py` —
  **29 passed**, unaffected by the CLI/config edit.

## Full-suite state (expected, not a Step 2 gate)

`uv run pytest -q` fails to collect: `tests/test_serve_app.py` still does
`from nctl_core.config import Config, ConfigInvalidError, ServeConfig`, which now raises
`ImportError`. This is expected — the six dedicated serve test files and `nctl_core/serve/` itself
are Step 3's deletion, not Step 2's. Step 2's own gate (CLI has no serve entry point, obsolete
config fails closed, static dashboard unaffected) is satisfied without touching them.

## Gate

The CLI has no `serve` entry point, the obsolete `[serve]` config fails closed under strict
validation, and the static dashboard still loads and appears in help. Proceeding to Step 3.
