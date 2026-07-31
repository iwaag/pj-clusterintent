# Step 7 Report — Live Migration + Acceptance

Status: complete.

## Live identities verified before writing the batch

Queried the live scratch Nautobot directly (not trusted from `p0/report.md`
blindly, per the plan):

- Three `node_agent` placements, all `config: {llm_provider_service:
  ollama}`, all `desired_state: active`: `node-agent / node-agent-aghub`
  (node `aghub`), `node-agent / node-agent-agpc` (node `agpc`), `node-agent /
  node-agent-agstudio` (node `agstudio`).
- `ollama` service: `lifecycle: active`, exactly one active placement
  `ollama-agstudio`, endpoint `http://agstudio.home.arpa:11434` (protocol
  `http`, port `11434`, `dns_name` set) — resolvable per idea-A §4.3/§4.4.

## Migration batch

`.local/service-relation-p1-migration.yaml` (gitignored, per the plan): six
operations — one `desired_service_binding` upsert
(`binding_name: llm_provider`, `provider_service: ollama`) plus one
`desired_service_placement` config-strip (`config: {}`, whole-config
replace) per consumer placement.

- Dry-run (`nctl desired apply -f ... --json`): `totals: {create: 3, update:
  3, delete: 0, conflict: 0}`, zero errors. Shown to the user before
  applying.
- Applied (`--yes`): `transaction.status: committed`. Verified directly in
  the container: all three `DesiredServiceBinding` rows exist
  (`aghub/agpc/agstudio llm_provider -> ollama`), all three placements'
  `config` is now `{}`.

## Acceptance demonstrations (all against the live scratch Nautobot)

1. **Old-key batch refused.** Upsert re-adding
   `config: {llm_provider_service: ollama}` to `node-agent-aghub`:
   `status: rolled_back`, error names `config` and
   `"Deployment profile 'node_agent' no longer accepts config key(s):
   llm_provider_service"`. Confirmed the row's `config` is still `{}` after
   the rollback.
2. **Ambiguous provider refused.** Created a second active `ollama`
   placement (`ollama-p1-scratch`, scratch node/endpoint) directly via ORM,
   then triggered the validator with a harmless real `apply_batch` call:
   `status: rolled_back`, error:
   `provider: ollama / (ambiguous: ollama-agstudio, ollama-p1-scratch)` plus
   the exact three-consumer list (`aghub`, `agpc`, `agstudio` /
   `node-agent` / `llm_provider`). Scratch rows deleted afterward; confirmed
   `ollama` is back to exactly one active placement.
3. **Cycle refused.** Two genuine cases:
   - Self-reference (length-1 cycle): a scratch node/service/placement bound
     to its own service — rejected with `"binding resolves back to its own
     consumer placement"`.
   - Two-node cycle: two scratch placements each bound to the other's
     service (`placement1 -> service2 -> placement2 -> service1 ->
     placement1`) — rejected with `"service binding graph contains a cycle:
     p1-cycle-service-2/p1-cycle-instance-2 -> p1-cycle-service/
     p1-cycle-instance -> p1-cycle-service-2/p1-cycle-instance-2"`. All
     scratch rows deleted afterward.
4. **Protected retire/delete refused, exact inbound set shown.**
   - Retiring `ollama` (`lifecycle: retired`) via `apply_batch`:
     `status: rolled_back`, error:
     `provider: ollama / ollama-agstudio` then all three real consumer
     lines (`aghub`, `agpc`, `agstudio` / `node-agent` / `llm_provider`).
     Confirmed `ollama.lifecycle` is still `active` after rollback.
   - Deleting `ollama` (dry-run plan): `action: conflict`, `reason` lists
     `desired_service_binding:<pk>` for all three real bindings plus
     `desired_service_placement:<pk>` for its own placement — caught before
     ever reaching the transaction, per the `_DELETE_BLOCKERS` extension
     from Step 3.

## `nctl drift --json` after migration

`summary: {converged: 10, drifting: 3, unknown: 3}`. `aghub`, `agstudio`,
`agpc` are all `status: converged` with no `missing_required_config` (or any
other) diff — the profile no longer requiring the old key and the config no
longer carrying it agree, so no new drift appeared on the three migrated
nodes. The 3 drifting / 3 unknown targets are the pre-existing, unrelated
ones already noted in `p0/report.md` (`agdnsmasq`, `agbach`,
`pj-voxel3dprint`, `prometheus`, `dnsmasq`); one item moved from `drifting`
to `converged` since the Phase 0 snapshot (unrelated to this phase).

## Cleanup

All scratch nodes/services/placements/bindings created for the ambiguous-
provider and cycle demonstrations were deleted afterward. No leftover rows.
`/tmp` scratch batch documents removed. The real migration batch document
remains at `.local/service-relation-p1-migration.yaml` (gitignored) as a
record.

## Next

Phase 1 is complete. Phase 2 (`nctl_core/production/service_dependencies.py`
resolving `DesiredServiceBinding` instead of the config key) can start
whenever the user is ready; until then, do not run `nctl reconcile --yes`
actuation against `node_agent` placements (accepted interim gap, unchanged
from `p0`/plan).
