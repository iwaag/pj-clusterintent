# Phase 1 Report — Desired Model and Batch Validation

Status: complete (2026-08-01). All 7 plan steps done; see `report1.md`
through `report7.md` for per-step detail. This is the roll-up.

## What shipped

- **`DesiredServiceBinding` model** (nintent, migration `0025`): identity
  only — `consumer_placement`, `binding_name`, `provider_service` — per
  idea-A §3.1. No status/type/notes/lifecycle field.
- **`desired_service_binding` batch kind**: wired through the whole batch
  envelope (`KIND_ORDER`, `_KEYS`, `_FIELDS`, `_CREATE_REQUIRED`,
  `_models()`, `_REFERENCE_KIND`, API permission map).
- **Per-row checks** (idea-A §4.7 and the old-key refusal): `PROFILE_BINDING_NAMES
  = {"node_agent": ("llm_provider",)}` and `REFUSED_PROFILE_CONFIG_KEYS =
  {"node_agent": ("llm_provider_service",)}`, enforced in
  `DesiredServiceBinding.clean()` / `DesiredServicePlacement.clean()` inside
  the existing per-operation `full_clean()` loop.
- **Final-state graph invariants** (idea-A §4.1–4.6) and **§8 retirement/
  deletion protection**: one validator (`_validate_service_binding_graph`)
  run once at the end of every `apply_batch` transaction, so §8 falls out of
  the same resolution-failure code path rather than a separate check.
  Provider-side failures (unresolved/ambiguous/inactive/unusable endpoint)
  report the exact inbound set in idea-A §8's literal shape; self-reference
  and cycle get their own concise messages. `_DELETE_BLOCKERS` extended so a
  `desired_service`/`desired_service_placement` delete conflict shows up in
  the dry-run plan before ever reaching the transaction.
- **Profile contract**: `ansible_agdev/vars/deployment_profiles.yml`'s
  `node_agent` profile no longer declares `llm_provider_service`.
- **Live one-way migration**: the three real `node_agent` placements
  (`aghub`, `agpc`, `agstudio`) converted from `config.llm_provider_service:
  ollama` to `llm_provider -> ollama` `DesiredServiceBinding` rows, applied
  atomically against the local scratch Nautobot.

## Verification summary

- Django-free suite (`nintent/`): 129 tests, OK (10 skipped), unchanged skip
  count throughout.
- Runtime gate (`run_nautobot_runtime_gate.sh`): `--keepdb` at each
  iteration (25 → 33 → 206 cases as coverage grew), final `--clean` run
  (required — new migration) also green at 206 cases, migrating from an
  empty database.
- `nctl` ordinary suite: 1040 passed, unaffected by the profile edit.
- Ansible conformance gate: 3 passed, unaffected (different scope).
- Live acceptance against the local scratch Nautobot (see `report7.md` for
  full transcripts): old-key reintroduction refused; ambiguous provider
  refused (exact 3-consumer inbound set); a length-1 self-reference cycle
  and a genuine two-node cycle both refused; retiring and deleting `ollama`
  both refused, each showing `provider: ollama / ollama-agstudio` plus all
  three real consumers (`aghub`/`agpc`/`agstudio` `/ node-agent /
  llm_provider`); `nctl drift --json` shows all three migrated nodes
  `converged` with no new drift.

## Completion criteria (roadmap, restated) — met

- An invalid batch (ambiguous provider, cycle, protected deletion/retirement)
  is rejected with a precise error naming the exact inbound set. ✓ (shown
  live, Step 7)
- The converted state (three `llm_provider` bindings to `ollama`, stripped
  configs) applies cleanly and atomically. ✓ (Step 7, `committed`, 0
  conflicts)
- A batch reintroducing `llm_provider_service` in a `node_agent` config is
  refused. ✓ (Step 7)
- All gate runs recorded with counts, plus the post-migration `nctl drift`
  delta. ✓ (`report4.md`, `report7.md`)

## Known interim gap (unchanged, accepted per plan)

`nctl_core/production/service_dependencies.py` still reads the old config
key and was deliberately not touched this phase. Production inventory now
loses `nintent_opencode_ollama_url` provenance for the three migrated nodes
until Phase 2 ports the resolver to `DesiredServiceBinding`. Do not run `nctl
reconcile --yes` actuation against `node_agent` placements until Phase 2
lands — the running nodes are already correctly configured, so simply not
actuating them is sufficient.

## Next

Phase 2 — port `nctl_core/production/service_dependencies.py` to resolve
`DesiredServiceBinding` rows, per `roadmap.md`. Its plan should be written at
`p2/plan.md` when that phase starts.
