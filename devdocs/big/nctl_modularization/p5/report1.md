# P5 Step 1 — Close inherited residuals

Status: complete.

- Closed R1. `drift.node_evaluation` now owns desired-node evaluation and deterministic actual-node ranking; `drift.endpoint_evaluation` owns desired-endpoint evaluation, IPAM eligibility, range policy, and interface/MAC candidate selection. `drift.evaluation` is reduced to the shared `EvaluationResult`, target/status vocabulary, and generic value/reference helpers. The new evaluator modules import only stdlib and read-model types at type-check time; the boundary test proves that importing either loads no transport or CLI module.
- `evaluation_snapshot` and the focused evaluator tests import the owning evaluator directly. No assertion was removed, weakened, or merged; test collection increased from 974 to **976** because the two new pure-module boundary cases are independent checks. No MANIFEST owning test ID moved, so its rows require no Step 1 edit.
- R2 is a deliberate keep. `production/composer.py` has one public composition owner; its private host assembly and document rendering helpers are used only by that composition flow. Moving them would create a second public coordination boundary without an independently testable contract.
- R4 is a deliberate keep. The IPAM partial-result matrix tests the executor's conversion of a handler result into round-level success, mutation evidence, and post-action control flow. The IPAM handler owns the raw action result, but it cannot own this executor boundary without duplicating the executor contract.
- Focused evaluator/comparator/boundary tests passed: **83 passed**. `nctl` ordinary passed: **976 passed**. A pre/post live `drift --json` comparison has no semantic difference from this refactor; its only changing fields are the independently time-derived source fetch timestamp and stale-observation `age_hours`.

