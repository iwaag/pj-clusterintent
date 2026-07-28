# Phase 2 — Step 3 report: planner and classification

Status: **complete locally**.

`compute_instance_not_linked` is now AUTOMATIC only through
`link_compute_realization`. It produces one compute-instance-anchored
`ledger_patch`, pinned to both UUIDs, VMID, match basis, and the platform/control
node it read. Ambiguous, stale, missing, or conflicting links fall back to
manual review. `compute_platform_observation_stale` remains manual review: no
safe candidate exists to route.
