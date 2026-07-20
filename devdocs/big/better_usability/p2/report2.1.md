# Phase 2 Step 2.1 — Baselines and executable contracts

Parent: [plan.md](plan.md), Step 2.1.

## Baselines

- nintent local unit suite, run from `nintent/`:
  `uv run python -m unittest discover -s nautobot_intent_catalog/tests -p 'test_*.py'` —
  **88 passed**.
- nctl full suite:
  `uv run --project nctl pytest -q nctl/tests` — **569 passed**, with the one pre-existing
  `StarletteDeprecationWarning` from `test_serve_ws.py`.
- Read-only live GraphQL query against the configured development Nautobot:
  `desired_node_operational_configs` count — **0**. No credentials, row identifiers, or actual
  facts were recorded.

The plan's abbreviated pytest commands are not safe baselines when launched without their target
paths: nintent has no pytest development dependency, and root-level pytest collection also finds
nodeutils. The commands above are the established Phase 0/1 invocations and measure the intended
88-test and 569-test suites exactly.

## Executable derivation contract

Added `nctl_core.production.derivation`, a pure resolver with no Nautobot or wall-clock access. Its
table-driven tests freeze the Phase 0 matrix before the GraphQL/model cutover:

- fresh Linux and Darwin normalization plus the exact closed value/source/reference/
  `override_won` record;
- single endpoint and unique-primary selection;
- zero endpoint and ambiguous endpoint failures, including deterministic evidence ordering;
- declared HAOS and forced Tailscale precedence;
- missing, invalid-timestamp, stale, and unsupported observation failures; and
- explicit records for absent Ansible port and safe power/laptop defaults.

The resolver can now emit `missing_connection_endpoint` and
`ambiguous_connection_endpoints`. Both joined the shared classifier/blocker vocabulary in the
same nctl commit; classification and planner coverage therefore remain fail-closed. Focused
resolver/classifier/planner result: **63 passed**.

## Objective old-surface deletion inventory

The pre-change `rg` sweep found the old model/root/list/output field or dead mechanism vocabulary
in these live source/test/seed/doc files. Phase 2's final sweep must remove the applicable runtime
occurrences; the historical migration remains intentionally:

### nintent

- `nautobot_intent_catalog/models.py`, `forms.py`, `filters.py`, `tables.py`, `views.py`, `urls.py`
- `nautobot_intent_catalog/loaders.py`, `importers.py`, `jobs.py`
- `nautobot_intent_catalog/templates/nautobot_intent_catalog/source_yaml_list.html`
- `nautobot_intent_catalog/tests/test_loaders.py`, `test_importers.py`
- `README.md`, `CONCEPT.md`
- retained history only: `nautobot_intent_catalog/migrations/0004_service_placement_operational_config.py`

### nctl

- `src/nctl_core/sources/desired.py`
- `src/nctl_core/production/adapter.py`, `composer.py`, `contract.py`
- `src/nctl_core/drift/comparators.py`, `evaluation_snapshot.py`, `service_placement.py`
- `src/nctl_core/reconcile/classify.py`, `planner.py`, `executor.py`, `fingerprint.py`
- tests: `test_sources_desired.py`, `test_sources_snapshot.py`, `test_production_adapter.py`,
  `test_production_composer.py`, `test_production_contract.py`, `test_dnsmasq_render.py`,
  `test_drift_comparators.py`, `test_drift_engine.py`, `test_drift_evaluation_snapshot.py`,
  `test_drift_render.py`, `test_drift_status.py`, `test_service_placement.py`,
  `test_reconcile_classify.py`, `test_reconcile_planner.py`, `test_reconcile_executor.py`

### nauto

- `seed/intent_sources.yaml`

## Result

No blocking surprise was found: the live zero-row migration precondition holds and both baselines
match the plan. No live state was mutated. The resolver contract is executable before any source
shape changes, and the new error codes cannot reach reconcile unclassified.
