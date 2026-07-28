# P3 Step 0 — Frozen tuple and baselines

Status: complete.

Private evidence: `.local/nctl-modularization/p3/20260728T013700Z/`.

- All six worktrees were clean. The implementation tuple remains nctl
  `a07db7f35e83ed53e8105edf5b4a133fd398692b`, nintent
  `3fbe896f9378006b8aeac22063488ba76ce9b5b4`, nauto
  `6dab422a725a2e2e4e24e98079e992d1111c0ef1`, nodeutils
  `775ed7fad5110a96186a737147b87d3bf450ced2`, and ansible_agdev
  `66b31c89986d1b2ecfa187a72209d8bd96838fd4`. The superproject began at
  `6439de5fc63e04ab1b2f9742c712246be5ac4ea5`.
- The local image reports nintent `84ac0b125c996bcc9c821252c34e84ca967c64f0`.
  This differs from the plan's planning-time image note but is inherited local
  scratch state; no application code or image was changed. The full runtime
  gates will decide whether it explains any failure.
- Desired compute platform and instance counts are both zero. Compute remains
  inert.
- `uv run pytest -q --durations=20` passed: **970 passed**. Compute conformance
  passed: **1 passed**. The committed fixture SHA-256 is
  `ccff71d9f4c7715a46c026c1529373fc38806208df49f512bc85d6a3e31b81ce`.
- The Phase 0 measurement method was rerun before edits. The baseline contains
  package/file/line totals, import edges, fan-in/fan-out, layer violations, and
  the executor's 31 direct imports.
- Cluster and `agdnsmasq` host-scope plan-mode envelopes, plans, results, and
  JSONL streams were captured using a phase-owned event directory. Both commands
  stayed in plan mode.
- dnsmasq bytes are identical to the Phase 0 baseline. Hosts-intent, production,
  and production-report comparisons also pass after excluding only their declared
  generation/timestamp/report-path fields (including their `nintent_*` names).
  Envelope-code and reconcile event-vocabulary baselines were captured.

