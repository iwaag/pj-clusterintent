# autolab episode — clusterintent implementation report (Step 5 job runner VM)

Date: 2026-08-07
Reported from: `devdocs/vision/vm/ex1/` (clusterintent implementation work for
the autodev episode).

## Delivered

`agautolab1` — the autodev episode's Step 5 job runner — now exists as a live
QEMU VM, created through `nctl reconcile` (first live QEMU creation on this
cluster):

- vmid 109 on aghub (`aghub-pve`), 4 vCPU / 8192 MB / 64 GB `local-lvm`,
  `vmbr0`, MAC `bc:24:11:7a:b1:09`, dhcp_reserved `192.168.0.130`,
  `agautolab1.local` / `agautolab1.home.arpa`.
- Running and booted into the Ubuntu 24.04.4 live-server installer ISO.
- Fully declared in desired state (node / endpoint / compute_instance
  triple); post-create observation linked the VirtualMachine and a repeat
  reconcile plans no further action.

Enabling work: iso storage-content evidence is now collected by nodeutils,
accepted by nauto's ingest, and satisfies the QEMU create gate. Details and
per-step evidence in [`../vm/ex1/report.md`](../vm/ex1/report.md).

## Handed to the user (autodev plan Step 5 boundary, by design)

1. OS install via the Proxmox console (install to the 64 GB disk; boot order
   then boots the disk).
2. SSH keys for the guest.
3. Claude login on the guest.

Autodev Step 5 (autolab installation on the VM — claude CLI + node + uv job
runner) resumes after this manual handoff. Cloud-init/golden-template
bootstrap remains a Phase 7 decision.
