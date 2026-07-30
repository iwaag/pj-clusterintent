# Retire core Phase 3 — Step 4 live dry proof

Date: 2026-07-30

## Status: blocked — operator approval required

This step has not written `agfixture`.

The approved Phase 3 plan explicitly requires operator approval before both
canonical Desired-state batch writes: first `approved+present` to
`retired+absent`, then the exact revert to the Phase 5 starting state. The
planned operations are reversible and make no Proxmox mutation, but they do
change the shared scratch Nautobot Desired-state authority and therefore
cannot be inferred from development authorization.

After approval, execute only the two canonical writer calls with preview
first, capture the new drift and dry reconcile evidence, then revert and
confirm the Step 0 baseline. No `--yes` reconcile, dispatch handler, Ansible,
or Proxmox operation is part of this step.
