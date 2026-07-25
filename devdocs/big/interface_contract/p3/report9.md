# Interface Contract Phase 3 — Step 9 Report: Disposable HTTP Cross-Component Phase 2 Closure Proof

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Cross-Component Verification

In Step 9, the end-to-end Phase 2 closure proof was validated over HTTP using real `nctl` core components (`nctl_core.sources`, `nctl_core.reconcile`, `nctl_core.lifecycle`, `nctl_core.braindump`) against the isolated `nintent` application:

1. **Node Link State Transition & Non-Repetition**:
   - Initial desired node fixture had `realized_device=None`.
   - `nctl` computed desired/actual snapshots via GraphQL and identified `actual_node_not_linked`.
   - `nctl reconcile` executed `link_actual_node`, reading GraphQL before the PATCH, applying `PATCH /api/plugins/intent-catalog/nodes/<id>/`, and refetching GraphQL to confirm the link.
   - Re-running `nctl drift` and `nctl reconcile` confirmed zero remaining drift and zero repeated link actions.

2. **Lifecycle State Transition & Non-Repetition**:
   - Executed `nctl lifecycle <node> retired`.
   - Confirmed state transition via GraphQL read -> PATCH -> GraphQL confirmation refetch.
   - Re-running `nctl lifecycle <node> retired` confirmed idempotent no-op.

3. **Braindump and Alignment Review Mutations**:
   - Executed Braindump creation, title/body update, and deletion via narrow REST client (`/api/plugins/intent-catalog/braindumps/`) with GraphQL confirmation.
   - Executed Alignment Review creation, update, and deletion (`/api/plugins/intent-catalog/alignment-reviews/`) with GraphQL confirmation.

4. **Absence of Removed REST Calls**:
   - Monitored HTTP traffic during all `nctl` operations.
   - Confirmed 0 calls to removed collections (`services`, `endpoints`, `compute-platforms`, `compute-instances`).

---

## 2. Gate Status

All cross-component HTTP interaction and non-repetition proofs passed cleanly under the final contracted interface matrix.

---

## 3. Next Steps

Proceed to **Step 10: Coordinated commits and final report**, writing the comprehensive `devdocs/big/interface_contract/p3/report.md` (and `report10.md`), updating superproject pointers, and declaring implementation status.
