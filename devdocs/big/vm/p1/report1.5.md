# Step 5 — Freeze the observation and ledger contract

Status: complete.

Field-by-field contract for the nested `facts.proxmox` schema Phase 2 implements, built from the
live shapes recorded in reports 1.2 and 1.3.

## Nested schema version

`facts.proxmox` gets its own `schema_version` key (e.g. `nodeutils.proxmox.v1`), independent of
the top-level `nodeutils.inventory.v2`. Justification: report 1.2 found no nested version key
exists today; Phase 2 changes this schema's shape (interface join, rootfs parsing) independently
of the top-level envelope, so it needs independent versioning.

## Cluster identity

| Field | Source (`pvesh` path/key) | Type/unit | Identity vs volatile | Freshness owner | Consumer |
|---|---|---|---|---|---|
| `cluster_name` | `/cluster/status` `name` | string | stable (but `id` was `null` for this 1-node cluster per report 1.2 §2) | nodeutils observation time | Cluster matching (plan §5.1) |
| `node_count` | `/cluster/status` derived | int | volatile | same | completeness check |
| `observed_node_names` | `/cluster/status` `nodes[].name` | list[string] | volatile | same | scope guard |

Because `cluster.id` was `null` live, Phase 2 must match Cluster candidates by `cluster_name`
uniqueness (plan §5.2's `cluster_name` config key), not by a Proxmox-native cluster UUID — no such
UUID was observed to exist for a single-node cluster.

## Per-guest identity and state

| Field | Source | Type/unit | Consumer |
|---|---|---|---|
| `guest_type` | derived (`qemu_vms` vs `lxc_containers` list membership) | enum `qemu\|lxc` | matching, schema/adapter dispatch |
| `vmid` | `raw.vmid` | int | stable identity, matching |
| `node` | `raw.node`/observation context | string | matching, dependency scope |
| `name` | `raw.name` | string | display only, never sole match key |
| `proxmox_status` | `raw.status` | enum (`running\|stopped\|...`) | power drift |
| `vcpus` | `raw.cpus` | int | capacity drift |
| `memory_mb` | `raw.maxmem` (bytes→MiB) | int, MiB | capacity drift |

## Interfaces (join contract)

| Field | Source | Rule |
|---|---|---|
| `config_interfaces[]` | `raw.config_net{N}` parsed | always retained, never discarded |
| `agent_interfaces[]` | `agent/network-get-interfaces` (QEMU only) | always retained separately |
| `joined_interfaces[]` | derived | created only for a unique normalized-MAC match between one config entry and one agent entry (report 1.2 §5 proves this is derivable — `net0`/`02:7b:67:47:0d:fd` ↔ `enp0s18`/same MAC for VMID 102) |
| unmatched evidence | derived | config-only, agent-only, duplicate-MAC, and missing-MAC cases are retained diagnostically, never guessed by name/order |

Truth table (verbatim from plan §5.6, reproduced against report 1.2 live data — VMID 102 is the
"one unique match / one unique match" row; `agdnsmasq` (VMID 108, LXC) never has agent data and is
always the "config only" row since guest-agent applies only to QEMU):

| Config MAC | Agent MAC | Result |
|---|---|---|
| unique match | unique match | joined, both provenances retained |
| present | absent | config-only; retain bridge/slot, no IP relation |
| absent | present | agent-only; no guessed config match |
| duplicate/invalid | any | ambiguous, target-local blocker |
| unique but different | unique but different | both unmatched |

## Capacity: rootfs vs aggregate disk

| Field | Source | Type/unit | Consumer |
|---|---|---|---|
| `lxc_rootfs_volume` | `raw.config_rootfs` parsed (`<storage>:<volume>,size=<N>G`) | string+int, GiB | LXC root-disk drift |
| `disk_gb` (aggregate) | `raw.maxdisk`/`disk` (bytes→GiB) | float, GiB | **display/estimate only**, never root-disk drift |
| QEMU root/boot disk | none pinned | — | **explicitly unsupported** until Phase 6 (plan §5.6) |

Report 1.2 §4 shows `disk_gb=7.78` vs `config_rootfs size=8G` for the same guest (`agdnsmasq`) —
concrete proof these two numbers must never be treated as the same field.

## Storage-content (Phase 2 allowlist extension)

| Field | Source | Rule |
|---|---|---|
| `storage_content[]` | `/nodes/{node}/storage/{storage}/content` (new, read-only `get`-only) | Phase 2 extends the helper allowlist with exactly this path grammar (`_NODE`/`_STORAGE` identifier patterns matching the existing helper's regex style) plus negative-path tests; Phase 1 does not claim live template availability (report 1.2 §6). |

## Completeness / freshness

- `observed_at` = nodeutils `collected_at` (report 1.2: `2026-07-24T04:31:04+00:00`).
- A `partial` collection marker is required per guest/platform; one absent guest in one collection
  must never be classified `offline`/`disappeared` (plan §5, Step 11.4).
- Finding codes for missing/malformed/duplicate data are deferred to Step 9's vocabulary table.

## Gate evaluation

Every field above has a named source path, type/unit, identity classification, and a named
consumer (matching, drift, or display) drawn directly from live evidence in reports 1.2/1.3, not
guessed. Step 5 gate passed.

## Discrepancies

None. This step only froze contract text; no code or live state changed.
