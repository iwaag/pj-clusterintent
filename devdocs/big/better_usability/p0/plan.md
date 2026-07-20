# Better Usability Phase 0 Implementation Plan: Field Audit and Tier Classification

Parent: [roadmap.md](../roadmap.md) — Phase 0. Rationale:
[discussion.md](../discussion.md).

## Goal

Produce the authoritative, reviewable map of what the operator genuinely declares, what the
system derives, and what exists only as an exceptional override. This phase changes no runtime
code or live data. Its output is the contract that Phase 1–4 implementation plans must cite rather
than reclassifying fields or inventing derivation/default behavior locally.

The audit is complete only when it answers all of these questions for every current writable
field:

1. Who or what is authoritative for the value?
2. Is the field **Intent**, **Derived**, or **Override**?
3. If Derived, what exact inputs and precedence produce it, and what happens when inputs are
   absent, stale, unsupported, or ambiguous?
4. If Override, what is the safe default, where is the exception persisted, and how does output
   show that it won over derivation/defaulting?
5. Which code paths currently write and read the value?
6. Does the current required/default/editable behavior contradict the tier?
7. Which later phase owns the correction, schema transition, output change, and tests?

## Current state (as of 2026-07-20)

- The only documents in this initiative are the parent roadmap and discussion; the Phase 0
  classification artifact does not yet exist.
- The live dev Nautobot has five `DesiredNode` rows, all `lifecycle=planned`, and zero
  `DesiredNodeOperationalConfig` rows. This validates the roadmap's mechanism-gap premise but is
  evidence, not a rule to encode.
- The live actual ledger does not provide a usable `observed_system` for every realized device.
  OS derivation therefore needs an explicit no/fresh/stale/unsupported-evidence policy; it cannot
  be specified as an unconditional "read the last observation" shortcut.
- Every live node currently has one primary endpoint, but the model permits multiple plausible
  endpoint candidates. The common live shape must not conceal the ambiguity case.
- `DesiredNode.lifecycle="planned"` is hard-coded independently in the model, quick-add form,
  host-creation operation, and YAML loader. A later default change must cover all of them.
- `DesiredNodeOperationalConfig` is consumed outside production composition: desired GraphQL/read
  models, service-placement evaluation, reconcile playbook selection, nintent loaders/import Jobs,
  seed data, docs, and the production output contract all refer to it.
- Baseline verification before this plan: `nctl/tests` 518 passed and nintent's local unit tests
  88 passed. Phase 0 makes documentation changes only and must leave those baselines unchanged.

Never copy the local API token or live object UUIDs into a checked-in artifact. Live inspection is
read-only and records only non-secret aggregate evidence needed for a decision.

## Deliverables

Create `devdocs/big/better_usability/p0/field-classification.md` with the following sections:

1. **Scope and vocabulary** — exact tier definitions and audit exclusions.
2. **Field classification table** — one row for every current writable model field.
3. **Structured JSON subfield appendix** — known/consumed keys inside writable JSON fields.
4. **Derivation and override rulebook** — algorithms, precedence, provenance, and ambiguity/failure
   behavior for every Derived/Override row.
5. **Reader/writer matrix** — all creation/update ingress and all runtime consumers.
6. **Failure-scope matrix** — global-contract versus target-local production errors needed by
   Phase 1.
7. **Lifecycle ingress matrix** — every place that supplies node/service lifecycle defaults.
8. **Phase assignment and decision summary** — concrete work handed to Phase 1–4, including the
   selected Phase 2 persistence shape for overrides.
9. **Open issues** — must be empty for any issue that can change schema shape, tier, derivation,
   default, failure scope, or phase ordering. Cosmetic naming questions may remain explicitly
   non-blocking.

No second, competing classification document is created. If later evidence changes a decision,
update this artifact in the same change as the affected phase plan and explain why.

## Classification vocabulary

Use exactly one primary tier per current field:

- **Intent** — a human or an explicitly delegated domain authority must decide the desired fact.
  Imported catalog intent still counts as Intent; "not typed manually" does not make it Derived.
  Intent remains prominent and may be required when the desired statement is meaningless without
  it.
- **Derived** — the system can compute the ordinary value deterministically from already-owned
  inputs. The persisted current field may be removed. A Derived row may name a separate optional
  override route, but the ordinary value is never demanded from the user.
- **Override** — an exceptional policy/choice for which a universal derivation is unsafe. It is
  optional, has a safe default or an explicit "not set", and is consulted only when present.

System-maintained caches and import timestamps are **Derived**, even if a broad serializer or UI
currently makes them technically writable. "Writable today" describes the problem surface; it
does not confer Intent status.

Do not classify framework-owned `PrimaryModel` fields (`id`, created/updated timestamps, tags,
custom-field infrastructure) as domain fields. List that exclusion once, then audit every field
declared by this app. Relationships declared by the app are in scope.

A current field that mixes ordinary derivation with exceptional input is classified by its normal
case, then split in the target design. Example: current `connection_path` is expected to classify
as Derived, while "force tailscale" belongs in a separately named Override route. Do not label one
required field both Derived and Override and leave its future behavior ambiguous.

## Required table formats

The main field table uses these columns:

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|

The derivation/override rulebook uses these columns:

| Value | Inputs | Precedence/algorithm | Missing/stale/ambiguous behavior | Safe default | Override persistence | Output provenance |
|---|---|---|---|---|---|---|

The reader/writer matrix uses one row per boundary, not one vague "nintent" row:

| Boundary | Read/write | Fields/models | Current behavior/default | Required change | Owning phase/tests |
|---|---|---|---|---|---|

For JSON fields, the main table classifies the container and the appendix enumerates every
documented or runtime-consumed key. At minimum inspect `source_config`, `expected_spec`,
`requirements`, `placement_policy`, placement `config`, and `dnsmasq_options`. For placement
`config`, audit the keys declared by every entry in
`ansible_agdev/vars/deployment_profiles.yml`; do not assume all service configuration is either
pure intent or pure mechanism as one undifferentiated blob.

## Step 0.1 — Freeze the model-field inventory

Enumerate app-declared fields from the model definitions, then cross-check forms, serializers,
filters/tables, loaders, importers, Jobs, and GraphQL exposure. Include:

- `IntentSource`
- `DesiredService`
- `DesiredDependency`
- `DesiredNode`
- `DesiredEndpoint`
- `DesiredServicePlacement`
- `DesiredNodeOperationalConfig`
- `DesiredIPRange`

For each field record type, null/blank behavior, model default, choices, constraint participation,
and relationship delete behavior where it affects usability. Separately record fields hidden from
normal forms but writable over REST/shell/import, and fields shown as editable despite being a
derived cache.

Cross-check that every field name appears exactly once in the classification table. Use model
source as the authoritative inventory; UI/forms alone are incomplete.

## Step 0.2 — Inventory every writer and default

Trace how a value enters or changes the ledger:

- regular Nautobot model forms and Quick Add forms;
- `operations/hosts.py` use-case creation;
- intent-catalog REST serializers/viewsets;
- YAML dataclasses, normalization defaults, importers, and import Jobs;
- seed/example YAML under `nauto/`;
- nctl REST write-back such as reconciliation status;
- admin/shell-only paths documented as recipes.

Record conflicting defaults explicitly. In particular, pin every current source of node lifecycle
and service lifecycle rather than recording only `models.py`. Note routes that do not exist (for
example a model without a REST ViewSet) because a later CLI command may depend on adding or using
one.

Phase 3 must be able to turn this section directly into a checklist of creation paths and tests.

## Step 0.3 — Classify fields by authority, not current implementation

Apply the discussion's test to every row: "If the operator never thought about this, is there a
right answer the system could safely pick?"

For difficult cases, write a short decision note adjacent to the table rather than hiding nuance
in the tier cell. The audit must explicitly settle at least:

- node and service lifecycle semantics/defaults;
- node type versus accepted actual types;
- identity/name/slug and source/catalog metadata;
- endpoint type/address/policy/naming and connection selection;
- service requirements, dependencies, placement, desired state, deployment profile, and config;
- actual-state policy and observed versus declared hosts;
- expected/declared OS;
- SSH port, power control, and laptop behavior;
- reconciliation status/timestamps and import-analysis status/timestamps;
- IP range policy/lifecycle and dnsmasq projection controls.

Do not use "existing required field" as evidence that a value is Intent. Conversely, do not call
a service-specific desired setting Derived merely because Ansible consumes it mechanically.

## Step 0.4 — Specify derivation, override, and provenance contracts

For every Derived value, write executable-quality prose: ordered inputs, normalization, tie-breaks,
freshness requirements, and the exact visible outcome when no safe result exists. Cover this
minimum scenario matrix:

| Scenario | Required policy decision |
|---|---|
| Fresh observed Linux/macOS with one usable primary endpoint | ordinary derived production input |
| Fresh node known only by mDNS, no actual object yet | bootstrap observation remains possible; production waits locally |
| Missing/stale/unsupported observed OS | do not guess; structured local finding and observation/review path |
| Declared/non-observable host such as HAOS | explicit override shape and validation |
| Exactly one usable endpoint | deterministic local endpoint/path derivation |
| Multiple endpoints with exactly one designated primary | deterministic designated-primary rule |
| Multiple equally plausible endpoints | explicit ambiguity finding; no lexical/arbitrary winner |
| Forced tailscale or non-standard SSH port | optional override and visible provenance |
| Unsafe OS/power combination | target-local validation/finding, never silent coercion |

The decision summary must select the target Phase 2 shape:

- retain an auto-materialized row; or
- dissolve the required row and introduce/name the optional override persistence location.

The roadmap favors dissolution, but Phase 0 must confirm it from the completed table. If
dissolution wins, enumerate which current fields disappear, which override fields survive or move,
and how a stable derived identifier replaces/removes `nintent_operational_config_id`. If retention
wins, document the concrete reason persistence has user value beyond caching derivable data.

For all derived/default/override output, require a common provenance concept containing at least:

- effective value;
- source kind (`intent`, `derived`, `default`, `override`);
- source reference/input summary;
- whether an override replaced a derived/default candidate;
- a finding when derivation was impossible or ambiguous.

Phase 0 defines the semantic contract, not the final JSON field names; Phase 2 owns the versioned
production/drift output schema.

## Step 0.5 — Build the consumer and transition impact map

Trace every classified field into runtime readers. The operational-config decision must explicitly
include at least:

- `nctl_core/sources/desired.py` GraphQL query and typed snapshot;
- `nctl_core/production/adapter.py` and `production/composer.py`;
- `nctl_core/drift/comparators.py` and `drift/evaluation_snapshot.py`;
- `nctl_core/reconcile/executor.py` OS-specific playbook selection;
- `nctl_core/production/contract.py` inventory/report schema and host variables;
- nintent models, forms, views, URLs, tables, filters, loaders, importers, Jobs, templates, tests,
  README, and migrations;
- `nauto/seed/intent_sources.yaml` and any other seed/example source;
- downstream Ansible references, confirming whether each exported variable is consumed or only
  metadata.

For each target schema change record:

- required Django migration operation and retained migration history;
- existing-row policy (unchanged, explicit lifecycle command, or intentional data migration);
- output/envelope schema bump;
- coordinated nintent/nctl deploy order and rollback point;
- explicit deletion list so no old runtime API/UI/import path remains.

Do not implement compatibility code in Phase 0. This is an impact/rollout specification for the
later plan.

## Step 0.6 — Classify production failures for Phase 1

Inventory every `ContractError` reachable from `compose_production_inventory`, including helpers
called before, inside, and after the per-node loop. Add a failure-scope table:

| Code | Origin | Owned by shared contract or one target? | Target kind/evidence | Required scope | Reconcile handling owner |
|---|---|---|---|---|---|

Use these rules:

- malformed shared deployment-profile definitions and corruption of the final closed output
  contract are global;
- missing/invalid operational data, endpoint/path resolution, platform/power policy, and placement
  config/profile use owned by one node/placement are target-local unless the audit documents a
  concrete cross-target invariant;
- a conflict between two assignments on one host is local to that host, even if the current merge
  helper raises a generic `ContractError`;
- each local code needs a target, evidence, severity, and later reconcile classification.

Explicitly call out that changing `missing_operational_config` from global to node-local requires
adding a non-global reconcile classification. List every new "recorded but not applied" finding
Phase 1 must define, including active placement evidence on a production-ineligible node even when
its config object is empty.

This table prevents Phase 1 from changing only the first known exception while claiming all
per-node mechanism failures are isolated.

## Step 0.7 — Assign work to phases and perform a consistency review

Every contradiction and transition item receives exactly one owning phase:

- **Phase 1:** target-local failure isolation; unapplied-intent findings; drift/status/reconcile
  code integration.
- **Phase 2:** derivation implementation; optional override persistence/schema; all
  operational-config consumers; provenance and output contract bump.
- **Phase 3:** node/service lifecycle behavior; every creation ingress; promotion/demotion CLI;
  existing-row transition.
- **Phase 4:** recipe rewrite; end-to-end feedback coverage; residual tier contradictions not
  requiring earlier schema/behavior changes.

Then review the artifact against these invariants:

- Phase 3 is hard-blocked on completed Phase 1 and Phase 2.
- No Derived field remains required human input in the target design.
- Every Override is optional, validated, persisted somewhere named, and visible when effective.
- No derivation resolves ambiguity invisibly.
- No target-owned error remains classified global without a documented cross-target invariant.
- Every new error-level code has a Phase 1/2 reconcile-classification task.
- Existing rows and all creation ingress have an explicit transition owner.
- Normal Django migration history is retained; only obsolete runtime surface is deleted.

## Verification

Documentation/static checks:

1. Compare the field inventory against `models.py`; every app-declared field is present exactly
   once, with framework-field exclusions documented.
2. Search every model and high-risk field name across all submodules; reconcile every hit with the
   reader/writer matrix or document why it is irrelevant.
3. Search lifecycle defaults in models, forms, operations, loaders, seeds, and tests; every ingress
   appears in the lifecycle matrix.
4. Search all `raise ContractError` sites in production composer/contract helpers; every reachable
   code appears in the failure-scope matrix.
5. Verify every Derived/Override row has a rulebook entry and every contradiction has an owning
   phase.
6. Verify later roadmap text does not contradict the selected persistence shape or dependency
   order; update the roadmap in the same commit if the completed audit changes a provisional
   choice.

Read-only environment checks:

- Re-run live desired/actual snapshot inspection only where it tests whether an input exists; do
  not turn current sample cardinality into a universal rule.
- Run `nctl drift --json` to confirm the current baseline remains readable.
- Run `uv run --project nctl pytest -q nctl/tests` and the nintent local unit suite to confirm the
  documentation-only phase did not disturb the workspace.
- Confirm root, `nctl`, and `nintent` worktrees contain only the intended documentation changes.

## Out of scope

- Runtime model, migration, API, CLI, composer, drift, reconcile, Ansible, or live-ledger changes.
- Creating operational-config rows to make the existing design appear complete.
- Promoting the five live planned nodes.
- Choosing an endpoint/OS by exercising a convenient live-only tie-break that is not valid for the
  full model.
- Adding temporary compatibility adapters between old and proposed GraphQL/output schemas.

## Exit criteria

- [ ] `p0/field-classification.md` contains every required section and every app-declared writable
  field exactly once.
- [ ] Every Derived value has deterministic inputs, precedence, no/stale/ambiguous behavior, and
  output provenance.
- [ ] Every Override has a safe default/not-set behavior and a named target persistence location.
- [ ] The Phase 2 operational-config shape is selected, with deletion/move/retention decisions for
  every current field and consumer.
- [ ] Every production composition error has an agreed global or target-local scope.
- [ ] Every lifecycle creation ingress and the existing-row transition are assigned to Phase 3.
- [ ] Every contradiction and breaking transition is assigned to exactly one later phase.
- [ ] No schema-shaping or behavior-shaping open issue remains.
- [ ] Roadmap, discussion, classification artifact, and this plan agree on Phase 1 → Phase 2 →
  Phase 3 as the hard dependency chain.
- [ ] Read-only live checks and both scoped test suites pass; no runtime or live data was changed.

## Suggested commit order

Phase 0 is one reviewable documentation change:

1. Add the complete `p0/field-classification.md` artifact.
2. In the same commit, update `roadmap.md` only where the audit replaces a provisional choice with
   an authoritative decision.
3. Record verification results in the commit message or a later `p0/report.md` when the Phase 0
   work is executed; do not mix Phase 1 runtime changes into the Phase 0 commit.
