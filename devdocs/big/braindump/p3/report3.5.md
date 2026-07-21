# Step 3.5 — Prove that review prose alone has zero deterministic effect

Status: complete.

## 1. Earlier diary isolation evidence

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

## 3. Formal isolated review-only window

After Step 3.4's successful fresh observation, the user-direct unmanaged-service policy Braindump
`c1e2eb7c-0efc-4968-965c-2a40695d8049` had review
`04b3c325-2f5c-4700-a3f9-61e8afc2c5ec`. With no other operation started in the window, nctl replaced
that review from the same local UTF-8 source file.

- Action: `replaced`; review UUID remained `04b3c325-2f5c-4700-a3f9-61e8afc2c5ec` and its
  `last_updated` advanced.
- Before/after normalized DesiredSnapshot hashes matched exactly.
- Before/after normalized ActualSnapshot hashes matched exactly.
- Before/after normalized drift comparison (summary, severity summary, target identity/status, and
  sorted diff-code sets) matched exactly.
- The configured nctl operation index count was unchanged; no reconcile, Ansible, nodeutils, or
  Nautobot Job operation was invoked by the review replacement.
- Production inventory and dashboard modification times were unchanged.

This proves the review write changed only the one AlignmentReview row. It does not claim semantic
alignment or fresh evidence beyond the separately observed facts in Step 3.4.

## Discrepancies

None for Step 3.5.
