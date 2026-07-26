# Side Fix 1 Step 1 Report — Ledger Mutation Boundary

Plan: [plan.md](plan.md), Step 1. Status: complete.

No live Nautobot request, Job, deployment, service action, commit, or push was performed.

## Implemented contract

`LedgerActionError` now carries a default-false `mutated` flag. The only writer that sets it for
this repair is `execute_link_actual_node()` after it receives a successful REST PATCH response:

- failures before PATCH or a rejected PATCH remain `mutated=false`;
- every failure in the subsequent GraphQL confirmation block retains its original error code and
  carries `mutated=true`; and
- a confirmation mismatch remains `success=false`; mutation evidence does not turn it into a
  successful action.

## Tests added or strengthened

`test_reconcile_ledger.py` now proves the marker for:

- rejected PATCH and pre-PATCH errors (`false`);
- post-PATCH GraphQL transport failure (`true`);
- post-PATCH missing node (`true`);
- post-PATCH slug mismatch (`true`);
- wrong linked device (`true`); and
- wrong link source (`true`).

## Verification

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py nctl/tests/test_reconcile_executor.py
27 passed in 0.63s
```

Next: propagate the ledger-owned marker through executor action evidence and shared round
accounting in Step 2.
