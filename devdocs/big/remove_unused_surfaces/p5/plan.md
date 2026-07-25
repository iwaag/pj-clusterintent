# Remove Unused Surfaces Phase 5 Implementation Plan: Coordinated Deployment and Final Verification

Parent: [roadmap.md](../roadmap.md) — Phase 5.

Predecessor: [Phase 4 final report](../p4/report.md) — `complete`, with nctl
`ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` and nintent
`c343c5a56047b0df9ad901dd4459863ef1954053` pushed and ready for one coordinated deployment.

VM dependency: [`devdocs/big/vm/p3/plan.md`](../../vm/p3/plan.md), especially Step 8. VM Phase 3
Steps 6–7 are complete; its seed/apply and environment-backed Steps 9–12 remain separate work after
this deployment phase.

Status: **proposed against a partially deployed live state**. Planning-time read-only inspection on
2026-07-25 found that migrations `0015` and `0016` and the target nintent revision are active in the
web container, but the worker and scheduler still run the old nintent revision. This plan must
audit and complete that interrupted/out-of-sequence deployment; it must not replay destructive
migrations merely to make the execution resemble the original roadmap sequence.

## 1. Goal and required transition

Deploy and positively verify the final CLI-only, cache-free contract while closing the current
mixed-container gap and preserving truthful evidence about work that already occurred before this
plan was written.

The planning-time transition is:

```text
current live state
  database
    = migrations 0015 + 0016 applied
    = four reconciliation-cache columns removed
  Nautobot web
    = nintent c343c5a...
  Nautobot worker + scheduler
    = old nintent ad9d363...                <-- mixed-version defect
  nctl checkout
    = matching final ebe8a1d...
  generated dashboard directory
    = still present and stale
  pre-migration backup
    = present, custom-format archive
  formal Phase 5 evidence
    = incomplete; prior report was deleted

to

final live state
  database
    = exact schema through 0016
  Nautobot web + worker + scheduler
    = exact same nintent c343c5a... revision
  nctl
    = exact matching ebe8a1d... revision
  retained paths
    = status/drift/render/reconcile-dry/ops/Braindump positively proven
  removed paths
    = commands, cache fields, links, routes, dependencies, server listener absent
  stale dashboard directory
    = explicitly archived or removed with separate approval
  evidence
    = pre-window backup validated
    + missing pre-migration aggregates reconstructed where possible
    + final matched tuple, measurements, omissions, and rollback proof recorded
```

The observable outcome is:

- all three Nautobot service containers are healthy and contain the exact target nintent commit;
- `showmigrations` reaches `0016`, `makemigrations --check --dry-run` reports no model drift, the
  four cache columns are absent, and the VM Phase 3 final schema is present;
- the prior migration's safety assertion is not claimed as a separately observed pre-window check;
  instead, the report distinguishes the migration's in-transaction success from any aggregate
  evidence reconstructed from the pre-window backup;
- retained live UI, REST, GraphQL, nctl CLI, operation-history, and Braindump paths work;
- a dry reconcile produces a bounded plan/evidence operation but executes no action;
- `nctl dashboard` and `nctl serve` fail through normal unknown-command handling;
- no process listens on TCP port 8300;
- no installed or local active code/config/current-document surface reintroduces the deleted
  feature family;
- the stale generated dashboard directory is no longer presented at its known live path;
- the final report compares Phase 0/Phase 4/final measurements without treating deletion counts as
  correctness proof; and
- every already-performed, rerun, reconstructed, omitted, failed, or separately deferred check is
  named precisely.

This phase does not create a replacement server, dashboard, cache, daemon, MCP surface, scheduled
drift process, or compatibility layer.

## 2. Governing inputs and planning-time baseline

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- every final report from remove-unused-surfaces Phases 0–4;
- this plan and the current Git history of `p5/`;
- `devdocs/big/vm/p3/plan.md` and `report3.6.md`/`report3.7.md`;
- `devenv/nautobot/docker-compose.yml`, `Dockerfile`, and `nautobot_config.py`;
- nintent migrations `0015_compute_platform_instance_and_endpoint_mac.py` and
  `0016_remove_reconciliation_dashboard_surfaces.py`;
- nctl's current README, output/compatibility/event documentation, command help, and configuration;
- the exact backup, image, container, database, and generated-dashboard metadata used below; and
- all current source/tests/config/docs covered by the deletion searches in the parent roadmap.

Later reports and the refactoring vision supersede historical plans where they conflict. Historical
artifacts remain evidence; they are not silently promoted to current truth.

### 2.1 Planning-time repository snapshot

Observed read-only before adding this plan:

| Repository | Revision | State |
|---|---|---|
| superproject | `02e9494cf38060aa10e02ed7f23c3d4c4de23da8` | clean; equal to `origin/main`; commit deletes an earlier `p5/report.md` |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean; equal to `origin/main`; final CLI-only/VM query revision |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean; equal to `origin/main`; final cache-free schema/docs revision |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean; unchanged |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean; unchanged |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean; unchanged |

The final report must record the actual starting and ending state again. Preserve unrelated user
changes if any worktree becomes dirty before implementation.

### 2.2 Planning-time live snapshot

Read-only inspection found:

- `nautobot-nautobot-1`, `nautobot-nautobot-worker-1`, and
  `nautobot-nautobot-scheduler-1` all report healthy;
- the web container contains nintent `c343c5a56047b0df9ad901dd4459863ef1954053`;
- the worker and scheduler containers each contain old nintent
  `ad9d36397d23c269ad748e13acbccc532fa29f52`;
- the three containers use three independently tagged Compose images, so rebuilding only the
  `nautobot` service cannot prove that worker and scheduler received the same package;
- live migrations show both `0015` and `0016` applied;
- the four `reconciliation_status`/`reconciliation_checked_at` columns are absent from the two
  live tables;
- no matching error/traceback line appeared in a narrow 30-minute log search, but this is not proof
  that the old worker/scheduler code is schema-compatible or that a relevant Job path ran;
- no process listens on TCP port 8300; and
- `/Users/eiji/.local/state/nctl/dashboard/` still contains `index.html` and `drift.json`.

The worker/scheduler mismatch is a blocking deployment defect even while Docker health checks are
green. Phase 5 cannot be complete until the package commit is verified inside every running
service container.

### 2.3 Already-performed migration and backup state

Git history contains commit `bff19abc7eff5c71b98f0b9f5fb6e69830e441f8`, which added an early
Phase 5 report for a local container update, followed by
`02e9494cf38060aa10e02ed7f23c3d4c4de23da8`, which deleted that report. The deleted report is useful
historical orientation, but its claims must be reverified; it is not the final Phase 5 report and
must not be restored verbatim.

Planning-time checks confirmed:

- `.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump` exists;
- it is mode `0600`, size 1,772,665 bytes;
- its planning-time SHA-256 is
  `622e9feb09eb7047aa10591a6c91ad6713252af45c7c0c714c93cb41f7c9eb96`;
- `pg_restore --list` succeeds when executed through the PostgreSQL container; and
- the live web package and schema match the target, while worker/scheduler do not.

The earlier execution did not record a formal desired-write/Job closure, a separate pre-migration
legacy-link count, or final reconciliation-cache counts before applying the migration. It also
mistook container recreation for package parity. The new report must state those facts. It may
reconstruct aggregate pre-migration facts from a disposable restore of the backup, but must not
rewrite that reconstruction as evidence captured before the original migration.

For orientation only, the roadmap's Phase 0 baseline recorded all five DesiredNodes as cached
`converged`, one of six DesiredServices as cached `converged`, and the other five service cache
values as blank. Step 1 must query the backup rather than copying those older counts forward.

### 2.4 Migration semantics that constrain this plan

Migration `0015`:

- creates the final compute platform/instance schema and desired endpoint MAC field;
- runs `assert_no_legacy_realized_vm()` inside the migration transaction;
- refuses to drop `DesiredNode.realized_vm` when any legacy link is non-null; and
- then removes the legacy link/source columns.

Because live `0015` is recorded as applied and the removed legacy columns are absent, its
in-transaction assertion necessarily returned successfully at migration time. This does not prove
that a separate pre-window count was captured or that writes were formally closed before startup.

Migration `0016` removes the four disposable dashboard-derived cache fields without translating
their values. Reversing it can recreate empty columns but cannot reconstruct the discarded cache.
Exact rollback therefore restores the pre-window database backup and the complete prior code tuple;
it does not reverse `0016` in place and pretend the old cache values survived.

### 2.5 Frozen final and rollback tuples

Final tuple prepared by Phase 4:

| Repository | Final revision |
|---|---|
| nctl | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` |
| nintent | `c343c5a56047b0df9ad901dd4459863ef1954053` |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |

The last known pre-VM-Phase-3 matched source tuple is:

| Repository | Rollback revision |
|---|---|
| superproject | `5424920` (VM Phase 3 Step 0 snapshot) |
| nctl | `fd9cb878a1cdab9a436e7d125d2e5697badc1fc4` |
| nintent | `ad9d36397d23c269ad748e13acbccc532fa29f52` |
| database | backup above, schema/migrations through `0014_braindump_exchange_diary` |

Implementation must reverify ancestry and availability. The final branch is not changed to support
both tuples. Rollback means temporarily restoring the entire old tuple; fix-forward means making
all services use the final tuple.

### 2.6 Phase 4 measurement baseline

Use the exact Phase 4 scopes when comparing the final state:

| Metric | Phase 4 value |
|---|---:|
| nctl top-level commands | 11 |
| nctl collected pytest cases | 954 |
| nctl tracked Python source lines (`src/`) | 17,763 |
| nctl tracked test lines (`tests/`) | 19,380 |
| nintent local Django-free tests | 187 |
| nintent full Nautobot App tests | 252 |
| nintent non-test Python lines including migrations | 9,560 |
| nintent test lines | 4,029 |
| nintent template lines | 1,327 |
| nintent numbered migrations | 16 |
| current-document set | 5,417 lines |

nctl's direct dependencies are `typer`, `httpx`, `pydantic`, and `pyyaml`; the development group is
`pytest` and `respx`; the lock resolved 26 packages with no server-only package. These values are
diagnostics and regression signals, not quotas.

## 3. Scope, non-goals, authority, and sequencing

### 3.1 In scope

- audit the already-applied migration and incomplete container rollout;
- validate the pre-window backup without restoring it over the live database;
- reconstruct missing pre-migration aggregate evidence in a disposable PostgreSQL environment
  where practical;
- create a fresh post-migration recovery snapshot before further live mutation;
- open a bounded maintenance window with explicit operator approval;
- stop desired writes, import Jobs/workers, scheduler activity, and routine nctl use;
- build all three Compose service images from the exact pushed nintent revision;
- verify the package revision inside each image before recreation and inside each container after
  recreation;
- restore one final matched nintent/nctl/schema combination;
- run migration/model/schema, UI, REST, GraphQL, VM-cutover, nctl, ops, and Braindump smoke checks;
- prove dry reconcile evidence without apply, SSH, Ansible, observation, ingest, or desired writes;
- prove both removed commands fail normally and no former server listener exists;
- rerun deletion searches, tests, dependency/package checks, and measurements;
- archive or remove only the known generated dashboard directory after a separate approval;
- resume ordinary operation only after all gates pass; and
- create one new authoritative `p5/report.md`.

### 3.2 Out of scope

- VM Phase 3 canonical seed preparation, approval, import, repeat-import proof, or Steps 9–12;
- any `nctl reconcile --yes`, direct apply, Ansible run, nodeutils collection, Nautobot ingest, SSH
  enrollment, or host actuation;
- creating compute intent, linking actual Cluster/VM objects, or modifying Proxmox;
- changing desired node, service, endpoint, MAC, IPAM, lifecycle, or Braindump content;
- changing the nctl/nintent final contract to accommodate the current mixed deployment;
- editing migration history or generating a `0017` solely to make this rollout pass;
- restoring the deleted early report as though it were the final report;
- adding runtime compatibility readers, old fields, aliases, routes, config keys, or a second
  schema;
- deleting old operation logs, reconcile artifacts, SSH trust data, or the broader nctl state
  directory;
- reading or copying dashboard HTML/JSON content into evidence;
- exposing secrets, raw database rows, private Braindump prose, provider payloads, or key material;
  and
- broad cleanup or refactoring unrelated to the deployment.

### 3.3 Approval gates

Writing this plan authorizes no live mutation. Implementation requires:

1. **Maintenance-window approval** before stopping containers/Jobs, taking the new live backup,
   rebuilding/recreating services, or performing authenticated live smoke activity.
2. **Dashboard disposition approval** after all retained-path verification passes. The default
   proposal is a reversible archive/move of exactly the known directory; permanent deletion
   requires explicit deletion authority.
3. **Rollback approval** if final-container parity or live verification fails and fix-forward cannot
   be completed safely. Database restore is destructive to post-backup state and must not start
   implicitly.
4. **Resume approval/confirmation** after the final gate, including acknowledgement that VM Phase 3
   seed work remains separate.

Read-only rechecks, local tests, local searches, checksum calculation, and disposable-container
backup validation may run before the maintenance window, provided they do not expose protected
content.

### 3.4 Required sequence

Because the database is already final while two services are old, prefer bounded fix-forward:

```text
read-only audit
  -> validate/reconstruct backup evidence in isolation
  -> operator approves maintenance window
  -> quiesce all Nautobot service paths
  -> take a fresh post-migration recovery snapshot
  -> build all three images without cache
  -> verify target commit inside every image
  -> recreate all three containers with verified images
  -> verify target commit inside every running container
  -> schema/UI/API/nctl/ops/Braindump/VM smoke checks
  -> separate dashboard archive/removal approval
  -> final searches/tests/measurements
  -> resume and report
```

Do not run migration `0015` or `0016` again as a staged action. A no-op `migrate --plan` or
`showmigrations` check is allowed; a second no-op migrate invocation is unnecessary evidence.

## 4. Frozen Phase 5 contracts

### 4.1 Matched-container contract

The web, worker, and scheduler are one deployed application even though Compose assigns three image
tags. Completion requires, for each service:

- recorded image tag and immutable image ID;
- installed `nautobot-intent-catalog` version;
- installed VCS commit from distribution metadata;
- running container ID/start time/health;
- exact target commit `c343c5a...`; and
- no relevant startup/schema/import error after the final recreation.

Docker `healthy`, a shared Dockerfile, a successful web check, or `--force-recreate` alone is not
package-parity proof.

Build every service explicitly:

```text
nautobot
nautobot-worker
nautobot-scheduler
```

Use `--no-cache`, capture each resolved Git SHA, inspect the package in each built image before
recreation, then use `up --no-build --force-recreate` so startup cannot silently substitute an
unverified build.

If any build resolves a different nintent SHA, stop before recreation. Do not accept the current
tip of a moving branch merely because it is newer.

### 4.2 Database and migration contract

The final database contract is:

- migrations through `0016`, exactly once in normal Django history;
- migration `0009` retained;
- no reconciliation cache columns on DesiredNode or DesiredService;
- no legacy `DesiredNode.realized_vm(+_source)` columns;
- final DesiredComputePlatform/DesiredComputeInstance tables and constraints present;
- DesiredEndpoint MAC field/constraint present;
- no unplanned migration according to `makemigrations --check --dry-run`; and
- no desired compute rows introduced by this phase.

The report must separate:

- **observed live post-state**;
- **guaranteed by successful in-transaction migration assertion**;
- **reconstructed from the pre-window backup**; and
- **not observed at the original time**.

An empty desired compute collection is the expected VM Step 8 cutover state, not proof of the later
seed path.

### 4.3 Backup and evidence-reconstruction contract

Validate the existing pre-window dump by:

1. recording path, owner/mode, size, checksum, and `pg_restore --list` result;
2. restoring it only into an isolated disposable PostgreSQL container/database;
3. confirming migration state through `0014`;
4. querying only aggregate counts needed for the missing gates:
   legacy realized-VM link/source usage, reconciliation-cache status/checked-at counts by model,
   and desired compute table absence;
5. recording aggregate results without copying row bodies or secrets;
6. destroying the disposable database/container after validation; and
7. retaining the original dump unchanged.

If full restore fails, record the exact failure. A successful TOC listing is useful but is not a
substitute for restore proof. Do not test the dump by restoring over `my_postgres_db`.

Before corrective recreation, take a second custom-format backup of the current `0016` live
database to a new Phase 5 evidence directory. This is a recovery point for container correction,
not a substitute for the pre-window rollback dump.

### 4.4 Retained CLI/evidence contract

The supported surface remains:

- fresh `nctl status`, `actual`, and `drift`;
- deterministic `render hosts-intent`, `render production`, and `render dnsmasq`;
- dry `nctl reconcile` planning;
- JSONL operation events and operation artifacts;
- `nctl ops list/show`;
- Braindump `list/show` structural reads; and
- the existing lock, terminal states, summaries, final drift, and operation IDs.

The dry reconcile is expected to write only bounded local operation evidence. It must:

- run without `--yes`;
- record mode/scope/operation ID/plan;
- execute zero actions;
- make zero SSH, Ansible, nodeutils, ingest, desired-state, or host mutations;
- be readable through `ops show`; and
- not contain a `dashboard` field or cause HTML/status-PATCH side effects.

Do not require live cluster convergence. Existing unrelated drift must be recorded separately from
deployment regressions.

### 4.5 UI, REST, GraphQL, and Braindump contract

Positive live checks must prove:

- normal DesiredNode and DesiredService list/detail UI pages render for an authenticated operator;
- no reconciliation status row/column/filter or dashboard navigation/link appears;
- the removed redirect route is absent;
- REST node/service responses omit the four cache fields;
- ordinary retained REST resources remain readable;
- GraphQL DesiredNode/DesiredService and final compute roots are available;
- GraphQL introspection does not expose the removed cache fields or legacy node VM fields;
- Braindump list/show paths retain their envelope/field structure; and
- no Braindump body, Alignment Review prose, token, or auth header is copied into tracked or private
  deployment evidence.

A token-only `302` to the login page does not prove that an authenticated UI page rendered.
Use an existing operator-authenticated browser/session where possible. If a temporary test session
must be created, disclose the session write and remove only that session afterward.

### 4.6 Removed-surface contract

Prove all of the following:

- `nctl --help` lists the retained 11-command surface and no `dashboard`/`serve`;
- invoking each removed command exits with Typer's normal unknown-command behavior;
- no FastAPI, Starlette, uvicorn, WebSocket, serve extra, template, or dashboard module is installed
  in nctl;
- no in-memory subscriber bus or server runner is present;
- no dashboard config, serve config/token, cache field, redirect, navigation link, or setting is
  active;
- no process listens on port 8300; and
- the known stale dashboard output path is absent after its approved disposition.

Do not create a temporary compatibility command or route to produce a friendlier error.

### 4.7 Dashboard-directory disposition contract

The only cleanup target is:

```text
/Users/eiji/.local/state/nctl/dashboard
```

Before action, resolve that exact path, confirm it is a directory rather than a symlink, and record
only its entry names/sizes. Do not open `index.html` or `drift.json`.

The default safe action is to move the whole directory atomically into the private Phase 5 evidence
directory as `retired-dashboard/`, with the containing directory mode `0700`. This is reversible
and removes the stale output from its formerly served/current-looking location. Permanent deletion
is allowed only if the operator explicitly chooses deletion.

Never target `/Users/eiji/.local/state/nctl`, operation directories, event logs, reconcile locks,
SSH trust stores, or a path derived from an unresolved variable/glob.

### 4.8 Reporting truth contract

The new `p5/report.md` is authoritative only for the execution performed under this plan. It must:

- mention the earlier out-of-sequence migration/container update and deleted report;
- record that the web/worker/scheduler mismatch was found during planning;
- never label reconstructed backup aggregates as contemporaneous pre-migration observations;
- never claim a path passed because no error was seen when the path did not run;
- distinguish exact positive proof from inherited Phase 3/4 evidence;
- state whether a temporary authenticated session or local operation evidence was written;
- state every skipped, failed, substituted, reconstructed, or deferred check;
- keep VM Phase 3 Steps 9–12 explicitly pending; and
- use `complete`, `partially complete`, `implemented, not fully deployed`, or `rolled back`
  accurately.

## 5. Safety and evidence handling

### 5.1 Private evidence directory

Create:

```text
.local/remove-unused-surfaces/p5/<timestamp>/
```

Use directory mode `0700` and file mode `0600`. Suggested evidence files:

```text
revisions-start.txt
live-start.txt
container-package-parity-before.tsv
pre-backup-metadata.txt
pre-backup-restore-aggregates.txt
post-migration-backup-metadata.txt
running-jobs-before.txt
build-images.tsv
build-resolved-shas.txt
container-package-parity-after.tsv
migration-schema-checks.txt
ui-rest-graphql-smoke.txt
vm-cutover-smoke.txt
nctl-retained-smoke.txt
nctl-removed-smoke.txt
ops-structural-smoke.txt
braindump-structural-smoke.txt
listener-and-process-check.txt
deletion-search-final.tsv
tests-and-measurements.txt
dependencies-and-plain-install.txt
dashboard-disposition.txt
rollback-commands-and-tuples.txt
resume-and-final-state.txt
```

The old backup may remain in its current private location. Record its path/checksum; do not copy it
unnecessarily.

### 5.2 Content that must not be recorded

Do not print or store:

- `.local/secrets` or any Nautobot/API/serve token;
- authentication headers, passwords, cookies, or session IDs;
- raw database rows, full dump contents, or unrestricted table exports;
- Braindump bodies, Alignment Review prose, titles that reveal private intent, or user-authored
  free text;
- dashboard HTML/JSON contents;
- private keys, raw SSH keys, vault data, or known_hosts contents;
- provider credentials or unrestricted Proxmox payloads;
- full generated production inventories in tracked reports; or
- unrelated operation artifact contents.

Private evidence may contain narrowly scoped JSON/schema/status output needed for verification, but
the tracked report contains only summaries, counts, hashes, public IDs where necessary, and
redacted command results.

For Braindump and operation checks, parse JSON in memory and emit only schema name, `ok`, counts,
field presence/types, terminal state, and a hash or redacted identifier. Do not tee raw output.

### 5.3 Allowed mutations under this plan

After the relevant approval, the allowed mutations are:

- stop/start/recreate the three Nautobot application containers;
- build/tag verified local Docker images;
- create one new post-migration database backup;
- create and destroy an isolated disposable PostgreSQL restore environment;
- create a temporary authenticated UI session only if necessary, then remove it;
- create one dry-reconcile operation and its normal local evidence;
- archive or explicitly delete the exact dashboard directory;
- add the Phase 5 plan/report and normal evidence-independent Git commits; and
- temporary build/test files with explicit cleanup.

No desired/actual/Braindump/provider/host mutation is authorized.

## 6. Verification design

### 6.1 Container parity proof

Run package inspection twice:

1. against each built image before it can replace a running container; and
2. against each final running container.

For every row, compare:

```text
service
image tag
image ID
container ID
package version
package VCS commit
health
```

All three VCS commits must equal `c343c5a...`. The final report must show three explicit rows, not
"all containers use the same Dockerfile."

### 6.2 Schema and migration proof

Use Django migration commands and direct PostgreSQL catalog queries to prove:

- exact applied migration list;
- no pending model migration;
- cache and legacy columns absent;
- final compute/MAC tables, columns, indexes, and named constraints present;
- no cache/status rows can be queried because the columns no longer exist;
- no desired compute rows were created by deployment; and
- migration history `0009` remains intact.

Catalog queries should select names/counts only. Do not dump model rows.

### 6.3 Live UI/API proof

Use positive assertions rather than only status codes:

- authenticated UI response is 200 and contains the expected retained page heading/object identity;
- removed status labels/dashboard links are absent from rendered HTML;
- REST JSON has retained identifiers and lacks removed keys;
- GraphQL returns non-empty ordinary roots where live data exists;
- final compute roots are queryable even when empty;
- introspection lacks removed/legacy fields; and
- dashboard redirect reverses to no route or returns the expected not-found behavior.

If a UI detail object is selected, record only its public slug/ID, not unrelated field contents.

### 6.4 nctl retained-path proof

Run from the repository root with the documented project form:

```text
uv run --project nctl nctl status --json
uv run --project nctl nctl actual --json
uv run --project nctl nctl drift --json
uv run --project nctl nctl render hosts-intent --json
uv run --project nctl nctl render production --json
uv run --project nctl nctl render dnsmasq --json
uv run --project nctl nctl reconcile --json
uv run --project nctl nctl ops list --json
uv run --project nctl nctl ops show <new-dry-operation-id> --json
uv run --project nctl nctl ops show <pre-existing-operation-id> --json
uv run --project nctl nctl braindump list --json
uv run --project nctl nctl braindump show <existing-id> --json
```

Confirm exact option placement from current `--help` before execution. Do not add `--out`,
`--yes`, `--refresh-observation`, or any apply command.

For renders, assert schema, success, object counts, warnings/findings, and deterministic digest
where exposed. Do not install generated artifacts.

For dry reconcile, assert the intended planner path actually ran and an operation ID exists. A
manual-review or planned terminal result is acceptable when caused by current drift; execution or
host actuation is not.

For `ops show`, prove both a new final-schema dry operation and an older historical operation remain
readable. A historical `result.json` containing an old self-contained dashboard field must not be
rewritten or migrated.

For Braindump, run list/show but emit only structural assertions so private prose never enters
evidence.

### 6.5 VM Phase 3 cutover proof

This phase owns only VM Step 8 deployment checks:

- final GraphQL compute roots exist;
- final REST/UI compute paths resolve;
- desired compute collections are empty unless an already-approved seed exists unexpectedly, in
  which case stop and classify the divergence;
- legacy node VM fields are absent;
- ordinary desired snapshot and drift parse successfully with final nctl;
- production, hosts-intent, and dnsmasq read/render paths work;
- actual-link fields remain non-writable through ordinary REST/YAML/UI;
- no compute/Proxmox action is planned;
- any desired-MAC blocker remains manual-review/scoped; and
- no SSH/Ansible/Proxmox boundary is invoked.

Do not perform VM Steps 9–12 or claim their seed/repetition/environment-backed proofs.

### 6.6 Tests, package proof, searches, and measurements

Repeat:

- full nctl pytest suite and collection count;
- `uv lock --check`;
- nintent local Django-free suite;
- full Nautobot App test suite in an isolated/test environment, or explicitly justify inheritance
  only if the deployed source is byte-identical to the already-proven runtime revision;
- clean plain nctl wheel build/install/import/help proof;
- direct and locked dependency inventory;
- source/test/template/current-doc line counts using Phase 4's exact scopes;
- all parent-roadmap deletion tokens across current source/tests/config/docs;
- installed nctl module/dependency absence checks; and
- installed nintent field/route/config absence checks.

The live smoke test is not a substitute for automated tests, and a smaller code/test count is not
proof of correctness.

### 6.7 Required deletion searches

Search at least these exact tokens across active source, tests, configuration, installed packages,
and current documentation:

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

Also search structurally for:

- `fastapi`, `starlette`, `uvicorn`, `websocket`, `serve` extras, and ASGI route/application code
  within nctl's owned package/dependency surface;
- subscriber registries, callback queues, worker-thread delivery, and server-only artifact readers;
- dashboard templates/assets, HTML/drift writers, status PATCH calls, and reconcile dashboard data;
- nintent model/filter/table/template/view/URL/navigation/config/serializer surfaces related to
  the removed cache/link; and
- active instructions that describe the removed behavior without using an exact token.

Allowed final matches are limited to migration history, explicit negative tests, this initiative's
roadmap/plan/report evidence, clearly superseded historical material, and proven unrelated
substrings or other-component implementations. Every remaining row needs file, line, category, and
reason.

## 7. Rollback design

### 7.1 Rollback triggers

Stop and choose fix-forward or rollback if:

- any built or running service contains a non-target nintent commit;
- any required container cannot become healthy;
- a schema/model mismatch, missing table/constraint, or unexpected migration appears;
- worker/scheduler logs show repeatable undefined-column/model import failures;
- retained UI/REST/GraphQL/nctl paths fail because of the deployment;
- desired compute data unexpectedly exists before the seed phase;
- a dry command crosses an SSH/Ansible/write boundary;
- the pre-window backup cannot be validated and another reliable exact rollback path is not
  available; or
- any secret/private prose enters an evidence file.

Unrelated pre-existing cluster drift is not itself a rollback trigger.

### 7.2 Preferred fix-forward

Because the database is already at `0016`, the first safe response to the current mismatch is to
build and run the exact final nintent image in all three services. Do not restore old cache fields
or add dual readers to make old workers tolerate the final schema.

If a final image is correct but one service recreation failed, keep the maintenance window closed,
fix that exact service, and repeat full three-row parity checks.

### 7.3 Exact rollback

If rollback is approved:

1. keep desired writes, workers, scheduler, Jobs, and routine nctl stopped;
2. take and retain a failure-state backup for forensic comparison;
3. verify the pre-window backup checksum and disposable-restore result;
4. stop all three Nautobot application containers;
5. drop/recreate only the confirmed Nautobot database and restore the pre-window custom dump;
6. build or use an immutable image explicitly pinned to nintent
   `ad9d36397d23c269ad748e13acbccc532fa29f52`;
7. do not rely on the unpinned GitHub default branch in `Dockerfile` for rollback;
8. recreate web, worker, and scheduler from the same verified old package revision;
9. activate nctl `fd9cb878a1cdab9a436e7d125d2e5697badc1fc4` for routine old-schema operations;
10. verify migrations through `0014`, legacy/cache schema and aggregate values, all container
    package commits, retained old-tuple operations, and health;
11. resume only after the whole old tuple is matched; and
12. report `rolled back`, preserving all failure evidence.

Do not use `migrate 0014` plus reverse `0016` as exact rollback: it cannot reconstruct discarded
cache values. Do not modify Proxmox, actual Cluster/VM rows, desired intent, or host artifacts
during rollback.

## 8. Procedure

### Step 0 — Reconfirm the partial-deployment baseline

1. Record root/submodule HEADs, upstreams, dirty files, and ownership.
2. Verify final and rollback commits exist and final nintent/nctl commits are reachable from
   `origin/main`.
3. Read Phase 4's final report and VM Phase 3 reports 3.6/3.7.
4. Inspect Git history for the added-then-deleted early `p5/report.md`; do not restore it.
5. Record all three container IDs, image IDs, health, start times, package versions, and package VCS
   commits.
6. Record live migrations, relevant schema names, desired-compute aggregate counts, and running/
   queued Job aggregates.
7. Check relevant logs from each service since its current start time.
8. Confirm no port-8300 listener or removed server process.
9. Record the dashboard path type, entry names, and sizes without reading content.
10. Confirm the pre-window backup path/mode/size/checksum and that `.local/` is ignored.
11. Create the new private evidence directory and retention note.
12. Confirm no live mutation occurred during Step 0.

Gate: the exact mixed state is documented; no healthy-status shortcut hides package mismatch; no
unowned dirty change or unexpected live activity is ignored.

### Step 1 — Validate backup and reconstruct missing pre-migration aggregates

1. Run `pg_restore --list` through a compatible PostgreSQL 15 tool and record success/failure.
2. Start an isolated, unexposed, disposable PostgreSQL 15 container with a task-specific temporary
   name and credential.
3. Restore the existing pre-window dump with appropriate no-owner/no-ACL handling.
4. Verify restored nintent migration history ends at `0014`.
5. Query aggregate-only legacy realized-VM link/source counts.
6. Query aggregate-only reconciliation cache counts by model/status and non-null checked-at count.
7. Confirm final compute tables/migration `0015` are absent in the restored database.
8. Record aggregates as `reconstructed from backup`, not `observed before migration`.
9. Stop and remove only the exact disposable container/volume after verifying its identity.
10. Recompute the original dump checksum and prove it is unchanged.
11. Record any restore warning, extension/owner issue, or omitted aggregate.

Gate: rollback media is restore-proven and missing aggregate evidence is reconstructed honestly, or
the inability to do so is explicit and blocks an unqualified completion/rollback claim.

### Step 2 — Open the approved maintenance window and create a current recovery point

This step requires maintenance-window approval.

1. Record the approval, start timestamp, operator, and allowed mutation scope.
2. Stop routine nctl commands and communicate/confirm the desired-write freeze.
3. Recheck active/running import Jobs and scheduled activity.
4. Stop the scheduler and worker first, then stop the web service so no new UI/API desired write
   can begin.
5. Confirm all three application containers are stopped and no import Job remains executing.
6. Create a fresh custom-format backup of the current `0016` database in the new evidence
   directory.
7. Set mode `0600`, compute SHA-256, and validate its TOC listing.
8. Record current database/container/image state and exact rollback/fix-forward commands before
   rebuilding.

Gate: all application write paths are quiesced, both recovery points are identified, and no
container rebuild/recreation has begun without approval.

### Step 3 — Build and verify all three final images

1. Reverify nintent `origin/main` still contains the exact target revision.
2. Build `nautobot`, `nautobot-worker`, and `nautobot-scheduler` explicitly with `--no-cache`.
3. Capture the resolved Git commit from each build log.
4. Record each resulting image tag and immutable image ID.
5. Run package metadata inspection in each stopped image without starting the application.
6. Require all three installed VCS commits equal `c343c5a...`.
7. Verify the old rollback image/commit remains identifiable, or record the exact pinned rebuild
   procedure.
8. If any SHA differs, do not recreate containers; keep the window closed and resolve the build.

Gate: three separately named images are package-proven before any final service starts.

### Step 4 — Recreate the matched application and verify startup

1. Recreate all three services together using `--no-build --force-recreate`.
2. Wait for the web health check and dependent worker/scheduler startup.
3. Record final container/image IDs and health.
4. Inspect installed package version and VCS commit inside each running container.
5. Require three exact `c343c5a...` rows.
6. Record relevant logs from each new start time and fail on schema/import/startup errors.
7. Confirm no old service container or unexpected duplicate worker/scheduler remains.
8. Confirm migrations did not advance beyond `0016`.

Gate: web, worker, and scheduler are one exact nintent revision against one final schema.

### Step 5 — Prove migration, VM cutover, UI, REST, and GraphQL post-state

1. Run `showmigrations` and `makemigrations --check --dry-run`.
2. Run the narrow catalog/schema assertions from §6.2.
3. Assert desired compute platform/instance counts match the expected pre-seed state.
4. Query final GraphQL ordinary and compute roots; prove removed/legacy fields are absent.
5. Query retained REST node/service/compute resources; prove removed fields are absent.
6. Prove ordinary REST/YAML/UI inputs cannot write actual links.
7. Perform authenticated DesiredNode/DesiredService list/detail UI checks.
8. Prove status rows/filters/dashboard navigation/link/redirect are absent.
9. Run the VM Step 8 desired snapshot plus hosts-intent/production/dnsmasq read checks without
   writing generated files.
10. Assert no compute/Proxmox action and no SSH/Ansible boundary appears.
11. Record any current desired-MAC finding separately; do not weaken its blocker classification.
12. Clean up only a temporary authentication session created specifically for this proof.

Gate: final schema and all retained Nautobot surfaces work positively; no seed or actuation occurred.

### Step 6 — Prove retained nctl, operation evidence, and Braindump paths

1. Run the status/actual/drift/render commands in §6.4.
2. Parse and record their schema, success, counts, and scoped warnings/findings.
3. Run one dry reconcile without `--yes` and record its operation ID.
4. Positively assert planner execution, mode, target scope, zero executed actions, zero preflight/
   Ansible/nodeutils/ingest side effects, and no dashboard field/write.
5. Read the new dry operation through `ops list/show`.
6. Read one pre-existing historical operation through `ops show`.
7. Run Braindump list/show through a redacting structural wrapper.
8. Confirm no private prose/raw artifact entered evidence.
9. Re-run container error logs after these live reads.

Gate: every retained inspection path named by the roadmap ran, the target dry planner path produced
evidence, and no live actuation or private-data leak occurred.

### Step 7 — Prove removed behavior and disposition the generated dashboard

1. Record `nctl --help` and its exact retained command set.
2. Invoke `nctl dashboard` and `nctl serve` separately; require normal unknown-command exit/code/
   wording.
3. Prove deleted modules/assets/config/schema/dependencies are absent from the local installation.
4. Prove installed nintent lacks cache/link/redirect/config behavior.
5. Confirm no former server process or port-8300 listener.
6. Resolve and validate the exact dashboard directory as specified in §4.7.
7. Present archive versus permanent-delete disposition to the operator.
8. After separate approval, archive/move the exact directory by default, or delete only if
   deletion was explicitly selected.
9. Confirm the original dashboard path is absent and unrelated nctl state entries are unchanged.
10. Record recoverability and destination if archived.

Gate: removed runtime behavior is absent and stale generated output is no longer at the live-looking
path, without touching broader state.

### Step 8 — Run final tests, searches, package proof, and measurements

1. Run the full nctl suite and `uv lock --check`.
2. Run the nintent local suite and the applicable isolated full Nautobot App suite.
3. Build/install a clean plain nctl wheel and repeat import/help/dependency absence proof.
4. Run every required deletion token search over current runtime, config, tests, migrations,
   current docs, and history as separate scopes.
5. Classify all remaining matches as migration, historical, negative-test, initiative-evidence, or
   unrelated substring; unexplained active matches fail the gate.
6. Remeasure all Phase 4 §2.6 scopes and record differences.
7. Confirm current docs still name only drift/reconcile/artifacts/ops inspection paths.
8. Run `git diff --check` in every changed repository.
9. Remove only validated temporary build/test/restore state.
10. Recheck worktree ownership and preserve unrelated changes.

Gate: retained tests/package checks pass, final searches have no unexplained active match, and all
measurements are repeatable diagnostics.

### Step 9 — Resume operations and freeze the final tuple

1. Re-run the three-container package parity table and health/log checks.
2. Re-run migration and port-8300 checks.
3. Confirm no import/reconcile/apply/Ansible/host action remains running from verification.
4. Confirm the dashboard source path remains absent after approved disposition.
5. Record exact root/submodule, image, container, installed-package, migration, database-backup, and
   operation-evidence identifiers.
6. Compare final state with Phase 0 and Phase 4 baselines.
7. Obtain resume confirmation and end the maintenance window.
8. Confirm ordinary web/worker/scheduler operation after resume without triggering a mutation-only
   Job for proof.
9. Record VM Phase 3 Steps 9–12 as the next separate handoff.

Gate: only the final matched tuple is active, all approved services are resumed, and no deferred VM
seed work is misreported as complete.

### Step 10 — Produce one authoritative Phase 5 report

Create `p5/report.md` containing:

- precise status and execution timestamp/window;
- private evidence directory and retention owner;
- starting/ending root and submodule revisions plus dirty-state ownership;
- the planning-time mixed web/worker/scheduler discovery;
- the earlier out-of-sequence migration/update and deleted-report history;
- pre-window backup metadata, restore proof, checksum, and reconstructed aggregate labels;
- fresh post-migration recovery backup metadata;
- exact maintenance approval, quiesce, and resume facts;
- three-row build-image and running-container package parity tables;
- exact migration/schema/model proof;
- VM Step 8-only proof and explicit Steps 9–12 deferral;
- authenticated UI, REST, and GraphQL results;
- retained nctl/drift/render/dry-reconcile/ops/Braindump results;
- positive proof the dry planner ran and executed nothing;
- removed-command/module/config/dependency/listener results;
- dashboard archive/delete approval, exact target, outcome, and recoverability;
- test results, deletion-search exceptions, dependencies, and before/after measurements;
- final matched and rollback tuples;
- confirmation of no desired/actual/Braindump/Ansible/SSH/host/Proxmox mutation;
- every reconstruction, inheritance, omission, substitution, failure, warning, and deferred item;
  and
- an exit-criteria table with evidence references.

The report may name the implementation/root revision it describes but must not invent the hash of
its own future commit. Commit/push remains subject to the repository's normal user-controlled push
workflow.

## 9. Verification matrix

| Area | Required proof |
|---|---|
| Repository tuple | exact final revisions present and remotely available; unrelated work preserved |
| Backup | pre-window dump checksum/TOC/full disposable restore; current recovery dump checksum/TOC |
| Missing pre-gate evidence | legacy/cache aggregates reconstructed and labeled as reconstruction, or explicit gap |
| Maintenance | approval, write/Job/routine-nctl closure, start/end, and resume recorded |
| Images | three explicit image tags/IDs contain exact target nintent commit before recreation |
| Containers | three explicit running container rows contain exact target commit and are healthy |
| Migrations | `0015`/`0016` applied; `0009` retained; no pending/unplanned migration |
| Schema | cache and legacy node-VM columns absent; final compute/MAC schema/constraints present |
| VM cutover | final roots/read paths work; pre-seed state; no compute action/SSH/Ansible/Proxmox |
| nintent UI | authenticated node/service pages render; status/filter/nav/link/redirect absent |
| REST/GraphQL | retained reads work; removed cache/legacy fields absent; compute roots available |
| CLI surface | 11 retained commands; removed commands return normal unknown-command errors |
| Drift/render | live JSON/human-supported reads and deterministic renders work without install |
| Reconcile | dry planner actually runs; operation ID/artifacts exist; zero execution/side effects |
| Operation inspection | new and historical operations readable through `ops list/show` |
| Braindump | list/show structural path works without recording private prose |
| Packaging | plain nctl install has no server/dashboard modules/assets/extra/dependencies |
| Events | JSONL/new dry operation terminal evidence works; no subscriber machinery returns |
| Listener | no old nctl process and no TCP 8300 listener |
| Dashboard files | exact known directory archived/removed with approval; broader state untouched |
| Searches | no unexplained active runtime/config/schema/test/current-doc match |
| Tests | nctl and nintent applicable suites pass; no live smoke substitutes for automated proof |
| Measurements | Phase 0/4/final scopes compared; counts treated as diagnostics |
| Secrets | no tokens, cookies, private prose, raw rows/dumps/dashboard contents/keys in reports |
| Rollback | exact old tuple and restore procedure are usable; no compatibility code added |

## 10. Exit criteria

- [ ] The earlier partial deployment and deleted early report are recorded truthfully.
- [ ] The current mixed web/worker/scheduler package state has been eliminated.
- [ ] All three built images and all three running containers independently prove nintent
      `c343c5a56047b0df9ad901dd4459863ef1954053`.
- [ ] nctl `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` is the active matching local revision.
- [ ] The pre-window backup is checksum- and restore-proven without touching the live database.
- [ ] Reconstructed pre-migration aggregates are explicitly labeled as reconstruction.
- [ ] A fresh current-schema recovery backup exists and passes checksum/TOC validation.
- [ ] Maintenance-window approval, quiesce, and resume are recorded.
- [ ] Live migrations end exactly at `0016`, migration `0009` remains, and no model migration is
      pending.
- [ ] The four reconciliation cache columns and legacy DesiredNode VM columns are absent.
- [ ] The final compute/MAC schema and constraints are present.
- [ ] No desired compute seed or actual-link mutation was introduced by this phase.
- [ ] Authenticated DesiredNode/DesiredService UI pages render without removed status/link surfaces.
- [ ] Retained REST and GraphQL paths work and omit removed/legacy fields.
- [ ] VM Phase 3 Step 8 read/cutover checks pass without compute/SSH/Ansible/Proxmox action.
- [ ] `nctl status`, `actual`, `drift`, all three renders, and dry reconcile run successfully or
      expose only explicitly classified pre-existing drift.
- [ ] The dry reconcile positively proves planner execution, operation evidence, and zero executed
      actions.
- [ ] `nctl ops list/show` reads both the new dry operation and historical operation evidence.
- [ ] Braindump list/show works without private prose entering evidence.
- [ ] `nctl --help` has the retained command set and no removed commands.
- [ ] `nctl dashboard` and `nctl serve` return normal unknown-command behavior.
- [ ] No server/dashboard module, asset, schema, config, token, dependency, or subscriber machinery
      is active or installed.
- [ ] No process listens on TCP port 8300.
- [ ] The exact generated dashboard directory was archived or removed with separate approval, and
      broader nctl state is untouched.
- [ ] Final deletion searches contain only classified migration/history/test/evidence exceptions.
- [ ] Applicable nctl/nintent suites, lock check, and plain-wheel proof pass.
- [ ] Final source/test/template/doc/dependency/command counts use the Phase 4 scopes.
- [ ] Exact final and rollback tuples, image IDs, backup checksums, and migration state are recorded.
- [ ] No desired/actual/Braindump/SSH/Ansible/nodeutils/ingest/host/Proxmox mutation occurred.
- [ ] Every omitted, failed, inherited, reconstructed, substituted, optional, or deferred check is
      visible in one final report.
- [ ] VM Phase 3 Steps 9–12 remain explicitly handed off, not silently treated as Phase 5 proof.

Code/schema absence alone is not completion. Completion requires a matched three-container
deployment, positive retained-path evidence, truthful recovery of the missing pre-migration facts,
safe stale-output disposition, and a reproducible final report.

## 11. Handoff after Phase 5

On successful completion, remove-unused-surfaces is complete and hands VM Phase 3:

- one final nintent schema deployed consistently to web, worker, and scheduler;
- one matching nctl desired/query/render contract;
- migrations through `0016`;
- no reconciliation cache, dashboard link, static/live dashboard, server, or subscriber bus;
- retained CLI/disk operation evidence proven live;
- a validated pre-window rollback backup and fresh post-migration recovery point;
- an empty/pre-seed compute intent surface unless separately approved data already existed;
- unchanged desired-MAC safety and no-actuation boundaries; and
- one authoritative Phase 5 final report.

VM Phase 3 may then begin its separately approved Step 9 canonical seed review. Phase 5 does not
authorize that seed, import apply, repeat proof, environment-backed mismatch fixture, or final VM
Phase 3 completion claim.
