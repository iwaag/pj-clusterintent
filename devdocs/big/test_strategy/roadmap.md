# Risk-Based Test Strategy — Development Roadmap

## Purpose

Replace test growth by feature, adapter, and historical phase with a smaller and more legible
suite organized around unique failure modes and supported state transitions.

This roadmap implements item 3 of
[`devdocs/vision/refactor/vision.md`](../../vision/refactor/vision.md). The vision and
[`README_DEV.md`](../../../README_DEV.md) remain authoritative for safety, evidence, and
completion language.

The observable outcome is:

```text
current
  96 test files across five submodules
  + 28,755 tracked Python test lines
  + repeated unit, transport, CLI, historical-phase, and absence assertions
  + strong focused safety coverage that is difficult to identify as one retained set
  + environment-backed proofs that often live only in phase evidence
  + no one documented command matrix for the whole retained kernel

to
  one risk register and transition matrix
  + a small Tier A suite for mutation and safety boundaries
  + table-driven Tier B tests for deterministic domain rules
  + smoke-level Tier C tests for retained presentation
  + reproducible commands that reuse the local scratch environment by default
  + clean disposable gates only where lifecycle or isolation behavior requires them
  + an explicit admission reason for every new test
  + no test that exists only for a deleted feature or superseded compatibility contract
```

The primary consumer is the developer or AI agent changing the deterministic kernel. The suite
must tell that consumer whether a change preserved exact scope, authority, evidence, freshness,
and non-repetition without requiring them to reconstruct old phase history.

This initiative changes test ownership and coverage, not supported cluster behavior. It does not
modularize nctl production code, implement compute reconciliation, create a Proxmox guest, revive
a dashboard or server, or weaken a production/external acceptance requirement.

## Governing decisions

### 1. Risk, not surface count, determines test depth

Classify retained behavior into three tiers:

| Tier | Meaning | Required evidence |
|---|---|---|
| A | mutation, trust, authorization, destructive boundary, scope, freshness, or durable evidence | focused failure tests plus at least one highest-practical-layer transition proof |
| B | deterministic parsing, normalization, validation, comparison, selection, rendering, or classification | table-driven, parametrized, or property-oriented contract tests |
| C | retained CLI text, read-only UI, templates, and other presentation | one small smoke/contract set per real consumer |

A GraphQL parser does not receive Tier A depth merely because it has many fields. A five-line
function that selects an SSH trust identity can require Tier A depth because a wrong answer can
authorize the wrong host.

Every test file, class, or parametrized table must have one primary tier and one named contract.
Tests may exercise several modules, but they must not be counted as several independent proofs of
the same failure mode.

### 2. One unique failure mode should have one primary owner

Coverage at adjacent layers is justified only when each layer catches a different defect:

- a pure test owns domain truth tables and deterministic bytes;
- a transport test owns GraphQL/REST/Job protocol parsing and error translation;
- a core-operation test owns sequencing and evidence;
- a CLI test owns option validation, confirmation behavior, exit code, and rendering; and
- an environment-backed test owns framework or external-tool behavior that mocks cannot prove.

Do not repeat a core success matrix through every CLI command. Do not keep a transport mock, a
core mock, and a CLI mock that all assert the same returned field with no distinct failure mode.
Prefer one primary contract test plus thin adapter smoke tests.

Production bug reproducers, security boundaries, and data-loss regressions are not deleted merely
because a broader test now passes. Their unique defect must first be named and either retained
directly or incorporated visibly into the higher-layer transition fixture.

### 3. Highest-practical-layer does not mean fresh-environment-by-default

Use the lowest environment that still contains the behavior's normative owner:

| Behavior owner | Highest practical layer |
|---|---|
| pure nctl/nintent/nodeutils rule | in-process test with real models and no transport mock |
| Django model, migration, transaction, permissions, or Job discovery | real Nautobot runtime using the persistent local scratch stack and a named test database; real HTTP only where HTTP owns the behavior |
| OpenSSH lookup/config semantics | disposable OpenSSH fixture using the real installed tools |
| Ansible inventory parsing, option precedence, host limiting, playbook check mode | real local `ansible-inventory` or fixture-scoped `ansible-playbook`, not a fabricated return code |
| nodeutils privileged Proxmox helper boundary | the existing real helper integration fixture |
| production/external cluster convergence | separately approved reversible fixture after local gates |

The ordinary suite remains offline with respect to public/external services. It may mutate a
named local test database or fixture-owned scratch state. Reuse the existing local containers and
`--keepdb` during iteration. Recreate the database/process only for migration or lifecycle
coverage, incompatible residue, or a milestone clean run. Environment-backed gates may be slower
and run less often, but their commands and prerequisites must be reproducible. Historical prose
saying a one-off fixture once passed is not a permanent test.

### 4. State-transition tests must prove action, observation, and non-repetition

Each retained automatic transition needs one test shaped like:

```text
initial mismatch
  -> real drift classification
  -> real plan with exact scope
  -> approved action boundary positively invoked
  -> changed state represented by supported observation/ingest
  -> fresh drift
  -> convergence or named resumable safe stop
  -> repeat plan does not repeat the action
```

Mocks may remain at the actual side-effect boundary, such as a disposable Ansible runner, but not
between the real drift engine and planner or between the planner and executor merely to make the
test easier. The test must assert the intended action and any required SSH preflight were
non-empty and targeted the exact expected identity.

Explicit write operations that are not reconcile transitions use the corresponding contract:
dry plan or pre-read, exact write, canonical refetch, persisted evidence, and idempotent repeat
where the operation promises idempotence.

### 5. Compatibility follows current consumers during the breaking-change phase

Durable operation artifacts, JSONL events, CLI JSON envelopes, and the fields consumed by
`nctl ops` remain important. They require read/write round-trip tests and retained-field contract
tests.

The current [`nctl/docs/compatibility.md`](../../../nctl/docs/compatibility.md) also requires a
deprecation window and parallel old/new schema versions for any breaking change. That policy
conflicts with the repository-wide coordinated breaking-change rule. Phase 0 must resolve the
conflict explicitly.

The intended final decision is:

- keep exact contracts required by current CLI/agent consumers and durable evidence readers;
- change a schema only in a matched-version rollout with migration or explicit historical-reader
  handling where existing on-disk evidence still needs to be inspected;
- do not retain an event or envelope field whose only consumer was removed;
- do not run parallel runtime writers merely to preserve an obsolete schema; and
- replace broad "floor forever" snapshots with contract tests tied to named consumers.

Existing evidence must not silently become unreadable. If `ops show` must continue reading an
older on-disk artifact, preserve the smallest reader or provide an explicit offline migration;
do not infer that this requires every old producer to remain.

### 6. Measurements diagnose; they do not authorize deletion

Record before and after:

- test files, statically declared test functions/methods, and collected cases;
- tracked test and non-test Python lines by component;
- runtime by component and slowest tests;
- fixture, mock, parametrization, and repeated-helper concentration;
- source-to-test line ratio as a diagnostic only;
- state transitions with real planner/executor or environment-backed proof;
- tests deleted with removed behavior;
- tests consolidated by unique failure mode; and
- flaky, order-dependent, network-dependent, and environment-skipped tests.

There is no numeric deletion quota. A net case-count increase is acceptable only when it closes a
named Tier A gap and the report separately shows what duplication or obsolete coverage was
removed. Completion still requires the suite to be smaller or simpler for explained reasons.

### 7. A test must be deterministic, isolated, and truthful

- Freeze time explicitly when time affects freshness, operation ordering, or status.
- Use stable fixture identities and deterministic ordering.
- Never depend on test execution order or residue from a prior run.
- Never call the public internet from an ordinary test.
- A test that needs Nautobot, OpenSSH, Ansible, sudo, or Proxmox must declare and check that
  prerequisite instead of silently changing semantics.
- Skip only when the test belongs to a documented optional environment tier. A Tier A gate may
  not silently skip in the environment where it is required.
- Isolation uses the smallest effective boundary: transaction rollback, stable synthetic IDs,
  named test database, temporary directory, or fixture-owned process.
- Persistent scratch containers, databases, networks, and volumes may remain and be reused when
  they are declared prerequisites. Teardown removes only state the individual test promises to
  own; milestone clean-run checks verify recreation and cleanup separately.
- A recoverable scratch leak or stale test database fails the affected gate and is repaired; it
  does not by itself block the entire roadmap.
- Empty actions, preflight lists, HTTP request logs, or observation sets mean the intended path
  was not exercised.

## Current-state baseline

This baseline was measured on 2026-07-26 before adding this roadmap. Phase 0 must repeat it rather
than treating it as permanent.

### Revisions and worktrees

| Component | Revision | State at measurement |
|---|---|---|
| superproject | `39dc8688520eb3b81a4995620e4aa1dc0cc95502` | clean |
| nctl | `e813f6963afc17af74c48aae5660461d3f10498a` | clean |
| nintent | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | clean |
| nauto | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | clean |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

The nctl revision includes the post-interface-contract fix that preserves mutation evidence when
`link_actual_node` or IPAM partially mutates and a later confirmation fails. Its focused
ledger/executor gate and the full 967-case nctl suite pass.

### Live and environment state

- The canonical interface contraction is deployed and its Phase 4 report is `complete`.
- The three local Nautobot web/worker/scheduler containers were healthy during this audit.
- nintent migrations are applied through
  `0016_remove_reconciliation_dashboard_surfaces`.
- The deployed canonical YAML, GraphQL, narrow REST, and read-only UI contract is the starting
  contract for this roadmap.
- VM Phase 3's latest report completes its old Steps 0-7. Its pre-deployment handoff is historical:
  interface-contract Phase 4 subsequently deployed migrations `0015` and `0016` and the final
  matched interfaces. Desired compute rows remained unseeded in that final report, so VM Phase 3
  Steps 9-12 still have no completion report. The compute/MAC seed and later realization are not
  authorized by this roadmap.
- No live Job, REST mutation, SSH, Ansible, nodeutils collection, ingest, or provider action was
  run while measuring this baseline.

### Test and line measurements

Tracked line counts include Python files known to Git; Ansible YAML and shell are intentionally
not folded into this Python-only comparison. "Local result" is the normal command available from
the current checkout; it is not substituted for the real Nautobot App suite.

| Component | Test files | Declared test functions/methods | Test lines | Non-test Python lines | Local result | Wall/runtime signal |
|---|---:|---:|---:|---:|---|---|
| nctl | 72 | 901 | 19,706 | 17,783 | 967 passed | 5.54 s pytest / 5.82 s wall |
| nintent | 12 | 304 | 5,407 | 9,419 | 226 run, 13 skipped | 0.039 s unittest / 0.12 s wall |
| nauto | 8 | 110 | 2,579 | 3,010 | 110 passed | 0.022 s unittest / 0.10 s wall |
| nodeutils | 3 | 54 | 917 | 2,157 | 54 passed | 2.24 s pytest / 2.44 s wall |
| ansible_agdev helper | 1 | 8 | 146 | 152 | 8 passed | 0.001 s unittest / 0.03 s wall |
| **Total** | **96** | **1,377** | **28,755** | **32,521** | — | — |

The exact nintent revision also passed 304/304 tests in a disposable real Nautobot environment
during interface-contract Phase 4. That is the current environment-backed baseline, not a claim
that the fast local command exercises those 304 cases.

The ordinary commands used for this measurement were:

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

### Concentration and runtime signals

The largest current test files are:

| File | Lines | Signal to investigate, not a predetermined deletion |
|---|---:|---|
| `nctl/tests/test_reconcile_executor.py` | 2,355 | many Tier A paths share local stubs and one module |
| `nintent/.../tests/test_loaders.py` | 1,270 | closed-schema variants may fit contract tables |
| `nctl/tests/test_dnsmasq_apply.py` | 1,033 | renderer, trust, Ansible, and CLI-adjacent concerns overlap |
| `nctl/tests/test_production_composer.py` | 1,023 | many deterministic branch variants |
| `nintent/.../tests/test_importers.py` | 926 | ownership and preview/apply cases need layer classification |
| `nauto/tests/test_proxmox_cluster_vm_upsert.py` | 817 | valuable safety logic is tested through a large fake ORM |
| `nauto/tests/test_proxmox_interface_ip_upsert.py` | 775 | same fake-ORM concentration and partial-evidence risks |
| `nctl/tests/test_drift_evaluation.py` | 724 | comparator/classification tables may overlap other files |

The slowest nctl tests are repository-status tests at about 0.27-0.31 seconds each because they
spawn Git commands. The existing real multi-round dnsmasq and IPAM tests take about 0.05 and 0.03
seconds respectively; their importance is risk coverage, not runtime.

Nodeutils' slowest and materially dominant test is the real privileged-helper boundary at about
2.17 seconds. Keep it unless an equally real replacement proves the same allowlisted execution
boundary. Its runtime is justified.

### Current strengths to preserve

- nctl has real drift-to-plan-to-executor multi-round tests for dnsmasq content convergence and
  non-DHCP IPAM convergence.
- reconcile tests cover partial progress, post-mutation failure, final-drift refresh failure,
  exact host scope, fresh route regeneration, and evidence retention.
- SSH enrollment, trust, preflight, malformed store, non-default port, and route identity have
  extensive focused coverage.
- nintent Import and Analyze have dry/apply/transaction/confirmation/repeat proofs in a disposable
  Nautobot environment.
- nintent's real App suite covers GraphQL, narrow REST, read-only UI permissions/routes, and model
  constraints.
- nauto covers stale observation rejection, guest-local failure isolation, no-op repeats,
  transaction behavior, IP namespace identity, and Proxmox actual-ledger materialization.
- nodeutils has a real helper-boundary integration test and closed managed-file observation tests.
- the removed server/dashboard tests are already gone; this roadmap need not refactor them.

### Known gaps and ambiguities to resolve

1. Interface-contract Phase 4 records one remaining gap: representative fail-closed node-link
   reset fixtures are covered with mocks but not through real HTTP against the named scratch test
   database.
2. Environment-backed nintent/nauto proofs are reproducible from phase evidence, but the
   repository does not yet document one stable cross-component command/harness as an ordinary
   risk-tier gate.
3. Many nauto Proxmox tests use a hand-built fake ORM. The fake is useful for fast domain
   diagnostics, but transaction, constraint, and framework behavior need a smaller real-Nautobot
   conformance set.
4. Ordinary nctl tests fake most `ssh-keyscan`, `ssh -G`, `ssh-keygen`,
   `ansible-inventory`, and `ansible-playbook` calls. Past environment proofs must be mapped to a
   maintained external-tool gate.
5. nintent's fast suite conditionally omits Nautobot-only cases. The distinction between fast and
   required runtime gates is documented in nintent but not as a repository-wide command matrix.
6. `nctl/docs/compatibility.md` promises deprecation-window dual schemas while the governing
   project policy requires coordinated breaking changes without compatibility-only runtime
   artifacts.
7. Historical names such as `test_p4_*`, `test_phase3_*`, and
   `test_vm_p3_compute_stays_inert.py` describe when a test was added rather than the lasting
   risk it owns. Some contain valuable cross-layer contracts; names alone neither retain nor
   delete them.
8. `nintent/test_remove_unused_surfaces.py` mixes lasting schema-absence checks, UI smoke,
   navigation, API, and historical-removal assertions that now overlap the canonical API/UI
   contract suites.
9. CLI/core/source tests for Braindump and several render operations may repeat success/error
   matrices at adjacent layers. The non-executable prose boundary and canonical refetch behavior
   must remain even if adapter duplication is removed.
10. No maintained manifest currently states which automatic transitions have real multi-round
    proof and which are intentionally manual, unsupported, or inert.

## Required risk and transition matrix

Phase 0 must turn the following starting matrix into an evidence-linked manifest. "Required
owner" names the final proof, not necessarily the current filename.

| Risk or transition | Tier | Required primary proof | Current disposition |
|---|---|---|---|
| SSH stable DesiredNode identity, offered-key match, malformed store, non-default port | A | focused trust tables plus real disposable OpenSSH fixture | keep and consolidate only true duplicates |
| credential source validation, token redaction, HTTP 401/403, Job authorization | A | focused config/error tests plus representative real HTTP denial | keep; add environment proof if absent |
| cluster/host exact scope through scan, inventory, `--limit`, action, observation | A | real planner/executor fixture and real Ansible boundary | keep and close any boundary substitution |
| dry-plan/apply separation for reconcile | A | zero-side-effect dry operation plus positive apply fixture | keep |
| successful mutation followed by failed confirmation | A | exact `mutated=true`, preserved action/evidence, fresh-drift or unknown result | keep post-interface side-fix regression |
| partial IPAM apply followed by failure | A | applied IDs retained, final drift refreshed, no history rewritten | keep |
| observation identity, freshness, schema, and managed-file path/digest | A | nodeutils report -> nauto ingest -> nctl fresh snapshot contract | replace isolated duplicate fixtures with shared versioned conformance data where useful |
| dnsmasq content mismatch -> deploy -> observe -> converge -> no repeat | A | existing real multi-round engine/planner/executor test plus external-tool boundary | keep |
| non-DHCP endpoint missing link -> IPAM -> refetch -> converge -> no repeat | A | existing real multi-round engine/planner/executor test plus real Job/HTTP conformance | keep |
| DesiredNode actual-link action | A | GraphQL pre-read -> PATCH -> GraphQL refetch -> fresh drift -> no repeat; include fail-closed reset | strengthen; closes known real-HTTP gap |
| forced observation refresh | A | exact host, one observation, fresh ingest, repeat convergence | keep |
| Import desired YAML preview -> apply -> confirm -> repeat no-op | A | real Nautobot Job in the named scratch test database and row fingerprint | keep one primary proof |
| Analyze source preview -> apply -> preserve operator fields -> repeat no-op | A | real Nautobot Job in the named scratch test database with local deterministic fetch fixture | keep one primary proof; no public-network dependency |
| nauto nodeutils/Proxmox ingest | A | valid report applies, invalid/stale report writes zero, partial guest failure is isolated, repeat no-op | keep fast logic plus small real ORM conformance |
| missing desired row | A | never delete, unlink, stop, replace, or retire an observed resource | keep explicit negative boundary |
| compute desired rows before first-realization roadmap | A | no compute drift, plan, writer, or provider action | keep until a later roadmap explicitly replaces it |
| desired-MAC conflict or ambiguity | A | blocked render has no authoritative bytes/digest, SSH, Ansible, or sibling-target effect; recovery is deterministic | keep the VM Phase 3 safety contract |
| Braindump/review write and non-executable prose | A for authority, C for text | canonical read/write/refetch plus proof prose-only edits cause no drift/action | keep boundary; shrink adapter repetition |
| normalization, lifecycle combinations, selection, schema bounds, classification | B | named tables or generated cases with readable IDs | replace branch-by-branch repetition |
| deterministic dnsmasq/hosts/production rendering | B | golden bytes/digest plus semantic edge table and real parser validation | keep unique contracts; combine redundant envelopes |
| GraphQL/REST/Job payload decoding | B, A for mutation errors | compact protocol tables and a real framework smoke | replace repeated per-operation transport errors where the mapping is identical |
| retained CLI help, exit codes, confirmation prompts, JSON/text | C, A where approval applies | one smoke matrix plus focused authority tests | reduce success-path multiplication |
| read-only nintent UI | C, A for absence of mutation | full route/permission manifest plus small representative rendering set | consolidate historical removal assertions |
| operation JSONL/artifact/ops inspection | A | write/read/restart/corruption/partial-log contract using real files | keep; replace obsolete compatibility floors |

The final manifest must distinguish:

- **automatic transition** — requires multi-round non-repetition proof;
- **explicit mutation** — requires authority, exact write, confirmation, and truthful evidence;
- **read-only deterministic operation** — requires stable domain output, not an apply loop;
- **manual safe stop** — requires evidence and resumability, not fake convergence; and
- **unsupported/inert** — requires proof that no action is emitted.

## Ownership and dependency map

| Concern | Final test owner |
|---|---|
| user wishes and non-executable prose | nintent model/API contract plus nctl Braindump authority test |
| canonical desired and actual transport | nctl source contract tests against pinned GraphQL selections |
| desired YAML validation and field ownership | nintent Tier B loader/import tables |
| Import/Analyze database transactions | nintent real-runtime gate in the named scratch test database |
| actual-ledger ingest policy | nauto fast domain tests plus scratch Nautobot conformance |
| drift comparison and target status | nctl Tier B drift tables |
| planning and exact action scope | nctl planner Tier B/Tier A boundary tests |
| orchestration, evidence, partial progress, non-repetition | nctl reconcile Tier A transition suite |
| SSH behavior | nctl focused contracts plus disposable OpenSSH gate |
| Ansible parsing and actuation boundary | nctl/ansible_agdev real-tool conformance gate |
| host observation schema and privileged helper | nodeutils plus ansible_agdev helper tests |
| read-only Nautobot presentation | nintent Tier C runtime smoke |
| local command documentation and final measurements | root README_DEV plus component development docs |

`remove_unused_surfaces` and `interface_contract` are complete prerequisites. This roadmap must
finish before `nctl_modularization`, so module splitting does not preserve duplicate or
implementation-detail tests by accident.

The in-progress VM work may change compute schemas but must not introduce compute actuation while
this roadmap runs. Keep the inert-compute safety test until the bounded first-realization roadmap
replaces it with an exact one-guest transition. Avoid concurrent edits to the same nctl
reconcile/compute tests; record and freeze the revision tuple if VM Phase 3 moves during this
initiative.

## Keep, delete, replace, and defer manifest

Phase 0 must classify every test file and shared fixture. The following decisions govern that
classification.

### Keep

- every production-bug reproducer that still protects a reachable contract;
- strict SSH trust, enrollment, path, identity, and fail-closed cases;
- exact host/guest scope and unrelated-target isolation;
- plan/apply separation and confirmation prompts;
- mutation evidence, partial progress, event/artifact privacy, and corruption handling;
- observation freshness, wrong identity/path, bounded file read, and schema rejection;
- transaction rollback, zero-write preview, explicit apply, and repeat idempotence;
- the real multi-round dnsmasq and IPAM transitions;
- one real helper/OpenSSH/Ansible/Nautobot proof where those external implementations own the
  semantics;
- one golden deterministic artifact per externally consumed byte contract; and
- the temporary compute-inert boundary until an approved roadmap supersedes it.

### Delete

- tests, fixtures, helpers, snapshots, docs, and dependencies whose only feature was the removed
  HTTP/WebSocket server, either dashboard, status cache, editable UI, removed REST collections,
  duplicate Jobs, or old YAML writers;
- compatibility assertions whose only consumer was removed;
- tests of private call order, helper name, intermediate object shape, or module placement where
  no external behavior or diagnostic boundary depends on it;
- duplicate adapter success cases already proven by a core contract and one adapter smoke;
- one-case functions whose only difference belongs as a row in an existing table;
- historical phase-name wrappers after their lasting contract is moved to a domain/risk-owned
  file; and
- skipped tests that can never run in any documented tier.

Historical migrations and historical reports are not test artifacts to delete.

### Replace

- broad compatibility floors with current-consumer evidence read/write contracts;
- repeated comparator, lifecycle, normalization, validation, and error-mapping functions with
  readable parametrized tables;
- repeated GraphQL/REST mock payload builders with small versioned conformance fixtures owned by
  the selected transport contract;
- large fake-ORM-only confidence with a combination of fast pure policy tests and a small real
  Nautobot transaction/constraint gate;
- scattered environment recipes with one documented, reusable local scratch harness plus a clean
  reconstruction mode;
- historical filenames with risk/domain filenames when the move improves ownership; and
- exhaustive UI rendering at every route with a complete route/permission/no-mutation manifest
  plus representative template rendering, unless a model has unique content semantics.

### Defer

- Hypothesis or another property-testing dependency unless Phase 2 finds a concrete generator
  that materially simplifies a current truth table;
- coverage-percentage gates and arbitrary line/case targets;
- a generic test framework, plugin system, provider matrix, or cross-repository test package;
- performance/load testing, distributed chaos testing, and production-grade CI infrastructure;
- AWS, Azure, a second compute provider, and a second guest kind;
- tests for unimplemented stop/delete/replace/migrate/resize operations; and
- nctl production modularization except for a minimal behavior-preserving seam needed to test an
  external boundary.

## Scope boundaries

### In scope

- inventory and classify all active tests and shared fixtures across the five submodules;
- delete orphan coverage left by completed removal/contraction work;
- resolve the nctl compatibility-policy conflict;
- consolidate duplicate deterministic cases into explicit tables;
- establish the Tier A transition manifest;
- preserve and strengthen safety/mutation coverage;
- close the known node-link real-HTTP fail-closed gap;
- add small real-framework/external-tool gates where mocks currently own normative behavior;
- standardize local scratch and clean-gate command documentation;
- record runtime, slowest tests, skips, flakiness, and before/after measurements; and
- update current documentation to explain test admission and risk tiers.

### Out of scope

- changing desired, actual, drift, planner, actuation, or evidence semantics merely to simplify a
  test;
- deleting a test solely because it is long, slow, old, or named after a historical phase;
- replacing required framework-backed or production/external acceptance with unit coverage;
- deploying a schema or desired-state change;
- running a live apply, Job apply, SSH enrollment, Ansible playbook, nodeutils collection, ingest,
  or Proxmox mutation without a separate phase plan and user approval;
- splitting the remaining large nctl source modules;
- compute drift, compute linking, guest creation, or provider abstractions;
- reviving removed presentation or remote-server interfaces; and
- adding public CI or external services without a current repository need.

## Phases

Concrete plans and one final report per phase should live under
`devdocs/big/test_strategy/pN/`.

### Phase 0 — Freeze risks, consumers, layers, and measurements

**Goal:** produce an evidence-backed manifest before deleting or combining any test.

Work:

1. Re-read this roadmap, the refactoring vision, README_DEV, local environment memo,
   Braindump roadmap, core-reconcile roadmap, remove-unused-surfaces final report,
   interface-contract roadmap/final report, VM roadmap, and latest VM Phase 3 report.
2. Record exact root/submodule revisions, dirty state, installed nintent/nauto revisions,
   migration state, and whether VM seed/cutover state changed.
3. Collect every suite with the environment that actually owns it. Record test IDs, file,
   primary tier, named contract, side-effect boundary, mocks, fixtures, runtime, skip reason, and
   unique defect.
4. Rerun tracked source/test line counts, test files/functions/collected cases, component runtime,
   slowest tests, and source-to-test ratios with commands committed to the phase evidence.
5. Search current code and docs for deleted surfaces and classify every surviving test reference
   as negative absence proof, migration/history, or orphan.
6. Build the exact automatic-transition/explicit-mutation/read-only/manual/inert manifest from the
   matrix above. Link each current proof and mark each gap.
7. Inventory shared fixtures and repeated builders by semantic payload. Do not merge fixtures
   merely because their dictionaries look similar if they represent different trust boundaries.
8. Audit mocked external behavior against OpenSSH, Ansible, Nautobot/Django, and filesystem
   semantics. Identify the smallest real-tool conformance cases.
9. Resolve `nctl/docs/compatibility.md` against the governing breaking-change policy and freeze
   the final artifact/event/envelope consumers before editing snapshots.
10. Run the complete unmodified baseline twice in deterministic order and once in a perturbed
    order where the runner supports it. Record any flake, leaked process/file/database, or
    order dependency.

**Exit criteria:** every active test has a tier and unique-contract disposition; every supported
transition has a named current proof or visible gap; the compatibility decision is explicit; all
baseline commands and measurements are reproducible; and no test or production code changed.

### Phase 1 — Remove orphan and superseded contract coverage

**Goal:** delete only tests whose behavior or contract is already removed or explicitly
superseded.

Work:

1. Delete any remaining active fixture/import/helper for serve, dashboard, status cache, removed
   REST collections, editable nintent UI, Quick Host Add, Source YAML, Preview Analyze,
   Generate Desired Services, or duplicate nauto desired writers.
2. Consolidate `nintent/test_remove_unused_surfaces.py` into the final model/API/UI/migration
   contracts:
   - keep one runtime proof that removed fields and routes are absent;
   - keep migration application/history proof;
   - remove repeated per-layer absence checks with no distinct consumer; and
   - keep the complete no-mutation route/permission manifest under the canonical UI owner.
3. Replace obsolete compatibility snapshot entries and deprecation-window wording according to
   Phase 0's approved current-consumer decision.
4. Rename or move historical `p4`, `phase3`, and similar tests only after recording the lasting
   contract and proving collected IDs remain represented. The compute-inert safety case stays.
5. Remove orphan fixtures, test-only dependencies, generated snapshots, and documentation in the
   same commit as their last test consumer.
6. Run deletion searches and the affected component's focused suite after each cleanup. Run its
   ordinary suite once when that component workstream is complete.
7. Compare the removed-test manifest with the final interface matrix; any test for a retained
   mutation or evidence contract blocks deletion.

**Exit criteria:** no active test belongs solely to a removed feature or superseded compatibility
branch; every deletion has a named removed consumer; migration/history exceptions are preserved;
all retained Tier A tests still pass; and before/after counts are recorded without using them as
the success criterion.

### Phase 2 — Consolidate deterministic Tier B and adapter Tier C coverage

**Goal:** express pure rules once and retain only the adapter checks that catch adapter-specific
failures.

Work:

1. Convert normalization, lifecycle, schema-bound, candidate-selection, placement, freshness,
   comparator, classification, and error-mapping variants to readable contract tables.
2. Give every table row a stable descriptive ID and enough expected output to diagnose a failed
   rule without inspecting implementation branches.
3. Consolidate repeated nctl GraphQL/REST response fixtures by canonical query or mutation
   contract. Preserve malformed, missing, duplicate, unauthorized, stale, and contradictory
   variants where each produces a distinct safe failure.
4. Reduce CLI repetition to:
   - one representative success/JSON/text smoke per retained command family;
   - usage, approval, exit-code, and redaction cases unique to the adapter; and
   - no restatement of the full core matrix.
5. Reduce read-only UI presentation to the complete route/permission/no-POST manifest plus
   representative rendering for unique templates, including separated autoescaped Braindump and
   Alignment Review prose.
6. Keep golden-byte tests only for actual downstream contracts. Pair each with semantic tests so
   a changed digest can be reviewed rather than blindly updated.
7. Split or merge test files by contract ownership only. Do not reorganize nctl production
   modules in this phase.
8. Run focused tests during each conversion, the affected component suite when its workstream is
   complete, and the Nautobot runtime gate once after the nintent/nauto changes that require it.
   Reuse the scratch test database during iteration.

**Exit criteria:** Tier B rules are readable tables instead of repeated branch tests; Tier C has
smoke-level depth except where authority is involved; failures remain diagnosable; golden files
have named consumers; and no Tier A condition was weakened or hidden in a broad parameter table.

### Phase 3 — Close Tier A transition and external-boundary gaps

**Goal:** make every retained mutation and automatic transition positively provable at its
highest practical layer.

Work:

1. Preserve the real multi-round dnsmasq and IPAM tests and refactor their fixtures only if the
   real drift/planner/executor path remains intact.
2. Add a durable DesiredNode link transition fixture:
   - GraphQL pre-read sees an unlinked exact node;
   - exact PATCH succeeds or is rejected at the intended point;
   - GraphQL confirmation succeeds, mismatches, disappears, resets, or returns the wrong identity;
   - post-write failure records `success=false, mutated=true`;
   - fresh final drift is obtained or truthfully marked unknown;
   - repeat planning does not relink a confirmed node; and
   - the representative fail-closed reset variants run through real HTTP against the named
     scratch test database.
3. Add or retain one disposable OpenSSH proof for bare stable alias, non-default route port,
   malformed managed store, offered-key mismatch, and effective-option precedence. Assert the
   real command path and exact public fingerprint without persisting raw key material in tracked
   evidence.
4. Add or retain a real Ansible boundary proof for staged inventory validation, exact host limit,
   forbidden SSH overrides, check/apply separation, and no playbook start after failed preflight.
5. Establish a small real Nautobot conformance gate for:
   - Import preview/apply/confirmation/repeat;
   - Analyze preview/apply/operator-field preservation/repeat;
   - IPAM transaction and actual field choices;
   - node-link and lifecycle GraphQL/REST behavior;
   - nauto valid/stale/invalid/partial Proxmox ingest; and
   - permission and authentication denial.
6. Prove the nodeutils managed-file observation and Proxmox helper outputs traverse the selected
   nauto/nctl schema fixtures without a second hand-maintained interpretation.
7. Prove Braindump or Alignment Review prose changes alone cause zero desired mutation, zero drift
   code change, zero plan action, and zero actuation.
8. Preserve the desired-MAC fail-closed path: mismatch, ambiguity, or invalid compute source data
   emits structured target-local diagnostics, produces no authoritative dnsmasq bytes or digest,
   leaves an existing output untouched, invokes zero SSH/Ansible calls, and recovers
   deterministically when the same canonical desired value becomes valid.
9. Keep compute desired rows inert through the real drift/planner dispatch until the later
   first-realization roadmap explicitly changes that contract.
10. For each Tier A test, record positive evidence that its action, preflight, write, observation,
   or denial actually ran. An empty path fails.
11. If a test exposes a production defect:
    - preserve the failing reproducer;
    - record the defect and its authority impact;
    - implement a bounded correction in the affected phase when the authoritative contract is
      already clear;
    - create a separate plan only when behavior must be chosen, scope materially expands, or a
      new production/external mutation boundary is introduced; and
    - rerun the highest practical transition, not only the new unit test.

**Exit criteria:** every supported automatic transition has one real multi-round proof; every
explicit mutation has authority/write/refetch evidence; external-tool assumptions run against
their normative implementation; the known real-HTTP node-link gap is closed; partial progress is
truthful; and unsupported/inert paths emit no action.

### Phase 4 — Standardize commands, verify isolation, and report the final strategy

**Goal:** make the resulting tiers reproducible for future developers and agents.

Work:

1. Document one command matrix in root README_DEV and link from component developer docs:
   - fast per-component commands;
   - full ordinary offline commands;
   - scratch-reusing Nautobot integration command;
   - clean Nautobot database reconstruction command for migration/final verification;
   - OpenSSH/Ansible/helper conformance commands;
   - any separately approved production/external acceptance command; and
   - prerequisites, expected skips, evidence location, and cleanup for each.
2. Ensure commands run from their documented working directories and do not rely on the
   superproject pytest accidentally discovering several submodules.
3. Run the affected fast/ordinary suites once, the complete ordinary suite once at final
   integration, one clean Nautobot gate, and the external-tool gates with the actual installed
   versions. Run repeated or alternate-order suites only for a named flake/order-dependence risk.
4. Verify ownership: persistent scratch prerequisites are documented; fixture-owned processes,
   rows, files, trust stores, generated inventories, and operation logs do not escape their
   declared scope. Do not classify the expected persistent scratch stack as a leak.
5. Run collected-case and tracked-line measurements with the same Phase 0 scripts; record runtime
   and slowest tests by component.
6. Review every skip and xfail. Each must name an optional environment or an open defect; no
   required Tier A proof may be silently skipped.
7. Search for removed surfaces, obsolete compatibility claims, orphan fixtures, historical-only
   active names, public-network test calls, secret literals, and undocumented test commands.
8. Confirm every retained automatic transition, explicit mutation, read-only operation, manual
   safe stop, and inert path in the manifest points to a passing test and current contract.
9. Record the exact final revision tuple, all deviations, tests deleted/combined/added, gaps
   closed, and any truthfully deferred item in one final report.

**Exit criteria:** a fresh agent can run the appropriate tier without consulting historical phase
reports; all gates are deterministic and clean up after themselves; before/after measurements and
slowest tests are recorded; every Tier A transition is linked to passing evidence; and the suite
is smaller or simpler for explicitly documented reasons.

## Verification matrix

| Area | Required final proof |
|---|---|
| Inventory | every active test/fixture has tier, owner, unique failure mode, environment, and disposition |
| Removed behavior | no operative test/helper/dependency remains outside migration/history or one named absence contract |
| Tier A | mutation, scope, trust, authorization, freshness, partial progress, and evidence boundaries positively run |
| Tier B | deterministic rule variants are explicit tables with diagnostic row IDs |
| Tier C | retained presentation has smoke depth and no duplicate domain matrix |
| dnsmasq | mismatch, real plan/action/preflight, observed digest, convergence, no repeat |
| IPAM | missing link, exact Job scope, applied IDs, fresh refetch, convergence, no repeat |
| node link | GraphQL/PATCH/GraphQL, real-HTTP failures, truthful mutation evidence, no repeat |
| desired Jobs | preview zero-write, explicit apply, atomicity, confirmation, ownership preservation, repeat no-op |
| actual ingest | valid/stale/invalid/partial/repeat behavior plus real ORM constraints |
| SSH | real OpenSSH identity/port/store/option behavior without policy weakening |
| Ansible | real inventory parser, exact limit, forbidden override rejection, dry/apply separation |
| observation | version, identity, freshness, bounded managed-file evidence, supported ingest path |
| Braindump | user/AI prose distinction and zero prose-to-actuation path |
| compute | inert until explicitly superseded; no hidden provider action |
| evidence | private atomic writes, readable historical artifacts, partial logs/results preserved |
| isolation | repeatable named-fixture runs, no cross-test contamination or unintended external write; alternate order only for a named risk |
| documentation | one command matrix, admission rule, tier definitions, and current prerequisites |
| measurements | same before/after method, runtime/slowest/skip/flaky results, explained changes |

## Test admission and review rules

Every new test added after this roadmap must state, in its name, table row, docstring, or review
description:

1. the unique failure mode it catches;
2. its tier;
3. why an existing lower or higher layer would not catch that defect as clearly;
4. the side-effect or external boundary it replaces with a fixture, if any; and
5. the positive evidence that proves the intended path ran.

During review:

- request consolidation when variants differ only by input and expected row;
- reject snapshots of unrestricted internal structures;
- reject a mock that encodes unverified external behavior;
- retain a narrow reproducer for a real incident unless its unique assertion is visibly present
  in the replacement;
- require a new state-transition test when a new automatic reconciler is added;
- require exact scope and no-repeat assertions for every new mutating action;
- require a named consumer before freezing another output field; and
- require documentation updates when a test needs a new environment or prerequisite.

## Required searches

Phase plans must search active code, tests, fixtures, configuration, and current documentation for
at least:

```text
serve
dashboard
reconciliation_status
reconciliation_checked_at
DesiredHostQuickAdd
source_yaml
PreviewIntentSourceAnalysis
GenerateDesiredServices
service_repositories.yaml
fields = "__all__"
compatibility
deprecation
legacy
fallback
test_p4_
test_phase3_
test_vm_p3_
skip
xfail
monkeypatch
MagicMock
Mock
respx
subprocess
ssh-keyscan
ssh-keygen
ssh -G
ansible-inventory
ansible-playbook
transaction.atomic
```

Matches are not deletion instructions. Classify each as retained contract, external boundary,
negative absence proof, migration/history, candidate consolidation, or orphan.

Also search for tests reading arbitrary source text to assert symbol/literal presence. Keep such a
test only when no executable contract can prove the behavior and a current consumer genuinely
depends on that literal.

## Safety, evidence, and rollback

### Safety

- Ordinary tests do not emit secrets or private payloads and do not depend on the public internet.
- Local scratch tests use synthetic identities and named databases/fixtures; they may reuse
  persistent containers, databases, and networks.
- Production/external state is read-only unless a separate phase plan names an approved reversible
  fixture. The local stack documented in `.local/localenv_memo.md` is not production state.
- Strict SSH verification, exact target scope, and Ansible override rejection remain enabled.
- Raw SSH keys, tokens, private Braindump bodies, Alignment Review summaries, and ObjectChange
  payloads do not enter tracked fixtures or reports.
- Missing desired state never becomes a deletion fixture.
- Successful side effects remain recorded when a later test step fails.
- A cleanup failure fails the affected environment gate and is reported. If the exact scratch
  target is known, repair it and continue; stop only when cleanup could affect an unresolved,
  production, external, or irreversible target.

### Evidence

Store raw logs only when needed to diagnose a failure or substantiate a Tier A/environment
boundary. Normal focused runs need only command, result, and relevant revision. Private evidence
belongs under `.local/test-strategy/` with restrictive permissions. Tracked reports contain only
sanitized summaries, public schema facts, relevant test IDs/counts/timings, revisions, and
artifact digests.

Do not copy live prose or credentials into a golden file. Do not use raw command output as a
substitute for a concise phase report.

### Rollback

Most changes are test-only and roll back by restoring the prior test/doc revision. Do not keep
both old and new duplicate tests as a rollback mechanism.

If a behavior-preserving production seam is added for testability and a gate fails:

1. stop before combining more tests;
2. restore the prior production implementation or fix forward only within the already-approved
   contract;
3. rerun the original retained test and the new highest-practical-layer gate;
4. record whether any disposable or live side effect occurred; and
5. do not describe a unit-only pass as closure of an environment failure.

If a scratch fixture mutates unexpected but exactly identifiable scratch state, preserve the
useful evidence, repair that scope, and continue after the affected gate passes. Stop and follow
the owning rollback plan when the target is unresolved, production/external, difficult to reverse,
or outside the authorized scope.

## Definition of done

This initiative is `complete` only when:

- every active test and shared fixture has one primary risk tier and named contract;
- every deleted test maps to removed behavior, superseded compatibility, or a replacement that
  visibly retains its unique failure mode;
- removed features have no orphan tests, fixtures, dependencies, or current documentation;
- retained Tier A boundaries remain positively exercised;
- dnsmasq, IPAM, and every other supported automatic transition have real multi-round
  non-repetition proof;
- node-link real-HTTP fail-closed and post-mutation evidence behavior is proven;
- Import, Analyze, lifecycle/link, Braindump/review, and ingest mutations have exact authority,
  write, confirmation, rollback/partial-progress, and repeat evidence as applicable;
- OpenSSH, Ansible, Nautobot/Django, and the privileged helper are tested against their normative
  implementations at the smallest practical layer;
- deterministic Tier B variants are consolidated into readable tables;
- Tier C presentation is smoke-level except where mutation authority requires stronger proof;
- durable artifacts and current-consumer schemas remain readable without compatibility-only
  runtime writers;
- no required Tier A gate silently skips, calls the public internet, weakens policy, or leaks
  state/secrets/private prose;
- the documented command matrix runs from the documented checkout, reuses declared scratch state
  during iteration, and includes one clean reconstruction/final gate where required;
- before/after files, cases, lines, runtime, slowest tests, skips, and transition coverage are
  recorded with the same measurement method;
- every omitted or substituted framework/production/external proof is visible and prevents an unqualified
  `complete` status; and
- the final suite is smaller or simpler for explained reasons, not because an acceptance
  criterion was deleted.

A lower test count is not the outcome. The outcome is a suite in which each important failure has
one clear owner and each supported mutation is proven to run, be observed, preserve truthful
evidence, and not repeat.
