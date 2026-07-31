# Phase 4 Report — Inspection Projection

## Step 1 — Projection builder in nctl_core

New `nctl/src/nctl_core/relations_render.py`: pure builder mirroring
`drift_render.py`'s build/render split.

- `build_relations(cfg, *, host=None, service=None)` calls
  `drift_render.fetch_and_compute_drift(cfg)` verbatim (relations is "drift's
  inputs, projected differently") then `render_relations_data(...)`.
- `render_relations_data(snapshot, result, generated_at, *, host=None,
  service=None, stale_after_hours=24)`: the pure projection. Per active
  consumer placement, per binding (sorted `binding_name`): resolves via
  `production.service_dependencies.resolve_all_bindings` (keyed by
  `placement_id -> binding_name`, so every binding gets its own edge whether
  or not its desired resolution succeeded — the deliberate inclusion the
  plan calls for, unlike drift which skips resolver errors).
  - **Resolved edges**: provider service/placement/node/endpoint-name/URL
    resolved from the resolution's provenance plus a
    `placement_id -> node_slug` and `endpoint_id -> endpoint_name` map built
    from `production.adapter.build_production_node_inputs`; actual evidence
    read from `consumer.realized.facts.observed_services[<observed_key>]
    .bindings[<binding_name>]` (`observed_key` = the consumer service's
    `DesiredService.name`, matching drift's own lookup key); state via
    `drift.binding_evaluation.evaluate_binding_state` — the same function
    drift calls, so the two commands cannot disagree. Provider convergence
    is read straight from the already-computed `DriftResult.targets`
    (`kind == "service"`, `status == "converged"`) rather than re-running
    the two-pass service evaluation drift does internally.
  - **Resolution-failure edges**: `provider = None`, `state = None`,
    `gap_codes = [resolution.error_code]`, `evidence` = the resolver's
    `error_evidence` plus `error_message` if present.
- `unreferenced`: active-placement service IDs (mirrors
  `service_dependencies.py`'s own `active_by_service` construction) minus
  the keys of `reverse_service_bindings(node_inputs)`, rendered as service
  slugs, sorted. A service with an active placement but zero inbound
  bindings is "unreferenced" — this correctly includes a pure consumer
  service like `node-agent` itself, not just a candidate-for-removal
  provider; the text/JSON output never phrases it as a deletion
  recommendation (hard rule 5).
- Determinism: edges sorted by `(consumer_node, consumer_service,
  binding_name)`; `unreferenced` sorted alphabetically. `--host`/`--service`
  filters match on either side of the edge (consumer or provider).
- `RELATIONS_SCHEMA = "nctl.relations.v1"`.
- `render_relations_text`: one line per edge (`node/service —binding→
  provider_service @provider_node [state, age]`, or `? [resolution_error:
  code]` for a failed resolution), an `unreferenced (informational): ...`
  block, and a `summary: state=count ...` line (`resolution_error` counted
  as its own summary bucket).

New `nctl/tests/test_relations_render.py` (6 tests), constructing
`SourceSnapshot`/`DriftResult` directly (no GraphQL mocking, since the
builder never touches Nautobot itself) via the same pydantic source models
`fetch_and_compute_drift` produces:

- `test_satisfied_edge` — resolved provider (service/node/endpoint-name/URL),
  `satisfied` state, empty gap codes.
- `test_misbound_edge` — configured endpoint disagreeing with desired
  produces `binding_misbound`.
- `test_resolution_failure_edge_included_with_error_code` — an ambiguous
  provider (two active placements for the same service) still produces one
  edge, `provider is None`, `gap_codes == ["binding_provider_ambiguous"]`,
  evidence carries `provider_service_slug`.
- `test_provider_not_converged_gap` — provider service `drifting` in the
  `DriftResult` yields `state="satisfied"` but
  `gap_codes == ["binding_provider_not_converged"]`.
- `test_unreferenced_service_listed_informational` — an orphaned service
  with an active placement and zero consumers appears in `unreferenced`
  alongside the pure-consumer `node-agent` service (both are correct: this
  is "who has no inbound edge", not "who could be deleted").
- `test_edges_sorted_deterministically` — two consumer nodes, edges ordered
  by consumer node slug regardless of input order.

Gate: `uv run pytest -q --durations=20` — **1091 passed** (was 1085 at Phase
3 completion; 6 net new). No other test file's count changed.

Commit: nctl `e354378`.

## Step 2 — CLI command and renderers

`nctl relations` registered in `cli/main.py` as a plain `@app.command()`
identically to `drift`: `--host`/`--service` filters (the same
`HostOption`/`ServiceOption` typer annotations `drift` uses — they now filter
edges on either the consumer or provider side), `--json`, `build_relations` +
`emit(...)`. Exit code follows the `status`/`drift` pattern exactly (`EXIT_OK`
when the fetch itself succeeded, regardless of how many edges are unhealthy —
an unhealthy binding is a finding, not a command failure); no discretion
needed here, the plan's suggested default was adopted as-is.

`render_relations_text` (already written in Step 1, exercised here through
the CLI): one line per edge —
`node/service —binding→ provider_service @provider_node [state, age]h`, or
`node/service —binding→ ? [resolution_error: code]` for a failed resolution
— followed by an `unreferenced (informational): ...` block (only when
non-empty) and a `summary: state=count ...` line.

`tests/test_cli_relations.py` (4 tests, mirroring `test_cli_drift.py`
exactly): default text output, `--json` envelope shape, `--host`/`--service`
filter pass-through, exit 1 on a failed fetch. `tests/test_cli_surface.py`'s
`RETAINED_COMMANDS` set gained `"relations"` (2 existing tests there now also
cover it: exact top-level command-set equality and `--help` listing every
retained command).

Root `README.md` and `nctl/README.md` command lists and prose updated: a
`nctl relations --json` example alongside the existing `nctl drift --json`
one, a one-paragraph description of what the projection is for, and (in
`nctl/README.md`) the full `nctl.relations.v1` envelope shape documented in
the same style as the `nctl.drift.v1` section immediately above it —
including the deliberate resolution-error-inclusion difference from `drift`
and the `unreferenced`/informational-only guarantee.

Gate: `uv run pytest -q --durations=20` — **1095 passed** (was 1091 after
Step 1; 4 net new). `uv run nctl --help` confirmed `relations` listed with
its help text.

Commit: nctl `3b38208`.
