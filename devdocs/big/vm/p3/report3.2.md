# Step 2 — Add the final models and destructive migration

Status: `complete` (local implementation and disposable-database proof; the real coordinated
deployment is Step 8, not run here).

Raw evidence: `.local/vm-p3/20260725-step1/` (spike/migration artifacts from Step 1's DB session
continued into Step 2; private, mode 0700/0600).

## 1. Final models added

`nintent/nautobot_intent_catalog/models.py`:

- `DesiredComputePlatform(PrimaryModel)`: `name`, `slug` (unique), `provider_type` (closed to
  `proxmox`), `lifecycle`, `control_node` (FK to `DesiredNode`, `PROTECT`, related name
  `controlled_compute_platforms`), `config_schema_version` (`v1`, editable=False),
  `config` (JSONField), `realized_cluster`/`realized_cluster_source` (nullable, `SET_NULL`,
  Phase 3 read-only). DB `CheckConstraint`s pin `provider_type='proxmox'`,
  `config_schema_version='v1'`, and `jsonb_typeof(config)='object'`.
- `DesiredComputeInstance(PrimaryModel)`: `desired_node` (`OneToOneField`, `CASCADE`, enforcing
  one instance per node structurally), `platform` (FK, `PROTECT`), `instance_kind`,
  `desired_power_state`, `vcpus`/`memory_mb`/`root_disk_gb` (`PositiveIntegerField` + DB
  `CheckConstraint` bounds matching Step 1's pure validator bounds exactly), `config_schema_version`,
  `config`, `realized_vm`/`realized_vm_source` (nullable, `SET_NULL`, Phase 3 read-only). No
  independent lifecycle field, per Section 5.4.
- `DesiredEndpoint.mac_address`: nullable `CharField(max_length=17)`, DB `UniqueConstraint`
  scoped to non-null values (`nic_unique_desired_mac_address`), normalized to canonical
  lower-case-colon form in `clean()` via `compute_contract.normalize_mac_address`.
- **`DesiredComputeInstance.config` VMID uniqueness**: `UniqueConstraint("platform",
  Cast(KeyTextTransform("vmid", "config"), output_field=BigIntegerField()),
  condition=Q(config__has_key="vmid"))` — the exact mechanism proven in Step 1.
- A shared `validate_compute_instance_topology(instance)` module-level function (in `models.py`,
  reused later by forms/REST/YAML per plan Section 5.5): resolves effective lifecycle, and for
  `active`/`approved` instances requires effective storage/bridge resolved (not `unresolved`) and
  exactly one primary DesiredEndpoint on the owning node with a canonical MAC, non-empty
  `mdns_name`, and a usable `dhcp_reserved`/`static` address contract. Called from
  `DesiredComputeInstance.clean()`.
- `DesiredNode.clean()` now blocks retiring a node that still controls a `DesiredComputePlatform`
  (`controlled_compute_platforms.exists()`), and its `realized_device`/`realized_vm` XNOR loop is
  reduced to `realized_device` only (the legacy `realized_vm` field is removed).

## 2. Legacy field removal and coordinated-breaking cleanup

`DesiredNode.realized_vm`/`realized_vm_source` are removed from the model. Every other in-repo
consumer was updated in the same commit so the app still imports and loads (required even to run
`makemigrations`):

- `tables.py`: dropped the `realized_vm` column from `DesiredNodeTable`.
- `forms.py`: dropped `realized_vm` from `DesiredNodeForm.Meta.fields` and its `save()` source loop.
- `filters.py`: dropped `realized_vm` from `DesiredNodeFilterSet.Meta.fields`.
- `views.py`: dropped `realized_vm` from both `DesiredNode` queryset `select_related()` calls.
- `api/serializers.py`: dropped `realized_vm_source` field and its XNOR loop entry from
  `DesiredNodeSerializer`.
- `jobs.py`: dropped `desired_node__realized_vm` from a `select_related()` call and the dead
  `realized_vm` candidate branch in `_observed_ip_candidates()` (guest-OS IP evidence only ever
  came from `realized_device`; the removed branch was already unreachable in practice).
- `templates/nautobot_intent_catalog/desirednode.html`: removed the "Realized VM" detail row.

New UI/REST/GraphQL/YAML surfaces *for* the new compute models are explicitly Step 3/4 work and are
not added here.

## 3. Migration `0015_compute_platform_instance_and_endpoint_mac`

Generated via Django's `makemigrations` against a disposable database (Section 4 below), then
hand-augmented with one `RunPython` operation, `assert_no_legacy_realized_vm`, inserted **before**
the `RemoveField` operations for `realized_vm`/`realized_vm_source`. It queries the historical
`DesiredNode` model for `realized_vm__isnull=False` and raises `RuntimeError` (aborting the whole
migration transaction) if any row is found. `makemigrations --check --dry-run` against the
disposable database confirms this hand-edited file has the identical schema effect Django itself
would generate (`No changes detected`).

## 4. Disposable-database proof (real PostgreSQL 15.17, not the shared `nautobot` database)

Since nintent is installed into the running container via `pip install git+https://...` (not a
volume mount — `.local/localenv_memo.md`), local source edits are invisible to the container until
push+rebuild. To exercise `makemigrations`/`migrate` locally without touching the live shared
database or the live container's real installed code:

1. `pg_dump -Fc nautobot` -> `pg_restore` into a fresh `nautobot_p3_scratch` database (exact clone
   of the live schema+data, migration state `0014`).
2. Backed up the container's installed `nautobot_intent_catalog` package
   (`.orig-backup`), then `docker cp`'d the local edited source over it — a purely local, disposable
   override of the container's writable layer, unrelated to the real coordinated push/rebuild
   deployment path.
3. Ran `nautobot-server makemigrations`/`migrate` with `NAUTOBOT_DB_NAME=nautobot_p3_scratch`, so
   every schema operation below hit only the scratch database, never `nautobot`.

Results:

| Case | Result |
|---|---|
| `makemigrations --dry-run` | generates exactly the operations in `0015...py` (`CreateModel` x2, `RemoveField` x2, `AddField`/`AddConstraint` for MAC and the six new-model FKs/constraints) |
| Forward `migrate 0015` with a synthetic non-null `realized_vm` fixture (set `aghub`'s `realized_vm` to a real scratch-DB VirtualMachine row) | **aborted**: `RuntimeError: Refusing to drop DesiredNode.realized_vm: 1 row(s) still have a non-null legacy realized_vm link ...`; `showmigrations` confirmed `0015` stayed unapplied and neither new table was created — the whole migration transaction rolled back, proving no partial `CreateModel` effect survived |
| Fixture cleared (`realized_vm` set back to `NULL`), forward `migrate 0015` | succeeded; both new tables exist with **0** rows each; `desirednode` no longer has `realized_vm`/`realized_vm_source` columns; `realized_device` untouched |
| Backward `migrate 0014` | succeeded; both new tables dropped; `realized_vm`/`realized_vm_source` columns restored on `desirednode` |
| Forward `migrate 0015` again | succeeded identically; `desiredcomputeplatform` count still 0 |

Forward/backward/forward and the legacy-fixture-blocks-forward proof are both satisfied.

## 5. Environment-backed ORM/constraint tests (against the same scratch database, migrated to 0015)

Ran `step2_orm_proof.py` through `nautobot-server shell` (`NAUTOBOT_DB_NAME=nautobot_p3_scratch`).
9/9 checks passed:

| Check | Result |
|---|---|
| Valid platform create (`aghub-pve-test`, full config) | created |
| `provider_type="aws"` rejected | `ValidationError`: `invalid_provider_type` |
| Retired control node rejected | `ValidationError`: `'The control node must not be retired.'` |
| Unknown platform config key (`api_url`) rejected | `ValidationError`: `unknown_config_key` |
| Instance create with no MAC/mDNS on the owning node's endpoint | `ValidationError`: `compute_primary_endpoint_missing` (topology validator fires from `clean()`) |
| Instance create after endpoint gets `mac_address=bc:24:11:23:dc:b7` (`agdnsmasq`'s real seed MAC) and already has `mdns_name`/`static` IP | created |
| Second instance on the same node (`agdnsmasq`) | rejected: `'Desired compute instance with this Desired node already exists.'` (OneToOne) |
| Duplicate `(platform, config.vmid=108)` on a second node, bypassing `full_clean` | DB `IntegrityError`: `duplicate key value violates unique constraint "dci_unique_platform_vmid"` |
| Retiring `aghub` while it controls `aghub-pve-test` | `ValidationError`: `'A DesiredNode that controls a DesiredComputePlatform cannot be retired.'` |

One benign, non-fatal Django warning appeared on every `full_clean()` call: `Got a database error
calling check() on <Q: (AND: RawSQL(jsonb_typeof(config) = 'object', ()))>: column "config" does
not exist`. This is Django's known limitation evaluating a raw-SQL `CheckConstraint` against an
unsaved in-memory instance during `Model.validate_constraints()` — Django logs and skips that one
constraint's pre-save simulation; the real `dcp_config_object`/`dci_config_object` `CHECK`
constraints still enforce it at actual `INSERT`/`UPDATE` time, and the pure `compute_contract`
validators already guarantee `config` is a dict before `clean()` ever reaches that point. No test
above depended on the raw-SQL constraint catching a bad value; each JSON-object case was validated
by the Python-side pure validator instead.

## 6. Cleanup

- `DROP DATABASE nautobot_p3_scratch` and removed the `pg_dump` file.
- Removed the `docker cp`-overridden package from the running container and restored the original
  `nautobot_intent_catalog.orig-backup` in its place (`chown`ed back to `nautobot:nautobot`).
- Confirmed after restore: `nautobot-server showmigrations nautobot_intent_catalog` on the live
  container again ends at `0014`, and the live `nautobot` database still has 0 rows with a non-null
  `realized_vm` — the live shared environment was not durably touched by this step's local proof
  work.
- Re-ran the nintent Django-free suite locally: 167/167 pass, no regression from the `models.py`
  edits.

## Gate

The migration is reversible (proven forward/backward/forward on a disposable clone of the live
schema+data), refuses data loss (proven with a synthetic non-null legacy fixture), and — once
applied — leaves only the final ownership model (`desirednode` has no VM-realization field; compute
realization lives solely on `DesiredComputeInstance.realized_vm`). All local consumers of the
removed field were updated in the same change so the app still loads. No live state in the shared
`nautobot-nautobot-1` container or its `nautobot` database was durably modified by this step.

Proceeding to Step 3.
