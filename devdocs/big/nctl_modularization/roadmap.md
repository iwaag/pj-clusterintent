# Remaining nctl Simplification and Modularization — Development Roadmap

## Purpose

Give the deterministic kernel that survived removal, interface contraction, and test consolidation
one clear owner per operational value, contract, and lifecycle decision — without introducing a new
speculative framework.

This roadmap implements item 4 of
[`devdocs/vision/refactor/vision.md`](../../vision/refactor/vision.md). The vision and
[`README_DEV.md`](../../../README_DEV.md) remain authoritative for safety, evidence, and completion
language. [`devdocs/big/test_strategy/roadmap.md`](../test_strategy/roadmap.md) is a completed
prerequisite and its
[`devtests/test_strategy/MANIFEST.md`](../../../devtests/test_strategy/MANIFEST.md) is the current
statement of which behavior is proven and by which test ID.

The observable outcome is:

```text
current
  three modules over 1,200 lines that each mix orchestration with domain rules
  + one compute contract implemented twice, in nintent and in nctl, with drifting coverage
  + a reconcile executor that imports twenty concrete feature modules and branches on action kind
  + GraphQL row parsing, domain validation, and source-issue policy in one desired-state module
  + generic transport/error translation interleaved with Braindump domain semantics
  + 57 error classes with no recorded statement of which caller distinguishes them
  + a README "Layout" section that says only "all business logic lives here"

to
  one named owner per operational value, contract, target set, route, identity, and lifecycle rule
  + one semantic owner for the compute contract, with an executable conformance mechanism
  + orchestration that depends on an action interface rather than on feature modules
  + pure domain rules that import no CLI, HTTP, Nautobot runtime, or Ansible execution
  + an error taxonomy where every distinct type has a caller that behaves differently
  + documented module responsibilities a new agent can read before changing code
  + identical end-to-end behavior, evidence, and manifest coverage
```

The primary consumer is the developer or AI agent making the next change to the kernel — most
immediately the `vm_first_realization` roadmap, which must add compute drift, planning, and one
guest actuator into these same modules. That roadmap is the concrete justification for doing this
work now rather than later: compute is the first domain that will need a new evaluator, a new
reconciler, and a new actuator simultaneously, and it must not be added by extending three
1,200-line files.

This initiative changes internal structure, not supported cluster behavior. It does not remove or
add a command, change an output envelope, change drift semantics, implement compute
reconciliation, create a Proxmox guest, revive a removed surface, or weaken any acceptance
requirement.

## Governing decisions

### 1. Responsibility, not line count, authorizes a split

A module is split only when it contains responsibilities that change for different reasons, have
different consumers, or carry different risk. A 1,200-line module with one reason to change stays.
A 200-line module that mixes an authorization decision with a rendering convenience may still be
separated.

Every proposed split must name, before the edit:

- the two or more independent reasons to change;
- the operational value, contract, or decision each side owns;
- who calls each side; and
- what would have gone wrong if they had already been separate.

"It is long," "it is hard to read," and "it would be more testable" are not sufficient on their
own. The third is admissible only when it names a specific external boundary that cannot currently
be exercised at its normative layer.

### 2. One semantic owner per contract, with an executable conformance mechanism

Where nintent and nctl both implement the same rule, exactly one becomes the semantic owner. The
other becomes a consumer that either calls the owner or is proven conformant by generated fixtures.
Two independently maintained implementations of one contract are a defect regardless of how similar
they currently look.

The vision permits three shapes of solution: a small shared wire contract, generated conformance
fixtures, or reducing nctl to transport parsing plus actuation-time safety checks. A new shared
Python package is permitted only if Phase 1 shows it produces less total ownership and deployment
complexity than the duplication it replaces. Given that nintent is installed into the Nautobot
image from GitHub (`.local/localenv_memo.md`) and nctl is a local `uv` project, a new co-installed
package adds a real deployment coupling and starts from a position of disadvantage.

### 3. Orchestration depends on interfaces; domain depends on nothing

The retained dependency rules are:

- pure domain rules import no CLI, HTTP client, Nautobot runtime, Ansible execution, subprocess, or
  filesystem-writing module;
- orchestration depends on an action or evaluator interface, not on the feature module that
  implements it;
- transport modules translate protocol into domain types and protocol errors into domain errors,
  and contain no domain policy;
- presentation renders a completed envelope and decides nothing; and
- a deleted public schema does not survive as an internal abstraction.

The existing `drift/registry.py` and `reconcile/registry.py` already express the intended shape.
`drift/registry.py` is a working execution seam. `reconcile/registry.py` currently registers only
static metadata while execution dispatch lives in `reconcile/executor.py`; that asymmetry is a
named target, not a reason to invent a third registry pattern.

### 4. No new framework without a current consumer

This roadmap must not produce a plugin system, provider abstraction, generic event bus, dependency
injection container, generic "service layer," or cross-repository framework package. An interface
is admissible when it has at least two current implementations or one current implementation plus a
concretely planned second one named in an approved roadmap. Compute is such a planned second
implementation for the reconciler and evaluator seams; it is not a justification for a general
provider abstraction.

### 5. Behavior, evidence, and test identity are preserved

Every phase is behavior-preserving. The proof is that the retained suite and every gate in the
root command matrix pass unchanged in meaning.

Renaming or moving a test module renames its test IDs. `devtests/test_strategy/MANIFEST.md` names
exact test IDs for 26 supported behaviors. Any move that changes a manifested ID must update the
manifest in the same commit and rerun that row's gate. A manifest row must never point at a
missing or renamed test between commits.

Durable operation artifacts, JSONL events, and CLI envelopes are current-consumer contracts under
[`nctl/docs/compatibility.md`](../../../nctl/docs/compatibility.md). Internal module layout is
explicitly outside that policy, so moving code is permitted; changing a written field is not, and
is out of scope for this roadmap.

### 6. Matched-version deployment over runtime branches

Any cross-repository contract change is a coordinated matched-version rollout. Do not add a shim,
dual reader, feature flag, or version branch to make nctl tolerate both an old and a new nintent.
nintent changes reach the local scratch stack only through commit, user-owned push, and
`docker compose build`; that cost is planned into the phase, not avoided with a compatibility
branch. The known rebuild caching hazard applies: verify the resolved nintent commit in the build
log rather than assuming the image picked it up.

## Current-state baseline

Measured on 2026-07-27 from the clean checkout below. Phase 0 must repeat these measurements rather
than treating them as permanent.

### Revisions and worktrees

| Component | Revision | State at measurement |
|---|---|---|
| superproject | `fbbd39d1eb07c16e3242846bd7f8ed82e57c14f5` | clean |
| nctl | `55f1a4bad9baffc998203a5003eee1cbcc005462` | clean |
| nintent | `055496d3e28d2ea6536f660a3ae352b8594279f3` | clean |
| nauto | `6dab422a725a2e2e4e24e98079e992d1111c0ef1` | clean |
| nodeutils | `775ed7fad5110a96186a737147b87d3bf450ced2` | clean |
| ansible_agdev | `66b31c89986d1b2ecfa187a72209d8bd96838fd4` | clean |

This is the exact tuple recorded as `complete` by
[`test_strategy/p4/report.md`](../test_strategy/p4/report.md). No source change has landed since.

### Environment and initiative state

- `remove_unused_surfaces`, `interface_contract`, and `test_strategy` are all `complete`. Their
  contracts — no serve/dashboard/status cache, canonical GraphQL read plus narrow REST mutation
  plus read-only UI, and the risk-tier command matrix — are this roadmap's starting contract.
- nintent migrations are applied through `0016_remove_reconciliation_dashboard_surfaces`.
- VM Phase 3 Steps 0-7 are reported complete; Steps 9-12 have no completion report and desired
  compute rows remain unseeded. Compute is inert and manifested as such
  (`compute-inert` row, `nctl/tests/test_compute_actuation_inert.py`).
- `vm_first_realization` has not been written. It is the intended consumer of this work.

### nctl size and concentration

| Package | Tracked files | Tracked lines |
|---|---:|---:|
| `src/nctl_core/` top level | 31 | 7,106 |
| `src/nctl_core/reconcile/` | 12 | 3,082 |
| `src/nctl_core/drift/` | 11 | 2,584 |
| `src/nctl_core/production/` | 6 | 2,237 |
| `src/nctl_core/sources/` | 6 | 2,095 |
| `src/nctl_core/cli/` | 2 | 679 |
| **Total source** | **68** | **17,783** |
| Tracked tests | 73 | 19,685 |

The nctl suite collects 967 cases. The three modules the vision flagged as over 1,200 lines are all
still over 1,200:

| Module | Lines | Distinct responsibilities visible today |
|---|---:|---|
| `reconcile/executor.py` | 1,261 | envelope models, dry/apply entry, round loop, production inventory regeneration, per-action-kind dispatch, playbook host grouping, observation action, plan construction, forced-observation rewrite, scope summary, terminal persistence, text rendering |
| `drift/evaluation.py` | 1,236 | node/endpoint/service evaluators, IP-range normalization and overlap classification, MAC and interface candidate selection and scoring, fact extraction, formatting helpers |
| `sources/desired.py` | 1,231 | GraphQL row builders, compute contract validators, compute collection assembly and source-issue policy, effective-value resolution, endpoint-MAC validation |

Other modules above 600 lines: `braindump.py` (858), `production/composer.py` (834),
`production/contract.py` (807), `dnsmasq.py` (696), `cli/main.py` (679), `sources/actual.py` (615).

The corresponding test concentration is `test_reconcile_executor.py` (2,355),
`test_dnsmasq_apply.py` (1,033), `test_production_composer.py` (1,023),
`test_drift_evaluation.py` (724), `test_reconcile_planner.py` (710), `test_dnsmasq.py` (701).

### Confirmed duplication: the compute contract

`nintent/nautobot_intent_catalog/compute_contract.py` (292 lines) and the compute block inside
`nctl/src/nctl_core/sources/desired.py` implement the same contract twice. Both define
`ComputeContractError` and near-identical `validate_provider_type`,
`validate_config_schema_version`, `_require_json_object`, `_require_non_empty_string`,
`validate_platform_config`, `validate_instance_config`, `validate_vmid`, `_validate_bounded_int`,
`validate_vcpus`, `validate_memory_mb`, `validate_root_disk_gb`, `normalize_mac_address`,
`effective_lifecycle`, `effective_value`, and `effective_single_source_value`. The actionable
lifecycle predicate exists in both under different names (`is_actionable_lifecycle` versus
`is_actionable_compute_lifecycle`).

They have already diverged. nctl additionally owns `validate_compute_lifecycle`,
`validate_instance_kind`, `validate_power_state`, `_validate_source`, and
`_validate_link_source_xnor`; nintent additionally owns the `PROVENANCE_*` constants. The
implementations that do exist in both are textually near-identical apart from formatting and
docstrings. Each side has its own tests. This is the clearest ownership defect in the repository
and is the reason Phase 1 comes before any file splitting.

### Error taxonomy

`src/` declares 57 error classes. `braindump.py` alone declares 19 `BraindumpError` subclasses
alongside 8 data models, 7 `build_*` operations, and 7 `render_*` functions. No current document
states which caller distinguishes which type. Some are genuinely load-bearing — a missing managed
SSH store must not be reported as a corrupt one — and some may exist only to carry a message
string.

### Existing seams worth preserving

- `output.py` is 42 lines and is already the single owner of `Envelope`/`EnvelopeError`/`emit`.
  Envelope shape is not the problem; per-domain error multiplication is.
- `drift/registry.py` is a working, order-independent comparator execution seam with a dedicated
  ordering test, and `README.md` documents how to add a comparator.
- `reconcile/registry.py` owns reconciler identity, DAG validation, and deterministic topological
  ordering.
- `drift/model.py`, `reconcile/model.py`, and `production/contract.py` already separate contract
  from implementation.
- `cli/main.py` already states and largely honours the "no business logic" convention.

### Known ambiguities Phase 0 must resolve

1. Whether `reconcile/reconcilers.py`, `reconcile/classify.py`, and `reconcile/registry.py` can
   own action execution, or whether execution must stay in the executor with an explicit interface.
2. Whether `production/contract.py`'s validation schema and its canonical-JSON/digest utilities are
   one responsibility or two, given the digest is also an externally consumed artifact contract.
3. Whether `dnsmasq.py`, `dnsmasq_render.py`, `dnsmasq_query.py`, and `dnsmasq_apply.py` already
   have clean ownership or duplicate skip/finding policy.
4. Whether `drift/evaluation_snapshot.py` and `drift/evaluation.py` split along a real boundary.
5. Which of the 57 error types have a caller that behaves differently, and which only carry text.
6. Whether the compute source-issue policy in `sources/desired.py` is transport concern, domain
   concern, or a third thing that belongs beside the drift evaluators.
7. Whether any test module's name encodes implementation structure rather than a contract, which
   would make it fragile against a legitimate move.

## Required audit areas

Phase 0 must produce a finding for each area the vision names, with an explicit
keep / split / merge / defer decision and the reason-to-change analysis behind it.

| Area | Concrete starting point |
|---|---|
| reconcile orchestration versus action-specific execution | `reconcile/executor.py` `_execute_action` branches on `action.action_kind`; executor imports 20 concrete modules including `dnsmasq_apply`, `production_render`, `observation`, `ssh_enroll`, `ansible` |
| desired transport versus compute domain validation and source-issue handling | `sources/desired.py` row builders versus its validators, `_build_compute_collections`, and `DesiredSourceIssue` policy |
| drift orchestration versus per-resource evaluators | `drift/evaluation.py` node/endpoint/service evaluators plus IP-range and MAC candidate machinery; `drift/engine.py`, `drift/comparators.py`, `drift/evaluation_snapshot.py` |
| production composition, route resolution, rendering | `production/composer.py`, `production/contract.py`, `production/derivation.py`, `production/adapter.py`, `production_render.py` |
| Braindump transport/error handling versus domain semantics | `braindump.py` 19 error classes plus transport plus operations plus renderers; `sources/braindump.py` |
| duplicated validation or contract logic between nintent and nctl | `nintent/.../compute_contract.py` versus `nctl/.../sources/desired.py`; also check `intent_contract.py`, loaders, and nauto ingest policy for the same pattern |
| output envelopes and error types without a unique caller need | 57 error classes across `src/`; `output.py`; per-command envelope data models |

Absence of a finding is itself a finding and must be recorded — for example, if
`production/derivation.py` already has exactly one reason to change, say so and leave it alone.

## Ownership and dependency map

The final state must be able to answer, in one place, "who owns this?" for each row:

| Value or decision | Intended final owner |
|---|---|
| compute contract semantics (types, bounds, lifecycle, effective values) | one repository, decided in Phase 1; the other consumes or conforms |
| desired-state GraphQL selection and row decoding | `sources/desired.py` transport layer, no domain policy |
| desired-state source-issue classification | the domain owner selected in Phase 2, not the row decoder |
| actual-state GraphQL selection and row decoding | `sources/actual.py` transport layer |
| drift comparison and target status | `drift/` evaluators behind the existing comparator registry |
| action identity, dependencies, and ordering | `reconcile/registry.py` and `reconcile/classify.py` |
| action execution for one action kind | one module per action kind behind the Phase 3 interface |
| reconcile round sequencing, evidence, and terminal state | `reconcile/executor.py`, reduced to orchestration |
| exact target set through scan, inventory, limit, action, observation | unchanged single owner; Phase 3 must prove it stayed single |
| route, port, alias, generation identity | `production/` composition and `inventory_trust.py`, unchanged |
| deterministic artifact bytes and digests | `production/contract.py` canonical JSON and `dnsmasq.py` content digest |
| operation IDs, events, artifacts, index | `events.py`, `artifacts.py`, `operations_index.py`, unchanged |
| envelope shape and emission | `output.py`, unchanged |
| CLI parsing, approval prompts, exit codes, rendering | `cli/main.py` and the `*_render` functions |
| documented module responsibilities | `nctl/README.md` "Layout" section, expanded |

`remove_unused_surfaces`, `interface_contract`, and `test_strategy` are completed prerequisites.

`vm_first_realization` must start after this roadmap, or must explicitly freeze a revision tuple
and accept that it is building on the pre-modularization shape. If both run concurrently they will
collide in `sources/desired.py`, `drift/evaluation.py`, `reconcile/executor.py`, and
`reconcile/reconcilers.py` — the exact files both initiatives touch. This roadmap must not seed
compute rows, add a compute evaluator, add a compute reconciler, or make compute non-inert.

## Keep, delete, replace, and defer manifest

### Keep

- every public command, flag, envelope field, exit code, event, and artifact;
- drift codes, target statuses, and classification outcomes;
- the exact host/guest target set contract through planning, scan, inventory validation, Ansible
  `--limit`, action result, and post-actuation observation;
- plan/apply separation, confirmation prompts, and approval boundaries;
- strict SSH verification, managed-store semantics, and fail-closed distinctions between missing,
  corrupt, unenrolled, unreachable, and mismatched;
- desired-MAC fail-closed behavior and its deterministic recovery;
- partial-progress and post-mutation evidence behavior;
- compute inertness until `vm_first_realization` supersedes it;
- `output.py`, the comparator registry, the reconciler registry, and the model/contract modules;
- every `MANIFEST.md` row's proven behavior, whatever the owning test is finally called; and
- historical operation-artifact readability.

### Delete

- one of the two compute contract implementations, per the Phase 1 decision;
- error types with no caller that distinguishes them, folded into a retained type with a stable
  code;
- helper functions duplicated across modules after a single owner is selected;
- internal abstractions left behind by already-removed public schemas;
- dead parameters, unreachable branches, and pass-through wrappers with one caller and no boundary
  meaning; and
- comments and docstrings that describe a historical phase rather than the current contract.

Nothing on this list authorizes deleting a behavior. Every deletion must be provably a duplicate,
unreachable, or unobservable.

### Replace

- action-kind branching in the executor with an action-execution interface plus per-kind modules;
- duplicated compute validation with one owner plus a conformance mechanism;
- inline domain policy inside GraphQL row builders with a call into the domain owner;
- interleaved transport-error translation and domain semantics in `braindump.py` with a transport
  boundary plus domain operations;
- the README "Layout" stub with a real responsibility map; and
- structure-named test modules with contract-named ones, only where the rename improves ownership
  and the manifest is updated in the same commit.

### Defer

- any new shared Python package, unless Phase 1 proves it is cheaper than the alternatives;
- a provider abstraction, plugin system, generic event bus, or DI container;
- async, concurrency, or performance work;
- a compute evaluator, compute reconciler, compute actuator, or seeded compute rows;
- type-checker strictness gates, lint rule expansion, and formatting-only churn beyond files
  already being edited;
- renaming public config keys, envelope versions, or event fields;
- restructuring nintent, nauto, nodeutils, or ansible_agdev beyond what Phase 1's contract decision
  strictly requires; and
- splitting a module solely because it exceeds a line threshold.

## Scope boundaries

### In scope

- remeasuring nctl structure, coupling, and duplication;
- deciding and implementing one semantic owner for the compute contract;
- separating transport, domain, orchestration, and presentation where they currently mix;
- introducing an action-execution interface with its current implementations;
- consolidating the error taxonomy to types callers actually distinguish;
- moving tests to follow contract ownership and updating `MANIFEST.md` in lockstep;
- documenting the resulting module responsibilities in `nctl/README.md`; and
- before/after measurements of files, lines, module fan-in/fan-out, and suite runtime.

### Out of scope

- changing any supported command, envelope, event, artifact, drift code, or exit code;
- changing drift, planning, actuation, observation, or evidence semantics;
- deploying a nintent schema change beyond what Phase 1's contract decision requires;
- seeding desired compute rows or making compute actionable;
- running a live apply, Job apply, SSH enrollment, Ansible playbook against real nodes, nodeutils
  collection against real nodes, ingest, or any Proxmox mutation without a separate phase plan and
  explicit user approval;
- pushing submodule commits (user-owned);
- reviving removed presentation or remote-server surfaces; and
- adding CI, external services, or new runtime dependencies.

## Phases

Concrete plans and one final report per phase live under `devdocs/big/nctl_modularization/pN/`.

### Phase 0 — Remeasure, map responsibilities, and freeze the seam decisions

**Goal:** produce an evidence-backed structural map and an approved seam plan before any code moves.
No production or test code changes in this phase.

Work:

1. Re-read this roadmap, the refactoring vision, `README_DEV.md`, `.local/localenv_memo.md`, the
   `core_reconcile`, `braindump`, `remove_unused_surfaces`, `interface_contract`, and
   `test_strategy` roadmaps with their final reports, and the VM roadmap with its latest Phase 3
   report.
2. Record exact revisions, dirty state, installed nintent revision in the running image, migration
   state, and whether VM state moved since this baseline.
3. Remeasure: tracked source and test files and lines per package, collected cases, suite runtime
   and slowest tests, and per-module import fan-in and fan-out within `nctl_core`.
4. Build the module responsibility map. For every module over 300 lines and every module named in
   the audit areas, record its responsibilities, its reasons to change, its consumers, its imports,
   and whether it mixes transport, domain, orchestration, or presentation.
5. Produce the duplication inventory across nintent and nctl — the compute contract at minimum, plus
   any other rule implemented twice. For each, record both implementations, their tests, their
   current divergences, and which side observes the rule at write time versus at actuation time.
6. Decide the compute-contract owner and mechanism. Record the deployment consequence of each
   candidate — nintent-owned with generated conformance fixtures, a shared wire contract, a shared
   package, or nctl reduced to transport plus actuation-time safety checks — and why the selected
   one produces less total ownership and deployment complexity.
7. Design the action-execution interface: its exact signature, which current action kinds implement
   it, what the executor keeps, and how the exact-target-set owner is preserved across the seam.
8. Classify all 57 error types as load-bearing, message-only, or unreachable, naming the caller
   that distinguishes each load-bearing one.
9. Map each proposed move to the test modules and `MANIFEST.md` rows it touches, and mark any
   manifested test ID that would be renamed.
10. Record the full baseline run of the root command matrix as the behavior-preservation reference.

**Exit criteria:** every audit area has a keep/split/merge/defer decision with its reason-to-change
analysis; the compute-contract owner and mechanism are chosen with their deployment consequence
stated; the action interface is specified; the error classification is complete; every manifested
test ID that would move is listed; measurements are reproducible; and no source or test file
changed.

### Phase 1 — Resolve the duplicated compute contract

**Goal:** one semantic owner for the compute contract, with an executable mechanism that fails when
the two repositories disagree.

This phase comes first because it is the only cross-repository change, because it constrains what
`sources/desired.py` can look like afterwards, and because leaving it until last would mean
splitting a module around a contract that is about to move.

Work:

1. Implement the Phase 0 decision. If nintent is the owner, nctl retains only transport parsing plus
   the actuation-time safety checks that must hold even against a compromised or stale read, and
   those retained checks are individually justified.
2. Build the conformance mechanism. Generated fixtures must be produced from the owner and consumed
   by the non-owner in an ordinary test, so a future divergence fails a gate rather than silently
   passing on both sides. A fixture that is copied by hand is not a conformance mechanism.
3. Reconcile the existing divergences explicitly: nctl's `validate_compute_lifecycle`,
   `validate_instance_kind`, `validate_power_state`, `_validate_source`, and
   `_validate_link_source_xnor`, and nintent's `PROVENANCE_*` constants. For each, state whether it
   belongs to the shared contract, to one side only, and why.
4. Preserve the actionable-lifecycle predicate under one name and remove the second spelling.
5. Preserve compute inertness. The contract may become single-owner; compute must still produce no
   drift, no plan action, and no actuation.
6. Update both sides' tests to the single owner. Retain every distinct failure mode; delete only
   assertions that are now duplicates of the conformance gate.
7. If nintent changed, commit, request the user's push, rebuild with `--no-cache`, verify the
   resolved nintent commit in the build log, and rerun the Nautobot runtime gate. Record the matched
   revision tuple.

**Exit criteria:** exactly one implementation of each shared compute rule exists; a conformance gate
fails on an injected divergence and is proven to do so; compute remains inert; the nctl ordinary
suite, the nintent tier, and the Nautobot runtime gate pass; and the matched revision tuple and
deployment evidence are recorded.

### Phase 2 — Separate transport from domain in the source and Braindump layers

**Goal:** GraphQL and REST modules translate protocol into domain types and protocol errors into
domain errors, and contain no domain policy.

Work:

1. Reduce `sources/desired.py` to selection, row decoding, and typed model construction. Move the
   surviving compute validation, effective-value resolution, compute collection assembly, endpoint
   MAC validation, and source-issue classification to the owner Phase 0 selected.
2. Confirm `sources/actual.py`'s Proxmox fact reading and error records are transport-shaped, and
   move any policy that decides meaning rather than shape.
3. Separate `braindump.py` into a transport/error-translation boundary, domain operations, and
   rendering. The non-executable prose boundary, the confirmation boundary, and the distinction
   between user prose and AI prose are unchanged and must be re-proven, not merely preserved by
   inspection.
4. Audit `nautobot.py` and `jobs.py` for domain policy that leaked into transport, and for error
   translation duplicated per operation.
5. Apply the Phase 0 error classification: fold message-only types into retained types with stable
   codes, keeping every distinction a caller acts on. Envelope error codes visible to CLI or agent
   consumers do not change.
6. Move tests to follow ownership. Update `MANIFEST.md` in the same commit as any renamed
   manifested ID.

**Exit criteria:** no domain policy remains in a row builder or protocol client; the retained error
types each name a caller that distinguishes them; envelope error codes are unchanged; the prose
authority and confirmation boundaries are positively re-proven; and the nctl suite and the
Nautobot runtime gate pass.

### Phase 3 — Give reconcile orchestration an action-execution seam

**Goal:** the executor sequences rounds, records evidence, and decides terminal state; it does not
know how any individual action is performed.

This is the highest-risk phase. It touches the exact-target-set contract, the SSH preflight
boundary, partial-progress evidence, and the largest test module in the repository.

Work:

1. Introduce the action-execution interface specified in Phase 0 and move `dnsmasq_config`,
   production inventory regeneration, observation, and any other current action kind behind it.
   Registration must not affect behavior or ordering; `reconcile/registry.py` remains the owner of
   identity and DAG order.
2. Remove `action_kind` branching from the executor. The executor must not import a feature module
   to perform an action.
3. Keep the exact target set single-owned end to end. Prove it: the same host set flows through
   planning, SSH scan, inventory validation, Ansible `--limit`, action result, and post-actuation
   observation, and a host-scoped run still excludes siblings.
4. Preserve evidence semantics exactly: `mutated=true` after a successful side effect with a later
   failure, retained action and preflight records, final-drift refresh or a truthful unknown, no
   rewritten history.
5. Extract round sequencing, plan construction, forced-observation handling, scope summary, terminal
   persistence, and text rendering only where each has an independent reason to change.
6. Split `tests/test_reconcile_executor.py` along the same ownership boundary. Both real multi-round
   transitions — dnsmasq content convergence and non-DHCP IPAM convergence — must remain single
   tests that traverse the real drift engine, planner, and executor. They may not be decomposed
   into per-stage unit tests.
7. Update every affected `MANIFEST.md` row in the same commit and rerun its gate.

**Exit criteria:** the executor contains no action-kind branch and no feature-module import for
action execution; every current action kind implements the interface; the exact target set, SSH
preflight, partial progress, and evidence behaviors are positively re-proven at the same layer as
before; both multi-round transitions still run through the real path; and the nctl suite, the
OpenSSH gate, and the Ansible gate pass.

### Phase 4 — Drift evaluation and production composition boundaries

**Goal:** per-resource evaluation and inventory composition have cohesive owners, and the
comparator seam is ready for a compute evaluator that this roadmap does not write.

Work:

1. Separate `drift/evaluation.py` into orchestration and per-resource evaluators for node,
   endpoint, and service, following the shape the existing comparator registry already implies.
2. Give IP-range normalization, overlap classification, and MAC/interface candidate selection and
   scoring their own owner. These are pure deterministic rules with their own consumers and are
   good Tier B table targets, but this roadmap moves them rather than rewriting their tests.
3. Confirm or correct the `drift/evaluation.py` versus `drift/evaluation_snapshot.py` boundary.
4. Verify the seam is sufficient for a future compute evaluator by describing exactly where it
   would register and what it would receive. Do not add a placeholder, stub, or empty registration.
5. Separate `production/composer.py`'s composition from route resolution and report shaping, and
   decide whether `production/contract.py`'s validation schema and canonical-JSON/digest utilities
   are one responsibility or two.
6. Keep deterministic bytes and digests byte-identical. Golden artifacts must not change; a changed
   digest in this roadmap is a defect, not an update.
7. Audit the dnsmasq module family for duplicated skip and finding policy and give it one owner.

**Exit criteria:** drift orchestration does not contain per-resource evaluation logic; the pure
IP/MAC rules have one owner; the future compute evaluator's registration point is documented
without a placeholder; all deterministic artifacts are byte-identical to the Phase 0 baseline; and
the nctl suite passes.

### Phase 5 — Document, remeasure, and report

**Goal:** make the resulting structure legible to the next agent and prove nothing was lost.

Work:

1. Replace the `nctl/README.md` "Layout" stub with a responsibility map: each package and each
   module over roughly 300 lines, what it owns, what it may import, and what it must not.
2. Document the action-execution seam beside the existing "Adding a comparator" section, so
   "Adding a reconciler" is equally answerable.
3. Record the module admission rules from this roadmap in the component development documentation,
   so a future change knows when a split is justified.
4. Run the complete root command matrix: nctl ordinary, nintent Django-free, nauto ordinary,
   nodeutils ordinary, Ansible helper, the Nautobot runtime gate in both `--keepdb` and `--clean`
   modes, OpenSSH conformance, Ansible conformance, privileged-helper integration, and the
   measurement entry point.
5. Verify every `MANIFEST.md` row points at a test that exists, runs, and passes in the named gate.
6. Rerun the Phase 0 measurements with the same method: files, lines, fan-in/fan-out, collected
   cases, runtime, slowest tests, skips.
7. Diff deterministic artifacts against the Phase 0 baseline and prove they are byte-identical.
8. Write one final report with the revision tuple, every deviation, every split with its
   reason-to-change justification, every deferred item, and the definition-of-done verdict.
9. State the handoff to `vm_first_realization`: where a compute evaluator registers, where a compute
   reconciler registers, where an actuator implements the action interface, and which safety
   contracts it inherits unchanged.

**Exit criteria:** module responsibilities and both extension seams are documented; the full command
matrix passes; every manifest row resolves to a passing test; before/after measurements are
recorded with the same method; deterministic artifacts are byte-identical; and the handoff is
explicit.

## Verification matrix

| Area | Required final proof |
|---|---|
| behavior preservation | every root-matrix gate passes with the same meaning as the Phase 0 baseline |
| public surface | no command, flag, envelope field, event field, artifact field, drift code, or exit code changed |
| deterministic artifacts | dnsmasq, hosts-intent, production, and canonical-JSON bytes and digests are identical to baseline |
| compute contract | exactly one implementation; conformance gate fails on an injected divergence |
| compute inertness | zero drift, zero plan action, zero actuation for valid compute rows, unchanged |
| exact target set | one host set through planning, scan, inventory validation, `--limit`, action, observation; siblings excluded |
| SSH boundary | OpenSSH conformance gate passes; missing, corrupt, unenrolled, unreachable, and mismatched remain distinct |
| Ansible boundary | Ansible conformance gate passes; forbidden overrides still rejected; check/apply separation intact |
| plan/apply separation | dry plan still has zero side effects; apply still requires its authority |
| evidence | `mutated=true` with failed confirmation, retained partial progress, truthful final drift or unknown |
| prose authority | Braindump and Alignment Review prose changes still cause zero desired mutation, drift change, plan action, and actuation |
| durable artifacts | historical operation evidence still readable through `nctl ops` |
| module boundaries | pure domain modules import no CLI, HTTP, Nautobot runtime, Ansible, or subprocess; orchestration imports no feature module for execution |
| error taxonomy | every retained type names a caller that distinguishes it; envelope codes unchanged |
| test identity | every `MANIFEST.md` row resolves to an existing passing test at every commit |
| framework restraint | no plugin system, provider abstraction, event bus, or DI container introduced |
| documentation | README responsibility map, both extension seams, and module admission rules are current |
| measurements | same before/after method for files, lines, coupling, cases, runtime, slowest tests |

## Module admission rules

Every module created or split by this roadmap, and every one created after it, must satisfy:

1. it owns one operational value, contract, target set, route, identity, or lifecycle decision;
2. it has a reason to change that is independent of the module it was separated from;
3. it names its consumers;
4. its layer is one of transport, domain, orchestration, or presentation, and it does not import
   downward across that boundary;
5. it does not exist solely to reduce another module's line count;
6. it does not reintroduce a public schema that was deleted as an internal abstraction; and
7. it has a documented place in the `nctl/README.md` responsibility map.

An interface is admissible only with at least two current implementations, or one current
implementation plus a second named in an approved roadmap.

## Required searches

Phase plans must search active source, tests, fixtures, configuration, and current documentation
for at least:

```text
compute_contract
ComputeContractError
validate_provider_type
validate_instance_config
normalize_mac_address
effective_lifecycle
is_actionable_lifecycle
is_actionable_compute_lifecycle
PROVENANCE_
action_kind
_execute_action
register_reconciler
registered_reconciler_ids
register(
run_comparators
DesiredSourceIssue
class .*Error
Envelope[
import nctl_core
from nctl_core
subprocess
Path(
phase
p4
legacy
fallback
shim
TODO
```

Matches are classification input, not instructions. Classify each as retained contract, duplicated
implementation, layering violation, historical comment, or orphan.

Also search both repositories for any other rule implemented on both sides — not only the compute
contract — and for tests that assert module paths, import structure, or symbol placement, since
those will break on a legitimate move and must be re-owned or deleted with their reason recorded.

## Safety, evidence, and rollback

### Safety

- Every phase is behavior-preserving; a behavior change discovered mid-phase is a defect to report,
  not a simplification to keep.
- No live apply, Job apply, SSH enrollment to a real node, Ansible run against real nodes, nodeutils
  collection from real nodes, ingest, or Proxmox operation without a separate phase plan and
  explicit user approval.
- The local Nautobot, PostgreSQL, and Redis stack is scratch, not production. Physical nodes,
  Proxmox, and external services are production/external targets and stay read-only by default.
- Strict SSH verification, exact target scope, Ansible override rejection, plan/apply separation,
  desired-MAC fail-closed behavior, and the non-executable prose boundary are never weakened to make
  a refactor land.
- Missing desired state never authorizes deletion, shutdown, or replacement.
- Secrets, raw keys, tokens, private prose, and live payloads do not enter tracked files, reports,
  or fixtures.
- Compute stays inert for the entire roadmap.
- nintent changes require user-owned push and image rebuild; do not work around that with a
  compatibility branch, and verify the resolved commit in the build log.

### Evidence

Each phase produces one report under `pN/`, not one per step. Reports carry the revision tuple,
decisions with their reason-to-change justification, gate results, measurements, deviations, and a
definition-of-done verdict. Raw command output belongs in operation artifacts or private evidence
under `.local/`, not in tracked prose.

Use the precise states: `complete`, `partially complete`, `implemented, not deployed`, `blocked`,
`superseded`. A passing suite after a move is not by itself proof that a boundary was preserved —
the specific boundary test must be named.

### Rollback

Changes are source-structural and roll back by restoring the prior revision of the affected
submodule. Do not keep an old module alongside a new one as a rollback mechanism.

If a gate fails after a move:

1. stop before moving anything else;
2. restore the prior structure, or fix forward only within the already-approved seam design;
3. rerun the failed gate and the highest-practical-layer test for the affected behavior;
4. record whether any scratch or disposable side effect occurred; and
5. do not describe a unit-level pass as closure of a gate-level failure.

If a cross-repository change is deployed to the scratch stack and must be reverted, revert to the
matched tuple on both sides together. Do not leave nctl reading a contract that the installed
nintent no longer writes.

## Definition of done

This initiative is `complete` only when:

- every audit area named by the vision has a recorded keep, split, merge, or defer decision with
  its reason-to-change justification;
- exactly one semantic owner exists for the compute contract, with a conformance mechanism proven
  to fail on divergence;
- reconcile orchestration depends on an action interface and contains no action-kind branch or
  feature-module execution import;
- drift orchestration is separate from per-resource evaluation, and the registration point for a
  future compute evaluator is documented without a placeholder;
- pure domain modules import no CLI, HTTP, Nautobot runtime, Ansible execution, or subprocess;
- transport modules contain no domain policy and no duplicated per-operation error translation;
- every retained error type names a caller that distinguishes it, and envelope codes are unchanged;
- no new plugin framework, provider abstraction, generic event bus, or DI container was introduced;
- every supported command, envelope, event, artifact, drift code, and exit code is unchanged, and
  every deterministic artifact is byte-identical to the Phase 0 baseline;
- every `MANIFEST.md` row resolves to an existing passing test in its named gate;
- the full root command matrix passes, including both Nautobot runtime modes and all conformance
  gates;
- compute remains inert and no compute row, evaluator, reconciler, or actuator was added;
- `nctl/README.md` documents module responsibilities and both extension seams, and the module
  admission rules are recorded;
- before/after measurements use the same method and every structural change is explained by
  ownership rather than size; and
- every omitted or substituted proof is visible and prevents an unqualified `complete` status.

A smaller file count is not the outcome. The outcome is a kernel where each contract, target set,
route, identity, and lifecycle decision has one findable owner, and where the next roadmap can add
one compute evaluator, one reconciler, and one actuator without editing three 1,200-line modules.
