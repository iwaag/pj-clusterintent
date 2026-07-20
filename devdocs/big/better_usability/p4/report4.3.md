# Phase 4 Step 4.3 — Analysis updates provenance-safe and dependency-stable

Parent: [plan.md](plan.md), Step 4.3.

Continues the same nintent deployable batch as Step 4.2 (no Nautobot rebuild yet; still
incompatible with the current nctl GraphQL query until Step 4.4).

## 1–2. Create-vs-update split; closed `analysis_provenance` shape

`importers.py`: `desired_service_defaults` split into two functions.

- `desired_service_create_defaults(service)` — full defaults for a brand-new row: `requirements`
  starts `{}` (never seeded from analysis), `analysis_provenance` from the new
  `analysis_provenance_defaults(analysis)` helper.
- `desired_service_update_fields(service)` — only source/catalog-derived fields
  (`source_ref`, `source_catalog_path`, `catalog_kind`, `catalog_namespace`,
  `catalog_metadata_name`, `catalog_owner`, `catalog_lifecycle`, `prefers_gpu`, `min_memory_gb`)
  plus `analysis_provenance`. **Judgment call, documented in code**: `requirements`, `lifecycle`,
  `notes`, `name`, `slug`, `display_name` are deliberately excluded from the update set — the plan
  says a refresh updates "only source/catalog fields, analysis_provenance, and last_analyzed_at";
  `requirements` is the field the plan calls out by name, but the same reasoning applies to
  `lifecycle` (Phase 3 kept `DesiredService.lifecycle`'s `proposed` default deliberate, and Step
  4.6's basic-service recipe explicitly has the operator set `active`), `notes` (an
  operator-editable form field), and `name`/`slug`/`display_name` (identity an operator may have
  renamed). Freezing all of them post-creation, not just `requirements`, is the actual fix for the
  bug class the plan describes, not a narrower literal reading of one example field.

`analysis_provenance_defaults(analysis)` builds the closed `status`/`confidence`/`reasons`/
`warnings` shape and raises `ValueError` on any key outside
`{status, confidence, reasons, warnings, malformed_dependencies}` — the internal
`analysis.py` → `importers.py` contract boundary, not user input, so an unexpected key is a real
drift bug caught immediately rather than silently absorbed.

## 3–4. Pure dependency diff plan; transactional ORM applier

`importers.py`: `plan_dependency_sync(existing, service)` — pure, natural-key
(`dependency_kind`, `namespace`, `name`) diff. Returns `create` (full `dependency_defaults()`
dicts, always `resolution_status=unresolved` for a new key), `update` (`{key, raw_ref,
dependency_type}` only — `notes`/`resolution_status`/`resolved_service` are structurally absent
from this shape, so the caller cannot accidentally overwrite them), `unchanged_keys`, and
`delete_keys`. Raises `ValueError` on duplicate normalized incoming keys before returning any
plan.

`jobs.py`'s `AnalyzeIntentSources.run()` rewritten:

1. Duplicate-key rejection runs once, before the transaction opens and before the service row
   itself is touched (`plan_dependency_sync(existing=[], service=service)` — duplicate detection
   only needs the incoming analysis, so this catches the failure with zero prior writes).
2. Inside one `transaction.atomic()` per service: `select_for_update()`-locked get-or-create
   (create path uses `desired_service_create_defaults`; update path uses
   `desired_service_update_fields` via `setattr`+`save(update_fields=...)`, never
   `update_or_create`), then the dependency plan is recomputed against the real DB rows and
   applied: `bulk_create` for `create`, targeted `.filter(...).update(raw_ref=..., dependency_type=...)`
   per `update` entry (never touching `notes`/`resolution_status`/`resolved_service`), and
   `.filter(...).delete()` per `delete_keys`.
3. `dependencies_replaced` replaced with `dependencies_created`/`dependencies_updated`/
   `dependencies_deleted`/`dependencies_unchanged` in the logged summary (item 5).

## 6. Tests

`nintent/nautobot_intent_catalog/tests/test_importers.py` — 6 new tests, local suite **98
passed** (up from Step 4.2's 92):

- `test_desired_service_identity_and_defaults_use_catalog_shape` updated: asserts
  `requirements == {}` and the analysis reasons now live under `analysis_provenance["reasons"]`.
- `test_desired_service_update_fields_excludes_operator_owned_fields` — pins the six excluded
  keys by name.
- `test_analysis_provenance_defaults_rejects_unknown_keys`.
- `test_plan_dependency_sync_creates_updates_deletes_and_preserves_unchanged` — one call
  exercising create + update (changed `raw_ref`) + delete (removed key) together.
- `test_plan_dependency_sync_identical_reanalysis_is_fully_unchanged` — every key lands in
  `unchanged_keys`, nothing else.
- `test_plan_dependency_sync_update_never_touches_notes_or_resolution` — asserts the `update`
  entry shape is exactly `{key, raw_ref, dependency_type}`, structurally proving
  `notes`/`resolution_status`/`resolved_service` can't leak into a write.
- `test_plan_dependency_sync_rejects_duplicate_incoming_keys`.

**Deliberately not covered locally** (per the same Django-free local-suite limitation recorded in
`report4.2.md`): "injected mid-transaction failure" rolling back both the service update and
dependency writes together. `transaction.atomic()` is standard Django behavior, not new logic
this step wrote, but proving the transaction boundary actually rolls back both writes together
needs a real Postgres-backed Nautobot — Step 4.7's mixed-node integration matrix or Step 4.8's
live verification is where this gets exercised, not a local pytest.

`test_operations_hosts.py`/`test_importers.py`'s pre-existing `placement_policy` /
`desired_service_defaults` references from Step 4.2 remain as fixed then; no further changes
needed to those tests here.

## Result

No blocking surprise. All six sub-items landed; local suite green at 98 tests (92 + 6 new). The
one real judgment call — freezing `lifecycle`/`notes`/`name`/`slug`/`display_name` on update, not
just `requirements` — is documented above and in `importers.py`'s docstrings so it's easy to
revisit if that reading turns out too broad once live re-analysis runs are observed at Step 4.8.
Step 4.4 (nctl GraphQL/report-3.0 cutover) is next; it is the step that finally removes
`placement_policy` from nctl's `DESIRED_QUERY`/typed snapshot, completing the coordinated schema
break this nintent batch started.
