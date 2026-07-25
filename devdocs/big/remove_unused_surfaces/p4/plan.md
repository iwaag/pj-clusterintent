# Remove Unused Surfaces Phase 4 Implementation Plan: Consolidate Current Documentation and Pre-deployment Evidence

Parent: [roadmap.md](../roadmap.md) — Phase 4.

Predecessor: [Phase 3 final report](../p3/report.md) — recorded as `implemented, awaiting push`
when it was written. At planning time the required nintent commit is now the checked-out
`origin/main`; Step 0 must reverify that handoff rather than relying on this planning observation.

Status: proposed; documentation consolidation, final pre-deployment verification, and revision
preparation only. The live rebuild, migrations `0015`/`0016`, removed-command live smoke checks,
and generated-dashboard cleanup remain Phase 5 work.

## 1. Goal and required transition

Make every current instruction describe the already-implemented CLI-only, dashboard-free,
cache-free contract before that contract is deployed to Nautobot.

Phases 1–3 removed the implementation locally, but several current documents still tell a human
or agent to run `nctl dashboard`, run `nctl serve`, use the reconciliation cache, or build future
work on those surfaces. Phase 4 removes those active instructions and freezes one exact
code/documentation/migration tuple for the coordinated deployment.

The transition is:

```text
before Phase 4
  local nctl
    = CLI-only, no dashboard/server runtime, no status push
  local nintent
    = no cache fields/link/config, migration 0016 ready
  current documentation
    = mixed contract:
        some nctl docs already describe drift/reconcile/ops correctly
        root and nintent READMEs still instruct dashboard use
        active core-reconcile and Braindump roadmaps still propose removed surfaces
        active VM roadmap still assigns findings/output to dashboard/status
  deployment
    = old nintent commit, migrations through 0014

after Phase 4
  current documentation
    = nctl CLI + structured output + JSONL/artifacts + nctl ops
    = nintent stores confirmed intent, not reconciliation cache
    = no active roadmap depends on or proposes the removed family
    = historical implementation reports remain truthful and clearly historical
    = VM desired-MAC and compute safety remain expressed through retained evidence
  pre-deployment evidence
    = deletion searches classified
    + repeatable source/test/dependency measurements
    + exact final matched and live rollback tuples
  deployment
    = still unchanged at 0014 until Phase 5
```

The observable outcome is:

- root and component READMEs name only supported commands and ownership boundaries;
- the core-reconcile dashboard and realtime API goals are explicitly superseded;
- Braindump's optional server/dashboard integration is explicitly superseded without changing
  Braindump, Alignment Review, Nautobot UI, GraphQL, REST, or nctl CLI semantics;
- the active VM roadmap and Phase 3 plan contain no operative dashboard/status-cache acceptance
  requirement;
- current documentation directs status inspection to fresh `nctl drift`, bounded operation
  outcomes to reconcile artifacts, and historical/running operation inspection to
  `nctl ops list/show`;
- repository-wide deletion searches have no unexplained active implementation, configuration,
  schema, or current-document match;
- pre-deployment measurements and dependency evidence are reproducible and do not treat reduced
  line/test counts as correctness proof;
- final nintent/nctl/root revisions and the live rollback tuple are recorded; and
- live Nautobot, its database, Jobs, hosts, generated dashboard files, and operation artifacts are
  unchanged.

This phase does not add a replacement GUI, API, daemon, MCP server, notification path, latest-state
cache, or compatibility alias.

## 2. Governing inputs and current baseline

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`, especially its historical-document and minimal-kernel
  boundaries;
- the parent roadmap;
- [Phase 0 final report](../p0/report9.md), especially the manifest and coordinated VM sequence;
- [Phase 1 final report](../p1/report9.md);
- [Phase 2 final report](../p2/report8.md);
- the Phase 3 plan and every Phase 3 report, treating [report.md](../p3/report.md) as the
  implementation summary but rechecking its formerly-pending push;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md` and latest VM Phase 3 reports;
- root and component READMEs/documents named in §5; and
- the current source, migration, config, test, packaging, and dependency files used by the
  deletion and measurement checks.

Later reports and the refactoring vision supersede historical plans where they conflict. Do not
copy an old command list, test count, dependency list, revision, or live state into the final
report without rechecking it.

### 2.1 Planning-time repository snapshot

Observed while this plan was written on 2026-07-25:

| Repository | Revision | Planning-time state |
|---|---|---|
| superproject | `207bff8e85f01b58ccea666d87e79263970174b2` | clean before `p4/plan.md` was added; `origin/main` at the same revision |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean; `origin/main` at the same revision; Phases 1–2 final implementation |
| `nintent` | `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | clean; `origin/main` at the same revision; Phase 3 implementation is now pushed |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

This is orientation only. Phase 4 implementation must preserve unrelated user changes and record
the actual starting state.

The checked-out `nintent` branch now proves that the one outstanding Phase 3 final-report item
(remote availability of `0914ca4...`) has been satisfied. Do not rewrite the historical Phase 3
report's then-accurate status. Instead, record the later push as a Phase 4 starting fact.

### 2.2 Planning-time live baseline

Read-only checks while this plan was written confirmed:

- all three Nautobot containers are healthy;
- the installed `nautobot-intent-catalog` distribution is `0.9.0` from
  `ad9d36397d23c269ad748e13acbccc532fa29f52`;
- live nintent migrations still end at `0014_braindump_exchange_diary`;
- local migrations `0015` and `0016` are not applied live; and
- no process listens on TCP port 8300.

Phase 4 must not change any of those live facts. The known generated directory
`/Users/eiji/.local/state/nctl/dashboard` remains Phase 5 cleanup scope; Phase 4 may record only
its path, entry names, and sizes, not read or archive its HTML/JSON content.

### 2.3 VM Phase 3 dependency

At planning time, VM Phase 3 reports Steps 0–5 complete and Step 6 has not started. Its active plan
requires:

```text
VM Phase 3 Step 6 — desired-MAC/dnsmasq deployability gate
  -> VM Phase 3 Step 7 — final review and matched commits
  -> coordinated deployment in VM Step 8 / remove_unused_surfaces Phase 5
```

The parent removal roadmap freezes the combined order as:

```text
remove_unused_surfaces Phases 1–3
  -> VM Phase 3 Step 6
  -> remove_unused_surfaces Phase 4 + VM Phase 3 Step 7
  -> one maintenance window applying 0015 then 0016
```

Therefore:

- documentation edits that do not claim a final tuple may be prepared before VM Step 6;
- final nctl tests, line/test counts, dependency inventory, commit hashes, and matched tuple must
  be recorded only after VM Step 6 is complete;
- Phase 4 and VM Step 7 must share one revision review rather than independently freezing
  different nctl/nintent pairs; and
- any VM Step 6 change to an output schema or current document must be folded into the Phase 4
  search and documentation pass before the tuple is final.

If VM Step 6 is still incomplete when implementation reaches the final-evidence gate, stop with
the documentation edits reviewable but Phase 4 `partially complete`; do not invent a provisional
deployment tuple.

### 2.4 Current documentation baseline

Planning-time searches found:

- stale active instructions in root `README.md`, `nintent/README.md`, and
  `nintent/README_QUICK.md`;
- stale active/future goals in `devdocs/big/core_reconcile/roadmap.md`,
  `devdocs/big/braindump/roadmap.md`, and `devdocs/big/vm/roadmap.md`;
- an already-amended supersession note and dashboard-free acceptance contract in
  `devdocs/big/vm/p3/plan.md`;
- no removed-surface token in current `nctl/README.md`,
  `nctl/docs/output-format.md`, `nctl/docs/compatibility.md`,
  `nctl/docs/usage_example.md`, or `nctl/docs/event-log.md`; and
- historical matches across completed Better Usability, Braindump, core-reconcile, VM, SSH-fix,
  and remove-unused-surfaces plans/reports/fixtures.

The active-document result is mixed rather than globally stale. Do not churn already-correct nctl
documentation merely to make every inventory row show an edit.

### 2.5 Current implementation and measurement baseline

The latest authoritative phase reports record:

| Metric | Current handoff value |
|---|---:|
| nctl top-level commands | 11 |
| nctl collected pytest cases | 954 |
| nctl tracked Python source lines (`src/`) | 17,763 |
| nctl tracked test lines (`tests/`) | 19,380 |
| nintent local Django-free tests | 187 |
| nintent full Nautobot App tests | 252 |
| nintent tracked non-test Python lines including migrations | 9,560 |
| nintent tracked test lines | 4,029 |
| nintent tracked template lines | 1,327 |
| nintent numbered migrations | 16 |

The nctl core dependency set is currently `typer`, `httpx`, `pydantic`, and `pyyaml`; its
development group is `pytest` and `respx`. Phase 1 proved a plain installed wheel contained none
of FastAPI, Starlette, uvicorn, websockets, httptools, uvloop, watchfiles, or python-dotenv.

These are handoff signals, not Phase 4 evidence and not quotas. Step 6 must remeasure after VM
Step 6 using the exact commands and scopes frozen in §7.

## 3. Scope, non-goals, authority, and sequencing

### 3.1 In scope

- update stale current root, nctl, and nintent operational documentation;
- add explicit supersession treatment to active core-reconcile and Braindump roadmaps;
- remove operative dashboard/status requirements from the active VM roadmap;
- reconfirm and, if needed, tighten the already-amended VM Phase 3 plan;
- preserve historical reports and fixtures as historical evidence;
- re-run the full removal-token searches with explicit current/history/test/migration
  classifications;
- prove current code, migration, examples, configuration, and documentation express one final
  contract;
- run or inherit only justified retained-path tests, with the inherited evidence identified
  exactly;
- record pre-deployment source/test line counts, collected tests, command surface, wheel/dependency
  inventory, and repository status;
- prepare final nintent/nctl/root commits and exact matched/rollback tuples;
- ask the user to push any new nintent documentation commit required by the GitHub-based build;
  and
- produce one final Phase 4 report.

### 3.2 Retained owners and documentation contract

| Concern | Current owner to document |
|---|---|
| Current desired/actual convergence status | a fresh `nctl drift` computation |
| One bounded reconcile outcome | its CLI result plus `plan.json`, round/final drift, action evidence, `result.json`, and JSONL log |
| Running or historical operation inspection | `nctl ops list/show` over durable disk evidence |
| Confirmed structured desired state | nintent |
| User-originated semantic Ground Truth | Braindump |
| Current AI explanation | Alignment Review |
| Actual ledger and observation | Nautobot/nauto plus nodeutils |
| Host actuation | ansible_agdev or another explicitly approved actuator |
| Deployment, migration, cleanup, rollback | user/operator-controlled Phase 5 maintenance window |

Do not use the unqualified phrase “single source of truth” for the entire system. The refactoring
vision's scoped authority table governs the wording.

### 3.3 Out of scope

Phase 4 does not:

- restore, replace, or emulate either dashboard or the serve API;
- add MCP, HTTP, WebSocket, daemon, scheduler, notification, TUI, or remote-agent integration;
- change nctl runtime schemas, reconciliation logic, action semantics, event ordering, locks, SSH
  policy, or operation artifacts for documentation convenience;
- change nintent models, migration operations, UI/API behavior, Braindump behavior, or desired
  schema;
- edit migration `0009`, `0010`, `0015`, or `0016`;
- delete historical plans, reports, fixtures, or old operation logs;
- rewrite old reports as though the removed feature never existed;
- remove the retained Nautobot UI for Braindumps, DesiredNodes, or DesiredServices;
- perform VM Phase 3 Step 6 implementation;
- deploy, rebuild, restart, migrate, run an import Job, apply a seed, write desired/actual data,
  run `nctl reconcile --yes`, invoke Ansible, or actuate a host;
- read generated dashboard HTML/JSON content;
- archive or remove the generated dashboard directory; or
- push a submodule or root commit.

If a documentation inconsistency reveals a runtime/schema defect rather than stale prose, stop
and route the defect back to its owning phase. Do not silently expand a documentation phase into
runtime implementation.

## 4. Frozen Phase 4 contracts

### 4.1 Supported operational inspection path

Current docs must consistently say:

```text
current cluster convergence
  -> nctl drift
  -> use --json for structured agent/tool consumption

one reconcile operation
  -> nctl reconcile dry plan
  -> separately authorized apply when intended
  -> persisted operation directory and result.json

past or running operation
  -> nctl ops list
  -> nctl ops show OPERATION_ID
```

`nctl drift` is fresh computation, not a persisted human dashboard. `nctl ops` is an evidence
reader, not a current-status cache. A historical `result.json` may still contain fields from its
own old schema and remains opaque evidence; current docs must not promise it is rewritten.

### 4.2 Removed contract wording

No current instruction may:

- list `nctl dashboard` or `nctl serve` as a supported command;
- tell a user to install a `serve` extra;
- describe `/api/v1`, WebSockets, port 8300, bearer-token serve auth, or a live browser dashboard
  as current/future work under an active roadmap;
- describe `reconciliation_status` or `reconciliation_checked_at` as current model/API fields;
- describe dashboard PATCH/status push as a current writer;
- configure or document `[dashboard]`, `[serve]`, `dashboard_url`, `dashboard_redirect`, or
  `NCTL_SERVE_TOKEN`;
- promise automatic dashboard regeneration from drift/reconcile;
- tell future VM phases to add dashboard tiles or dashboard/status effects; or
- imply a replacement presentation or remote API will be built in this initiative.

When a token is necessary to explain a deletion or supersession, the surrounding document must
make that historical/removal status explicit.

### 4.3 Core-reconcile history contract

`devdocs/big/core_reconcile/roadmap.md` is an active summary containing historical phases. Update
its current vision and design conventions to the retained CLI/disk-evidence contract.

Mark its Phase 3 dashboard and Phase 5 realtime API goals as **superseded and removed** by this
initiative, linking to the removal roadmap. Preserve enough original phase description to explain
the historical `p3/` and `p5/` reports; do not edit those completed reports or claim they were
never implemented.

The retained Phase 0–2 and Phase 4 responsibilities remain historical design context for the
current kernel.

### 4.4 Braindump authority contract

`devdocs/big/braindump/roadmap.md` keeps:

- both models and their prose ownership;
- minimal Nautobot UI;
- GraphQL reads;
- REST mutations;
- nctl CLI reads/writes;
- timestamp attention hints;
- confirmation before structured desired writes; and
- the separation between desired-write and reconcile-apply authority.

Its optional Phase 4 `nctl serve`/dashboard integration is superseded. Replace that optional goal
with a short explicit supersession statement: no remote/presentation extension is planned without
a named consumer and separate roadmap. Do not describe the retained Nautobot UI as a removed
dashboard.

### 4.5 VM safety and output contract

The active VM documents must express findings through:

- structured drift codes and bounded evidence;
- human-readable CLI drift text;
- reconcile classification, including manual-review/safe-stop states;
- planner/action suppression where unsafe;
- durable operation artifacts and `nctl ops` inspection; and
- positive zero-SSH/zero-Ansible or non-repetition proof where required.

Remove dashboard/status-cache effects from the active VM roadmap's vocabulary, Phase 4 output
requirements, Phase 9 documentation goal, and per-phase definition of done.

The active VM Phase 3 plan already uses this retained contract. Update only its top supersession
status if needed to say that local removal is implemented and live deployment is pending; do not
weaken desired-MAC mismatch/ambiguity blocking, digest suppression, direct-apply and planner
rechecks, exact target isolation, recovery, or non-repetition.

### 4.6 Historical evidence contract

Historical plans, reports, operation fixtures, and migrations may contain removed names because
they truthfully record an earlier contract.

Keep:

- completed reports under `devdocs/big/core_reconcile/p3/` and `p5/`;
- completed Better Usability, Braindump, VM, and SSH-fix phase records;
- every remove-unused-surfaces plan/report;
- migration history `0009` and `0010`;
- removal migration `0016`;
- negative tests proving removed fields/routes/config are absent; and
- the opaque historical operation fixture in `nctl/tests/test_operations_index.py`.

Do not mass-replace tokens in historical files. The active roadmap or directory-level context
must be sufficient to prevent a reader from treating an old implementation goal as current.

### 4.7 Revision and rollback contract

The final pre-deployment tuple must name:

```text
final matched tuple
  root:    <Phase 4 final root revision>
  nintent: <pushed commit containing 0015 + 0016 + current docs>
  nctl:    <VM Step 6 + removal + current docs final commit>
  nauto:   <exact revision intended for the coordinated VM sequence>
  nodeutils / ansible_agdev: exact unchanged or intentionally changed revisions

live rollback tuple
  nintent: ad9d363... or the exact rechecked live commit
  migration state: through 0014
  nctl/root and other component revisions actually used before the window
  database backup: Phase 5 command/path owner, not created in Phase 4
```

The Phase 4 report may record the root implementation revision it reports on, followed by a later
documentation-only report commit. It must not invent a self-referential final-report hash.

## 5. File-level documentation inventory

Step 1 must re-run searches before accepting this inventory.

### 5.1 Required edits

| File | Required final treatment |
|---|---|
| root `README.md` | remove dashboard/serve commands and explanatory sections; add/retain `ops list/show` and CLI/disk-evidence guidance |
| `nintent/README.md` | remove the cache-writer REST description and the reconciliation-status/dashboard-link section; document fresh drift and operation evidence |
| `nintent/README_QUICK.md` | remove the dashboard command, cache PATCH, and `dashboard_url` setup; point to drift/reconcile/ops |
| `devdocs/big/core_reconcile/roadmap.md` | update current vision/conventions; explicitly mark historical Phase 3 and Phase 5 goals superseded/removed |
| `devdocs/big/braindump/roadmap.md` | supersede optional server/dashboard integration while preserving minimal UI/API/CLI and prose authority |
| `devdocs/big/vm/roadmap.md` | replace operative dashboard/status requirements with retained CLI/JSON/reconcile/artifact evidence |
| `devdocs/big/vm/p3/plan.md` | revalidate the Phase 0 amendment; update only removal/rollout status or newly stale references |

### 5.2 Required review; edit only if the current contract is incomplete

| File | Review target |
|---|---|
| `nctl/README.md` | 11-command CLI, drift/reconcile/ops inspection, no cached-status claim |
| `nctl/docs/output-format.md` | current envelopes omit `nctl.dashboard.v1`, `nctl.serve.v1`, and `ReconcileData.dashboard` |
| `nctl/docs/compatibility.md` | no promise for removed schemas/routes; historical artifacts treated as evidence |
| `nctl/docs/usage_example.md` | examples use retained commands only |
| `nctl/docs/event-log.md` | JSONL durability without subscriber/WebSocket wording |
| `nctl/example.nctl.toml` | no `[dashboard]`/`[serve]` section or token |
| `nintent/README_DEV.md` | current model/testing guidance contains no cache/link contract |
| root `README_DEV.md` | scoped authority, evidence, completion, and breaking-change guidance remains correct |
| `devenv/nautobot/nautobot_config.py` | plugin remains enabled and has no `dashboard_url` |

An unchanged reviewed file is a valid outcome. Record it as `verified-current`, not as an omitted
inventory item.

### 5.3 Intentionally unchanged historical files

Do not edit:

- `devdocs/big/core_reconcile/p3/**` or `p5/**`;
- completed Braindump `p0/**` through `p3/**`;
- completed Better Usability phase plans/reports/fixtures;
- completed VM reports and the VM Phase 1 plan;
- completed SSH-fix plans/reports;
- remove-unused-surfaces Phases 0–3 plans/reports and the parent roadmap, except a narrowly
  justified cross-link correction;
- nintent migrations `0009`, `0010`, `0015`, and `0016`; or
- old operation logs/artifacts and the opaque operations-index test fixture.

If an old directory is genuinely ambiguous when entered directly, prefer one small current
directory-level supersession note over rewriting every historical file. Do not add notices unless
the active-roadmap links are insufficient.

## 6. Deletion-search and classification design

### 6.1 Required token set

Search at least:

```text
nctl serve
nctl dashboard
nctl_core.serve
nctl_core.dashboard
nctl_core.dashboard_render
nctl.serve.v1
nctl.dashboard.v1
DashboardConfig
ServeConfig
dashboard_url
dashboard_redirect
reconciliation_status
reconciliation_checked_at
NCTL_SERVE_TOKEN
/api/v1/ws
```

Also search structural/package terms within nctl-owned scopes:

```text
FastAPI
Starlette
uvicorn
WebSocket
subscribe
subscriber
publish
8300
[dashboard]
[serve]
index.html
drift.json
```

Generic terms must be scoped and read in context. For example, `ansible_agdev/api` is a retained
unrelated FastAPI webhook service, `subscribe` may be ordinary prose, and `drift.json` may name a
historical operation artifact. A substring match alone does not authorize deletion.

### 6.2 Search scopes

Run and record separate searches for:

1. current runtime source, packaging, config, templates, and current docs;
2. active tests and migrations;
3. historical plans, reports, and fixtures; and
4. ignored/local invocation state relevant to live consumers, without reading secrets.

Run tracked-file searches separately in the superproject and each submodule so submodule content
is not silently skipped. Use an explicit current-document list from §5 rather than classifying
every Markdown file by path alone.

### 6.3 Allowed final matches

Every remaining match must be assigned exactly one reason:

- applied migration history (`0009`, dependency reference in `0010`);
- the explicit removal migration (`0016`);
- a negative assertion proving absence in
  `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py`;
- the historical opaque-artifact fixture in `nctl/tests/test_operations_index.py`;
- the parent roadmap, refactoring vision, this plan, and Phase 4 report explaining removal;
- historical plans/reports/fixtures whose active roadmap marks the goal superseded;
- a current supersession notice that names the retired surface solely to prevent reintroduction;
  or
- an unrelated component match with a named retained consumer, such as `ansible_agdev/api`.

Any current instruction, runtime import, route, schema, model field, config reader, dependency,
template, or unexplained test fixture match blocks completion.

The final report must provide counts by classification and name every active-code/test exception;
“grep was noisy” is not a classification.

## 7. Pre-deployment measurement and dependency design

### 7.1 Stable measurement scope

Record at least:

| Component | Required measurement |
|---|---|
| nctl | top-level command count/list; tracked `src/` Python lines; tracked `tests/` lines; collected and passing pytest cases; wheel file count; direct and locked dependencies |
| nintent | tracked non-test Python lines including migrations; tracked test lines; tracked template lines; migration count; local test count; latest exact Nautobot-runtime proof |
| root/current docs | tracked line count for the §5 current-document set; stale-token matches before/after |
| nauto/nodeutils/ansible_agdev | exact revisions and confirmation whether unchanged; tracked source/test lines if changed by the coordinated VM work |

Freeze the exact `git ls-files` path patterns and tools in the evidence report so Phase 5 can
repeat them. Do not compare a Python-only baseline with a later Python-plus-template count.

### 7.2 Test evidence

After VM Step 6 and documentation edits:

1. run the full nctl suite from `nctl/` with the locked environment;
2. run `uv lock --check`;
3. run the documented local nintent suite from `nintent/`;
4. cite the Phase 3 252-test Nautobot-runtime result only if the final nintent diff after
   `0914ca4...` contains documentation alone;
5. if any nintent runtime, migration, packaging, template, or test file changed, rerun the
   applicable disposable Nautobot test proof instead of inheriting Phase 3 evidence;
6. run Markdown/link/path checks available locally, plus `git diff --check`; and
7. record every skipped, inherited, failed, or unavailable check explicitly.

Documentation-only edits do not require live Nautobot mutation. A cited prior test result must
name the exact code-tree relationship that makes it applicable.

### 7.3 Dependency and plain-install proof

For nctl:

- record `pyproject.toml` direct dependencies and development group;
- run `uv lock --check` and save a locked dependency tree;
- prove FastAPI, Starlette, uvicorn, websockets, httptools, uvloop, watchfiles, and python-dotenv
  are not locked or installed solely by nctl;
- build a wheel in a fresh `mktemp -d` directory;
- install only that wheel and its core dependencies into a fresh environment;
- run `nctl --help` and import retained CLI/events/operations modules;
- inspect wheel files and installed metadata for serve/dashboard modules/assets/extras; and
- remove only the validated temporary directory.

Do not classify `httpx`, `respx`, `anyio`, or `h11` as server residue without tracing their
retained consumers.

For nintent, record the exact package revision and migration files that the GitHub-based Phase 5
build will consume. Dependency upgrades are not part of Phase 4.

### 7.4 Counts are diagnostic, not acceptance

Line count, test count, and package count explain the removal and let Phase 5 detect an unexpected
deployment mismatch. They do not replace:

- absence of the retired contract;
- positive retained CLI/evidence tests;
- the Phase 3 disposable migration proof; or
- Phase 5's live matched-version verification.

## 8. Safety and evidence handling

Use a private directory such as:

```text
.local/remove-unused-surfaces/p4/<timestamp>/
```

Use mode `0700` for directories and `0600` for evidence files. Suggested files:

```text
revisions-start.txt
live-readonly-baseline.txt
current-doc-manifest.tsv
deletion-search-before.tsv
deletion-search-after.tsv
tests-nctl.log
tests-nintent-local.log
measurements.txt
dependencies.txt
plain-install.txt
matched-and-rollback-tuples.txt
environment-restoration.txt
```

Do not store or print:

- `.local/secrets` or the Nautobot token;
- authentication headers;
- Braindump bodies or Alignment Review prose;
- raw database rows or dumps;
- dashboard HTML/JSON contents;
- private keys, raw SSH key blobs, or vault contents;
- unrestricted provider payloads; or
- full operation artifact contents unrelated to the narrow schema/path proof.

Allowed live checks are read-only: container health, installed package metadata, migration state,
running Job count, process/listener checks, command help, aggregate counts, and names/sizes of the
known generated dashboard entries.

Do not run removed commands merely to prove they exist or fail before deployment. Source/help
inspection proves the local command surface in Phase 4; Phase 5 proves the deployed removed-command
error behavior.

## 9. Procedure

### Step 0 — Reconfirm prerequisites, ownership, and non-mutation boundary

1. Record root and all submodule HEADs, upstreams, dirty files, and dirty-file ownership.
2. Verify `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` is an ancestor of nintent `origin/main`.
3. Reconcile the Phase 3 final report's former `awaiting push` state by recording the later
   read-only remote fact; do not edit that report's historical statement.
4. Record VM Phase 3's latest completed step and current worktrees.
5. Require VM Step 6 complete before the final-evidence/tuple Steps 6–7. If it is incomplete,
   documentation drafting may continue but the phase cannot complete.
6. Record live container health, installed nintent version/commit, migrations, and running Jobs.
7. Confirm no port-8300 listener or removed-surface process exists. Do not stop an unexpected
   process without operator approval.
8. Confirm local `0015`/`0016` exist in order and remain unapplied live.
9. Record the generated dashboard directory path and entry names/sizes without reading contents.
10. Confirm `.local/secrets` is ignored without reading it.
11. Create the private evidence directory and record its retention owner.

Gate: dirty state is owned, Phase 3's push is available, the VM dependency is explicit, live
remains at `0014`, no removed process is active, and no mutation has occurred.

### Step 1 — Freeze the current-document manifest

1. Enumerate every file in §5 and verify it exists.
2. Re-run the required and structural token searches across every repository.
3. Assign each matching tracked file one classification:
   `edit-current`, `verified-current`, `historical`, `migration`, `negative-test`,
   `keep-unrelated`, or `initiative-evidence`.
4. Trace links from root/component READMEs and active roadmaps to catch stale instructions that do
   not use an exact search token.
5. Check command blocks, config examples, schema examples, headings, anchors, and phase handoffs.
6. Add newly discovered current documents to the manifest before editing.
7. Freeze the exact intended changed-file list and explain any difference from §5.

Gate: every current document and every token match has one owner and disposition; no unknown row
remains.

### Step 2 — Update root and component documentation

1. In root `README.md`, remove both retired commands and their feature sections.
2. Keep the ordinary CLI examples concise; add `nctl ops list/show` where operation inspection is
   introduced.
3. State that fresh drift, bounded reconcile evidence, and disk artifacts are the supported
   inspection paths, without promising a replacement GUI.
4. In `nintent/README.md`, remove the dashboard cache writer from the REST discussion.
5. Delete the current reconciliation-cache/dashboard-link section and replace only the useful
   operator guidance with the scoped authority wording in §4.1.
6. In `nintent/README_QUICK.md`, remove the dashboard command/config/PATCH instructions and show
   retained drift/reconcile/ops commands.
7. Review every nctl current document and edit only any contract gap found in Step 1.
8. Verify examples use working directories consistently:
   root uses `uv run --project nctl nctl ...`; nctl-local docs use `uv run nctl ...`.
9. Check links and anchors after deleting headings.

Gate: current operational docs contain only retained commands/config/contracts and explain where
fresh status and operation evidence come from.

### Step 3 — Mark superseded active-roadmap goals

1. Update the core-reconcile roadmap's current Vision and design conventions to CLI/disk evidence.
2. Mark core-reconcile Phase 3 and Phase 5 as superseded/removed with a direct link to this
   initiative; leave their historical descriptions and reports intact.
3. Update Braindump Phase 4 to state that its optional nctl server/dashboard integration is
   superseded.
4. Positively preserve Braindump's models, minimal Nautobot UI, GraphQL reads, REST writes, nctl
   CLI, authorship, and non-executable prose boundary.
5. Update the VM roadmap's general finding contract, Phase 4, Phase 9, and definition-of-done
   references from dashboard/status to the retained output/evidence contract.
6. Re-read the VM Phase 3 plan's supersession note and all Step 6/8/11/deliverable/handoff
   sections. Update only stale rollout tense or a newly found operative requirement.
7. Diff the VM documents and prove desired-MAC conflict/ambiguity blocking, digest suppression,
   planner/direct-apply suppression, zero SSH/Ansible, recovery, scope isolation, and
   non-repetition remain unchanged.

Gate: no active roadmap asks future work to restore a removed surface, and no retained VM or
Braindump safety/authority condition was weakened.

### Step 4 — Protect history and verify cross-links

1. Search completed phase directories for links from current roadmaps.
2. Confirm old core-reconcile Phase 3/5 reports are reachable as historical evidence but not
   presented as current guidance.
3. Confirm Better Usability's dashboard fixture has no current test/runtime consumer.
4. Confirm old Braindump and VM reports remain unchanged.
5. Confirm migrations `0009`, `0010`, `0015`, and `0016` are byte-identical to the Phase 3
   handoff.
6. Confirm old operation artifacts are not modified or reparsed.
7. Add at most a narrow directory-level notice if a direct entry point remains genuinely
   ambiguous after active-roadmap edits.

Gate: history is truthful, current guidance is unambiguous, and no evidence was deleted for a
cleaner grep result.

### Step 5 — Run final deletion and retained-contract searches

1. Run the §6 token set separately over current runtime/config/docs, tests/migrations, and history.
2. Run nctl import/module/package searches for deleted `serve`/dashboard code and assets.
3. Search dependency manifests and lockfiles for server-only packages.
4. Search nintent current source/schema/templates/config for all four cache/link/config tokens.
5. Search active VM/Braindump/core-reconcile documents for operative requirements, reading every
   remaining match in context.
6. Verify the current-document set has zero obsolete command/config/schema instructions.
7. Produce the final classified exception table with file, token, line, category, and reason.
8. Run `git diff --check` in every changed repository.

Gate: no unexplained active match remains; all exceptions fit §6.3.

### Step 6 — Run retained verification and record repeatable measurements

This step begins only after VM Phase 3 Step 6 is complete.

1. Record the final pre-commit source state and VM Step 6 report/revisions.
2. Run the full nctl suite and record collected/passed/skipped/failed counts and duration.
3. Run `uv lock --check`.
4. Run the local nintent suite.
5. Determine whether the final nintent runtime tree differs from the Phase 3-proven tree. Inherit
   the exact Phase 3 Nautobot-runtime proof only for documentation-only change; otherwise rerun it
   against disposable state.
6. Build and prove the plain nctl wheel using §7.3.
7. Record the exact command surface and absence of removed commands from `--help`.
8. Record source/test/template/current-doc line counts with frozen path patterns.
9. Record direct and locked dependency inventories and absence/presence reasons.
10. Record revisions and measurements for any nauto/nodeutils/ansible_agdev repository changed by
    the coordinated VM work.
11. Re-run final searches after generated lock/build/test activity and remove only validated
    temporary build/test state.
12. Record every warning, inherited result, omitted check, and cleanup action.

Gate: final measurements are repeatable by Phase 5, retained tests pass, package proof is clean,
and environment cleanup is complete.

### Step 7 — Prepare final commits and deployment/rollback tuples

1. Review each repository diff against the Step 1 manifest.
2. Commit nintent README changes as documentation on top of the already-pushed Phase 3
   implementation.
3. Ask the user to push the final nintent commit; do not push it.
4. Verify read-only that the exact final nintent commit is reachable from `origin/main`.
5. Commit any nctl documentation changes together with or after the final VM Step 6 code as a
   reviewable final nctl revision.
6. Commit root active-roadmap/README changes and final submodule pointers in a reviewable unit.
7. Record the exact matched tuple from §4.7, including nauto/nodeutils/ansible_agdev revisions.
8. Re-record the live installed nintent commit/migration state and the actual pre-window nctl/root
   tuple.
9. Record Phase 5's rollback prerequisite and owner, but do not create the live database backup
   yet.
10. Confirm no rebuild, restart, migration, Job, desired write, seed, reconcile apply, Ansible
    run, dashboard cleanup, or host mutation occurred.

Gate: final code/docs/migration revisions are committed, the nintent revision is remotely
available for the GitHub-based image build, rollback facts are exact, and no mixed-version
deployment has begun.

### Step 8 — Produce one final Phase 4 report

Write `report.md` containing:

- precise status;
- execution timestamp and private evidence path;
- starting and ending root/submodule revisions and dirty-state ownership;
- resolution of Phase 3's formerly-pending push;
- VM Phase 3 Step 6/7 coordination result;
- live installed revision/migration state before and after;
- exact edited, verified-current, historical, migration, negative-test, and keep-unrelated file
  inventory;
- before/after current-document token counts;
- supersession treatment for core-reconcile, Braindump, and VM;
- proof that VM desired-MAC and Braindump boundaries remain;
- final deletion-search exceptions;
- nctl/nintent tests and inherited-proof justification;
- source/test/template/doc line counts and collected tests;
- direct/locked/plain-wheel dependency results;
- exact matched and live rollback tuples plus remote availability;
- environment and temporary-state cleanup;
- confirmation that generated dashboard content was neither read nor changed;
- confirmation of no live mutation;
- every omitted, substituted, inherited, failed, optional, or deferred check; and
- an exit-criteria table with exact evidence references.

The report must name the implementation/root revision it describes without inventing the hash of
its own future documentation commit.

Do not mark Phase 4 `complete` if VM Step 6 is unfinished, final nintent is not pushed, a current
instruction remains stale, an active-roadmap dependency remains, a deletion match is unexplained,
the measurement scopes are not repeatable, or a required test/cleanup gate is unresolved.

## 10. Verification matrix

| Area | Required proof |
|---|---|
| Root operations | root README lists retained CLI only and explains drift/reconcile/ops evidence |
| nctl docs | command/config/output/event docs contain no removed schema or server/dashboard promise |
| nintent docs | no cache fields, status push, dashboard link/route, or `dashboard_url`; retained REST/GraphQL/UI role is accurate |
| Core-reconcile | current vision is CLI/disk evidence; historical Phase 3/5 goals explicitly superseded |
| Braindump | optional serve/dashboard integration superseded; models/UI/API/CLI/authorship boundary retained |
| VM roadmap | findings and future phases use JSON/human drift, reconcile classification, artifacts, and ops |
| VM Phase 3 | no operative removed-surface requirement; desired-MAC safety and zero-actuation proof unchanged |
| Current docs | explicit manifest is complete; no stale command/config/schema instruction |
| Runtime deletion | no deleted imports/modules/routes/templates/config/dependencies return |
| Tests/migrations | every removed-token match is a named negative assertion, opaque history fixture, or migration/history record |
| History | completed reports/fixtures remain truthful and are not presented as current guidance |
| CLI/package | 11-command or final VM-adjusted retained surface; clean plain wheel; no server extra/assets/dependencies |
| nctl tests | full final suite collected and passed after VM Step 6 |
| nintent tests | local suite passes; exact runtime proof rerun or validly inherited |
| Measurements | frozen path patterns and commands yield repeatable pre-deployment counts |
| Revisions | exact final matched tuple and actual live rollback tuple recorded |
| Remote availability | final nintent commit is reachable for the GitHub-based image build |
| Live state | installed commit and migrations remain unchanged through `0014`; no live mutation |
| Secrets/evidence | no token, private prose, raw dashboard content, dump, or key material enters tracked evidence |

## 11. Exit criteria

- [ ] Phase 3's implementation commit is remotely available, with the later push recorded without
      rewriting its historical report.
- [ ] VM Phase 3 Step 6 is complete and Phase 4/VM Step 7 use one final revision review.
- [ ] Root README contains no supported `dashboard` or `serve` command/instruction.
- [ ] nintent READMEs contain no reconciliation cache, dashboard PATCH, link, redirect, or config
      contract.
- [ ] Current nctl docs describe only the retained command/config/schema/event surface.
- [ ] Current status is documented as fresh `nctl drift`, not a persisted cache.
- [ ] Bounded operation outcomes and history are documented through reconcile artifacts, JSONL,
      and `nctl ops list/show`.
- [ ] Core-reconcile's dashboard and realtime API phases are explicitly superseded/removed.
- [ ] Braindump's optional server/dashboard integration is explicitly superseded.
- [ ] Braindump models, minimal UI, GraphQL, REST, CLI, authorship, and prose non-execution remain.
- [ ] The active VM roadmap has no dashboard/status-cache output or acceptance requirement.
- [ ] The active VM Phase 3 plan has no operative removed-surface dependency.
- [ ] Desired-MAC mismatch/ambiguity blocking, digest suppression, planner/direct-apply
      suppression, zero SSH/Ansible, recovery, scope isolation, and non-repetition remain.
- [ ] Historical plans/reports/fixtures and old operation evidence are preserved.
- [ ] Migrations `0009`, `0010`, `0015`, and `0016` are unchanged.
- [ ] All required deletion tokens were searched separately across every repository and scope.
- [ ] Every remaining match has one allowed §6.3 classification.
- [ ] No current runtime/config/template/schema/dependency or current-instruction match is
      unexplained.
- [ ] The final nctl suite and lock check pass after VM Step 6.
- [ ] The nintent local suite passes, and runtime proof is rerun or inherited with an exact
      documentation-only justification.
- [ ] A clean plain nctl install contains no server/dashboard code, assets, extra, or dependency.
- [ ] Source/test/template/current-doc counts, collected tests, command surface, and dependency
      inventories use repeatable scopes.
- [ ] Exact final root/nintent/nctl/nauto/nodeutils/ansible_agdev revisions are recorded.
- [ ] Exact live rollback commit/migration tuple is recorded.
- [ ] The final nintent commit is pushed by the user and remotely verified.
- [ ] Live Nautobot remains on its original installed commit with migrations through `0014`.
- [ ] No rebuild, restart, migration, Job, desired/actual write, seed, reconcile apply, Ansible
      run, host actuation, or dashboard-directory cleanup occurred.
- [ ] Temporary build/test state is removed and generated dashboard content was not read.
- [ ] The final report records all deviations, inherited evidence, omissions, warnings,
      exceptions, and status.

A clean documentation grep alone is not completion. Completion requires one current contract,
positive retained-path evidence, repeatable pre-deployment measurements, exact revision/rollback
readiness, and proof that the live system was not partially deployed.

## 12. Handoff to Phase 5

Phase 5 receives:

- current root/component documentation naming only supported CLI/evidence paths;
- explicit supersession of active core-reconcile, Braindump, and VM dashboard/server goals;
- unchanged historical evidence and migration history;
- nctl with the final VM Step 6 behavior plus no server/dashboard runtime or dependencies;
- nintent with migrations `0015` and `0016`, no cache/link/config residue, and current docs;
- exact pushed nintent and matching nctl revisions;
- exact root/nauto/nodeutils/ansible_agdev revisions;
- a repeatable pre-deployment measurement and dependency baseline;
- classified deletion searches with no unexplained active matches;
- the exact live rollback tuple at `0014`;
- live Nautobot still unchanged; and
- one Phase 4 final report.

Phase 5 alone may:

- begin the maintenance window;
- stop writes/Jobs/routine nctl operations;
- back up the live database;
- rebuild and restart Nautobot from the pushed final nintent revision;
- apply `0015` then `0016`;
- activate the matching nctl revision;
- run live UI/REST/GraphQL/CLI/ops/Braindump/VM smoke checks;
- prove removed commands fail and no former server listens;
- archive or remove only the known generated dashboard directory with explicit authority;
- resume operations; and
- compare final live measurements with Phase 4's pre-deployment baseline.

