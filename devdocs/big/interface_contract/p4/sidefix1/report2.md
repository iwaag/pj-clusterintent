# Side Fix 1 Step 2 Report — Executor Propagation and Shared Round Accounting

Plan: [plan.md](plan.md), Step 2. Status: complete.

No live Nautobot request, Job, deployment, service action, commit, or push was performed.

## Implemented contract

`_execute_action()` now copies `LedgerActionError.mutated` into a failed `ActionResult` without
an error-code allowlist. Its error `action_completed` JSONL event records the same safe boolean.

`_execute_round()` now uses one private `success or mutated` predicate at every accumulator site:

- bootstrap/ledger actions;
- production inventory regeneration;
- service actions; and
- post-actuation observation.

This retains the prior successful production-inventory and observation behavior while making a
failed-but-mutated node-link or partial IPAM action visible to `had_side_effects`. Comments and
the final-drift-unknown message now describe successful actions and positively recorded mutation
separately from full action confirmation.

## Verification

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py nctl/tests/test_reconcile_executor.py
70 passed in 0.97s
```

The focused executor test also proves the failed action's `ActionResult` and `action_completed`
JSONL event both contain `success=false, mutated=true`.

Next: verify partial IPAM/no-apply controls and terminal final-drift refresh behavior in Step 3.
