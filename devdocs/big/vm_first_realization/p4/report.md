# First Proxmox Guest Realization — Phase 4 Report

Status: **complete**. One Proxmox LXC container, `agfixture` (VMID 109), was created and started exactly once on `aghub`.

See [report0.md](report0.md) through [report8.md](report8.md) for the per-step evidence. The authoritative creation operation is `01KYMKYC3Q7566T9H3WE1QM92B`; it preserves the successful create/start tasks, the later result-file failure, and its successful post-actuation nodeutils/ingest evidence. The recovery ledger operation is `01KYMM53DMK2EVETKKHPQSPXXS`, which linked VirtualMachine `3a6aa5b1-f128-4d23-82f7-9c97acff3a68` and made no Proxmox mutation.

Final drift: compute realization converged; node terminal is `waiting_for_manual_initial_access`; no repeat action is planned. No credentials or key material are recorded here.
