# Retire core Phase 3 — final report

Date: 2026-07-30

## Status: complete

Phase 3 makes compute drift and reconciliation planning retirement-aware while
deliberately retaining a zero-execution destroy path.

| Component | Revision |
|---|---|
| superproject baseline | `d625830f3775ac165cca13089dbc34e403720916` |
| nctl final | `a3a01ec5aa2c0899838a80d96afd96676adf0942` |
| nintent | `7c880237eeb5f1f75b678b199ebd19340bc4a5c5` |
| nauto | `6462ebcbd9b8033853b60473dbe7f18d400cdd0b` |
| nodeutils | `775ed7fad5110a96186a737147b87d3bf450ced2` |

## Delivered contract

- One pure disposition derives ordinary, presence-conflict, retained,
  destroy-required, removal-complete, and unknown outcomes from typed desired
  and actual snapshots. Its destroy candidate pins the exact instance, desired
  node, platform, cluster, VM, LXC/VMID, observed Proxmox node, control node,
  and one-host scope.
- Drift reports `compute_instance_destroy_required` (warning) and
  `compute_instance_removal_complete` (info) and suppresses stale retained
  power/resource/link comparisons. Summary evidence carries Actual presence
  and the disposition.
- `compute_presence_lifecycle_conflict` is the deliberate third-code
  extension to the Phase 0 vocabulary: an absent request outside retirement is
  visible/manual-review and never authorizes removal.
- The planner produces exactly one `destroy_compute_instance` only for the
  frozen LXC gate and refuses retired links. Retired transitions suppress
  same-node observation actions.

## Phase 3 safety boundary and limitations

`destroy_compute_instance` has no dispatch handler. Therefore a Phase 3
`reconcile --yes` fails only that action truthfully as non-mutating
`unknown_reconciler`; no `--allow-destroy`, playbook, `pct` invocation, or
Proxmox write exists. Phase 4 owns all execution capability.

F7 remains: changing a retained removed instance back to `present` can report
`compute_instance_missing` but cannot recreate while the stale link/retained
row exists. Re-creation is outside retire core.

F8 was measured rather than widened: after the fixture became retired+absent,
its node target remained converged with production state `out_of_scope`; the
compute target carried the single destroy-required finding. No guest-OS node
drift blocked this Phase 3 dry proof.

## Live dry proof and verification

With operator approval, an atomic canonical-writer update changed only the
fixture's node lifecycle and compute desired presence. Drift produced the
expected destroy-required finding; dry reconcile operation
`01KYRN1KM7K6ZJDD6W0RDABRXT` contained exactly one frozen destroy action.
The same canonical writer then restored `approved + present`; final dry
operation `01KYRN219DBVX0AV663AB13AA0` had no action and matched the Step 0
fixture baseline. No Proxmox mutation occurred.

| Gate | Result |
|---|---|
| nctl ordinary | 996 passed |
| compute conformance | 1 passed |

nintent, nauto, nodeutils, Ansible, and Nautobot-runtime gates do not apply:
no corresponding component surface changed in this nctl-only phase.

Phase 4 handoff: add the distinct destroy capability and handler, re-resolve
the pinned typed target immediately before mutation, destroy only the planned
LXC, then run normal observation/ingest and prove fresh absence convergence.
