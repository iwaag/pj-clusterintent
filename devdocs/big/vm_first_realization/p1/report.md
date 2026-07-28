# First Proxmox Guest Realization — Phase 1 report

Status: **complete**.

Phase 1 wrote the approved desired roots through the canonical Import Job and made compute
realization visible, scoped, and inert. `agdnsmasq` now separately appears as its stale guest-OS
node target and as its VMID-108 compute-instance target. It matches `aghub-proxmox`/`agdnsmasq`
by platform scope and VMID; the sole actionable diagnostic is the deliberately unrecorded ledger
link, reserved for Phase 2.

See [report0.md](report0.md), [report1.md](report1.md), [report2-5.md](report2-5.md), and
[report6.md](report6.md) for evidence, approvals, test counts, and deviations. No Proxmox,
Ansible, or realization-link mutation occurred. Phase 0's new-fixture record remains its sole
unmet condition and is not implied by this completion.
