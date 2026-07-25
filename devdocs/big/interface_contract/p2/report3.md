# Phase 2 Step 3 — Move node-link reads and confirmation to GraphQL

Parent: [plan.md](plan.md) — Step 3.

This step replaces REST GET in `nctl`'s `execute_link_actual_node` reconciler with canonical GraphQL reading via `fetch_desired_snapshot()`.

## 1. Work Completed

### `nctl` Reconciler Implementation (`nctl_core/reconcile/ledger.py`)
- Replaced `_get_node()` (REST GET `/api/plugins/intent-catalog/nodes/{node_id}/`) with `_get_desired_node_by_id()`, which fetches the desired snapshot via GraphQL (`fetch_desired_snapshot`).
- Verified node identity, UUID, and slug alignment from the GraphQL snapshot prior to sending the PATCH request.
- Retained strict precondition: refuses to link if `realized_device_id` or `realized_device_source` is already set.
- Retained exact two-field REST PATCH payload (`realized_device` + `realized_device_source="derived"`).
- Replaced post-PATCH REST GET with a fresh GraphQL fetch (`fetch_desired_snapshot`) to positively confirm that both `realized_device_id` and `realized_device_source="derived"` were committed.
- Removed legacy REST serialization helpers (`_linked_id`, `_get_node`).

### Audit of `rest_get` Usage across `nctl/src/`
- Verified via grep that zero domain-object REST GET callers remain in `nctl`.
- Classified all 4 remaining `rest_get` occurrences in `nctl/src/`:
  1. `nctl_core/nautobot.py:63` — `NautobotClient.rest_get` method definition.
  2. `nctl_core/jobs.py:128` — Job discovery protocol (`/api/extras/jobs/`).
  3. `nctl_core/jobs.py:144` — JobResult status polling protocol (`/api/extras/job-results/{id}/`).
  4. `nctl_core/jobs.py:200` — FileProxy artifact lookup protocol (`/api/extras/file-proxies/`).

## 2. Test Verification

- **`nctl` Test Suite:** 954 passed in 6.09s (`cd nctl && uv run pytest`).
- **`execute_link_actual_node` Unit Tests:** Verified happy path GraphQL-before/PATCH/GraphQL-after confirmation, typed patch failure (`node_link_patch_failed`), refetch mismatch rejection (`node_link_not_confirmed`), and pre-existing link refusal (`node_already_linked`).

## 3. Gate Status

Step 3 gate passed. All `nctl` domain reads use GraphQL, and `execute_link_actual_node` confirms writes through GraphQL. Proceeding to Step 4.
