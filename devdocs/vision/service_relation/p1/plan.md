# Phase 1 Plan — Desired Model and Batch Validation

Goal (from [roadmap](../roadmap.md) Phase 1): add `DesiredServiceBinding` to
nintent, enforce the [idea-A](../idea-A.md) §4/§8 invariants at the batch
endpoint, and in the same change migrate the three existing
`llm_provider_service: ollama` config entries to binding rows while making the
old config key refused.

Experimental environment: no backward compatibility, no legacy input, no
production data. Drop-and-recreate migrations are fine. Everything below that
is not under "Hard rules" or "Completion criteria" is a recommendation —
implementer's discretion.

## Scope

In: nintent model + migration, nintent batch validation, the one-way migration
batch, removal of the `llm_provider_service` variable from the `node_agent`
profile contract, local + live verification.

Out (later phases): nctl resolution/drift/inventory (Phase 2), consumer-side
observation and binding states (Phase 3), the `nctl relations` projection
(Phase 4). Do not touch `nctl_core/production/service_dependencies.py` in this
phase.

## Facts gathered during planning

- **Model site:** `nintent/nautobot_intent_catalog/models.py`. Relevant
  existing models: `DesiredService` (slug unique, lifecycle choices incl.
  `active`/`retired`), `DesiredServicePlacement` (identity
  `(desired_service, instance_name)`, `desired_state` active/disabled,
  `deployment_profile` slug, `desired_endpoint` nullable FK), `DesiredEndpoint`
  (identity `(desired_node, name, endpoint_type)`, has `protocol`, `port`, and
  several address fields).
- **Batch site:** `nintent/nautobot_intent_catalog/batch.py` (~344 lines) is
  the whole planner/applier. To add a kind you touch: `KIND_ORDER`, `_KEYS`,
  `_FIELDS`, `_CREATE_REQUIRED`, `_models()`, `_REFERENCE_KIND` (add
  `consumer_placement -> desired_service_placement`,
  `provider_service -> desired_service`), and `_DELETE_BLOCKERS`.
  `_reference_identity` already supports dict identities, which
  `consumer_placement` needs (`{"desired_service": ..., "instance_name": ...}`).
  Upsert replaces `config` wholly (dict equality compare, then `setattr`), so a
  migration batch can strip a config key by upserting the config without it.
- **Anti-model:** the removed `DesiredDependency` is at nintent `aca2fa9^`
  (`git show aca2fa9^:nautobot_intent_catalog/models.py`). It had
  `resolution_status`, `resolved_service`, `dependency_type`, `notes` — all of
  which idea-A §3.1 forbids. Its removal commit `aca2fa9` is also a complete
  checklist of the UI surfaces a model touches (filters, tables, navigation,
  templates, urls, views, factories) — useful both ways.
- **Profile contract:** `ansible_agdev/vars/deployment_profiles.yml`,
  `node_agent` profile, declares `llm_provider_service` with `required: true`.
  nctl's production contract enforces required keys
  (`missing_required_config`) and closed key sets, so once the variable is
  removed from that file, a placement config still carrying the key fails
  composition — that is the nctl-side half of "old key refused".
- **Rows to migrate:** exactly three active `node_agent` placements carry
  `config.llm_provider_service: "ollama"`: aghub, agstudio, agpc (agpc was
  added during Phase 0 — see [p0/report.md](../p0/report.md)). Verify the
  exact placement identities against live desired state before writing the
  migration batch; do not trust this list blindly.
- **Migration numbering:** latest nintent migration is
  `0024_remove_desiredservice_backstage_identity.py`; yours will be 0025+.
- **Deployment path:** local Nautobot installs nintent from GitHub
  (`pip install git+...`), not a mount. Reflecting changes requires commit →
  push (ask the user to push; do not push yourself) →
  `docker compose build --no-cache` (plain build can silently cache a stale
  nintent commit — check the resolved SHA in the build log) → migrate →
  restart. See `.local/localenv_memo.md`.

## Design decisions and recommendations

### Model (§3.1 — exact, nothing more)

`DesiredServiceBinding`: `consumer_placement` FK (`DesiredServicePlacement`,
`on_delete=PROTECT` recommended — DB-level backstop under the batch validator),
`binding_name` slug, `provider_service` FK (`DesiredService`, `PROTECT`).
Unique constraint on `(consumer_placement, binding_name)`. No status, type,
notes, or lifecycle. Add `@extras_features("graphql")` — Phase 2 reads desired
state via GraphQL. UI surfaces (table/filter/nav/detail template) are
discretionary; if you add them, mirror what `aca2fa9` removed minus the dead
fields, and keep `test_ui_contract.py`/`test_templates.py` green.

### Binding-name declaration (§4.7)

nintent cannot read `deployment_profiles.yml` (that file is Ansible-owned and
nintent has no repo-sibling access at runtime). Recommendation: declare the
closed profile→binding-name map as a small constant in nintent, e.g.
`PROFILE_BINDING_NAMES = {"node_agent": ("llm_provider",)}`, checked by the
batch validator. This duplicates one tuple across repos; that is acceptable
for now — Phase 3 will need the same declaration for the observation slot and
can revisit ownership. Use `llm_provider` as the binding name (idea-A §11's
example) unless you find a reason not to.

### Where to enforce the graph invariants

The per-row checks (§4.7 binding name declared, old config key refused, field
shape) fit the existing per-operation planning loop. The graph invariants —
§4.1–4.6 (active consumer placement, active services, exactly one active
provider placement, usable endpoint, no self-reference, acyclic) and §8
(retire/delete protection) — are properties of the *resulting* state, not of
one operation. Recommendation: validate the final state inside
`apply_batch`'s `transaction.atomic()` after all writes, and roll back with
structured errors on violation. This matches README_DEV's dry-run policy:
"the apply path is the authority for correctness". Running the same validator
against a simulated planned state during `plan_batch` is a nice-to-have, not
required; do it only if it stays cheap.

§8 protection must catch all of: deleting the provider service, setting its
lifecycle out of active (retiring/deprecating), deleting or disabling its
single active placement, and removing/nulling that placement's endpoint —
while inbound bindings remain *after* the batch. Because validation runs on
final state, "unless the same atomic batch removes or retargets them" falls
out for free. Also extend `_DELETE_BLOCKERS` so a plan shows the conflict
early: `desired_service` and `desired_service_placement` gain an inbound-
bindings blocker (respecting `deleted_pks` as the existing entries do).

Rejection errors must include the exact inbound set, in roughly idea-A §8's
shape: provider service/placement plus each
`consumer_node / consumer_service / binding_name`. Put it in the transaction
error or a structured `errors` entry — precise enough that an operator can
write the fixing batch from the message alone.

### Usable endpoint (§4.4)

Minimum check: the provider placement has a `desired_endpoint`, and that
endpoint has a protocol in `{http, https}`, an integer port in 1–65535, and at
least one address source (`ip_address`/`dns_name`/…). This mirrors what
nctl's `_endpoint_url` in `service_dependencies.py` will demand in Phase 2 —
read it once before writing the check so the two sides cannot disagree on
"usable". Do not build URL normalization in nintent; that is Phase 3's shared-
function problem. Do not import nctl.

### Cycle check (§4.5–4.6)

Walk: binding → provider service → its single active placement → that
placement's own bindings → … The graph is a handful of nodes; a plain DFS
with a visited set on placement PKs is enough. Self-reference is the length-1
case of the same walk.

### Old-key refusal

Two halves, one coordinated change:

1. nintent batch validator rejects any `node_agent` placement whose final
   `config` contains `llm_provider_service` (a clear, named error).
2. `ansible_agdev/vars/deployment_profiles.yml` drops the
   `llm_provider_service` variable from `node_agent`. Nothing else in that
   file changes; leave `deployment_profile_reconciliation` alone.

### Migration batch (one-way, operator-applied)

Not a Django data migration — a desired-state batch document (kept in
`.local/`, gitignored), applied via
`uv run --project nctl nctl desired apply -f ... [--yes]`, containing per
consumer placement:

- upsert `desired_service_binding` with `binding_name: llm_provider`,
  `provider_service: ollama`;
- upsert the placement with its current `config` minus the
  `llm_provider_service` key (whole-config replacement — fetch current live
  config first and preserve every other key).

One atomic batch, applied after the new nintent is deployed. The refusal rule
sees the *final* configs (already stripped), so validator and migration cannot
deadlock each other.

## Known interim gap (accepted)

After the live migration, `service_dependencies.py` (which still reads the
config key) resolves nothing, so generated production inventory loses
`nintent_opencode_ollama_url` until Phase 2 ports the resolver to binding
rows. Consequence: do not run `nctl reconcile` actuation against `node_agent`
placements between Phase 1 live apply and Phase 2 completion — the running
nodes are already correctly configured, so simply not actuating them is
sufficient. Since the profile also stops requiring the key,
`missing_required_config` drift must not appear either; spot-check
`nctl drift --json` after migration and record the delta in the report.

## Steps

Follow the phase execution style: one report section + one commit per step;
pause for user judgment before live/hard-to-reverse actions.

1. **Model + migration.** Add `DesiredServiceBinding`, generate the schema
   migration. Django-free fast suite green
   (`python3 -m unittest discover -s nautobot_intent_catalog/tests` from
   `nintent/`, 10 expected skips).
2. **Batch kind + per-row validation.** Wire the new kind through `batch.py`
   tables, add binding-name declaration and old-key refusal. Unit tests in
   `test_batch.py` style (they run Django-free via the `_models()`
   ImportError path for envelope checks; ORM-backed cases go to the runtime
   gate).
3. **Graph invariants + §8 protection.** Final-state validator in
   `apply_batch`, `_DELETE_BLOCKERS` extension, exact-inbound-set errors.
   Include negative tests for each completion criterion: ambiguous provider
   (second active ollama placement), cycle, protected retire/delete, undeclared
   binding name, unusable endpoint.
4. **Runtime gate.** `./devtests/test_strategy/run_nautobot_runtime_gate.sh
   --keepdb` during iteration; `--clean` once at the end (new migration ⇒
   clean run is required). Check the stated `cases=` count.
5. **Profile contract edit.** Remove the variable from
   `deployment_profiles.yml`; run the nctl ordinary suite
   (`uv run pytest -q` in `nctl/`) since fixtures may reference the key, plus
   the Ansible conformance gate if the file's consumers changed shape.
6. **Deploy to local Nautobot** (pause: ask the user to push nintent, then
   build with `--no-cache`, verify the resolved SHA, migrate, restart).
7. **Live migration + acceptance** (pause: show the dry plan first). Apply the
   migration batch with `--yes`; then demonstrate against the live endpoint:
   an old-key batch is refused, an ambiguous-provider batch is refused, a
   cycle batch is refused, deleting/retiring `ollama` is refused with the
   three-consumer inbound set, and `nctl drift --json` shows no new drift on
   aghub/agstudio/agpc. Record everything in `p1/report.md`.

## Hard rules (the only prohibitions)

- The batch endpoint stays the sole desired-state writer; invariants are
  enforced there atomically (roadmap hard rule 2).
- No resolution or binding-state storage on the model — computed only
  (hard rule 1; the `aca2fa9^` fields stay dead).
- No dual sources of truth: the old config key dies in this same change
  (hard rule 4).
- Do not push nintent/ansible_agdev yourself; ask the user.
- Do not actuate real cluster nodes (`nctl reconcile ... --yes` against
  physical hosts) in this phase; live work is limited to the scratch Nautobot
  and the desired-state batch, per the interim-gap note above.

## Completion criteria (roadmap, restated)

- An invalid batch — ambiguous provider, cycle, protected deletion/retirement
  — is rejected with a precise error naming the exact inbound set.
- The converted state (three `llm_provider` bindings to `ollama`, stripped
  configs) applies cleanly and atomically.
- A batch reintroducing `llm_provider_service` in a `node_agent` config is
  refused.
- All gate runs recorded in `p1/report.md` with counts, plus the post-
  migration `nctl drift` delta.
