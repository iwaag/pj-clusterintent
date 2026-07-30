# Retire core Phase 3 — Step 3 classification and planning

Date: 2026-07-30

## Status: complete

nctl commit `a3a01ec5aa2c0899838a80d96afd96676adf0942` registers
`destroy_compute_instance` as an automatic, mutating, observation-requiring
`compute_destroy` reconciler and makes the planner derive it again from the
typed disposition.

- A qualifying retired+absent+present LXC creates exactly one action for one
  `compute_instance`, with the complete frozen identity and exactly its
  control-node `host_slugs`.
- The destroy action suppresses same-node `observe_node`, just as a create
  transition does. Link planning independently refuses retained, destruction,
  and removal-complete dispositions.
- `compute_presence_lifecycle_conflict` and
  `compute_instance_removal_complete` are manual-review/no-action codes;
  failed destroy gates cannot be upgraded from a stale diff and return named
  manual-review fallbacks.

This is intentionally inert. `destroy_compute_instance` is absent from the
dispatch handler map, and tests assert that there is no `--allow-destroy`,
destroy playbook, or `pct` invocation. Consequently, a Phase 3 `reconcile
--yes` reaches the standard `unknown_reconciler` failed, non-mutating result
for this one planned action. Phase 4 owns the capability, handler, and any
Proxmox mutation.

Verification: `cd nctl && uv run pytest -q --durations=20` — **996 passed**.
