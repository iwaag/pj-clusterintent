# Side Fix 1 Step 0 Report — Baseline and Failing Mutation-Evidence Assertions

Plan: [plan.md](plan.md), Step 0. Status: complete.

No live Nautobot request, Job, deployment, service action, commit, or push was performed. This
step added only the two intentionally failing executor assertions needed to demonstrate the defect
before implementation.

## Baseline

| Repository | Revision | Worktree before Step 0 |
|---|---|---|
| superproject | `22921a0fd749231f03a2f77c9f8552d33f418c1d` | clean |
| `nctl` | `79b6d6b3e8025722ae1a408daacbf706e845e11d` | clean |

The pre-change focused command passed:

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py nctl/tests/test_reconcile_executor.py
67 passed in 1.08s
```

## Deliberate failing checks

Added to `nctl/tests/test_reconcile_executor.py`:

1. `test_link_actual_node_confirmation_failure_after_successful_patch_is_recorded_not_dropped`
   now requires the retained failed action to have `mutated is True` and the round to have
   `had_side_effects is True`.
2. `test_reconcile_ipam_partial_conflict_is_not_reported_as_success` now requires
   `outcome.had_side_effects is True` when one pinned endpoint was applied.

The expected red run was:

```text
uv run --project nctl pytest nctl/tests/test_reconcile_executor.py -q
2 failed, 41 passed in 0.97s
```

The failures prove the recorded defect exactly:

| Case | Actual before repair | Required result |
|---|---|---|
| successful node-link PATCH followed by failed confirmation | `ActionResult.mutated=False` | `True` |
| partial IPAM apply with one applied endpoint | `RoundOutcome.had_side_effects=False` | `True` |

Next: implement the ledger-owned post-PATCH mutation marker and propagate it through executor
round accounting.
