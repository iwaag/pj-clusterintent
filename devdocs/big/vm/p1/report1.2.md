# Step 2 — Fresh read-only Proxmox observation

Status: complete.

## 1. Pre/post execution non-mutation proof

- Pre-execution: `/opt/nodeutils` HEAD `36e1c5752ba895780eea21b8e994926b93cc1c53`, clean tree;
  helper sha256 `b332447784b68e1e2beb55e83c81b5edecf062599b7aa55d9012be61786b9295`; existing remote
  report `/var/lib/nodeutils/inventory.json` — 38913 bytes, mtime 2026-07-23 22:20.
- Command run over the Step-0-verified SSH route (no Ansible needed; direct verified user):
  `env PYTHONDONTWRITEBYTECODE=1 /opt/nodeutils/.venv/bin/nodeutils collect --proxmox enabled
  --format json`. No `--output`, no `uv run`, no root execution. Exit 0, empty stderr.
- Post-execution: HEAD, tree status, and helper digest identical to pre-execution.
  `/var/lib/nodeutils/inventory.json` size/mtime **unchanged** (38913 bytes, same mtime) — proves
  the collector ran in stdout mode only and did not overwrite the existing remote report.
- Raw stdout saved to `.local/vm-p1/20260724T042313Z/nodeutils-collect.json` (mode 0600, outside
  Git).

## 2. Top-level assertions

- `schema_version`: `nodeutils.inventory.v2` (top-level; there is no separate nested
  `facts.proxmox.schema` field yet — Step 5 must add one, per plan §5.6).
- `collected_at`: `2026-07-24T04:31:04+00:00`.
- `collector`: `{"command": "collect", "name": "nodeutils", "version": "0.2.0"}`.
- `facts.proxmox.enabled`: `true`; `facts.proxmox.detected`: `true`.
- Cluster: `name: aghub-proxmox`, `node_count: 1`, `nodes: ["aghub"]`, `status: Active`,
  `type: Proxmox VE`. `cluster.id` is `null` in this single-node cluster (no stable cluster UUID
  is offered by `/cluster/status` for a 1-node cluster — noted for Step 5's identity contract).
- One Proxmox node observed: `aghub`, `status: online`.
- Two storages: `local-lvm` (`type: lvmthin`, `content: images,rootdir`, `active/enabled: 1`) and
  `local` (`type: dir`, `content: backup,vztmpl,import,iso`, `active/enabled: 1`).

## 3. Guest inventory (positive count assertion)

- 3 QEMU VMs: `105 agk3s` (running), `102 aghaos` (running), `100 infra` (stopped).
- 6 LXC containers: `103 agprome` (stopped), `104 aggrafana` (stopped), `101 agansible`
  (running), `107 agkeadhcp` (stopped), `108 agdnsmasq` (**running**), `106 agnomad` (stopped).

## 4. `agdnsmasq` full evidence (VMID 108)

```
guest_type: lxc
node: aghub
proxmox_status: running
vcpus: 1, memory_mb: 512
disk_gb: 7.78   (derived: bytes_to_gb(maxdisk=8350298112))
config_rootfs (raw): "local-lvm:vm-108-disk-0,size=8G"
interfaces: [{name: net0, bridge: vmbr0, mac_address: BC:24:11:23:DC:B7,
              ip: 192.168.0.2/24, gateway: 192.168.0.1}]
unprivileged: 1
```

- **Confirmed live** that `disk_gb` (7.78, from aggregate `maxdisk`) and the actual rootfs grammar
  (`size=8G`) disagree numerically (binary-GiB rounding/overhead), reproducing plan §4.1/§Roadmap
  Decision 5's warning that `maxdisk` must not be called the root-disk value. The exact rootfs
  size, `8G`, must come from parsing `config_rootfs`, not `disk_gb`.
- Configured interface evidence (bridge `vmbr0`, MAC `BC:24:11:23:DC:B7`, slot `net0`) is present
  and unambiguous for this guest kind (LXC never goes through the QEMU guest-agent path).

## 5. Live confirmation of the guest-agent interface-replacement loss (plan §4.1 / roadmap §5)

VMID 102 (`aghaos`) has `config_agent: "1"` and a live guest-agent result. Direct comparison:

- Raw configured NIC (`raw.config_net0`): `"virtio=02:7B:67:47:0D:FD,bridge=vmbr0"` — MAC
  `02:7b:67:47:0d:fd`, bridge `vmbr0`, slot `net0`.
- Final normalized `interfaces` list for this guest contains **11 guest-agent-reported
  interfaces** (`lo`, `enp0s18`, `docker0`, `hassio`, 7 `veth*` interfaces) and **zero** entries
  carrying `bridge` or `net0`/slot information. One agent entry (`enp0s18`, MAC
  `02:7b:67:47:0d:fd`) matches the configured MAC exactly by normalized value, but the merged
  record loses `bridge: vmbr0` entirely because agent-reported interfaces carry no bridge field.

This is a live, concrete reproduction of the schema defect: a unique normalized-MAC match (config
`net0` ↔ agent `enp0s18`) **is derivable** here, but the current `normalize_qemu_vm()` throws away
the config-side bridge/slot evidence unconditionally rather than joining the two records. Phase 2
must join by normalized MAC rather than replace.

## 6. Storage-content path (not exercised)

Per Step 0's helper audit, `/nodes/{node}/storage/{storage}/content` is outside the current
allowlist. This step does not attempt to bypass that boundary; template-availability evidence
remains unverified until Phase 2 extends the allowlist, consistent with plan §5.7/§9.

## 7. Rootfs grammar (LXC)

`config_rootfs` raw grammar observed: `"<storage>:<volume>,size=<N>G"`
(e.g. `local-lvm:vm-108-disk-0,size=8G`). This differs in both storage prefix and unit encoding
from the QEMU `maxdisk`/`disk` aggregate byte counts — confirms they are not interchangeable
sources, consistent with roadmap Decision 5.

## Gate evaluation

Guest list is non-empty (9 guests total), `agdnsmasq` was positively observed with node, VMID,
power, capacity, NIC, MAC, bridge, and rootfs evidence, and collection time/collector identity
were asserted from live stdout — this satisfies the Step 2 gate (an empty list, missing
`agdnsmasq`, or swallowed error would not have).

## Discrepancies

- `facts.proxmox` currently has no nested schema-version field of its own (only the top-level
  `nodeutils.inventory.v2`). Recorded as a Step 5 contract gap, not a blocker.
- `cluster.id` is `null` for this single-node cluster; Step 5 must decide the stable-identity
  field Phase 2 uses when no cluster UUID is offered.
