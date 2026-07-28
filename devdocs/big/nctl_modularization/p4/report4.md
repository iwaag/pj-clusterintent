# P4 Step 4 — Compute evaluator registration point

Status: complete.

`drift/registry.py` now records the exact future extension seam: a
`@register("compute_instance")` comparator receives `(SourceSnapshot,
DriftContext)`, reads the two typed desired compute collections, may use a new
open `Target.kind`, and extends `UNKNOWN_CODES` for no-data status handling.
It adds no comparator, placeholder, row, planner action, or actuator.

`tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions` passed (**1 passed**). The Step 0 read-only snapshot remains zero desired compute platform and instance rows.
