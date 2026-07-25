# Phase 2 Step 5 — Run focused verification

Parent: [plan.md](plan.md) Step 5.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`step5-focused-tests.txt`, `step5-full-tests.txt`.

## 1. Plan's exact focused command

```bash
uv run pytest -q \
  tests/test_cli_surface.py tests/test_config.py tests/test_compatibility_snapshots.py \
  tests/test_reconcile_executor.py tests/test_operations_index.py tests/test_cli_drift.py \
  tests/test_drift_render.py tests/test_cli_ops.py
```

Result: **112 passed**, 0 failed.

## 2. New test: §6 dashboard-free artifact/no-PATCH proof

Added `test_already_converged_terminal_artifacts_have_no_dashboard_write_or_status_patch` to
`test_reconcile_executor.py`, right after `test_already_converged_when_no_diffs` (the plan's
"representative no-action terminal fixture"). It:

- installs a fail-fast sentinel on `NautobotClient.rest_patch` (`AssertionError` if called at
  all) — this is a structural proof, not a mock-return check: since Step 3 deleted the only
  `rest_patch` caller that touched reconciliation-cache fields
  (`dashboard/push.py`, deleted in Step 2), there is no code path left in `run_reconcile()` that
  could reach this sentinel, and the test's pass confirms that by actually running the real
  executor to a terminal state without tripping it;
- asserts `"dashboard" not in envelope.model_dump(mode="json")["data"]`;
- walks the full operation artifact directory and asserts `result.json`, `plan.json`, and
  `drift-final.json` are present, while `index.html` and `drift.json` (the two dashboard-owned
  filenames) are absent, both by directory listing and by direct `Path.exists()` check.

One representative fixture is sufficient per plan §6 ("for representative no-action terminal
fixtures, install a fail-fast sentinel...") — the sentinel's structural reachability (§3 below)
already generalizes to every other reconcile scenario, so a second copy of the same proof for
each terminal state would test the same absence twice, not new behavior.

## 3. §6 terminal-scenario matrix — existing coverage confirmed

| Scenario | Required result | Test |
|---|---|---|
| Plan mode with actionable drift | `planned`, `ok=true` | `test_plan_mode_never_mutates_and_reports_planned` |
| Apply with no diffs | `already_converged`, `ok=true` | `test_already_converged_when_no_diffs`, `test_already_converged_terminal_artifacts_have_no_dashboard_write_or_status_patch` (new) |
| Apply converges after action | `converged`, `ok=true` | `test_link_actual_node_action_executes_and_converges_next_round` |
| Manual-review blocker | `manual_intervention_required`, `ok=false` | `test_manual_review_blocks_before_any_mutation` |
| Unsupported/non-converged path | unchanged existing state/`ok` | `test_no_progress_stops_before_max_rounds`, `test_max_rounds_reached_when_progress_never_completes`, `test_local_blocker_allows_independent_action_then_reports_manual_intervention` |
| Failure before final drift | `failed`, `ok=false` | `test_interrupted_before_round_reports_failed`, `test_unknown_host_reports_failed_with_code` |
| Failure after a mutation | `failed`, truthful progress | `test_post_actuation_observation_store_failure_retains_deployment_evidence`, `test_final_drift_refresh_failure_after_store_failure_reports_unknown` |

All listed tests are pre-existing (none needed rewriting beyond the Step 3 `_stub_dashboard()`
removal already recorded in report3.md) and pass in the Step 5 focused run and the full suite
below — each asserts positive evidence (state, rounds/actions, SSH preflight, or manual/unsupported
records) for its terminal path, not merely a green exit, matching README_DEV's "no error is not
proof the target path ran" rule.

## 4. Structural no-PATCH generalization

`grep -rn "rest_patch" src/nctl_core/` (rerun here) shows five call sites plus the
`NautobotClient.rest_patch` definition itself in `nautobot.py`: `lifecycle.py` (`nctl lifecycle`'s
own PATCH), two in `braindump.py` (Braindump-diary PATCHes), and one in
`reconcile/ledger.py:116` — `execute_link_actual_node`'s PATCH of `realized_device`/
`realized_device_source` onto a `DesiredNode`, an intentionally retained ledger-linking action,
not a reconciliation-status-cache write. None of the five write `reconciliation_status` or
`reconciliation_checked_at` (re-confirmed by grepping those two literal field names across
`src/`: zero matches, consistent with Step 6's fuller deletion search). `reconcile/executor.py`
itself (as opposed to `ledger.py`, which it calls into for specific plan actions) has zero direct
`rest_patch` callers after Step 3, so every reconcile terminal path in the table above is
dashboard/status-PATCH-free by construction, not only the one directly sentineled.

## 5. Full-suite confirmation

`uv run pytest -q` (full suite): **954 passed** (953 after Step 4 + 1 new test).

## Gate

Focused tests and all required terminal scenarios pass; the new test provides positive evidence
(not merely an empty assertion) that the intended no-dashboard/no-PATCH path actually ran through
the real executor. Step 5 gate met.
