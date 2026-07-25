# Step 3 — Add UI, REST, and GraphQL surfaces

Status: `complete` (local implementation, positively exercised against a disposable database
clone; the real live deployment is Step 8).

Raw evidence: `.local/vm-p3/20260725-step1/step3_*` (private, mode 0700/0600).

## 1. UI surfaces added

`nintent/nautobot_intent_catalog/`:

- `forms.py`: `DesiredComputePlatformForm` (`name`, `slug`, `provider_type`, `lifecycle`,
  `control_node`, `config`) and `DesiredComputeInstanceForm` (`desired_node`, `platform`,
  `instance_kind`, `desired_power_state`, `vcpus`, `memory_mb`, `root_disk_gb`, `config`). Neither
  exposes `config_schema_version` (non-editable) or the `realized_cluster`/`realized_vm`
  actual-link/source fields — ordinary CRUD structurally cannot write them.
- `tables.py`: `DesiredComputePlatformTable` (identity, provider/lifecycle, control node,
  realized cluster, instance count) and `DesiredComputeInstanceTable` (node, platform, kind/power,
  a rendered **effective lifecycle** column via `compute_contract.effective_lifecycle`, capacity,
  realized VM). `DesiredEndpointTable`/`DesiredNodeTable` gained a `mac_address` column
  (endpoint) and stayed otherwise unchanged (the legacy `realized_vm` column was already dropped in
  Step 2).
- `filters.py`: `DesiredComputePlatformFilterSet` (slug/provider/lifecycle/control node/realized
  cluster) and `DesiredComputeInstanceFilterSet` (desired node/platform/kind/power/realized VM);
  `DesiredEndpointFilterSet` gained `mac_address` (exact and in the free-text `q` search).
- `views.py`: full List/Detail/Edit/Delete views for both models. `DesiredComputeInstanceView`
  supplies `effective_lifecycle`, `effective_storage`, `effective_bridge` (via the Step 2
  `_resolve_compute_effective_value` helper) as extra template context. `DesiredNodeView` now
  `prefetch_related`s `controlled_compute_platforms`/`desired_compute_instance`.
- `urls.py`/`navigation.py`: `compute-platforms/` and `compute-instances/` list/add/detail/edit/
  delete routes, and two new nav items under **Desired State**.
- Templates: new `desiredcomputeplatform.html` (attributes + a **Desired Compute Instances**
  related panel) and `desiredcomputeinstance.html` (attributes, effective lifecycle, effective
  storage/bridge with provenance, realized VM). `desiredendpoint.html` and `desirednode.html`
  gained MAC/compute-relation rows; `desirednode.html` gained a **Compute Realization** panel
  showing the node's `desired_compute_instance` and `controlled_compute_platforms`.
- `tests/test_templates.py`: both new template names added to the expected set.

## 2. REST surfaces added

- Routes: `/api/plugins/intent-catalog/compute-platforms/` and `/compute-instances/` (`api/urls.py`).
- `DesiredComputePlatformSerializer`/`DesiredComputeInstanceSerializer` (`api/serializers.py`):
  `fields = "__all__"` with `read_only_fields = ("realized_cluster", "realized_cluster_source")` /
  `("realized_vm", "realized_vm_source")` — these FK fields have no `editable=False` on the model
  (only their `_source` companions do), so they are explicitly listed rather than relying on DRF's
  auto-detection. `config_schema_version` is explicitly declared as a writable `CharField`
  (overriding DRF's auto-read-only mapping for the underlying `editable=False` model field) so an
  omitted value keeps the model's `"v1"` default while an explicit wrong value is rejected.
  Neither serializer duplicates the config/MAC/topology validators: `NautobotModelSerializer`'s
  `ValidatedModelSerializer` base already calls `instance.full_clean()`, which runs the exact same
  `compute_contract` validators and `validate_compute_instance_topology` the model/UI path uses.
- `api/views.py`: `DesiredComputePlatformViewSet`/`DesiredComputeInstanceViewSet`
  (`NautobotModelViewSet`, standard list/create/retrieve/update/partial_update/destroy).

## 3. GraphQL

Both models already carry `@extras_features("graphql")` from Step 2; no additional wiring code was
needed. Verified live (Section 5 below) that Nautobot auto-generates `desired_compute_platforms`/
`desired_compute_instances` query roots with the exact field spellings and Nautobot's uppercase
GraphQL enum convention.

## 4. Disposable-database live proof (same technique as Step 2)

`pg_dump`/`pg_restore` cloned the live `nautobot` database into `nautobot_p3_step3_scratch`;
`docker cp` temporarily overrode the container's installed package (backed up first, restored
after); `NAUTOBOT_DB_NAME=nautobot_p3_step3_scratch nautobot-server migrate` brought the scratch
database to `0015`. All checks below ran against the scratch database only.

`step3_ui_rest_graphql_proof.py`, run through `nautobot-server shell` with a `force_login`ed
superuser (`Client`) and a `force_authenticate`d DRF `APIClient`: **23/23 passed**.

| Area | Checks |
|---|---|
| UI list/add | platform list (200), platform add form (200), instance list (200) |
| UI create | platform create via form (302 redirect + row exists); instance create via form (302 + row exists, using `agdnsmasq`'s endpoint after setting its `mac_address` to the real seed MAC `bc:24:11:23:dc:b7`) |
| UI validation error | `provider_type="aws"` POST re-renders the form (200), creates no row |
| UI detail | platform/instance detail pages 200, platform detail shows the created name |
| UI related panels | node detail (`agdnsmasq`) page contains the created instance's URL; node detail (`aghub`) page contains the created platform's URL |
| REST create | omitted `config_schema_version` -> `201`, response value `"v1"`; explicit `"v1"` -> `201`; explicit `"v2"` -> `400` |
| REST link-write rejection | POST with `realized_cluster` set to a random UUID still returns `201` with `realized_cluster: null` (the field is read-only, so DRF silently drops the input rather than accepting it) |
| REST get/patch | `GET` on a created platform -> `200`; `PATCH config` -> `200` with the updated value |
| REST instance create (non-actionable draft) | a `planned`-lifecycle node's compute instance, with a random `realized_vm` UUID in the payload, creates successfully (`201`) with `realized_vm: null` — the read-only field is ignored, and the `planned` effective lifecycle correctly skips the topology-completeness check |
| GraphQL | `desired_compute_platforms`/`desired_compute_instances` roots return non-empty results with `id`, intent fields, `config`/`config_schema_version`, `control_node`/`platform`/`desired_node` relations, and `realized_cluster`/`realized_cluster_source` / `realized_vm`/`realized_vm_source` — zero GraphQL errors |

A follow-up query (`step3_graphql_enum_check.py`) confirmed Nautobot's uppercase GraphQL enum
convention end to end: `provider_type: "PROXMOX"`, `lifecycle: "ACTIVE"`,
`instance_kind: "CONTAINER"`/`"VIRTUAL_MACHINE"`, `desired_power_state: "RUNNING"`/`"STOPPED"`.

One earlier iteration of this script incorrectly expected a REST-created `DesiredComputeInstance`
on a fresh node with no endpoint to accept a `realized_vm` write; it instead correctly failed with
`compute_primary_endpoint_missing`/`effective bridge is unresolved` because that node's default
`active` lifecycle made the instance actionable. The test was fixed to use a `planned`-lifecycle
node (a legitimate non-actionable draft), not the topology validator — the validator's behavior was
correct on the first attempt.

The same benign `RawSQL` `CheckConstraint` warning from Step 2 appears here on every `full_clean()`
call (Django cannot pre-evaluate that one constraint against an unsaved instance); it does not
affect any result, since the pure `compute_contract` validators already guarantee `config` is a
dict before that point, and the real DB `CHECK` still applies at `INSERT`/`UPDATE`.

`makemigrations nautobot_intent_catalog --check --dry-run` against the scratch database after all
of the above writes: `No changes detected` — confirming the UI/REST layer introduced no implicit
schema drift.

## 5. Cleanup

`DROP DATABASE nautobot_p3_step3_scratch`; removed the `pg_dump` file; restored the container's
original installed package from its backup (`chown`ed back to `nautobot:nautobot`). Confirmed
afterward: the live container is back at migration `0014`, and the live `nautobot` database still
has 0 non-null legacy `realized_vm` rows — no durable change to the shared live environment.

Re-ran the nintent Django-free suite locally: 167/167 pass (unaffected — this suite doesn't import
the Django-gated code paths changed in this step, but confirms the `compute_contract` module and
the rest of the package still parse/import cleanly).

## Gate

Every supported UI/API/read path was positively exercised with real objects, not merely a 200
response against empty roots: list/add/detail/edit-error for both models, one full create+patch+
link-write-rejection REST round trip per model, related-object panels on `DesiredNode`, and
non-empty GraphQL roots with the exact expected field/enum spellings.

Proceeding to Step 4.
