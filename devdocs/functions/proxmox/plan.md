# Proxmox Nautobot Self-Registration Plan

## Goal

Extend `nodeutils/nautobot_self_register.py` so a Proxmox VE host can self-register not only as a Nautobot Device, but also register the Proxmox cluster and discovered QEMU/LXC guests into Nautobot's virtualization inventory.

The Proxmox-specific logic should live in a separate module so the existing generic host registration remains maintainable.

## Design Summary

Keep `nautobot_self_register.py` responsible for generic host inventory and Device upsert.

Add a Proxmox-specific module, tentatively:

```text
nodeutils/proxmox_inventory.py
```

Responsibilities:

- Detect whether the current Linux host is a Proxmox VE node.
- Collect Proxmox cluster, node, QEMU VM, LXC container, storage, and network facts.
- Normalize Proxmox facts into a stable internal inventory shape.
- Register or update Nautobot virtualization objects.
- Avoid destructive deletes; mark missing guests inactive/offline in later phases.

`nautobot_self_register.py` should only:

- call Proxmox detection after generic Linux inventory collection;
- adjust default role/device type for Proxmox hosts when no local override is set;
- invoke the Proxmox registration flow after the physical host Device is upserted;
- expose CLI flags for dry-run and optional Proxmox behavior.

## Nautobot Object Mapping

### Physical Proxmox Node

Register the host as a normal Nautobot `dcim.Device`.

Recommended defaults when Proxmox is detected:

- role: `proxmox-host`
- device_type: `Proxmox Host`
- tags: existing tags plus `proxmox`
- custom fields:
  - `proxmox_node_name`
  - `proxmox_version`
  - `proxmox_cluster_name`
  - `proxmox_cluster_id`

The existing self-registration fields such as CPU, memory, disk, GPU, OS, Docker, and systemd inventory should continue to work.

### Proxmox Cluster

Register the Proxmox cluster as Nautobot `virtualization.Cluster`.

Recommended fields:

- name: Proxmox cluster name, or a stable fallback for standalone nodes
- type: `Proxmox VE`
- status: `Active`
- custom fields:
  - `proxmox_cluster_id`
  - `proxmox_quorate`
  - `proxmox_node_count`

For a standalone Proxmox node, create a single-node cluster representation. This keeps VM/LXC registration consistent because Nautobot VMs attach naturally to a Cluster.

### QEMU VM

Register as Nautobot `virtualization.VirtualMachine`.

Recommended fields:

- name: Proxmox guest name when available, else `vm-<vmid>`
- cluster: matching Proxmox cluster
- status: mapped from Proxmox state
- vcpus: VM CPU count
- memory: VM memory in MB
- disk: total disk in GB or MB depending Nautobot field expectations
- role: `virtual-machine`
- custom fields:
  - `proxmox_guest_type`: `qemu`
  - `proxmox_vmid`
  - `proxmox_node`
  - `proxmox_status`
  - `proxmox_template`
  - `proxmox_tags`

### LXC Container

Register as Nautobot `virtualization.VirtualMachine`, because Nautobot has no dedicated LXC container model.

Use fields and custom fields to distinguish it from QEMU VMs:

- role: `lxc-container`
- custom fields:
  - `proxmox_guest_type`: `lxc`
  - `proxmox_vmid`
  - `proxmox_node`
  - `proxmox_status`
  - `proxmox_template`
  - `proxmox_unprivileged`
  - `proxmox_tags`

### Guest Interfaces And IPs

Register guest NICs as `virtualization.VMInterface` when reliable data is available.

Register IPs as `ipam.IPAddress` and assign them to VM interfaces when:

- the Proxmox agent reports IPs for QEMU guests; or
- LXC config contains static IPs; or
- guest config exposes an address confidently.

Avoid guessing IPs from names, ARP, or incomplete network strings in the first implementation.

## Data Collection Strategy

Prefer Proxmox local commands on the Proxmox host for phase 1. They avoid introducing API token management and are easy to validate manually.

Detection commands and files:

- `/etc/pve`
- `/etc/os-release`
- `pveversion`
- `pvesh`

Useful collection commands:

```bash
pveversion --verbose
pvesh get /cluster/status --output-format json
pvesh get /cluster/resources --output-format json
pvesh get /nodes --output-format json
pvesh get /nodes/<node>/qemu --output-format json
pvesh get /nodes/<node>/lxc --output-format json
pvesh get /nodes/<node>/storage --output-format json
pvesh get /nodes/<node>/network --output-format json
pvesh get /nodes/<node>/qemu/<vmid>/config --output-format json
pvesh get /nodes/<node>/lxc/<vmid>/config --output-format json
```

Optional later data:

- QEMU guest agent network IPs:
  - `pvesh get /nodes/<node>/qemu/<vmid>/agent/network-get-interfaces --output-format json`
- HA resources:
  - `pvesh get /cluster/ha/resources --output-format json`
- Replication:
  - `pvesh get /nodes/<node>/replication --output-format json`

## Module Shape

Suggested public functions:

```python
def is_proxmox_host() -> bool:
    ...

def collect_proxmox_inventory(config: dict[str, Any], host_inventory: dict[str, Any]) -> dict[str, Any]:
    ...

def upsert_proxmox_inventory(
    config: dict[str, Any],
    client: NautobotClient,
    host_inventory: dict[str, Any],
    host_device: dict[str, Any],
    proxmox_inventory: dict[str, Any],
) -> dict[str, Any]:
    ...
```

Suggested internal helpers:

```python
def run_pvesh(path: str) -> Any:
    ...

def get_cluster_status() -> dict[str, Any]:
    ...

def get_cluster_resources() -> list[dict[str, Any]]:
    ...

def get_node_guests(node: str) -> list[dict[str, Any]]:
    ...

def normalize_qemu_vm(raw: dict[str, Any], node: str) -> dict[str, Any]:
    ...

def normalize_lxc_container(raw: dict[str, Any], node: str) -> dict[str, Any]:
    ...
```

Keep Nautobot API helpers either reusable from `nautobot_self_register.py` or moved into a shared module later, for example:

```text
nodeutils/nautobot_client.py
```

Do not do that extraction in the first pass unless the import cycle becomes awkward.

## CLI Behavior

Add flags to `nautobot_self_register.py`:

```text
--proxmox auto|enabled|disabled
--proxmox-json
```

Defaults:

- `auto`: run Proxmox collection only when Proxmox is detected.
- `enabled`: fail if Proxmox collection cannot run.
- `disabled`: skip all Proxmox-specific collection and writes.

Existing behavior:

- `--json` should include a top-level `proxmox` section when detected.
- `--dry-run` should print both the Device payload and the Proxmox virtualization payload plan.
- Normal execution should upsert the Device first, then the Proxmox cluster and guests.

## Configuration

Extend `self_inventory.yaml` with optional Proxmox settings:

```yaml
proxmox:
  enabled: auto
  cluster_type: "Proxmox VE"
  cluster_status: "Active"
  host_role: "proxmox-host"
  host_device_type: "Proxmox Host"
  qemu_role: "virtual-machine"
  lxc_role: "lxc-container"
  guest_status_map:
    running: "Active"
    stopped: "Offline"
    paused: "Offline"
  include_guest_interfaces: true
  include_guest_ips: true
```

Allow normal top-level overrides to keep working:

- `role`
- `device_type`
- `tags`
- `custom_fields`

Local overrides should win over Proxmox defaults.

## Required Nautobot Seed Data

Before writes can succeed, Nautobot needs these objects.

Roles:

- `proxmox-host`
- `virtual-machine`
- `lxc-container`

Device type:

- `Proxmox Host`

Manufacturer:

- whatever the physical hardware reports, with fallback to `Generic`

Cluster type:

- `Proxmox VE`

Statuses:

- `Active`
- `Offline`

Tags:

- `self-registered`
- `home`
- `proxmox`

Custom fields:

- `proxmox_cluster_name`
- `proxmox_cluster_id`
- `proxmox_node_name`
- `proxmox_version`
- `proxmox_guest_type`
- `proxmox_vmid`
- `proxmox_node`
- `proxmox_status`
- `proxmox_template`
- `proxmox_tags`
- `proxmox_unprivileged`

Seed these in the Nautobot-side Job or a dedicated migration/seed file before enabling writes.

## Implementation Phases

### Phase 1: Read-Only Proxmox Detection And Inventory

- Add `nodeutils/proxmox_inventory.py`.
- Implement `is_proxmox_host()`.
- Implement local command wrapper for `pveversion` and `pvesh`.
- Collect cluster status, resources, nodes, QEMU guests, and LXC guests.
- Normalize inventory into JSON-safe dicts.
- Add `--proxmox-json` and include Proxmox data in `--json`.
- No Nautobot writes in this phase.

Acceptance:

- Running on a non-Proxmox Linux host does not fail.
- Running on a Proxmox host emits cluster, node, QEMU, and LXC facts.
- Missing optional commands or permission issues produce clear errors in `enabled` mode and non-fatal skip in `auto` mode.

### Phase 2: Proxmox Host Defaults

- When Proxmox is detected and no local override exists, set:
  - role: `proxmox-host`
  - device_type: `Proxmox Host`
  - tag: `proxmox`
- Add Proxmox host facts to Device custom fields.
- Keep normal Device upsert unchanged otherwise.

Acceptance:

- Proxmox host still registers as a `dcim.Device`.
- Existing user overrides continue to win.
- Dry-run clearly shows Proxmox-specific Device payload fields.

### Phase 3: Cluster And Guest Upsert

- Add Nautobot upsert for `virtualization.Cluster`.
- Add Nautobot upsert for QEMU VMs.
- Add Nautobot upsert for LXC containers as `VirtualMachine`.
- Match existing VMs by custom field `proxmox_vmid` plus cluster or by name fallback.
- Do not delete missing VMs.

Acceptance:

- Repeated runs are idempotent.
- QEMU and LXC guests appear under the Proxmox cluster.
- Guest type and VMID are preserved as custom fields.

### Phase 4: Interfaces And IP Addresses

- Parse QEMU/LXC network config into VM interfaces.
- Use QEMU guest agent for IP discovery when available.
- Assign discovered IPs to VM interfaces only when confidence is high.
- Avoid overwriting manually curated IP assignments unless the record is self-managed.

Acceptance:

- VM interfaces are stable across repeated runs.
- IPs discovered from guest agent or static LXC config are assigned.
- Dynamic or ambiguous data is skipped rather than guessed.

### Phase 5: Lifecycle And Drift Handling

- Track last-seen timestamps for clusters and guests.
- Mark previously self-registered but now-missing guests as `Offline` after a configurable grace period.
- Add dry-run reporting for create/update/offline actions.
- Consider optional prune behavior only after the inactive flow is proven.

Acceptance:

- Removed Proxmox guests do not disappear unexpectedly from Nautobot.
- Operators can see stale records and choose cleanup policy.

## Testing Plan

Unit tests:

- Proxmox detection from mocked files/commands.
- `pvesh` JSON parsing.
- QEMU normalization.
- LXC normalization.
- Status mapping.
- Dry-run payload building.

Integration-style tests with fixtures:

- sample `/cluster/status`
- sample `/cluster/resources`
- sample `/nodes/<node>/qemu`
- sample `/nodes/<node>/lxc`
- sample QEMU config
- sample LXC config
- sample guest agent interfaces

Manual validation on Proxmox:

```bash
uv run --env-file .env nautobot-self-register --json
uv run --env-file .env nautobot-self-register --proxmox-json
uv run --env-file .env nautobot-self-register --dry-run
uv run --env-file .env nautobot-self-register --verbose
```

## Risks And Decisions

### LXC Representation

Decision: represent LXC containers as Nautobot `VirtualMachine` records with `proxmox_guest_type=lxc`.

Reason: Nautobot does not have a first-class LXC model, and this keeps scheduling and inventory queries simple.

### Source Of Truth

Decision: Proxmox is the source of truth for VM/LXC existence and basic runtime attributes. Nautobot remains the source of truth for higher-level service placement metadata.

Reason: Proxmox has the runtime state; Nautobot has the inventory, relationship, and automation context.

### Deletes

Decision: do not delete Nautobot records in early phases.

Reason: accidental deletion of curated metadata is more damaging than stale records. Use status changes first.

### API Versus Local Commands

Decision: start with local `pvesh` commands.

Reason: the script is intended to run on the host itself, and local commands avoid a second credential system. A Proxmox API client can be added later for remote collection.

## Open Questions

- Should a standalone Proxmox host always create a synthetic single-node cluster, or should this be configurable?
- Should VM/LXC names be globally unique, or should display names include the VMID to avoid collisions?
- Which Nautobot custom fields already exist in the current seed job, and which need to be added?
- Should storage pools be represented only as custom fields first, or modeled more explicitly later?
- Should bridge/network information become Nautobot interfaces/IPAM prefixes, or remain raw Proxmox metadata in phase 1?

