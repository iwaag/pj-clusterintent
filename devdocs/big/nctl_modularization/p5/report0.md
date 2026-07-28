# P5 Step 0 — Freeze and baseline

Status: complete.

Private evidence: `.local/nctl-modularization/p5/20260728T000000Z/`.

- The frozen tuple is superproject `6ed0516`, nctl `b5b4a44`, nintent `4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, and ansible_agdev `66b31c8`. All six worktrees were clean before this tracked report was added. The running Nautobot image has nintent package version `0.9.0`; its inherited installed source revision is recorded by Phase 0 as `e8732f1`.
- Read-only Nautobot inspection found `desired_compute_platforms=0` and `desired_compute_instances=0`.
- `nctl` ordinary passed: **974 passed**. Compute conformance passed: **1 passed**.
- The Phase 0 measurement method was copied into the P5 evidence root before use, preserving the method while avoiding a further write to Phase 0 evidence. It found 94 nctl Python modules and 15 recorded layer-violation rows (plus the header). A first direct invocation exposed that the historical helper hard-codes its Phase 0 output directory; it rewrote only its derived private measurement files, not artifacts, source, or tracked files. All subsequent P5 measurement output uses the copied helper under the P5 evidence root.
- Captured read-only renders, `drift --json`, `status`, and a plan-mode `reconcile --json`; no apply-mode command or external actuation ran. dnsmasq bytes match the Phase 0 digest exactly. Raw hosts-intent and production hashes differ only because they embed the declared dynamic timestamp, generation ID, and generation-dependent report-path fields. After normalizing exactly those declared exclusions, all three artifact diffs are empty. This is inherited scratch-state timing, not a contract difference.

