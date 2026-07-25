# Phase 2 Report — Step 1 (Typed three-source fetch layer)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 1.

## What was built

New package `nctl/src/nctl_core/sources/`:

- `desired.py` — one pinned GraphQL query (`DESIRED_QUERY`) fetching nodes, endpoints, IP
  ranges, operational configs (with their `local_endpoint`/`tailscale_endpoint` relations),
  service placements, services, and dependencies in a single round trip. Pydantic read-models
  (`DesiredNode`, `DesiredEndpoint`, `DesiredIPRange`, `DesiredNodeOperationalConfig` +
  `DesiredEndpointRef`, `DesiredServicePlacement`, `DesiredService`, `DesiredDependency`,
  bundled as `DesiredSnapshot`). Choice fields (`lifecycle`, `node_type`, `endpoint_type`,
  `ip_policy`, `dnsmasq_record_type`, `range_policy`, `actual_state_policy`,
  `expected_host_os`/`declared_host_os`, `connection_path`, `power_control`, `desired_state`,
  `assignment_source`, `service_type`, `resolution_status`) are lowercased on the way in, same
  pattern as `dnsmasq_query.py`. This is a superset of that module's desired-side fetch; Step 4
  switches `render dnsmasq` onto it.
- `actual.py` — `ActualFacts`, `read_actual_facts`, `actual_type_problem`,
  `missing_required_facts`, `ACTUAL_FACT_FIELDS`, `REQUIRED_FACT_BY_CONSUMER`,
  `SUPPORTED_REALIZED_TYPE` ported **unchanged** from nintent's `actual_facts.py`. New
  `ACTUAL_QUERY` fetches devices (`_custom_field_data`), virtual machines, interfaces
  (name/mac/device), and IP addresses (host/mask/interfaces) in one request, adapted into
  `ActualDevice`/`ActualVirtualMachine`/`ActualInterface`/`ActualIPAddress`, bundled as
  `ActualSnapshot`. `ActualDevice.actual_facts()` calls the ported `read_actual_facts` directly.
- `observed.py` — `ObservedFacts` + `read_observed_facts(dump: NodeDump)`, the typing `dumps.py`
  deferred to this phase. Reads `facts.system`, `facts.network.primary_mac_address`,
  `facts.network.primary_ip_address`, `facts.network.primary_interface.name` — the same shape
  nauto's `ingest_nodeutils_inventory.py::build_custom_fields` reads before writing the
  actual-fact custom fields `actual.py` reads back out.
- `snapshot.py` — `SourceSnapshot` (`desired`, `actual`, `observed`, `observed_errors`,
  `fetched_at`) and `build_source_snapshot(cfg, client)`: one desired fetch, one actual fetch,
  one dumps-dir scan. A dump-scan error degrades only `observed_errors` (matching `nctl
  status`'s independent-degradation convention); a GraphQL failure propagates as
  `NautobotError` since there is no trustworthy state to compare without it.

## Risk resolved: empirical field checks against the live dev instance

Per the plan's "risk to verify first," introspected and queried the live dev Nautobot
(`http://localhost:8000`, `nautobot_intent_catalog==0.5.0`) before pinning either query:

- Root query field names confirmed: `desired_nodes`, `desired_endpoints`, `desired_ip_ranges`,
  `desired_node_operational_configs`, `desired_service_placements`, `desired_services`,
  `desired_dependencies`, `devices`, `virtual_machines`, `interfaces`, `ip_addresses`.
- `DesiredNodeOperationalConfigType` and `DesiredServicePlacementType` field sets confirmed by
  introspection; both pinned queries executed against live data with no GraphQL errors.
- `DeviceType.local_endpoint`/`tailscale_endpoint`-style relations (`realized_device`,
  `realized_vm`) confirmed nullable and traversable to `{ id }`.
- **Real deviation found and recorded in `actual.py`'s docstring**: `host_system` and
  `network_interface` — two of the six allowlisted actual-fact custom fields — have no
  registered `CustomField` definition on the live instance, so Nautobot's GraphQL layer does
  not expose `cf_host_system` / `cf_network_interface` shortcut fields (introspection lists
  `cf_primary_mac_address`, `cf_primary_ip_address`, `cf_last_seen`, `cf_inventory_source`, and
  many others, but not those two). All six fields are fetched via `_custom_field_data` (the raw
  JSON blob) instead of per-field `cf_*` shortcuts — `read_actual_facts` already expects a plain
  mapping, so the ported function needed no change.

## End-to-end smoke test against live data

Ran `build_source_snapshot` against the dev Nautobot instance and the configured
`inventory.dumps_dir` (`nctl.toml`, token from `.local/localenv_memo.md`) as a live check beyond
the respx-mocked unit tests:

- Desired: 5 nodes, 5 endpoints, 3 IP ranges, **0** operational configs, placements, services,
  and dependencies — the dev dataset has no operational-config/placement/service data seeded
  yet. All 5 `desired_nodes` currently have `lifecycle: planned`, which is below
  `PRODUCTION_ELIGIBLE_LIFECYCLES = {approved, active}`; `agbach.local`, `agpc`, `agstudio.local`
  are Devices with actual data, but none is linked as a `desired_node`'s `realized_device` in
  this dataset. Recording this now because it directly constrains Step 2's parity gate: a live
  `nctl render production` run today will legitimately produce an empty inventory (0 eligible
  nodes), matching whatever the live `Export Production Inventory` Job also produces against
  the same empty inputs — "empty matches empty" is still a valid parity check, just not a very
  informative one. Populating operational configs/placements is outside this phase's scope to
  fix; parity is about the composer, not the dataset.
- Actual: 3 devices (matches `.local/localenv_memo.md`'s roster), 0 VMs, 0 interfaces, 0 IP
  addresses (DCIM/IPAM objects for these hosts aren't populated beyond the Device row itself in
  this dataset). Each device's `actual_facts()` correctly returned `local_ip`, `mac_address`,
  `collected_at`, `inventory_source` from real custom-field data, and correctly returned
  `observed_system=None`/`network_interface=None` — genuinely absent in the dataset, not a
  fetch bug (spot-checked by re-querying `_custom_field_data` directly: neither key is present
  on any of the three devices).
- Observed: 1 dump found in the configured `dumps_dir` (`agstudio.local`, `system: Darwin`), 0
  scan errors.

## Tests

- `tests/test_sources_desired.py` — pinned-query field coverage assertion, plus one
  respx-mocked fetch verifying every choice-field lowercasing and relation-flattening path
  (node `realized_device`/`realized_vm`, endpoint `desired_node`, operational-config
  `local_endpoint`/`tailscale_endpoint`, placement `desired_service`/`desired_node`/
  `desired_endpoint`, dependency `source_service`/`resolved_service`).
- `tests/test_sources_actual.py` — direct tests of the ported `read_actual_facts` (allowlist
  isolation, blank-value handling), `actual_type_problem`, `missing_required_facts`
  (per-consumer selectivity, confirmed against the ported vocabulary unchanged from
  `actual_facts.py`), plus a respx-mocked fetch and a query-shape assertion pinning
  `_custom_field_data` over `cf_host_system` (documents the live-schema deviation above so a
  future schema change that adds the missing CustomField definitions is a visible test change,
  not a silent behavior change).
- `tests/test_sources_observed.py` — typed extraction from a `NodeDump`, including tolerance
  for a dump with no `network` section.
- `tests/test_sources_snapshot.py` — `build_source_snapshot` fetches desired and actual exactly
  once each (asserted via a respx call-count), and a broken dump file degrades
  `observed_errors` without failing the snapshot.

## Verification

- `uv run pytest -q` — **101 passed** (14 new; 87 pre-existing from Phases 0–1, no regression).
- Live smoke test (see above) — ran successfully end to end against the dev Nautobot instance
  and the real `dumps_dir`, with no exceptions and results consistent with the two independent
  spot-checks (`.local/localenv_memo.md`'s host roster; direct `_custom_field_data` queries).

## Deviations from plan

- The plan's Step 1 description mentions the query risk as something to "resolve empirically
  before pinning the query"; this was done for both the desired and actual queries in this one
  step rather than splitting further, since both risks were resolvable in the same live-instance
  session and the fetch layer is small enough that keeping desired/actual/observed together as
  one commit-sized unit (per the plan's own Step 1 scope) reads better than fragmenting further.
- No REST fallback was needed — every field the plan flagged as a risk (`desired_service_placements`,
  `desired_node_operational_configs`, custom-field data, interface/MAC/IP traversal) resolved
  cleanly over GraphQL. The one real surprise (`host_system`/`network_interface` lacking `cf_*`
  shortcuts) doesn't require a fallback since `_custom_field_data` already covers it.

## Commit boundary

Clean, self-contained, nctl-only commit: the three-source fetch layer plus its test suite, fully
green, with no dependency on anything outside `nctl`. This is commit 1 of the plan's suggested
order ("nctl: three-source fetch layer + read models + tests").

**Not done yet, deliberately left for the next commit(s):**

- Step 2 — port the production composer (`production_inventory.py`,
  `production_inventory_contract.py`) onto this fetch layer, `nctl render production`, and its
  live parity gate against `Export Production Inventory`. Given the dataset finding above, the
  parity gate will need to either seed minimal operational-config/placement data first or
  explicitly document an empty-inventory parity result — a call to make when Step 2 starts.
- Steps 3–8 (comparator framework, evaluation port + dnsmasq switch-over, `nctl drift`, nintent
  deletion, ansible_agdev cleanup, docs) all sit downstream of Step 2 per the plan's ordering.

## Exit criteria status

- [ ] `nctl drift --json` — pending Steps 3–5.
- [ ] Comparator registry — pending Step 3.
- [ ] `nctl render production` parity — pending Step 2.
- [ ] Deployment-profiles byte contract removed — pending Steps 2, 6, 7.
- [ ] Evaluate Jobs / `IntentEvaluation` deleted, `render dnsmasq` unchanged — pending Steps 4, 6.
- [x] Desired-state processing logic exists only in `nctl_core` for the sources built so far
  (`sources/desired.py`, `sources/actual.py`, `sources/observed.py` are the only place this
  phase's ported/typed logic lives; nintent's originals are untouched, not yet deleted).
- [x] `uv run pytest` passes in nctl (101 passed) — nintent's suite is unaffected since nothing
  in nintent changed this step.

Next: Step 2 — port `production_inventory.py`/`production_inventory_contract.py` onto
`SourceSnapshot`, add `nctl render production`, and run the parity gate against the live
`Export Production Inventory` Job (accounting for the dataset's current zero
operational-configs/placements).
