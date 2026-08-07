# ex1 Step 4 report — desired state + first live QEMU create (agautolab1)

Status: complete

## Desired-state batch

Re-synced `.local/desired-state.yaml` via `nctl desired export -o`, then
appended the agautolab1 triple (copied from the agdnsmasq shape with the
planned deltas):

- `desired_node` agautolab1 — service_host, lifecycle active,
  accepted_actual_types [virtual_machine].
- `desired_endpoint` primary — mac `bc:24:11:7a:b1:09` (unused; only
  `bc:24:11:23:dc:b7` existed), ip_policy dhcp_reserved `192.168.0.130`
  (free; used pool IPs were .2/.10/.100/.110/.120), dns
  `agautolab1.home.arpa`, mdns `agautolab1.local`.
- `desired_compute_instance` — platform aghub-pve, instance_kind
  virtual_machine, vmid 109, template
  `local:iso/ubuntu-24.04.4-live-server-amd64.iso`, storage local-lvm,
  bridge vmbr0, vcpus 4 / memory_mb 8192 / root_disk_gb 64, no
  `unprivileged` key.

Preview showed exactly `create: 3, unchanged: 40, conflict: 0`; committed
atomically with `--yes` (same counts).

## Dry plan (operation 01KZDD0X8ZBG80Z8DZVT80RPZB)

Single pinned `create_compute_instance:agautolab1` with `guest_type: qemu`,
vmid 109, the uploaded ISO as template, and the exact endpoint MAC — the iso
evidence gate from Steps 1–3 passed (`compute_template_unavailable` did not
appear). One companion ledger action `reconcile_ipam:agautolab1`
(missing_actual_ip_address; Nautobot-internal). The two manual_review
findings (`missing_interface_candidate`, `no_realized_object`) are the
expected pre-create state of a VM that does not exist yet.

The user pre-approved apply on condition the dry plan matched this shape; it
did.

## Apply (operation 01KZDD27BCEDW9NFXFEHXHJBEC)

```
state: converged, scope summary: converged=2
round 0: [ok] create_compute_instance:agautolab1, [ok] reconcile_ipam:agautolab1,
         [ok] regenerate_production_inventory, [ok] post_actuation_observation
round 1: [ok] link_compute_realization:agautolab1, [ok] regenerate_production_inventory
```

## Acceptance (per the vm report exit criterion)

1. **Created + started:** `qm list` on aghub shows
   `109 agautolab1 running 8192 MB / 64 GB`. `qm config 109`: cores 4,
   `net0: virtio=bc:24:11:7a:b1:09,bridge=vmbr0`,
   `scsi0: local-lvm:vm-109-disk-0,size=64G`,
   `ide2: local:iso/ubuntu-24.04.4-live-server-amd64.iso,media=cdrom`,
   boot order scsi0;ide2 — exactly the planned parameters.
2. **Post-create observation links the VirtualMachine:**
   round 1's `link_compute_realization:agautolab1` succeeded and the final
   scope summary is `converged=2`.
3. **No second create:** repeat dry `nctl reconcile agautolab1`
   (operation 01KZDD4ZSVPB3G1QEA6H0C0ZPQ) plans **zero actions**,
   `scope summary: converged=2`.

This is the first live QEMU creation through `nctl reconcile` — the Phase 6
live exit criterion.
