# Phase 2 Step 2.6 — Seed data and current documentation

Parent: [plan.md](plan.md), Step 2.6.

## Seed cutover

`nauto/seed/intent_sources.yaml` now uses the strict
`desired_node_operational_overrides` root. The former nine mandatory rows became six genuine
exception rows:

- `agmbp2019` and `agmbp2018`: WOL and laptop overrides;
- `agpc`: WOL override;
- `agstudio`: macOS sleep override;
- `agbach`: macOS sleep and laptop overrides; and
- `aghaos`: declared HAOS plus non-default Ansible port 2222.

Repeated required/declared policy, expected Linux/macOS, local path, primary endpoint, `none`
power, and false laptop values were removed. `agprometheus`, `aggrafana`, and `agnomad` no longer
materialize no-op rows.

## Current documentation

- `nauto/README.md` now describes optional exceptions, automatic observed Linux/macOS and endpoint
  derivation, and the strict replacement root. This is the short supersession note for the current
  operator-facing seed recipe.
- nintent's current [README.md](../../../../nintent/README.md) and
  [CONCEPT.md](../../../../nintent/CONCEPT.md) contracts were already updated with the model/schema
  batch in Step 2.2 (`b6f4ec0`): both describe optional genuine overrides and reject the old root.
  No additional nintent documentation edit was necessary in this step.
- Historical `devdocs/functions/*` and completed core-reconcile reports were left unchanged. The
  Phase 4 end-user add/register recipe was not pulled forward.

## Verification

The complete seed was loaded twice through nintent's real `load_intent_sources()` loader. Both
results were equal and error-free: **9 nodes, 9 endpoints, 6 placements, 6 overrides**.

The existing real import primitive idempotence test was run separately:
`StrictImportHelperTests.test_validated_upsert_is_idempotent_for_matching_defaults` — **1 passed**.
It confirms a repeated matching upsert returns `unchanged` without validation/save mutation.

`git diff --check` passed. No live import or Nautobot state change was performed.
