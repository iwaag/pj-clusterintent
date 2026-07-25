# Phase 0-EX1 Implementation Plan: Expose nintent models via Nautobot GraphQL

Parent: [roadmap.md](../roadmap.md) — Phase 0-EX1: make the desired state readable through the
same GraphQL endpoint as the actual state, before any command starts consuming it.

## Current state (as of 2026-07-14)

- Phase 0 is complete ([p0/report0.3-0.7.md](../p0/report0.3-0.7.md)): `nctl status` works, and
  `NautobotClient.ping()` currently confirms the intent-catalog app via a REST probe of
  `/api/plugins/intent-catalog/nodes/?limit=1` — with a comment already marking it for
  replacement in this phase (`nctl/src/nctl_core/nautobot.py`).
- `nintent` (`nautobot_intent_catalog`, v0.3.0) defines 10 models in `models.py`:
  `IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`,
  `DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange`,
  `IntentEvaluation`, `DeploymentProfileProjection`. None are GraphQL-registered today.
- Every model except `DeploymentProfileProjection` already has a `NautobotFilterSet` in
  `filters.py` — a prerequisite for Nautobot's auto-generated GraphQL filtering.
- Dev Nautobot is `networktocode/nautobot:3.1.3` (GraphQL served at `/api/graphql/`, read-only).
- Deployment constraint (`.local/localenv_memo.md`): the dev container installs nintent from
  GitHub, so verifying changes requires commit → push (ask the user) → `docker compose build` →
  restart. Plan the work so all nintent changes land in as few push cycles as possible.

## Approach

Nautobot auto-generates GraphQL types for plugin models decorated with
`@extras_features("graphql")` (the same mechanism core models use), including:

- a top-level plural query field per model (e.g. `desired_nodes`, `desired_endpoints`),
- traversal of FKs/reverse relations **between any two registered types** — which is exactly what
  the roadmap wants: `DesiredNode.realized_device` → core `Device`, and the reverse
  `Device.intent_catalog_desired_nodes`, become walkable once the nintent types join the schema,
- filtering backed by the existing FilterSets.

So the primary implementation is the decorator, not hand-written graphene types. Custom types in
`graphql/types.py` (registered via the app config) are the **fallback only**, if auto-generation
mishandles something (JSONFields, the string-typed `ip_address`, etc.).

**Risk to verify first**: exact auto-generated query-field and relation names, and JSONField
scalar behavior, on Nautobot 3.1.3 specifically. Step 1 resolves this empirically before nctl
pins any names.

## Step 1 — Register GraphQL types in nintent

- Add `@extras_features("graphql")` (from `nautobot.apps.models`) to all desired-state models:
  `IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`,
  `DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange`.
  - `IntentEvaluation`: include it — Phase 3 writes a reconciliation status and reading it back
    over GraphQL will be wanted; it costs nothing now.
  - `DeploymentProfileProjection`: **exclude**. It is an advisory Ansible-owned snapshot with no
    FilterSet, not desired state; exposing it would suggest an authority it doesn't have.
- No new models, no field changes ⇒ **no DB migration**. (`extras_features` only populates the
  in-memory registry. Confirm `nautobot-server post_upgrade`/restart is enough; if Nautobot 3.x
  turns out to require a ContentType/feature migration, generate it — but none is expected.)
- Bump nintent version to 0.4.0 (breaking-change phase, but keep versions honest).

Local verification before pushing: run nintent's existing test suite; if the repo has no
Nautobot-integrated test harness, verification is deferred to the live check in Step 2.

## Step 2 — Deploy and pin the actual schema

- Commit in `nintent`, ask the user to push, then
  `cd devenv/nautobot && docker compose --env-file ../.env build && docker compose --env-file ../.env up -d`.
- Introspect the live schema (token from `.local/localenv_memo.md`, never committed):

```graphql
{ __schema { queryType { fields { name } } } }
```

- Record in this phase's report: the exact top-level field names (expected style:
  `desired_nodes`, `desired_endpoints`, …), the relation field names on both sides
  (`DesiredNodeType.realized_device`, `DeviceType.intent_catalog_desired_nodes`, and the
  reverse `desired_endpoints` on `DesiredNodeType`), and how JSONFields
  (`expected_spec`, `requirements`, …) come back.
- Run the roadmap's exit-criteria query for real — desired + actual in one request, e.g.:

```graphql
{
  desired_nodes {
    name
    lifecycle
    desired_endpoints { name endpoint_type ip_address dns_name generate_dnsmasq }
    realized_device {
      name
      interfaces { name ip_addresses { address } }
    }
  }
}
```

- If any of this fails (missing fields, unqueryable JSON), fall back to explicit graphene types
  in `nintent/nautobot_intent_catalog/graphql/types.py` for the affected models only, and note
  the deviation in the report.

## Step 3 — Switch `nctl status` to a GraphQL introspection probe

In `nctl/src/nctl_core/nautobot.py`:

- Replace the REST probe (`INTENT_CATALOG_PROBE_PATH`) in `ping()` with a schema check using the
  existing `graphql()` method:

```graphql
{ __type(name: "DesiredNodeType") { name } }
```

  (Pin the type/field names discovered in Step 2; probe the small set nctl will actually consume
  in Phases 1–2 — at minimum the desired-node and desired-endpoint types.)

- `NautobotInfo` gains the precision the roadmap asks for: keep `intent_catalog: bool` meaning
  "app installed" (from `/api/status/` `nautobot-apps`, unchanged) and add
  `intent_graphql: bool` = "the intent GraphQL types are present in the schema". Schema stays
  `nctl.status.v1` if this is purely additive to `data.nautobot`; the golden-shape test is
  updated either way (pre-freeze, breaking is allowed but must be explicit).
- Degradation: introspection failure (connection, auth, GraphQL error) must not crash `status` —
  it yields `intent_graphql: false` plus an `EnvelopeError` (`code: intent_graphql_missing` or
  reuse the connection/auth codes), consistent with Phase 0's independent-degradation rule.
- Update `render_status_text()` to show the new field.

## Step 4 — Tests, docs, report

- nctl tests (respx): introspection returns the type → `intent_graphql: true`; returns `null`
  (plugin without GraphQL types) → `false` + error; GraphQL endpoint erroring while
  `/api/status/` succeeds → status still renders, `ok: false`. Update the golden-shape test for
  the envelope change. Delete the now-dead REST-probe test paths.
- Live verification against dev Nautobot: `uv run nctl status --json` shows
  `intent_graphql: true`; the Step 2 joined query returns real data for the existing desired
  nodes.
- Docs: note in `nctl/README.md` (conventions section) the division of labor the roadmap fixes
  from here on: **reads = GraphQL via `NautobotClient.graphql()`, writes = REST** (intent-catalog
  ViewSets stay for writes). One paragraph; the roadmap remains the source.
- Write `devdocs/vision/core_reconcile/p0-ex1/report.md` in the established style, including the
  pinned schema names (Step 2) — Phase 1 and 2 will build their queries from that record.

## Out of scope

- Any consumer of the new types beyond the `status` probe (dnsmasq rendering is Phase 1, drift
  is Phase 2).
- GraphQL mutations / write paths (Nautobot GraphQL is read-only by design; writes stay REST).
- Removing the intent-catalog REST ViewSets (still the write path, and Phase 3 needs them).
- Exposing `DeploymentProfileProjection` or nodeutils dump data via GraphQL.

## Exit criteria (from roadmap, made checkable)

- [ ] All desired-state models (incl. `IntentEvaluation`, excl. `DeploymentProfileProjection`)
  are queryable at `/api/graphql/` on the dev Nautobot.
- [ ] One GraphQL query returns desired nodes + desired endpoints joined with core DCIM/IPAM
  objects (realized device, interfaces, IPs) — the Step 2 query, saved in the report.
- [ ] `nctl status` verifies the intent types via GraphQL introspection (REST probe removed) and
  degrades cleanly when they're absent.
- [ ] `uv run pytest` passes in nctl; the actual schema names are documented in the report.

## Suggested commit order

1. nintent: `@extras_features("graphql")` on the models + version bump (single push cycle;
   Steps 1–2).
2. nctl: introspection probe + `NautobotInfo.intent_graphql` + tests + README note (Steps 3–4).
3. Parent repo: submodule pointer bumps + `p0-ex1/report.md`.
