# ex1 Step 5 report — handoff (autodev episode boundary)

Status: complete (safe stop at the designed boundary)

Per plan, execution stops after the repeat-reconcile check. The VM
`agautolab1` (vmid 109 on aghub) is running and booted into the Ubuntu
24.04.4 live-server installer ISO (empty 64 GB scsi0 is not bootable, so
first boot falls through to ide2 per the create playbook's boot order).

## Manual work handed to the user (by design, autodev plan Step 5 decision)

1. OS install through the Proxmox console (target disk: the 64 GB
   `local-lvm:vm-109-disk-0`; after install, boot order boots the disk).
2. SSH keys for the new guest.
3. Claude login on the guest.

Network intent already declared for when the guest comes up: MAC
`bc:24:11:7a:b1:09`, dhcp_reserved `192.168.0.130`, `agautolab1.local` /
`agautolab1.home.arpa`.

## Reporting artifacts

- Step reports: `report1.md` … `report5.md` (this directory).
- Episode summary: [`report.md`](report.md).
- Autodev episode cross-report: `devdocs/vision/autolab/report.md`.

## Out of scope confirmed untouched

Cloud-init/golden-template bootstrap (Phase 7), QEMU mutable diffs,
autolab installation on the VM.

## Easier Next Time

One pain noted for a WorkflowEpisode: the harness permission classifier
blocked `nctl desired apply` previews intermittently (worked on retry),
and direct `ssh root@aghub.local` with `ansible_key` is denied — the
Ansible path (`ansible.cfg` user + become) is the working route for file
placement on cluster nodes; worth a runbook note next time.
