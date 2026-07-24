# Step 1 — Current data-flow and ownership audit

Status: complete.

Pure read audit; no code, ledger, or live state was changed. Line references are against the
submodule HEADs pinned in `report1.0.md`.

## 1. nodeutils collection entry point

- `nodeutils/nodeutils_collect.py:40` — top-level schema constant `nodeutils.inventory.v2`.
- `nodeutils/nodeutils_collect.py:1333` — `proxmox_data = proxmox_inventory.collect_proxmox_inventory(...)`.
- `nodeutils/nodeutils_collect.py:1334-1335` — `if proxmox_data.get("enabled") or proxmox_data.get("detected"): inventory["proxmox"] = proxmox_data`.
- `nodeutils/nodeutils_collect.py:1237` — `"proxmox": inventory.get("proxmox")` is where `facts.proxmox` is exposed in the final `facts` dict.

## 2. `nodeutils/proxmox_inventory.py`

- pvesh paths read: `/cluster/status` (L384), `/cluster/resources` (L385), `/nodes` (L386),
  `/nodes/{node}/qemu` (L400), `/nodes/{node}/lxc` (L402), `/nodes/{node}/qemu/{vmid}/config`
  (L283), `/nodes/{node}/lxc/{vmid}/config` (L324), `/nodes/{node}/storage` (L405),
  `/nodes/{node}/network` (L411), `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces`
  (L245, guest-agent).
- `normalize_qemu_vm()` L274-311. **Confirmed** plan §4.1 claim: L289 sets
  `interfaces = config_interfaces(...)`; L291-293 `if agent_interfaces: interfaces =
  agent_interfaces` — guest-agent interfaces **replace** rather than merge with configured
  interfaces, losing bridge/NIC-slot evidence whenever agent data exists.
- `disk_gb`: QEMU L307 and LXC L342 both use
  `bytes_to_gb(first_nonempty(raw.get("maxdisk"), raw.get("disk")))` — **confirmed** aggregate
  `maxdisk`/`disk`, not parsed rootfs/root-disk config.

## 3. Privileged helper (recheck)

- `ansible_agdev/roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read:12-30` — allowlist has no
  `/nodes/{node}/storage/{storage}/content` pattern. Consistent with Step 0's live digest match.

## 4. `ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml`

**Confirmed not safe for Phase 1 live observation.** It clones/force-updates the nodeutils
checkout via the `git` module, runs `uv sync --frozen`, applies the `nodeutils_pvesh_helper` role
(package/helper install), executes `nodeutils collect`, and writes a remote report to
`/var/lib/nodeutils/inventory.json`, followed by `stat`/`assert` checks on that written file. This
playbook deploys and mutates; Phase 1 Step 2 must not invoke it.

## 5. `nauto/jobs/ingest_nodeutils_inventory.py`

- Upserts only `dcim.Device` objects: `match_device()` (L254, matches by `serial`/`name`),
  `create_device()` (L500), `update_device()` (L512).
- Full custom-field allowlist (L379-428): `last_seen`, `host_system`, `os_name`, `os_version`,
  `kernel_version`, `architecture`, `cpu_model`, `cpu_cores`, `memory_gb`, `gpu_count`,
  `gpu_models`, `gpu_memory_gb`, `gpu_accelerator_summary`, `disk_total_gb`, `serial_number`,
  `primary_mac_address`, `primary_ip_address`, `network_interface`, `inventory_source`,
  `ai_resource_summary`, `observed_services`, `docker_engine_state`,
  `docker_container_running_count`, `docker_container_total_count`, `docker_compose_projects`,
  `docker_published_ports`, `docker_service_summary`, `service_inventory_updated_at`,
  `inventory_raw_json`, plus conditional `owner`/`purpose`.
- `inventory_raw_json` (L413-423) whitelists only `identity` and
  `facts.{hardware,gpu,disk,network,software,services}` — **`facts.proxmox` is not a candidate
  key and is silently dropped**, not merely unconsumed.
- **Confirmed**: no Cluster/VirtualMachine/VMInterface object is created by normal ingest today.

## 6. Historical self-registration path

- `git -C nodeutils log --all --oneline -- nodeutils/nautobot_self_register.py` returns nothing
  under that literal path across all history (path search found no match); however commit
  `9ab3abd` ("add proxmox register", 2026-06-21) does exist and touches
  `nautobot_self_register.py`, `proxmox_inventory.py`, `example.self_inventory.yaml`,
  `tests/test_proxmox_inventory.py`.
- `git -C nodeutils ls-tree -r HEAD --name-only | grep -i "regist\|nautobot"` returns **no
  output** — **confirmed**: no self-registration/nautobot-named file exists at current HEAD
  (`36e1c575...`). The old writer is history-only.

## 7. `nintent/nautobot_intent_catalog/models.py`

- `DesiredNode` (L253): `realized_device` FK (L319) + `realized_device_source` (L326,
  `derived|override`); `realized_vm` FK (L333) + `realized_vm_source` (L340, same choices).
  `clean()` (L412-421) enforces relation/source presence together (XNOR).
- `DesiredEndpoint` (L425): owns `ip_address`, `ip_policy`, `dns_name`/`_source`,
  `mdns_name`/`_source`, `realized_ip_address` FK (actual IP link). **No `mac_address` field
  exists** on this model today — confirmed absent.
- `@extras_features("graphql")` decorates every catalog model (L33, 79, 195, 252, 424, 554, 667,
  789, 847, 884).
- YAML loader `nintent/nautobot_intent_catalog/loaders.py`: `load_intent_sources()` (L197),
  `yaml.safe_load()` (L215), section roots read via `_list_section(data, "desired_nodes")`
  (L259) and `_list_section(data, "desired_endpoints")` (L275). **Confirmed**: only these two
  roots exist; no compute-platform/instance root.

## 8. UI/API surface (location index only, per plan scope)

`nintent/nautobot_intent_catalog/{forms.py,tables.py,filters.py,views.py,api/serializers.py,
api/views.py}`.

## 9. `nctl/src/nctl_core/sources/desired.py`

- GraphQL fragment (L48-49): `realized_vm { id }`, `realized_vm_source`.
- Row parsing (L268, L280-281): `realized_vm = row.get("realized_vm")`;
  `realized_vm_id=realized_vm["id"] if realized_vm else None`;
  `realized_vm_source=_lower(row.get("realized_vm_source"))`. Confirmed direct
  `DesiredNode.realized_vm` consumption.

## 10. `nctl/src/nctl_core/sources/actual.py`

- GraphQL query reads `virtual_machines { id name }` (L46).
- `fetch_actual_snapshot()` (L225-231): `ActualVirtualMachine(id=row["id"], name=row["name"])` —
  **confirmed** only `id`/`name`, no Cluster/VMID/power/capacity/interface fields.
- Device custom-field allowlist mirrors ingest's write-side list (L1-17 comment; same 8
  Nautobot-native `cf_*` GraphQL shortcuts: `primary_mac_address`, `primary_ip_address`,
  `last_seen`, `inventory_source`, etc.).

## 11. Production/drift/dnsmasq consumers

- `unsupported_actual_type` literal: produced by `actual_type_problem()` in
  `nctl/src/nctl_core/sources/actual.py:154-165`; consumed in
  `nctl/src/nctl_core/production/composer.py:121` (`PRODUCTION_BLOCKING_NODE_CODES`),
  `nctl/src/nctl_core/reconcile/classify.py:108`, and `nctl/src/nctl_core/drift/status.py:42`.
- `select_mdns_endpoint()` — `nctl/src/nctl_core/hosts_intent.py:224-238`. **Confirmed** sorted-
  first fallback: tries `endpoint_type in ("primary","management")` first
  (`sorted(matching, key=_endpoint_sort_key)[0]`, L232-236), else falls back to
  `sorted(candidates, key=_endpoint_sort_key)[0]` over any mdns-named candidate regardless of type
  (L238). Compute NIC selection must not reuse this.
- DHCP reservation/MAC dependency: `nctl/src/nctl_core/dnsmasq.py`, `resolve_dhcp_reservation()`
  L142-189 — reads `endpoint_observed["dhcp_mac_candidates"]` (L155-158), normalizes via
  `_normalize_mac()` (L170-174), renders `dhcp-host=...` only with exactly one normalized
  candidate and no `missing_mac_address`/`invalid_mac_address`/`ambiguous_interface` skip reason
  (L179-189).

## 12. `nctl ssh enroll` and the stable DesiredNode UUID alias

- `nctl/src/nctl_core/ssh_trust.py` — `derive_host_key_alias(node_id)` (L37+) derives
  `HostKeyAlias` purely from the DesiredNode UUID (`uuid.UUID(node_id)` validated at L34),
  intentionally hardware-independent (documented L40-43).
- `nctl/src/nctl_core/ssh_enroll.py` — `SshEnrollData` (L53), `scan_offered_keys()` (L146),
  `find_legacy_trusted_keys()` (L170), `select_verified_offered_keys()` (L217),
  `ManagedSshStore`/`ManagedEntry` (L271+).
- `nctl/src/nctl_core/inventory_trust.py` — re-derives expected trust vars per host from
  `nintent_desired_node_id` and cross-checks against `derive_host_key_alias` (L27-30 imports),
  used by the `apply dnsmasq` preflight.
- Wired into `nctl/src/nctl_core/cli/main.py` and `reconcile/ssh_preflight.py`/
  `reconcile/executor.py`. **Confirmed**: both the command and the UUID-alias trust store already
  exist; Phase 5 reuses rather than reinvents this.

## Ownership conclusion

Normal nauto ingest is the sole live write owner of the Device ledger today, and drops
`facts.proxmox` entirely — it neither writes it into `inventory_raw_json` nor materializes it into
Cluster/VirtualMachine/VMInterface objects. The historical self-registration/Proxmox-upsert path
(commit `9ab3abd` lineage) does not exist at current HEAD on any submodule branch. Per plan §5.1,
**normal nauto ingest is confirmed and declared the sole owner of future Cluster/VM/VMInterface
ledger writes**; the old path is audited-only, not restored.

## Discrepancies

None. All plan §4 baseline claims audited in this step were reproduced exactly against current
submodule HEADs.
