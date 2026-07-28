# First Proxmox Guest Realization — Phase 3 Step 2 Report

Status: **complete**.

`nctl` now reads the Cluster's closed `proxmox_storage_content` ledger through
typed `ProxmoxStorageScope` and item models. The live `aghub:local:vztmpl`
scope exposes the required Ubuntu 24.04 volid. A malformed storage scope is
dropped and counted locally while the remaining Cluster facts continue to be
usable; it cannot downgrade the entire platform into a false
`compute_platform_missing` result.

Evidence:

- focused reader/evaluation/render tests: **29 passed**;
- the pre-existing and post-change live drift payloads are byte-identical after
  removing only their generated/fetched timestamps (the unavoidable envelope
  freshness fields); and
- the live drift status remains 9 converged, 3 unknown, 1 drifting, with
  `compute_instance/agdnsmasq` converged.

The `nctl actual` diagnostic intentionally remains unchanged; storage content
is typed input for creation preflight, not a new public actual-render field.
