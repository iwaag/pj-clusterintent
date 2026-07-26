# Test Strategy Phase 0 Implementation Plan: Freeze Risks, Consumers, Layers, and Measurements

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: proposed; read-only audit, disposable-environment verification, and documentation-only
phase.

## 1. Goal

Phase 0 creates the evidence-backed test manifest that Phases 1–4 will use before any test is
deleted, combined, renamed, or moved.

The phase must answer:

1. What lasting contract and unique failure mode does every active test or shared fixture own?
2. Which risk tier and execution environment is the primary owner of that contract?
3. Which supported automatic transitions, explicit mutations, read-only operations, manual safe
   stops, and unsupported or inert paths already have truthful proof, and which have a visible
   gap?
4. Which artifact, event, and CLI-envelope fields have a named current or historical reader?
5. Can the unmodified baseline be reproduced without order dependence, leaked state, public
   network access, or hidden required skips?

The observable result is one reproducible inventory and transition manifest in which every active
test has exactly one primary tier, named contract, unique-defect disposition, and final
`keep`/`delete`/`replace`/`defer` recommendation.

Phase 0 does not refactor the suite. It freezes the evidence and decisions needed to do that
safely in later phases.

## 2. Required outputs

Phase 0 produces:

1. this implementation plan;
2. one private evidence directory under `.local/test-strategy/p0/<UTC timestamp>/`;
3. an exact repository, installed-package, migration, and environment manifest;
4. a static test-definition inventory and a runner-collected case inventory;
5. a test/fixture ownership manifest with tiers, contracts, boundaries, mocks, and dispositions;
6. an evidence-linked risk and operation-kind transition manifest;
7. a deleted-surface and historical-reference classification;
8. a shared-fixture and repeated-builder inventory based on semantic payload;
9. an external-behavior audit for OpenSSH, Ansible, Nautobot/Django, HTTP, and filesystem
   assumptions;
10. an explicit compatibility decision and current/historical consumer manifest for durable
    evidence and envelopes;
11. repeatable baseline measurements and normal/repeated/perturbed-order run results;
12. leak, skip, flake, and order-dependence findings; and
13. `devdocs/big/test_strategy/p0/report.md` with a final state of `complete`, `partially
    complete`, or `blocked`.

Only these tracked files may change during Phase 0:

- this plan; and
- `devdocs/big/test_strategy/p0/report.md`.

All collection scripts, raw logs, runner plugins, copied test IDs, HTTP method logs, container
manifests, and timing data remain private under `.local/test-strategy/p0/`. No production source,
test source, fixture, snapshot, dependency, lock file, component documentation, seed, generated
inventory, or submodule pointer may change.

If the audit contradicts the parent roadmap or the refactoring vision, stop and amend the
governing document explicitly in a separately reviewed change. Do not hide a changed contract in
the Phase 0 report.

## 3. Authority and safety boundary

### 3.1 Allowed actions

Phase 0 may:

- inspect tracked and ignored repository metadata needed to identify the configured local
  environment;
- read Git revisions, diffs, status, source, tests, documentation, configuration structure, and
  generated route or schema registries;
- inspect installed package metadata, process/container health, image identity, migration state,
  and read-only row counts;
- run every ordinary offline test suite;
- create private AST, collection, ordering, measurement, and classification helpers under the
  phase evidence directory;
- create an isolated Nautobot/PostgreSQL/Redis environment using synthetic credentials,
  identities, databases, networks, volumes, and a non-live host port;
- run tests that mutate only their isolated disposable database or temporary filesystem;
- run real OpenSSH and Ansible conformance discovery only against controller-local disposable
  fixtures;
- use GraphQL query documents and HTTP `GET`, `HEAD`, or `OPTIONS` against the live local
  Nautobot when a read-only fact cannot be obtained from installed metadata;
- record sanitized private evidence and the two tracked documents listed above; and
- remove only the exact disposable resources created by this phase.

GraphQL queries normally use HTTP `POST`; that transport is allowed only for a query document.
The query must not contain a mutation.

### 3.2 Prohibited actions

Phase 0 must not:

- edit, delete, combine, rename, regenerate, or re-record a test or fixture;
- change production code to make collection or tests easier;
- update a dependency or install a new tracked test plugin;
- run a live GraphQL mutation, REST mutation, Job, JobHook, or scheduled Job;
- run live `nctl reconcile --yes`, `nctl apply`, lifecycle or Braindump writes, SSH enrollment,
  Ansible playbooks, nodeutils collection, ingest, or a provider action;
- create, update, link, unlink, retire, or delete live desired or actual rows;
- edit desired YAML, compute/MAC seed data, `nctl.toml`, or a generated inventory;
- rebuild, restart, migrate, stop, or replace the live Nautobot web, worker, or scheduler;
- contact the public internet from a test or fixture;
- weaken strict SSH verification, target scoping, authorization, or Ansible override rejection;
- read or copy `.local/secrets`, authentication headers, private keys, raw public key blobs,
  Braindump bodies, Alignment Review summaries, or ObjectChange payloads into evidence; or
- push, rewrite history, or alter a submodule pointer.

The presence of a token file may be checked by metadata only when needed. Its contents must never
be opened or printed.

### 3.3 Stop conditions

Stop the affected gate, preserve evidence, and do not repair code during this phase when:

- a test or collection command mutates live state or contacts the public internet;
- the exact live/disposable target cannot be distinguished;
- a disposable compose file resolves a live database, Redis instance, volume, network, port, or
  token;
- cleanup would require a broad or unresolved deletion target;
- a test exposes a production defect;
- current VM Phase 3 work changes the frozen revision tuple while classification is in progress;
  or
- a required contract cannot be assigned without inventing user intent or changing supported
  behavior.

A production defect becomes a named Phase 0 gap and retained reproducer candidate. Its correction
requires a separate bounded plan.

## 4. Governing inputs and planning-time orientation

Before executing Step 0, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent test-strategy roadmap;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/remove_unused_surfaces/p5/report.md`;
- `devdocs/big/interface_contract/roadmap.md`;
- `devdocs/big/interface_contract/p4/report.md`;
- `devdocs/big/vm/roadmap.md`;
- the active VM Phase 3 plan and the latest applicable report under `devdocs/big/vm/p3/`;
- `nctl/docs/compatibility.md`;
- component `README.md` and `README_DEV.md` files relevant to their test commands; and
- current source, test configuration, and tracked tests in all five submodules.

Later reports take precedence over earlier planning snapshots. In particular:

- remove-unused-surfaces and interface-contract completion reports supersede their pre-deployment
  baselines;
- the interface-contract Phase 4 report leaves a real-HTTP fail-closed node-link reset gap;
- VM Phase 3's old pre-cutover handoff is superseded by the later matched deployment through
  nintent migrations `0015` and `0016`; and
- no compute desired-row seed or first realization is authorized by this phase.

Historical plans and reports are evidence, not active consumers. Do not rewrite them to remove
historical names or claims.

### 4.1 Planning-time repository snapshot

This snapshot was observed while this plan was authored on 2026-07-26. Phase execution must
recapture it:

| Repository | Planning-time revision | Planning-time state |
|---|---|---|
| superproject | `8b907aa9a47da948c05cd08e42e9471e86f66aad` | clean before this plan was added |
| `nctl` | `e813f6963afc17af74c48aae5660461d3f10498a` | clean |
| `nintent` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | clean |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

The parent roadmap's counts, timings, installed revisions, and container health are orientation
only. Do not copy them into the final report as fresh evidence.

### 4.2 Collision and sequencing rule

`remove_unused_surfaces` and `interface_contract` are complete prerequisites. This initiative must
finish before nctl modularization.

VM Phase 3 may continue to refine its later compute seed/cutover plan, but it must not introduce
compute actuation during Phase 0. At the start and end of every long-running collection gate,
recapture the six-repository revision tuple. If a component revision moves:

1. finish or terminate the current command safely;
2. identify the changed files and whether they affect tests, schemas, transitions, or consumers;
3. mark all derived inventories stale;
4. restart collection against one new frozen tuple; and
5. record the abandoned tuple without mixing its measurements into the final baseline.

## 5. Evidence layout and schemas

Create the evidence root with mode `0700` and default file mode `0600`. Use a UTC timestamp in the
directory name. At minimum, retain:

```text
.local/test-strategy/p0/<timestamp>/
  README.txt
  commands.jsonl
  revisions-start.tsv
  revisions-end.tsv
  environment.tsv
  installed-components.tsv
  migrations.txt
  tracked-test-files.tsv
  static-tests.tsv
  collected-cases.tsv
  test-ownership.tsv
  fixture-ownership.tsv
  transition-manifest.tsv
  risk-register.tsv
  reference-classification.tsv
  external-boundaries.tsv
  compatibility-consumers.tsv
  compatibility-decision.md
  measurements.tsv
  runtime-summary.tsv
  slowest-tests.tsv
  skips-xfails.tsv
  run-results.tsv
  leak-check-before.tsv
  leak-check-after.tsv
  findings.tsv
  logs/
```

`commands.jsonl` records timestamp, working directory, sanitized argument vector, exit code,
duration, environment ID, and output-file digest. It must not record inherited environment
values, tokens, headers, test payload bodies, or shell history.

### 5.1 Test ownership schema

`test-ownership.tsv` has one row per static test definition or parametrized table owner:

| Column | Meaning |
|---|---|
| `test_id` | stable source definition ID |
| `component` | `nctl`, `nintent`, `nauto`, `nodeutils`, or `ansible_agdev` |
| `file`, `line` | tracked source location |
| `primary_environment` | lowest environment containing the normative owner |
| `tier` | exactly one of `A`, `B`, or `C` |
| `contract_id` | stable risk/domain contract name |
| `operation_kind` | transition vocabulary from Section 6.2 |
| `unique_defect` | the distinct failure the test detects |
| `positive_evidence` | non-empty path proving the intended behavior ran |
| `side_effect_boundary` | real boundary or exact substituted fixture |
| `mocks` | mocked calls or `none` |
| `fixtures` | shared/local fixture IDs |
| `consumers` | named current reader/operator |
| `disposition` | `keep`, `delete`, `replace`, or `defer` |
| `replacement_owner` | required for `replace` |
| `reason` | evidence-backed disposition rationale |

`collected-cases.tsv` separately records runner, environment, collected node ID, parameter ID,
skip/xfail state, and owning `test_id`. This prevents a parametrized test from being counted as
many independent proofs of one failure mode while preserving exact collected-case measurements.

### 5.2 Fixture ownership schema

`fixture-ownership.tsv` has one row per shared fixture, factory, builder, conformance payload,
golden file, snapshot, fake service, or test-only helper. Record:

- definition and consumers;
- semantic payload and trust boundary;
- scope and cleanup behavior;
- mutability and deterministic identity/time behavior;
- external behavior encoded by the fixture;
- whether another fixture is textually similar;
- whether the similarity is semantically mergeable;
- final disposition and replacement owner; and
- orphan status.

Similar dictionaries are not merge candidates when they model different authority, trust,
freshness, transaction, or failure boundaries.

### 5.3 Manifest completeness checks

Private validation scripts must fail unless:

- every tracked active test file is represented;
- every collected case maps to exactly one static owner;
- every static owner is collected in at least one declared environment or has a named collection
  gap;
- every owner has one tier, contract, operation kind, unique defect, and disposition;
- every `replace` row names its replacement owner and retained assertion;
- every shared fixture has at least one consumer or is classified as orphan;
- every Tier A row names positive evidence and a highest-practical-layer owner or visible gap;
- no one test is counted as several primary proofs; and
- every roadmap risk row maps to a manifest entry.

## 6. Audit vocabulary and decision rules

### 6.1 Risk tiers

Use the parent roadmap definitions without creating intermediate tiers:

- `A`: mutation, trust, authorization, destructive boundary, exact scope, freshness, partial
  progress, or durable evidence;
- `B`: deterministic parsing, normalization, validation, comparison, selection, rendering, or
  classification; and
- `C`: retained text, read-only UI, templates, and presentation.

Approval, no-mutation, redaction, and permission assertions remain Tier A even when exercised
through a CLI or UI adapter.

### 6.2 Operation kinds

Every retained contract receives exactly one primary operation kind:

| Kind | Required proof |
|---|---|
| `automatic_transition` | real classify/plan/action/observe/fresh-drift sequence and no repeat |
| `explicit_mutation` | authority or dry pre-read, exact write, canonical refetch, truthful evidence, and idempotent repeat where promised |
| `read_only_deterministic` | stable domain output and named consumer; no apply loop |
| `manual_safe_stop` | fail-closed evidence and resumable state; no fabricated convergence |
| `unsupported_inert` | positive proof that no action, writer, or provider dispatch is emitted |

### 6.3 Dispositions

- `keep`: owns a reachable unique contract at the appropriate layer.
- `delete`: only protects removed behavior, an obsolete consumer, an implementation detail, or an
  impossible documented tier.
- `replace`: its unique assertion moves visibly to one stronger or more legible owner.
- `defer`: a future contract is explicitly out of scope and no placeholder test is added.

Age, file size, runtime, historical filename, mock count, or a line-ratio measurement never
authorizes deletion by itself.

### 6.4 Reference classifications

Every required-search match must be classified as exactly one of:

- `retained_contract`;
- `external_boundary`;
- `negative_absence_proof`;
- `migration_history`;
- `historical_document`;
- `candidate_consolidation`; or
- `orphan`.

A historical report is not an active consumer. A negative absence proof is retained only when it
has one named current surface or security boundary to keep absent.

## 7. Implementation procedure

### Step 0 — Freeze the tuple and create private evidence

1. Re-read all governing inputs in Section 4.
2. Confirm the superproject and five submodules have no unexpected dirty or untracked changes.
   Preserve user changes; do not clean or reset them.
3. Record exact HEAD, branch, upstream relation, submodule pointer, and porcelain status for all
   six repositories.
4. Record OS, architecture, Python, uv, pytest, unittest/Django, Git, Docker, OpenSSH, and Ansible
   versions used by the gates.
5. Create the evidence tree and initialize `commands.jsonl`.
6. Snapshot existing processes and exact names of relevant live containers, disposable
   containers, volumes, networks, temporary trust stores, generated inventories, test databases,
   and phase-owned files for later leak comparison.
7. Record a digest of every current tracked test file so Phase 0 can prove the suite stayed
   unmodified.

Gate: one clean, immutable revision tuple and one private evidence root are recorded. Unexpected
user changes are reported and worked around; they are never discarded.

### Step 1 — Reconstruct current installed and migration state

Use read-only inspection to record:

1. live Nautobot version and the health/image identity of web, worker, and scheduler;
2. installed nintent and nauto package versions and VCS commits in all three processes;
3. applied nintent migrations, including whether `0015` and `0016` are applied;
4. read-only counts for DesiredComputePlatform and DesiredComputeInstance;
5. the current checked-in VM seed proposal and whether the Phase 3 seed/cutover state has moved
   since the latest authoritative reports;
6. current Job registration and migration/runtime test entry points relevant to the inventory;
   and
7. any mixed-process or repository/deployment mismatch.

Do not record live object prose, token values, ObjectChange bodies, desired YAML contents not
needed for schema identity, or actual host observations.

Gate: repository and installed tuples are distinguishable, migration state is explicit, and the
report can state truthfully whether compute remains unseeded and inert.

### Step 2 — Collect every suite in its owning environment

Build inventories from Git-tracked files, AST discovery, and runner collection:

1. enumerate tracked test modules and shared fixture/helper files in each submodule;
2. parse test functions, methods, classes, parametrization decorators, unittest skips, pytest
   marks, fixtures, factories, monkeypatches, mocks, subprocess calls, and test-only builders;
3. collect pytest node IDs without executing tests;
4. load unittest suites with a private discovery helper that prints fully qualified IDs without
   running them;
5. collect both nintent's fast Django-free suite and its complete disposable Nautobot App suite;
6. distinguish nintent cases intentionally unavailable to the fast environment from tests that
   silently skip in their required environment;
7. collect nauto's current fast suite separately from any real-Nautobot conformance proof;
8. record the nodeutils privileged-helper and ansible_agdev helper environments separately from
   pure unit tests; and
9. reconcile static definitions with all collected IDs.

The ordinary starting commands are:

```bash
cd nctl && uv run pytest --collect-only -q
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest --collect-only -q
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

The private unittest collector must load the same discovery roots without executing test methods.
The disposable Nautobot collector must use the installed App's real test command and exact
Nautobot version rather than treating the local 13 skips as complete coverage.

Gate: every tracked test definition and collected case is reconciled to an owning environment.
Collection failures and environment-only gaps remain visible.

### Step 3 — Assign tier, contract, boundary, and unique defect

Review every test owner and populate `test-ownership.tsv`:

1. identify the production or presentation contract it protects;
2. name the unique defect it catches;
3. identify the normative behavior owner and primary environment;
4. record real side effects and the exact mocked boundary;
5. record the positive assertion showing the intended path ran;
6. assign one tier and operation kind;
7. name the current consumer;
8. identify overlap with adjacent-layer tests; and
9. assign a preliminary disposition.

Use the roadmap ownership map as the default:

- nintent owns desired model/YAML rules, Import/Analyze transaction behavior, and read-only UI;
- nauto owns actual-ledger ingest policy;
- nodeutils owns observation schema and privileged collection output;
- nctl owns canonical reads, drift, planning, exact scope, orchestration, evidence, and
  non-repetition;
- nctl plus disposable OpenSSH owns trust semantics;
- nctl/ansible_agdev plus real Ansible owns inventory and actuation-boundary semantics; and
- durable real files own artifact/event/`ops` round trips.

Do not assign an adapter mock as the primary owner when the same behavior is normatively defined
by Django, OpenSSH, Ansible, the filesystem, or the real planner/executor.

Gate: every active test has exactly one primary owner and preliminary disposition.

### Step 4 — Reproduce measurements

Using private scripts committed only to phase evidence, record per component:

- tracked test files;
- static test definitions;
- runner-collected cases;
- tracked test lines and non-test Python lines;
- source-to-test line ratio;
- runtime and slowest tests;
- skip and xfail counts with reasons;
- fixture, factory, mock, parametrization, subprocess, and repeated-helper concentration;
- public-network and environment dependency signals; and
- automatic transitions with real planner/executor or environment-backed proof.

Line counts must use Git-tracked Python files and one frozen classification rule. Record the exact
file lists and command digest, not only totals. Test lines include complete tracked test modules;
non-test lines exclude those same files. Do not fold Ansible YAML or shell into the Python ratio.

Static definition counts must use Python AST, not a text search for `def test_`. Collected-case
counts come from the runner and remain separate.

Gate: all measurements are reproducible from retained commands and exact file lists.

### Step 5 — Classify removed-surface and historical references

Search active source, tests, fixtures, configuration, and current documentation for every term in
the parent roadmap's required-search list:

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

Also search for tests that read arbitrary production source text merely to assert a symbol or
literal. Record repository, file, line, active/historical context, current consumer, and one
reference classification from Section 6.4.

Do not treat a search match as deletion permission. Historical migrations and reports stay
historical. Active removed-route and removed-field assertions must be reduced later to one named
absence owner, not deleted wholesale during Phase 0.

Gate: no active match is unclassified.

### Step 6 — Build the risk and transition manifest

Expand every row in the roadmap's required risk matrix into evidence-linked contracts. For each
operation record:

- operation kind;
- authority and canonical owner;
- exact initial state;
- intended action or denial;
- exact target scope;
- observation/refetch requirement;
- durable evidence requirement;
- repeat behavior;
- current primary test ID and environment;
- unique variants retained at focused layers;
- mocked or substituted boundaries;
- current status (`proven`, `partial`, `gap`, `manual`, or `inert`);
- Phase 1/2/3 disposition; and
- gap-closing owner.

At minimum, represent independently:

- SSH identity, port, offered-key, malformed-store, and option-precedence boundaries;
- credential source, redaction, HTTP denial, and Job authorization;
- cluster/host exact scope;
- reconcile plan/apply separation and forced refresh;
- post-mutation confirmation failure and partial IPAM progress;
- nodeutils-to-nauto-to-nctl observation identity/freshness/schema/path/digest;
- dnsmasq and non-DHCP IPAM multi-round convergence;
- DesiredNode actual linking, including fail-closed reset;
- Import and Analyze preview/apply/refetch/repeat;
- nodeutils and Proxmox ingest validity/staleness/partial failure/no-op;
- missing-desired no-delete behavior;
- compute inertness and desired-MAC blocked/recovery behavior;
- Braindump/Alignment Review authority and prose non-executability;
- deterministic parsing/rendering/classification;
- transport decoding;
- CLI/UI presentation and approval;
- durable artifact/event/`ops` reads, restarts, corruption, and partial logs; and
- manual safe stops and unsupported actions.

An empty action, preflight, request log, observation, denial, or refetch is `partial` or `gap`, not
`proven`.

Gate: every supported operation has one named proof or visible gap, and no transition is claimed
from several independent lower-layer tests.

### Step 7 — Inventory fixtures and repeated semantic payloads

For every shared and locally repeated fixture:

1. record its consumers and semantic purpose;
2. distinguish desired, actual, observed, transport, trust, transaction, and presentation data;
3. identify duplicated constants, builders, UUIDs, timestamps, response envelopes, and fake
   services;
4. record whether time and ordering are frozen;
5. record setup and teardown scope;
6. identify accidental public-network, host filesystem, process, database, or environment
   dependencies;
7. identify orphan helpers and test-only dependencies; and
8. recommend keep/delete/replace without changing the fixture.

Repeated payloads are mergeable only when one canonical fixture preserves the same authority,
schema version, ownership, and failure boundary for every consumer.

Gate: every shared fixture has a named contract and disposition; every proposed merge explains
why the trust boundary is the same.

### Step 8 — Audit mocked external behavior

Build `external-boundaries.tsv` with one row per externally defined assumption:

| Boundary | Required comparison |
|---|---|
| OpenSSH | `ssh-keyscan`, `ssh-keygen`, `ssh -G`, stable alias, non-default port, malformed store, effective option precedence |
| Ansible | real inventory parsing, variable precedence, forbidden override detection, exact `--limit`, check/apply separation |
| Nautobot/Django | GraphQL/REST/Job discovery, HTTP status, permissions, transactions, constraints, ORM field behavior |
| HTTP | authentication/authorization errors, malformed payloads, timeouts, and post-write confirmation |
| Filesystem | atomic private writes, path canonicalization, permissions, corruption, restart reads, and cleanup |
| Privileged helper | current real allowlisted Proxmox helper boundary |

For each assumption record the current mocked test, normative implementation/version, prior
historical proof, currently maintained real test, smallest proposed real conformance case, and
Phase 3 gap owner.

Historical prose that a fixture once passed does not count as maintained proof. Run only existing
safe local/disposable real-tool gates in Phase 0; do not add them to tracked tests yet.

Gate: every normative external assumption either has a maintained real proof or a precisely
bounded Phase 3 gap.

### Step 9 — Resolve compatibility against named consumers

Audit `nctl/docs/compatibility.md`, `EventRecord`, event vocabulary, envelope models, snapshot
tests, artifact writers, `nctl ops` readers, CLI renderers, current agent/operator documentation,
and representative historical artifacts.

`compatibility-consumers.tsv` must record:

- schema/version and field or event name;
- writer;
- current reader;
- durable historical reader requirement;
- current operator/agent consumer;
- persistence location and privacy boundary;
- existing snapshot/round-trip/corruption proof;
- decision (`retain`, `remove_in_matched_rollout`, `small_historical_reader`,
  `offline_migration`, or `unresolved`); and
- evidence for that decision.

The frozen policy for later phases is:

1. preserve exact contracts required by named current consumers;
2. preserve readable existing evidence through the smallest reader or an explicit offline
   migration when historical inspection is required;
3. use matched-version changes rather than parallel obsolete runtime writers;
4. remove fields whose only consumer was removed;
5. do not preserve broad snapshots merely as a floor forever; and
6. never silently make existing operation evidence unreadable.

The report must explicitly resolve the current document's deprecation-window/dual-version
language against the repository-wide coordinated breaking-change policy. Updating
`nctl/docs/compatibility.md` and its tests is Phase 1 work, not Phase 0 work.

Gate: every frozen field/event has a named consumer or an explicit later removal decision, and
the policy conflict has one approved final interpretation.

### Step 10 — Run the unmodified baseline repeatedly and out of order

Run the exact ordinary suites from their documented component directories:

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

For each suite:

1. run the normal order twice from an equivalent clean process environment;
2. run once in deterministic reverse collection order;
3. compare collected IDs, pass/fail/skip/xfail results, warnings, runtime, slowest cases, and
   created state;
4. capture failures individually without allowing one component to hide another;
5. compare phase-owned filesystem, process, database, container, network, volume, and generated
   artifact state before and after; and
6. recapture repository digests and the revision tuple.

Do not add `pytest-randomly` or another dependency. Use a private pytest collection hook under the
evidence directory that reverses `items` without changing their IDs. Use a private unittest
runner that loads the same discovery suite, flattens it, reverses the cases, and preserves normal
setup/teardown semantics. For the real Nautobot App suite, use the framework's supported reverse
ordering option if available and record the exact command; otherwise record `unsupported` rather
than silently substituting a different environment.

The complete disposable Nautobot App gate must run against an isolated database/process and the
exact installed candidate tuple. Run it twice normally and once reversed if supported. Include
the full App suite, not only files that pass locally. A required runtime test that skips in this
environment is a failure of the gate unless its optional environment is documented.

Existing local OpenSSH, Ansible, and privileged-helper gates may be run only against disposable
targets and must declare prerequisites. Missing maintained gates become Phase 3 gaps; they are
not replaced with live cluster activity.

Any failed baseline is preserved as a finding. Do not repair it in Phase 0 and do not relabel a
narrower passing suite as the missing proof.

Gate: the full unmodified baseline has two normal results, one supported perturbed-order result,
and explicit leak/flake/skip findings for every owning environment.

### Step 11 — Reconcile manifests and write the final report

1. Rerun all manifest completeness validations.
2. Reconcile static counts, collected counts, runtime results, skips, fixture consumers, required
   searches, risk rows, and compatibility fields.
3. Verify tracked test-file digests are unchanged.
4. Verify production/test Git trees and submodule pointers are unchanged.
5. Tear down exact disposable resources and prove them absent while the live stack remains
   unchanged.
6. Compare starting and ending process/filesystem/database snapshots and classify every
   difference.
7. Write one sanitized `report.md`; link evidence by relative private path descriptions without
   copying secrets or raw live prose.
8. Assign the final status using Section 10.

Gate: all exit criteria are either satisfied or named as blockers; no omitted or substituted
check is hidden.

## 8. Verification matrix

| Area | Phase 0 proof |
|---|---|
| Revision | exact clean start/end tuple and unchanged tracked test digests |
| Installed state | per-process nintent/nauto revisions, migrations, and VM seed/cutover status |
| Static inventory | every tracked test and shared fixture represented |
| Runtime collection | every collected case maps to one static owner and environment |
| Tier ownership | exactly one tier, contract, operation kind, unique defect, and disposition per owner |
| Tier A | highest-practical proof linked or visible gap; positive path evidence is non-empty |
| Tier B | candidate truth tables and duplicate branch tests identified without editing them |
| Tier C | named presentation consumer and candidate smoke owner identified |
| Removed behavior | every current/historical match classified; orphan candidates explicit |
| Transitions | automatic/mutation/read-only/manual/inert manifest covers every roadmap risk |
| Fixtures | semantic/trust boundaries and consumers recorded; orphans visible |
| External tools | mocks compared with normative versions; smallest real gaps named |
| Compatibility | every field/event has a consumer decision; policy conflict explicit |
| Measurements | repeatable file/case/line/runtime/ratio/concentration method and raw file lists |
| Determinism | two normal runs and one supported reverse-order run per owning environment |
| Isolation | no public network, live writes, leaked disposable state, or hidden required skip |
| Reporting | one sanitized final report with exact deviations and status |

## 9. Expected Phase 0 findings and later-phase handoff

Phase 0 is expected to produce, but must not prejudge, these later work queues:

- Phase 1: orphan/superseded surface tests, historical absence duplication, obsolete compatibility
  floors, and their last test-only helpers or dependencies;
- Phase 2: repeated deterministic tables, transport payloads, CLI success matrices, UI rendering,
  and historical filenames whose lasting contract needs a risk-owned home;
- Phase 3: real-HTTP node-link reset, small real Nautobot ORM/transaction proofs, maintained
  OpenSSH and Ansible conformance, and cross-component observation schema proof; and
- Phase 4: repository-wide command documentation, final measurement reruns, teardown audit, and
  the final evidence-linked test strategy.

These are classifications, not authorization to edit future-phase files.

## 10. Reporting and completion states

The final report must contain:

- execution window and private evidence root;
- exact starting and ending repository/installed tuples;
- environment and migration state;
- inventory totals by component, tier, operation kind, environment, and disposition;
- the complete transition status summary with named proofs and gaps;
- fixture and mock concentration findings;
- removed/historical reference dispositions;
- the compatibility decision and named consumers;
- two normal and one perturbed-order result per environment;
- runtimes, slowest tests, skips, xfails, flakes, leaks, and public-network findings;
- proposed Phase 1/2/3 work queues;
- every failure, omission, substitution, deviation, and concurrent revision change; and
- proof that no test or production code changed.

Use these states:

- `complete`: every active test/fixture is classified, every roadmap risk has proof or a visible
  gap, compatibility is resolved, measurements and repeated runs are reproducible, disposable
  cleanup is proven, and no test or production code changed;
- `partially complete`: the inventory is useful but one or more declared environment,
  compatibility, transition, or repeat-run checks remain incomplete; or
- `blocked`: the exact tuple cannot be frozen, safe environment ownership cannot be established,
  or a required decision cannot be made without new authority.

A failing or missing Tier A proof does not automatically prevent Phase 0 from being `complete`
when Phase 0 has truthfully identified and assigned that gap to Phase 3. An unclassified Tier A
gap, missing inventory coverage, unresolved compatibility consumer, hidden required skip, mixed
revision baseline, or unverified cleanup does prevent `complete`.

## 11. Exit criteria

Phase 0 is `complete` only when:

- every active test and shared fixture has one tier, named contract, environment, unique defect,
  and disposition;
- every collected case maps to exactly one owner;
- every supported operation has one named current proof or visible gap;
- every empty or substituted path is labeled partial/gap rather than pass;
- every removed-surface and historical-name reference is classified;
- every fixture merge candidate is justified by semantic and trust equivalence;
- external-tool mocks have a normative conformance owner or bounded gap;
- artifact, event, envelope, and historical-reader consumers are frozen under one explicit
  compatibility decision;
- exact file/case/line/runtime/ratio/slowest/skip measurements are reproducible;
- all ordinary and environment-owning baselines have two normal results and one supported
  perturbed-order result;
- flakes, order dependencies, public-network dependencies, and leaked state are explicit;
- disposable resources are removed exactly and live state remains unmodified;
- all tracked test and production files retain their starting digests;
- the final revision tuple is consistent; and
- the report uses precise completion language without converting a narrower test into a missing
  environment proof.

The success criterion is not a lower test count. It is a frozen, reviewable map showing which
single test owner protects each important failure and which later change may simplify the suite
without weakening authority, evidence, scope, freshness, or non-repetition.
