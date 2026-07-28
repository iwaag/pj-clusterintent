# P4 Step 3 — Resource evaluator ownership

Status: partially complete.

The snapshot adapter boundary was re-verified: it remains the single snapshot traversal and relationship-resolution owner. No evaluator or comparator move was made in this step because the remaining evaluator-local candidate/ranking helpers must move together to avoid a cyclic or compatibility import. The registry ordering contract remains untouched.

This residual prevents claiming the planned one-module-per-resource evaluator split.
