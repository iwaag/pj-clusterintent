# Phase 0-EX1 Report — Steps 2–4 (deploy, pin schema, switch status probe, tests)

Date: 2026-07-14. Continues from [report1.md](report1.md) (Step 1: `@extras_features("graphql")`
in `nintent`, pushed and merged as `nintent@035cfa9`). Implements
[plan.md](plan.md) Steps 2 through 4.

## Step 2 — Deployed and pinned the actual schema

- Rebuilt the dev Nautobot image with `docker compose --env-file ../.env build --no-cache` (the
  Dockerfile does a plain `pip install git+https://github.com/iwaag/nprojects.git`, no cache-buster,
  so `--no-cache` was needed to force re-resolving `HEAD`). Build log confirms
  `Resolved ... to commit 035cfa953afc...` and `Successfully installed nautobot-intent-catalog-0.4.0`.
  (`iwaag/nprojects.git` is the pre-rename remote for what is now `iwaag/nintent.git`; GitHub
  transparently redirects, no Dockerfile change needed.)
- `docker compose --env-file ../.env up -d` recreated `nautobot`, `nautobot-worker`,
  `nautobot-scheduler`; `nautobot-nautobot-1` reported healthy.
- Live introspection confirms all 8 registered types with the expected snake_case naming:
  top-level query fields `intent_source(s)`, `desired_service(s)`, `desired_dependency/-ies`,
  `desired_node(s)`, `desired_endpoint(s)`, `desired_service_placement(s)`,
  `desired_node_operational_config(s)`, `desired_ip_range(s)`, `intent_evaluation(s)`.
  `DeploymentProfileProjection` correctly absent.
- Relation names (both directions), pinned for Phase 1/2 to build on:
  - `DesiredNodeType.realized_device` → `DeviceType` (object, nullable)
  - `DeviceType.intent_catalog_desired_nodes` → list of `DesiredNodeType` (reverse FK, matches the
    `related_name` in `models.py`)
  - `DesiredNodeType.desired_endpoints` → list of `DesiredEndpointType` (forward reverse-FK,
    matches `related_name="desired_endpoints"`)
  - `DesiredNodeType.realized_vm` → `VirtualMachineType` (object, nullable; not yet consumed by any
    plan but confirmed present)
  - `DesiredEndpointType.realized_ip_address` → `IPAddressType` (object, nullable)
- JSONField scalar behavior: `expected_spec`, `accepted_actual_types`, `requirements`, etc. all come
  back typed as `GenericScalar` (Nautobot's JSON-safe passthrough) — queryable and returned as
  native JSON, no custom scalar issues.
- `DesiredEndpoint.ip_address` (a plain `CharField`, not a Nautobot IP type) auto-generated as a
  clean `String` scalar — no ambiguity, no fallback type needed.
- Ran the roadmap's exit-criteria joined query (desired nodes + endpoints + `realized_device` +
  `interfaces` + `ip_addresses`) verbatim from the plan against the live instance. It executed with
  no GraphQL errors and returned all 5 desired nodes with their endpoints. `realized_device` came
  back `null` for all of them — expected: the current dev dataset has `DesiredNode` records but none
  have their `realized_device` FK populated yet. That's a data-population gap (out of scope for this
  phase, which is only about schema exposure), not a schema or query-shape problem; confirmed
  separately that `devices { name interfaces { ... } }` resolves fine and lists 3 real devices.
- **No fallback graphene types were needed** — auto-generation via `extras_features` handled every
  field, including JSON and the string-typed IP, correctly on Nautobot 3.1.3. `graphql/types.py`
  remains unwritten.

## Step 3 — Switched `nctl status`'s intent-catalog probe to GraphQL introspection

In `nctl/src/nctl_core/nautobot.py`:

- Removed `INTENT_CATALOG_PROBE_PATH` and the REST probe of
  `/api/plugins/intent-catalog/nodes/?limit=1`.
- Added `NautobotClient._check_intent_graphql()`, which runs a single aliased introspection query
  (`{ node: __type(name: "DesiredNodeType") { name } endpoint: __type(name: "DesiredEndpointType")
  { name } }`) via the existing `graphql()` method, and returns `True` only if both types resolve.
  Any `NautobotError` subclass (connection, auth, GraphQL error) is caught and treated as "not
  present" rather than propagating — `ping()` itself still only raises for the primary
  `/api/status/` call, unchanged from before.
- `NautobotInfo` gained `intent_graphql: bool` (default `False`). Per the plan, `intent_catalog`
  keeps its original meaning — "app installed", from `/api/status/`'s `nautobot-apps` — and is no
  longer ANDed with any reachability probe; `intent_graphql` is the new, separate "intent GraphQL
  types are present" signal.
- `status.py`'s `_check_nautobot()`: when `intent_catalog` is true but `intent_graphql` is false,
  emits `EnvelopeError(code="intent_graphql_missing")` — status still renders (`ok: false`, not a
  crash), consistent with Phase 0's independent-degradation rule. Unauthenticated still short-
  circuits to `nautobot_unauthenticated` before this check runs.
- `render_status_text()` now prints `intent_graphql: <bool>` alongside `intent_catalog`.
- Schema stayed `nctl.status.v1` (purely additive field on `data.nautobot`), per the plan's option;
  the golden-shape test was updated to include the new key.

## Step 4 — Tests, docs, live verification

- `nctl/tests/test_nautobot.py`: replaced the REST-probe-based tests with
  `test_ping_ok_with_intent_catalog_graphql_present` (both types resolve → `intent_graphql: true`),
  `test_ping_intent_catalog_installed_but_graphql_types_missing` (introspection returns `null` for
  both → `false`), `test_ping_intent_graphql_false_on_graphql_endpoint_error` (GraphQL endpoint
  errors while `/api/status/` succeeds → `intent_graphql: false`, `ping()` doesn't raise), and
  updated `test_ping_without_intent_catalog_plugin` to also assert `intent_graphql is False`. All
  REST-probe-path tests and the now-dead `INTENT_CATALOG_PROBE_PATH` references were deleted.
- `nctl/tests/test_status.py`: added `test_build_status_not_ok_when_intent_graphql_missing`
  (installed-but-missing → `ok: false`, `intent_graphql_missing` in `errors`); updated the
  golden-shape assertion's expected key set for `data.nautobot` to include `intent_graphql`; updated
  the "all checks pass" `OkClient` fixture to set `intent_graphql=True` so that test still represents
  a genuinely all-green state under the new degradation rule.
- `nctl/README.md`: added the "Reads vs writes" convention paragraph the roadmap fixes from this
  phase onward — reads via `NautobotClient.graphql()`, writes stay REST (intent-catalog ViewSets).
- `uv run pytest` in `nctl` — 49 passed (up from 46; 3 net-new GraphQL-probe tests replacing 2
  REST-probe tests, plus the new degradation test).
- Live verification against the rebuilt dev Nautobot:
  - `NAUTOBOT_TOKEN=<real> uv run nctl status --json` → `ok: true`,
    `nautobot.intent_catalog: true`, `nautobot.intent_graphql: true`, all 5 submodules reported
    (this session's `nintent` and `nctl` bumps show up as `clean` at their new pinned commits).
  - `NAUTOBOT_TOKEN=wrong uv run nctl status --json` → `ok: false`,
    `nautobot_unauthenticated`, `intent_catalog: false`, `intent_graphql: false` (auth failure short-
    circuits before the GraphQL check runs, as designed).

## Deviations from plan

- `docker compose build` needed `--no-cache` in practice — the Dockerfile's `pip install git+...`
  step has no inherent cache-buster, so a plain `build` would have reused the stale layer. Not
  called out explicitly in the plan's Step 2 command but consistent with its intent.
- The joined query's `realized_device` came back `null` for all nodes in the live check — a data
  gap in the dev dataset (no `DesiredNode.realized_device` FKs populated yet), not a schema issue.
  Noted rather than treated as a failure since the plan's exit criterion is about the query *shape*
  working end to end, which it does.

## Exit criteria — all met

- [x] All desired-state models (incl. `IntentEvaluation`, excl. `DeploymentProfileProjection`) are
  queryable at `/api/graphql/` on the dev Nautobot (live-verified via introspection).
- [x] One GraphQL query returns desired nodes + desired endpoints joined with core DCIM/IPAM
  objects (realized device, interfaces, IPs) — ran the plan's exact query live; see Step 2.
- [x] `nctl status` verifies the intent types via GraphQL introspection (REST probe removed) and
  degrades cleanly when they're absent (live-verified with a bad token; unit-tested for the
  installed-but-missing case).
- [x] `uv run pytest` passes in nctl (49 passed); nintent's `uv run python3 -m unittest discover`
  passes (203 passed, from Step 1); actual schema names documented above.

Phase 0-EX1 is complete. Commits: `nintent@035cfa9` ("Register desired-state models for Nautobot
GraphQL", pushed and merged by the user as `10d9fbc "p0-ex1-s1"` in the parent repo's submodule
pointer), `nctl@7cf302f` ("Switch intent-catalog status probe to GraphQL introspection"), and this
parent-repo commit bumping the `nctl` submodule pointer alongside this report. Next per the roadmap
is Phase 1 (bake in the dnsmasq workflow), which will build its GraphQL queries from the field/
relation names pinned in Step 2 above.
