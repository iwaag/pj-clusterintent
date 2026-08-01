no# Phase 4 Plan — Inspection Projection

Goal (roadmap Phase 4, idea-A §9): one deterministic, derived-on-demand graph
view — an `nctl` command that answers "who depends on what, and is it real"
for the whole cluster, per edge: consumer service/placement, binding name,
provider service, resolved placement and endpoint, actual binding state, gap
codes, and evidence freshness. Plus the `unreferenced` service list, labeled
informational. Text/JSON only; no graph drawing; nothing persisted.

Scratch environment, destructive phase: no backward compatibility, no
migration concerns. The command is read-only against Nautobot, so there is no
approval boundary anywhere in this phase — the only live step is running the
command against the scratch cluster and reading the output.

## Execution style

One step at a time; append a section to `p4/report.md` and commit after each
step (nctl commits in the submodule, superproject pointer bump at the end).
Full nctl test suite (`uv run pytest -q --durations=20`, currently 1085
passed) is the gate for each code step.

## Hard rules (the minimum)

1. The projection is computed fresh from desired + actual state on every
   invocation — never persisted, never cached (roadmap hard rule 1 / idea-A §9).
2. `unreferenced` is information only; the output must not phrase it as a
   deletion recommendation (hard rule 5).
3. One evaluation logic: reuse `evaluate_binding_state` and
   `normalize_endpoint_url` — do not reimplement the five-state precedence or
   normalization in the projection, or drift and relations will disagree.

Everything else — command name, schema field names, module layout, text
formatting, extra filters — is implementer's discretion.

## Step 1 — Projection builder in nctl_core

A pure builder (suggested: new `nctl_core/relations_render.py`, mirroring
`drift_render.py`'s build/render split) that takes the fetched snapshot +
computed drift and produces the edge list and unreferenced list.

Ingredients, all existing:

- **Fetch + compute in one call:** `drift_render.fetch_and_compute_drift(cfg)`
  ([drift_render.py:99](nctl/src/nctl_core/drift_render.py#L99)) returns
  `(SourceSnapshot, DriftResult, generated_at)` and already handles token,
  profiles, and Nautobot errors. Reuse it verbatim — relations is exactly
  "drift's inputs, projected differently".
- **Desired resolution per edge:**
  `production.service_dependencies.resolve_all_bindings(node_inputs)`
  ([service_dependencies.py:211](nctl/src/nctl_core/production/service_dependencies.py#L211)),
  with `node_inputs = build_production_node_inputs(snapshot)` (see how
  [evaluation_snapshot.py:102](nctl/src/nctl_core/drift/evaluation_snapshot.py#L102)
  does it). Keyed `placement_id -> binding_name`; each
  `ServiceDependencyResolution` carries either `provenance[0]`
  (`provider_placement_id`, endpoint identity, resolved URL in `.variables`)
  or an `error_code`/`message`/`evidence` for the §6 resolution failures.
- **Actual evidence:** per consumer node in the snapshot at
  `observed_services[<service>].bindings[<binding_name>]`
  (`configuration_status`, `configured_endpoint`, `reachability_status`,
  `checked_at`) — see `_evaluate_bindings` in
  [service_placement.py:174](nctl/src/nctl_core/drift/service_placement.py#L174)
  for the exact read pattern.
- **State evaluation:** `drift.binding_evaluation.evaluate_binding_state`
  ([binding_evaluation.py:48](nctl/src/nctl_core/drift/binding_evaluation.py#L48)).
  Freshness threshold is `cfg.reconcile.service_observation_max_age_hours`
  (default 24h); the evaluation's evidence dict already includes
  `age_hours` / `stale_after_hours` — pass them through as the edge's
  freshness fields rather than inventing new ones.
- **Provider convergence** (needed for `provider_converged` on
  `BindingCheck` / the `binding_provider_not_converged` gap): read each
  provider service's status from the `DriftResult` targets
  (`kind == "service"`), same information the two-pass evaluation in
  `evaluate_all_services` derives. You do not need to re-run the two-pass
  dance — drift already did it; you are projecting its result.
- **Reverse view / unreferenced:**
  `reverse_service_bindings(node_inputs)`
  ([service_dependencies.py:264](nctl/src/nctl_core/production/service_dependencies.py#L264))
  gives inbound consumers per provider service; `unreferenced` = active
  desired services minus its keys.

One deliberate difference from drift: drift **skips** bindings whose desired
resolution errored (dedup against `LocalCompositionError` composition drift —
see `_binding_checks_by_placement_id`,
[evaluation_snapshot.py:315](nctl/src/nctl_core/drift/evaluation_snapshot.py#L315)).
Relations must **include** those edges, with the resolution `error_code` as
the edge's gap code and no actual state — §9 explicitly wants
desired-resolution gaps visible in the projection. This is a projection-side
inclusion, not a change to drift.

Determinism: sort edges by `(consumer_node, consumer_service, binding_name)`
and the unreferenced list alphabetically, same convention
`reverse_service_bindings` already uses.

Suggested edge shape (adjust freely):

```json
{
  "consumer": {"node": "aghub", "service": "node-agent", "placement_id": "..."},
  "binding_name": "llm_provider",
  "provider": {"service": "ollama", "placement_id": "...", "node": "agstudio",
                "endpoint": "ollama-api", "url": "http://agstudio.home.arpa:11434/v1"},
  "state": "satisfied",
  "gap_codes": [],
  "evidence": {"configured_endpoint": "...", "reachability_status": "reachable",
                "checked_at": "...", "age_hours": 0.1, "stale_after_hours": 24.0}
}
```

Unit tests: pure-builder tests with doctored snapshots (the
`test_drift_render.py` misbound test shows how to fabricate one), covering at
least: a satisfied edge, a misbound edge, a resolution-failure edge (ambiguous
provider) appearing with its error code, provider-not-converged, an
unreferenced service, and stable ordering.

Report + commit (nctl).

## Step 2 — CLI command and renderers

- `nctl relations` with `--json` (name is discretionary; `relations` matches
  the roadmap's example). Register in
  [cli/main.py](nctl/src/nctl_core/cli/main.py) as a plain `@app.command()`
  like `status`/`drift` — parse, call the Step 1 builder, `emit(...)`.
- Envelope via `output.Envelope.build` with a new schema name (suggest
  `nctl.relations.v1`). Exit codes: follow the `status` pattern — `EXIT_OK`
  when the fetch succeeded, regardless of how many edges are unhealthy; an
  unhealthy binding is a finding, not a command failure. (Discretionary — if
  you prefer drift-style nonzero-on-gaps, say so in the report.)
- Text renderer: one line per edge is enough, e.g.
  `aghub/node-agent —llm_provider→ ollama @agstudio [satisfied, 0.1h]`,
  followed by an `unreferenced (informational): ...` block. Optional but
  cheap and useful: `--host` / `--service` filters mirroring `build_drift`'s.
- Update the command list in the root `README.md` and `nctl/README.md`.

Tests: CLI-level test if the existing suite has a pattern for it (check
`tests/` for `main`/CLI tests), otherwise renderer tests are sufficient.

Full suite gate, report + commit (nctl).

## Step 3 — Live run and roadmap close-out

Read-only, no approval needed:

```bash
uv run --project nctl nctl relations
uv run --project nctl nctl relations --json
```

Expected against the current cluster: three `llm_provider` edges
(aghub/agpc/agstudio node-agent → ollama@agstudio), state `satisfied` if
evidence is fresh and ollama is up — note P3's re-check saw a transient
`binding_unreachable` on agstudio, so an unhealthy state here is a real
signal, not necessarily a Phase 4 bug; cross-check against `nctl drift --json`
(the two must agree, since they share the evaluation). If evidence is stale
(>24h since the P3 runs), edges will be `unknown`; a
`nctl reconcile HOST --refresh-observation --yes` refresh is allowed but ask
the user first since it actuates.

Record the actual output (redact nothing — no secrets appear in this
projection by construction; observation returns only the allowlisted slot).

Close out: paste the completion evidence in `p4/report.md`, mark Phase 4 done
in `roadmap.md`, commit nctl + superproject pointer bump + docs. Pushes go
through the user per the usual flow.

## Completion

`nctl relations` (one command) answers "who depends on what, and is it real"
for the whole cluster: every binding edge with resolved provider, actual
state, gap codes, and freshness; unreferenced services listed as information.
Output agrees with `nctl drift` on binding states. Nothing persisted.
