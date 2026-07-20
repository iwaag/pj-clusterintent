# Verification report

## Full suite

`uv run pytest -q` (nctl) — **518 passed**, 0 failed.

## Live replay against dev Nautobot

Ran `NAUTOBOT_TOKEN=... uv run nctl reconcile agdnsmasq --yes --json` against the local dev
Nautobot instance (`http://localhost:8000`, containers already running).

Note: the exact reproduction state from the plan doc (`dnsmasq` service in
`service_observation_missing`) no longer exists live — `nctl drift` now reports the `dnsmasq`
service target as `service_missing` instead, meaning the service's observation gap was
already resolved by evidence gathered during the original bug investigation (per
`report6.md`'s follow-up conversation, referenced in `plan.md`). This is expected drift in
long-lived environment state between then and now, not a surprise requiring a decision — no
`service_observation_missing`/`service_observation_stale`/`service_observed_facts_unknown`
diff was available to reproduce the original failing batch live.

What was confirmed instead, across a full 3-round `--yes` run:
- No `observe_node` action failed, and grepping the full JSON result for
  `"bootstrap-eligible"` and `"observe_node"` failures found zero occurrences.
- `reconcile_ipam` and `regenerate_production_inventory` continue to succeed each round, as
  before.
- The only failing action was `dnsmasq_config` (`dnsmasq_inventory_group_empty` — the
  generated inventory has no hosts in the `dnsmasq_server` group), which is unrelated to this
  fix: it's a downstream deployment-inventory content issue, not an `observe_node`/target-kind
  batching problem.

Combined with the new planner tests (Step 1) directly exercising the
`service_observation_missing` → node-target-resolution path, and the new executor test (Step
2) confirming `run_observation` only ever receives node slugs for a service-kind evidence-gap
diff, the fix is verified: the `observe_node` action reconciler_id given a service-kind
OBSERVATION diff resolves to the owning node, and — per the exit criteria — no code path can
reach `run_observation` with a service slug anymore.

## Exit criteria check

- `nctl reconcile --yes` no longer fails `observe_node` for a service-kind evidence-gap diff:
  verified by test (Step 1 planner test + Step 2 executor test); live confirmation limited by
  current environment state as noted above, but no regression or new failure mode observed.
- Node-kind and service-kind evidence gaps on the same node dedupe into one target: verified
  by `test_observe_node_resolves_service_target_to_owning_node`.
- No change to `classify.py`'s classification table: confirmed — `classify.py` was not
  touched; only `planner.py`'s `OBSERVATION` branch changed.
