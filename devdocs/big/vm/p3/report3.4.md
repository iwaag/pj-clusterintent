# Step 4 — Add strict YAML preview and transactional import

Status: `complete` (local implementation, positively exercised against a disposable database
clone; the real live deployment is Step 8, the real reviewed seed is Steps 9-10).

Raw evidence: `.local/vm-p3/20260725-step4/` (private, mode 0700/0600).

## 1. Loader additions

`nintent/nautobot_intent_catalog/loaders.py`:

- New roots `desired_compute_platforms` / `desired_compute_instances`, each normalized by a
  strict allowed/required-key mapping (`_strict_mapping_errors`) matching Section 5.8 exactly.
- `DesiredComputePlatformEntry` / `DesiredComputeInstanceEntry` dataclasses. Provider type,
  config-schema-version, platform/instance `config`, and vcpus/memory/root-disk bounds are
  validated by importing and calling the *exact same* Django-free `compute_contract` functions
  the model layer calls (`validate_provider_type`, `validate_config_schema_version`,
  `validate_platform_config`, `validate_instance_config`, `validate_vcpus`, `validate_memory_mb`,
  `validate_root_disk_gb`) — a load-time rejection and a model `ValidationError` can never diverge
  on the same input, because it is literally one shared implementation.
- Reference identities: platform by unique `slug`; instance by unique `desired_node` (one instance
  per node, checked at load time by `_duplicate_compute_instance_errors` in addition to the DB
  `OneToOneField`). `_duplicate_compute_platform_errors` rejects a duplicate platform `slug`
  within one YAML document.
- `DesiredEndpointEntry` gained `mac_address` (this field existed on the model/UI/REST since Step
  2/3 but had no YAML path at all before this step). `_normalize_desired_endpoint_entry` calls
  `compute_contract.normalize_mac_address` and surfaces `ComputeContractError` as a load error.
  `_duplicate_endpoint_mac_errors` rejects a duplicate non-null MAC within one YAML document
  (the DB `nic_unique_desired_mac_address` constraint is the second, authoritative layer, proven in
  Section 4 below).

## 2. Importer additions

`nintent/nautobot_intent_catalog/importers.py`: `desired_compute_platform_identity`/`_defaults`
and `desired_compute_instance_identity`/`_defaults` are pure identity/projection functions
matching the existing `desired_node_identity`/`desired_endpoint_defaults` pattern exactly.
`desired_endpoint_defaults` now also projects `mac_address`.

## 3. Import Job: order, preview mode, and diffs

`nintent/nautobot_intent_catalog/jobs.py`:

- `_import_intent_rows` now processes `desired_compute_platforms` then
  `desired_compute_instances` between `desired_endpoints` and `desired_services`, matching the
  Section 5.8 import order exactly. `_resolve_desired_compute_platform(slug)` resolves the
  instance's platform reference the same way `_resolve_desired_node`/`_resolve_desired_service`
  already resolve theirs.
- `_import_intent_rows` returns `(counts, diffs)` instead of only `counts`. `diffs` is populated
  identically on every call (not only in preview mode) via a new `_validated_upsert_diff` wrapper
  around the existing `_validated_upsert`: it diffs the *persisted, post-`full_clean()`* field
  values (so MAC canonicalization / config normalization never causes preview and apply to
  disagree), reporting every changed field's old/new value, or `{}` for `unchanged`.
- `ImportIntentSources` gained a `preview` `BooleanVar`. When set, the Job wraps the identical
  `_import_intent_rows` call in `transaction.atomic()` and calls
  `transaction.set_rollback(True)` before the block exits — the exact same parsing, reference
  resolution, normalization, full validation (`full_clean()`), and diff computation as apply
  (Section 5.8's explicit preview/apply-parity requirement), with zero committed writes
  guaranteed by the forced rollback rather than by skipping `save()` (which would have broken
  same-pass reference resolution — see Section 4 Scenario A). The Job writes
  `intent-import-preview.json` / `intent-import-apply.json` via `self.create_file` with the exact
  per-object diffs, and logs a summary that now also carries `desired_compute_platforms` /
  `desired_compute_instances` counts.
- `_json_safe` renders diff values (UUIDs, dicts, lists) into JSON-serializable form without
  depending on Django's JSON encoder.

## 4. Environment-backed proof (real PostgreSQL 15.17, disposable clone — not the shared database)

Same technique as Steps 2/3 (`.local/localenv_memo.md`: nintent is installed via
`pip install git+...`, not a volume mount, so local edits are invisible to the running container
without push+rebuild):

1. `pg_dump -Fc nautobot` from `my_postgres_db` -> `pg_restore` into a fresh
   `nautobot_p3_step4_scratch` database (exact clone of the live schema+data, still at migration
   `0014` at restore time).
2. Backed up the container's installed `nautobot_intent_catalog` package
   (`.orig-backup`), then `docker cp`'d this step's edited source over it.
3. `NAUTOBOT_DB_NAME=nautobot_p3_step4_scratch nautobot-server migrate nautobot_intent_catalog`
   applied `0015` cleanly (`makemigrations --check --dry-run` afterward: `No changes detected`).

Ran `step4_yaml_import_proof.py` through `nautobot-server shell`
(`NAUTOBOT_DB_NAME=nautobot_p3_step4_scratch`): **31/31 checks passed**.

| Scenario | Result |
|---|---|
| **A. Preview, single-pass reference resolution.** One YAML document creates `aghub-pve-step4-test` (`DesiredComputePlatform`) and, in the *same* pass, a `DesiredComputeInstance` for `agdnsmasq` that references it by slug, plus sets the real `agdnsmasq` endpoint's `mac_address`. | Preview reports `compute_platforms_created=1`, `compute_instances_created=1`, `endpoints_updated=1`, with exact identities in the diff list. Row counts and the endpoint's `mac_address` are **unchanged** in the DB immediately after — the in-pass slug resolution succeeded against the uncommitted platform row before the forced rollback discarded it. |
| **B. Apply** (same YAML, `preview=False`). | Platform and instance exist with the exact expected fields (`config.vmid == 108`, platform FK correct); endpoint `mac_address == bc:24:11:23:dc:b7`. |
| **C. Repeat apply** (identical YAML again). | All three rows report `unchanged`; zero creates/updates; `last_updated` identical before/after for platform, instance, and endpoint. |
| **D. Last-row rollback.** Two throwaway `planned`-lifecycle nodes (topology validation is a non-issue for `planned`), two `DesiredComputeInstance` entries on one new platform with the same `config.vmid=208`. | The second row's `full_clean()` raised `ValidationError({'__all__': ['Constraint "dci_unique_platform_vmid" is violated.']})` — Django's `validate_constraints()` did catch this expression-based constraint here (unlike Step 2's report, which needed to bypass `full_clean()` to observe the raw `IntegrityError`; either way the outer `transaction.atomic()` unwinds on any uncaught exception). Neither the platform nor the first instance survived the rollback. |
| **E. Duplicate MAC in one pass.** Two endpoints on `agpc`, same `mac_address`. | Second endpoint's `full_clean()` raised `ValidationError({'__all__': ['Constraint "nic_unique_desired_mac_address" is violated.']})`; the first endpoint's MAC write did not survive the rollback either. |
| **F. Source YAML template render.** `render_to_string` of the edited `source_yaml_list.html` with real platform/instance/endpoint objects. | Renders without a template error; output contains the platform slug, the instance's node, and the canonical MAC. |

## 5. Source YAML display

`views.py`: `source_yaml_intent_source_list` now also passes `desired_compute_platforms` /
`desired_compute_instances` into the template context. `source_yaml_list.html` gained a **MAC
Address** column on the Desired Endpoints table and two new sections (**Desired Compute
Platforms**, **Desired Compute Instances**) matching the existing per-root table style.

## 6. Cleanup

- `DROP DATABASE nautobot_p3_step4_scratch`; removed the `pg_dump` file.
- Removed the `docker cp`-overridden package from the running container and restored the original
  `nautobot_intent_catalog.orig-backup` in its place (`chown`ed back to `nautobot:nautobot`).
- Confirmed after restore: `nautobot-server showmigrations nautobot_intent_catalog` on the live
  container again ends at `0014`; a query for the new compute-platform table against the live
  `nautobot` database fails with "relation does not exist" (expected — the live schema is still
  pre-`0015`), confirming the live shared environment was not durably touched.
- Re-ran the nintent Django-free suite locally: **187/187 pass** (167 before this step; 20 new
  tests added across `test_loaders.py`, `test_importers.py`, `test_jobs_import.py`).

## Gate

Preview and apply share one code path end to end and provably diverge only in whether the
transaction commits; a same-pass reference from a new instance to a new platform resolves
correctly under preview because the forced rollback happens only at the very end; repeat apply is
a true no-op with stable `last_updated`; a last-row DB-constraint failure — both the compute-VMID
case and the endpoint-MAC case — rolls back every preceding write in the same pass, including a
platform the failing row never touched. No Proxmox/actual-ledger state was read or written in this
step.

Proceeding to Step 5.
