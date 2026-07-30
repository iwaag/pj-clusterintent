# Retire core Phase 2 — final report

Date: 2026-07-30

## Status: complete

Phase 2 makes complete Proxmox observation authoritative for the presence of managed guest rows,
without deleting any Actual row or introducing retirement drift/actuation semantics.

- nauto `6462ebcbd9b8033853b60473dbe7f18d400cdd0b` writes every validated guest `present`; only a
  complete observation of the same Cluster may mark omitted managed `(guest_type, vmid)` rows
  `absent`. Partial, stale, unmanaged, other-cluster, and already-absent cases do not create a
  false absence write.
- The existing `proxmox_presence` seed field now also attaches to VirtualMachine. nctl
  `13ae1cd64646cc94af76f54a200ca3d69b611318` projects it into typed VM facts and the actual side
  of ordinary compute realization evidence.
- Scratch deployment synced and executed the new nauto Job source. Two fresh read-only `aghub`
  collections and real Ingest Nodeutils Inventory Job runs proved all real guests present, then a
  disposable omitted VM absent, while platform completeness stayed `complete`. The disposable
  row was removed and final drift retained its baseline summary and code set.

## Accepted transitional limit and Phase 3 handoff

F3 is accepted: pre-Phase-2 VM rows had no presence field, so replaying an equal-timestamp old
collection would correctly conflict with the new allowlisted `present` value. The first deployed
ingest was therefore a fresh collection, not a replay.

Phase 3 must consume `presence=absent` only after effective lifecycle and desired presence are
applied. In this phase an absent VM deliberately still matches as an ordinary realization; no new
drift code, classification, action, CLI option, Proxmox call, or destroy path exists.

## Verification

| Gate | Result |
|---|---|
| nauto ordinary | 112 passed |
| nctl ordinary | 990 passed |
| compute conformance | 1 passed |
| Nautobot runtime `--keepdb` | 181 passed |

The runtime gate used the final tuple: nintent `7c88023`, nauto `6462ebc`, nctl `13ae1cd`, and
nodeutils `775ed7f`. It reported the established three RawSQL `models.W045` warnings and no test
failure.
