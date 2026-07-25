# Remove Unused nctl Server and Dashboard Surfaces — Development Roadmap

## Purpose

Remove the unused `nctl serve` HTTP/WebSocket surface, both live and static dashboards, and the
dashboard-derived reconciliation cache in nintent. Preserve the CLI-driven deterministic kernel,
operation evidence, and Braindump/Alignment Review workflow.

This roadmap implements item 1 of
[`devdocs/vision/refactor/vision.md`](../../vision/refactor/vision.md). That vision is authoritative
for system boundaries and must be read before making a phase plan.

The intended transition is:

```text
current
  nctl CLI
  + static dashboard and Nautobot status push
  + HTTP operation API and WebSocket event stream
  + live browser dashboard
  + derived reconciliation cache and dashboard links in nintent

to
  nctl CLI
  + structured command output
  + JSONL operation events and on-disk artifacts
  + nctl ops inspection
  + no server, dashboard, or duplicated status cache
```

The outcome is deletion, not deprecation. No compatibility server, hidden command, disabled route,
old config alias, or retained status field is added.

## Why this work is justified

The user has confirmed that neither dashboard is used and that no external process uses
`nctl serve`. The intended operating model is a resident or remote AI agent invoking the local
`nctl` CLI and reading CLI JSON, event logs, and operation artifacts.

The removed surfaces are not required for reconciliation correctness:

- `nctl drift` already computes the authoritative desired-versus-actual result;
- `nctl reconcile` already persists plans, round drift, results, and JSONL events;
- `nctl ops list/show` already reads past and running operations from disk;
- the status fields in nintent are explicitly a stale-able cache written only by the dashboard;
  and
- the server wraps existing core functions without owning desired state, actual state, drift, or
  actuation semantics.

Removing them reduces dependencies, schemas, concurrency behavior, derived state, test burden, and
documentation without weakening the control loop.

## Governing decisions

### 1. CLI and disk evidence are the supported operation surface

Retain:

- `nctl status`;
- `nctl actual`;
- `nctl drift`;
- render and apply commands;
- `nctl reconcile`;
- lifecycle, SSH, session, and Braindump commands;
- `nctl ops list/show`;
- human-readable output and supported `--json` envelopes;
- reconcile locking;
- JSONL event logs;
- plan, before/after drift, action, and `result.json` artifacts; and
- explicit operation IDs used internally to correlate one bounded operation.

Do not add a replacement daemon, MCP server, socket, polling endpoint, file watcher, notification
service, or new "latest snapshot" cache in this initiative. A future remote interface requires a
new concrete consumer and a separate roadmap.

### 2. Remove both dashboard implementations

The following are one retired feature family:

- static `nctl dashboard`;
- `index.html` and dashboard-owned `drift.json` generation;
- dashboard status push;
- the browser page served from `GET /`;
- API reads used only by that browser page; and
- dashboard URL configuration and links.

Do not keep the static dashboard as a fallback for removing the live dashboard. Neither has a
current consumer.

### 3. Remove the nintent reconciliation cache instead of finding a new writer

`DesiredNode.reconciliation_status`, `DesiredNode.reconciliation_checked_at`,
`DesiredService.reconciliation_status`, and `DesiredService.reconciliation_checked_at` are derived
from the last dashboard run. They are not user intent and are not the convergence source of truth.

Drop the fields and every UI/API/config surface dedicated to them. Do not move them to another
model, custom field, local file, or periodic Job. Humans and agents obtain current status from
`nctl drift`; operation-specific results come from reconcile evidence.

### 4. Preserve migration history

Migration `0009_reconciliation_status.py` has been applied to the live database and remains in
normal Django history. Do not edit or delete it.

Local migration `0015_compute_platform_instance_and_endpoint_mac.py` is committed and not yet
applied live. Add a separate `0016_remove_reconciliation_dashboard_surfaces.py` depending on
`0015`. Prefer applying `0015` and `0016` in the same coordinated VM Phase 3 maintenance window
described in this roadmap's Phase 5 over rewriting either historical migration.

Reversing `0016` may recreate empty columns but cannot reconstruct discarded cache values. Exact
rollback therefore uses the pre-window database backup and prior matched nintent/nctl revisions.
This data loss is acceptable because the values are disposable derived cache, but it must be
recorded explicitly.

### 5. Remove the in-memory subscriber bus with the server

`nctl_core.events` currently contains a process-wide subscriber registry, per-subscriber worker
threads, bounded queues, drop behavior, and callback isolation used only by the WebSocket server.
Remove that machinery.

Retain `EventRecord`, ULID generation, and `OperationLog` JSONL writes. JSONL remains the durable
operation evidence and the source used by `nctl ops`.

### 6. Keep operation indexing; remove server-only readers

Retain `nctl_core.operations_index` and `nctl_core.ops_render` because the CLI uses them directly.
Delete server-only artifact allowlisting, latest-snapshot lookup, ASGI response helpers, and
server-side operation runner/gating.

The cross-process reconcile lock remains. The server's additional in-process single-flight gate
has no consumer after server deletion.

### 7. Break removed contracts cleanly

Delete:

- `nctl.dashboard.v1`;
- `nctl.serve.v1`;
- all `/api/v1/*` and WebSocket contracts owned by nctl serve; and
- `ReconcileData.dashboard`.

There is no deprecation window because there is no consumer and the repository is in a coordinated
breaking-change phase. Do not emit old envelopes from hidden paths or retain an `/api/v2` server.

Update the current `nctl.reconcile.v2` payload in place by removing its optional `dashboard` field.
Do not create and maintain a second reconcile schema solely for an unused field. Existing
historical `result.json` files remain self-contained evidence and are not migrated or reparsed by
the retained `nctl ops` implementation.

### 8. Historical reports remain historical

Do not rewrite completed reports under `devdocs/big/core_reconcile/p3/` or
`devdocs/big/core_reconcile/p5/`. Add a clear supersession notice to the current
`devdocs/big/core_reconcile/roadmap.md`, and update current READMEs and active roadmaps so future
work does not reintroduce the deleted goals.

## Current-state baseline

This baseline was read on 2026-07-25 and must be repeated at Phase 0.

### Revisions and worktrees

| Component | Revision | State |
|---|---|---|
| superproject | `4f756f000543162e14a7a9a00e51eac1fe8f75ee` | only the new refactoring docs were untracked |
| nctl | `cb655c698312d864c311277e904c457213ae8d89` | clean |
| nintent | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

### Live Nautobot state

- Nautobot `3.1.3` was healthy and authenticated through `nctl status`.
- The installed nintent distribution was `0.9.0` from Git commit
  `ad9d36397d23c269ad748e13acbccc532fa29f52`.
- Live nintent migrations were applied through `0014_braindump_exchange_diary`; local `0015` was
  not applied.
- All five DesiredNodes had cached status `converged`.
- Of six DesiredServices, one had cached status `converged` and five were blank.
- The deployment config set
  `dashboard_url = "http://192.168.1.50/nctl-dashboard/"`.
- The local generated dashboard directory contained `index.html` and `drift.json`.

These cached values and generated files are not authoritative state.

### Size and test signals

- `nctl` collected 1,029 pytest cases.
- Tracked nctl Python source was 19,186 lines; tracked nctl tests were 21,140 lines.
- Dedicated serve/dashboard source, templates, and the eight primary dedicated tests totaled
  3,590 lines.
- Including `test_cli_dashboard.py` and `test_cli_serve.py`, the dedicated files totaled 3,728
  lines and 73 test functions.
- Additional coupling existed in config tests, compatibility snapshots, event delivery,
  reconcile-executor tests, READMEs, and nintent models/UI.

The implementation report must remeasure these values. They are not target quotas.

## Deletion and edit inventory

Phase plans must re-run repository-wide searches before using this list.

### nctl files to delete

Delete the dashboard implementation:

```text
src/nctl_core/dashboard/
src/nctl_core/dashboard_render.py
tests/test_dashboard_html.py
tests/test_dashboard_push.py
tests/test_dashboard_render.py
tests/test_cli_dashboard.py
```

Delete the server implementation:

```text
src/nctl_core/serve/
tests/test_serve_app.py
tests/test_serve_dashboard.py
tests/test_serve_operations.py
tests/test_serve_runner.py
tests/test_serve_ws.py
tests/test_cli_serve.py
```

### nctl files to edit

At minimum:

- `src/nctl_core/cli/main.py`
  - remove imports, options, and the `dashboard` and `serve` commands;
- `src/nctl_core/config.py`
  - remove `DashboardConfig`, `ServeConfig`, their `Config` fields, serve token resolution, and
    loopback-only validation;
  - remove imports used only by those types;
- `src/nctl_core/reconcile/executor.py`
  - remove `DashboardData`, `ReconcileData.dashboard`, `_write_dashboard()`, its terminal call,
    dashboard warning behavior, and dashboard wording;
  - keep final drift artifact, summaries, result persistence, and terminal state unchanged;
- `src/nctl_core/events.py`
  - remove subscriber callbacks, worker threads, queues, publish logic, and subscriber-specific
    imports;
  - retain durable JSONL behavior;
- `src/nctl_core/drift_render.py`
  - remove dashboard-specific documentation wording without changing drift data;
- `pyproject.toml`
  - remove the `serve` optional extra and FastAPI/uvicorn from the development group;
- `uv.lock`
  - regenerate it and confirm server-only transitive dependencies disappear; and
- `example.nctl.toml`
  - remove `[dashboard]` and `[serve]`.

Review and edit:

- `tests/test_config.py`;
- `tests/test_compatibility_snapshots.py`;
- `tests/test_reconcile_executor.py`; and
- any test fixture constructing `dashboard` or `serve` config sections.

Delete `_stub_dashboard()` and its repeated calls from reconcile tests. Delete the test whose only
contract is dashboard failure degradation. Do not replace those calls with another no-op
presentation stub.

### nintent files to edit

At minimum:

- `nautobot_intent_catalog/models.py`
  - remove four cache fields and duplicated status constants/choices;
- add migration `0016_remove_reconciliation_dashboard_surfaces.py`;
- `nautobot_intent_catalog/api/serializers.py`
  - remove dashboard-writer commentary and any explicit writability tied to the cache;
- `nautobot_intent_catalog/filters.py`
  - remove reconciliation-status filters;
- `nautobot_intent_catalog/tables.py`
  - remove status columns and render helpers;
- `nautobot_intent_catalog/templates/nautobot_intent_catalog/desirednode.html`;
- `nautobot_intent_catalog/templates/nautobot_intent_catalog/desiredservice.html`;
- `nautobot_intent_catalog/views.py`
  - remove dashboard context, setting resolver, and redirect view;
- `nautobot_intent_catalog/urls.py`
  - remove `dashboard_redirect`;
- `nautobot_intent_catalog/navigation.py`
  - remove conditional nctl Dashboard navigation;
- `nautobot_intent_catalog/__init__.py`
  - remove the `dashboard_url` default setting; and
- relevant tests or environment-backed checks.

Do not remove an entire DesiredNode or DesiredService REST ViewSet in this roadmap merely because
dashboard status push used it. Canonical REST/GraphQL/UI/YAML contraction belongs to the separate
interface-contract roadmap.

### Deployment and current documentation to edit

- `devenv/nautobot/nautobot_config.py`
  - remove `dashboard_url`;
- root `README.md`;
- `nctl/README.md`;
- `nctl/docs/output-format.md`;
- `nctl/docs/compatibility.md`;
- `nctl/docs/usage_example.md`;
- `nintent/README.md`;
- `nintent/README_QUICK.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/vm/roadmap.md`; and
- the active `devdocs/big/vm/p3/plan.md`.

Current docs must position `nctl drift`, reconcile artifacts, and `nctl ops` as the supported
inspection path. Do not promise a replacement GUI.

In `devdocs/big/braindump/roadmap.md`, mark its optional Phase 4 serve/dashboard integration as
superseded. Preserve the Braindump models, minimal UI, GraphQL reads, REST mutations, and nctl CLI
workflow.

In the active VM Phase 3 plan, remove dashboard/status requirements from:

- desired-MAC finding presentation;
- Step 6 wiring;
- Step 8 smoke checks;
- Step 11 environment-backed proof;
- deliverables and verification tables; and
- Phase 4 handoff language.

Keep the desired-MAC mismatch/ambiguity blocker, manual-review classification, digest suppression,
planner suppression, zero SSH/Ansible calls, and recovery/non-repetition proof.

Historical phase plans and reports remain unchanged except for an optional short supersession note
at their directory entry point. They must not be rewritten as though the deleted feature never
existed.

## Scope boundaries

### In scope

- delete server/dashboard runtime code and schemas;
- remove server-only concurrency and event subscriber machinery;
- remove nintent derived cache and dashboard link;
- remove dependencies and configuration;
- decouple reconcile terminal handling from dashboard generation;
- update active documentation and VM Phase 3 acceptance criteria;
- add and deploy the nintent removal migration;
- delete feature-specific tests and update shared contract tests;
- verify retained CLI/evidence workflows; and
- explicitly clean up or archive the known local generated dashboard directory.

### Out of scope

- redesigning GraphQL/REST/YAML/UI ownership generally;
- simplifying Braindump CRUD beyond removing server/dashboard integration;
- broad test consolidation unrelated to deleted behavior;
- splitting large nctl modules;
- implementing Proxmox compute drift or guest creation;
- replacing `nctl serve` with another API, MCP server, daemon, or agent protocol;
- adding scheduled drift, notifications, or a terminal UI;
- deleting old event logs or reconcile artifacts;
- changing SSH policy or reconcile action semantics; and
- removing framework-generated REST reads solely because GraphQL is canonical.

## Ownership and dependencies

| Concern | Owner after this initiative |
|---|---|
| Desired and actual reads, drift, plan, bounded execution, evidence | nctl CLI/core |
| Durable operation history | nctl JSONL logs and operation artifact directories |
| Confirmed structured intent and its Nautobot UI/API | nintent |
| Braindump semantic Ground Truth and current Alignment Review | nintent storage plus user/agent workflow |
| Host actuation | ansible_agdev or another explicitly approved actuator |
| Actual observation and ledger ingest | nodeutils and nauto/Nautobot |
| Local Nautobot plugin configuration | `devenv/nautobot/nautobot_config.py` |
| Push, maintenance-window, migration, and cleanup authority | user/operator |

The interface-contract roadmap may later remove other unused REST/UI/YAML paths, but this roadmap
does not wait for or pre-empt that broader decision. It removes only paths whose consumer is the
confirmed-unused server/dashboard family.

The risk-based test roadmap follows this work: feature-specific tests are deleted here, while
unrelated consolidation waits until the deleted code is gone. The nctl modularization roadmap also
follows this work so it only restructures surviving code.

The pending VM Phase 3 schema and desired-MAC work overlaps directly with this roadmap. Do not
implement either against independently changing nintent/nctl contracts. Phase 0 must select one
coordinated owner and matched revision tuple, and the live migration/cleanup phase requires
explicit operator approval.

## Phases

Concrete implementation plans and one final report per phase should live under
`devdocs/big/remove_unused_surfaces/pN/`. Avoid one report per small edit.

### Phase 0 — Freeze the final removal contract and live baseline

**Goal:** establish an exact, current deletion manifest and prevent collision with the pending VM
Phase 3 cutover.

Work:

1. Re-read this roadmap, the refactoring vision, README_DEV, local environment memo, and latest VM
   Phase 3 reports.
2. Record root/submodule revisions, dirty state, live installed nintent commit, migration state,
   running Jobs, and current nctl command surface.
3. Record cache row counts by status and the exact generated dashboard path without copying
   secrets or HTML/data contents into tracked reports.
4. Search source, tests, configuration, current docs, historical docs, and local deployment config
   for every removal token.
5. Classify each discovered reference as delete, edit, keep-shared, or historical.
6. Confirm no current process, cron entry, launch agent, shell wrapper, Makefile target, or external
   client invokes `nctl dashboard`, `nctl serve`, port 8300, or the configured dashboard URL.
7. Confirm no active nctl serve process is listening before implementation or live rollout.
8. Amend the pending VM Phase 3 plan before its Step 7/8 matched commit and deployment gates.
9. Freeze the exact final `ReconcileData` field set and the retained event/ops contracts.

**Exit criteria:** the manifest names every current reader/writer and confirms zero real consumers;
the retained CLI/evidence surface is explicit; the VM Phase 3 plan no longer requires a removed
surface; and no live mutation has occurred.

### Phase 1 — Remove nctl serve and server-only event machinery

**Goal:** make nctl a CLI-only package with no ASGI, HTTP, WebSocket, or in-memory subscriber
surface.

Work:

1. Delete `nctl_core.serve` and its dedicated CLI/server tests.
2. Remove the `serve` command, options, config model, auth/token/CORS/loopback logic, and examples.
3. Remove FastAPI, uvicorn, and server-only transitive dependencies through a regenerated lock.
4. Remove the event subscriber bus while preserving JSONL event writes and their failure isolation.
5. Keep operations index and `ops list/show`; remove only server-specific snapshot/artifact
   adapters and runner gates.
6. Remove `/api/v1`, WebSocket, serve-startup, and OpenAPI compatibility snapshots and docs.
7. Build/install nctl without extras in a clean temporary environment and prove ordinary CLI
   imports do not require FastAPI, Starlette, or uvicorn.
8. Run focused event, operation-index, ops CLI, config, and command-help tests.

**Exit criteria:** `nctl --help` has no `serve`; no nctl package file imports FastAPI, Starlette,
uvicorn, or WebSocket libraries; no subscriber worker thread machinery remains; JSONL events and
`nctl ops` still work; and a plain installation has no server dependency.

### Phase 2 — Remove static dashboard, status push, and reconcile coupling

**Goal:** remove all nctl dashboard behavior while retaining fresh drift and reconcile evidence.

Work:

1. Delete the dashboard package, renderer, templates, command, config, envelopes, and dedicated
   tests.
2. Remove dashboard/status push from the server-independent nctl dependency graph.
3. Remove `ReconcileData.dashboard`, `_write_dashboard()`, calls, warnings, docstrings, and repeated
   test stubs.
4. Preserve final drift generation, `final_drift_path`, summary/scope summary, terminal state,
   progress evidence, `result.json`, and operation completion ordering.
5. Update compatibility/output docs and snapshots to remove `nctl.dashboard.v1` and the reconcile
   dashboard field.
6. Update current READMEs and example config.
7. Prove a converged, planned, manual-review, and failed reconcile result no longer attempts any
   HTML write or Nautobot status PATCH and otherwise retains the same terminal semantics.
8. Prove `nctl drift --json`, human drift output, reconcile result artifacts, and `nctl ops` provide
   the retained inspection paths.

**Exit criteria:** `nctl --help` has no `dashboard`; no dashboard module/template/schema/config
remains; reconcile has no presentation side effect; and retained drift/reconcile evidence is
complete without a replacement cache.

### Phase 3 — Remove nintent cache fields and dashboard links

**Goal:** remove the database and Nautobot presentation/API residue of the dashboard.

Work:

1. Add migration `0016_remove_reconciliation_dashboard_surfaces.py` after local `0015`.
2. Remove four model fields and their duplicated choices/constants.
3. Remove filter, table, detail-template, serializer-comment, view-context, redirect, URL,
   navigation, and plugin-setting behavior.
4. Remove `dashboard_url` from the development Nautobot configuration.
5. Add focused model/schema/template/URL checks and a disposable-database forward migration proof.
6. Prove a normal DesiredNode/DesiredService UI page still renders and GraphQL/REST responses no
   longer expose the removed cache fields.
7. Confirm Braindump/Alignment Review UI and APIs are unchanged.
8. Prepare matched nintent/nctl commits and record the rollout and rollback revision tuples.
9. Ask the user to push nintent; do not push on the user's behalf.

**Exit criteria:** a disposable database reaches `0016`; removed columns, fields, filters, UI rows,
nav links, redirect routes, and setting are absent; ordinary desired-state and Braindump paths
still work; and matched revisions are ready for deployment.

### Phase 4 — Consolidate current documentation and pre-deployment evidence

**Goal:** ensure no active instruction or roadmap asks an agent to use or rebuild the removed
surfaces before the new revisions are deployed.

Work:

1. Update all current READMEs, examples, output/compatibility docs, and active roadmaps listed in
   the inventory.
2. Mark core-reconcile dashboard and realtime API goals as superseded by this roadmap.
3. Mark Braindump optional server/dashboard integration as superseded without changing its core
   authority boundary.
4. Remove dashboard/status requirements from the active VM roadmap and Phase 3 plan while
   preserving desired-MAC safety requirements.
5. Preserve historical reports and link them as historical evidence when useful.
6. Rerun repository-wide deletion searches and confirm the matched commits contain code, migration,
   examples, and current documentation for one final contract.
7. Record pre-deployment source/test line counts, collected test counts, dependency inventory, and
   the exact live rollback tuple.

**Exit criteria:** current documentation names only supported commands and contracts; no active
roadmap depends on the removed features; all deletion searches are clean except migration history
and clearly marked historical evidence; and the code/documentation/migration revision tuple is
ready for one coordinated deployment.

### Phase 5 — Coordinated deployment and final verification

**Goal:** deploy the final CLI-only/cache-free contract, prove it on the local environment, and
record completion evidence.

Work:

1. Begin the already-required VM Phase 3 maintenance window and stop desired writes, import Jobs,
   routine nctl operations, and any old dashboard/server process.
2. Recheck the VM Phase 3 legacy realized-VM precondition and all other `0015` gates.
3. Back up the database and record the exact rollback commands/revisions.
4. Record final cache counts for evidence only; do not translate them.
5. Build/restart Nautobot from the exact pushed nintent revision.
6. Apply `0015` and `0016` in order and activate the matching nctl revision before resuming routine
   operation.
7. Run `makemigrations --check --dry-run`, `showmigrations`, UI/GraphQL/REST smoke checks, and the
   revised VM Phase 3 cutover checks.
8. Run nctl status, drift, render, dry reconcile, ops list/show, and Braindump list/show against the
   live environment.
9. Prove removed commands return normal CLI "no such command" behavior and no process listens on
   the former nctl serve port.
10. Search installed/local code and current docs for obsolete runtime references.
11. After successful verification, explicitly remove or archive only the known generated
    `~/.local/state/nctl/dashboard` directory. Do not touch the broader nctl state directory,
    event logs, SSH trust store, or operation artifacts.
12. Resume operations and record the final matched revision tuple.
13. Rerun source/test line counts, collected test counts, and dependency inventory.
14. Produce one final report comparing the Phase 0 and final state, including every omitted or
    deferred item and without treating line/test count as the correctness criterion.

**Exit criteria:** live Nautobot is at `0016`; the cache columns and dashboard links are absent;
the CLI-only nctl revision is active; retained drift/reconcile/ops/Braindump paths work; no server
is listening; stale generated dashboard output is no longer presented as current; rollback
evidence exists; and the measured reduction and retained proofs are recorded.

## Verification matrix

| Area | Required proof |
|---|---|
| CLI surface | `nctl --help` contains retained commands and no `dashboard`/`serve`; removed commands fail as unknown |
| Packaging | clean plain install imports/runs without FastAPI, Starlette, uvicorn, websockets, or serve extra |
| Configuration | example and strict config contain no dashboard/serve sections; obsolete keys are not silently accepted |
| Events | JSONL sequence, write-failure isolation, operation ID, and terminal event behavior remain; subscriber threads are absent |
| Operation inspection | `ops list/show` indexes existing and new operation logs/artifacts, including directories containing historical `result.json` files |
| Drift | live and fixture `drift --json` plus human output remain unchanged apart from documentation |
| Reconcile | plan/apply terminal states, summaries, progress, final drift, result persistence, and lock remain; no dashboard field/write/PATCH |
| nintent schema | forward migration through 0016; no four cache columns/fields; migration 0009 retained |
| nintent UI/API | node/service pages render without status rows; nav/redirect absent; normal GraphQL/REST behavior retained |
| Braindump | list/show/create/review paths and user/AI authorship boundary unaffected |
| VM Phase 3 | desired-MAC conflict still suppresses authoritative artifact, digest, plan, SSH, and Ansible without dashboard assertions |
| Live rollout | exact installed commit and migration state; no old process/port; revised smoke checks pass |
| Deletion | no runtime imports, schemas, routes, config, docs, or dedicated tests remain outside migration/history exceptions |
| Secrets | no Nautobot token, serve token, private prose, key material, or raw dashboard content enters tracked evidence |

## Required deletion searches

The implementation plan may refine the commands, but completion must search at least these tokens
across active source, tests, config, and current docs:

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

Expected remaining matches must be limited to:

- migration `0009_reconciliation_status.py` and later migration dependencies/history;
- this roadmap and the refactoring vision;
- historical plans/reports explicitly marked as superseded; and
- evidence reports that explain the removal.

An unexplained active-code or current-document match blocks completion.

## Rollback

Rollback is coordinated, not a runtime compatibility mode.

If failure occurs before live migration:

- keep the live `0014` deployment and prior nctl revision active;
- fix the final matched revisions or report `implemented, not deployed`; and
- do not partially expose the local compute/dashboard-removal schema.

If failure occurs after `0015`/`0016` migration:

1. stop desired writes and routine nctl operations;
2. restore the pre-window database backup;
3. rebuild/restart the prior installed nintent commit;
4. reactivate the prior nctl revision;
5. verify migration state, desired rows, status cache, and ordinary operations; and
6. report which post-migration evidence was produced before rollback.

Do not restore compatibility by re-adding status fields, serve routes, or dashboard commands to
the final branch.

## Definition of done

This initiative is complete only when all of the following are true:

- `nctl serve`, `/api/v1`, WebSocket delivery, and the live dashboard are absent;
- `nctl dashboard`, static rendering, status push, and dashboard config are absent;
- FastAPI/uvicorn and server-only transitive dependencies are absent from nctl;
- the event subscriber bus is absent while JSONL evidence remains;
- nintent has no reconciliation cache fields, dashboard setting, nav link, redirect, or status UI;
- reconcile produces fresh final drift and terminal evidence with no dashboard field or side
  effect;
- active docs and VM Phase 3 criteria no longer depend on removed surfaces;
- Braindump/Alignment Review and all retained deterministic safety boundaries still work;
- live migration and matched-version verification passed;
- stale generated dashboard files were explicitly handled without deleting unrelated nctl state;
  and
- the final report records before/after measurements and every required proof.

Code deletion or a smaller test count alone is not completion. Completion is the demonstrated
absence of the unused surfaces together with positive proof that the retained CLI control loop and
evidence paths still work.
