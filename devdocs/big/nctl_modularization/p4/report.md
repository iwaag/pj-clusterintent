# P4 — Drift evaluation and production composition boundaries

Status: active additional work.

Frozen input was superproject `f46a3a6`, nctl `786b61b`, nintent `4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, and ansible_agdev `66b31c8`; private evidence is under `.local/nctl-modularization/p4/20260728T022804Z/`.

Completed splits are deterministic IP-range rules (`drift.ip_ranges`), gap-status precedence (`drift.gap_status`), shared MAC normalization (`drift.interfaces`), and canonical JSON/digests (`nctl_core.canonical`). The dnsmasq audit kept its single skip/finding owner and boundary tests now cover the new pure modules. The compute evaluator seam is documented in `drift.registry` without activation.

Additional completion work is tracked in [`reportex.md`](reportex.md), including
the service evaluator and production route/model/report splits. It replaces the
old residual list while work is active; no compatibility shim or
behavior-changing substitute has been added.

Both local Nautobot runtime-gate modes now pass; the evidence is recorded in
[`reportex.md`](reportex.md). The inherited Phase 3 test-ownership residual
remains unchanged.
