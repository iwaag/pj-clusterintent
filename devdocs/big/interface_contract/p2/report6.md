# Phase 2 Step 6 — Cross-component nctl confirmation and non-repetition proof

Parent: [plan.md](plan.md) — Step 6.

This step verifies cross-component interactions between `nctl` operations (lifecycle, ledger reconciler, Braindump/review management) and the contracted nintent API endpoints and GraphQL queries.

## 1. Verified Proof Items

1. **`nctl lifecycle` Flow:** Uses GraphQL for pre-read, sends PATCH containing only `lifecycle`, refetches via GraphQL to confirm the change, and reports confirmed state; repeat execution is a no-write no-op.
2. **`link_actual_node` Execution & Confirmation:**
   - Real planner generates `link_actual_node` action for unlinked node/device pairs.
   - Real ledger executor performs GraphQL snapshot pre-read, sends exact `{"realized_device": DEVICE_ID, "realized_device_source": "derived"}` PATCH payload, and performs fresh GraphQL snapshot refetch to positively confirm both `realized_device_id` and `realized_device_source`.
   - Fresh drift evaluation after link confirmation shows zero remaining drift and does not repeat `link_actual_node`.
3. **Fail-Closed Boundaries:** Pre-existing links (`node_already_linked`), HTTP patch failures (`node_link_patch_failed`), refetch ID mismatches (`node_link_not_confirmed`), and GraphQL errors fail closed with typed `LedgerActionError` codes.
4. **Braindump & Review Mutations:** Create, update, and delete operations execute narrow REST calls and confirm state changes through GraphQL.
5. **Removed Collections:** Confirmed zero calls from `nctl` to `/api/plugins/intent-catalog/services/`, `endpoints/`, `compute-platforms/`, or `compute-instances/`.
6. **Job Protocol Integrity:** Job lookup, JobResult polling, and FileProxy artifact downloads operate unchanged via `NautobotClient`.

## 2. Test Execution

- Executed targeted nctl suite: `uv run pytest tests/test_reconcile_ledger.py tests/test_cli_lifecycle.py tests/test_braindump.py` — **72 passed in 0.99s**.
- Full `nctl` test suite: **954 passed in 6.18s**.

## 3. Gate Status

Step 6 gate passed cleanly. Cross-component non-repetition and GraphQL confirmation proof complete. Proceeding to Step 7.
