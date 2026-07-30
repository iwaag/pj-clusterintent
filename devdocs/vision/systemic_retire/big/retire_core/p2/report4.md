# Retire core Phase 2 — Step 4 deployment and live transition

Date: 2026-07-30

## Status: complete

The operator pushed the exact nauto revision, and the scratch deployment completed:

- nauto `6462ebcbd9b8033853b60473dbe7f18d400cdd0b`
- nctl `13ae1cd64646cc94af76f54a200ca3d69b611318`
- the rebuilt web image's `/opt/nautobot/build_info.json` records nauto `6462ebc` and nintent
  `7c88023`.
- Git Repository `main` synced successfully to `6462ebc`; the worker checkout and refreshed Job
  records were verified at that SHA.
- `Seed Home Cluster` was applied with `dry_run=false`, `update_existing=true`; the deployed
  `proxmox_presence` CustomField now targets both `virtualization.virtualmachine` and
  `virtualization.vminterface`.

The first fresh, `aghub`-scoped `nctl reconcile aghub --refresh-observation --yes` run completed
as operation `01KYRK6N41KZH4025VK89EXJ12`: normal nodeutils collection and the real **Ingest
Nodeutils Inventory** Job produced a complete platform observation and wrote all ten real guests
(including `agfixture`) `proxmox_presence=present`.

A disposable scratch VM `p2-synthetic-absence-proof` (LXC VMID 65002, no Proxmox guest) was then
created in the observed Cluster. The second fresh observation/real Job ingest, operation
`01KYRK9W1H1HEX3ZG56P7NRJPM`, changed only that synthetic VM to `absent`; all real guests stayed
`present` and platform state remained `complete`. Its `proxmox_observed_at` advanced to the fresh
generation. The synthetic row was deleted afterward. No Proxmox or `agfixture` write occurred.

Before, during, and after the proof, `nctl drift --json` remained `drifting=2`, `converged=9`,
`unknown=4`, with the same compute codes. The intentional only output addition is
`compute_realization_summary.actual.presence`.
