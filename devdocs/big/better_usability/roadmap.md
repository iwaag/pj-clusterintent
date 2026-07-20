# Better Usability — Development Roadmap

Companion to `discussion.md` (problem analysis and guiding principles). This roadmap sequences
the work to close the intent/mechanism gap. Concrete per-change implementation plans are written
separately (`devdocs/small/*`) when each phase is picked up; this document defines the phases,
their exit criteria, and implementation hints worth capturing now.

## Premises

- **Breaking-change phase.** No backward compatibility is required. Schemas, models, CLI, and API
  may be broken freely. **Leave no runtime compatibility shims or transitional data-copy surface
  behind** — when a field or model is replaced, delete the old runtime model/API/UI/import path
  outright rather than deprecating it. Normal Django schema migrations (including `DeleteModel`)
  are still required and remain in migration history; "no migration artifacts" does not mean
  deleting already-applied migration files or leaving the database schema unmanaged.
- **Single-operator, personal-use is the primary case.** Ease of casual use and operator
  efficiency take priority over process rigor. A step that costs the user time without giving
  *them* (the sole stakeholder) value is a defect, not diligence.
- **Secure/multi-role is a future main route, not a current requirement.** Keep the lifecycle
  state machine and any structural hooks that a real approval/permission system would later use,
  but do not implement — or charge the user for — separation-of-duties ceremony now. Security
  needs only the bare minimum for a LAN-only experimental system (no plaintext credentials that
  cause real harm, no tokens in Git), consistent with `devdocs/vision/core_reconcile/roadmap.md`.
- **Derive aggressively, but legibly.** Every value the system infers or defaults instead of
  taking from the user must be discoverable in `nctl` output (drift/status/render report), so a
  wrong guess is never silent (discussion.md Principles 3 & 5, and the non-goal caveat).

## Note on nintent deployment

Any change under `nintent/` requires commit → push → `docker compose build` → restart to reach
the running instance (`.local/localenv_memo.md`: nintent is `pip install git+…`, not volume-
mounted; push is the user's step). Batch nintent model/schema changes so the number of
push/rebuild cycles is minimized — prefer landing all model changes for a phase together. Changes
confined to `nctl/` need no rebuild and can iterate freely.

When an nintent schema removal changes the GraphQL shape consumed by nctl, the matching nctl and
nintent commits form one coordinated breaking rollout. Do not add a dual-schema compatibility
adapter merely to support a mixed-version interval: test both sides together, have the user push
the nintent commit, rebuild/restart Nautobot, then run the matching nctl revision. The concrete
phase plan must spell out that order and the rollback point.

## Mandatory checks for every per-phase implementation plan

Every concrete plan under `devdocs/small/*` (or a phase subdirectory here) must cite Phase 0's
classification table and explicitly cover the applicable items below. These are planning gates,
not optional cleanup for a later phase.

1. **Scope every failure.** Classify each new/existing error as global-contract or target-local.
   Invalid shared deployment-profile/output schemas may fail globally; missing or invalid data
   owned by one node/placement must produce a structured local skip/finding. Do not infer scope
   merely from the fact that the current helper raises `ContractError`.
2. **Integrate findings end to end.** Every new skip/drift code must define target kind, severity,
   human message/evidence, dashboard/status effect, and reconcile classification. A node-level
   error absent from `nctl_core.reconcile.classify.CODE_CLASSIFICATION` makes planning fail closed;
   a warning intentionally omitted from reconcile must be tested as such.
3. **Inventory all readers and writers.** A model/default change must cover model fields, forms,
   quick-add/use-case operations, REST/GraphQL, YAML loaders/import Jobs, seed data, nctl typed
   snapshots, composer/evaluators/executor, output contracts, docs, and tests as applicable. A
   model default alone is not a creation-path default when another ingress hard-codes a value.
4. **Preserve overrides and provenance.** Removing a required mechanism model must still leave an
   explicit place for genuine exceptions. Every derived/defaulted value must expose value, source,
   and whether an override won; ambiguous or missing inputs must never be resolved by an invisible
   arbitrary choice.
5. **Plan schema/data transition.** State the Django migration, output schema-version change,
   treatment of existing rows, coordinated nintent/nctl rollout, and rollback. Changing a default
   affects only future rows unless an explicit one-time transition is included.
6. **Test both isolation and orchestration.** Besides pure composer/model tests, cover `nctl drift`,
   `nctl reconcile` planning/classification, mixed good+bad nodes, and the relevant live/local
   scenario. "Render continues" is insufficient if reconcile then crashes or blocks unrelated
   targets on the same finding.

---

## Phase 0 — Field audit and tier classification (no code)

**Goal: produce the authoritative map of which fields are Intent / Derived / Override, so every
later phase has an agreed target.**

- Enumerate every user-writable field across nintent's models (`DesiredNode`,
  `DesiredEndpoint`, `DesiredService`, `DesiredServicePlacement`, `DesiredNodeOperationalConfig`,
  `DesiredIPRange`, dependencies, `IntentSource`) and tag each Intent / Derived / Override per
  discussion.md Principle 1.
- For each **Derived** field, record the derivation rule and its inputs (e.g. "connection_path ←
  the node's sole endpoint; if multiple, ← endpoint tagged/typed as primary"). For each
  **Override**, record the safe default.
- Flag every field whose current `required`/no-default status contradicts its tier — these become
  the concrete work items for later phases.

**Exit criteria**: `p0/field-classification.md`, an authoritative table that later plans cite
instead of re-deciding tiers ad hoc. It must also identify all current readers/writers, define
ambiguity/no-input behavior for every Derived value, name the persistence location for every
Override, and assign each required change to a later phase. See `p0/plan.md`.

## Phase 1 — Stop discarding intent silently, and stop failing globally (`nctl` only)

**Goal: make the current behavior honest and safe *before* changing any defaults. Pure `nctl`
changes, no nintent rebuild — the fastest safety win.**

- **Local-fail the missing operational config.** In `production/composer.py`, convert the
  `missing_operational_config` `ContractError` (composer.py:185) from a global abort into a
  per-host skip with a structured reason, matching the existing `_host_actual_skip_reasons`
  pattern. One half-configured node must never take down the whole render (discussion.md
  Principle 4). This removes the first known landmine, but Phase 1 must also audit every
  `ContractError` reachable inside the per-node composition loop (`invalid_actual_state_policy`,
  platform/power, endpoint/connection, placement profile/config, variable collision, etc.) and
  localize every target-owned failure. Shared profile-schema and final output-contract corruption
  remain global.
- **Surface ignored/derived intent.** Where placement `config` (or any recorded intent) is not
  applied because a node is out of production scope, emit it as a visible drift/skip finding, not
  silence (discussion.md Principle 3). The dnsmasq loopback case (discussion.md Example 1) should
  have produced a "placement recorded but not applied: node not in production scope" signal,
  including the placement/config evidence even when `config == {}`.
- **Wire the new findings through drift/reconcile.** Define target kind and severity for each new
  local skip/finding and add every error-level code to reconcile classification. In particular,
  moving `missing_operational_config` from a global `ContractError` to a node skip changes it from
  the global blanket classification to a code that must be explicitly classified. Decide whether
  it blocks only that target or a cluster apply; do not let it become an
  `UnclassifiedDiffCodeError`.
- Tests: composer test asserting a single config-less/invalid eligible node skips alone while
  others still render; tests asserting recorded-but-unapplied placement evidence surfaces in the
  report/drift; planner/executor tests asserting the same findings do not crash reconcile or
  silently suppress unrelated work.

**Exit criteria**: no single node's mechanism gap can fail the cluster render; any recorded intent
that doesn't take effect is reported.

## Phase 2 — Derive the mechanism (`DesiredNodeOperationalConfig`)

**Goal: the operator declares a node + placement and the connection/OS/policy mechanism fills
itself in. The user sees operational config only when overriding.**

Two viable shapes — Phase 0's audit + a short design plan should pick one:

- **(a) Auto-materialize**: keep the model, but have the system create/maintain the row from
  derivations (single endpoint → `connection_path` + `local_endpoint`; last nodeutils
  observation → `expected_host_os`; sensible policy default), so it's never a manual step.
- **(b) Dissolve into derivation**: drop the separate required model; compute the same values
  on demand in `composer.py`/`hosts_intent.py` from endpoints + observed state, with an optional
  override record only for the rare Override-tier cases.

Given the breaking-change premise (no artifacts left behind), **(b) is favored** unless the audit
surfaces a reason the persisted row is needed — it removes an entire required-model burden rather
than automating around it. "Dissolve" does not mean "delete overrides": the design must name an
optional override persistence shape for declared/non-observable hosts, forced connection path or
endpoint, non-standard SSH port, power policy, laptop policy, and any other Phase 0 Override.
Either way:

- Derivation inputs already exist: `DesiredEndpoint` rows (IP/mDNS/type) and the actual-state OS
  observed by nodeutils and stored on the Device custom fields
  (`nctl/src/nctl_core/sources/actual.py`).
- Every derived value must be labeled derived in output (Principle 3), so an inferred OS that's
  wrong is visible in drift rather than mysterious. The production report/output contract must
  represent at least the value, provenance/source, and override status; bump its schema and remove
  `nintent_operational_config_id` if the referenced row no longer exists.
- Preserve the one thing the current model does well: the Override-tier fields (`ansible_port`,
  `power_control`, `is_laptop`) already have good defaults — carry that pattern to the rest.
- If the model is dropped/reshaped, delete the old model, its admin/UI, serializers, and the
  `clean()`/`CheckConstraint` outright (breaking-change premise); also remove or reshape its
  GraphQL query/read model, YAML loader/import Job, seed data, composer adapter, service-placement
  evaluation, reconcile OS/playbook selection, inventory variables, docs, and tests. Port only
  what derivation/override still needs.
- Derivation must fail visibly rather than guess: a fresh/unobserved, stale, or unsupported-OS
  node stays bootstrap-observable and is locally skipped from production until evidence exists;
  a declared host such as HAOS uses an explicit override; multiple plausible endpoints require a
  deterministic Phase 0 rule or an override rather than arbitrary selection.

**Exit criteria**: registering a node + placement with zero operational-config input produces a
correct production render (connection, OS group, actuation) for the common case; overrides remain
possible and are the only time a human touches mechanism.

## Phase 3 — Intent takes effect on creation (`lifecycle` default + promotion)

**Goal: expressing intent is approving it, for the single operator. `planned` stays as a formal
state for the future secure route but no longer gates everyday use.**

- **Default `DesiredNode.lifecycle` to `active` across every creation ingress**: model, regular and
  quick-add forms, `create_desired_node_with_primary_endpoint`, REST behavior, YAML loader/import,
  seed/example data, and tests. Batch the nintent changes to save a rebuild. This phase has a hard
  dependency on both Phase 1 (complete target-local failure isolation) and Phase 2 (no required
  operational-config input); Phase 1 alone would merely turn a newly active node into a safe skip,
  which does not satisfy this phase's actuation goal.
- **Provide an explicit promotion/demotion affordance** for when someone *does* want the state
  machine — a thin `nctl` command to move a node's lifecycle — so `planned` remains usable as the
  entry point of a future approval flow without requiring Django admin. This is the "keep the
  skeleton for secure use" half of discussion.md Principle 5.
- Reconsider whether `DesiredService.lifecycle` (a separate field with the same vocabulary,
  models.py:125 — easy to conflate with the node's) should follow the same default, per Phase 0's
  audit. Record what, if anything, consumes service lifecycle today so the change is behavioral,
  not cosmetic.
- Define the transition for existing nodes. A default change does not alter current `planned`
  rows; use the new explicit lifecycle command as a reviewed one-time promotion (favored for this
  personal deployment) or include an intentional data migration. Do not silently assume the five
  currently planned dev nodes became active.
- Update `nctl/docs/add-a-basic-service.md` and the scenario-1 node-registration flow so the
  documented recipe matches the new "intent is live on creation" reality — and, if any manual
  lifecycle step ever remains, states it explicitly (its current total omission is the documented
  gap from discussion.md Example 2).

**Exit criteria**: a node created with only its intent (exists; runs service X) is immediately in
production scope and actuated on the next reconcile, with no manual promotion and no operational-
config step; the lifecycle state machine still exists and is drivable for anyone who wants it.

## Phase 4 — Recipe & feedback consolidation

**Goal: the documented path and the tooling's feedback reflect the intent-first model end to
end.**

- Rewrite the "add a basic service" and "register a new PC" recipes around the reduced input set
  (intent only; mechanism derived), removing every now-unnecessary manual step.
- Ensure `nctl status`/`drift`/render reports collectively answer, for any node: what intent is
  recorded, what the system derived vs. what was explicitly set, and what (if anything) is
  recorded but not yet taking effect — closing Principle 3 across the surface.
- Sweep for any remaining Intent/Mechanism conflation flagged by Phase 0 that earlier phases
  didn't reach.

**Exit criteria**: following the recipes literally, a single operator goes from "new PC" to
"service running, drift converged" supplying only genuine intent, with mechanism either derived
or explicitly and visibly overridden.

---

## Sequencing rationale

Phase 1 is first because it is pure `nctl`, needs no rebuild, and removes the global-failure
landmines that make later default changes dangerous. Phase 2 removes the mechanism burden and is a
hard prerequisite for Phase 3: local-fail alone is safe but does not make new intent effective.
Phase 3 then safely makes intent live-on-creation across all input paths and explicitly handles
existing rows. Phase 4 aligns docs and feedback last, once the behavior they describe is stable.
Phases 1 and 2 are independently shippable; Phase 3 is shippable only on top of both, and every
phase must satisfy the mandatory planning checks above.
