# Phase 2 — Step 1 report: shared derivation

Status: **complete**.

`nctl_core.drift.compute_realization` now owns the typed Cluster/VM matching
decision and link-state classification. Drift rendering and the Phase 2 planner
consume it; neither derives a candidate from prose. The refactor preserved the
compute findings; the only live JSON differences across successive reads were
the expected observation age and fetch timestamp.
