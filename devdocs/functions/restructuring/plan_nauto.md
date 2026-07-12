# Nauto Restructuring Plan

## Goal

Add a server-side ingestion path that accepts `nodeutils` inventory reports and writes validated, centrally governed data into Nautobot.

Nautobot API credentials should live only on the Nautobot/server side. Host-side scripts should not need Nautobot write tokens for the normal inventory flow.

## Target Design

`nauto` becomes the trusted writer for host inventory updates:

```text
nodeutils report
  -> central collection path
  -> nauto ingest job
  -> Nautobot Device and custom field updates
```

The ingestor should validate report structure, identify the host, apply central policy, then create or update Nautobot objects.

## Recommended First Implementation

Implement ingestion as a Nautobot Job in this repository:

```text
nauto/jobs/ingest_nodeutils_inventory.py
```

Register it from:

```text
nauto/jobs/__init__.py
```

The Job can initially take one of these inputs:

- a report file path on the Nautobot server
- a directory containing report files
- pasted JSON text for manual testing

This keeps the first implementation simple and avoids designing a custom HTTP API before the data model is proven.

## Server-Side Responsibilities

The ingestor should own these responsibilities:

- Parse and validate report JSON/YAML.
- Enforce supported `schema_version` values.
- Reject oversized, malformed, or stale reports.
- Determine the Nautobot Device match.
- Resolve Nautobot objects such as location, role, status, device type, manufacturer, and tags.
- Apply central mappings and allowlists.
- Update Device fields and custom fields.
- Log what changed.
- Keep raw report storage bounded.

## Trust Boundary

The host report is evidence, not authority.

Self-reported facts that can usually be accepted:

- hostname
- fqdn
- OS name/version
- kernel version
- architecture
- CPU model/core count
- memory size
- disk summary
- GPU summary
- Docker/service observation summary
- Proxmox facts from trusted Proxmox hosts

Fields that should be centrally governed:

- Nautobot location
- role
- status
- tags
- owner
- production/service criticality
- whether a host is allowed to update an existing Device
- whether a host is allowed to create a new Device

The ingestor can use host-provided hints for these fields, but should only apply them if they match a central allowlist or mapping.

## Host Matching Policy

Use a deterministic matching order:

1. configured `node_id` or registered host identity, if introduced
2. serial number, when present and credible
3. machine-id or platform UUID, if stored in a custom field
4. hostname/fqdn fallback

Avoid creating duplicates when a host changes hostname. Store the chosen identity source in a custom field or log entry so future behavior is explainable.

## Mapping Policy

Add a server-side mapping file such as:

```text
nauto/seed/nodeutils_ingest.yaml
```

Possible contents:

```yaml
defaults:
  location: Home
  status: Active
  tags:
    - self-registered
    - home

roles_by_system:
  Linux: linux-workstation
  Darwin: macos-workstation

device_types_by_system:
  Linux: Ubuntu PC
  Darwin: Mac

allowed_self_reported:
  service_roles: true
  preferred_services: true
  owner: false
  location: false
```

This file should be the source of truth for central policy. Host-side `self_inventory.yaml` should not directly decide sensitive Nautobot classifications.

## Custom Fields

Use the current Device custom field names unless a rename has a clear value. Avoid adding duplicate fields solely to preserve old host-side command behavior:

- `last_seen`
- `os_name`
- `os_version`
- `kernel_version`
- `architecture`
- `cpu_model`
- `cpu_cores`
- `memory_gb`
- `gpu_count`
- `gpu_models`
- `gpu_memory_gb`
- `gpu_accelerator_summary`
- `disk_total_gb`
- `serial_number`
- `primary_mac_address`
- `primary_ip_address`
- `inventory_source`
- `ai_resource_summary`
- `service_roles`
- `preferred_services`
- `observed_services`
- `docker_engine_state`
- `docker_container_running_count`
- `docker_container_total_count`
- `docker_compose_projects`
- `docker_published_ports`
- `docker_service_summary`
- `service_inventory_updated_at`
- `inventory_raw_json`

Add fields only if they become necessary:

- `nodeutils_schema_version`
- `nodeutils_collector_version`
- `nodeutils_identity_source`
- `nodeutils_report_hash`
- `nodeutils_report_signed`

## Ingestion Modes

Start with batch/manual ingestion:

```text
Run Job -> load one file or directory -> dry_run=true -> inspect logs -> dry_run=false
```

Later options:

- scheduled Nautobot Job reading a drop directory
- webhook or small authenticated HTTP receiver outside Nautobot
- Git-backed report repository for auditability
- SFTP/rsync upload directory processed by the Job

Avoid exposing a broad unauthenticated upload endpoint. If an HTTP endpoint is added, use mTLS, per-host tokens with only submit permission, or signed reports.

## Validation Rules

Initial validation should include:

- supported `schema_version`
- required top-level keys
- parseable `collected_at`
- maximum report age
- maximum report size
- bounded list and string lengths
- expected data types for custom field inputs
- reject unknown schema versions by default

When a report fails validation, the Job should log the reason and skip writes for that report.

## Security Rules

- Nautobot API token remains server-side only.
- Direct host-to-Nautobot writes are removed from the normal design.
- Do not trust host-provided role/location/status/tags without server-side policy.
- Do not store unbounded raw reports in custom fields.
- Keep raw report retention short if reports are copied to disk.
- Log source path, report hash, matched Device, and action.

## Implementation Steps

1. Add `seed/nodeutils_ingest.yaml` for central defaults and allowlists.
2. Add `jobs/ingest_nodeutils_inventory.py`.
3. Implement report loading from file path, directory, or pasted JSON.
4. Implement schema and size validation.
5. Implement host matching and duplicate avoidance.
6. Reuse or port payload-building logic from `nodeutils` into the server-side Job.
7. Resolve Nautobot objects from server-side mapping, not from host authority.
8. Add `dry_run` logging before enabling writes.
9. Register the Job in `jobs/__init__.py`.
10. Update `README.md` with the new collector/ingest workflow.
11. Keep `Seed Home Cluster` aligned with any new custom fields.

## Cutover Plan

1. Add server-side ingest Job.
2. Update one or two test hosts to emit reports only.
3. Run ingest in `dry_run=true` and compare planned Nautobot changes with the intended central mapping.
4. Enable writes for those hosts.
5. Move the remaining hosts to collector mode.
6. Remove Nautobot tokens from host `.env` files.
7. Remove old direct self-registration code and documentation from `nodeutils`.

## Acceptance Criteria

- A `nodeutils` report can update a Nautobot Device without the host holding a Nautobot token.
- `dry_run=true` shows matched Device, planned create/update action, and changed fields.
- The Job rejects malformed, stale, oversized, or unsupported-schema reports.
- Location, role, status, device type, manufacturer, and tags come from server-side policy.
- Existing AI resource review and service placement workflows continue to use the same Device custom fields.

## Open Questions

- Should the first server-side input be a file path, directory, or pasted JSON?
- Should host identity be managed by SSH host keys, signed report keys, serial number, machine-id, or a manually assigned node ID?
- Should raw reports be retained outside Nautobot for audit, or only the derived custom fields stored?
- Should Proxmox guest inventory remain in the same ingest Job or be split into a dedicated Proxmox ingest path?
