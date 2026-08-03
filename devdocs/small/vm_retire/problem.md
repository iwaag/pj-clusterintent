# Reason Why QEMU VMs Cannot Be Automatically Destroyed via nctl

`nctl reconcile` enforces a strict safety guard regarding automated compute instance destruction:

1. **LXC Container Restriction**: Automated destruction actions (`destroy_compute_instance`) are intentionally restricted exclusively to Proxmox LXC containers (`instance_kind == "container"` and `guest_type == "lxc"`).
2. **QEMU VM Safety Guard**: Full QEMU Virtual Machines (`instance_kind == "virtual_machine"` and `guest_type == "qemu"`) are explicitly excluded from automated destruction (`instance_kind_not_container` / `guest_type_not_lxc`).
3. **Disposition Result**: Even when a QEMU VM has `desired_presence: absent` and `lifecycle: retired` declared in the Desired State, `nctl` evaluates its disposition as `retained` rather than generating a destroy action. The physical VM must be destroyed via direct Proxmox CLI commands (e.g., `qm destroy <vmid>`) or manual infrastructure management.
