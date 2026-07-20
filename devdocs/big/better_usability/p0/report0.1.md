# Phase 0 — Step 0.1 report: Freeze the model-field inventory

Parent: [plan.md](plan.md) Step 0.1.

## What was done

- Read `nintent/nautobot_intent_catalog/models.py` in full and enumerated all 100 app-declared
  fields across the 8 audited models (`IntentSource` 12, `DesiredService` 21, `DesiredDependency`
  9, `DesiredNode` 14, `DesiredEndpoint` 14, `DesiredServicePlacement` 11,
  `DesiredNodeOperationalConfig` 10, `DesiredIPRange` 9).
- Cross-checked every field against `forms.py`, `filters.py`, `tables.py`, `views.py`, `urls.py`,
  `operations/hosts.py`, `operations/ipam.py`, `api/serializers.py`, `api/views.py`, `api/urls.py`,
  `loaders.py`, `importers.py`, `jobs.py`, `names.py`, `analysis.py`, and the `nauto/seed/*.yaml`
  files, to find hidden-writable, hidden-derived, and REST-exposed-but-form-hidden fields.
- Confirmed the current schema/default and every writer for each field; began the classification
  table (§2 of `field-classification.md`) and the JSON subfield appendix (§3).
- Ran the two documentation/static-check baselines named in the plan's Verification section:
  `uv run --project nctl pytest -q nctl/tests` → **518 passed** (matches plan.md's recorded
  baseline), and the nintent local unit suite via `uv run python -m unittest discover -s
  nautobot_intent_catalog/tests -p "test_*.py"` → **88 passed** (matches plan.md's recorded
  baseline; note the correct invocation needed `uv run`, not a bare `.venv/bin/python`, since the
  checked-in `.venv` lacked PyYAML — this is an environment note, not a code defect).
- Did a read-only live check: GraphQL query against the dev Nautobot confirmed exactly 5
  `DesiredNode` rows, all `lifecycle=PLANNED`, 0 `DesiredNodeOperationalConfig` rows, and exactly
  one `PRIMARY` endpoint per node — matching plan.md's "Current state" section with no surprises.

## Findings surfaced in this step (carried into the table)

- **Three independent, disagreeing defaults for `DesiredNode.node_type`**: model default `device`
  vs. Quick Add form/operation default `virtual_machine` vs. loader default `device`.
- **`DesiredEndpoint.ip_policy`**: model default `static` vs. YAML-import default `external` —
  a silent, path-dependent difference in desired outcome for the same "no input given" case.
- **`DesiredEndpoint.generate_dnsmasq`**: model default `False` vs. Quick Add
  form/operation default `True` (both agree with each other, both disagree with the model).
- **Two Job-managed derived caches on `IntentSource` (`last_import_status`,
  `last_import_summary`) are exposed as editable in `IntentSourceForm`**, while the third
  (`last_imported_at`) is correctly excluded — a hand-edit footgun analogous to discussion.md's
  Example 1 (a value that looks live but is silently overwritten). `DesiredNode`/`DesiredService`
  reconciliation-cache fields do **not** have this problem — they are correctly absent from their
  forms.
- **`DesiredService.placement_policy` is round-tripped end-to-end (GraphQL → typed snapshot →
  `_expected_service_facts`) but never read again anywhere in `drift/`/`reconcile/`**, and every
  current creation path hard-codes it to `{}` — a vestigial/unconsumed field.
- **`DesiredNodeOperationalConfig` has zero live rows and no creation path other than hand-filling
  the form or authoring YAML** — confirms discussion.md Example 3 exactly as described.
- No blocking surprises. Nothing here required stopping for human judgment; all findings are
  carried forward into later steps as planned (tier assignment in 0.3, derivation rules in 0.4,
  phase ownership in 0.7).

## Next step

Step 0.2 — inventory every writer/default in more structured form as the reader/writer matrix
(§5), including conflicting-default call-outs already surfaced above.
