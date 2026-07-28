# P4 Step 0 — Freeze and baseline

Status: complete.

Private evidence: `.local/nctl-modularization/p4/20260728T022804Z/` (directory mode `0700`; captured files are private).

- All six component worktrees were clean before the phase's tracked documents were added. The frozen tuple is superproject `f46a3a6`, nctl `786b61b`, nintent `4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, and ansible_agdev `66b31c8`. The local running Nautobot image remains the inherited nintent `84ac0b1` revision.
- A read-only source snapshot confirmed `desired_compute_platforms=0` and `desired_compute_instances=0`.
- `nctl` ordinary passed: **970 passed**. Compute conformance passed: **1 passed**.
- The Phase 0 measurement method was rerun before edits. Its component collection counts are nctl 970, nintent 236, nauto 110, nodeutils 54, and Ansible helper 4; it also captured tracked file/line totals and test ratios.
- Baselines were captured for deterministic dnsmasq, hosts-intent, and production artifacts; `nctl drift --json`; `nctl status --json`; and the cluster-scoped `nctl reconcile --json` dry-plan envelope. The only declared exclusions for later production comparisons are generated timestamp, generation ID, and generation-dependent report-path fields (including their `nintent_*` counterparts). No apply-mode command, live node operation, or cross-repository change occurred.
- Inherited Phase 3 residuals remain external to this phase: the physical IPAM/action-boundary test split remains in `test_reconcile_executor.py`, and both local Nautobot runtime-gate modes previously stopped during test-database setup with the `dcim_module` `pg_type_typname_nsp_index` duplicate-key failure. Step 8 will retry both runtime modes and report their actual outcome.
