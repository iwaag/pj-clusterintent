# Test Strategy Phase 2 — Step 0 Report: Evidence, Queue, and Protected Baseline

Parent: [plan.md](plan.md), Step 0.

Status: **`complete`**.

## Baseline

- Superproject: `41b64b8d8a8d0246ad7b14463cddf250e79d4afb`, clean at the start.
- Submodules were clean at `nctl` `4ac8b7c42b4c957b1788db68f25824a2dd982816`,
  `nintent` `2c1a8a4f0e774c7b683dd4758c6986451e571ddd`, `nauto`
  `1c78af8bdbfc69cafdc293b4082f866de9f271b0`, `nodeutils`
  `3a0fdf9817d970935847aafd46c35bf07133c20c`, and `ansible_agdev`
  `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162`.
- The Phase 0 evidence directory is
  `.local/test-strategy/p0/20260726T034839Z/`; Phase 1 reports status `complete`.
- `nctl` and `nintent` match the Phase 1 final submodule revisions, with no test delta to
  compare before Phase 2 work.

## Private evidence and safety boundary

Created `.local/test-strategy/p2/20260726T144434Z/` with directory mode `0700` and files mode
`0600`. It contains the required starting revisions, tool and scratch-state records, Tier B/C
case baseline, grouped work queue, protected Tier A list, Phase 0/1 delta, and an initially empty
consolidation ledger.

The exported baseline has 1,078 Tier B/C cases (the Phase 0 total) and 299 protected Tier A
cases. The grouped queue has 82 component/file/contract/operation/boundary groups. No test group
has been proposed for consolidation yet, so no focused pre-change test was due in this step.

The persistent local scratch Docker engine and Nautobot container were reachable. No container,
database, service, desired state, external target, or secret-bearing file was read or changed.

## Next step

Select a specific domain-owned Tier B candidate only after adding its proposed ledger row and
identifying its adjacent protected Tier A cases. The first focused baseline will be run before an
edit to that candidate.
