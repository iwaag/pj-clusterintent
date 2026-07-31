# Service Relation Roadmap

Realize [idea-A.md](idea-A.md) — service bindings as desired and actual
state — in phases. Each phase gets its own concrete plan (`pN/plan.md`) when
it starts; this document fixes only the order, the goal, and the completion
meaning of each phase.

Context: experimental scratch environment. No backward compatibility, no
migration shims, no legacy input support. Implementers have wide discretion on
code layout, API shape, and test strategy; the few hard rules are listed at
the end.

## Phase 0 — Precondition cleanup

Clear the known-broken observation substrate before building on it.

- Push the pending nodeutils commits (provider observation fix from
  `systemic_serice_coop`); the remote collector installs nodeutils from
  GitHub, so unpushed commits are invisible to it.
- Rerun `nctl reconcile agstudio --refresh-observation --yes` and confirm the
  `ollama` service converges (the last run stopped at
  `manual_intervention_required`).
- Commit the `service_relation` design docs (currently untracked).

Completion: whole-cluster `nctl drift` is converged and the design docs are in
git.

## Phase 1 — Desired model and batch validation

Add `DesiredServiceBinding` to nintent and enforce the idea-A invariants at
the only desired-state writer.

- Model per idea-A §3.1: `consumer_placement` FK, `binding_name`,
  `provider_service` FK; identity `(consumer_placement, binding_name)`.
  Nothing else — no status, no type, no notes.
- Batch endpoint validates §4 (active endpoints resolvable, exactly one
  active provider placement, usable endpoint, acyclic, profile declares the
  binding name) and §8 (reject retiring/deleting a provider or its placement
  or endpoint while inbound bindings remain, unless the same atomic batch
  removes or retargets them). Rejection errors include the exact inbound set.
- Same change, one-way migration: convert the existing
  `llm_provider_service: ollama` config entries (aghub, agstudio node-agent
  placements) into bindings via a desired-state batch, and make the
  `node_agent` profile reject the old config key. Drop-and-recreate
  migrations are fine; there is no production data.

Hints: the removed model is at nintent `aca2fa9^` — useful as a list of what
not to rebuild. Cycle checking only needs to walk binding → provider service →
active placement → that placement's bindings; the graph is tiny.

Completion: an invalid batch (ambiguous provider, cycle, protected deletion)
is rejected with a precise error; the valid converted state applies cleanly;
old config key is refused.

## Phase 2 — Resolution, drift, and inventory from the binding model

Port the consumer side of nctl to read bindings instead of placement config.

- Rework `nctl_core/production/service_dependencies.py` to resolve
  `DesiredServiceBinding` rows; keep its classified errors and provenance
  reporting. Delete the config-key reading path entirely.
- `nctl drift` reports desired-resolution failures per idea-A §6 (provider
  missing/ambiguous, endpoint unusable, invalid binding name, self-reference,
  cycle) as node-local drift, as the resolver errors do today.
- Production inventory keeps emitting `nintent_opencode_ollama_url` (or a
  renamed generalized variable — implementer's choice) with provenance.
- Add the reverse view: given a provider, list its consumer placements and
  binding names. Surface it minimally — `nctl prune` / retirement dry plans
  must show the inbound set; a dedicated subcommand is optional here.

Completion: `nctl reconcile aghub --yes` followed by a short
`nctl agent run aghub` works with zero per-host Ansible mapping, driven
entirely by binding rows; deleting `ollama` from desired state is visibly
blocked with its consumer list.

## Phase 3 — Consumer-side actual evidence

Observe each binding at the consumer and evaluate the five states.

- nodeutils, per binding on the observed node: read the profile-allowlisted
  config slot (for `node_agent`: the OpenCode provider URL), normalize it,
  and run one bounded reachability probe (a few seconds) against the
  configured endpoint from the consumer node. Emit
  `binding_name / configuration_status / configured_endpoint /
  reachability_status / observed_at` per idea-A §5.
- Ingest through the existing `observed_services` actual-state channel; do
  not add a parallel ledger.
- nctl evaluates `unknown / unbound / misbound / unreachable / satisfied`
  and folds the result into convergence: a binding is converged only when
  resolution succeeds, the state is `satisfied`, and the provider placement
  is itself converged. Stale or absent evidence is `unknown`, and `unknown`
  is not converged — pick a freshness threshold up front and write it down.

Hints: endpoint normalization must be identical on the desired and observed
sides or `misbound` will flap; share one normalization function. The probe
must run on the consumer node (nodeutils), not from the controller — the
agstudio DNS incident is the reference case for why the perspectives differ.

Completion: manually mis-editing the OpenCode config on one node produces
`misbound` drift; stopping Ollama produces `unreachable`; restoring both and
reconciling returns the cluster to converged.

## Phase 4 — Inspection projection

One deterministic graph view for humans and agents, derived on demand.

- A `nctl` command (e.g. `nctl relations --json`) emitting per-edge: consumer
  service/placement, binding name, provider service, resolved placement and
  endpoint, actual binding state, gap codes, and evidence freshness — idea-A
  §9. Derived from current desired + actual state, never persisted.
- Include the `unreferenced` service list, clearly labeled as informational,
  not a deletion recommendation.
- Text/JSON output is sufficient; graph drawing is out of scope.

Completion: one command answers "who depends on what, and is it real" for the
whole cluster.

## Deferred (design separately if ever needed)

Everything in idea-A §10: optional bindings, multi-provider/failover,
external providers, version/capability matching, config-file discovery,
automatic retirement, historical telemetry, graphical UI.

## Hard rules (the minimum)

1. Resolution and binding state are computed, never stored or hand-edited.
2. The batch endpoint remains the sole desired-state writer; invariants are
   enforced there atomically.
3. Observation returns only the allowlisted slot value — never whole config
   files or credentials.
4. No dual sources of truth: the old config key dies in the same change that
   introduces the model.
5. Nothing is auto-deleted from graph degree; `unreferenced` is information
   only.

Everything else — schema details, code layout, CLI naming, test structure,
scratch-DB rebuilds, migration squashing — is implementer's discretion.
