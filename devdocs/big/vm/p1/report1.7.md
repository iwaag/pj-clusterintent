# Step 7 — Field classification and rejected-field audit

Status: complete.

## Retained-field table

```text
model/schema | field | class | owner | source | consumer
```

| model/schema | field | class | owner | source | consumer |
|---|---|---|---|---|---|
| DesiredComputePlatform | name/slug | Intent | operator | form/YAML | UI, adapter lookup |
| DesiredComputePlatform | provider_type | Contract | schema | fixed `proxmox` | adapter dispatch |
| DesiredComputePlatform | lifecycle | Intent | operator | form/YAML | observe/link/create/start gate |
| DesiredComputePlatform | control_node | Intent | operator | form/YAML | observation/actuation target |
| DesiredComputePlatform | config.cluster_name | Derived (optional intent) | operator or derivation | live cluster.name uniqueness (report 1.2/1.5) | Cluster matching, scope guard |
| DesiredComputePlatform | config.default_storage | Derived (optional intent) | operator or derivation | live storage list (report 1.2 §2, `local`/`local-lvm`) | create payload default |
| DesiredComputePlatform | config.default_bridge | Derived (optional intent) | operator or derivation | live NIC evidence (`vmbr0`, report 1.2 §4) | single-NIC create payload |
| DesiredComputePlatform | realized_cluster(+_source) | Actual link/cache | nctl link action | Nautobot Cluster (0 rows live today) | explicit-first matching |
| DesiredComputeInstance | desired_node/platform/instance_kind | Intent | operator | form/YAML | scope, adapter dispatch |
| DesiredComputeInstance | desired_power_state | Intent | operator | form/YAML | start-plan gate |
| DesiredComputeInstance | vcpus/memory_mb/root_disk_gb | Intent | operator, bounded by live fixture (`agdnsmasq`: 1 vcpu/512MB/8GB, report 1.2 §4) | form/YAML | create/drift |
| DesiredComputeInstance | config.vmid | Intent (optional) | operator or derived allocation | live VMID range observed 100-108 (report 1.2 §3) | create payload, collision check |
| DesiredComputeInstance | config.template | Intent (creation-only) | operator | Step 8 build-source evidence | create only |
| DesiredComputeInstance | config.storage/bridge | Intent (optional override) | operator | live storage/bridge lists | create payload |
| DesiredComputeInstance | config.unprivileged | Intent | operator | live `unprivileged: 1` observed for agdnsmasq | LXC security intent |
| DesiredComputeInstance | realized_vm(+_source) | Actual link/cache | nctl link action | Nautobot VirtualMachine (0 rows live today) | explicit-first matching |
| DesiredEndpoint | mac_address | Intent (new) | operator, initially populated from observed `bc:24:11:23:dc:b7` under "operator confirmation required" (report 1.4) | form/YAML | DHCP render, Proxmox NIC create |

## Rejected-field table (with live-evidence-backed reasons)

| Field/category | Reason rejected | Live evidence |
|---|---|---|
| API URL, username, token ID, TLS flag, vault reference | Credentials stay outside nintent (plan §6, roadmap Decision 6) | `.local/secrets`/`token_file` pattern (report 1.0 §2) already the correct owner |
| CPU model, sockets, NUMA, ballooning, BIOS/UEFI, machine type | No named consumer | Live QEMU raw config (VMID 102, report 1.2 §5) shows these exist in Proxmox but nothing in nctl/nintent reads them |
| Arbitrary args/cloud-init | No named consumer, unbounded surface | — |
| Utilization, uptime, task/history, HA, replication, backup/snapshot policy | No named consumer | Live raw data includes `uptime`, `netin/netout`, `diskread/diskwrite` (report 1.2 §4) — explicitly excluded from any retained field |
| Bind mounts, passthrough, USB/PCI, tags | No named consumer | Live `tags: null`, `config_tags` (VMID 102) observed but unused by any consumer |
| Provider-generic/AWS/Azure fields | Out of roadmap scope (Decision 3) | — |
| Duplicate IP/DNS/MAC ownership, persisted `net0` | Single-owner rule (roadmap Decision 4); `net0`/slot is adapter-derived, not stored intent | Report 1.4's frozen mapping stores bridge+MAC as intent but derives `net0` only at execution time |
| QEMU aggregate `maxdisk` as "root disk" | Proven non-equivalent to actual root volume | Report 1.2 §4/§7: `disk_gb=7.78` vs `config_rootfs size=8G` for the same guest |
| QEMU root/boot disk (any field) | No exact source proven yet | Report 1.2 §7: only LXC `rootfs` grammar was confirmed; QEMU has no equivalent parsed field today — deferred to Phase 6 |
| `cluster.id` as stable Cluster key | Observed `null` live for a single-node cluster | Report 1.2 §2, report 1.5 |

## Moving a rejected field to retained

Per plan §Step7, this requires a current concrete use case, a named consumer, a safe actuator
mapping, and fresh actual evidence — none of the rejected fields above meet this bar today. The
one live example that came close (`cluster.id`) was evaluated and still rejected because the
alternative (`cluster_name` uniqueness) is sufficient given today's single-node cluster.

## Gate evaluation

Every retained field cites a named consumer from reports 1.2-1.6; every rejected field cites a
concrete reason, several backed by the live raw Proxmox config observed in Step 2. Step 7 gate
passed.

## Discrepancies

None.
