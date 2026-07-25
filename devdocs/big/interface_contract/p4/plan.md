# Interface Contract Phase 4 Implementation Plan: Coordinated Data Transition and Deployment

Parent: [roadmap.md](../roadmap.md) — Phase 4.

Predecessors:

- [Phase 0 final report](../p0/report.md) — live ownership, the retained interface matrix, and
  the desired-state disposition ledger were frozen without mutation.
- [Phase 1 final report](../p1/report.md) — the strict nine-root YAML contract and dry-plan/apply
  Jobs were implemented but have not been deployed or applied to live state.
- [Phase 2 final report](../p2/report.md) — REST contraction and canonical GraphQL confirmation
  reads were implemented but remain undeployed.
- [Phase 3 final report](../p3/report.md) — the UI contraction source changes exist, but the
  planning-time audit in Section 2 of this plan found that Phase 3's runtime and cross-component
  completion claims are not reproducible and that its current runtime suite fails. Phase 4 must
  repair and re-prove that work before any live maintenance or data mutation.

Status: proposed. This plan authorizes implementation of the named Phase 3 follow-ups and
preparation of deployment artifacts. It does not itself authorize a live Job apply, retained REST
mutation probe, service rebuild/restart, or database restore. Those actions require the explicit
approvals and gates below.

## 1. Goal and required transition

Deploy one matched, minimal read/write contract without losing confirmed desired state, realized
links, actual-ledger evidence, JobHook state, operation evidence, or the separation between user
Braindump prose and AI Alignment Review prose.

The Phase 4 transition is:

```text
before Phase 4
  live Nautobot
    = nintent c343c5a56047b0df9ad901dd4459863ef1954053
    + migrations through 0016
    + pre-contraction REST and editable UI
    + pre-Phase-1 Import/Analyze behavior
  source control
    = Phase 1 YAML/Job contraction
    + Phase 2 REST/GraphQL contraction
    + Phase 3 UI contraction
  verification
    = local Django-free nintent suite passes with 10 runtime skips
    + nctl suite passes
    + Phase 3 disposable runtime suite currently fails
    + no reproducible Phase 3 HTTP evidence
  deployment input
    = Dockerfile installs mutable GitHub main
    + canonical YAML has no stable path present in every Nautobot process

after Phase 4
  source and tests
    = Phase 3 runtime defects repaired
    + full disposable UI/API/GraphQL/HTTP contract re-proved
  deployment artifact
    = exact nintent and nauto commits pinned and verifiable
    + identical image digest used by web, worker, and scheduler
    + canonical YAML available read-only at one explicit path in every required process
  live interface
    = one joined GraphQL domain-read contract
    + only nodes, Braindumps, and Alignment Reviews as narrow REST mutation collections
    + exactly 22 nintent human list/detail routes, all read-only
    + strict YAML Import and Analyze Jobs dry by default
    + no duplicate nauto desired writer or candidate generator
  live data
    = reviewed YAML preview
    + separately approved apply
    + GraphQL refetch
    + repeat apply with no repeated change
    + preserved desired identities, prose counts, realized links, provenance, actual ledger,
      JobHooks, and operation evidence
  VM handoff
    = VM Phase 3 Steps 9–12 use the deployed YAML Import contract
    + compute roots remain empty until their separate reviewed seed is approved
```

The strongest acceptance evidence is a traceable sequence:

```text
repair and disposable proof
  -> exact revisions and reproducible image
  -> maintenance freeze
  -> verified database/media backup
  -> matched code deployment
  -> official live preview
  -> separate apply approval
  -> apply/refetch/repeat
  -> retained/removed interface smoke
  -> resume and VM handoff
```

No step may reinterpret an empty plan, an unexercised writer, or a green Django-free suite as proof
of a runtime contract.

## 2. Phase 3 audit and mandatory follow-up

This audit was performed while authoring this plan on 2026-07-26. It inspected current source,
tests, Git history, private evidence, the running deployment, and a fresh isolated Nautobot 3.1.3
test run using the exact checked-out nintent source.

### 2.1 Positively confirmed Phase 3 implementation

The following source-level transition is present:

- `nintent/nautobot_intent_catalog/urls.py` declares exactly 22 list/detail routes.
- `views.py` retains eleven `ObjectListView` and eleven `ObjectView` classes and no nintent
  `ObjectEditView`, `ObjectDeleteView`, or `FormView`.
- `forms.py`, Quick Host Add's operation, Quick Host Add templates, and the Source YAML template
  are absent.
- active tables contain no `ButtonsColumn`, `ToggleColumn`, or `TABLE_ACTION_BUTTONS`.
- navigation links only to the eleven retained list pages.
- the custom DesiredNode and Braindump templates contain no retained mutation control.
- the checked-out nintent local suite passes 223 tests with 10 Nautobot-runtime skips.
- the checked-out nctl suite passes all 954 tests.
- all submodule worktrees were clean before this plan was added.

These facts show that the core UI deletion was implemented. They do not satisfy Phase 3's runtime,
HTTP, documentation, and evidence gates.

### 2.2 Reproduced Phase 3 defects and proof gaps

| Required Phase 3 claim | Planning-time finding | Phase 4 disposition |
|---|---|---|
| Full disposable Nautobot runtime suite passes | A fresh isolated run of `test_ui_contract`, `test_braindump`, and `test_api_contract` found 47 tests and ended with **9 failures and 6 errors** | Repair in Step 1 and rerun the complete App suite in Step 2 |
| Retained UI POSTs are tested with normal view authority | `UINonMutationRuntimeTests` grants only DesiredNode and DesiredService view permissions, then posts to all eleven lists; nine cases return 403 before method behavior is exercised | Grant the matching permission per model, assert the expected unavailable method response, and compare before/after row fingerprints |
| Removed Braindump/review UI is absent | Six `BrainDumpViewTests` still reverse and exercise deleted Braindump add/edit/delete and Alignment Review add/edit/delete routes | Replace them with absence, literal-404, non-mutation, and read-only panel tests; keep REST CRUD tests |
| All retained lists/details render | The new Phase 3 suite reverses route names but does not create and render all eleven list/detail fixture pairs | Add a table-driven runtime fixture/render matrix |
| All former literal UI paths are unavailable | Route reversal is covered, but the retained source does not contain the claimed complete literal-path 404 matrix | Add literal list plus representative/detail/alternate-path checks for every removed family |
| Retained pages cannot mutate | The current test checks status only for list POSTs and does not snapshot all row fields/counts or test details | Add full list/detail method and zero-write proof |
| Complete Phase 2 REST method/field matrix | `test_api_contract.py` has selected route and method checks, not the complete frozen list/detail/method/response/writable/zero-write matrix promised by Phase 3 | Implement the full table-driven runtime matrix |
| IntentSource GraphQL roots fail schema validation | Registry membership is checked, but singular/plural invalid schema queries are not executed | Execute the negative queries and positive retained-root queries |
| Missing node-link fail-closed boundaries were added | No Phase 3 nctl test/code commit exists; Phase 3 changed nctl documentation only | Add the missing ledger/executor cases from the Phase 3 plan and preserve post-PATCH evidence |
| Real planner/executor/API HTTP transition and direct writers were proved | No reusable harness or captured HTTP result exists in source or private evidence | Build and execute a reproducible isolated HTTP harness in Step 2 |
| Phase 3 private evidence is reproducible | `.local/interface-contract/p3/20260726_004827/` contains only `environment_snapshot.txt`; the reported runtime and HTTP evidence is absent | Record fresh sanitized evidence; do not invent the missing historical artifacts |
| Current documentation contains no removed UI recipe | `nctl/docs/register-a-new-pc.md` has a supersession note but its operative Sections 1–3 still instruct `sources/add/` and Quick Host Add; `nintent/README_DEV.md` still gives active `ButtonsColumn` guidance | Rewrite the current recipe and correct active developer guidance |
| Final source tuple is exact | Phase 3 reports name nintent `271fba1` as final, while the superproject currently points to later nintent `5881a6f`; the report does not give an exact final superproject SHA | Freeze the actual repaired tuple in Steps 3 and 10 |

The isolated audit used only the `nic-p1-disposable` project, a fresh PostgreSQL volume, a fresh
Redis volume, and the checked-out local nintent source. It did not reach the live database, Redis,
media volume, API, or port 8000. The exact disposable containers, network, and volumes were removed
after the failed result was recorded.

### 2.3 Phase 3 closure gate

No live maintenance window may begin until all of the following are true:

1. the obsolete positive UI mutation tests are removed or converted to final-contract tests;
2. the complete UI, REST, and GraphQL runtime matrices pass in Nautobot 3.1.3;
3. the real isolated HTTP node-link transition, fresh non-repetition, lifecycle writer, and
   Braindump/review writers pass through real GraphQL and REST;
4. all missing nctl fail-closed cases pass;
5. active documentation no longer gives an operative removed-UI instruction;
6. fresh evidence files contain the commands, revisions, test summaries, HTTP call classification,
   and teardown proof; and
7. the Phase 4 report records that Phase 3's prior runtime/HTTP assertions were superseded by this
   fresh proof.

Do not rewrite old Phase 3 results as though they were originally executed. Add a short dated
correction/supersession note to the Phase 3 final report and relevant Step 8–10 reports, then keep
their original text as historical evidence.

## 3. Authority, prerequisites, and planning-time baseline

### 3.1 Governing inputs

Before implementation, re-read:

- root `README.md` and `README_DEV.md`;
- `.local/localenv_memo.md`;
- the parent interface-contract roadmap;
- all Phase 0–3 plans and final reports, with Section 2's qualification;
- `devdocs/vision/refactor/vision.md`;
- the active Braindump, core-reconcile, and VM roadmaps;
- `devdocs/big/vm/p3/plan.md`, especially its interface-contract supersession note and Steps 9–12;
- current nintent, nctl, and nauto READMEs and active recipes;
- nintent UI/API/GraphQL/Job tests and nctl writer/reconcile tests;
- `devenv/nautobot/Dockerfile`, `docker-compose.yml`, and `nautobot_config.py`; and
- every active match from Section 10.

The parent roadmap's final interface matrix and ownership table remain authoritative.

### 3.2 Planning-time source and live snapshot

Observed on 2026-07-26:

| Target | Revision/state |
|---|---|
| superproject | `6e94147c34c4ad1b0f3bfdaeca9b4e176b7bf6cc`, clean before this plan |
| nintent | `5881a6f85bae07a5d2a48aaa94b067e0bcc197e5`, clean, equal to both checked remotes' `main` at audit time |
| nctl | `bafe7d2b9a9a5d704087e7c2edf96226d349ac8f`, clean, equal to `origin/main` |
| nauto | `2635e648469d6e6bad87af113f7427b878b0a387`, clean, equal to `origin/main` |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c`, unchanged/out of scope |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162`, unchanged/out of scope |
| live Nautobot | 3.1.3; web, worker, and scheduler healthy |
| installed nintent | package 0.9.0 from Git commit `c343c5a56047b0df9ad901dd4459863ef1954053` |
| live nintent migrations | applied through `0016_remove_reconciliation_dashboard_surfaces` |

This is orientation, not the deployment tuple. Step 0 must recapture all revisions, upstream
availability, dirty state, installed commits, image IDs, migration state, running Jobs, and live
aggregate fingerprints.

### 3.3 Deployment configuration blockers found during planning

The current Dockerfile installs:

```text
git+https://github.com/iwaag/nprojects.git
```

without an exact commit. A rebuild from mutable `main` is not a reproducible matched deployment.
The `nprojects.git` and `nintent.git` `main` refs happened to resolve to the same commit during this
audit, but equality at one instant is not a pin.

The final Import Job also needs one stable canonical YAML path. Current `PLUGINS_CONFIG` is empty,
and the default fallback is `<process cwd>/nauto/seed/intent_sources.yaml`, which does not exist in
the current containers. A copy of `intent_sources.yaml` was found only in the web container's
Nautobot Git-repository checkout; the worker and scheduler did not have the same path. Because Jobs
execute on the worker, that state blocks a reliable live preview/apply.

Before deployment, the image/configuration must therefore:

- require an exact nintent Git SHA at build time;
- include or otherwise expose the exact nauto commit's canonical YAML at one explicit read-only
  path available to both web and worker (and scheduler for parity);
- set `NAUTOBOT_INTENT_SOURCES_FILE` or the equivalent App setting to that path in every relevant
  service;
- fail the build/startup if either revision or the YAML file is absent;
- label or otherwise expose both embedded revision SHAs; and
- prove identical YAML SHA-256 and nintent direct-url commit in all three containers.

The preferred implementation is to build the exact nintent commit from GitHub and copy/checkout
the exact nauto commit's `seed/intent_sources.yaml` into the immutable image. This remains one
source-controlled YAML owner; the image copy is a verified deployment artifact. Do not use a
mutable host checkout, mutable branch head, or web-container-only Git checkout as the worker's
input.

### 3.4 Approval boundaries

The following are read-only or disposable and may be executed while preparing the phase:

- source/test/documentation changes;
- local and isolated tests;
- read-only live GraphQL/REST GET/OPTIONS/status queries;
- aggregate live fingerprints that exclude private prose;
- candidate image builds that do not replace a running service; and
- backup-restore testing against a disposable database.

The following require an explicit operator approval at their named gate:

1. entering the maintenance window and stopping/replacing live services;
2. applying the final YAML Import Job with `apply=true`;
3. executing any positive retained REST mutation probe in live Nautobot;
4. restoring the live database or media archive; and
5. resuming Jobs and routine mutation operations.

Pushing repaired commits is owned by the user. The implementation must stop before the candidate
build if the required remote SHAs are unavailable.

## 4. Scope and non-goals

### 4.1 In scope

- repair and truthfully re-prove the incomplete Phase 3 gates;
- correct active documentation that still instructs removed UI writes;
- pin and verify the exact nintent/nauto deployment inputs;
- provide one explicit canonical YAML path to all Nautobot processes;
- freeze matched nintent, nctl, nauto, deployment-config, and superproject revisions;
- capture a fresh live preservation baseline without private prose;
- verify a database dump and media archive before cutover;
- deploy the contracted code under a maintenance freeze;
- run the official final YAML preview against live state;
- apply only the separately approved exact plan;
- refetch and prove repeat idempotence;
- run the complete retained/removed live interface smoke matrix;
- preserve and verify actual-ledger, JobHook, Job, operation, and VM-read boundaries;
- resume operations only after all gates pass; and
- hand the final YAML Import contract to VM Phase 3 Steps 9–12.

### 4.2 Explicitly retained

- all nintent domain models and migrations through `0016`;
- the eleven consumer-backed GraphQL model registrations and four pinned nctl queries;
- the nodes, Braindumps, and Alignment Reviews REST collections with their Phase 2 methods/fields;
- nctl lifecycle, node-link, Braindump/review, drift, render, reconcile, ops, SSH, and session
  behavior;
- the strict nine-root canonical YAML and dry-plan/apply Import/Analyze contracts;
- the IPAM Job and nauto actual-ledger ingest;
- the eleven read-only nintent list/detail pairs and nested review panel;
- all current confirmed desired rows, realized links, provenance, actual-ledger rows, and
  operation artifacts;
- the live AI Resource Auto Review JobHook and its populated Device custom fields; and
- native Nautobot UI/API surfaces outside nintent ownership.

### 4.3 Out of scope

- adding or deleting a domain model or migration;
- implementing compute drift, matching, linking, guest creation, stop/delete/replace, or Proxmox
  actuation;
- seeding VM Phase 3 compute rows or adopting its proposed MAC/template values;
- running Analyze, IPAM, Ingest, Seed, or reconcile apply modes except where explicitly approved
  by this plan;
- converting Braindump or Alignment Review prose into executable input;
- changing drift, planner, SSH, Ansible, observation, or operation-evidence schemas;
- removing the AI Resource Auto Review JobHook;
- adding a generic CRUD API, compatibility route, UI writer, dashboard, server, daemon, or MCP
  surface;
- broad test consolidation or nctl modularization;
- altering host state, generated production artifacts, dnsmasq, known_hosts, or Proxmox; and
- pushing commits on the user's behalf.

## 5. Frozen deployment and data contracts

### 5.1 Matched revision and image contract

The final deployment tuple must contain:

```text
superproject SHA
nintent SHA
nctl SHA
nauto SHA
nodeutils SHA
ansible_agdev SHA
deployment-config SHA
candidate image ID/digest
installed nintent direct-url SHA
embedded canonical YAML SHA-256
live rollback image ID/digest
live rollback installed nintent SHA
live nauto GitRepository revision
```

The web, worker, and scheduler must run the same candidate image ID. Each must report the exact
nintent SHA and canonical YAML digest. A branch name, a tag without a resolved SHA, or “latest”
does not satisfy this contract.

No mixed old/new nintent and nctl operation is supported. Routine nctl mutations remain stopped
until both sides of the final tuple pass smoke checks.

### 5.2 Live preservation manifest

Before maintenance, capture sanitized identities/counts and stable field digests for:

- IntentSource;
- DesiredNode;
- DesiredEndpoint;
- DesiredIPRange;
- DesiredNodeOperationalOverride;
- DesiredService;
- DesiredDependency;
- DesiredServicePlacement;
- DesiredComputePlatform;
- DesiredComputeInstance;
- BrainDumpDocument count, authorship counts, and per-row digest computed without exporting body;
- AlignmentReview count and per-row digest computed without exporting summary;
- DesiredNode realized Device ID/source pairs;
- DesiredEndpoint realized IPAddress ID/source pairs;
- compute realized links, expected to remain unchanged;
- Device, Cluster, VirtualMachine, Interface, VMInterface, and IPAddress aggregate identities;
- Job, ScheduledJob, JobHook, and relevant custom-field definitions/counts;
- latest JobResult identity/status/time and active/pending JobResult set;
- operation-directory entry names and public result/schema digests, without copying credentials or
  private payloads; and
- current migrations, installed package commit, image IDs, and container start times.

Reports may contain aggregate counts, stable public IDs, route names, schema fields, and hashes.
They must not contain a token, authorization header, Braindump body, Alignment Review summary, raw
ObjectChange payload, raw Device custom-field value, unrestricted provider payload, or credential.

### 5.3 Canonical YAML and Import contract

The checked-in `nauto/seed/intent_sources.yaml` remains the only bulk desired-state document and
contains exactly these roots:

```text
intent_sources
desired_nodes
desired_endpoints
desired_ip_ranges
desired_compute_platforms
desired_compute_instances
desired_services
desired_service_placements
desired_node_operational_overrides
```

The planning-time identity hypothesis is:

| Root | Expected identities |
|---|---:|
| IntentSource | 2 |
| DesiredNode | 5 |
| DesiredEndpoint | 5 |
| DesiredIPRange | 3 |
| DesiredComputePlatform | 0 |
| DesiredComputeInstance | 0 |
| DesiredService | 6 |
| DesiredServicePlacement | 1 |
| DesiredNodeOperationalOverride | 0 |
| **Total declared rows** | **22** |

This is not a pre-approved live result. The official preview artifact must name every
create/update/unchanged/conflict action. The expected safe result is 22 unchanged rows or only
field updates already authorized by Phase 0's disposition ledger. Any create, conflict, identity
change, lifecycle change on an existing node, realized-link change, deletion-like action, or
unexplained field update stops before apply and requires a new user decision.

Omission never means delete, retire, disable, unlink, replace, or stop. Compute roots stay empty.

The live sequence is:

```text
official preview (apply=false)
  -> artifact/schema/digest and zero-write verification
  -> separate operator approval of the exact object plan
  -> apply=true
  -> GraphQL/ORM confirmation and preservation comparison
  -> repeat apply=true only within the approved no-op/idempotence boundary
  -> final preview showing the same unchanged state
```

The repeat run must not update `last_updated`, create ObjectChanges, or repeat a semantic write for
unchanged rows. If the implementation's truthful artifact uses transaction terminology for a
zero-change apply, the database fingerprints, not the label alone, decide whether a write occurred.

### 5.4 Deployment ordering clarification

The parent roadmap lists live YAML preview before code deployment. The current live package cannot
produce the final Phase 1 preview artifact, so an official preview cannot be obtained from the old
deployment.

Use this safe ordering:

1. run a read-only candidate-image planner against the frozen live baseline if practical;
2. enter maintenance and take verified backups;
3. deploy the exact candidate image with operations still frozen;
4. verify health/migrations and run the official `apply=false` Job;
5. stop for plan review and separate apply approval; and
6. apply/refetch/repeat before operations resume.

Deploying the candidate before official preview does not authorize a data mutation. If preview is
unexpected, leave operations frozen and either fix forward or restore the complete prior image
tuple. Do not reintroduce compatibility routes.

### 5.5 Backup and rollback-point contract

The pre-cutover backup consists of:

- a PostgreSQL custom-format dump of the live `nautobot` database;
- a Nautobot media-volume archive sufficient to restore FileProxy/Job artifacts;
- a manifest containing file sizes, SHA-256 digests, dump listing result, timestamps, database
  server version, and the revision/image rollback tuple; and
- a successful restore of the dump into a separately named disposable database followed by
  migration and aggregate-count checks.

Redis is not authoritative and is not restored as state. Never claim a backup is valid only
because `pg_dump` exited zero; `pg_restore --list` and the disposable restore must pass.

Store backups and raw evidence under:

```text
.local/interface-contract/p4/<timestamp>/
```

with directories mode `0700` and files mode `0600`. Do not commit them.

## 6. Implementation and deployment procedure

### Step 0 — Recapture boundary, evidence, and live preservation baseline

1. Record exact local/root/submodule SHAs, branches, remote SHAs, dirty files, and ahead/behind
   state.
2. Record live container names, image IDs, health, start times, installed nintent direct-url SHA,
   Nautobot/Django/PostgreSQL/Redis versions, and migration list.
3. Confirm all required repaired commits are available remotely; do not push.
4. Create the protected evidence directory and record its permissions.
5. Capture the full Section 5.2 preservation manifest without private prose.
6. Record active/pending Jobs and establish that no conflicting Import, Analyze, IPAM, Ingest,
   Seed, VM seed, or routine nctl mutation is running.
7. Record the exact canonical YAML file SHA and validate its nine roots and 22 planning-time
   identities through the production loader.
8. Record the current nauto GitRepository revision/path behavior in web and worker.
9. Record current live GraphQL roots, REST routes/OPTIONS, UI route availability, and nctl
   read-only command results as the rollback baseline.
10. Record operation/artifact directory manifests without reading secret-bearing contents.

Gate: the live baseline is readable, no unclassified desired/YAML change occurred since Phase 0,
the evidence is sanitized, and no live mutation has occurred.

### Step 1 — Repair Phase 3 tests and active documentation

1. Convert the obsolete Braindump/Alignment Review UI mutation tests into final-contract absence,
   literal-404, panel separation, escaping, and non-mutation tests.
2. Build reusable fixture factories for all eleven retained UI models, including reviewed and
   unreviewed Braindumps plus safe realized-link relationships.
3. Grant the exact `view_*` permission for each retained model and assert every list/detail GET,
   missing-permission result, POST method result, and unchanged row fingerprint.
4. Assert all 38 removed route names fail reversal and every former literal mutation/utility URL
   returns 404 for a broadly permitted authenticated user.
5. Assert final navigation, table columns, filters, related read links, templates, forms,
   provenance, lifecycle, link/source, effective compute context, and timestamps.
6. Expand the Phase 2 API runtime test into the complete frozen route/method/response-field/
   writable-field/invalid-input/zero-write matrix.
7. Execute invalid IntentSource singular/plural GraphQL queries and positive retained-root queries.
8. Add the Phase 3 plan's missing nctl node-link boundaries: absent ID, absent node, slug mismatch,
   partial link/source, pre/post GraphQL failure, wrong confirmation source, and post-PATCH
   executor evidence/progress preservation.
9. Replace the operative removed-UI workflow in `nctl/docs/register-a-new-pc.md` with canonical
   YAML Import plus `nctl lifecycle`; a note above stale instructions is not enough.
10. Correct active `nintent/README_DEV.md` guidance so it describes read-only tables rather than
    advising new `ButtonsColumn` edit/delete actions.
11. Search every other current document named by the roadmap and fix any operative removed API/UI
    instruction.
12. Add dated supersession/correction notes to the Phase 3 final and Step 8–10 reports without
    deleting their original historical text.

Gate: the repaired tests express only the final contract, active documentation has no executable
removed-UI recipe, and local suites pass.

### Step 2 — Re-prove Phase 2/3 in disposable Nautobot and HTTP

Use an isolated Nautobot 3.1.3/PostgreSQL 15/Redis environment with the exact repaired nintent and
nctl source:

1. prove the compose/network/volume/port names cannot resolve or mount live resources;
2. migrate an empty database through `0016`;
3. run `makemigrations nautobot_intent_catalog --check --dry-run`;
4. run the complete Nautobot App suite, not only the three files that failed during planning;
5. run all 22 list/detail UI cases, 38 removed-route cases, navigation/table/template cases, and
   before/after mutation fingerprints;
6. run the full REST and GraphQL matrices;
7. expose the disposable app on a non-live port with a disposable token;
8. create a synthetic unlinked DesiredNode and uniquely matching Device;
9. use real nctl GraphQL snapshots and the real planner to produce `actual_node_not_linked`;
10. execute the real ledger writer through GraphQL/PATCH/GraphQL;
11. recompute fresh drift/plan and prove the link action does not repeat;
12. execute lifecycle change/no-op and Braindump/review create/update/delete through the real
    clients with GraphQL confirmation;
13. execute representative fail-closed reset fixtures;
14. record HTTP method/path/status counts and prove zero calls to removed REST collections;
15. rerun nctl's full 954-or-later test suite;
16. retain sanitized commands, summaries, artifacts, and revision IDs; and
17. tear down only the exact disposable containers, volumes, and network, then prove they are gone.

Gate: all runtime/HTTP tests pass with positive action evidence. Any failure keeps live deployment
blocked.

### Step 3 — Freeze commits and build a reproducible candidate

1. Commit nintent runtime-test/documentation repairs in reviewable commits.
2. Commit nctl tests/documentation only if changed.
3. Update the superproject pointers and deployment configuration.
4. Ask the user to push the exact required nintent/nctl/root commits.
5. Resolve the remote SHAs again and require exact equality with the intended tuple.
6. Replace mutable-branch nintent installation with an exact-SHA build input.
7. Make the exact nauto commit's canonical YAML available at one immutable, explicit image path;
8. set the explicit YAML path in web, worker, and scheduler;
9. build the candidate once and record its image ID/digest and build inputs;
10. run the full App suite and migration check inside the candidate image;
11. start disposable web/worker/scheduler containers from that same image and verify the installed
    nintent SHA and YAML digest in all three; and
12. prove the candidate can discover exactly three nintent Jobs and the final nauto Job set.

Gate: there is one reproducible candidate image and exact remote revision tuple. Rebuilding the
same source tuple must not silently select a different nintent or YAML commit.

### Step 4 — Approve maintenance, freeze writers, and verify backups

After explicit approval to enter maintenance:

1. announce the maintenance boundary and stop routine nctl mutations and VM Phase 3 seed work;
2. prevent new Import, Analyze, IPAM, Ingest, Seed, and other relevant Job submissions;
3. stop scheduler/worker processing and wait for the recorded active Job set to reach zero;
4. stop or otherwise quiesce the web write path before the backup snapshot;
5. take the PostgreSQL custom-format dump and Nautobot media archive;
6. write checksums and a rollback manifest;
7. restore the dump into a disposable database and compare migrations and aggregate counts;
8. verify the media archive can be listed and sampled without exposing private contents;
9. recheck live database fingerprints after backup and before deployment; and
10. record the exact cutover time and zero-write interval.

Gate: backup and restore proof pass, no writer is active, and the rollback tuple is complete.

### Step 5 — Deploy the exact matched code with data writes still frozen

1. replace web, worker, and scheduler with the already-tested candidate image; do not rebuild from
   a mutable branch during the window;
2. run the normal Nautobot upgrade/sync procedure required for the installed App;
3. prove no new nintent migration exists and applied migrations still end at `0016`;
4. prove `makemigrations --check --dry-run` is clean;
5. start web, worker, and scheduler from the same image ID;
6. verify health and exact nintent/YAML revision/digest in every process;
7. sync/verify nauto Jobs at the exact approved commit without running Seed or Ingest;
8. confirm exactly three nintent Jobs and the approved nauto Jobs are discoverable;
9. run only read-only health, GraphQL schema, route-registration, and source-file checks; and
10. keep routine operations and VM seeding frozen.

Gate: the final code is healthy and matched, live row fingerprints are unchanged, and no Import
apply or retained writer has run.

### Step 6 — Run the official live YAML preview and obtain apply approval

1. run `Import Intent Sources` with `apply=false` using the explicit canonical path;
2. capture `intent-import-result.json` and verify schema `nintent.intent-import.v1`;
3. independently prove the preview changed no row count, field digest, ObjectChange count,
   realized link, JobHook, actual-ledger row, or private prose digest;
4. compare all 22 declared identities and every proposed field change with Phase 0's disposition
   ledger and the fresh baseline;
5. require zero conflicts, errors, delete-like actions, lifecycle overwrites, and realized-link
   writes;
6. explain every create/update; do not accept an unexpected difference because it is small;
7. present the exact artifact totals and identities to the user without private prose; and
8. request separate approval for the exact apply plus its conditional idempotence repeat.

Gate: only the exact reviewed plan is authorized. Any changed live/YAML ownership fact stops the
phase before mutation.

### Step 7 — Apply, refetch, and prove repeat idempotence

After explicit approval of the exact plan:

1. recheck the source SHA, image ID, active Job set, and target-row precondition fingerprints;
2. run `Import Intent Sources` with `apply=true`;
3. require a committed transaction and confirmed post-commit refetch;
4. fetch all retained desired roots through the canonical GraphQL query;
5. compare identities, YAML-owned fields, preserved fields, lifecycles, realized links/sources,
   prose hashes/counts, JobHooks, and actual-ledger fingerprints with the approved before/after
   manifest;
6. stop immediately on any unapproved side effect;
7. run the approved repeat `apply=true` and require no semantic write, no changed row timestamp,
   and no new ObjectChange for unchanged rows;
8. run a final `apply=false` preview and require the same all-unchanged state;
9. preserve all three versioned artifacts and their SHA-256 digests; and
10. record intended ObjectChanges separately from unrelated cluster history.

Gate: apply/refetch/repeat is truthful and confirmed, with no loss or unapproved change.

### Step 8 — Run the live retained/removed interface and Job smoke matrix

Run read-only checks first:

1. canonical desired, actual, and Braindump GraphQL queries validate and return the expected
   shapes; do not include private prose in evidence;
2. IntentSource GraphQL roots fail schema validation;
3. only the three retained nintent REST collections reverse/respond;
4. all four removed REST families return 404;
5. all 22 retained UI routes render with normal permissions;
6. all former add/edit/delete/Quick Host Add/Source YAML paths return 404;
7. navigation/tables/templates contain no mutation affordance;
8. Import, Analyze, and IPAM default to dry modes and emit their expected artifact shapes;
9. nauto Seed/Ingest dry-run behavior and Job discovery are intact without an apply;
10. `nctl status`, `actual`, `drift --json`, deterministic renders into a protected temporary
    directory, dry `reconcile`, `ops list/show`, and Braindump list/show pass;
11. dry reconcile performs zero SSH/Ansible/Job mutation; and
12. VM Phase 3 read-only compute/YAML roots are accepted as empty and produce no compute action.

Positive live mutation proof is a separate approval gate. If approved, use dedicated synthetic
identities only:

- exercise a synthetic lifecycle transition and repeat no-op;
- exercise a synthetic node-link transition and fresh non-repetition;
- exercise synthetic Braindump/review create/update/delete;
- confirm every write through GraphQL;
- remove only the exact synthetic rows; and
- record any intentional ObjectChange residue.

Do not mutate a confirmed production node merely to obtain a green test. If the user declines the
live synthetic probe, report the live retained-writer check as omitted and the overall phase as
partially complete unless the parent roadmap is explicitly amended.

Gate: every retained read/write path is positively exercised at the required layer, removed paths
are absent, and no host or provider actuation occurred.

### Step 9 — Preservation audit, resume, and VM handoff

1. repeat the complete Section 5.2 preservation manifest;
2. classify every difference as approved Import change, approved synthetic probe/cleanup,
   expected Job/operation evidence, or defect;
3. prove the AI Resource Auto Review JobHook and its custom-field definitions/data were not
   unintentionally changed;
4. prove no desired compute row, Proxmox object, generated production file, SSH trust entry,
   Ansible target, or host service was changed;
5. prove database migrations remain through `0016`;
6. confirm all containers use the final matched image and all local repositories are at the final
   tuple;
7. obtain approval to resume scheduler, worker, routine Jobs, and nctl mutation operations;
8. resume in a controlled order and verify health/queue state;
9. hand the deployed strict YAML/Import contract and exact nauto revision to VM Phase 3 Steps
   9–12; and
10. state explicitly that VM compute/MAC/template seed content still requires its own preview and
    user approval and was not applied here.

Gate: only reviewed differences exist, operations resume cleanly, and VM work no longer depends on
a removed interface.

### Step 10 — Final searches, measurements, commits, and report

1. run all Section 10 searches across active code, tests, configuration, and current docs;
2. classify historical matches rather than deleting history;
3. record before/after route, ViewSet, GraphQL root, Job, UI class/form/table/template, test, and
   line measurements;
4. run all local/runtime/HTTP/live smoke suites and `git diff --check`;
5. record exact final, deployed, and rollback tuples;
6. record backup/restore verification and evidence retention owner/date;
7. record the Phase 3 audit defects and their final dispositions separately from Phase 4
   deployment results;
8. record every skipped, substituted, declined, or failed check;
9. write per-step reports where useful and one
   `devdocs/big/interface_contract/p4/report.md`;
10. update the parent roadmap only if a discovered fact changes its current contract; and
11. declare `complete`, `partially complete`, `implemented, not deployed`, or `rolled back`
    according to the actual evidence.

## 7. Required verification matrix

| Area | Required proof |
|---|---|
| Phase 3 repair | prior 9 failures/6 errors are eliminated by final-contract tests, not skips |
| Disposable App suite | complete Nautobot runtime suite passes through migration `0016` |
| Disposable HTTP | real planner/executor/API transition, fresh non-repetition, lifecycle, and prose writers |
| GraphQL desired | one joined query returns every retained desired root/relation |
| GraphQL actual | one joined query returns selected Device/Cluster/VM/interface/IP fields |
| GraphQL Braindump | list/show relation works without private prose entering evidence |
| IntentSource | GraphQL singular/plural absent; ORM Job and read-only UI retained |
| REST routes | exactly nodes, Braindumps, and Alignment Reviews retained |
| REST methods/fields | complete list/detail method, exact fields, invalid input, and zero-write rejection matrix |
| Write confirmation | lifecycle, link, Braindump, and review prove GraphQL before/after |
| UI | exactly 22 retained list/detail routes render with permissions |
| Removed UI | all mutation/utility names non-reversible and literal paths 404 |
| UI non-mutation | list/detail POST behavior and full row fingerprints prove zero writes |
| Braindump boundary | separated, autoescaped user/AI panels; reviewed/unreviewed; no controls |
| YAML | exact nine roots, unknown roots rejected, omission no-op, 22 reviewed identities |
| Import | preview zero-write; approved atomic apply; GraphQL refetch; repeat no-op |
| Analyze/IPAM | dry default and artifact contracts remain |
| nauto | exact Job revision; no duplicate desired writer/generator; Ingest retained |
| Image | exact nintent/nauto SHAs; identical web/worker/scheduler image ID |
| YAML path | explicit read-only path and identical digest in web/worker/scheduler |
| Schema | no new migration; live state remains through `0016`; makemigrations clean |
| Backup | DB dump lists/restores; media archive lists; checksums recorded |
| Preservation | desired/prose/link/actual/JobHook/operation manifests match approved changes |
| nctl | status/actual/drift/render/dry-reconcile/ops/Braindump read checks pass |
| No actuation | zero unapproved SSH, Ansible, Job apply, host, or provider action |
| VM handoff | compute roots remain empty; final Import contract available to VM Steps 9–12 |
| Secrets | no token, credential, private prose, raw custom-field payload, or provider dump in reports |

## 8. Evidence and report requirements

The final report must include:

1. exact status and deployed/rolled-back statement;
2. exact start, repaired-source, candidate, deployed, and rollback tuples;
3. evidence and backup locations, permissions, retention owner/date, and redaction statement;
4. the Section 2 Phase 3 audit table with final dispositions;
5. the failed planning-time disposable result and the passing repaired result;
6. full disposable UI/API/GraphQL/HTTP test summaries and teardown proof;
7. image build inputs, image digest, installed commit, and per-container YAML digest;
8. before/after preservation manifests and every classified difference;
9. backup listing and disposable restore result;
10. official Import preview/apply/repeat artifacts and totals;
11. retained/removed live route and writer results;
12. nctl and VM read-only smoke results;
13. Job freeze/resume times and queue state;
14. before/after measurements and current/historical search classification;
15. every user approval and its exact authorized scope;
16. every deviation, omitted check, declined live probe, unexpected state, or rollback action; and
17. the VM Phase 3 Steps 9–12 handoff.

Do not include live tokens, authorization headers, Braindump bodies, Alignment Review summaries,
raw ObjectChange payloads, raw Device custom-field values, full database/media contents, raw SSH
keys, or credentials.

## 9. Failure handling and rollback

### 9.1 Before maintenance

If Phase 3 repair, disposable proof, remote SHA availability, image reproducibility, canonical
YAML path, or live baseline classification fails:

- do not stop or rebuild live services;
- do not run a live Job;
- leave live state on the rollback tuple;
- fix the implementation and restart at the failed gate; and
- report `partially complete` or `implemented, not deployed` truthfully.

### 9.2 After maintenance but before YAML apply

If backup verification, candidate startup, migration check, Job discovery, official preview, or
read-only smoke fails:

1. keep writers and routine nctl operations stopped;
2. preserve sanitized failure evidence;
3. confirm whether the database/media fingerprints changed;
4. fix forward only if the correction remains within the approved window and tuple;
5. otherwise restore the complete prior web/worker/scheduler image and nctl/nauto tuple; and
6. resume only after the old contract and pre-window fingerprints are verified.

No database restore is needed when data did not change. Do not restore merely to hide a failed
test.

### 9.3 After YAML apply

If apply, confirmation, repeat, or preservation comparison detects an unapproved data change:

1. stop all relevant writers;
2. preserve the apply artifact, committed action list, JobResult, and failure point;
3. do not run a compensating YAML omission or ad hoc ORM edit;
4. obtain explicit approval before restoring;
5. restore the verified database dump and matching media archive when rollback is chosen;
6. restore the complete prior image/revision tuple;
7. verify migrations, desired/prose/link/actual/JobHook counts and hashes, GraphQL, UI, REST, and
   ordinary nctl read behavior; and
8. record every side effect that occurred before restore.

Because no schema migration is expected, do not create a migration or compatibility reader as a
rollback mechanism.

### 9.4 After operations resume

Any later rollback is still a complete tuple rollback. Do not mix:

- old UI with new REST;
- old Import variables with new YAML;
- new nctl writers with old nintent reads;
- a restored database with un-restored FileProxy media; or
- a new nauto seed revision with an old approved plan.

## 10. Required searches

Search active code, tests, configuration, shell wrappers, Makefiles, and current documentation for
at least:

```text
ObjectEditView
ObjectDeleteView
FormView
NautobotModelForm
DesiredHostQuickAdd
desiredhost_quick_add
create_desired_node_with_primary_endpoint
DesiredHostCreationResult
source_yaml_intent_source_list
source_yaml_list
AlignmentReviewAddView
AlignmentReviewEditView
AlignmentReviewDeleteView
alignmentreview_add
alignmentreview_edit
alignmentreview_delete
braindumpdocument_add
braindumpdocument_edit
braindumpdocument_delete
ButtonsColumn
ToggleColumn
TABLE_ACTION_BUTTONS
form method="post"
csrf_token
type="submit"
Quick Host Add
Source YAML
normal Nautobot CRUD
DesiredServiceSerializer
DesiredEndpointSerializer
DesiredComputePlatformSerializer
DesiredComputeInstanceSerializer
DesiredServiceViewSet
DesiredEndpointViewSet
DesiredComputePlatformViewSet
DesiredComputeInstanceViewSet
PreviewIntentSourceAnalysis
GenerateDesiredServices
service_repositories.yaml
desired_services.generated.yaml
disable_missing
intent-import-preview.json
intent-import-apply.json
fields = "__all__"
rest_get
@extras_features("graphql")
git+https://github.com/iwaag/nprojects.git
NAUTOBOT_INTENT_SOURCES_FILE
intent_sources_file
```

Classify rather than blindly delete:

- retained REST mutation and Job protocol calls;
- native Nautobot forms/routes outside nintent;
- Import/Analyze/IPAM POST semantics;
- eleven retained GraphQL registrations;
- historical plans, reports, migrations, and artifacts;
- dated Phase 3 correction notes;
- the exact pinned Git URL in deployment configuration; and
- the explicit final YAML path.

An operative current recipe, runtime import, positive UI mutation test, mutable unpinned build,
web-only YAML path, or compatibility alias for a removed surface blocks completion.

## 11. Definition of done

Phase 4 and the overall interface-contract initiative are `complete` only when:

- every Phase 3 audit defect in Section 2 is repaired and re-proved;
- the complete disposable Nautobot and real HTTP gates pass;
- current documentation contains no operative removed-UI/API instruction;
- exact repaired commits are pushed by the user and frozen in the superproject;
- the candidate image pins exact nintent and nauto revisions;
- web, worker, and scheduler run the identical image and see the identical canonical YAML digest;
- a verified database dump and media archive exist and the database restore test passed;
- the maintenance freeze prevented concurrent desired/actual mutation;
- live code uses the final GraphQL/REST/UI/YAML/Job matrix;
- official Import preview was zero-write and separately approved;
- apply/refetch/repeat/final-preview proves the exact reviewed desired state and no repeated write;
- all current desired identities, lifecycles, realized links/sources, prose hashes/counts,
  actual-ledger state, JobHooks, and operation evidence survived except for explicitly approved
  changes;
- retained writers were positively exercised and GraphQL-confirmed at the required layer;
- removed REST and UI paths are absent live;
- nctl read/dry-operation and Job dry-run smoke checks pass;
- no unapproved SSH, Ansible, host-service, provider, compute, or generated-file action occurred;
- migrations remain through `0016` with no model diff;
- operations resumed cleanly only after approval;
- VM Phase 3 Steps 9–12 received the deployed YAML Import contract without any compute seed being
  smuggled into this phase;
- reports and evidence contain no secret or private prose; and
- the final report records every deviation or omitted check without weakening completion language.

A reduced route count, a successful container restart, or an all-unchanged Import artifact alone
is not completion. Completion is a matched deployment with preserved intent, bounded write
authority, reproducible runtime proof, and a confirmed non-repeating data transition.
