# Step 3.5 — Prove that review prose alone has zero deterministic effect

Status: partially complete; formal isolated-window evidence remains required.

## 1. Evidence obtained

- Before diary writes, the Braindump list was empty and drift had six targets with summary
  `converged: 2`, `unknown: 4`.
- Three `user_direct` Braindumps and three current Alignment Reviews were created through nctl.
- A post-write drift comparison retained the same schema, target identities, target statuses, summary,
  severity summary, and sorted diff-code sets as the pre-write result. Only ordinary time-derived
  evidence can age between reads.
- The diary writes did not create a DesiredService, DesiredServicePlacement, lifecycle change,
  nodeutils collection, Ansible action, or reconcile operation.
- Two reviews were later replaced in the same rows after the separate approved reconcile operation.

## 2. Boundary retained

The subsequent `agpc` reconcile was an explicitly approved deterministic operation, not an effect of
review prose. Its inventory/dashboard post-processing is recorded in `report3.4.md` and must not be
attributed to the diary feature.

## 3. Remaining formal proof

The Phase 3 plan requires a deliberately isolated review-only window with before/after normalized
desired projections, operation-event index, generated-artifact timestamps, and actual-observation
identity. The current evidence strongly demonstrates drift isolation but was collected across
Braindump creation and a later reconcile attempt, so it does not satisfy that stricter proof.

After resolving Step 3.4's collection blocker, perform one review replacement with no other live
operation in the window and record the complete comparison.

## Discrepancies

Do not mark Step 3.5 complete until the isolated review-only verification is run.
