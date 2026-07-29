# Phase 1 Step 1 Report — Schema Reduction

## Result

Complete. nintent now uses the Phase 0 reduced desired-state schema. Migration
`0019_reduce_desired_state_schema` removes every field assigned to removal,
including analysis/provenance fields and realized-link source fields. The
read-only UI, filters, serializers, templates, loader input, canonical seed,
and Django-free coverage were reduced with the models.

The obsolete Analyze Intent Sources Job and its analysis modules were removed;
`DesiredDependency` remains a model and will be handled as a first-class batch
kind in the following steps. Compute provider/schema discriminators are no
longer persisted on platforms or instances; their fixed Proxmox/v1 contract
continues to be owned by `compute_contract.py`.

## Verification

- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — passed: 133 tests, 14 expected skips.
- `python3 -m compileall -q nintent/nautobot_intent_catalog` — passed.
- `git diff --check` — passed before commit.

The migration is intentionally not applied to the local Nautobot scratch
database in this step: the required clean runtime migration gate is the Phase
1 final verification gate.
