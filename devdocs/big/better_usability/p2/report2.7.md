# Phase 2 Step 2.7 — Full scenario and orchestration matrix

Parent: [plan.md](plan.md), Step 2.7.

## Matrix result

The combined resolver/composer/drift/reconcile tests cover the required matrix:

- fresh observed Linux and Darwin, unique endpoint and unique-primary selection, and exact
  required/derived provenance;
- missing and ambiguous endpoints as node-local failures, each paired with a healthy neighbor
  whose inventory output remains unchanged;
- missing/stale/invalid actual evidence, unsupported actual type/OS, and no guessed platform;
- declared HAOS, forced local and Tailscale endpoints, invalid incomplete overrides, non-default
  port, WOL, macOS sleep, laptop, and safe defaults;
- every declared local composition code paired with a healthy node, plus cluster/host reconcile
  isolation for an ambiguous endpoint;
- schema 1.0 rejection, strict schema 2.0 output, and old YAML-root rejection.

The matrix review found two details that needed explicit closure:

1. Drift provenance now carries a deterministic endpoint `source_summary`, so when a forced local
   override wins, the selected endpoint and the alternate automatically eligible candidate remain
   visible without changing the closed operational value records.
2. Reconcile executor host grouping now receives the plan/drift operation timestamp explicitly;
   a test pins that exact value at the shared resolver boundary instead of relying on a nearby
   snapshot timestamp.

## Regression results

- Focused nintent loader/import/writer/template suite: **72 passed**.
- Full nintent suite: **89 passed**.
- Focused nctl source/production/drift/dashboard/reconcile/compatibility suite: **225 passed**.
- Full nctl suite: **587 passed**, with one pre-existing Starlette/httpx deprecation warning.
- `python -m compileall -q src` and `git diff --check` passed.

All executor tests used fakes. No ledger write, Job trigger, rebuild, Ansible actuation, live import,
or generated artifact write occurred.

## No-artifact sweep

Across current nintent/nctl runtime and the nauto seed, excluding migration history and bytecode,
there are no occurrences of:

- `DesiredNodeOperationalConfig` or the typed `operational_configs` list;
- `expected_host_os`, `desired_actual_os_mismatch`, or `service_placement_os_mismatch`;
- `nintent_operational_config_id`; or
- `PHASE1_LOCAL_CODES`.

The only four current-code occurrences of `desired_node_operational_configs` are the strict loader
rejection branch and its test. This is intentional rejection, not a compatibility reader or shim.
`PRODUCTION_INVENTORY_SCHEMA_VERSION` is `2.0`; no runtime 1.0 producer remains.
