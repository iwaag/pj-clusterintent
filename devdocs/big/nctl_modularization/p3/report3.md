# P3 Step 3 — Bootstrap action seam

Status: complete.

- Added the frozen `ActionContext`, `ExecutedAction`, `ActionHandler`, shared
  action-boundary evidence constructors, and static dispatch seam.
- Moved `observe_node`, `link_actual_node`, and `reconcile_ipam` into dedicated
  handlers. The executor now partitions through handler phase metadata and no
  longer imports observation or ledger execution.
- Post-actuation observation is now an in-memory action dispatched through the
  same seam; it is never added to `plan.json` or `plan_created`.
- Under the recorded approval, the nintent runtime test now calls
  `execute_action(ActionContext(...), action)`. It changed one import and one
  direct invocation only; no nintent application code, image, or push changed.
- nctl ordinary passed: **970 passed**. The Nautobot runtime reuse gate passed.

Implementation commits: nctl `675d4dc`; nintent `4f46bc8`.

