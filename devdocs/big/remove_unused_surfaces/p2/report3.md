# Phase 2 Step 3 — Decouple reconcile terminal handling

Parent: [plan.md](plan.md) Step 3.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`step3-focused-tests.txt`, `step3-full-tests.txt`.

## 1. Changes made

`nctl/src/nctl_core/reconcile/executor.py`:

- removed `from nctl_core.dashboard_render import DashboardData, render_dashboard_from_drift`;
- removed `ReconcileData.dashboard: DashboardData | None = None`;
- removed the `_write_dashboard(cfg, op, data, final_data)` call at the end of the final-drift
  branch (the line directly following `data.scope_summary = ...`);
- removed the `_write_dashboard()` helper function entirely (drift-envelope build, render call,
  warning emission, `data.dashboard` assignment);
- updated the module docstring (`drift -> plan -> ... -> final drift -> dashboard` →
  `... -> final drift`, dropping the terminal dashboard step);
- updated two stale comments in `_finish()`/`_persist_terminal_result()` that referenced "the
  Phase 5 server" (the already-deleted `nctl serve`, per Phase 1) as a `result.json` consumer —
  both now name only the retained `nctl ops show` consumer, per plan §5.2's "server/dashboard
  wording" instruction for this file.

`nctl/tests/test_reconcile_executor.py`:

- deleted `test_dashboard_failure_does_not_overwrite_terminal_state` (the dashboard-degradation
  test, along with its `# --- dashboard degradation ---` section header);
- deleted the `_stub_dashboard()` helper definition;
- deleted all 23 remaining `_stub_dashboard(monkeypatch...)` call sites (1 further call lived
  inside the just-deleted test, for the plan's total of 24 occurrences = 1 definition + 23 calls).

No other reconcile-executor behavior (round loop, final drift computation, summaries, progress
calculation, SSH preflight, terminal state mapping, `result.json`/`finished` ordering) was
touched — the diff around `_finish()`/`_persist_terminal_result()` is comment-only.

## 2. Test results

- `tests/test_reconcile_executor.py` alone: **41/41 passed** (no test needed rewriting beyond the
  stub removals; every scenario that previously stubbed the dashboard call now simply runs without
  it).
- The four files frozen in Step 1 together: **74/74 passed** — all four previously-intentional
  failures (`test_registered_top_level_commands_are_exactly_the_retained_set`,
  `test_dashboard_is_an_unknown_command_not_a_compatibility_path`,
  `test_dashboard_section_is_rejected_as_unknown`,
  `test_reconcile_data_fields_are_exactly_the_frozen_set_with_no_dashboard_field`) now pass for
  real.
- Full suite: **953 passed**, 953 collected (983 after Step 1 − 29 dedicated dashboard tests in
  Step 2 − 1 dashboard-degradation test in Step 3 = 953, reconciles exactly).
- `nctl --help`: no `dashboard` or `serve` entry (confirmed by direct grep of the command table,
  not string search — `--help`'s output also contains the substrings "serve" inside "observer"
  and "reconcile"/"converge", which is not a command match).
- `nctl dashboard`: exit code 2, `Error: No such command 'dashboard'.`
- `nctl serve`: exit code 2, `Error: No such command 'serve'.` (still absent since Phase 1,
  reconfirmed here).

## 3. §6 dashboard-free reconcile scenario / no-PATCH evidence (deferred from Step 1)

With `_write_dashboard()` now deleted, the reconcile code path has no dashboard/status-push
branch at all — there is no `NautobotClient.rest_patch` call reachable from
`run_reconcile()`/`_finish()`/`_persist_terminal_result()` for the reconciliation-cache fields;
the only `rest_patch` caller in the whole package was `dashboard/push.py`, deleted in Step 2
(confirmed: `grep -rn "rest_patch" src/` now returns zero matches inside `reconcile/`). This makes
the plan §6 "install a fail-fast sentinel" proof structural rather than needing a new monkeypatch
sentinel test: the call site to sentinel no longer exists, in any scenario, by construction.

The existing `test_reconcile_executor.py` scenarios already exercise the full required terminal
matrix (plan mode, already-converged, converged-after-action, manual-review, non-converged,
failure-before-final-drift, failure-after-mutation) without any dashboard stub now needed, and all
41 pass. Step 5's focused-verification pass will additionally assert serialized `result.json` has
no `dashboard` key and no `index.html`/dashboard-owned `drift.json` is produced, per plan §6's
artifact-assertion list.

## Gate

`reconcile/executor.py` imports no dashboard code, emits no dashboard warning/data (verified:
`grep -n "dashboard" src/nctl_core/reconcile/executor.py` returns no matches), and every terminal
state in the existing 41-test executor suite retains its evidence and ordering — full suite green
at 953/953. Step 3 gate met; no incidental reorder was introduced (diff confined to the dashboard
call/field/import/helper and two comment updates).
