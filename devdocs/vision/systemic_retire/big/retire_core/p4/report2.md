# Phase 4 Step 2 — bounded destroy playbook

Status: complete.

Added `ansible_agdev/playbooks/proxmox/destroy_lxc.yml`. It has one host and accepts one VMID only. Its reachable `pct` sequence is bounded to:

1. `status <vmid>`;
2. `stop <vmid>` only when the probe reports running;
3. `destroy <vmid>` only when the guest was present;
4. final `status <vmid>` requiring absence.

It writes a controller-local `0600` JSON result, distinguishing a destruction from an already-absent guest. It contains no loop, wildcard, cluster action, `qm`, or other guest mutation.

Validation: the real-playbook Ansible conformance gate used a disposable `pct` stub and asserted both running (`status → stop → destroy → status`) and already-absent (`status → status`) paths. It passed (3 tests total).
