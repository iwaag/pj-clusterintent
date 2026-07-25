# Phase 2 Step 2 — Remove the command, config, implementation, and dedicated tests

Parent: [plan.md](plan.md) Step 2.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`step2-results.txt`.

## 1. Changes made

- `nctl/src/nctl_core/cli/main.py`: removed the `from nctl_core.dashboard_render import
  build_dashboard, render_dashboard_text` import; removed `DashboardJsonOption`,
  `DashboardOutOption`, `DashboardFromOption`, `NoPushOption`, and the `dashboard` command function
  entirely; removed the `reconcile` command docstring's "regenerates the dashboard from the same
  final drift payload" promise (plan §5.2).
- `nctl/src/nctl_core/config.py`: removed `DashboardConfig` and the `Config.dashboard` field;
  every other config section is unchanged.
- `nctl/example.nctl.toml`: removed the `[dashboard]` section; all other sections unchanged.
- Deleted the five implementation paths (plan §5.1): `src/nctl_core/dashboard/__init__.py`,
  `src/nctl_core/dashboard/html.py`, `src/nctl_core/dashboard/push.py`,
  `src/nctl_core/dashboard/template.html`, `src/nctl_core/dashboard_render.py`. The now-empty
  `dashboard/` directory (including its stale `__pycache__`) was removed.
- Deleted the four dedicated dashboard test files: `tests/test_cli_dashboard.py`,
  `tests/test_dashboard_html.py`, `tests/test_dashboard_push.py`, `tests/test_dashboard_render.py`.

## 2. Test/import results

- `tests/test_config.py`: **24/24 passed**, including the Step 1 `test_dashboard_section_is_
  rejected_as_unknown`, now genuinely passing (`[dashboard]` fails strict validation because the
  field no longer exists at all, not because of a special-cased rejection).
- `tests/test_cli_surface.py` and `tests/test_compatibility_snapshots.py` still fail to *import*:
  both pull in `nctl_core.cli.main` / `nctl_core.reconcile.executor`, and
  `src/nctl_core/reconcile/executor.py:32` still has
  `from nctl_core.dashboard_render import DashboardData, render_dashboard_from_drift` — the module
  this step just deleted. `uv run nctl --help` fails the same way.

## 3. Deviation: Step 2's own gate cannot be fully met before Step 3

Plan §8 Step 2's gate text ("...retained commands/config still work") assumes `cli/main.py` is
importable at the end of this step. It is not, because `reconcile/executor.py` — edited only in
Step 3 — still imports the just-deleted `nctl_core.dashboard_render`. This is a genuine
interdependency in the plan's own step boundary, not an implementation mistake: `cli/main.py`
transitively imports `reconcile/executor.py` for the `reconcile` command, and `executor.py`'s
dashboard coupling is explicitly Step 3's scope (§5.2: "remove dashboard imports, field, call,
helper, warnings" from `executor.py`).

Rather than pull Step 3's behavioral decoupling (removing `_write_dashboard()`, its call, the
`ReconcileData.dashboard` field, and `_stub_dashboard()`) forward into this step, Step 2 stops at
its own scope and leaves this import error as a clearly diagnosed, expected mid-refactor state —
consistent with Step 1's precedent that a documented, precisely-attributed intentional failure is
preferable to force-fitting unrelated work into a step to make it independently green. Config-only
verification (§2 above) is complete and fully passing; CLI-level and compatibility verification
resume in Step 3 once `executor.py` no longer imports the deleted module.

## Gate

The dashboard CLI command, `DashboardConfig`/`Config.dashboard`, the `[dashboard]` example section,
and all nine dashboard implementation/test files are absent (verified by direct `ls`/`grep` in
`step2-results.txt`). Config contract is proven working end-to-end. CLI-level "both old commands
fail normally, retained commands still work" verification is deferred to Step 3 per the deviation
above, where it will be re-run and recorded.
