# Phase 2 — Step 0 report: baseline

Status: **complete** (read-only; 2026-07-28 JST).

The local Nautobot web, worker, and scheduler were healthy. `nctl drift --json`
identified exactly one fresh, unique link candidate: compute platform `aghub-pve`
(`a7161364-75b2-4f80-b208-5d210144590d`) maps to Cluster
`0ef3f747-b905-42f7-82d8-7e8572e9b63d`; compute instance `agdnsmasq`
(`e3d067a6-6cd1-410f-a809-91a30f8706a9`) maps by VMID 108 to VirtualMachine
`935f0b6f-5926-41e2-80db-bfa4b637cfce`. Both links were absent.

Baseline render SHA-256 values: dnsmasq
`305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1`,
hosts-intent `fd4f62a09806fc2a0736e2434b196c5eaa5e4f018796eaef802ad5c6f54f33b8`,
production `ab204c118826ac758f86bca26d849662c7b58d33bbbce6a01045c7c1bef79969`.
No Proxmox or ledger mutation occurred.
