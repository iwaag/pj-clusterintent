# Phase 2 Step 2.4 — Production composition and schema 2.0

Parent: [plan.md](plan.md), Step 2.4.

## Composition cutover

- Removed `OperationalConfigInput`, `EndpointInput`, the required-row gate, and the
  `missing_operational_config` branch. Eligible nodes resolve directly from all endpoints, the
  optional override, allowlisted actual facts, and the command's fixed `generated_at`.
- Resolver failures use the existing structured local skipped/errors pair with stage
  `operational_derivation`, the failing field, and sorted candidate/override evidence. No partial
  successful provenance is emitted.
- Removed stored expected-OS comparison and `desired_actual_os_mismatch` generation. Fresh Darwin
  selects macOS directly; fresh Linux selects Linux directly.
- Preserved effective inventory behavior for connection variables, OS groups, power/laptop,
  Ansible port, actual MAC/interface, realized Device ID, placements, and service groups.
- Removed `nintent_operational_config_id`; `nintent_desired_node_id` remains the stable host link.

## Closed report schema 2.0

`PRODUCTION_INVENTORY_SCHEMA_VERSION` is now `2.0`. Every successful `report.hosts[]` record has
the exact eight-key `operational_values` object. Each value has exactly:

- `value`;
- source `derived`, `default`, or `override`;
- a kind-specific, allowlisted `source_reference`; and
- boolean `override_won`.

The validator rejects unknown/missing host, operational-value, value-record, and source-reference
keys; invalid sources and non-boolean flags also fail. Schema `1.0` inventory/report artifacts are
rejected, and a schema `2.0` inventory carrying the removed operational-config ID is rejected as an
unknown host variable.

Endpoint IP values are normalized. VPN endpoints are excluded from automatic local selection,
Tailscale remains override-only, and invalid IP text is not treated as a usable address.

## Isolation and determinism

Tests prove that a healthy observed node with no override renders with complete provenance, and
that adding an ambiguous-endpoint neighbor leaves the healthy host variables unchanged while only
the bad node receives `ambiguous_connection_endpoints`. Existing placement/config/merge failures
remain node-local; shared profile and final document corruption remain global.

## Verification

Focused derivation/adapter/contract/composer/render/CLI/compatibility suite: **95 passed**.
`git diff --check` passed.

The complete nctl suite is intentionally deferred until Step 2.5 replaces the remaining drift and
reconcile imports of the deleted source class. No compatibility alias was added for those
consumers, and no half-cutover revision was run against the live old GraphQL server.

No live state or generated inventory artifact was written.
