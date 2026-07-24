# Step 0 — Safety preflight and live contract recheck

Status: `complete`.

Raw evidence: `.local/vm-p2/20260724-step0/manifest.txt` (private, mode 0700/0600).

## 1. Revision and dirty-state check

`git submodule status` on the superproject shows all five participating submodules exactly at
the plan-writing manifest revisions, and `git status --short` is clean:

| Repository | Revision | Matches plan manifest |
|---|---|---|
| `ansible_agdev` | `c6faafdaef4ed43fe3477ee0443437d4b9b58ea9` | yes |
| `nauto` | `489ff6fc869b4df7748b862dd0b8efc75aea764f` | yes |
| `nctl` | `576e13b856fc5a657cd0b6cce4382679ba60e6a6` | yes |
| `nintent` | `ad9d36397d23c269ad748e13acbccc532fa29f52` | yes |
| `nodeutils` | `36e1c5752ba895780eea21b8e994926b93cc1c53` | yes |

No source-changed audit is required before Step 1.

## 2. Current live Nautobot counts (allowlisted)

| Object | Count |
|---|---:|
| `dcim.Device` | 5 |
| `virtualization.ClusterType` | 0 |
| `virtualization.Cluster` | 0 |
| `virtualization.VirtualMachine` | 0 |
| `virtualization.VMInterface` | 0 |
| `extras.CustomField` | 36 |

This matches the Section 4.3 baseline (zero Cluster/VM/VMInterface/`proxmox_*` custom fields).
The `aghub` Device row exists (Phase 1 baseline), UUID recorded privately.

## 3. GraphQL/REST schema probe

- GraphQL query root exposes `cluster`/`clusters`, `cluster_type`/`cluster_types`,
  `virtual_machine`/`virtual_machines`, `device_cluster_assignment`/`device_cluster_assignments`.
- REST `OPTIONS` on `virtualization/virtual-machines/`: native `disk` field is integer GB
  (`"Disk (GB)"`), native `memory` field is integer MB (`"Memory (MB)"`), confirming the unit
  assumptions in Section 5.4.
- REST `OPTIONS` on `virtualization/interfaces/`: fields include `mac_address`, `bridge`,
  `virtual_machine`, `ip_addresses`, `custom_fields` — matches the VMInterface mapping plan.
- REST `OPTIONS` on `ipam/ip-addresses/`: the model exposes **both** `interfaces` and
  `vm_interfaces` M2M relations, and a separate `ipam/ip-address-to-interface` through-endpoint
  exposes mutually exclusive `interface`/`vm_interface` fields. This positively confirms Section
  5.4/5.6's assumption that one exact IPAddress row may relate to both a Device interface and a
  VMInterface (dual-layer evidence) — the live model supports it, so Step 5 need not special-case
  its absence.

## 4. Proxmox cluster-identity classification

Read through the installed, still-read-only helper (`sudo /usr/local/libexec/nodeutils-pvesh-read
/cluster/status`) on `aghub`: the response is a single `type=node` row with no provider cluster
row. This positively classifies the live case as `standalone_node_fallback`, `identity_value` =
`aghub`, current synthesized display name `aghub-proxmox`, and the durable scope key will be
`standalone-device:<aghub Device UUID>`, matching Section 5.5 rule 3. The observer Device UUID is
recorded privately in the run manifest, not in this committed report.

## 5. Remote nodeutils/helper state

- `/opt/nodeutils` on `aghub` is at `36e1c5752ba895780eea21b8e994926b93cc1c53`, clean, matching
  the submodule pin exactly.
- The installed helper is `/usr/local/libexec/nodeutils-pvesh-read`; its SHA-256 digest is
  recorded in the private manifest for later before/after comparison.
- The current `/var/lib/nodeutils/inventory.json` report is `nodeutils.inventory.v2` with a
  `facts.proxmox` block that has **no nested `schema_version`** and still contains raw
  `cluster`/`resources`/`nodes`/`networks`/`storages`/per-guest `raw` fields — exactly the Section
  4.1 baseline this phase replaces.
- The live guest set includes LXC `agdnsmasq` (VMID 108, running, `node=aghub`) and QEMU
  `aghaos` (VMID 102, running, with `qemu-guest-agent` interface evidence) — both are usable as
  golden fixtures in Step 1.
- Live storages: `local` (advertises `vztmpl` among its content types) and `local-lvm`
  (`images,rootdir`). `local` is the only Step 2 storage-content candidate on this host today.

## 6. nauto/nctl baseline

- `nauto/seed/nodeutils_ingest.yaml` has no future-skew policy key yet — matches the Section 4.3
  baseline; Step 3 adds `max_future_skew_seconds` (default 300) here.
- `nauto/jobs/` contains only `seed_home_cluster.py`, `nodeutils_ingest_batch.py`,
  `nodeutils_ingest_summary.py` — Device-only ingest, no virtualization writer yet.
- `nctl_core/sources/actual.py` currently builds `ActualVirtualMachine` from only `id`/`name` via
  a GraphQL query with no Cluster/VMInterface fields — matches Section 4.4 baseline.

## 7. Secret hygiene

No credential value appears in any command argv, this report, or the retained manifest; the
Nautobot token was read only from `.local/secrets` (already git-ignored) and never echoed. SSH
used the existing `ansible_key` identity and pinned host-key alias from the generated inventory.

## Gate

Starting state, exact live API/relation shape, Cluster-name provenance
(`standalone_node_fallback`), time policy (none yet, to be added), and rollback revisions are all
recorded and match the plan's assumptions. No discrepancy requires a pre-Step-1 audit.

Proceeding to Step 1.
