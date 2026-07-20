# Phase 2 Step 2.3 — nctl source shape and shared resolver inputs

Parent: [plan.md](plan.md), Step 2.3.

## Source contract replacement

- Replaced GraphQL root `desired_node_operational_configs` with
  `desired_node_operational_overrides`; no query fallback or dual Pydantic model exists.
- Replaced the typed snapshot list with optional `DesiredNodeOperationalOverride` records and
  removed stored policy/expected-OS fields from that shape.
- Added the five source metadata values to typed desired nodes/endpoints:
  DNS/mDNS source, realized Device/VM source, and realized IP source.
- Production adaptation now supplies every endpoint owned by the node, its optional override,
  realized-object type, allowlisted actual facts, and placement set independently. It does not
  preselect an endpoint or derive policy in the GraphQL layer.

## Resolver coverage extended

The pure resolver introduced in Step 2.1 now has executable coverage for:

- fresh observed Linux/macOS and declared HAOS;
- zero/one/many/unique-primary endpoint selection with stable candidate evidence ordering;
- forced local and forced Tailscale precedence;
- observed local IP precedence over the selected endpoint address for required hosts;
- absent/stale/invalid/unsupported observation evidence;
- incomplete forced endpoints and invalid power combinations; and
- complete closed provenance records, including defaulted optional values.

The adapter only translates IDs/typed values into resolver input dataclasses. Semantic selection
remains in this single resolver.

## Verification

Focused source/snapshot/adapter/resolver/dnsmasq tests:

```text
uv run --project nctl pytest -q \
  nctl/tests/test_sources_desired.py \
  nctl/tests/test_sources_snapshot.py \
  nctl/tests/test_production_adapter.py \
  nctl/tests/test_production_derivation.py \
  nctl/tests/test_dnsmasq_render.py
```

Result: **30 passed**. `git diff --check` passed.

This is intentionally an undeployable half of the coordinated breaking cutover: production/drift/
reconcile consumers still named the removed old typed class at this exact commit. No compatibility
alias was added merely to make the mixed-schema interval runnable. Step 2.4 and Step 2.5 replace
those consumers before any full-suite or live-server execution; the version set is deployed only
after those matching commits pass together.

No live query was run against the still-old Nautobot schema, and no live state was mutated.
