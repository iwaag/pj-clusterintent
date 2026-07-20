# Step 2 report — regression test at the executor/observation boundary

## Test added (`nctl/tests/test_reconcile_executor.py`)

`test_observe_node_action_only_receives_node_slugs_for_service_diffs` — drives
`run_reconcile` end to end (through `_execute_action` → `_run_observation_action` →
`run_observation`) with a `service_observation_missing` diff whose target is
`kind="service", slug="dnsmasq"` and `desired.expected.node_slug == "agdnsmasq"`. Stubs
`run_observation` to capture the `target_slugs` it's called with and asserts the list is
exactly `["agdnsmasq"]` — never `"dnsmasq"` — and that the resulting action succeeds. This
exercises `executor.py:355`'s `target_slugs = [t.slug for t in action.targets if t.slug]`
against the planner's now-resolved node target, closing the gap the plan noted: no existing
test drove a service-kind evidence-gap diff through the executor at all.

## Result

`uv run pytest -q tests/test_reconcile_executor.py -k observe_node_action` — 1 passed.

Full suite: `uv run pytest -q` — 518 passed (up from 514 before Steps 1–2; +3 planner tests,
+1 executor test).
