# Phase 2 Step 2.5 — Drift, dashboard, service evaluation, and reconcile

Parent: [plan.md](plan.md), Step 2.5.

## Drift and provenance

- `production_policy` now emits one node-targeted `derived_value_provenance` INFO diagnostic for
  every desired node. Successful resolution contains the shared eight operational value records;
  unsuccessful resolution contains the exact finding code, field, and allowlisted evidence rather
  than partial values.
- The diagnostic also carries persisted DNS/mDNS and realized node/IP link provenance with owning
  row/field references. INFO remains converged-safe and is intentionally omitted from reconcile.
- Text and dashboard tests pin visibility, detail payloads, INFO severity, and safe escaping of a
  hostile `</script>` value inside provenance evidence.
- `node_existence` now derives required observation from absence of the optional
  `declared_host_os`; it no longer looks for a mandatory operational-config row.

## Service evaluation

- Active placement evaluation receives `actual_state_policy` and `host_os` from the same pure
  resolver used by production composition. Declared HAOS remains observation-exempt; observed
  Linux/macOS uses required evidence.
- Removed the independent stored expected-OS comparison and
  `service_placement_os_mismatch`. Effective OS remains visible as placement evidence without
  manufacturing a second desired value.

## Reconcile safety

- Replaced the Phase 1 blocker constant with the current semantic
  `PRODUCTION_BLOCKING_NODE_CODES`, including operational derivation and observation failures.
  Classifier and exhaustive planner tests import this canonical set.
- Production actions are pruned by node-local blockers from the selected scope. A cluster plan
  with one ambiguous-endpoint node still schedules the healthy host; host-scoped plans now also
  restrict service action host lists to the requested host. This test exposed and fixed a prior
  host-scope leakage where all placements of a selected service could be retained.
- Executor OS/playbook grouping resolves from the shared resolver using the snapshot's fixed
  timestamp. A host missing from the snapshot, a derivation failure, or a missing OS playbook now
  raises an invariant error; there is no `None` or arbitrary-playbook fallback.
- `link_actual_node` atomically PATCHes the realized link and its `derived` source, then refetches
  and confirms both values.

## Verification

Complete nctl suite: **584 passed**, with one pre-existing Starlette/httpx deprecation warning.
`python -m compileall -q src` and `git diff --check` passed.

No live state or generated inventory artifact was written.
