# Retire core Phase 3 — Step 4 live dry proof

Date: 2026-07-30

## Status: complete

With operator approval, the canonical Desired writer processed a two-operation
atomic batch for `agfixture`: its DesiredNode became `retired` and its
DesiredComputeInstance became `desired_presence=absent`. Both the preview and
the apply returned `create=0, update=2, delete=0, unchanged=0, conflict=0`.

The resulting drift had exactly `compute_instance_destroy_required` (warning)
and `compute_realization_summary` (info) for the compute target; it recorded
the retained, explicitly `present` VM and `disposition=destroy_required`.
The retired node target remained converged and moved its production state to
`out_of_scope`, which is the F8 measurement for this fixture. Dry reconcile
operation `01KYRN1KM7K6ZJDD6W0RDABRXT` planned exactly one
`destroy_compute_instance:agfixture` action with the real frozen IDs, VMID
`109`, guest type `lxc`, observed node/control host `aghub`, and only
`host_slugs=["aghub"]`; it had no observe, manual-review, or unsupported
entry.

The same two-operation writer batch was then previewed and committed with
`approved + present`. Both calls again returned exactly two updates. The final
drift and dry plan (`01KYRN219DBVX0AV663AB13AA0`) return `agfixture` to the
Step 0 baseline: both targets are converged, ordinary realization evidence is
present, and the plan has no action.

No `reconcile --yes`, dispatch handler, Ansible operation, Actual-row write,
or Proxmox mutation occurred.
