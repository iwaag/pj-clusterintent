# Phase 2 Step 6 — Run deletion searches and package proof

Parent: [plan.md](plan.md) Step 6.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`deletion-searches-final.txt`, `step6-model-inspection.txt`, `step6-wheel-build.txt`,
`wheel-filelist.txt`.

## 1. Sixteen-token deletion search — zero unexplained matches

Ran the plan's full token list against `src/`, `tests/`, `example.nctl.toml`, `README.md`,
`docs/`:

```text
nctl dashboard, nctl_core.dashboard, nctl_core.dashboard_render, nctl.dashboard.v1,
DashboardConfig, DashboardData, StatusPushData, dashboard_url, status_push, render_dashboard,
build_dashboard, _write_dashboard, reconciliation_status, reconciliation_checked_at,
[dashboard], index.html
```

Result (`deletion-searches-final.txt`): 14 of 16 tokens have zero matches at all. The remaining
two are exactly the plan's expected active-test exceptions:

- `reconciliation_status`: one match, `tests/test_operations_index.py:148`, inside the literal
  historical opaque-artifact fixture (plan §4.5/§5.3's named exception).
- `[dashboard]`: two matches, both in `tests/test_config.py`'s new
  `test_dashboard_section_is_rejected_as_unknown` — the docstring and the TOML fragment used to
  prove the section is now *rejected*, not accepted.
- `index.html`: three matches, all in `tests/test_reconcile_executor.py`'s new
  `test_already_converged_terminal_artifacts_have_no_dashboard_write_or_status_patch` — the
  docstring and the two assertions proving the file is *absent*.

No other token has any match anywhere in the searched scope.

## 2. Additional inspections

- **Typer command registration**: `sorted(click_app.commands)` = `['actual', 'apply', 'braindump',
  'drift', 'lifecycle', 'ops', 'reconcile', 'render', 'session', 'ssh', 'status']` — exactly the
  11 frozen commands, no `dashboard`/`serve`.
- **`Config.model_fields`**: `['ansible', 'events', 'inventory', 'nautobot', 'reconcile', 'repo',
  'source_path', 'ssh']` — no `dashboard`/`serve` field.
- **`ReconcileData.model_fields`**: exactly the 16 frozen fields (`artifact_dir`,
  `event_log_path`, `final_drift_path`, `initial_drift_path`, `manual_review`, `mode`,
  `operation_id`, `plan_path`, `progress_made`, `rounds`, `scope`, `scope_summary`,
  `ssh_preflight`, `state`, `summary`, `unsupported`) — no `dashboard`.
- **Plain imports**: `import nctl_core.cli.main` and `import nctl_core.reconcile.executor` both
  succeed with no error.
- **Status-PATCH literals/routes**: `grep -rn "rest_patch" src/nctl_core/` (rerun) still shows
  only `lifecycle.py`, two in `braindump.py`, and `reconcile/ledger.py`'s retained
  `execute_link_actual_node` device-linking PATCH — none targeting `reconciliation_status`/
  `reconciliation_checked_at` (both already confirmed zero matches above).

## 3. Wheel proof

Built in a fresh `mktemp -d` directory (`uv build --out-dir "$BUILD_DIR"`): succeeded, producing
`nctl-0.0.1-py3-none-any.whl`. `python3 -m zipfile -l` listed **74 entries**; `grep -i dashboard`
against that listing returns zero matches — no `nctl_core/dashboard/*`, `dashboard_render.py`, or
template asset is packaged.

## 4. `pyproject.toml`/`uv.lock` unchanged

`git status --short pyproject.toml uv.lock` is empty — both files are untouched since Phase 1
(last edited in commit `183e894`, Phase 1 Step 4). No dashboard-only dependency was discovered
during this phase; `httpx`/`pydantic` (dashboard's former imports) remain reachable through other
retained consumers, matching the plan's own prediction (§5.2). `uv lock --check`: clean
(`Resolved 26 packages`).

## Gate

No unexplained active nctl dashboard runtime/schema/config/writer match remains, and the built
wheel has no packaged dashboard asset. Step 6 gate met.
