# First Proxmox Guest Realization — Phase 2 report

Status: **complete for the existing-guest ledger-link objective**.

`agdnsmasq`'s existing LXC VMID 108 is now explicitly linked through the
approved narrow API: platform `aghub-pve` links to its observed Cluster and
the desired compute instance links to its observed VirtualMachine. The
derivation is shared by drift and planning, the dry plan fixed both UUIDs,
the handler confirmed writes through GraphQL, and a fresh drift reports
`match_basis=linked`; repeat planning contains no compute action.

The classification changed from manual review to the single automatic
`link_compute_realization` ledger patch. `compute_platform_observation_stale`
remains manual review because no fresh, unique candidate exists in that case.
The interface-contract hand-off is implemented by reinstating exactly two
compute REST collections, each restricted to its realization relation/source
pair. The inert test was replaced by an exact ledger-action/no-Proxmox-path
contract.

See [report0.md](report0.md) through [report8.md](report8.md) for revisions,
deployment, operation IDs, verification, and the stated Import Job durability
follow-up. Nothing was created or mutated on Proxmox.
