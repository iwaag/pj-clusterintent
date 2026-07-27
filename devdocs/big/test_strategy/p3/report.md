# Test Strategy Phase 3 — Final Report

Parent: [plan.md](plan.md).

Status: **`complete`**.

## Outcome

Phase 3 closes the retained Tier A external-boundary and DesiredNode transition gaps without a
production/external mutation. The maintained gates now cover loopback OpenSSH and Ansible behavior,
exact-local-source Nautobot/Django behavior, real DesiredNode GraphQL/PATCH/GraphQL transitions,
nodeutils-to-nauto-to-nctl schema traversal, prose authority separation, desired-MAC safe stops,
and compute inertness.

The new nintent runtime cases retain two critical high-layer contracts: a PATCH that succeeds but
is reset before confirmation remains `mutated=true` throughout the public reconcile evidence and
receives fresh final drift; and authorized Braindump/Alignment Review writes leave real drift codes
and planned actions unchanged.

## Final verification

```text
nctl ordinary suite                                      967 passed
nodeutils ordinary suite                                  54 passed
nauto ordinary suite                                     110 passed
ansible_agdev nodeutils helper suite                       4 passed
OpenSSH conformance gate                                   2 passed
Ansible conformance gate                                   1 passed
exact-local-source Nautobot App suite                    290 passed
```

The Nautobot runtime used the named `test_nautobot` database and resolved nintent, nauto, nctl,
and nodeutils from explicit `/tmp/p3-*` copies. All fixture-owned source/dependency copies,
loopback processes, keys, stores, inventories, playbooks, markers, and temporary event artifacts
were removed by their owning test or exact-path cleanup. Persistent scratch containers were reused
as documented prerequisites and were not reset or deployed. No root `nctl.toml`, `.local/secrets`,
real inventory, external host, Proxmox endpoint, public-network service, or production mutation
was used.

## Revision and worktree note

The final Phase 3 test changes include nintent revision `6a4b2afc891b9404c9cbdc09e4c4d6c1e8379711`.
During finalization, pre-existing superproject commit `e01b86c` changed the plan heading; it is
unrelated to this work and was preserved without modification. The final tracked worktree is clean.
