# Better Usability — Development Roadmap

Companion to `discussion.md` (problem analysis and guiding principles). This roadmap sequences
the work to close the intent/mechanism gap. Concrete per-change implementation plans are written
separately (`devdocs/small/*`) when each phase is picked up; this document defines the phases,
their exit criteria, and implementation hints worth capturing now.

## Premises

- **Breaking-change phase.** No backward compatibility is required. Schemas, models, CLI, and API
  may be broken freely. **Leave no compatibility shims or migration artifacts behind** — when a
  field or model is replaced, delete the old one outright rather than deprecating it. Carrying
  dead compatibility surface forward is itself a usability cost this effort exists to remove.
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

**Exit criteria**: a classification table (checked into this directory) that later plans cite
instead of re-deciding tiers ad hoc.

## Phase 1 — Stop discarding intent silently, and stop failing globally (`nctl` only)

**Goal: make the current behavior honest and safe *before* changing any defaults. Pure `nctl`
changes, no nintent rebuild — the fastest safety win.**

- **Local-fail the missing operational config.** In `production/composer.py`, convert the
  `missing_operational_config` `ContractError` (composer.py:185) from a global abort into a
  per-host skip with a structured reason, matching the existing `_host_actual_skip_reasons`
  pattern. One half-configured node must never take down the whole render (discussion.md
  Principle 4). This is the prerequisite that makes Phase 3's default-to-active safe.
- **Surface ignored/derived intent.** Where placement `config` (or any recorded intent) is not
  applied because a node is out of production scope, emit it as a visible drift/skip finding, not
  silence (discussion.md Principle 3). The dnsmasq loopback case (discussion.md Example 1) should
  have produced a "config recorded but not applied: node not in production scope" signal.
- Tests: composer test asserting a single config-less eligible node skips alone while others
  still render; a test asserting recorded-but-unapplied config surfaces in the report.

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
than automating around it. Either way:

- Derivation inputs already exist: `DesiredEndpoint` rows (IP/mDNS/type) and the actual-state OS
  observed by nodeutils and stored on the Device custom fields
  (`nctl/src/nctl_core/sources/actual.py`).
- Every derived value must be labeled derived in output (Principle 3), so an inferred OS that's
  wrong is visible in drift rather than mysterious.
- Preserve the one thing the current model does well: the Override-tier fields (`ansible_port`,
  `power_control`, `is_laptop`) already have good defaults — carry that pattern to the rest.
- If the model is dropped/reshaped, delete the old model, its admin/UI, serializers, and the
  `clean()`/`CheckConstraint` outright (breaking-change premise); port only what the derivation
  needs.

**Exit criteria**: registering a node + placement with zero operational-config input produces a
correct production render (connection, OS group, actuation) for the common case; overrides remain
possible and are the only time a human touches mechanism.

## Phase 3 — Intent takes effect on creation (`lifecycle` default + promotion)

**Goal: expressing intent is approving it, for the single operator. `planned` stays as a formal
state for the future secure route but no longer gates everyday use.**

- **Default `DesiredNode.lifecycle` to `active`** (nintent model change; batch with any other
  Phase-3 nintent changes to save a rebuild). Depends on Phase 1 (local-fail) and ideally Phase 2
  (no operational-config landmine) having landed, so a freshly-created active node can't blow up
  the render.
- **Provide an explicit promotion/demotion affordance** for when someone *does* want the state
  machine — a thin `nctl` command to move a node's lifecycle — so `planned` remains usable as the
  entry point of a future approval flow without requiring Django admin. This is the "keep the
  skeleton for secure use" half of discussion.md Principle 5.
- Reconsider whether `DesiredService.lifecycle` (a separate field with the same vocabulary,
  models.py:125 — easy to conflate with the node's) should follow the same default, per Phase 0's
  audit.
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
landmine that makes every later default change dangerous. Phase 2 removes the mechanism burden
that would otherwise become a cluster-wide outage once Phase 3 flips the default. Phase 3 then
safely makes intent live-on-creation. Phase 4 aligns docs and feedback last, once the behavior
they describe is stable. Each phase is independently shippable and leaves the system in a better,
consistent state.
