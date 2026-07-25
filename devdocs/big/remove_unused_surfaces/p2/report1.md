# Phase 2 Step 1 — Freeze the final CLI/config/reconcile tests

Parent: [plan.md](plan.md) Step 1.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`step1-new-tests.txt`.

## 1. Changes made (before any implementation deletion)

- `nctl/tests/test_cli_surface.py`: removed `dashboard` from `RETAINED_COMMANDS` (11-command final
  set); added `test_dashboard_is_an_unknown_command_not_a_compatibility_path` mirroring the
  existing `serve` unknown-command test.
- `nctl/tests/test_config.py`: added `test_dashboard_section_is_rejected_as_unknown` beside the
  retained `test_serve_section_is_rejected_as_unknown`.
- `nctl/tests/test_compatibility_snapshots.py`:
  - removed the `from nctl_core.dashboard_render import DashboardData` import;
  - removed the `"nctl.dashboard.v1"` entry from `FROZEN_DATA_FIELDS`;
  - removed the `"nctl.reconcile.v2"` entry from the generic (superset/floor) `FROZEN_DATA_FIELDS`
    dict, since that check only proves a floor and the frozen contract here requires exactness;
  - added `FROZEN_RECONCILE_DATA_FIELDS` (the exact 16-field Phase 0 set, including
    `ssh_preflight`, excluding `dashboard`) and a dedicated
    `test_reconcile_data_fields_are_exactly_the_frozen_set_with_no_dashboard_field` asserting
    `set(ReconcileData.model_fields) == FROZEN_RECONCILE_DATA_FIELDS` (equality, not subset).

## 2. Intentional pre-deletion failures recorded

Ran the three edited files plus the full suite (`step1-new-tests.txt`, and a full-suite run).
Exactly 4 failures, each mapping to a Step 2/3 deletion, 979/983 other tests unaffected:

| Failing test | Fails because | Fixed by |
|---|---|---|
| `test_cli_surface.py::test_registered_top_level_commands_are_exactly_the_retained_set` | `dashboard` command still registered | Step 2 (remove CLI command) |
| `test_cli_surface.py::test_dashboard_is_an_unknown_command_not_a_compatibility_path` | `dashboard` still runs (fails on network, not "unknown command") | Step 2 |
| `test_config.py::test_dashboard_section_is_rejected_as_unknown` | `DashboardConfig`/`Config.dashboard` still accept `[dashboard]` | Step 2 (remove `DashboardConfig`) |
| `test_compatibility_snapshots.py::test_reconcile_data_fields_are_exactly_the_frozen_set_with_no_dashboard_field` | `ReconcileData.dashboard` still present | Step 3 (remove `ReconcileData.dashboard`) |

Full-suite run: 4 failed, 979 passed (983 collected — 3 new tests, since one new compatibility
test was added while one entry moved out of the loop-based superset dict, and two new CLI/config
tests were added net of no removals).

## 3. Deferred: §6 reconcile artifact/PATCH assertions

Plan Step 1.6 asks for "the minimum dashboard-free reconcile artifact/PATCH assertions from §6."
These are deliberately deferred to Step 3 rather than added here, for a safety reason specific to
this codebase: `_write_dashboard()`'s real (unstubbed) code path writes to the *live* default
`DashboardConfig.out_dir` (`~/.local/state/nctl/dashboard`, the user's real home directory,
per plan §7's explicit prohibition on touching that path) and can attempt a live Nautobot
`rest_patch` unless every fixture stubs `render_dashboard_from_drift` — exactly what all 24
existing `_stub_dashboard()` call sites already do. Writing a new, not-yet-stubbed pre-deletion
test to prove absence of dashboard/PATCH behavior would therefore have to either (a) reuse the
`_stub_dashboard()` pattern, which cannot demonstrate the dashboard code path is *gone* since the
code is still present and being deliberately routed around, or (b) run unstubbed, which risks a
real home-directory write this phase must not perform. The genuine absence proof is only possible
and safe once Step 3 deletes `_write_dashboard()` itself; §6's scenario matrix and no-PATCH
sentinel are implemented there instead. This is a deviation in ordering, not in coverage — §6 is
still fully executed, just inside Step 3 where it can run safely.

## Gate

Every new/changed assertion maps to plan §4 (CLI/config/reconcile contracts) or §6 (deferred to
Step 3 with recorded rationale above), and no test preserves a removed presentation contract as
passing. Step 1 gate met with the one recorded, safety-motivated ordering deviation.
