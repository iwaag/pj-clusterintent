# Phase 1 Step 1.3 — Report active placements deferred by lifecycle

Parent: [plan.md](plan.md) Step 1.3.

## What changed

`production/composer.py`:

- `compose_production_inventory` now materializes `nodes` into `all_nodes` once (it was previously
  consumed only by the `eligible` filter), so the full unfiltered node list is available for the
  new lifecycle check.
- Added `unapplied_placement_findings(nodes)`: a pure helper, independent of `compose_production_inventory`
  and deployment profiles. For every node whose `node_type` is production-capable but whose
  `lifecycle` is not in `PRODUCTION_ELIGIBLE_LIFECYCLES`, it emits one `active_placement_not_applied`
  entry per `desired_state="active"` placement, sorted by `(node.slug, placement.instance_name,
  placement.id)`. Evidence: `desired_node*`, `node_lifecycle`, `eligible_lifecycles` (sorted), and
  the full placement (`id`, `instance_name`, `deployment_profile`, `config_schema_version`,
  `desired_state`, `config` verbatim — including `{}`).
- `compose_production_inventory` appends `unapplied_placement_findings(all_nodes)` into
  `report["drift"]` before final sorting. Existing `eligible`/`included`/`active_placements`/
  `inactive_placements` counters are untouched — the drift array is the only new visibility
  surface, per the plan's explicit instruction not to redefine old counters.
- A container/other node-type-ineligible node does not gain this code merely because it's also
  lifecycle-ineligible — the helper checks `node_type` first and skips entirely if that's the
  actual reason for exclusion (Phase 1 is scoped to the lifecycle gate only).
- A `disabled` (or any non-`active`) placement on an ineligible node produces no finding — only
  recorded *active* intent that silently fails to apply is in scope.

## Tests added (`test_production_composer.py`)

- `test_active_placement_on_ineligible_lifecycle_emits_finding` (parameterized over `planned`,
  `deprecated`, `retired`).
- `test_disabled_placement_on_ineligible_node_produces_no_finding`.
- `test_empty_config_is_still_evidence_for_unapplied_placement` — confirms `config == {}}` still
  produces a finding (the roadmap's flagship dnsmasq-loopback example).
- `test_multiple_placements_on_one_ineligible_node_each_get_a_finding`.
- `test_production_eligible_control_node_gets_no_unapplied_finding`.
- `test_node_type_only_ineligibility_does_not_gain_the_lifecycle_code`.
- `test_unapplied_placement_findings_helper_is_deterministically_ordered`.
- `test_unapplied_placement_findings_does_not_touch_profiles` — confirms the helper never raises
  even for a profile name that doesn't exist anywhere, since it never validates against one.

## Test count

```
uv run --project nctl pytest -q nctl/tests
```

Result: **550 passed** (540 baseline after Steps 1.1-1.2 + 10 new Step 1.3 tests), 1 unrelated
pre-existing warning.

## Note

This step landed in the same working session as Step 1.4 (`report1.4.md`) and both are committed
together: the composer already feeds `report["drift"]` straight into
`drift/comparators.py::production_policy`, which — before Step 1.4's changes — converts every
`report["drift"]` entry using the OS-mismatch-specific message template regardless of code. Landing
Step 1.3 alone would have silently rendered `active_placement_not_applied` findings with a
nonsensical `"expected None, observed None"` message the first time a real `planned`/`deprecated`
node with an active placement flowed through `nctl drift`. See `report1.4.md`'s "why classification/
dispatch was added in this commit" note.
