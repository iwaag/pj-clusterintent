# Phase 2 Plan — Resolution, Drift, and Inventory from the Binding Model

Goal (from [roadmap](../roadmap.md) Phase 2): port the consumer side of nctl
from the dead `llm_provider_service` config key to `DesiredServiceBinding`
rows — resolution, drift surfacing, production inventory, and the reverse
(provider → consumers) view — and thereby lift Phase 1's "do not actuate
`node_agent` placements" restriction.

Experimental environment: no backward compatibility, no legacy input. The old
config-key path is deleted, not deprecated. Everything below not under "Hard
rules" or "Completion criteria" is a recommendation — implementer's
discretion.

## Scope

In: nctl desired-state fetch (bindings), rework of
`nctl_core/production/service_dependencies.py`, composer/contract error-code
and provenance updates, reverse inbound-set view surfaced in prune/retirement
dry plans, live verification ending in `nctl reconcile aghub --yes` +
`nctl agent run aghub`.

Out (later phases): consumer-side observation, binding states
(`unknown/unbound/misbound/unreachable/satisfied`), freshness, and probe
(Phase 3); the `nctl relations` projection (Phase 4). nintent changes are
expected to be **zero** this phase — the model, batch validation, and §8
protection already shipped in Phase 1.

## Facts gathered during planning

- **The resolver to rework:**
  `nctl/src/nctl_core/production/service_dependencies.py` (~140 lines, pure).
  It scans active `node_agent` placements for a non-empty
  `config["llm_provider_service"]`, resolves the provider service slug to its
  single active placement + endpoint, and returns per-consumer-node
  `ServiceDependencyResolution(variables, provenance, error_*)`. It also has a
  `primary: true` tiebreak for multi-placement providers — this contradicts
  idea-A §4 (exactly one active provider placement, no implicit fallback) and
  the Phase 1 nintent validator already rejects such states; delete it.
- **Live data:** three real bindings exist (aghub/agpc/agstudio `node-agent`
  placements → `llm_provider` → `ollama`), applied in Phase 1 Step 7. The
  placement configs no longer carry the old key, so the current resolver
  resolves nothing — that is the known Phase 1 gap this phase closes.
- **How errors already become drift:** `composer.py:243` calls
  `resolve_service_dependencies(all_nodes)`; in `_compose_host` an
  `error_code` raises `LocalCompositionError(stage="service_dependency")`,
  which marks the node `skipped` with the code as reason — that is what the
  roadmap means by "as the resolver errors do today". You get §6 desired-
  resolution failures as node-local drift for free by keeping this shape.
  Two allowlists must track your new codes:
  `SERVICE_DEPENDENCY_LOCAL_CODES` in `composer.py` (~line 95) — an
  unexpected code escaping the per-node loop is re-raised, not downgraded —
  and the report contract in `production/contract.py`, where
  `_SERVICE_DEPENDENCY_KEYS` (~line 516) enforces the *exact* key set of each
  provenance entry. If you change provenance keys, update that constant or
  every report validation fails.
- **On success:** `variables` are merged into host vars
  (`base_vars.update`) and `provenance` lands in
  `NodeOutcome.service_dependencies` → the node report. Keep both behaviors.
- **Fetch layer:** `nctl_core/sources/desired.py` holds the one pinned
  GraphQL query (`DESIRED_QUERY`) + pydantic read-models; bindings are not
  fetched yet. `DesiredServiceBinding` carries `@extras_features("graphql")`
  (nintent `models.py:742`), so a root query — presumably
  `desired_service_bindings` — should exist. **Verify the exact field name
  and shape against the live scratch Nautobot GraphQL before coding** (the
  file's docstring pattern: pinned queries are empirically checked). You need
  `id`, `consumer_placement { id }`, `binding_name`,
  `provider_service { id slug }`. No ChoiceFields on this model, so the
  UPPERCASE-enum-name gotcha does not apply.
- **Adapter:** `production/adapter.py` builds `NodeInput`/`PlacementInput`
  from the snapshot. Bindings must reach the resolver somehow — a
  `bindings: tuple[...]` field on `PlacementInput`, or a separate
  `bindings_by_placement` argument to `resolve_service_dependencies`; your
  choice. The resolver stays pure either way.
- **Endpoint URL:** `_endpoint_url` demands address + protocol in
  `{http, https}` + port 1–65535, brackets IPv6, and appends `/v1`. Phase 1's
  nintent "usable endpoint" check was written to mirror exactly this, so the
  two sides agree on "usable" today — don't loosen one without the other.
  The `/v1` suffix is OpenCode-specific; fine for now, but keep the function
  pure and importable, because Phase 3 must share one normalization between
  desired and observed sides or `misbound` will flap.
- **Inventory variable:** `nintent_opencode_ollama_url` has exactly one
  consumer: `ansible_agdev/playbooks/agent/setup_opencode.yml` (asserts
  defined/string/non-empty, maps it to `opencode_agent_ollama_url`). Renaming
  to something binding-derived (e.g. `nintent_binding_llm_provider_url`) is
  allowed and means editing that one playbook in the same change; keeping the
  old name is equally fine. Roadmap leaves this to you.
- **Binding-name → variable knowledge:** the resolver must know that binding
  `llm_provider` on profile `node_agent` produces this variable. A small
  constant map in `service_dependencies.py` (the nctl twin of nintent's
  `PROFILE_BINDING_NAMES = {"node_agent": ("llm_provider",)}`) is enough; an
  unknown binding name arriving from desired state is a classified error
  (§6 "invalid binding name"), not a crash.
- **Reverse view / prune:** `nctl_core/retirement_prune.py` builds delete
  operations (`_desired_operations`) and an eligibility dict for `nctl prune`.
  Deleting a provider-hosting node's endpoint/placement is already refused by
  nintent's §8 validator and pre-flagged by `_DELETE_BLOCKERS` in the batch
  dry-run plan — the roadmap requirement is that the inbound set is *visible
  in the dry plan*. Confirm the `submit_batch` dry-run path actually surfaces
  the blocker detail in prune output; add a small pure helper (bindings →
  inbound set per provider) and include it in the prune plan/eligibility
  output. A dedicated `nctl` subcommand is optional — skip it unless it costs
  nothing.
- **Tests:** nctl ordinary suite is 1040 passing
  (`uv run pytest -q` in `nctl/`). `tests/test_service_dependencies.py` (3
  tests) is written against the config key and will be rewritten wholesale.
  Fixture placements elsewhere may still carry `llm_provider_service` in
  configs — grep and strip them; nintent now refuses that key, and dead
  fixture data invites confusion.
- **Deployment:** nctl runs locally (`uv run --project nctl nctl ...`) — no
  Nautobot rebuild needed for nctl-only changes. Only if you discover a
  missing nintent GraphQL exposure does the nintent deploy loop apply
  (commit → ask user to push → `docker compose build --no-cache`, check the
  resolved SHA in the build log → restart; see `.local/localenv_memo.md`).

## Design decisions and recommendations

### Resolution (rework, don't rewrite around)

Keep the module's proven shape: pure function, per-consumer-node result,
classified errors with evidence, deterministic. Change the *input trigger*
from "config key present" to "binding rows exist for an active consumer
placement", and generalize the walk per idea-A §4/§6:

binding → provider service (must be active) → exactly one active placement →
usable endpoint → URL.

Error codes are yours to name; a reasonable set mirroring §6:
`binding_provider_missing`, `binding_provider_ambiguous`,
`binding_endpoint_missing/invalid/unusable`, `binding_name_undeclared`,
`binding_self_reference`, `binding_cycle`. Renaming the old `llm_provider_*`
codes is encouraged (no compatibility); just update both allowlists and any
render/test string that mentions them. Self-reference and cycle *should* be
impossible in stored state (nintent rejects them at write time), but the
resolver reads a snapshot it doesn't control — classify them, don't assert.

Multiple bindings per consumer placement are legal in the model (identity is
`(consumer_placement, binding_name)`); today only `llm_provider` exists.
Resolve per binding, merge variables; the old "more than one dependency on a
node is an error" check dies with the config path.

### Drift

No new drift machinery. Resolver error → `LocalCompositionError` → skipped
node with reason code → node-local drift, exactly as today. Verify with one
end-to-end drift test (e.g. a snapshot where `ollama` has two active
placements → consumer nodes show the ambiguity code in `nctl drift --json`).

### Inventory and provenance

Keep emitting the URL variable with provenance
(`consumer_placement_id`, `binding_name`, provider placement + endpoint ids —
adjust `_SERVICE_DEPENDENCY_KEYS` to whatever you settle on). The completion
test is that `nctl render production` / `nctl drift` provenance for the three
migrated nodes comes back, driven by binding rows.

### Reverse view

One pure function over the snapshot: provider service (and its active
placement) → sorted list of `consumer_node / consumer_service / binding_name`.
Use it in prune/retirement dry output; idea-A §8's literal shape is the
target rendering. Don't persist anything.

## Steps

Follow the phase execution style: one report section + one commit per step;
pause for user judgment before live/hard-to-reverse actions.

1. **Fetch bindings.** Verify the GraphQL field against live Nautobot
   (read-only), extend `DESIRED_QUERY` + `DesiredSnapshot` with a
   `DesiredServiceBinding` read-model, thread it through
   `sources/snapshot.py` and the adapter. Suite green.
2. **Rework the resolver.** Binding-driven resolution, new error codes,
   delete the config-key path and the `primary` tiebreak, update
   `SERVICE_DEPENDENCY_LOCAL_CODES` + `_SERVICE_DEPENDENCY_KEYS`, rewrite
   `test_service_dependencies.py` (cover: happy path, provider missing,
   ambiguous, endpoint unusable, undeclared binding name, self-reference,
   cycle, multi-binding merge). Strip any stale `llm_provider_service` from
   fixtures. One end-to-end drift test for the error → node-local-drift path.
3. **Reverse view in prune.** Inbound-set helper + surface it in
   `nctl prune` dry output; confirm the batch dry-run blocker detail is
   visible. Decide and apply the variable-name choice (edit
   `setup_opencode.yml` if renaming). Full gates: nctl suite, Ansible
   conformance gate.
4. **Live read-only verification.** Against the scratch Nautobot:
   `nctl drift --json` shows the three nodes converged with binding-driven
   provenance restored; `nctl render production` emits the URL variable for
   all three; a dry-run batch deleting `ollama` is refused/blocked showing
   the three-consumer inbound set. Record outputs.
5. **Live actuation** (pause: get user approval — this touches real nodes,
   and it is the first `node_agent` actuation since the Phase 1 freeze).
   `nctl reconcile aghub --yes`, then a short `nctl agent run aghub`.
   The nodes are already correctly configured, so expect a no-op/converged
   result — a config rewrite here means the rendered URL diverged from
   reality; stop and investigate before touching more nodes. Record
   everything in `p2/report.md`; state explicitly that the Phase 1
   actuation restriction is lifted.

## Hard rules (the only prohibitions)

- Resolution stays computed, never stored (roadmap hard rule 1); the reverse
  view is derived on demand, never persisted.
- The config-key reading path is deleted in this same change — no fallback,
  no dual source (hard rule 4).
- Do not push nctl/nintent/ansible_agdev yourself; ask the user.
- No consumer-side observation or binding-state evaluation — that is
  Phase 3's contract; don't pre-build half of it.
- Pause for user approval before Step 5's live actuation.

## Completion criteria (roadmap, restated)

- `nctl reconcile aghub --yes` followed by a short `nctl agent run aghub`
  works with zero per-host Ansible mapping, driven entirely by binding rows.
- Deleting `ollama` from desired state is visibly blocked with its consumer
  list in the dry plan.
- The old config-key path no longer exists in nctl (grep-clean for
  `llm_provider_service` outside devdocs).
- Production inventory/provenance for aghub/agpc/agstudio is restored and
  recorded, plus all gate runs with counts, in `p2/report.md`.
