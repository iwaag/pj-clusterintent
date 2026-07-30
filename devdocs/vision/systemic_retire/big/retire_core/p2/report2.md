# Retire core Phase 2 — Step 2 seed

Date: 2026-07-30

## Status: complete

Committed in nauto `6462ebc`.

The existing `proxmox_presence` CustomField now targets both
`virtualization.vminterface` and `virtualization.virtualmachine`; its description now explicitly
covers complete scoped guest and interface enumeration. No second presence field or migration was
added. The nauto ordinary suite remained green (112 tests).
