# Phase 4 Step 6 — gates and handoff

Status: complete.

Final gates, after the live evidence-ownership correction:

| Gate | Result |
|---|---|
| nctl ordinary (`uv run pytest -q --durations=20`) | 1005 passed |
| compute conformance | 1 passed |
| Ansible conformance | 3 passed |

The compute conformance gate remains applicable because the nctl compute actuation contract changed. nintent, nauto, nodeutils, and the Nautobot runtime gates were not run: no code in those repositories or their runtime/App surfaces changed. The live Step 5 observation did exercise the existing nodeutils → nauto ingestion path but did not modify it.

Recorded limitations:

- F6: `create_compute_instance` remains outside `SSH_REQUIRING_RECONCILER_IDS`, although its handler uses Ansible over SSH. This known pre-existing asymmetry was not widened in Phase 4; destroy is included.
- F8: the `agfixture` disposable LXC was spent by Phase 4. Phase 5 must reuse its durable evidence or provision a separate disposable fixture.
- Repeated removal-complete reconcile has zero actions but is rendered as `manual_intervention_required` because the existing planner treats its informational finding as manual review. Its scope remains converged and it does not repeat destruction.

Phase 5 handoff: use operation `01KYRR92T751HFE65AYTCPGPS0` for the exact one-shot destroy evidence and `01KYRRCZRCAQGMB4SAEHG49ZH8` for fresh observation/ingest convergence. The status of Phase 4 is **complete**.
