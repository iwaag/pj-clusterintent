# Phase 2 Step 1 — Freeze executable tests for the final contract

Parent: [plan.md](plan.md) — Step 1.

This step freezes executable test cases for the Phase 2 REST and GraphQL contracts across both `nintent` and `nctl`.

## 1. Test Updates Completed

### `nintent`

- Added `nautobot_intent_catalog/tests/test_p2_contract.py` containing static and runtime assertions for:
  - `IntentSource` removal from GraphQL registration while retaining all 11 other models (`DesiredNode`, `DesiredEndpoint`, etc.).
  - Absence of deleted serializers (`DesiredServiceSerializer`, `DesiredEndpointSerializer`, `DesiredComputePlatformSerializer`, `DesiredComputeInstanceSerializer`).
  - Absence of deleted ViewSets (`DesiredServiceViewSet`, `DesiredEndpointViewSet`, `DesiredComputePlatformViewSet`, `DesiredComputeInstanceViewSet`).
  - Strict absence of `fields = "__all__"` on retained serializers (`DesiredNodeSerializer`, `BrainDumpDocumentSerializer`, `AlignmentReviewSerializer`).
  - Runtime API checks (under Nautobot test runner): 404 for removed REST collection URLs (`/api/plugins/intent-catalog/services/`, etc.) and 405 for disallowed methods (such as POST to `nodes/`).

### `nctl`

- Updated `nctl/tests/test_reconcile_ledger.py` to assert that `execute_link_actual_node`:
  - Executes GraphQL `DESIRED_QUERY` before PATCH to resolve node identity and verify pre-existing link state.
  - Sends exact `realized_device` + `realized_device_source="derived"` PATCH payload.
  - Executes fresh GraphQL `DESIRED_QUERY` after PATCH to positively confirm the link and source before returning success.
  - Fails closed with typed `LedgerActionError` codes (`node_already_linked`, `node_link_patch_failed`, `node_link_not_confirmed`).

## 2. Test Execution Verification

- **`nintent` Unit Tests:** 227 tests collected, 222 passed, 5 skipped (Django/Nautobot runtime guarded).
- **`nctl` Test Suite:** 950 passed, 4 failed as expected (specifically `test_link_actual_node_*` in `test_reconcile_ledger.py` prior to Step 3 implementation of GraphQL reading in `ledger.py`).

## 3. Gate Status

Step 1 gate passed. Tests explicitly describe the frozen Phase 2 target contract. Proceeding to Step 2.
