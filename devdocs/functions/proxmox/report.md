# Proxmox Nautobot Self-Registration Implementation Report

## Summary

Started the Proxmox implementation from `.local/proxmox/plan.md`.

Implemented the first working slice:

- Proxmox-specific logic is now separated into `nodeutils/proxmox_inventory.py`.
- `nautobot-self-register` now supports Proxmox modes:
  - `--proxmox auto`
  - `--proxmox enabled`
  - `--proxmox disabled`
- `--proxmox-json` prints only the Proxmox inventory result.
- Proxmox hosts can have host Device defaults applied automatically:
  - role: `proxmox-host`
  - device type: `Proxmox Host`
  - tag: `proxmox`
  - Proxmox custom fields merged into the Device payload
- Proxmox cluster/QEMU/LXC collection is implemented through local `pvesh`.
- Nautobot write support for Proxmox cluster and guests has been added as a first pass.
- LXC containers are represented as Nautobot `VirtualMachine` records with `proxmox_guest_type=lxc`.
- Documentation and config examples were updated.
- Unit tests were added for Proxmox mode handling and guest normalization.

## Files Changed

- `nodeutils/proxmox_inventory.py`
  - New Proxmox detection, collection, normalization, dry-run, and Nautobot upsert module.

- `nodeutils/nautobot_self_register.py`
  - Imports Proxmox module.
  - Adds `--proxmox` and `--proxmox-json`.
  - Reuses one Nautobot client for Device and Proxmox writes.
  - Applies Proxmox host defaults when Proxmox inventory is enabled.
  - Includes Proxmox dry-run output under a top-level `proxmox` key.

- `nodeutils/pyproject.toml`
  - Adds `proxmox_inventory` to `py-modules`.

- `nodeutils/example.self_inventory.yaml`
  - Adds commented Proxmox configuration example.

- `nodeutils/README.md`
  - Adds Proxmox behavior, command prerequisites, and usage examples.

- `nodeutils/tests/test_proxmox_inventory.py`
  - Adds unittest coverage for mode validation, non-Proxmox auto skip, QEMU normalization, LXC normalization, and disabled dry-run payloads.

## Implemented Behavior

### Non-Proxmox Hosts

Default `auto` behavior skips Proxmox work when the host does not look like Proxmox VE.

Example observed output:

```json
{
  "detected": false,
  "enabled": false,
  "mode": "auto"
}
```

Existing generic self-registration still works when Proxmox is disabled or skipped.

### Proxmox Detection

Detection checks:

- Linux platform
- `/etc/pve`
- `/etc/os-release` containing Proxmox/PVE hints
- successful `pveversion`

### Proxmox Collection

Collection uses local commands:

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

QEMU guest agent IP/interface collection is attempted when enabled:

```bash
pvesh get /nodes/<node>/qemu/<vmid>/agent/network-get-interfaces --output-format json
```

Failures for guest agent, storage, and network details are non-fatal.

### Nautobot Mapping

Physical host:

- Nautobot `dcim.Device`

Cluster:

- Nautobot `virtualization.Cluster`

QEMU:

- Nautobot `virtualization.VirtualMachine`
- `proxmox_guest_type=qemu`

LXC:

- Nautobot `virtualization.VirtualMachine`
- `proxmox_guest_type=lxc`

## Verification Run

Commands run from `nodeutils/`:

```bash
uv run ruff check .
uv run python -m unittest discover -s tests
python3 -m py_compile nautobot_self_register.py proxmox_inventory.py tests/test_proxmox_inventory.py
uv run nautobot-self-register --proxmox disabled --proxmox-json
uv run nautobot-self-register --proxmox disabled --json
uv run nautobot-self-register --proxmox disabled --dry-run
uv run nautobot-self-register --proxmox-json
```

Results:

- `ruff`: passed
- `unittest`: passed, 5 tests
- `py_compile`: passed
- `--proxmox disabled --proxmox-json`: passed
- `--proxmox disabled --json`: passed
- `--proxmox disabled --dry-run`: passed
- `--proxmox-json` on the current non-Proxmox host: passed with `detected=false`

## Current Limitations

- This has not yet been run on an actual Proxmox host.
- Nautobot write paths for `virtualization.Cluster` and `VirtualMachine` are implemented but not validated against a live Nautobot instance with the required seed data.
- VM interface and IP object upserts are not implemented yet. Interface/IP data is collected and normalized, but not written to Nautobot.
- Missing/deleted Proxmox guests are not marked offline yet.
- Storage and network data are collected into the Proxmox inventory output but are not modeled in Nautobot yet.
- VM matching currently prefers name, then tries common custom-field filter names for `proxmox_vmid`. This may need adjustment against the actual Nautobot version and custom field filter behavior.
- The VM `disk` payload uses normalized GB values. Confirm Nautobot's expected unit in the target deployment before relying on disk writes.

## Required Nautobot Objects Before Live Write

Create or seed these before running write mode on Proxmox:

- Cluster type: `Proxmox VE`
- Roles:
  - `proxmox-host`
  - `virtual-machine`
  - `lxc-container`
- Device type: `Proxmox Host`
- Tags:
  - `self-registered`
  - `home`
  - `proxmox`
- Statuses:
  - `Active`
  - `Offline`
- Custom fields:
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
  - `proxmox_node_count`

## Recommended Next Steps

1. Run on a Proxmox host in read-only mode:

   ```bash
   uv run --env-file .env nautobot-self-register --proxmox-json
   uv run --env-file .env nautobot-self-register --proxmox enabled --dry-run
   ```

2. Compare the emitted payload with the target Nautobot API schema.

3. Add or update Nautobot-side seed data for the required roles, cluster type, tags, statuses, device type, and custom fields.

4. Validate one live write against a test Nautobot instance.

5. Implement VMInterface/IPAddress upsert after live Proxmox output is reviewed.

