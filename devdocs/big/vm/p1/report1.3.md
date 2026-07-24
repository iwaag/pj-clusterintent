# Step 3 — Live Nautobot schema and object baseline

Status: complete.

All requests were GET/OPTIONS only against `http://localhost:8000`. The token was read from
`.local/secrets` into a shell variable and never appeared in a saved argv, report, or log.

## 1. Device baseline

- `dcim.devices?name__ie=aghub` → 1 result. `id fcebe565-6aeb-40b1-ba51-4bde1e1065bc`.
- `dcim.devices?name__ie=agdnsmasq` → 1 result. `id 36178882-1229-4aa1-9e50-faa7cb41188d`.
- Both have the same `status`/`role` FK objects; both have the full 36-key custom-field set from
  Step 1 item 5. **No `proxmox_*` custom field exists on either Device** — confirmed by the
  content-type-scoped custom-field list below.

## 2. Custom-field inventory (`/api/extras/custom-fields/`)

- 36 custom fields exist cluster-wide today; **all 36 are scoped to `content_types:
  ["dcim.device"]` only**. Zero custom fields are scoped to `virtualization.cluster` or
  `virtualization.virtualmachine`. No `proxmox_*`-named field exists anywhere. Phase 2/3 creates
  this allowlist from scratch — there is no legacy field to reuse or collide with.

## 3. Cluster / VirtualMachine / VMInterface objects

- `/api/virtualization/clusters/` → **count 0**.
- `/api/virtualization/virtual-machines/` → **count 0**.
- `/api/virtualization/interfaces/` → **count 0**.
- `/api/virtualization/cluster-types/` → **count 0** — no `ClusterType` (e.g. "Proxmox VE") exists
  yet either; Phase 2 must create one before any Cluster can be upserted.
- Confirms roadmap's "current gap": `agdnsmasq` today has **only** its Device-level identity
  materialized; the VM-level compute layer has zero live rows to conflict with or migrate from.

## 4. REST OPTIONS — native field shape

- `VirtualMachine` POST fields (native, no custom fields applied yet): `name`, `vcpus`, `memory`,
  `disk`, `cluster`, `tenant`, `platform`, `status`, `role`, `primary_ip4`, `primary_ip6`,
  `software_version`, `software_image_files`, `comments`, plus config-context fields. **No native
  VMID field** — VMID must be a dedicated custom field per plan §Ownership.
- `Cluster` POST fields (native): `name`, `cluster_type`, `cluster_group`, `tenant`, `location`,
  `comments`. `cluster_type` is a required FK to `ClusterType`, currently zero rows (item 3).
- `OPTIONS`/`Allow` prove method availability only, not field/object write permission for the
  live token; that proof remains at the Phase 3/4 approved-write-and-refetch gate per plan §Step3.

## 5. `DesiredNode` live rows (5 total, via `/api/plugins/intent-catalog/nodes/`)

| slug | realized_device | realized_device_source | realized_vm | realized_vm_source |
|---|---|---|---|---|
| agbach | set | override | null | null |
| **agdnsmasq** | set (`36178882-...`) | override | **null** | **null** |
| aghub | set (`fcebe565-...`) | derived | null | null |
| agpc | set | override | null | null |
| agstudio | set | override | null | null |

Every live row currently has `realized_vm: null` — **zero non-null legacy rows exist**, so plan
§5.5's data-transition Steps 3/4 (migrating actual non-null links) have nothing to migrate today;
Steps 1, 2, 5, 6 remain mandatory regardless, per the plan's explicit instruction.

## 6. `DesiredEndpoint` live rows (5 total, via `/api/plugins/intent-catalog/endpoints/`)

- Exactly one `primary` endpoint per node exists for all 5 nodes, including `agdnsmasq`
  (`27818c12-fe15-4c9f-83d0-7949523f6c33`): `ip_address 192.168.0.2`, `mdns_name
  agdnsmasq.local`, `dns_name agdnsmasq.home.arpa`, `realized_ip_address` set. This IP/mDNS name
  matches the live NIC evidence from Step 2 (`192.168.0.2/24` on `net0`).
- Full field list for this serializer: `created, custom_fields, description, desired_node,
  display, dns_name, dns_name_source, dnsmasq_record_type, endpoint_type, generate_dnsmasq, id,
  ip_address, ip_policy, last_updated, mdns_name, mdns_name_source, name, natural_slug,
  notes_url, object_type, port, protocol, realized_ip_address, realized_ip_address_source, url,
  vpn_dns_name`. **`mac_address` is absent** — confirms Step 1 model-source finding against the
  live serializer, not just the model file.

## 7. GraphQL/enum shape

Deferred to Step 1's static citations (`nctl/src/nctl_core/sources/desired.py:48-49`,
`sources/actual.py:46`) plus this step's live REST confirmation that the same field names exist
server-side. No separate live GraphQL probe was needed since the REST responses already exhibit
identical field names/shapes and the existing nctl client (audited in Step 1) already consumes
this GraphQL surface correctly against this same live instance (Step 0's `nctl drift`/`render`
runs succeeded against it).

## 8. Duplicate/stale-row check

No duplicate device names, no orphan VM/interface/IP rows (there are zero VM/interface rows to be
orphaned). No stale-row cleanup is required before Phase 2.

## Gate evaluation

Live Device, DesiredNode, DesiredEndpoint, custom-field, Cluster, VirtualMachine, and ClusterType
shapes are all recorded with exact counts and IDs. No POST/PATCH/PUT/DELETE was sent; no Job was
run. Step 3 gate passed.

## Discrepancies

None. All plan-baseline claims about the current absence of Cluster/VM/VMInterface materialization
and the absence of `DesiredEndpoint.mac_address` are reproduced by live evidence, not just static
audit.
