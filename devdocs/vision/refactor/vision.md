# Refactoring Vision — A Small Deterministic Kernel for an Agent-Operated Cluster

## Purpose

This document is the governing guidance for the refactoring roadmaps that will be created under
`devdocs/big/`. It does not itself define implementation steps. Each roadmap must use this vision
to decide what to remove, what to retain, how to order the work, and what evidence is required
before claiming completion.

The refactoring has five related but separately planned concerns:

1. remove unused presentation and remote-server surfaces;
2. reduce read/write interfaces to the minimum supported contract;
3. reorganize the test strategy around risk and unique failure modes;
4. simplify and modularize the remaining `nctl` implementation; and
5. replace the broad VM roadmap with a bounded roadmap that proves one first guest realization.

The desired result is not the smallest possible codebase. It is the smallest system that still
preserves user intent, makes routine and risky operations deterministic, and leaves enough
evidence for an AI agent or human operator to diagnose a safe stop.

## Documents every roadmap must read

Before writing a roadmap governed by this vision, read:

- `README.md` for the current system overview and operational commands;
- `README_DEV.md` for cross-component safety, evidence, and completion rules;
- `.local/localenv_memo.md` for the current local deployment constraints;
- `devdocs/big/braindump/roadmap.md` for the Braindump/Alignment Review authority boundary;
- `devdocs/big/core_reconcile/roadmap.md` for the history of the current nctl responsibilities;
- `devdocs/big/vm/roadmap.md` and the latest reports under `devdocs/big/vm/` when the work touches
  compute models or the in-progress Phase 3 cutover; and
- the relevant component READMEs and current source before accepting any inventory copied into a
  roadmap.

Historical plans and reports are evidence, not automatically the current contract. Later reports
and this vision supersede earlier statements where they conflict. In particular, the dashboard
and realtime API goals in the original core-reconcile vision are no longer current goals.

## System mission

The system exists so an AI agent can help a user move a local PC cluster toward the user's wishes
without improvising every routine or safety-sensitive operation from scratch.

The agent and the deterministic tooling are complementary:

- the agent interprets wishes, handles ambiguity, asks questions, proposes structured changes,
  investigates failures, and may perform approved one-off operations;
- nintent stores confirmed structured desired state;
- Nautobot and nodeutils provide the actual-state ledger and observations;
- nctl computes drift, plans bounded operations, coordinates repeatable workflows, and preserves
  operation evidence; and
- Ansible or another narrowly approved actuator performs repeatable host-side changes.

`nctl` and `ansible_agdev` are not intended to encode every action an agent might ever perform.
They should encode the repeatable and risky subset for which deterministic scope, validation,
idempotence, and post-change observation materially improve safety or cost.

## Truth and authority layers

Avoid the unqualified phrase "single source of truth." This system has several scoped authorities.

| Layer | Authority | Meaning |
|---|---|---|
| Braindump | User-originated prose | Semantic Ground Truth for what the user wants, including preferences, uncertainty, and constraints |
| Alignment Review | AI-authored prose | The agent's current explanation of how Braindump, desired state, and actual state relate |
| Desired state | Confirmed structured nintent data | Executable commitment accepted by the user |
| Actual state | Nautobot ledger plus fresh nodeutils observations | Latest supported observation of the cluster |
| Drift | Deterministic desired-versus-actual computation | Source of truth for convergence status, not for the meaning of the user's wishes |
| Operation evidence | Plan, events, action results, and post-observation artifacts | Source of truth for what a particular operation attempted and proved |

An active Braindump wish need not always be immediately realizable. It must instead be in one of
these explainable conditions:

- represented in structured desired state and converged;
- represented in desired state but visibly drifting, blocked, or waiting for an approved manual
  step;
- awaiting a named user decision before it can become structured intent;
- explicitly unsupported or deferred, with that limitation stated in the Alignment Review; or
- superseded or withdrawn by confirmed user input.

No wish may disappear merely because it is inconvenient to represent. Conversely, prose alone
must never authorize actuation.

The intended authority flow is:

```text
Braindump
  -> agent reads current desired, actual, and drift
  -> Alignment Review and exact structured proposal
  -> user confirmation
  -> nintent desired state
  -> nctl dry plan
  -> separate apply authority
  -> actuation
  -> fresh observation and drift
  -> refreshed Alignment Review
```

Preserve the non-executable prose boundary. Neither a Braindump body nor an Alignment Review is a
command stream, planner input, drift code, or automatic deletion signal.

## Target architecture

### The deterministic kernel

The retained deterministic kernel should cover:

- canonical desired- and actual-state reads;
- validation needed to fail safely before a mutation;
- deterministic drift and exact target-scope calculation;
- dry planning and explicit apply authority;
- authentication and SSH trust checks;
- repeated or safety-sensitive actuation;
- fresh post-change observation;
- bounded convergence and non-repetition checks; and
- durable operation IDs, event logs, plans, and final result artifacts.

These responsibilities remain even if they require substantial tests. Their cost is justified by
the risk they control.

### Agent-owned flexibility

The following normally remain agent or operator work unless repeated evidence justifies
automation:

- ambiguous wish interpretation;
- read-only exploration and diagnosis;
- approved one-off SSH operations or unusual recovery steps, using only untracked local secret
  references and recording no secret value in evidence;
- an approved manual bootstrap through a console;
- unsupported provider operations;
- choosing among tradeoffs not recorded as structured intent; and
- composing or refreshing Alignment Reviews.

An operation should be promoted into deterministic tooling when one or more of these are true:

- it is expected to recur;
- it mutates more than one object or host;
- it is destructive or hard to reverse;
- it changes identity, credentials, SSH trust, network reachability, or storage;
- it must be idempotent;
- a cheap local model must be able to invoke it reliably; or
- a failure must preserve exact partial-progress evidence.

Do not promote a one-time shell command into a permanent framework solely because an agent used it
once.

## Non-negotiable safety boundaries

Every roadmap must preserve the applicable rules below.

1. Braindump and Alignment Review prose is non-executable.
2. Desired-state write authority and reconcile apply authority remain separate.
3. Strict SSH verification is never weakened to make an acceptance path easier.
4. A host-scoped plan uses one exact target set through validation, preflight, actuation, and
   observation.
5. A mutation is not complete until the changed state is freshly observed through the supported
   path.
6. Successful side effects and partial progress remain visible when a later step fails.
7. Missing desired state never authorizes deletion, shutdown, or replacement of an observed
   resource.
8. Secrets remain outside nintent and tracked evidence.
9. A test passes an intended path only when positive evidence shows that path actually ran.
10. Removing a convenience feature must not remove operation artifacts needed for audit,
    diagnosis, or resumability.

This repository remains in a coordinated breaking-change phase. Remove obsolete runtime
contracts rather than carrying shims, dual readers, deprecated aliases, or fallback routes.
Normal migration history, reversible data migrations, and rollback instructions remain required.

## Current refactoring signals

The following measurements were taken on 2026-07-25. Roadmaps must remeasure them rather than
assuming they are still current:

- `nctl` collects 1,029 pytest cases;
- tracked `nctl` Python source is about 19,186 lines and tracked test code about 21,140 lines;
- tracked test functions across the five submodules number about 1,355;
- dashboard/serve code, templates, and dedicated tests account for at least about 3,590 lines;
- the VM initiative documentation is about 11,169 lines, with a 1,333-line Phase 3 plan; and
- `reconcile/executor.py`, `sources/desired.py`, and `drift/evaluation.py` are each over 1,200
  lines.

These numbers are signals, not deletion quotas. Completion is not defined by reaching an arbitrary
line or test count. A reduction is valuable only when it removes unused behavior, duplicate
contracts, redundant coverage, or unnecessary coupling without weakening the kernel.

## Required roadmap set

The following are recommended as separate roadmaps under `devdocs/big/`. Names may be refined, but
their scopes and dependency boundaries must remain explicit.

### 1. Unused surface removal

Suggested location: `devdocs/big/remove_unused_surfaces/roadmap.md`.

#### Goal

Remove the unused HTTP/WebSocket server, both dashboards, and the derived Nautobot status cache
while preserving CLI operation, machine-readable results, and evidence.

#### Removal inventory that the roadmap must verify

- `nctl serve`, its FastAPI application, runner, WebSocket stream, live dashboard, configuration,
  optional dependencies, schemas, tests, and documentation;
- the static `nctl dashboard` command, HTML renderer/templates, output directory and URL
  configuration, status push, schemas, tests, and documentation;
- automatic dashboard generation from reconcile terminal handling;
- nintent `reconciliation_status` and `reconciliation_checked_at` derived-cache fields;
- serializers, forms, filters, tables, templates, navigation, redirect views, settings, and tests
  that exist only for those fields or the dashboard URL; and
- compatibility snapshots or event fields whose only consumer is a removed surface.

The roadmap must discover the exact inventory from current code. This list is a starting point,
not permission to delete a shared operation-log or artifact helper merely because serve also used
it.

#### Capabilities that must remain

- `nctl status`, `nctl drift`, render commands, `nctl reconcile`, and SSH enrollment;
- human-readable CLI output and `--json` where it has a real CLI/agent consumer;
- reconcile locking;
- operation IDs, JSONL event logs, plan/before/after/result artifacts;
- CLI inspection such as `ops list/show` if still independently useful; and
- Braindump/Alignment Review storage and the agent workflow.

#### Data and rollout guidance

The reconciliation status fields are disposable derived caches, not user intent. Their removal
does not require translating their values into a replacement store. Applied migration history
must remain, and a new migration should remove the live columns.

The roadmap must check the live Phase 3 deployment state. If the compute-schema cutover is still
pending, evaluate whether status-field removal can share the same matched-version maintenance
window. Do not rewrite a migration already applied to the live database merely to reduce the
number of files.

#### Minimum exit criteria

- no serve or dashboard command, import, configuration, dependency, route, template, or documented
  supported schema remains;
- reconcile reaches the same terminal state and writes the same essential evidence without
  attempting dashboard generation or status push;
- nintent has no stale dashboard navigation or cache fields;
- plain CLI installation has no FastAPI/uvicorn dependency; and
- drift, plan/apply, event logging, result inspection, and Braindump workflows still pass their
  retained acceptance paths.

### 2. Canonical interface contraction

Suggested location: `devdocs/big/interface_contract/roadmap.md`.

#### Goal

Give every model and operation the minimum real read/write surface instead of automatically
supporting UI, REST, GraphQL, YAML, CLI, dashboard, and server access everywhere.

#### Governing default

- canonical structured reads use Nautobot GraphQL;
- writes use REST only where GraphQL mutations are unavailable and a real writer exists;
- a user-facing Nautobot UI exists only for a demonstrated human workflow;
- YAML import exists only when source-controlled bulk intent is an actual supported workflow;
- CLI commands are thin agent/human adapters over retained core operations; and
- no API is added solely for hypothetical future clients.

Nautobot's standard `ModelViewSet` may incidentally provide REST GET while it is retained for
POST/PATCH/DELETE. Do not add custom code merely to forbid that incidental read. Instead, keep
GraphQL as the documented and tested canonical read contract and do not create duplicate nctl
readers or full duplicate REST-read test matrices.

#### Required interface matrix

The roadmap must inventory every affected domain object and operation with columns equivalent to:

| Object/operation | Real consumer | GraphQL read | REST mutation | Human UI | YAML | CLI | Decision |
|---|---|---:|---:|---:|---:|---:|---|

Every retained checkmark needs a named current consumer. "Could be useful later" is not a
consumer.

The inventory must include at least:

- DesiredNode, DesiredEndpoint, DesiredService, placements, overrides, dependencies, and IP
  ranges;
- DesiredComputePlatform and DesiredComputeInstance;
- BrainDumpDocument and AlignmentReview;
- actual-ledger objects read by nctl;
- nintent import/analyze/preview Jobs; and
- nctl write operations that call Nautobot Jobs or REST endpoints.

#### Braindump-specific contract

Braindump/Alignment Review is core, not a convenience feature to remove.

Retain the smallest workflow that lets:

- the user create or edit a Braindump through a genuinely used UI or an agent-transcribed path;
- the agent read Braindumps and reviews through GraphQL;
- the agent create, replace, or delete the current review through REST;
- the agent propose confirmed structured desired-state changes through the canonical desired
  writer; and
- the user and agent distinguish user prose from AI prose.

Do not add an LLM runtime, semantic parser, alignment score, findings schema, background reviewer,
history engine, or prose-to-actuation path inside nctl. The existing nctl Braindump wrapper may be
simplified, but its semantic authority and confirmation boundary must remain.

#### Minimum exit criteria

- every supported read and write has one documented owner and one canonical path;
- redundant loaders, serializers, CLI wrappers, YAML roots, and tests are removed where they have
  no named consumer;
- GraphQL remains the joined read path used by nctl;
- REST remains only where a supported mutation requires it, even if framework-provided reads are
  incidentally available; and
- the full Braindump-to-confirmed-desired workflow remains possible without prose becoming
  executable.

### 3. Risk-based test strategy

Suggested location: `devdocs/big/test_strategy/roadmap.md`.

#### Goal

Replace test growth by feature-surface multiplication with a smaller, risk-based suite that
provides stronger evidence for the control-loop transitions that matter.

The roadmap is logically independent of feature removal, but consolidation must occur after
removed features and their tests are deleted. Do not spend time refactoring tests for code already
scheduled for deletion.

#### Required test tiers

**Tier A — safety and mutation boundaries**

Keep strong focused tests and at least one highest-practical-layer control-loop test for:

- SSH trust and identity;
- credentials and authorization failures;
- exact host/guest scope;
- destructive or irreversible boundaries;
- plan/apply separation;
- partial progress and evidence preservation;
- observation freshness;
- idempotence and non-repetition; and
- fail-closed behavior for ambiguous, corrupt, or stale inputs.

**Tier B — deterministic domain logic**

Use table-driven, parametrized, or property-oriented tests for:

- normalization;
- comparator truth tables;
- candidate selection;
- lifecycle combination;
- schema bounds;
- deterministic rendering; and
- classification mappings.

Prefer one clear contract table to many tests that restate the same branch through different
mocking layers.

**Tier C — presentation and convenience**

Use a small smoke or contract test for retained CLI text, UI templates, and other presentation.
Delete the tests with a removed presentation feature. Do not snapshot large internal structures
unless an actual external consumer depends on that exact shape.

#### Test admission and deletion rules

Every new test must identify the unique failure mode it catches that existing coverage would miss.
A production bug reproducer or security boundary may remain even when similar tests exist.

Delete or combine a test when:

- its feature or public contract was removed;
- it asserts an implementation detail rather than observable behavior;
- a higher-layer test proves the same condition with no meaningful diagnostic loss;
- variants differ only in data and belong in a table; or
- it protects a compatibility contract explicitly superseded during this breaking-change phase.

Do not delete tests merely to meet a count. Do not substitute unit tests for required live or
environment-backed proof.

#### Required baseline and outcome measurements

Record before and after:

- collected test cases and tracked test lines by component;
- suite runtime by component and the slowest tests;
- source-to-test line ratio as a diagnostic only;
- the number of separately maintained tests for removed features;
- which state transitions have real planner/executor or environment-backed proof; and
- flaky, order-dependent, or fixture-heavy areas.

#### Minimum exit criteria

- removed features have no orphan tests or fixtures;
- retained Tier A boundaries remain positively exercised;
- duplicate pure-logic variants are consolidated;
- at least one real multi-round test exists for each supported automatic state transition;
- the ordinary test commands and risk tiers are documented; and
- the suite is smaller or simpler for explained reasons, with no acceptance criterion silently
  weakened.

### 4. Remaining nctl simplification and modularization

Suggested location: `devdocs/big/nctl_modularization/roadmap.md`.

#### Goal

After deletion and test consolidation, give the remaining deterministic kernel clear ownership
boundaries and reduce code concentration without introducing a new speculative framework.

This roadmap must not start by splitting files mechanically. First remeasure the remaining code
and identify responsibilities that still change for different reasons.

#### Required audit areas

- reconcile executor orchestration versus action-specific execution;
- desired GraphQL transport models versus compute-domain validation and source-issue handling;
- drift evaluation orchestration versus node, endpoint, service, and compute evaluators;
- production composition, route resolution, and rendering;
- Braindump generic transport/error handling versus domain semantics;
- duplicated validation or contract logic between nintent and nctl; and
- output envelopes and error types that are unique without representing a unique caller need.

For duplicated nintent/nctl compute rules, select one semantic owner. Possible solutions include a
small shared wire contract, generated conformance fixtures, or reducing nctl to transport parsing
plus actuation-time safety checks. Do not create a new generic package unless it produces less
total ownership and deployment complexity than the duplication it replaces.

#### Module boundary rules

- one owner per operational value, target set, route, path, identity, and lifecycle decision;
- pure domain rules do not import CLI, HTTP server, Nautobot runtime, or Ansible execution;
- orchestration depends on action interfaces, not on feature-specific presentation;
- deleted public schemas do not survive as internal abstractions;
- matched-version deployment is preferred to runtime compatibility branches; and
- line count alone is not a reason to create a module.

#### Minimum exit criteria

- remaining large modules have documented, cohesive responsibilities;
- any split is justified by ownership or independent change, not cosmetic size;
- duplicated contracts have one authority or an explicit conformance mechanism;
- no new plugin framework, provider abstraction, or general-purpose event bus is introduced
  without a current consumer; and
- retained end-to-end behavior and evidence are unchanged.

### 5. First VM/guest realization

Suggested location: `devdocs/big/vm_first_realization/roadmap.md`.

#### Goal

Replace the broad later phases of `devdocs/big/vm/roadmap.md` with the smallest workflow that
proves one confirmed compute wish can become one newly realized Proxmox guest through the standard
control loop and is not recreated on a repeat run.

#### Current handoff that must be rechecked

At the time this vision was written:

- VM Phase 1 and Phase 2 were reported complete;
- VM Phase 3 reports Steps 0 through 5 complete locally;
- the live coordinated Phase 3 cutover, seed, desired-MAC environment proof, and final report were
  still later steps; and
- Phase 4 and later compute drift/creation work had not begun.

The new roadmap must inspect the actual revisions, live migration state, reports, and worktrees.
It must not assume this snapshot is still current.

#### Phase 3 scope correction

Retain the desired-MAC safety behavior that prevents an ambiguous or conflicting MAC from
producing an authoritative dnsmasq artifact or actuation. Remove dashboard/status propagation
from that behavior.

Revise old Phase 3 checks that require:

- dashboard rendering;
- dashboard-derived status effects;
- dashboard smoke tests; or
- status-cache write-back.

Replace them with drift JSON, human CLI output where useful, planner classification, action
suppression, stable deployed bytes/digest, and zero SSH/Ansible calls.

Before the old Phase 3 pre-cutover commit/deployment steps, decide whether interface contraction
or status-field removal changes the final matched schema. Do not deploy a known-to-be-obsolete
surface merely because an earlier plan listed it.

#### Exact first-realization contract

The roadmap must choose exactly one disposable guest fixture and name its kind.

- If the success claim is "one QEMU virtual machine," an LXC container does not satisfy it.
- If an LXC is selected as the cheaper first proof, call the result a Proxmox guest/container and
  do not claim that QEMU creation was proven.

For the selected fixture, define only:

- the confirmed Braindump wish and structured desired records;
- platform/control-node identity;
- guest kind and stable candidate identity;
- minimum CPU, memory, root storage, template, bridge, endpoint, MAC, and power intent actually
  needed for creation;
- freshness and collision checks;
- a least-privilege ensure-present/start actuator;
- the manual initial-access and explicit SSH-enrollment safe stops;
- fresh Proxmox observation and Nautobot linking; and
- repeated reconcile behavior.

#### Required state transition

```text
confirmed Braindump wish
  -> exact structured desired proposal
  -> user confirmation and desired write
  -> dry plan for one scope
  -> separate apply authority
  -> create/start actually executes once
  -> fresh Proxmox observation and ingest
  -> stable compute link
  -> waiting_for_manual_initial_access or the next explicitly supported state
  -> repeat reconcile does not recreate the guest
  -> Alignment Review explains the resulting current state
```

The manual initial-access safe stop is a successful resumable terminal when that is the selected
contract. Do not add cloud-init, OpenTofu, a golden-template system, arbitrary guest commands, or a
new bootstrap framework merely to avoid it.

#### Explicit deferrals

Move these out of the first-realization roadmap unless the one selected fixture cannot exist
without them:

- a second guest kind;
- general CPU/memory/disk mutation;
- stop, delete, replace, migrate, shrink, or move;
- automatic initial guest access;
- multi-NIC support;
- AWS, Azure, or generic provider abstractions;
- a new proposal engine inside nctl;
- generalized capacity scheduling; and
- whole-cluster compute lifecycle management.

Each may receive its own future roadmap when a concrete case justifies it.

#### Minimum exit criteria

- one confirmed user wish is represented in structured desired state;
- one dry plan identifies one exact guest scope and its dependencies;
- create/start is positively shown to execute once through the approved boundary;
- fresh observation and ingest identify and link the created resource;
- partial progress survives a manual-access or SSH-enrollment safe stop;
- a repeat run does not recreate the resource;
- unrelated guests are neither acted on nor blocked by target-local failure; and
- the refreshed Alignment Review states what converged, what remains manual, and what is
  unsupported.

## Roadmap dependency and execution order

The roadmaps are separate so their goals and completion claims stay clear. They are not fully
independent in execution.

```text
refactoring vision and current-state recheck
  -> canonical interface decisions
  -> unused surface removal
  -> delete tests belonging to removed behavior
  -> risk-based test consolidation
  -> modularize only the remaining code
  -> resume the bounded first-realization roadmap
```

Some work can be prepared in parallel conceptually:

- the test policy and interface matrix can be written while the removal inventory is collected;
- the VM handoff can be audited read-only; and
- the matched maintenance-window decision can be prepared before code changes.

Avoid concurrent implementation changes in the same nintent/nctl schema and output contracts.
The in-progress VM Phase 3 cutover, status-cache removal, and interface contraction may touch the
same migrations, serializers, GraphQL query, tests, and deployment window. One roadmap must name
the coordinated owner and exact revision tuple when these overlap.

The recommended practical sequence is:

1. pause before deploying the old VM Phase 3 plan unchanged;
2. approve the canonical interface matrix and deletion manifest;
3. revise the remaining VM Phase 3 contract to remove dashboard/status requirements while keeping
   desired-MAC actuation safety;
4. execute the coordinated schema and unused-surface removal with a recorded rollback point;
5. consolidate the tests that remain;
6. modularize only confirmed hotspots in the smaller codebase; and
7. execute the one-guest realization roadmap.

If live deployment state has moved past this sequence, write a truthful transition from the actual
state rather than forcing the repository back to this snapshot.

## Requirements for every concrete roadmap

Each roadmap created from this vision must include:

### Purpose and bounded outcome

- one observable outcome;
- the user or system consumer that justifies it;
- explicit non-goals; and
- a statement of what will be smaller, simpler, or newly proven.

### Current-state inventory

- exact revisions and dirty state;
- live deployment and migration state where applicable;
- current commands, models, API/UI/YAML surfaces, dependencies, tests, docs, and generated
  artifacts in scope;
- named actual consumers; and
- measurements that can be repeated after implementation.

Do not copy a historical inventory without rechecking it.

### Ownership and dependency map

- the canonical owner of every retained model, validation rule, route, target set, artifact, and
  write;
- cross-submodule changes and matched-version constraints;
- other refactoring roadmaps that must finish first; and
- conflicts with the in-progress VM work.

### Keep/delete/replace decisions

For every material surface, state exactly one:

- **keep** — with its current consumer and contract;
- **delete** — with all code, schema, dependency, test, documentation, migration, and artifact
  consequences;
- **replace** — with one final contract and no compatibility-only branch; or
- **defer** — with no placeholder implementation.

### Safety and data transition

- dry-run and approval boundaries;
- database migration and rollback;
- secret handling;
- preservation of operation evidence;
- handling of partial progress;
- live fixture and cleanup where mutation is required; and
- proof that removed derived data was not authoritative user intent.

### Verification

- focused tests for unique remaining risks;
- deletion checks for old commands, imports, fields, routes, config keys, dependencies, schemas,
  docs, and fixtures;
- highest-practical-layer proof for each retained automatic transition;
- environment-backed checks when a framework or external tool defines the behavior; and
- before/after measurements.

### Reporting

Use precise states: `complete`, `partially complete`, `implemented, not deployed`, `blocked`, or
`superseded`.

A successful command with an empty action path is not proof. Removed features should be proven
absent; retained mutation paths should be proven to run; convergence should be proven by fresh
observation and non-repetition.

## Documentation discipline

Refactoring documentation must reduce uncertainty rather than duplicate itself.

- This vision owns the shared philosophy and must not be copied wholesale into every roadmap.
- A `devdocs/big/<initiative>/roadmap.md` owns initiative scope, phases, dependencies, and exit
  criteria.
- A phase plan owns the concrete transition and verification procedure for that phase only.
- A phase report records the final evidence and deviations; raw command output belongs in
  operation artifacts or appropriately protected local evidence, not repeated prose reports.
- Prefer one phase report over one report per small implementation step.
- Link to an authoritative contract instead of restating it in multiple files.
- Preserve historical reports, but mark superseded claims clearly.

Plan length is not itself a quality measure. A plan should be only as detailed as needed to
prevent an unsafe or ambiguous implementation. Enumerating every test input in prose is usually
less maintainable than defining a contract table and letting the test suite express the cases.

## Overall success condition

The refactoring is successful when:

- the user can still record a Braindump as semantic Ground Truth and receive an Alignment Review
  grounded in current desired, actual, and drift state;
- confirmed wishes still enter one canonical structured desired-state path;
- routine and risky operations still use a deterministic dry-plan/apply/observe loop;
- unused dashboard and server surfaces and their derived status cache are gone;
- reads and writes have minimal, named canonical interfaces;
- the test suite concentrates on unique risks and real state transitions rather than surface
  multiplication;
- remaining nctl modules have clear ownership without speculative frameworks; and
- one precisely named Proxmox guest kind has been created once, freshly observed, linked, and
  shown not to be recreated by the standard workflow.

The goal is a system in which a capable remote agent or a cheaper local model can safely operate
the same small deterministic kernel, while unusual work remains possible through explicit,
evidence-backed human/agent judgment.
