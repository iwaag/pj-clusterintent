# Phase 2 Step 8 Report: Coordinated Deployment and Fresh Read-Only Collection

Status: implemented and live-deployed. All Step 8 gate items are positively exercised.

This report covers [`plan.md`](plan.md) Step 8 ("Coordinated deployment and fresh read-only
collection"). Unlike Steps 1-7, this step performs live, hard-to-reverse actions against the real
local Nautobot instance and the real `aghub` host, so it proceeded only after explicit user
approval at each gate named in Section 3.3 of the plan. Raw execution evidence (job IDs, digests,
refetched object lists) is stored under `.local/vm-p2/20260724-step8/`, mode `0700`/`0600`.

## 1. Submodule commit review (plan Step 8.1-8.2)

All four participating submodules were already committed in reviewable per-step units (Steps
1-7, `report2.1.md`-`report2.7.md`) and already pushed to `origin/main` before this step started —
`git status -sb` / `git log @{u}..` showed a clean working tree and zero unpushed commits for
`ansible_agdev`, `nauto`, `nctl`, and `nodeutils`. No additional commit or push was needed; the user
was informed of this rather than asked to push again.

## 2. Nautobot Git Repository sync (plan Step 8.3)

`POST /api/extras/git-repositories/<id>/sync/` was issued against the `main` Git Repository
(`https://github.com/iwaag/nauto`). `current_head` moved from the pre-Phase-2 pin `617036d3` to
`4cea3b68b1bc766aedf75d8ea166b0e68d735bc2`, matching local `nauto` HEAD exactly. Both
`Seed Home Cluster` and `Ingest Nodeutils Inventory` Jobs show `installed: true, enabled: true` at
the new revision. No old-report ingestion was running concurrently in this single-operator dev
environment, so the "pause old Proxmox ingest" clause had nothing to pause.

## 3. Prerequisite seed: dry-run, approval, apply (plan Step 8.4-8.5)

`Seed Home Cluster` was run with `dry_run=true` first (job result `6d14ca61-2b21-4673-ad22-
44543c61a16a`, SUCCESS). The diff contained only the expected new objects:

- `Would create cluster type Proxmox VE`
- `Would create role virtual-machine`
- `Would create role lxc-container`
- `Would create custom field proxmox_*` (21 fields: `proxmox_observer_device_id`,
  `proxmox_identity_source`, `proxmox_scope_key`, `proxmox_observed_at`,
  `proxmox_observation_state`, `proxmox_observation_detail`, `proxmox_observed_node_names`,
  `proxmox_node_count`, `proxmox_storage_content`, `proxmox_guest_type`, `proxmox_vmid`,
  `proxmox_node`, `proxmox_status`, `proxmox_lxc_rootfs`, `proxmox_interface_evidence`,
  `proxmox_config_slot`, `proxmox_guest_interface_name`, `proxmox_bridge`,
  `proxmox_interface_source`, `proxmox_presence`, `proxmox_managed_ip_evidence`)
- `Would create status Unknown` and content-type extensions for `Active`/`Offline` to cover
  `virtualization.virtualmachine`/`vminterface`/`ipam.ipaddress`
- pre-existing unrelated `IntentSource`/`DesiredService` seed rows (unchanged Phase-1 baseline
  content, not part of this phase's scope)

No unexpected create/update appeared. This diff was shown to the user, who explicitly approved
applying it (`AskUserQuestion` — "Apply now"). `Seed Home Cluster` was then run with
`dry_run=false, update_existing=true` (job result `760d3357-8b5b-44b3-b470-bb668c314faf`,
SUCCESS).

Refetch confirmed every prerequisite object exists exactly as planned:

| Object | Refetched state |
|---|---|
| ClusterType | `Proxmox VE` |
| Roles | `virtual-machine`, `lxc-container` |
| Custom fields | all 21 `proxmox_*` keys present |
| Status `Active` content types | `dcim.device`, `dcim.location`, `ipam.ipaddress`, `virtualization.virtualmachine`, `virtualization.vminterface` |
| Status `Offline`/`Unknown` content types | `virtualization.virtualmachine` |

## 4. Superproject pins (plan Step 8.6)

`nodeutils` and `ansible_agdev` were unchanged by Steps 4-7 (only `nauto`/`nctl` changed since
Step 3). The superproject's tracked submodule pins (`339d361b...` for `ansible_agdev`,
`3a0fdf98...` for `nodeutils`) already matched both repositories' local HEAD and `origin/main`
exactly (`git submodule status` clean, no pin update required).

## 5. Deploy to `aghub` (plan Step 8.7)

Connectivity check: `ping aghub.local` and an SSH probe both succeeded before running anything.
`ansible-playbook -i inventories/generated/hosts_intent.yml
playbooks/nautobot/run_nodeutils_collect.yml --limit aghub` ran the supported non-root path
(clone/update `/opt/nodeutils` at `nodeutils_version: HEAD`, `uv sync --frozen`, run
`nodeutils collect`), with the `nodeutils_pvesh_helper` role applied beforehand. Result:
`ok=33 changed=4 unreachable=0 failed=0`, all built-in ownership/mode assertions ("must remain
owned by eiji", "must exist and be owned by eiji", "must be mode 0600") passed.

Post-deploy verification on `aghub`:

- `/opt/nodeutils` HEAD = `3a0fdf9817d970935847aafd46c35bf07133c20c`, tree clean — exactly the
  pinned commit.
- Helper digest = `699793c050a18ac06cc0114d230657bb2f34a20c167158af8f517a2fbf93ddf0` (changed from
  the Step 0 baseline digest, consistent with the Step 2 storage-content helper change).

## 6. Fresh collection (plan Step 8.8-8.9)

First fresh collection (`collected_at 2026-07-24T15:07:54+00:00`):

- top-level `schema_version = nodeutils.inventory.v2`; nested `facts.proxmox.schema_version =
  nodeutils.proxmox.v1` — the old unversioned nested shape is gone.
- `cluster = {name: aghub-proxmox, name_source: standalone_node_fallback, identity_value: aghub,
  node_count: 1}` — matches the Step 0 classification exactly.
- `agdnsmasq` present in `lxc_containers`: `vmid=108, node=aghub, proxmox_status=running,
  rootfs={storage: local-lvm, volume: vm-108-disk-0, size_gb: 8.0}`, `observation.state=complete`
  across `identity`/`config`/`rootfs` sections, one joined interface
  (`net0`, MAC `bc:24:11:23:dc:b7`, bridge `vmbr0`, IP `192.168.0.2/24`).
- `storage_content`: one scope (`aghub`/`local`/`vztmpl`), `state=complete`, containing exactly
  two `vztmpl` items (`ubuntu-22.04-standard_22.04-1_amd64.tar.zst`,
  `ubuntu-24.04-standard_24.04-2_amd64.tar.zst`), no other fields beyond the Section 5.2 allowlist.

This satisfies the plan's positive assertions: v1 nested schema, non-empty collection, and
`agdnsmasq` vmid 108 positively matched.

## 7. Phase 5 candidate `volid` (plan Step 8.10)

Per Section 5.7, selecting the candidate is an operator decision, made only after the new read
path exposed the exact inventory (the two `vztmpl` items above). The user was asked to choose
between the two exposed templates and selected:

```text
local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst
```

A second fresh collection was then run (`collected_at 2026-07-24T15:09:44+00:00`). The
`storage_content` scope was again `state=complete`, and the exact same `volid` string
(`local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst`) was present, alongside the other
template. No template was downloaded or guessed; this is acceptance evidence only, per Section 3.2
and Section 5.7's explicit non-goal.

## 8. No Proxmox mutation check (plan Step 8.11)

The helper remains a fixed `pvesh get` proxy (unchanged boundary from Steps 1-2); nothing in this
step's Ansible run or API calls touched a write path. Guest-list diff across both fresh
collections, and against the Step 0 baseline (`report2.0.md`/`manifest.txt`):

| | qemu | lxc |
|---|---|---|
| Step 0 baseline | `infra(100)`, `aghaos(102, running)`, `agk3s(105, running)` | `agansible(101)`, `agprome(103)`, `aggrafana(104)`, `agnomad(106)`, `agkeadhcp(107)`, `agdnsmasq(108, running)` |
| Step 8 (both collections) | `infra(100, stopped)`, `aghaos(102, running)`, `agk3s(105, running)` | `agansible(101, running)`, `agprome(103, stopped)`, `aggrafana(104, stopped)`, `agnomad(106, stopped)`, `agkeadhcp(107, stopped)`, `agdnsmasq(108, running)` |

Identical guest set (same 9 VMIDs, same names, same kinds); running/stopped power values are
ordinary Proxmox-observed facts, not something this step (or nauto's read-only ingest, which was
not run against this fresh report in Step 8) changed. No guest was created, started, stopped,
resized, moved, or deleted, and no Nautobot Cluster/VM ingest ran yet — that is Step 9's job. The
seed apply in Section 3 above touched only prerequisite ClusterType/Role/Status/CustomField
objects, never a Device, VM, or unrelated ledger row.

## Gate

- fresh, non-empty `nodeutils.proxmox.v1` collection: proven (two runs);
- prerequisite Nautobot objects match the plan exactly, applied only after separate dry-run
  review and explicit user approval: proven;
- Cluster identity source (`standalone_node_fallback`, scope key derivable from the `aghub`
  Device UUID) proven directly from the fresh report's `cluster` block;
- the same exact operator-recorded candidate `volid` appears in a second complete fresh
  storage-content observation: proven;
- no Proxmox guest/resource state changed relative to the Step 0 baseline: proven.

Step 8 is fully satisfied. Proceeding to Step 9 (first live ingest, refetch, and repeat-ingest
proof) remains gated behind its own separate before-image/dry-run/apply approval, per Section 3.3
item 3.
