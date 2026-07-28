# Phase 1 — Steps 2–5 report: compute drift implementation

Status: **complete**.

`nctl_core.drift.compute_evaluation` is a pure domain evaluator registered through the thin
`compute_instance` comparator wrapper. It derives (but never writes) platform/Cluster and
instance/VirtualMachine matches, emits source issues, compares only observed fields, and records
creation-only `template` plus unobservable `unprivileged` in the realization summary.

Both `compute_platform` and `compute_instance` targets are seeded, host scope selects the latter
by owning-node slug, and CLI/reconcile summaries use the same projection. Compute codes are all
manual-review or unsupported in this phase: **no compute reconciler, handler, or AUTOMATIC code
was added**. The former zero-drift inert test now positively requires compute drift/targets and
zero compute actions; the manifest and nctl comparator documentation were updated.

The two planned classification deviations are implemented and intentionally temporary:

1. `compute_instance_not_linked` is `manual_review`, not Phase 0's future `ledger_link`, until
   Phase 2 supplies that reconciler.
2. `compute_platform_observation_stale` is `manual_review`, not observation routing, because
   Phase 1 has no compute-target-to-control-node observation consumer.

