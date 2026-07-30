# Phase 4 Step 0 — baseline

Status: complete (read-only).

Recorded 2026-07-30 before Phase 4 implementation:

- Superproject `27c4033`; nctl `a3a01ec`; ansible_agdev `aa8f9f4`; nintent `7c88023`; nauto `6462ebc`; nodeutils `775ed7f`.
- `agfixture` is `approved` with `desired_presence=present`; its linked LXC is observed present (VMID `109`).
- `nctl drift --json` reported `agfixture` compute and node targets converged; cluster summary was `converged=9`, `drifting=2`, `unknown=4` for unrelated existing findings.
- `nctl reconcile agfixture --json` was a non-mutating plan with zero actions, operation `01KYRPN56FHY29B1K8SR7NASXN`.

No Desired or Actual state was changed.
