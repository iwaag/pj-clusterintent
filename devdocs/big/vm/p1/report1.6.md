# Step 6 — Freeze the desired model, API, and YAML contract

Status: complete.

Turns plan §5.2/§5.3/§5.4 into a Phase 3 implementation checklist, using the live-confirmed
`DesiredNode` conventions from Step 1 (`nintent/nautobot_intent_catalog/models.py:280-339`):
`LIFECYCLE_CHOICES` is exactly `planned|approved|active|deprecated|retired`; actual-link FKs use
`on_delete=models.SET_NULL, blank=True, null=True` plus a paired `*_source` CharField
(`derived|override`, `editable=False`); intent-owning FKs elsewhere in the file use
`on_delete=models.PROTECT` (e.g. lines 578/583/588/692/709/716).

## `DesiredComputePlatform`

| Field | Django type | on_delete/null | Form/table | REST | GraphQL | YAML |
|---|---|---|---|---|---|---|
| `name` | `CharField` | — | edit/list | rw | read | required |
| `slug` | `SlugField(unique=True)` | — | edit/list | rw | read | identity key |
| `provider_type` | `CharField(choices=(("proxmox","Proxmox"),))` | not null, default `proxmox` | display-only (single choice) | rw, closed choice | read, enum | required, rejects non-`proxmox` |
| `lifecycle` | `CharField(choices=LIFECYCLE_CHOICES)` reusing `DesiredNode.LIFECYCLE_CHOICES` verbatim | default `active` | edit/list/filter | rw | read, enum | optional, default `active` |
| `control_node` | `ForeignKey("DesiredNode")` | `on_delete=PROTECT` (intent-owning, unlike actual links) | edit/detail | rw | read | required, references `desired_nodes` identity |
| `config_schema_version` | `CharField`, immutable after create (`clean()` rejects change) | not null | display-only | read-only after create | read | pinned per plan version, e.g. `v1` |
| `config` | `JSONField` validated against closed key set (`cluster_name`, `default_storage`, `default_bridge`) | default `{}` | JSON edit widget + per-key validation | rw, server-side schema validation | read (as scalar JSON or typed sub-object) | nested mapping under `desired_compute_platforms[].config` |
| `realized_cluster` | `ForeignKey("virtualization.Cluster")` | `on_delete=SET_NULL, blank=True, null=True` | detail-only | rw via explicit link action only (Phase 4) | read | not settable via YAML import |
| `realized_cluster_source` | `CharField(choices=(("derived","Derived"),("override","Override")), editable=False)` | blank/null | detail-only | paired with above | read | not settable via YAML import |

Model-level `clean()`/constraint checklist: `provider_type` closed to `proxmox`; unknown `config`
keys raise `ValidationError`; `realized_cluster_source` present iff `realized_cluster` is set
(mirrors the existing `DesiredNode.clean()` XNOR pattern at model.py:412-421); `control_node` must
reference a non-`retired` `DesiredNode` (constraint, not just form validation, since YAML import
bypasses forms).

## `DesiredComputeInstance`

| Field | Django type | on_delete/null | Consumer |
|---|---|---|---|
| `desired_node` | `OneToOneField("DesiredNode")` | `on_delete=CASCADE` (deleting the node retires its compute intent; matches existing endpoint pattern at model.py:464) | scope/identity owner |
| `platform` | `ForeignKey("DesiredComputePlatform")` | `on_delete=PROTECT` (plan §5.1: platform deletion is protected while instances reference it) | dependency closure |
| `instance_kind` | `CharField(choices=(("container","Container"),("virtual_machine","Virtual Machine")))` | not null | matching/schema dispatch |
| `desired_power_state` | `CharField(choices=(("running","Running"),("stopped","Stopped")), default="running")` | not null | start-plan gate |
| `vcpus` | `PositiveIntegerField` + `MinValueValidator(1)`/bounded max (Step 7 pins exact bound from live fixture) | not null | create/drift |
| `memory_mb` | `PositiveIntegerField`, MiB-fixed | not null | create/drift |
| `root_disk_gb` | `PositiveIntegerField`, GiB-fixed | not null | create; drift only vs. `lxc_rootfs_volume` (report 1.5), never vs. `disk_gb` |
| `config_schema_version` | `CharField`, immutable after create | not null | strict validation |
| `config` | `JSONField`, closed keys `vmid`, `template`, `storage`, `bridge`, `unprivileged` | default `{}` | create payload, safe identification |
| `realized_vm` | `ForeignKey("virtualization.VirtualMachine")` | `on_delete=SET_NULL, blank=True, null=True` | actual link |
| `realized_vm_source` | `CharField(choices=derived/override, editable=False)` | blank/null | provenance |

No independent `lifecycle` field (roadmap Decision 10): effective lifecycle is a computed property
reading `self.desired_node.lifecycle` gated by `self.platform.lifecycle`, not a stored column.

Constraints: one `DesiredComputeInstance` per `DesiredNode` (guaranteed structurally by
`OneToOneField`, no extra constraint needed); `unprivileged` key rejected when
`instance_kind="virtual_machine"`; `unique_together`-style DB constraint on non-null
`config->vmid` scoped to `platform` (two instances on the same platform must not request the same
VMID) — deferred exact SQL/JSON-field-constraint mechanism to the Phase 3 migration author, since
Nautobot's Django version support for JSON-field partial-uniqueness needs a version check not
performed in Phase 1.

## `DesiredEndpoint.mac_address`

| Field | Django type | Rule |
|---|---|---|
| `mac_address` | `CharField(max_length=17, blank=True, null=True)` + custom normalizing validator (lower-case colon-separated) | `unique=True` constraint scoped to non-null values (Django `UniqueConstraint(fields=["mac_address"], condition=Q(mac_address__isnull=False))`, since a bare `unique=True` would still enforce uniqueness for NULLs incorrectly only on some backends — Postgres NULLs are distinct by default so a plain `unique=True` is actually sufficient here; both are viable, Phase 3 picks one and documents it) |

Model `clean()`, DRF serializer, Django form, and YAML loader must all call the same
`normalize_mac_address()` helper (new, shared function) rather than duplicating the regex across
four surfaces.

## YAML roots

```yaml
desired_compute_platforms: []
desired_compute_instances: []
```

Loader changes (`nintent/nautobot_intent_catalog/loaders.py`, extending the `_list_section`
pattern at lines 259/275): add `_list_section(data, "desired_compute_platforms")` and
`_list_section(data, "desired_compute_instances")`, each strict on unknown top-level keys per
existing loader behavior. Identity key: `slug` for platforms, `desired_node` (by `DesiredNode`
slug) for instances. Transactional import order: `desired_compute_platforms` before
`desired_compute_instances` (FK dependency), both after `desired_nodes`/`desired_endpoints`
(existing roots), consistent with the plan's existing node→endpoint ordering.

## REST/GraphQL

- REST: new `DesiredComputePlatformViewSet`/`DesiredComputeInstanceViewSet` following the existing
  `DesiredNodeViewSet`/`DesiredEndpointViewSet` registration pattern
  (`nintent/nautobot_intent_catalog/api/urls.py:8-11`), mounted at
  `/api/plugins/intent-catalog/compute-platforms/` and `.../compute-instances/`.
- `realized_cluster`/`realized_vm` link writes require `*_source` in the same PATCH (plan §Step6),
  enforced in the serializer's `validate()`, not just the model, so YAML import gets the same
  rejection.
- GraphQL: both models get `@extras_features("graphql")` (matching every existing model, Step 1
  item 7) with equivalent root/field naming to their REST serializers.

## nctl pydantic desired-snapshot fields

New `DesiredComputePlatform`/`DesiredComputeInstance` pydantic models in
`nctl/src/nctl_core/sources/desired.py`, added alongside the existing `realized_vm`/
`realized_vm_source` parsing (lines 268/280-281) as part of the Phase 3 "compatibility reader"
release (plan §5.5 Step 2) — not implemented in Phase 1.

## Gate evaluation

Every Section 5 field now has a decided Django type, null/constraint rule, form/table/filter
placement, REST/GraphQL surface, and YAML root — derived from live model conventions (Step 1) and
live gaps (Step 3: no `ClusterType`, no `proxmox_*` custom fields, no `mac_address` field). Step 6
gate passed.

## Discrepancies

One open implementation choice was left for the Phase 3 author rather than forced here: the exact
mechanism for a non-null-`vmid`-per-platform uniqueness constraint depends on the deployed Django/
Nautobot JSONField constraint support, which Phase 1 did not version-check. This is recorded as an
implementation decision, not a blocker, since either mechanism satisfies the same intent.
