# Phase 2 Step 2.2 — nintent schema and writer batch

Parent: [plan.md](plan.md), Step 2.2.

## Schema cutover

- Added optional one-to-one `DesiredNodeOperationalOverride` with only genuine exception fields:
  declared HAOS, forced path/endpoints, Ansible port, power behavior, and laptop behavior.
- Deleted the runtime `DesiredNodeOperationalConfig` model, constraint, form/filter/table/views,
  URLs/reverse names, navigation item, detail template, GraphQL model registration, YAML/import
  helpers, and Job counters. No alias or dual surface was retained.
- Override validation rejects empty/no-op rows, incomplete Tailscale pairs, cross-node endpoints,
  unusable forced endpoints, incompatible local/Tailscale combinations, unsafe HAOS power, and
  out-of-range Ansible ports.

Migration `0010_operational_overrides_and_provenance` performs the coordinated transition:

1. add nullable source metadata fields;
2. create the override model;
3. abort before deletion if any old operational-config row exists;
4. conservatively backfill existing names as `intent` and existing realized links as `override`;
5. delete the old model.

The reverse migration recreates the historical old table through Django's normal `DeleteModel`
reverse operation and clears source fields before removing them. It intentionally does not invent
an override-to-old-config converter.

## Provenance writers

- Quick Add records explicit DNS/mDNS as `intent` and generated names as `derived`.
- Strict YAML import records explicit names as `intent` and importer-generated names as `derived`.
- Regular node/endpoint forms stamp manual realized-link changes `override`, and clear source when
  the value is cleared. Source fields remain hidden from normal forms.
- REST serializers expose validated source metadata. A relationship/name write without an
  automation source becomes `override`/`intent`; an atomic write may explicitly state `derived`;
  null values clear source. Value/source presence must always agree.
- `ReconcileDesiredIPAMIntent` now writes `realized_ip_address` and
  `realized_ip_address_source=derived` atomically in both create-and-link and link-existing paths.

## YAML, UI, and current docs

- The strict root is `desired_node_operational_overrides`; the old root is rejected explicitly.
- Only `desired_node` is structurally required. Safe default keys (`power_control`, `is_laptop`)
  may be omitted, while a document containing no meaningful override is rejected.
- Nautobot CRUD and DesiredNode detail now present "Operational Override" as an optional exception,
  including an add link when none exists.
- `nintent/README.md` and `nintent/CONCEPT.md` describe derivation as the common path and the new
  override-only contract.

The nauto seed remains unchanged in this step, as assigned to Step 2.6. The running Nautobot image
also remains unchanged, per the coordinated rollout rule.

## Verification

- `uv run python -m unittest discover -s nautobot_intent_catalog/tests -p 'test_*.py'` —
  **89 passed** (88 baseline + one strict-old-root test).
- `uv run python -m compileall -q nautobot_intent_catalog` — passed.
- Django 4.2 migration-module import/dependency/operation-count check — passed; dependency is
  `0009_reconciliation_status` and the migration contains eight operations.
- `git diff --check` — passed.

No live migration, rebuild, REST write, or data mutation was performed. The pre-deployment old-row
assertion remains zero from Step 2.1 and will be repeated immediately before Step 2.8 migration.
