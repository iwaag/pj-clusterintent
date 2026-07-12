# Step 6 Report: Deterministic Production Inventory Composition

## Summary

Completed Step 6. Added a pure, Nautobot-independent composition module
`nintent/nautobot_intent_catalog/production_inventory.py` that joins desired nodes, placements,
operational configs, realized objects, allowlisted actual facts, and the deployment-profile map into
a schema `1.0` production inventory document plus a structured companion report. The composer reuses
the Step 1 contract primitives (`production_inventory_contract.py`) and the Step 5 actual-fact reader
(`actual_facts.py`), and it runs both contract validators on its own output so it fails closed if it
ever produced a non-conforming document.

The Nautobot Job and Ansible workflow that drive this composer are intentionally **not** part of this
step; they are Step 7. Step 6 is the pure engine and its tests.

## Status of plan items

| # | Item | Outcome |
|---|------|---------|
| 1 | Pure composition module, no Nautobot Job deps | `production_inventory.py`, no Django import; returns inventory + report |
| 2 | Select approved/active nodes; fail if any lacks exactly one operational config | `is_production_eligible`; `missing_operational_config` global error |
| 3 | Join actual-backed nodes to realized Device; validate freshness + consumer-required facts | `_host_actual_skip_reasons` via `actual_type_problem`/`actual_state_problem`/`missing_required_facts` |
| 4 | Compose declared HAOS from typed settings + endpoints, no realized object/nodeutils | declared path skips actual checks; connection from `local_endpoint` |
| 5 | Service groups from deployment profiles, never observed services | service membership only from active placements + profile group |
| 6 | linux/macos selectors from normalized observed system; haos from declared | selector group keyed by `evaluate_platform_policy` host_os |
| 7 | Drift vs `expected_host_os` without using expected for host_os/selectors | host_os and selectors come from observed; expected only feeds drift |
| 8 | `host_os: haos` only for declared HAOS; validate platform/power combos | declared path returns haos; `evaluate_platform_policy` validates power |
| 9 | Resolve local/Tailscale connection vars per contract | `resolve_connection_variables`; `ansible_host` stripped (resolved in group_vars/all) |
| 10 | Map only declared, type-valid placement config keys to audited Ansible vars | `map_placement_config` per active placement |
| 11 | Global-failure/host-skip taxonomy; no dangling group members for skipped hosts | skip records reasons; skipped hosts' placements counted inactive, never grouped |
| 12 | Detect conflicting host variable assignments, fail deterministically | `merge_host_variables` over base + placement assignments |
| 13 | Deterministic ordering + schema-versioned YAML/JSON renderers | sorted members/keys; `render_production_inventory_yml` / `render_production_report_json` |
| 14 | Unit tests covering joins, HAOS, Device-only, skips, global failures, determinism, multiplicity | `test_production_inventory.py`, 20 tests |

## Changes

### nintent/nautobot_intent_catalog/production_inventory.py (new)

- Input dataclasses (`EndpointInput`, `OperationalConfigInput`, `PlacementInput`, `RealizedState`,
  `NodeInput`) describe exactly what the Step 7 Job will assemble from Django models, so the engine
  stays pure and unit-testable without a Nautobot runtime.
- `is_production_eligible`: `approved`/`active` lifecycle and an exportable node type
  (`device`/`virtual_machine`/`service_host`; containers and `planned` nodes are out of scope, not
  skipped). The actual-backed vs declared decision is made by the operational config policy, not the
  node type.
- `compose_production_inventory`:
  - validates the deployment-profile map up front (global failure on a bad map);
  - iterates eligible nodes sorted by slug for determinism;
  - raises `missing_operational_config` (global) when an eligible node has no operational config;
  - skips actual-backed hosts with structured reasons (`no_realized_device`,
    `unsupported_actual_type`, `stale_actual_data`/`missing_actual_data`,
    `missing_observed_system`/`missing_mac_address`) and leaves declared HAOS exempt from actual
    checks;
  - builds ssh_hosts host vars, OS selector groups, `power_managed`, and service groups; service
    membership comes only from active placements and the profile group;
  - merges base host vars with each active placement's mapped, type-validated config through
    `merge_host_variables`, so a conflicting assignment is a deterministic global failure;
  - records drift (`desired_actual_os_mismatch`) with node context without letting the expected OS
    drive host_os or selectors;
  - emits a schema `1.0` report with `eligible/included/skipped/placements/active_placements/
    inactive_placements` and `hosts/skipped/drift/errors`;
  - runs `validate_production_inventory_document` and `validate_production_report` on its output as a
    fail-closed self-check.
- `render_production_inventory_yml` / `render_production_report_json`: deterministic, schema-versioned
  YAML and JSON (sorted keys, sorted members).

Design notes:
- `ansible_host` is intentionally not a per-host variable (it is not in the contract's allowed host
  variable set); the composer exports the raw connection components and leaves `ansible_host`
  resolution to generated `group_vars/all/main.yml` per the connection contract.
- `network_interface` is exported when present but not required per host; only `host_os`
  (observed_system) and, for WOL nodes, `mac_address` are consumer-required, honoring "do not require
  every allowlisted field on every host."

### nintent/nautobot_intent_catalog/tests/test_production_inventory.py (new)

- 20 tests across actual-backed joins, observed-vs-expected selectors and drift, WOL/`power_managed`,
  Tailscale connection, declared HAOS without a realized object, the full skip taxonomy (no device,
  VM, stale data, missing WOL MAC), global failures (missing operational config, invalid
  platform/power, conflicting placement variables, unknown profile), multiple services on one node,
  multiple instances of one service, disabled placements, eligibility scoping, byte-stable output, and
  schema-versioned parseable renderers.

## Verification

- `python3 -m unittest nautobot_intent_catalog.tests.test_production_inventory` — 20 tests pass.
- Full nintent suite: 170 tests pass (was 150 after Step 5; +20 here).
- `python3 -m py_compile production_inventory.py` — OK.
- No execution environment is available, so there is no live Nautobot Job run; the composer is pure
  and fully exercised by unit tests, and it self-validates its output against the contract.

## Exit Criterion Status

Met. Identical input (nodes + profile map + generation metadata) produces byte-stable YAML and JSON
output (`test_output_is_byte_stable`), and unsupported or ambiguous state fails closed: global
contract violations raise `ContractError` and abort, while host-specific actual-state problems skip
only the affected host with structured reason codes and never leave dangling group membership.

## Notes

- The composer consumes `evaluate_platform_policy`, `resolve_connection_variables`,
  `map_placement_config`, `merge_host_variables`, `actual_state_problem`, and the
  inventory/report validators from `production_inventory_contract.py` (Step 1), plus
  `read_actual_facts`/`actual_type_problem`/`missing_required_facts` from `actual_facts.py` (Step 5).
  Normalization and freshness logic were not re-implemented.
- Step 7 will add the Nautobot Job that fetches desired nodes/placements/operational configs/realized
  Devices, calls `read_actual_facts` on each realized Device, builds the `NodeInput` list, invokes
  `compose_production_inventory`, and publishes the rendered `production.yml` plus the JSON report.
- The companion report's `errors` array is always empty on the success path because every global
  contract violation raises and aborts the job (fail closed); non-fatal host issues are reported in
  `skipped`/`drift`.
