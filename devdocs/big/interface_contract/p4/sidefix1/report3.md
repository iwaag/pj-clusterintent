# Side Fix 1 Step 3 Report — Partial Mutation and Final-Drift Proof

Plan: [plan.md](plan.md), Step 3. Status: complete.

No live Nautobot request, Job, deployment, service action, commit, or push was performed.

## Partial-IPAM audit result

`reconcile_ipam` already provides exact positive mutation evidence through non-empty validated
`applied_endpoint_ids`. This step proves shared accounting now consumes it:

- one applied endpoint plus one unresolved endpoint remains `success=false, mutated=true`, and
  now yields `had_side_effects=true`;
- a conflict/skip-only result with no applied endpoint remains `success=false, mutated=false`;
- when regeneration is also failed, that no-apply result leaves `had_side_effects=false`.

The remaining Job protocol failures (timeout, polling failure, missing/invalid artifact after a
Job launch) do not contain exact committed-row evidence. They were not relabeled as
`mutated=true`; the boolean contract would otherwise overstate what nctl knows. No separate
tri-state follow-up is required by the current code paths, but any future need to report a
material unknown-write condition must be recorded as a separate problem rather than inferred here.

## Final-drift proof

Added run-level tests with the real `_run_apply()` flow and only the external drift boundary
stubbed:

1. A failed `link_actual_node` action with `mutated=true`, followed by a terminal store error,
   triggers exactly one fresh drift read. The new final drift is stored and its summary replaces
   the round-start summary.
2. If that refresh fails, the failed-mutated action remains in `rounds`, `progress_made=true`,
   the original terminal error remains present, `final_drift_unknown` is added, and
   `final_drift_path` is empty.

The existing successful production-inventory, observation, interruption, store-failure, and
post-actuation evidence-retention tests remain in the focused suite. The side fix deliberately
does not redesign `max_rounds`, `no_progress`, or operation-state classification.

## Verification

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py nctl/tests/test_reconcile_executor.py
72 passed in 0.93s
```

Next: complete Step 4 reporting/documentation closure, then run the full nctl suite and whitespace
checks before finalizing the side fix.
