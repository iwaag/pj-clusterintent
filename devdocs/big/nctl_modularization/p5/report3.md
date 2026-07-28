# P5 Step 3 — Extension seams

Status: complete.

- README now documents the reconciler seam beside the comparator seam: registry identity and DAG, planner-owned target sets, `ActionContext` → `ExecutedAction`, dispatch registration, `phase`/`needs_client`, and dispatch-level error translation/evidence retention.
- The comparator section now restates the approved future compute evaluator registration point, explicitly preserving compute inertness and prohibiting placeholder registration.
- Documentation-only change; no comparator, planner action, reconciler, handler, or compute row was added.

