# Phase 1 — Step 0 report: baseline re-verification

Status: **complete** (read-only baseline only). Run 2026-07-28 JST.

| Item | Result |
|---|---|
| Superproject / nctl / nauto / nintent | `34261ed` / `1ca0e74` / `6dab422` / `4f46bc8` |
| Running Nautobot services | web, worker, scheduler healthy |
| Baked nintent / nauto | `84ac0b125c996bcc9c821252c34e84ca967c64f0` / `1c78af8bdbfc69cafdc293b4082f866de9f271b0` |
| Compute ledger | `aghub-proxmox`, complete observation at `2026-07-27T22:20:28Z`; `agdnsmasq` is LXC VMID 108 on `aghub` |
| Drift baseline | 5 unknown, 5 converged, 1 drifting; zero desired compute rows and zero compute codes |
| `agdnsmasq` MAC cross-check | Device-side `bc:24:11:23:dc:b7` equals VMInterface `BC:24:11:23:DC:B7` after normalization |
| dnsmasq render SHA-256 | `305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1` (matches p0) |

The p0 report's `hosts-intent` and production digest values did not match a direct hash of the
current command output (`a6d7a1e45a2d71080ed6df16a71e1c3c907a63406133425291c8ae119303383c` and
`468b5e67d1eeb663fd1520f8e582a7e46daabdf2e149dc537ff5b91b688c5794`). This is a baseline
finding to resolve with canonical artifact bytes during Step 1; it is not a compute or Proxmox
mutation. The Cluster observation is within the shared 72-hour freshness limit, so no collection
or ingest was needed.

Phase 0 remains blocked only on the separate, operator-confirmed new-guest fixture record; that
record is not required for this phase's existing `agdnsmasq` seed.
