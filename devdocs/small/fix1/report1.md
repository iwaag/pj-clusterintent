# Step 1 report — planner resolves service-observation targets to their node

## Change

`nctl/src/nctl_core/reconcile/planner.py`, in `build_plan`'s `OBSERVATION` branch: when a
diff classified `OBSERVATION` has `target.kind == "service"`, the planner now reads
`node_slug` / `node_id` from `diff.desired["expected"]` and substitutes a
`Target(kind="node", slug=node_slug, id=node_id)` before keying/storing it in
`observe_targets`, instead of using the diff's own service target. Node-kind observation
diffs go through unchanged. If a service diff lacks a resolvable `node_slug`, `build_plan`
now raises `ValueError` (treated as a planner defect, matching the design decision — this
shouldn't happen since `evaluate_all_services` always populates it for the service-evidence
codes).

`observe_codes` accumulation was left as-is (code-level, not target-level).

## Tests added (`nctl/tests/test_reconcile_planner.py`)

- `test_observe_node_resolves_service_target_to_owning_node` — a `service_observation_missing`
  diff on a service target plus a node-kind evidence-gap diff for the *same* node collapse
  into one `kind="node"` target (dedup), with both diff codes claimed.
- `test_observe_node_resolves_service_target_alongside_unrelated_node` — a service diff mixed
  with an unrelated node's evidence-gap diff produces two distinct node targets, matching
  today's multi-node aggregation behavior.
- `test_observe_node_raises_when_service_diff_has_no_node_slug` — a service-kind OBSERVATION
  diff missing `desired.expected.node_slug` raises `ValueError` mentioning `node_slug`.

Also added a `_service_observation_diff` test helper alongside the existing `_node_diff` /
`_service_diff` helpers.

## Result

`uv run pytest -q tests/test_reconcile_planner.py` — 18 passed (15 previously existing + 3
new).
