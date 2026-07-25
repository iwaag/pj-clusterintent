# Phase 1 Step 1 — Add retained-boundary regression tests

Parent: [plan.md](plan.md), Step 1.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Tests added

1. `tests/test_cli_surface.py` (new) — top-level CLI surface contract (plan §5.3): asserts all 12
   intended Phase 1 commands (including `dashboard`) appear in `nctl --help`, `serve` does not, and
   `nctl serve` fails as Typer's ordinary unknown-command error rather than entering a
   compatibility path.
2. `tests/test_config.py` — replaced `test_serve_config_is_strict_and_bounded` and
   `test_serve_resolve_token_from_env_or_file` (both exercise implementation being deleted) with
   `test_serve_section_is_rejected_as_unknown`, asserting `[serve]` fails strict validation like
   any other unrecognized top-level section. Also removed the `cfg.serve.*` default assertions from
   `test_load_valid` (that config model field is being deleted, not merely reconfigured).
3. `tests/test_events.py` — added `test_emit_returns_the_record_even_when_persistence_fails` and
   `test_write_failure_warns_at_most_once_per_operation_log`, protecting §4.2's durable contract
   (`emit()` return value and single-warning isolation) independent of the subscriber bus being
   deleted.
4. `tests/test_operations_index.py` — added
   `test_historical_result_json_with_removed_dashboard_field_is_listed_opaquely`: a `result.json`
   fixture containing an old `dashboard` block and `reconciliation_status` field, asserting it is
   listed as an ordinary opaque artifact (name + size only) with no parsing/rejection.

## Run against the current (pre-deletion) implementation

`uv run pytest -q tests/test_cli_surface.py tests/test_config.py tests/test_events.py tests/test_operations_index.py`
— **43 passed, 3 failed**.

Intentional failures (each maps to a Section 4 contract that Steps 2-3 implement, not a defect in
the new test):

| Test | Why it currently fails |
|---|---|
| `test_cli_surface.py::test_help_lists_exactly_the_retained_commands_and_no_serve` | `serve` is still a registered Typer command (§4.1, deleted in Step 2) |
| `test_cli_surface.py::test_serve_is_an_unknown_command_not_a_compatibility_path` | `nctl serve` still runs and fails only on a missing token, not as an unknown command (§4.1, Step 2) |
| `test_config.py::test_serve_section_is_rejected_as_unknown` | `Config.serve: ServeConfig` still accepts `[serve]` as a known field (§4.1, Step 2) |

All other tests pass, including every already-retained-behavior assertion: the durable event
tests (returned record, single-warning isolation) and the historical `result.json` test pass
against the current implementation with no code change, because `operations_index` already treats
artifacts opaquely by name/size — confirming §4.3's retained contract needs no Step-1 code change,
only this explicit regression coverage.

No new test preserves server/dashboard/subscriber behavior; each new or replaced assertion maps to
exactly one Section 4 contract.

## Gate

Every new test maps to one contract in plan Section 4, and the 3 intentional pre-deletion failures
are the only failures. Proceeding to Step 2.
