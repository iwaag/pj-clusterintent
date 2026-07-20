# Phase 4 Step 4.4 — Cut nctl to the reduced GraphQL shape and report schema 3.0

Parent: [plan.md](plan.md), Step 4.4.

## 1. `placement_policy` removed from GraphQL query, typed models, builders, evaluation facts

`sources/desired.py`: `placement_policy` removed from `DESIRED_QUERY`'s `desired_services`
selection, the `DesiredService` typed model, and `_build_service`. `drift/evaluation.py`'s
`_expected_service_facts` no longer includes a `placement_policy` key. Test fixtures
(`test_sources_desired.py`, `test_drift_render.py`, `test_drift_evaluation.py`) updated to match
— no dual shape accepted anywhere; a query still asking Nautobot for the removed GraphQL field
would simply fail against the new nintent schema, which is the intended coordinated break.

## 2. Typed node/placement input enrichment

`production/composer.py`:

- `NodeInput` gained `role: str | None` and `accepted_actual_types: tuple[str, ...]`.
- `PlacementInput` gained `service_id`, `service_slug`, `instance_role`, `assignment_source`,
  `endpoint_id` — the "service identity and assignment source" the plan calls for.
- New `ACCEPTED_ACTUAL_TYPE_DEFAULTS` + `accepted_actual_types_source(node_type,
  accepted_actual_types)` — the same per-node-type mapping as nintent's
  `operations.hosts._accepted_actual_types` and `loaders._ACTUAL_TYPE_DEFAULTS` (Phase 4
  Decision 4's "no new provenance field is needed" rule), returning `"derived"` when the stored
  list matches the canonical mapping and `"override"` otherwise.

`production/adapter.py`: `build_production_node_inputs` now indexes `snapshot.desired.services`
by id and passes `role`/`accepted_actual_types` through on `NodeInput`, and resolves
`service_slug`/`instance_role`/`assignment_source`/`endpoint_id` onto each `PlacementInput`.

## 3. Split inventory/report version constants

`production/contract.py`: `PRODUCTION_REPORT_SCHEMA_VERSION = "3.0"` added, independent of
`PRODUCTION_INVENTORY_SCHEMA_VERSION` (still `"2.0"`, unchanged). `nctl.render.production.v1`'s
envelope is untouched. `_validate_generation_metadata` split into a schema-agnostic
`_validate_generation_id_and_timing` shared by both the inventory-document and report validators,
so the two schema-version checks can never drift onto the wrong constant.

## 4–5. Report `3.0`'s closed `nodes` collection; exact-shape validation

`production/contract.py`: `validate_production_report_v3` replaces `validate_production_report`
(no dual shape). Closed node-record shape per Decision 2:
`desired.node` (id/slug/name/lifecycle/node_type/role/accepted_actual_types/
accepted_actual_types_source), `desired.endpoints`, `desired.placements` (service identity +
assignment source + endpoint reference), `desired.operational_override`; `actual.operational_values`
(same `{value, source, source_reference, override_won}` value-record contract, reused unchanged),
`actual.operational_finding`, **`actual.local_findings`** (added beyond Decision 2's literal JSON
example — Decision 3's own prose separately requires "structured local findings with code,
severity, message, stage, and bounded evidence" per node, which the example JSON doesn't show;
implemented as a list, closed keys `{code, severity, message, stage, evidence}`), and
`actual.production` (`state` ∈ `included`/`skipped`/`out_of_scope`/`unknown` — composer never
emits `unknown`, reserved for a future non-composer producer; `reasons`; `placement_effects` with
`effect` ∈ `applied`/`inactive_by_intent`/`not_applied` and a `reason`).

Validation rejects: schema `2.0` (`unsupported_report_schema`), partial/missing-key node records
(`invalid_contract_keys`), duplicate node or placement IDs across the whole report
(`duplicate_node_id`/`duplicate_placement_id`), an unknown `placement_id` in `placement_effects`
(`placement_effect_unknown_placement`), a missing effect for a desired placement, and — the
"placement effects contradicting node state" requirement — an `included` node reporting
`not_applied` (`placement_effect_contradicts_node_state`; an included node's own composition
either applies an active placement or the node isn't included at all, so this combination can
only mean a producer bug).

`production/composer.py`'s `compose_production_inventory` rewritten:

- The Ansible inventory document is still built by the **same eligible-node loop, unchanged**,
  for byte-stability (confirmed: `test_output_is_byte_stable` and
  `test_group_c_output_is_byte_stable_across_runs` still pass unmodified).
- Report building is a **separate translation pass**: each node's composition result is captured
  in a `_NodeOutcome` (state/reasons/effective values/finding/active ids), independent of the
  inventory-building local variables, then `_node_report_record` turns every `_NodeOutcome` into
  one closed node record. This isolates the new report shape from the delicate byte-stable
  inventory path by construction, not by convention.
- Operational mechanism (`resolve_operational_values`) is now computed for **every** desired node,
  including out-of-scope ones — Principle 3 ("a value the system infers must be visible") applies
  regardless of whether the node can currently act on it, which is new: the old composer only ever
  called this for eligible nodes.
- Summary gained `out_of_scope`, `applied_placements`, `not_applied_placements`; `eligible`/
  `included`/`skipped`/`placements`/`active_placements`/`inactive_placements` retained with the
  same meaning.
- The old `hosts`/`skipped`/`drift`/`errors` collections and their builder helpers
  (`_local_skip_entry`, `_local_error_entry`, `_error_sort_key`) are deleted, not kept alongside
  the new shape.

**Necessary plumbing fix beyond this step's literal item list**: `drift/comparators.py`'s
`production_policy` read `composition.report["errors"]`/`["skipped"]`/`["drift"]` directly and
would have crashed (`KeyError`) the instant the composer's report shape changed — this isn't
optional deferral to Step 4.5, it's a hard coupling this step's own change breaks immediately.
Fixed with the minimum viable translation: `local_findings` → the same node-targeted ERROR diffs
as before, `production.state == "skipped"` → the same generic skip-reason diffs (still
deduplicated against structured-error `(slug, code)` pairs), and `active_placement_not_applied`
now always comes from the pure, composer-independent `unapplied_placement_findings(node_inputs)`
(previously only used in the no-profiles branch) rather than reading it back out of the composer's
`report["drift"]`. This is plumbing to keep nctl functional, not Step 4.5's drift
text/dashboard/`intent_effect_summary`-rename work, which is untouched here — the `derived_value_
provenance` code and old rendering are exactly as they were.

**Design divergence, called out explicitly**: report 3.0's own `not_applied`/`node_out_of_scope`
now covers *every* out-of-scope reason (lifecycle **and** node_type), broader than
`unapplied_placement_findings`'s narrower lifecycle-only scope (kept as-is, still feeding the
existing `active_placement_not_applied` drift code per its own documented contract). A container
node is out of production scope either way; the report's job is to represent that uniformly per
Decision 2, while the specific drift *code* stays scoped to what Phase 1 already classified. Test
`test_node_type_only_ineligibility_is_out_of_scope_in_the_report` pins both halves of this
explicitly so the distinction can't silently blur back together.

## 6. Tests

Full nctl suite: **610 passed**, 3 still-failing (unchanged from Step 4.1, correctly deferred to
Step 4.5): the `intent_effect_summary` rename and both `deployment_profiles_unavailable`
contracts. `test_production_composer.py` (54 tests, up from 51) and `test_production_contract.py`
(9 tests) cover: every lifecycle/node-type scope combination (included/skipped/out_of_scope),
successful and failing derivation, every Group C later-stage local-composition code (parametrized
matrix, now asserted via `local_findings`/`skip_reasons` helpers instead of the old report keys),
active vs. disabled placements, mixed good+bad nodes (byte-identical healthy output beside a
failing neighbor), `accepted_actual_types_source` derived/override in isolation and inside a full
report node record, placement service-identity/assignment-source projection, and the
no-profiles path (unchanged, still degrades to `{}` per Step 4.5's own not-yet-landed
`deployment_profiles_unavailable` work). Contract tests cover the full v3 shape plus every
rejection path named in item 5 above.

Two test-fixture placement-ID collisions (`"p1"` reused across unrelated nodes in six Group C
`_bad_*` builders) surfaced by the new cross-report `duplicate_placement_id` check were fixed by
giving each bad-node fixture its own IDs — a fixture-hygiene fix the new validator's correctness
requires, not a design change.

## Result

No blocking surprise. All six sub-items landed; nctl suite green apart from the two contract tests
deliberately deferred to Step 4.5 (drift/dashboard/reconcile consolidation), which is next.
