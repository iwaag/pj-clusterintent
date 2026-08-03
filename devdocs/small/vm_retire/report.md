# QEMU VM Retirement Report (`aghaos` / `homeassistant`)

## Overview

Successfully retired and destroyed the `homeassistant` QEMU Virtual Machine (`aghaos`, Proxmox VMID: 102) on host `aghub` using the official `nctl reconcile` workflow.

## Timeline & Executed Steps

1. **Braindump Creation & Review**:
   - Recorded user wish to decommission `homeassistant` (Braindump ID: `7cf9c7f9-3d55-427e-83a5-090d6f4be2d8`).
   - Attached Alignment Review outlining the retirement path via Nautobot desired state and `nctl reconcile`.

2. **Desired State Declaration**:
   - Upserted `DesiredNode`: `slug: aghaos`, `lifecycle: retired`.
   - Upserted `DesiredComputeInstance`: `desired_presence: absent`, `instance_kind: virtual_machine`, `config.vmid: 102`, linked with `realized_vm` (`a6f18ece-aa90-4da0-a4bb-c0821acb6e86`).
   - Transaction status: `committed`.

3. **Reconciliation & Automated Destruction**:
   - Command: `nctl reconcile aghaos --allow-destroy --yes`
   - **Operation ID**: `01KZ304R6VX1FGJZCXQ37M6X3W`
   - **Action**: `destroy_compute_instance:aghaos` (via Ansible playbook `destroy_qemu.yml` on `aghub`).
   - **Proxmox VM Destroy Result**: `destroyed: true`, `absent: true`.
   - **Post-Actuation Observation**: Triggered automatic nodeutils collection on `aghub` and updated Nautobot actual ledger.

## Final Result

- **Reconcile State**: `converged`
- **Scope Status**: `aghaos` scope converged (13 total converged targets in cluster).
- **Proxmox VM State**: VMID 102 successfully removed from host `aghub`.
