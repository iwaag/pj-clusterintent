# Phase 0 Report — Minimal Desired-State Contract

## Result

Phase 0 is complete. The refactor will use one authenticated batch REST endpoint as the only
supported writer for structured desired state. PostgreSQL will retain only normalized current rows;
it will not retain submitted YAML/JSON, revisions, import history, or a new audit model.

The target boundary is:

```text
private YAML or JSON -> desired-state batch API -> normalized current rows -> GraphQL -> nctl
```

The endpoint is the only new public mutation surface in this initiative. Existing per-model PATCH
routes and the file-based Import Intent Sources Job are removed at cutover. Braindump, alignment,
actual ingest, and IPAM reconciliation remain outside this boundary.

This report is an implementation input, not an implementation plan.

## Measured current state

- `nctl` already reads desired state only through one GraphQL snapshot in
  `nctl_core/sources/desired.py`.
- The current file importer is already split into a pure-ish plan (`import_plan.py`) and an atomic
  ORM apply (`jobs.py:_apply_import`). Its input is tied to a server-side path through
  `load_intent_sources(Path(...))`.
- There are four supported desired-state write paths today:

  | Writer | Rows it changes | Replacement |
  |---|---|---|
  | `Import Intent Sources` Job | all nine YAML roots | batch API |
  | `Analyze Intent Sources` Job | source analysis fields, services, dependencies | removed from this initiative's current-state model; see below |
  | `nctl lifecycle` | `DesiredNode.lifecycle` | one-operation batch |
  | nctl ledger reconciler | node/device, platform/cluster, and instance/VM links | one-operation or two-operation batch |

- The UI is inspection-only for the scoped desired models. There is no remaining model form that
  must be preserved as a writer.
- The current API exposes only `nodes`, `compute-platforms`, and `compute-instances` as desired
  mutation collections. They are narrow PATCH routes used by nctl.
- The real cluster document is tracked at `nauto/seed/intent_sources.yaml`; development config
  also embeds `/opt/nautobot/intent_sources.yaml`. Both are file-ownership surfaces to remove in
  Phase 4.

## Minimal persistence decision

`PrimaryModel` identity/timestamps are framework data and remain. No initiative-specific metadata
is added.

The table below classifies application fields by the current control loop, rather than preserving
fields merely because the old YAML or read-only UI could display them.

| Model | Retain now | Remove in the coordinated Phase 1 schema cutover |
|---|---|---|
| `IntentSource` | `slug` as the service-identity namespace | `name`, `source_type`, `url`, `ref`, `enabled`, `owner`, `description`, `source_config`, `last_import_status`, `last_imported_at`, `last_import_summary` |
| `DesiredService` | source namespace relation, `name`, `slug`, `service_type`, `lifecycle`, `catalog_namespace`, `catalog_metadata_name` | `display_name`, source/catalog analysis fields, `prefers_gpu`, `min_memory_gb`, `requirements`, `analysis_provenance`, `notes`, `last_analyzed_at` |
| `DesiredDependency` | all fields: nctl's service evaluator currently reads dependency resolution | none |
| `DesiredNode` | `name`, `slug`, `node_type`, `lifecycle`, `role`, `accepted_actual_types`, `expected_spec`, `realized_device` | `description`, `intent_source`, `notes`, `realized_device_source` |
| `DesiredEndpoint` | node relation, `name`, `endpoint_type`, IP/gateway/policy, MAC, DNS/mDNS/VPN DNS, `protocol`, `port`, dnsmasq fields, `realized_ip_address` | `dns_name_source`, `mdns_name_source`, `realized_ip_address_source`, `description` |
| `DesiredIPRange` | `name`, `slug`, addresses, policy, lifecycle, dnsmasq fields | `description` |
| `DesiredComputePlatform` | `name`, `slug`, lifecycle, control node, `config`, `realized_cluster` | `provider_type` and `config_schema_version` (both fixed to Proxmox/v1), `realized_cluster_source` |
| `DesiredComputeInstance` | node/platform relations, kind, desired power, vCPU/memory/disk, `config`, `realized_vm` | `config_schema_version` (fixed to v1), `realized_vm_source` |
| `DesiredServicePlacement` | service/node/optional endpoint relations, instance name, desired state, deployment profile, config schema version, config | `instance_role`, `assignment_source`, `reason` |
| `DesiredNodeOperationalOverride` | all fields except no-op rows; all are consumed by production composition | none |

### Consequences

- Git-repository catalog analysis is not a current control-loop requirement for this cluster. The
  `Analyze Intent Sources` Job, its per-source status/history, and its source-derived service
  metadata are removed rather than moved behind another writer. `DesiredDependency` remains
  because it is currently evaluated by nctl; a later initiative may remove it only after removing
  that evaluator path.
- A retained `IntentSource` is a minimal namespace row for the existing qualified service identity.
  It is not a stored URL, Git reference, or import provenance record.
- `*_source` provenance fields are presentation metadata, not inputs to a current decision. The
  corresponding relation itself remains the actual link.
- Fixed schema/provider discriminator fields are code contract, not per-cluster state. Their
  validators move to code in the same release that removes the fields.
- Removing a field also removes its GraphQL selection, filters, tables, templates, loader keys,
  serializers, tests, and documentation. No compatibility aliases remain.

## Canonical batch request contract

Phase 2 will expose exactly one endpoint:

```text
POST /api/plugins/intent-catalog/desired-state/batch/
```

The request is either JSON or YAML. Both decode into the same envelope; neither has a separate
meaning or server-side file reference.

```yaml
dry_run: true
operations:
  - op: upsert
    kind: desired_node
    key:
      slug: agpc
    values:
      name: agpc
      node_type: device
      lifecycle: active
  - op: delete
    kind: desired_endpoint
    key:
      desired_node: old-node
      name: primary
      endpoint_type: primary
```

`dry_run: true` plans only. `dry_run: false` validates all operations and commits exactly once.
The response uses the existing useful plan vocabulary:

```text
create | update | delete | unchanged | conflict
```

It includes per-operation identity, changed fields, conflicts, totals, and transaction outcome.
The response is returned to the caller only; it is not persisted as a custom artifact or database
row.

### Operation rules

- The only operations are `upsert` and `delete`. A one-row edit is an `upsert` batch of length one.
- `key` uses a stable natural identity. The identities are:

  | Kind | Key |
  |---|---|
  | `intent_source` | `slug` |
  | `desired_node` | `slug` |
  | `desired_endpoint` | `desired_node`, `name`, `endpoint_type` |
  | `desired_ip_range` | `slug` |
  | `desired_compute_platform` | `slug` |
  | `desired_compute_instance` | `desired_node` |
  | `desired_service` | `intent_source`, `catalog_namespace`, `catalog_metadata_name`, `service_type` |
  | `desired_dependency` | `source_service` qualified key, `dependency_kind`, `namespace`, `name` |
  | `desired_service_placement` | desired-service qualified key, `instance_name` |
  | `desired_node_operational_override` | `desired_node` |

- An `upsert` changes only named `values`; omitted values are unchanged. A nullable value is
  cleared with explicit `null`.
- References may resolve to a row already present or to an earlier/effective upsert in the same
  batch. Missing or ambiguous references are conflicts.
- A delete is explicit. It is blocked while another desired-state row references its target; the
  caller must include the dependent deletes. It never cascades from API omission.
- Actual links are ordinary named fields on the owning row. nctl uses the same `upsert` operation
  to set or clear them; it does not receive a second link-specific endpoint.
- A conflict, validation error, or failed apply leaves every row unchanged.

This deliberately selects partial operations over a whole-document replacement. The current
control-plane use needs small lifecycle and realization-link writes as well as structural edits;
an explicit batch avoids separate APIs and avoids making accidental omission destructive.

## Cutover order

The scratch database is migrated in place. Retained current rows and actual links are preserved;
values in fields designated for removal are discarded. No raw file snapshot or data-copy model is
introduced.

1. Implement the Phase 1 service and migrations in nintent. It consumes in-memory decoded input
   and owns validation, planning, ordering, deletion checks, and transaction apply.
2. Add and test the Phase 2 endpoint in nintent. Deploy it to the scratch Nautobot image.
3. Change nctl lifecycle and ledger linking to use the endpoint, then run the nctl and runtime
   tests against that deployed image.
4. Deploy the coordinated nintent cutover that removes the old PATCH routes, Import/Analyze Jobs,
   file-path setting/environment fallback, deprecated fields, and their readers.
5. Submit the existing cluster state through a private local batch document, confirm GraphQL/nctl
   reads, then remove the tracked `intent_sources.yaml` and all real-data examples.

During steps 2–3, the old routes may exist only as a short deployment bridge. They are not a
supported final interface and are deleted in step 4. nintent changes still follow the local
deployment rule: commit, user push, image rebuild, restart, migrate, then test the matching nctl
revision.

## Phase 1 planning notes

- Reuse the current loader normalization and `plan_upsert` ideas, but replace path-based loading
  and root-specific YAML ownership with the batch envelope above.
- Keep HTTP decoding and REST serialization thin. The plan/apply service must be callable without
  HTTP for focused tests.
- The required migration is intentionally breaking. Do not create dual fields, fallback settings,
  old API aliases, or import compatibility readers.
- Test data may continue to use direct ORM setup. Tests that claim to prove a public nctl/operator
  write path must use the batch API.
- Existing Nautobot authentication and conventional validation responses are sufficient. No new
  role system, payload archive, approval flow, or signature mechanism is needed.

## Phase 0 exit criteria

All requested Phase 0 outputs now exist in this report:

- a field classification and removal assignment;
- one batch wire contract with identities and deletion semantics;
- a complete supported-writer inventory; and
- a coordinated migration/deployment order.
