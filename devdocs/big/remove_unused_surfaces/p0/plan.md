# Remove Unused Surfaces Phase 0 Implementation Plan: Freeze the Removal Contract and Baseline

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: proposed; read-only audit and documentation phase.

## 1. Goal

Freeze the exact deletion boundary for the unused nctl server/dashboard feature family before
runtime code or the live Nautobot schema changes. Phase 0 also resolves the overlap with the
already-running VM Phase 3 work so that nintent migration `0015`, the new removal migration
`0016`, and the matching nctl revision are not developed or deployed as incompatible tuples.

Phase 0 produces:

1. a current repository and live-environment baseline;
2. an exhaustive, classified manifest of every server/dashboard/cache reference;
3. positive evidence that there is no real consumer visible in the agreed audit boundary;
4. a frozen retained CLI, reconcile, event-log, artifact, and `ops` contract;
5. an amended active VM Phase 3 plan that no longer requires a removed surface; and
6. one final `report.md` that states whether the phase gate passed.

This phase changes tracked documentation only:

- this plan;
- `devdocs/big/vm/p3/plan.md`; and
- `devdocs/big/remove_unused_surfaces/p0/report.md`.

It does not delete runtime code, change dependencies, create migration `0016`, rebuild Nautobot,
run a migration, write desired state, run a Job, invoke Ansible, generate a dashboard, or clean up
the existing dashboard directory.

## 2. Governing inputs and current planning baseline

Before executing this plan, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md`;
- every existing report under `devdocs/big/vm/p3/`, using the latest numbered report as the
  current implementation state;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `nctl/README.md`; and
- `nintent/README.md`.

Historical plans and reports are evidence, not current requirements. Do not edit their narrative
to pretend that the removed features never existed.

### 2.1 Planning-time snapshot

The following was observed while this plan was authored on 2026-07-25. It is orientation only;
Phase 0 execution must recapture it rather than copying it into the final report.

| Repository | Planning-time revision | Planning-time state |
|---|---|---|
| superproject | `4f756f000543162e14a7a9a00e51eac1fe8f75ee` | new refactoring/removal docs untracked |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

The latest VM Phase 3 implementation report is currently `report3.5.md`. Steps 0–5 are reported
complete locally, Step 6 is next, local nintent migration `0015` exists, and the live deployment
is still on migration `0014`. This makes the plan amendment a gate before VM Phase 3 Step 6 is
finished and before its Step 7/8 matched-commit and deployment work.

The planning-time `nctl --help` surface contains:

```text
status
actual
drift
dashboard
reconcile
lifecycle
serve
render
apply
ops
braindump
ssh
session
```

Phase 0 records that surface. It does not remove commands; command deletion begins in Phases 1
and 2.

### 2.2 Known planning-time inventory refinement

The parent roadmap's deletion list is a starting point. The planning scan found one additional
dedicated file:

```text
nctl/tests/test_events_bus.py
```

It tests only the in-memory subscriber registry, worker threads, bounded queues, drop behavior,
callback fan-out, and unsubscribe behavior. Those are server-only contracts. Classify this whole
file as `delete`, while preserving and continuing to test `EventRecord` and `OperationLog` JSONL
writes separately.

Generated `__pycache__` and `.pyc` files are not manifest entries and must not be tracked.

## 3. Authority, sequencing, and collision decision

### 3.1 Coordinated owner

The `remove_unused_surfaces` initiative owns the final shared nctl/nintent removal contract and
the coordination of the matched-version maintenance window. VM Phase 3 continues to own:

- desired compute platform/instance and endpoint-MAC semantics;
- desired-MAC mismatch/ambiguity classification;
- dnsmasq deployable-versus-blocked behavior;
- digest and planner suppression;
- the zero-SSH/zero-Ansible safety boundary; and
- its separately approved seed and non-repetition proofs.

The removal initiative owns:

- deletion of `serve`, both dashboards, and the subscriber bus;
- removal of the four nintent cache fields and dashboard links;
- migration `0016`;
- the dashboard-free reconcile result contract;
- active-documentation contraction; and
- final proof that CLI/disk evidence remains.

Neither initiative independently owns a live deployment of the shared schema/query pair.

### 3.2 Required order after Phase 0

Use this order:

```text
Phase 0
  -> amend VM Phase 3 plan
  -> remove_unused_surfaces Phases 1–3 locally
  -> finish VM Phase 3 Step 6 against the dashboard-free target contract
  -> remove_unused_surfaces Phase 4 + VM Phase 3 Step 7 matched review/commits
  -> one coordinated maintenance window:
       nintent final revision
       migration 0015
       migration 0016
       matching nctl final revision
  -> revised VM Phase 3 Step 8+ and remove_unused_surfaces Phase 5 verification
```

Phase 0 itself does not advance any live gate. If VM Step 6 has already started when this phase is
executed, inventory its edits and rebase its acceptance language onto the frozen contract; do not
discard correct desired-MAC work.

### 3.3 Prohibited mixed states

Do not:

- deploy nintent `0015` without a matching nctl query revision;
- deploy nintent `0016` while an old dashboard writer can still PATCH the removed fields;
- deploy dashboard-free nctl against live nintent merely as a partial rollout and then claim the
  initiative complete;
- let VM Phase 3 Step 7 freeze commits that still import or test dashboard/serve contracts;
- create `0016` by editing `0009` or `0015`;
- add compatibility fields, config aliases, hidden commands, or dual readers to bridge the window;
  or
- begin the live window without user/operator approval, a database backup, and the exact rollback
  tuple.

## 4. Frozen final contract

This section is authoritative for Phases 1–5. A later phase may correct an implementation detail,
but it must not expand the interface without amending this plan and explaining the concrete
consumer.

### 4.1 Removed contracts

The final runtime has none of:

- CLI commands `nctl dashboard` or `nctl serve`;
- schemas `nctl.dashboard.v1` or `nctl.serve.v1`;
- any nctl-owned HTTP, OpenAPI, WebSocket, `/api/v1/*`, or browser dashboard route;
- static `index.html` or dashboard-owned `drift.json` generation;
- dashboard status PATCHes;
- `DashboardConfig`, `ServeConfig`, `[dashboard]`, `[serve]`, `dashboard_url`,
  `NCTL_SERVE_TOKEN`, or a `serve` package extra;
- process-wide event subscribers, subscriber threads, queues, drop behavior, or callbacks;
- `ReconcileData.dashboard`;
- nintent `reconciliation_status` or `reconciliation_checked_at` on DesiredNode or
  DesiredService;
- nintent dashboard navigation, redirect, link context, status table/filter/detail presentation,
  or plugin setting; or
- a replacement daemon, server, cache, TUI, notification path, or "latest snapshot."

Strict configuration remains `extra="forbid"`. After removal, obsolete `[dashboard]` and `[serve]`
sections fail validation; they are not silently ignored or accepted as deprecated keys.

### 4.2 Retained command surface

Retain the existing behavior and supported text/JSON output of:

```text
status
actual
drift
reconcile
lifecycle
render
apply
ops
braindump
ssh
session
```

The final `nctl --help` must omit only `dashboard` and `serve` as part of this initiative. This
plan does not authorize removing another command because a search happens to show low usage.

### 4.3 Final `ReconcileData` field set

Keep schema name `nctl.reconcile.v2` and remove its optional `dashboard` field in place. Do not
introduce `v3` solely for this deletion and do not emit a null or hidden replacement field.

The final top-level `ReconcileData` fields are exactly:

| Field | Retained meaning |
|---|---|
| `operation_id` | correlation ID for JSONL and artifact directory |
| `mode` | plan/apply mode |
| `scope` | exact `PlanScope` |
| `state` | terminal/current reconcile state |
| `event_log_path` | durable JSONL path |
| `artifact_dir` | operation artifact directory |
| `plan_path` | persisted plan |
| `initial_drift_path` | persisted initial drift |
| `final_drift_path` | persisted fresh/final drift |
| `rounds` | `RoundSummary` evidence |
| `manual_review` | structured non-automatic findings |
| `unsupported` | structured unsupported findings |
| `summary` | full-scope status counts |
| `scope_summary` | requested-scope status counts |
| `progress_made` | truthful side-effect/progress flag |
| `ssh_preflight` | structured controller-local SSH evidence |

Retain the current `RoundSummary` fields (`round`, `drift_fingerprint`, `actions`,
`ssh_preflight`) and `ActionResult` evidence. Preserve terminal state calculation, final-drift
refresh, action ordering, progress preservation after side effects, result persistence, and
reconcile locking. No HTML write or status PATCH occurs after terminal state calculation.

Historical `result.json` files containing `dashboard` remain immutable evidence. Do not migrate,
rewrite, or add a compatibility parser for them. `nctl ops` lists them as ordinary artifacts and
does not depend on their old dashboard field.

### 4.4 Retained event contract

Retain `EventRecord` exactly as durable JSONL evidence:

| Field | Type/meaning |
|---|---|
| `ts` | timezone-aware event timestamp |
| `operation_id` | operation correlation ID |
| `op` | operation name |
| `seq` | monotonically increasing per-operation sequence |
| `event` | event vocabulary value |
| `level` | event severity, default `info` |
| `message` | human-readable bounded description |
| `data` | structured event-specific object |

Retain:

- ULID generation;
- `<events.log_dir>/<operation_id>.jsonl`;
- `OperationLog.start()`, `emit()`, and `finish()`;
- append-order JSONL writes;
- write-failure isolation and one warning; and
- operation IDs used to correlate artifacts.

Delete:

- `Subscriber`;
- `_SubscriberEntry`;
- `_subscribers` and its lock;
- `subscribe()`;
- `_publish()`;
- worker threads, bounded queues, callback error/drop warnings, and subscriber tests; and
- the post-write call that publishes an event in memory.

Event persistence must not become conditional on a subscriber, and removal of `_publish()` must
not change the record returned by `emit()`.

### 4.5 Retained operation inspection contract

Retain `nctl_core.operations_index` and `nctl_core.ops_render`, including:

- `nctl.ops.list.v1` with `log_dir` and `operations`;
- `nctl.ops.show.v1` with `log_dir`, `operation`, and `events`;
- `OperationRecord` fields:
  `operation_id`, `op`, `state`, `ok`, `result`, `started_at`, `updated_at`, `last_seq`,
  `event_count`, `corrupt_lines`, `log_path`, `artifact_dir`, and `artifacts`;
- safe operation-ID validation;
- tolerant reading of partial/corrupt JSONL lines;
- indexing an event log, an artifact-only directory, or both;
- recursive artifact name/size listing; and
- read-only behavior that emits no new operation merely because history was inspected.

Delete only the server adapters for public artifact allowlisting, latest-snapshot lookup, HTTP
responses, and server-side operation runners/gates. Do not delete the shared
`OperationArtifacts`, reconcile artifacts, `result.json`, old event logs, or SSH trust state.

### 4.6 Retained inspection path

After removal:

- fresh cluster convergence comes from `nctl drift` / `nctl drift --json`;
- planned and bounded mutation comes from `nctl reconcile`;
- one operation's proof comes from its JSONL and on-disk artifacts;
- operation discovery comes from `nctl ops list/show`; and
- Braindump/Alignment Review remains its existing non-executable user/agent workflow.

Do not imply that `nctl ops` is a freshness cache. It is historical/ongoing operation evidence.

### 4.7 Migration and rollback contract

Keep `0009_reconciliation_status.py` unchanged. Add
`0016_remove_reconciliation_dashboard_surfaces.py` as a separate migration depending directly on
`0015_compute_platform_instance_and_endpoint_mac`.

Migration `0016` removes only the four disposable cache columns. It does not copy their values to
another table, file, custom field, event, or operation artifact. A Django reverse migration may
recreate empty columns, but it cannot reconstruct the discarded timestamps/statuses and therefore
is not the exact operational rollback.

The exact post-window rollback is:

1. stop desired writes and routine nctl operations;
2. restore the database backup taken before `0015`/`0016`;
3. rebuild/restart the prior installed nintent revision;
4. reactivate the prior nctl revision; and
5. verify the restored migration state, cache aggregates, and retained CLI workflow.

Phase 0 records the pre-window tuple and this rule; it does not take the final backup or exercise a
live rollback.

## 5. Evidence location and safety

Create one private evidence directory:

```text
.local/remove-unused-surfaces/p0/<YYYYMMDD-HHMMSS>/
```

Set the directory to mode `0700` and regular evidence files to `0600`. Suggested files:

```text
revisions.txt
worktrees.txt
nctl-help.txt
nctl-command-help.txt
runtime.txt
migrations.txt
jobs.txt
cache-counts.json
dashboard-path.txt
tracked-token-matches.tsv
local-invocation-paths.txt
process-audit.txt
consumer-audit.txt
manifest.tsv
vm-plan-diff.txt
```

The raw directory remains git-ignored. The tracked report may contain revisions, public package
versions, migration names, aggregate counts, file paths, command names, and match classifications.
It must not contain:

- `.local/secrets` contents or a Nautobot token;
- authentication headers;
- a serve token;
- dashboard HTML or `drift.json` contents;
- Braindump bodies, Alignment Review text, shell-history prose, or other private user text;
- private keys or raw SSH public-key blobs;
- full database rows or dumps; or
- unrestricted process environments or command-line arguments that could contain credentials.

Use the configured token file indirectly through nctl or a container-local ORM query. Never place a
token in an argv, evidence command transcript, or tracked report.

## 6. Procedure

### Step 0 — Establish the non-mutation boundary

1. Create the private evidence directory and record its path and permissions.
2. Confirm `.local/secrets`, the evidence directory, `nctl.toml`, generated dashboard output, and
   Python caches are ignored.
3. Record the current date/time/timezone and the name of the operator performing the audit; do not
   record private prose.
4. Confirm that Phase 0 commands are limited to filesystem/process/config/schema reads and tracked
   documentation edits.
5. Before any container command, record the current container names and health. Do not restart a
   container.
6. If a supposedly read-only command would trigger generation, event logging, a Job, dashboard
   status push, or another write, omit it and record the substitution.

Gate: the evidence location is private, secrets remain indirect, and no live or generated state
has changed.

### Step 1 — Record repository and VM Phase 3 state

Record:

```bash
git rev-parse HEAD
git status --short
git submodule status
git diff --submodule=short
```

For each submodule, record `git rev-parse HEAD`, `git status --short`, current branch/upstream, and
whether the superproject gitlink matches. Do not clean or reset any existing change.

Then:

1. list and read every `devdocs/big/vm/p3/report*.md`;
2. identify the highest completed step and any explicitly pending/deferred proof;
3. confirm whether VM Step 6 work has begun since this plan was written;
4. confirm local migration `0015_compute_platform_instance_and_endpoint_mac.py` exists and record
   its dependency; and
5. record whether any uncommitted nctl/nintent edit overlaps a Phase 1–3 deletion/edit path.

If overlapping implementation has begun, stop only the conflicting write work, classify the
existing edits, and amend sequencing. Do not overwrite user or VM initiative changes.

Gate: the report states the exact root/submodule tuple and the real VM Phase 3 handoff point.

### Step 2 — Record the live read-only baseline

Against the running local environment:

1. record Nautobot and Django versions;
2. record `nautobot-intent-catalog` distribution version and its installed Git commit from
   installed metadata/build evidence;
3. run `showmigrations nautobot_intent_catalog`;
4. run `makemigrations nautobot_intent_catalog --check --dry-run`;
5. confirm live `0014`/`0015`/`0016` state rather than assuming the roadmap baseline;
6. count `JobResult` rows in `PENDING` or `RUNNING` and record only count plus public IDs/names if
   nonzero;
7. group DesiredNode and DesiredService rows by `reconciliation_status`, preserving blank/null as
   its own bucket;
8. separately count non-null `reconciliation_checked_at` rows for each model;
9. resolve the dashboard output directory from `Config.load().dashboard.resolved_out_dir()` and
   record its exact path, existence, and only the expected filenames/sizes—not contents; and
10. record the configured deployment `dashboard_url` value as a public local URL without reading
    or displaying any secret setting.

Use an ORM aggregation equivalent to:

```python
Model.objects.values("reconciliation_status").annotate(count=Count("id")).order_by("reconciliation_status")
```

Do not PATCH rows, run `nctl dashboard`, open a migration transaction, or touch file timestamps in
the dashboard directory. If live state has already advanced beyond `0014`, stop the phase and
reconcile the roadmap/rollback assumptions before continuing.

Gate: live package commit, migration state, running-Job count, cache aggregates, and generated path
are current and no cache value or file was changed.

### Step 3 — Capture the current nctl surface and retained evidence behavior

Capture without invoking an operation:

```bash
uv run --project nctl nctl --help
uv run --project nctl nctl dashboard --help
uv run --project nctl nctl serve --help
uv run --project nctl nctl reconcile --help
uv run --project nctl nctl ops --help
uv run --project nctl nctl ops list --help
uv run --project nctl nctl ops show --help
```

Record:

- top-level command names;
- dashboard/serve options and schemas;
- current config sections;
- optional/development server dependencies;
- current `ReconcileData`, `RoundSummary`, and `EventRecord` model fields;
- current `nctl.ops.list.v1` and `nctl.ops.show.v1` fields; and
- paths/names of existing operation JSONL/artifacts, without copying artifact contents.

`--help` is selected because normal `status`, `drift`, `dashboard`, `serve`, or `reconcile` may
write event logs or other output. Live retained-command smoke tests belong to Phase 5.

Gate: the report can compare the current surface with Section 4 field-for-field.

### Step 4 — Build the exhaustive deletion manifest

Search each tracked repository separately so submodule files are included and ignored/generated
files are excluded. Search active source, tests, packaging, config, current docs, active roadmaps,
historical docs, and migration history.

At minimum search case-sensitively for the parent roadmap tokens:

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

Also search structural/coupling tokens:

```text
FastAPI
uvicorn
starlette
websocket
subscribe(
_publish(
_subscribers
nctl-event-subscriber
render_dashboard_from_drift
build_dashboard
push_statuses
status_push
latest_snapshot
OperationRunner
8300
nctl-dashboard
/api/v1/
```

Use tracked file lists (`git ls-files`) or equivalent, not a raw recursive search that treats
`.venv`, `uv` caches, `.git`, `__pycache__`, or local generated output as source. For every match,
write one manifest row:

| Column | Meaning |
|---|---|
| `repository` | root, nctl, nintent, etc. |
| `path` | repository-relative path |
| `symbol_or_token` | matched feature/symbol |
| `role` | reader, writer, config, dependency, test, current-doc, history, generated-local |
| `consumer` | exact caller/reader, or `none` |
| `classification` | `delete`, `edit`, `keep-shared`, or `historical` |
| `phase` | Phase 1, 2, 3, 4, 5, or N/A |
| `reason` | short ownership rationale |

Do not classify only by filename. Trace imports/callers for helpers used by both a removed surface
and retained CLI code.

Gate: every match has exactly one classification, phase, and reason; no unexplained entry remains.

### Step 5 — Apply the minimum classification rules

#### `delete`

The manifest must include at least:

```text
nctl/src/nctl_core/serve/
nctl/src/nctl_core/dashboard/
nctl/src/nctl_core/dashboard_render.py
nctl/tests/test_serve_app.py
nctl/tests/test_serve_dashboard.py
nctl/tests/test_serve_operations.py
nctl/tests/test_serve_runner.py
nctl/tests/test_serve_ws.py
nctl/tests/test_cli_serve.py
nctl/tests/test_dashboard_html.py
nctl/tests/test_dashboard_push.py
nctl/tests/test_dashboard_render.py
nctl/tests/test_cli_dashboard.py
nctl/tests/test_events_bus.py
```

If a newly discovered test asserts only a removed command, route, schema, HTML surface, subscriber,
or cache writer, classify it `delete`. Do not replace it with a no-op presentation test.

#### `edit`

The manifest must include at least:

```text
nctl/src/nctl_core/cli/main.py
nctl/src/nctl_core/config.py
nctl/src/nctl_core/events.py
nctl/src/nctl_core/reconcile/executor.py
nctl/src/nctl_core/drift_render.py
nctl/pyproject.toml
nctl/uv.lock
nctl/example.nctl.toml
nctl/tests/test_config.py
nctl/tests/test_compatibility_snapshots.py
nctl/tests/test_reconcile_executor.py

nintent/nautobot_intent_catalog/models.py
nintent/nautobot_intent_catalog/api/serializers.py
nintent/nautobot_intent_catalog/filters.py
nintent/nautobot_intent_catalog/tables.py
nintent/nautobot_intent_catalog/views.py
nintent/nautobot_intent_catalog/urls.py
nintent/nautobot_intent_catalog/navigation.py
nintent/nautobot_intent_catalog/__init__.py
nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desirednode.html
nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desiredservice.html
devenv/nautobot/nautobot_config.py
```

Also classify all current READMEs/output docs/compatibility docs/usage examples and active
roadmaps named by the parent roadmap as `edit` in Phase 4, even when their text is not executable.

#### `keep-shared`

The manifest must preserve at least:

```text
nctl/src/nctl_core/artifacts.py
nctl/src/nctl_core/operations_index.py
nctl/src/nctl_core/ops_render.py
nctl/src/nctl_core/output.py
nctl/src/nctl_core/reconcile/lock.py
```

It must also preserve the durable subset of `events.py`, retained tests for JSONL write order and
write-failure isolation, operation-index/ops CLI tests, reconcile artifacts, and existing operation
directories.

The REST DesiredNode/DesiredService ViewSets are shared desired-state mutation/read surfaces. Do
not delete a whole ViewSet merely because the dashboard writer used PATCH.

#### `historical`

Keep:

- `nintent/.../migrations/0009_reconciliation_status.py`;
- migration `0010`'s dependency on `0009`;
- historical core-reconcile, better-usability, VM, Braindump, and fix reports/plans that describe
  what existed at the time;
- historical operation JSONL and artifact directories; and
- future `0016` history after it is created.

Current roadmap promises are not historical merely because they mention an old design. Mark and
edit current roadmaps in Phase 4. Where classification is ambiguous, use the document's current
status and whether later work is expected to follow it.

Gate: deletion does not absorb a shared kernel helper, and history does not remain presented as an
active instruction.

### Step 6 — Audit real consumers and local invocation paths

The roadmap already records the user's statement that neither dashboard is used and no external
process uses `nctl serve`. Phase 0 turns that statement into a bounded audit; it does not claim
that filesystem/process inspection can mathematically prove the absence of an unknown remote
machine.

Audit:

1. tracked Makefiles, scripts, CI config, service units, compose files, Ansible tasks, and shell
   wrappers for the removed commands, port, route, token name, and configured URL;
2. git-ignored project-local executable/config files by filename and match path only, excluding
   `.local/secrets`, evidence payloads, Braindump/private prose, caches, and generated dashboard
   contents;
3. the current user's crontab;
4. user and system LaunchAgent/LaunchDaemon plist paths;
5. loaded `launchctl` services;
6. current processes for nctl serve, uvicorn loading nctl, and dashboard generation;
7. TCP listeners on port 8300;
8. Docker-published port 8300 and containers whose command invokes nctl serve; and
9. known reverse-proxy/static-host configuration for the configured dashboard URL.

For shell history, do not copy or search unrestricted history into evidence. If history is used at
all, run a count-only exact-command query locally and record only zero/nonzero plus timestamps of
matching invocations, never surrounding commands or private arguments.

Consumer evidence is sufficient when:

- the user confirmation is cited;
- repository and local automation searches show no invoker;
- no current server process/listener exists;
- no cron/launch/container/reverse-proxy automation invokes the feature; and
- any remaining URL merely points to stale generated output and has no current workflow consumer.

If an invoker is found, do not delete it silently. Record its owner, target, frequency, and whether
it is active. Stop Phase 0 until the user confirms it can be removed or scopes it out of this
initiative.

Gate: every discoverable consumer is either zero or explicitly resolved by the user, and port 8300
has no nctl listener.

### Step 7 — Amend the active VM Phase 3 plan

Edit `devdocs/big/vm/p3/plan.md` before VM Phase 3 proceeds to matched commits or deployment.
Preserve all compute, endpoint-MAC, migration-`0015`, seed, safety, and no-actuation requirements.

Make these exact semantic changes:

1. add a short supersession/coordinated-rollout note pointing to this roadmap and plan;
2. in the `desired_mac_mismatch` contract, replace `dashboard/status` presentation with
   structured JSON drift, human drift output, and reconcile manual-review evidence;
3. in deliverables, remove dashboard/status/serve output work and require only retained
   drift/CLI/reconcile/artifact output;
4. in Step 5, remove dashboard from the list of dispatch surfaces in which compute rows must remain
   inert; retain drift/planner/reconcile inertness;
5. in Step 6, remove dashboard/status wiring and require the finding in JSON/human drift plus
   manual-review classification, digest suppression, planner suppression, direct apply/executor
   defense, zero SSH, and zero Ansible;
6. in Step 8, remove the dashboard read-path smoke test and add retained `nctl ops list/show`
   evidence where an operation exists;
7. in Step 11, remove dashboard/status derivation and retain the structured finding,
   human/JSON drift, manual-review, unchanged bytes/digest, and zero-actuation proof;
8. update its verification tables and deliverables consistently;
9. in Phase 4 handoff, replace "dashboard explanation" with structured CLI/drift/reconcile evidence;
   and
10. state that the live window applies local `0015` then `0016` from one exact nintent revision and
    activates one matching nctl revision before operations resume.

Do not rewrite `report3.0.md` through `report3.5.md`; they accurately record the implementation at
the time. A historical statement that compute rows were inert to dashboard dispatch is not an
active dependency.

After editing, search the active plan for:

```text
dashboard
serve
reconciliation_status
reconciliation_checked_at
```

Any remaining match needs an explicit historical/supersession explanation. Run `git diff --check`
and save the focused diff to the private evidence directory.

Gate: VM Step 6/8/11 acceptance can pass with only retained CLI/evidence surfaces, and its live
rollout cannot produce a mixed `0015`/`0016`/nctl tuple.

### Step 8 — Freeze the post-Phase-0 implementation manifest

Review the manifest against:

- every file in the parent roadmap deletion/edit inventory;
- every newly discovered match;
- imports and test fixtures, not only string matches;
- `pyproject.toml` and lockfile dependency reachability;
- local deployment config;
- current docs versus historical docs; and
- the VM plan amendment.

Record counts by classification and phase, but do not use count reduction as an acceptance target.
Explicitly call out:

- `test_events_bus.py` as the additional delete;
- any server module that is actually shared and therefore must first be decoupled rather than
  blindly deleted;
- any dependency that remains for a non-server consumer;
- every expected historical exception; and
- the exact known generated dashboard directory to handle only in Phase 5.

The manifest is frozen when every Phase 1–4 implementation path can be derived from it without a
new ownership decision. Newly discovered files in later phases must be added to that phase's report
and reconciled against the same classification rules.

Gate: no `unknown`, `investigate`, or unowned row remains.

### Step 9 — Produce the Phase 0 report

Create `devdocs/big/remove_unused_surfaces/p0/report.md` with:

1. status: `complete`, `partially complete`, or `blocked`;
2. exact execution timestamp and private evidence directory;
3. root/submodule revisions and dirty-state ownership;
4. live installed nintent revision, migration state, and running-Job count;
5. aggregate cache counts and generated dashboard path;
6. current command/config/dependency surface;
7. manifest counts plus every important delete/edit/keep/history decision;
8. consumer audit boundary and result;
9. explicit zero-listener result for port 8300;
10. the frozen contracts from Section 4, referenced rather than redefined;
11. VM Phase 3 current step, amendment summary, and coordinated owner/sequence;
12. confirmation that no live mutation occurred;
13. every discrepancy, omission, or substituted check; and
14. an exit-criteria table with evidence references.

Do not paste the 500+ raw search lines into the report. Summarize them by classified path and point
to the private manifest.

Gate: the report is sufficient for Phase 1 to begin without relying on conversational context.

## 7. Expected Phase 0 manifest

The execution-time scan is authoritative, but the plan expects these groups.

| Group | Classification | Implementation phase |
|---|---|---|
| `nctl_core.serve`, live dashboard template, HTTP/WS runner/adapters | delete | Phase 1 |
| subscriber bus and `test_events_bus.py` | delete durable subset retained | Phase 1 |
| serve CLI/config/auth/dependencies/snapshots/docs | delete/edit | Phase 1 / Phase 4 |
| static dashboard package/renderer/template/push/CLI tests | delete | Phase 2 |
| reconcile dashboard import/field/write/warnings/test stubs | edit/delete | Phase 2 |
| dashboard config/schema/examples/current docs | edit/delete | Phase 2 / Phase 4 |
| nintent four cache fields and UI/API/config link residue | edit + new migration | Phase 3 |
| local deployment `dashboard_url` | edit | Phase 3 |
| current root/nctl/nintent docs and active roadmaps | edit | Phase 4 |
| migration `0009`, `0010` dependency, historical reports/artifacts | historical | N/A |
| JSONL, operation artifacts/index/render, locks, drift/reconcile kernel | keep-shared | all phases |
| known local generated dashboard directory | inspect now; archive/remove only with approval | Phase 5 |

## 8. Verification

Phase 0 is documentation/read-only, so no full runtime suite is required. Run:

```bash
git diff --check
git status --short
git submodule status
```

Additionally verify:

- every raw evidence file has the required private mode;
- no secret or dashboard content appears in the tracked diff;
- `devdocs/big/vm/p3/plan.md` has no unexplained active dependency on dashboard/serve/cache fields;
- the manifest contains all parent-roadmap tokens and the structural tokens in Step 4;
- each manifest row has one of the four allowed classifications;
- current `nctl --help` evidence positively shows both commands existed at baseline;
- process/listener evidence positively shows no nctl server was active;
- cache counts came from real aggregation rather than copied roadmap numbers;
- the installed nintent commit and migration state came from the running environment;
- `ReconcileData` and event/ops fields were read from current source;
- report paths do not point to secrets or make private evidence tracked; and
- the only tracked changes are Phase 0 documentation and pre-existing user-owned changes.

Do not run `nctl dashboard` as a verification step. Do not start `nctl serve` merely to prove its
current behavior.

## 9. Exit criteria

Phase 0 is `complete` only if all are checked:

- [ ] The exact root/submodule tuple and dirty ownership are recorded.
- [ ] The running nintent commit, migration state, and active Job count are recorded.
- [ ] Cache counts by status and the exact generated directory are recorded without contents.
- [ ] Current nctl commands, config sections, schemas, and server dependencies are captured.
- [ ] Every source/test/config/current-doc/history/local-deployment match is classified.
- [ ] `nctl/tests/test_events_bus.py` and any other newly found dedicated surface are included.
- [ ] Shared operation/evidence helpers are explicitly protected from deletion.
- [ ] The user-confirmed no-consumer decision is backed by repository, automation, process,
      listener, container, and local service-config checks.
- [ ] No nctl serve process is listening on port 8300.
- [ ] The final `ReconcileData`, JSONL event, operation-index, and `ops` contracts are frozen.
- [ ] The active VM Phase 3 plan has no removed-surface acceptance requirement.
- [ ] VM Phase 3 and this initiative share one explicit migration/deployment sequence.
- [ ] No runtime code, database row, migration state, Job, generated dashboard, service, or
      operation artifact was changed.
- [ ] `report.md` records all omissions/discrepancies and uses precise completion language.

If a real consumer is found, the active VM plan cannot be safely amended, live state has advanced
unexpectedly, or ownership of overlapping edits cannot be established, report `blocked` or
`partially complete`; do not reinterpret a narrower scan as proof of completion.

## 10. Handoff to Phase 1

Phase 1 receives:

- the classified removal manifest;
- the retained contracts in Section 4;
- a zero-consumer/listener decision within the documented audit boundary;
- the exact nctl/nintent/VM Phase 3 starting revisions;
- an amended VM Phase 3 plan;
- the known additional deletion of `test_events_bus.py`;
- the expected historical exceptions; and
- an explicit instruction that no live deployment occurs until the coordinated `0015` + `0016`
  window.

Phase 1 may then delete the server and subscriber bus while proving JSONL and `nctl ops` behavior.
It must return to this phase's classification rules if a newly discovered coupling would remove
part of the deterministic kernel.
