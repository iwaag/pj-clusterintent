# Phase 2 Report — Resolution, Drift, and Inventory from the Binding Model

Status: **complete**. All five steps in [plan.md](plan.md) executed; the
Phase 1 restriction on `node_agent` placement actuation is **lifted**.

## Step 1 — Fetch bindings

Verified the live scratch Nautobot GraphQL schema (read-only query) before
coding: `desired_service_bindings { id binding_name consumer_placement { id }
provider_service { id slug } }` matches the plan's guess exactly. Three real
rows exist (aghub/agpc/agstudio `node-agent` → `llm_provider` → `ollama`),
confirming Phase 1's migrated state is still in place.

Added `DesiredServiceBinding` to `sources/desired.py` (query + read-model +
snapshot field), a `BindingInput` dataclass on `PlacementInput.bindings` in
`production/model.py`, and threaded it through `production/adapter.py`
(`bindings_by_placement`, sorted by `(binding_name, id)`).

Test fixtures across the suite needed a `"desired_service_bindings": []` key
added to every stubbed GraphQL response (`test_sources_desired.py`,
`test_drift_render.py`, `test_deployment_profile_availability_contract.py`,
`test_reconcile_ledger.py`, `test_sources_snapshot.py`,
`test_intent_effect_summary_contract.py`, `test_compute_collection.py`,
`test_dnsmasq_render.py`).

Commit: `7f5dc33` — suite green (1040 passed).

## Step 2 — Binding-driven resolver

Rewrote `nctl_core/production/service_dependencies.py` from scratch:

- Trigger changed from "`llm_provider_service` config key present" to
  "binding rows exist on an active consumer placement". Walk: binding →
  provider service (by `service_id`, not slug) → exactly one active
  placement → usable endpoint → URL.
- Deleted the `primary: true` tiebreak entirely (contradicted idea-A §4; no
  test depended on it once the config-key path was gone).
- New error codes (idea-A §6): `binding_name_undeclared`,
  `binding_self_reference`, `binding_provider_missing`,
  `binding_provider_ambiguous`, `binding_cycle`, `binding_endpoint_missing`,
  `binding_endpoint_invalid`, `binding_endpoint_unusable`. Self-reference and
  cycle are classified (not asserted) since the resolver reads a snapshot it
  doesn't control — a small DFS (`_reaches`) walks the binding graph through
  every active placement's bindings to detect cycles back to the consumer's
  own service.
- `PROFILE_BINDING_VARIABLES = {("node_agent", "llm_provider"):
  "nintent_opencode_ollama_url"}` is the nctl twin of nintent's
  `PROFILE_BINDING_NAMES`; an unknown `(profile, binding_name)` pair is
  `binding_name_undeclared`, not a crash.
- Multiple bindings per consumer placement now resolve independently and
  merge variables/provenance (the old "more than one dependency is an error"
  check is gone, per the plan).
- Updated the two allowlists that must track error-code renames:
  `SERVICE_DEPENDENCY_LOCAL_CODES` in `composer.py` and
  `reconcile/classify.py`'s manual-review code list. Updated
  `_SERVICE_DEPENDENCY_KEYS` in `contract.py` to
  `{consumer_placement_id, binding_name, provider_service_slug,
  provider_placement_id, endpoint_id}`.
- Rewrote `test_service_dependencies.py` wholesale (14 tests): happy path,
  no-bindings-no-entry, inactive-placement-ignored, provider missing,
  provider ambiguous, endpoint missing, endpoint invalid (wrong node),
  endpoint unusable (no port), undeclared binding name, self-reference,
  provider cycle, multi-binding merge.
- Added one end-to-end drift test
  (`test_ambiguous_binding_provider_surfaces_as_node_local_drift` in
  `test_drift_render.py`): a snapshot where `ollama` has two active
  placements makes the consumer node's `nctl drift` output show
  `binding_provider_ambiguous` as a node-targeted diff, proving the
  resolver-error → `LocalCompositionError` → node-local-drift path still
  works unchanged.

Commit: `e18da8c` — suite green (1050 passed). Grep-clean for
`llm_provider_service` outside devdocs and this report's own retrospective
mention.

## Step 3 — Reverse view in prune

Added `reverse_service_bindings(nodes) -> dict[str, list[dict]]` to
`service_dependencies.py`: a pure function over the snapshot mapping each
provider `service_id` to its sorted list of
`{consumer_node, consumer_service, binding_name}` entries. Derived on demand,
never persisted, per hard rule 1.

Wired into `retirement_prune.py`: `_inbound_consumers(snapshot, node)` finds
the node's actively-hosted service IDs and looks up their inbound bindings,
included as `eligibility["inbound_consumers"]` in every branch of `_resolve`
(both `ineligible` and `eligible` outcomes) so the dry plan (`eligibility.json`
artifact) always shows who would be orphaned before nintent's own
`_DELETE_BLOCKERS` refusal ever triggers. `render_prune_text` prints a
human-readable "Inbound consumers (N)" section when non-empty.

Confirmed the deeper mechanism this builds on: nintent's `_DELETE_BLOCKERS`
(`nautobot_intent_catalog/batch.py`) already covers `desired_service` →
`inbound_bindings` and `desired_service_placement` → `service_bindings`, so a
raw `nctl desired apply` dry-run of a service/placement delete already comes
back `conflict` with a `reason` string listing blocking binding/placement
pks — verified live in Step 4.

Variable-name decision: kept `nintent_opencode_ollama_url` (roadmap explicitly
allows either choice); no edit to `setup_opencode.yml` needed.

Tests added: 2 in `test_service_dependencies.py` (lists inbound consumers
sorted, ignores inactive placements), 1 in `test_retirement_prune.py`
(eligibility surfaces inbound consumers for a hosted provider service).

Gates: nctl suite 1053 passed; Ansible conformance gate
(`devtests/test_strategy/test_ansible_conformance.py`) 3 passed — unaffected,
as expected (it exercises SSH/inventory trust, not service dependencies).

Commit: `c4f4edb`.

## Step 4 — Live read-only verification

Against the scratch Nautobot (`http://localhost:8000/`):

1. **`nctl drift --json`**: aghub, agpc, agstudio all `converged`, each
   carrying a `service_dependencies` provenance entry with the new key shape
   (`consumer_placement_id`, `binding_name: "llm_provider"`,
   `provider_service_slug: "ollama"`, `provider_placement_id`,
   `endpoint_id`) — binding-driven resolution confirmed live, closing the
   gap Phase 1 left open (config keys removed from placements, old resolver
   returning nothing).
2. **`nctl render production`**: all three hosts emit
   `nintent_opencode_ollama_url: http://agstudio.home.arpa:11434/v1`.
3. **Dry-run batch delete of `ollama`**
   (`nctl desired apply -f <doc> --json`, `dry_run: true`,
   `{op: delete, kind: desired_service, key: {slug: ollama}}`): returned
   `action: conflict`, `reason: "blocked by: desired_service_binding:<id
   ×3>, desired_service_placement:<id>"` — the three blocking binding ids
   matched exactly the three live bindings queried in Step 1
   (aghub/agpc/agstudio), confirming the three-consumer inbound set is
   visible and the deletion is refused.

## Step 5 — Live actuation (approved)

User approval obtained before proceeding (this is real-node actuation, the
first `node_agent` write since the Phase 1 freeze).

- `nctl reconcile aghub --yes` → `state: already_converged`,
  `scope summary: converged=2`, `ok: True`. No config rewrite occurred — the
  node was already correctly configured from binding-driven resolution, as
  predicted.
- `nctl agent run aghub --prompt "Say OK and nothing else."` → succeeded, new
  OpenCode session created, model replied `OK`. This proves the resolved
  `nintent_opencode_ollama_url` (driven entirely by the `DesiredServiceBinding`
  row, not any placement config) is a real, reachable endpoint the node agent
  actually used.
- Post-actuation `nctl drift --json` re-checked: aghub, agpc, agstudio still
  `converged`. No divergence; nothing to investigate.

**The Phase 1 "do not actuate `node_agent` placements" restriction is
lifted.**

## Completion criteria (roadmap, verified)

- ✅ `nctl reconcile aghub --yes` followed by `nctl agent run aghub` works
  with zero per-host Ansible mapping, driven entirely by binding rows.
- ✅ Deleting `ollama` from desired state is visibly blocked with its
  consumer list in the dry plan (3 binding ids, matching the 3 live
  consumers).
- ✅ Grep-clean for `llm_provider_service` outside devdocs
  (`grep -rn llm_provider_service nctl/src nctl/tests` → no hits).
- ✅ Production inventory/provenance for aghub/agpc/agstudio restored and
  recorded above; gate counts: nctl suite 1053 passed (was 1040 at Step 1,
  1050 at Step 2, 1053 at Step 3 — 13 net new tests across the phase),
  Ansible conformance gate 3 passed.

## Next

Phase 3 (consumer-side actual evidence / binding states) per
[roadmap.md](../roadmap.md) — not started.
