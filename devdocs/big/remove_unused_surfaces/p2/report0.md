# Phase 2 Step 0 — Reconfirm the Phase 1 handoff and current manifest

Parent: [plan.md](plan.md) Step 0.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/` (mode `0700`, files `0600`), containing
`revisions.txt`, `dirty-state.txt`, `uv-version.txt`, `baseline-help.txt`,
`baseline-measurements.txt`, `baseline-dashboard-matches.txt`, `deletion-searches-baseline.txt`.

## 1. Revisions and dirty state

| Repository | Revision | Dirty state |
|---|---|---|
| superproject | `ced6fe217aee872d752c36929850c018775b6fd7` | clean |
| `nctl` | `73096304abcf18bb8fd9d504e9df9166fd959919` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean |

Matches the Phase 1 final report's ending `nctl`/`nintent` revisions exactly; the superproject
advanced only through non-code planning commits (`p2 plan`, Phase 1 report/roadmap commits).

## 2. Phase 1 handoff confirmed intact

- `nctl --help` has 12 top-level commands (`status actual drift dashboard reconcile lifecycle
  render apply ops braindump ssh session`); `serve` is absent, `dashboard` remains — exact plan
  §2.2 baseline.
- No `nctl serve`/`nctl_core.serve`/uvicorn process or listener found (`ps aux` and `lsof -i :8300`
  both empty).
- `uv --version`: `uv 0.11.24 (Homebrew 2026-06-23 aarch64-apple-darwin)`.

## 3. Baseline measurements

| Metric | Value |
|---|---|
| Tracked nctl source lines (`src/`) | 18,137 |
| Tracked nctl test lines (`tests/`) | 20,025 |
| Full suite collected tests | 980 |
| Dashboard delete-set files | 9 (`dashboard/__init__.py`, `dashboard/html.py`, `dashboard/push.py`, `dashboard/template.html`, `dashboard_render.py`, `test_cli_dashboard.py`, `test_dashboard_html.py`, `test_dashboard_push.py`, `test_dashboard_render.py`) |
| Dashboard delete-set total lines | 1,304 (948 `.py` + 356 `template.html`) |
| Dedicated dashboard test functions | 29 (`test_dashboard_push.py`=9, `test_cli_dashboard.py`=4, `test_dashboard_render.py`=9, `test_dashboard_html.py`=7) |
| `_stub_dashboard` occurrences in `test_reconcile_executor.py` | 24 (1 definition + 23 calls) |

All figures match plan §2.2 exactly.

## 4. Newly discovered active wording classified

| Location | Content | Classification |
|---|---|---|
| `src/nctl_core/sources/desired.py:40` | comment: "...dashboard, or reconcile action is added in this step (Phase 4/5 territory per..." | edit in Step 4 — stale dashboard-dispatch reference in an active compute-inertness comment, no behavior change |
| `src/nctl_core/drift_render.py:82` | docstring pointing users to `nctl dashboard` | edit in Step 4 — replace with supported text/JSON drift contract wording |
| `tests/test_vm_p3_compute_stays_inert.py:2` | module docstring: "...drift/planner/dashboard/reconcile dispatch entirely..." | edit in Step 4 — presentation-independent wording, no behavior change |
| `tests/test_operations_index.py` | historical `result.json` fixture containing a literal legacy `dashboard` field | keep-shared — plan §4.5/§5.3 explicit exception, opaque-artifact evidence, not a reader |

No other unclassified active-scope reference was found.

## 5. Deletion-search baseline (pre-removal, expected to be non-empty)

Ran the plan's 16-token search (`nctl_core.dashboard`, `nctl_core.dashboard_render`,
`nctl.dashboard.v1`, `DashboardConfig`, `DashboardData`, `StatusPushData`, `dashboard_url`,
`status_push`, `render_dashboard`, `build_dashboard`, `_write_dashboard`, `reconciliation_status`,
`reconciliation_checked_at`, `[dashboard]`, `index.html`, `_stub_dashboard`) across `src/`,
`tests/`, `example.nctl.toml`, `README.md`, `docs/`. 223 lines of matches recorded in
`deletion-searches-baseline.txt` — expected, since this is the pre-deletion baseline. This file is
the reference point for Step 6/7's post-deletion clean search.

## 6. Evidence directory permissions

Created `.local/remove-unused-surfaces/p2/20260725-155334/` at mode `0700`; all seven recorded
files corrected to mode `0600` after creation (three files were briefly `0644` from shell
redirection defaults before the explicit `chmod`).

## Gate

The Phase 1 handoff is intact (12-command CLI, no serve residue, clean/matching revisions), every
dashboard reader/writer/test/doc reference has a Step 2–4 disposition, and no live nctl
server/listener is present. Step 0 gate met.
