# P4 — Drift evaluation and production composition boundaries

Status: partially complete.

Frozen input was superproject `f46a3a6`, nctl `786b61b`, nintent `4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, and ansible_agdev `66b31c8`; private evidence is under `.local/nctl-modularization/p4/20260728T022804Z/`.

Completed splits are deterministic IP-range rules (`drift.ip_ranges`), gap-status precedence (`drift.gap_status`), shared MAC normalization (`drift.interfaces`), and canonical JSON/digests (`nctl_core.canonical`). The dnsmasq audit kept its single skip/finding owner and boundary tests now cover the new pure modules. The compute evaluator seam is documented in `drift.registry` without activation.

The phase is not complete: MAC/interface candidate extraction and node ranking remain evaluator-local, resource evaluators were not split, and production composition/route/report/model ownership was not split. Those omissions are recorded in reports 2, 3, and 5; no compatibility shim or behavior-changing substitute was added. Phase 5 therefore inherits the responsibility-map work plus these unresolved boundary splits. `vm_first_realization` inherits the documented compute registration point and the existing Phase 3 action seam.

All offline gates and named behavior proofs passed (reported in `report8.md`). Runtime verification is unavailable as described there, so it also independently prevents an unqualified completion claim. The inherited Phase 3 test-ownership residual remains unchanged.
