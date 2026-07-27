# P1 Step 5 — Bind the consumer

Status: complete.

## Consumer binding

nctl retains its read-time validators because stale or compromised GraphQL rows must still become
visible `DesiredSourceIssue` records and be excluded from typed compute collections. Their semantics
are no longer maintained by instruction: `nctl/tests/test_compute_conformance.py` replays every
committed owner-generated case and compares successful values or exact error code/path/string.
It also compares the shared constants, including the nctl spelling of lifecycle/link-source tuples.

The actionable predicate now has one spelling, `is_actionable_lifecycle`; a repository search found
no remaining `is_actionable_compute_lifecycle` reference. No nctl check was deleted: every
Step 1 nctl-only check has a named snapshot-safety or source-issue consequence. No existing source
snapshot assertion was removed, so the deleted-assertion list is empty.

## Verification

- `nctl/tests/test_compute_conformance.py`: 1 passed.
- nctl ordinary gate: **968 passed** in 5.39s (the Step 0 baseline plus the new consumer test).

No runtime nintent import, shared package, migration, wire field, drift comparator, planner action,
reconciler, or actuator was added.

## Gate verdict

Complete: the consumer is fixture-bound, the predicate naming is unified, the exact replay test
passes, and all nctl ordinary tests pass.
