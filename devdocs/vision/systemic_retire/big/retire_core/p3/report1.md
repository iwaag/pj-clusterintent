# Retire core Phase 3 — Step 1 pure disposition

Date: 2026-07-30

## Status: complete

nctl commit `aa422a6225723b4bb7cc310b98e9b87badd4afaa` adds the pure
`derive_compute_dispositions()` derivation. Every desired compute instance now
gets exactly one typed outcome: `ordinary`, `presence_conflict`, `retained`,
`destroy_required`, `removal_complete`, or `unknown`.

The derivation reuses the existing typed realization rather than reading drift
text. It pins the frozen destruction identity when (and only when) the
retired+absent instance has a trustworthy, explicitly `present` LXC match:
instance/node/platform/cluster/VM IDs, VMID, observed Proxmox node, control
node, and one-item `host_slugs`. `presence=None` cannot authorize destruction
and remains `retained`; explicit `presence=absent` is `removal_complete`.
Every rejected actionable gate carries a named reason.

The current desired-platform schema no longer contains `provider_type`: its
only supported provider was structurally reduced to Proxmox in nintent
migration `0019`. The former non-Proxmox gate is therefore unrepresentable at
this nctl boundary; the remaining instance kind, guest type, VMID, cluster,
control-node, realization, and platform-trust gates are tested directly.

Verification: `cd nctl && uv run pytest -q --durations=20` — **992 passed**.

No evaluator, planner, dispatch handler, CLI option, playbook, Actual write,
or Proxmox call was added in this step.
