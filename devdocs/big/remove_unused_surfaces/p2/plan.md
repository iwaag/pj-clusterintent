# Remove Unused Surfaces Phase 2 Implementation Plan: Remove the Static Dashboard and Reconcile Coupling

Parent: [roadmap.md](../roadmap.md) — Phase 2.

Predecessor: [Phase 1 final report](../p1/report9.md) — `complete`.

Status: proposed; local nctl implementation and verification only.

## 1. Goal and required transition

Remove the remaining nctl dashboard implementation: the `dashboard` CLI command, static HTML
renderer and template, dashboard-owned `drift.json`, status push into nintent, dashboard
configuration, `nctl.dashboard.v1`, and automatic dashboard generation from reconcile terminal
handling.

Preserve fresh drift output and the complete reconcile evidence path. After this phase, nctl has
no presentation side effect after drift or reconcile and no writer for nintent's disposable
reconciliation cache. The cache fields themselves remain temporarily in nintent until Phase 3.

The Phase 2 transition is:

```text
before
  nctl drift
  + nctl dashboard
      -> compute/load drift
      -> write index.html and dashboard-owned drift.json
      -> PATCH reconciliation status/timestamp to nintent
  + nctl reconcile
      -> write final drift artifact
      -> regenerate dashboard and PATCH status cache
      -> persist result.json and finished event

after Phase 2
  nctl drift
      -> human text or nctl.drift.v1 JSON
  + nctl reconcile
      -> plan/round/action/final-drift artifacts
      -> result.json
      -> finished event
  + nctl ops list/show
      -> durable operation inspection
  + no HTML, dashboard-owned snapshot, or status-cache write
```

The observable outcome is an 11-command CLI with no `dashboard` command. `nctl reconcile` retains
schema name `nctl.reconcile.v2` but its data payload has the exact Phase 0 frozen field set with no
`dashboard` field. Converged, planned, manual-review, unsupported/non-converged, and failed
operations preserve their existing state, summaries, progress, SSH evidence, final drift where
available, `result.json`, and event ordering.

This is a coordinated breaking deletion. Do not retain a hidden command, renderer shim, null
dashboard field, accepted `[dashboard]` alias, replacement cache, or alternative presentation
service.

## 2. Governing inputs and current baseline

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- [Phase 0 plan](../p0/plan.md), especially frozen contracts §4.1, §4.2, §4.3, §4.5, and §4.6;
- [Phase 0 final report](../p0/report9.md);
- [Phase 1 plan](../p1/plan.md);
- every Phase 1 report, treating [report9.md](../p1/report9.md) as authoritative;
- current `nctl/README.md`;
- current `nctl/docs/compatibility.md`;
- current `nctl/docs/output-format.md`;
- current `nctl/docs/usage_example.md`;
- `nctl/src/nctl_core/dashboard/`;
- `nctl/src/nctl_core/dashboard_render.py`;
- `nctl/src/nctl_core/reconcile/executor.py`;
- `nctl/src/nctl_core/config.py`;
- `nctl/src/nctl_core/cli/main.py`; and
- all dashboard, config, compatibility, CLI-surface, operation-index, and reconcile-executor
  tests.

Phase 0's frozen final contract is authoritative. Phase 1 removed the server and subscriber bus
without changing any static-dashboard or reconcile-dashboard behavior; its handoff is therefore
the exact Phase 2 starting point.

### 2.1 Planning-time repository snapshot

Observed while this plan was written on 2026-07-25:

| Repository | Revision | State relevant to Phase 2 |
|---|---|---|
| superproject | `02ba66d7fd62e3694e263d80d9115aca3dc83969` | clean |
| `nctl` | `73096304abcf18bb8fd9d504e9df9166fd959919` | clean; Phase 1 complete |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean; unchanged in Phase 2 |

This snapshot is orientation only. Step 0 must recapture revisions and dirty-state ownership.
Preserve unrelated user changes if the repositories have moved.

No live deployment occurs in this phase. The final nctl and nintent revisions are deployed
together only through the coordinated maintenance sequence in the parent roadmap. Phase 2 does
not rebuild Nautobot, apply migration `0015` or `0016`, or clean generated dashboard output.

### 2.2 Current implementation and measurements

At the planning-time nctl revision:

- `nctl --help` has 12 top-level commands; `serve` is absent and `dashboard` remains;
- the full nctl suite collects 980 tests;
- tracked nctl Python source is 18,137 lines and tracked test Python is 20,025 lines;
- the four dashboard package files, `dashboard_render.py`, and four dedicated dashboard test
  files total 9 tracked files and 1,304 lines;
- the four dedicated dashboard test files collect 29 test functions;
- `DashboardConfig` owns `out_dir`, optional `url`, and path expansion;
- `dashboard_render.py` owns `nctl.dashboard.v1`, loading an old drift envelope, HTML/JSON writes,
  status push, and human dashboard output;
- `dashboard/push.py` is the only nctl writer of `reconciliation_status` and
  `reconciliation_checked_at`;
- `ReconcileData` has one field beyond the Phase 0 final target: `dashboard`;
- `_run_apply()` writes a final drift artifact and then calls `_write_dashboard()`;
- `_write_dashboard()` catches renderer/write-back errors, emits dashboard warnings, and stores
  `DashboardData` in the reconcile result;
- `_finish()` persists `result.json` before the terminal `finished` event; and
- 23 reconcile-executor tests call `_stub_dashboard()`, while one dedicated test preserves only
  dashboard-failure degradation.

Phase 1 already proved:

- durable JSONL event behavior;
- `nctl ops list/show`;
- historical `result.json` files are opaque artifacts;
- a clean wheel installation has no server dependencies; and
- the static dashboard is the only remaining retired presentation surface.

The Phase 2 line/test reduction is diagnostic only. Completion depends on deleting the unused
surface and positively preserving the retained CLI/evidence contracts.

## 3. Scope, non-goals, and ownership boundary

### 3.1 In scope

- delete `nctl_core.dashboard`, `nctl_core.dashboard_render`, their template, and dedicated tests;
- remove the `dashboard` CLI command, options, imports, help text, and `nctl.dashboard.v1`;
- remove `DashboardConfig`, `Config.dashboard`, and `[dashboard]` example configuration;
- make obsolete `[dashboard]` input fail strict config validation;
- delete all status-push code and nctl PATCH bodies for the two reconciliation cache fields;
- remove `DashboardData`, `ReconcileData.dashboard`, `_write_dashboard()`, its call, warnings, and
  wording;
- remove every `_stub_dashboard()` call and the dashboard-failure-only reconcile test;
- freeze `ReconcileData` to the exact Phase 0 field set without changing schema name;
- preserve final drift generation, summaries, terminal state, progress, SSH evidence,
  `result.json`, and terminal event ordering;
- update mixed CLI/config/compatibility/reconcile tests;
- update current nctl documentation and example configuration for the retained inspection paths;
- edit active nctl source/test wording that still treats dashboard as a dispatch or consumer;
- prove dashboard-free reconcile outcomes across the required terminal-state matrix;
- prove no HTML write or reconciliation-cache PATCH occurs; and
- produce one final Phase 2 report with exact evidence and deviations.

### 3.2 Retained owners after Phase 2

| Concern | Retained owner |
|---|---|
| Fresh desired-versus-actual status | `nctl drift` / `nctl.drift.v1` |
| Human inspection of fresh drift | `render_drift_text()` |
| Machine inspection of fresh drift | `nctl drift --json` |
| Bounded plan/apply | `nctl reconcile` |
| Per-operation proof | JSONL plus operation artifact directory |
| Terminal reconcile payload | `result.json` using `nctl.reconcile.v2` |
| Operation discovery/history | `nctl ops list/show` |
| Event persistence | `EventRecord` and `OperationLog` |
| Structured desired state | nintent, unchanged in this phase |
| Current cache columns and Nautobot UI residue | temporary Phase 3 responsibility |

`nctl ops` is operation history, not a replacement freshness cache. Do not introduce a latest
snapshot file, new HTML page, periodic writer, or terminal dashboard.

### 3.3 Out of scope

- removing nintent model fields, filters, tables, templates, URLs, navigation, or plugin settings;
- creating or applying migration `0016`;
- changing DesiredNode/DesiredService REST or GraphQL ownership generally;
- changing drift comparison, planner classification, action ordering, SSH policy, or actuation;
- changing VM Phase 3 desired-MAC/dnsmasq semantics;
- broad test consolidation unrelated to the deleted dashboard;
- deleting or rewriting historical `result.json`, event logs, or operation artifacts;
- deleting or archiving `~/.local/state/nctl/dashboard` before Phase 5 approval;
- editing historical core-reconcile/dashboard reports to pretend the feature never existed;
- repository-wide documentation consolidation and supersession notices owned by Phase 4;
- live Nautobot access, container restart, database migration, Job, desired write, Ansible, or
  reconcile apply; and
- push or deployment.

The root README and cross-initiative current roadmaps still contain known dashboard references
classified for Phase 4. Phase 2 updates nctl's current package documentation; it must not broaden
into the Phase 4 repository-wide documentation pass.

## 4. Frozen Phase 2 contracts

### 4.1 Final CLI and configuration

The exact top-level command set after Phase 2 is:

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

`nctl --help` must omit both retired commands. Invoking `nctl dashboard` or `nctl serve` must return
Typer's ordinary unknown-command usage failure. Do not add a retirement command or custom
compatibility message.

`Config` must have no `dashboard` or `serve` field. Existing `StrictModel(extra="forbid")` behavior
must make `[dashboard]` and `[serve]` invalid. The latter remains covered by the Phase 1 config
regression test.

### 4.2 Removed dashboard contracts

The final nctl runtime has none of:

- `nctl.dashboard.v1`;
- `DashboardData`;
- `StatusPushData`;
- `DashboardConfig`;
- `build_dashboard()`;
- `render_dashboard_from_drift()`;
- `render_dashboard_html()`;
- `render_dashboard_text()`;
- static `index.html` or dashboard-owned `drift.json` generation;
- `--out`, `--from`, or `--no-push` dashboard options;
- `dashboard_url`;
- dashboard status PATCHes;
- reconciliation-cache writer routes, lookup fallback, counters, or warnings; or
- dashboard package resources in a built wheel.

Do not replace any removed item with a no-op, null object, deprecated alias, or differently named
presentation abstraction.

### 4.3 Exact `ReconcileData` contract

Keep schema name `nctl.reconcile.v2`. The final model fields are exactly:

```text
operation_id
mode
scope
state
event_log_path
artifact_dir
plan_path
initial_drift_path
final_drift_path
rounds
manual_review
unsupported
summary
scope_summary
progress_made
ssh_preflight
```

Remove `dashboard` in place. Do not:

- create `nctl.reconcile.v3` solely for this deletion;
- serialize `"dashboard": null`;
- preserve a private alias;
- parse or rewrite old payloads; or
- make `nctl ops` validate historical result bodies.

Update the compatibility test from a dashboard-bearing floor to an exact assertion for
`ReconcileData`. Exactness is required here because a hidden extra presentation field would
violate the Phase 0 frozen contract.

### 4.4 Reconcile evidence and ordering

Preserve:

- plan and initial drift persistence;
- final full-cluster drift computation when current logic provides one;
- `final_drift_path`;
- `summary` and `scope_summary`;
- `rounds`, `ActionResult`, and per-round SSH evidence;
- `manual_review` and `unsupported`;
- truthful `progress_made`, including partial mutations before a later failure;
- top-level `ssh_preflight`;
- state/`ok` mapping;
- `drift_resolved` or `non_converged` event behavior;
- `result.json` persistence before `finished`;
- one terminal `finished` event;
- reconcile locking; and
- historical operation indexing.

The dashboard-free terminal sequence is:

```text
final drift available
  -> write round-N/drift-final.json
  -> assign full/scope summaries
  -> calculate truthful progress_made
  -> build terminal nctl.reconcile.v2 envelope
  -> emit drift_resolved or non_converged when applicable
  -> persist result.json
  -> emit finished
```

If final drift is unavailable under an existing failure path, preserve the current
`final_drift_unknown` semantics and do not invent a dashboard or fallback snapshot.

Removing `_write_dashboard()` must not move `_persist_terminal_result()` after `op.finish()`, drop
round evidence, or change terminal-state calculation.

### 4.5 Historical artifacts

Historical `result.json` files containing `dashboard` or old cache-related content remain
immutable evidence. Keep the Phase 1 operation-index regression test that lists such a file as an
opaque artifact.

The literal legacy field in that focused fixture is an expected active-test exception to deletion
searches. It is not a reader, compatibility parser, or runtime schema.

## 5. File-level implementation inventory

### 5.1 Delete

Delete the complete static dashboard implementation:

```text
nctl/src/nctl_core/dashboard/__init__.py
nctl/src/nctl_core/dashboard/html.py
nctl/src/nctl_core/dashboard/push.py
nctl/src/nctl_core/dashboard/template.html
nctl/src/nctl_core/dashboard_render.py
```

Delete tests whose only subject is the removed feature:

```text
nctl/tests/test_cli_dashboard.py
nctl/tests/test_dashboard_html.py
nctl/tests/test_dashboard_push.py
nctl/tests/test_dashboard_render.py
```

These nine paths are the Phase 0 frozen Phase 2 delete set. Do not retain the template as an
unused package asset.

### 5.2 Edit runtime and example configuration

| File | Required Phase 2 edit |
|---|---|
| `nctl/src/nctl_core/cli/main.py` | remove dashboard imports, option aliases, command, and reconcile docstring promise |
| `nctl/src/nctl_core/config.py` | remove `DashboardConfig` and `Config.dashboard`; preserve all unrelated path/config behavior |
| `nctl/src/nctl_core/reconcile/executor.py` | remove dashboard imports, field, call, helper, warnings, and server/dashboard wording; preserve evidence and terminal ordering |
| `nctl/src/nctl_core/drift_render.py` | replace dashboard-consumer wording with the supported text/JSON drift contract |
| `nctl/src/nctl_core/sources/desired.py` | remove the stale dashboard-dispatch reference from the active compute-inertness comment without changing behavior |
| `nctl/example.nctl.toml` | remove the complete `[dashboard]` section; keep all retained config sections unchanged |

No dependency is known to be dashboard-only after Phase 1. Do not change `pyproject.toml` or
`uv.lock` unless a fresh reachability check discovers a real orphan. `httpx`, `pydantic`, and
other dashboard imports also have retained consumers.

### 5.3 Edit shared tests

| File | Required Phase 2 test change |
|---|---|
| `nctl/tests/test_cli_surface.py` | remove `dashboard` from the exact retained set, update phase wording, and prove both removed commands are unknown |
| `nctl/tests/test_config.py` | add `[dashboard]` rejection; retain `[serve]` rejection and every unrelated config test |
| `nctl/tests/test_compatibility_snapshots.py` | remove dashboard imports/schema; remove `dashboard` from reconcile; assert the exact final `ReconcileData` fields including `ssh_preflight` |
| `nctl/tests/test_reconcile_executor.py` | delete `_stub_dashboard()`, all 23 calls, and dashboard-degradation-only test; add/strengthen dashboard-free terminal and artifact assertions |
| `nctl/tests/test_operations_index.py` | retain the historical-result opaque-artifact test unchanged except for wording if needed |
| `nctl/tests/test_vm_p3_compute_stays_inert.py` | replace dashboard-specific wording with presentation-independent drift/planner/reconcile language; keep behavior unchanged |

Do not replace `_stub_dashboard()` with another presentation no-op. Its removal is evidence that
reconcile no longer has a presentation dependency.

### 5.4 Update current nctl documentation

Edit:

```text
nctl/README.md
nctl/docs/compatibility.md
nctl/docs/output-format.md
nctl/docs/usage_example.md
```

Required changes:

- remove dashboard command examples, configuration, schema, rendering, URL, status-push, and
  reconcile-reuse claims;
- remove `nctl.dashboard.v1`;
- remove `dashboard` from the documented `nctl.reconcile.v2` data fields;
- describe fresh status through `nctl drift` text/JSON;
- describe bounded results through reconcile artifacts and `result.json`;
- describe historical inspection through `nctl ops list/show`;
- avoid presenting `ops` as current convergence state; and
- do not promise a replacement GUI.

`docs/event-log.md` has no current dashboard coupling after Phase 1 and needs no edit unless a fresh
search finds one.

Phase 4 still owns root README, nintent README/README_QUICK, active cross-initiative roadmaps, and
the final repository-wide supersession pass.

## 6. Required dashboard-free reconcile scenarios

Use existing reconcile fixtures and assertions wherever possible. Add only tests needed to prove
the removed side effect and retained evidence.

| Scenario | Required result | Required retained evidence | Forbidden evidence/side effect |
|---|---|---|---|
| Plan mode with actionable drift | `planned`, `ok=true` | plan, initial drift, `result.json`, finished event | no dashboard field, HTML, dashboard drift file, or cache PATCH |
| Apply with no diffs | `already_converged`, `ok=true` | final drift, summaries, `result.json`, drift-resolved + finished events | no presentation write/PATCH |
| Apply converges after action | `converged`, `ok=true` | round action, final drift, progress, SSH evidence as applicable, result | no presentation write/PATCH |
| Manual-review blocker | `manual_intervention_required`, `ok=false` | finding, final drift/summaries when current path provides them, result, non-converged + finished | no action, HTML, or PATCH |
| Unsupported/non-converged path | unchanged existing state/`ok` | findings/errors, rounds and final drift as applicable, result | no presentation write/PATCH |
| Failure before final drift | `failed`, `ok=false` | structured error, result, finished event | no invented final snapshot/dashboard |
| Failure after a mutation | `failed`, truthful progress | completed action, refresh/final-drift or `final_drift_unknown`, result | no lost evidence or presentation fallback |

For representative no-action terminal fixtures, install a fail-fast sentinel around
`NautobotClient.rest_patch` or the narrowest equivalent boundary to prove no cache PATCH occurs.
Do not globally forbid retained Nautobot mutations in action tests that legitimately exercise
linking or IPAM.

For artifact assertions:

- inspect only the operation's temporary artifact directory;
- assert `result.json`, plan, and expected drift files exist;
- assert no `index.html` or dashboard-owned root `drift.json` exists;
- assert serialized current results have no `dashboard` key; and
- preserve the historical-result fixture separately.

## 7. Safety and evidence handling

Create one git-ignored evidence directory:

```text
.local/remove-unused-surfaces/p2/<YYYYMMDD-HHMMSS>/
```

Set the directory to mode `0700` and regular files to `0600`. Record concise output for:

```text
revisions.txt
dirty-state.txt
baseline-help.txt
baseline-measurements.txt
baseline-dashboard-matches.txt
focused-tests.txt
reconcile-matrix.txt
deletion-searches.txt
wheel-filelist.txt
full-tests.txt
final-help.txt
final-measurements.txt
final-status.txt
```

The tracked report may contain revisions, public package versions, file/test/line counts, command
names, test summaries, and sanitized paths. It must not contain:

- `.local/secrets` or Nautobot token contents;
- authorization headers;
- dashboard HTML or `drift.json` contents;
- Braindump or Alignment Review prose;
- private keys or raw SSH key blobs;
- full live database rows; or
- unrestricted operation artifact contents.

This phase requires no secret and must not read `.local/secrets`.

All dashboard-writing tests use pytest temporary directories. Never run the pre-removal
`nctl dashboard` command against the real configuration or default output directory. Do not
delete, archive, touch, or inspect the contents of the known generated dashboard directory; Phase
5 handles only that exact path with approval.

## 8. Procedure

### Step 0 — Reconfirm the Phase 1 handoff and current manifest

1. Record root/nctl/nintent revisions and dirty-state ownership.
2. Confirm Phase 1 is complete and nctl has no serve/server/subscriber residue.
3. Record `uv --version`, `nctl --help`, 980-test collection baseline, source/test lines, and the
   nine dashboard delete paths.
4. Re-run dashboard/cache-token searches and importer traces across nctl source, tests, metadata,
   example config, and current docs.
5. Classify newly discovered active wording such as `sources/desired.py`,
   `test_vm_p3_compute_stays_inert.py`, and the intentional historical-result fixture.
6. Confirm no live nctl server/listener has reappeared; do not start one.
7. Create the private evidence directory and verify permissions.

Gate: the Phase 1 handoff is intact, nctl ownership is clear, and every current dashboard
reader/writer/test/doc reference has a Phase 2 decision.

### Step 1 — Freeze the final CLI/config/reconcile tests

Before removing implementation:

1. update the exact CLI retained-command set to the 11-command final contract;
2. add the ordinary unknown-command assertion for `dashboard`;
3. add strict `[dashboard]` rejection beside the retained `[serve]` rejection;
4. update compatibility expectations to remove `nctl.dashboard.v1`;
5. define the exact `ReconcileData` field assertion;
6. add the minimum dashboard-free reconcile artifact/PATCH assertions from §6; and
7. record which new absence assertions intentionally fail before deletion.

Tests for already-retained evidence must continue to pass. Do not weaken final drift, result
ordering, progress, SSH, or state assertions to accommodate the deletion.

Gate: every new/changed assertion maps to §§4 or 6, and no test preserves a removed presentation
contract.

### Step 2 — Remove the command, config, implementation, and dedicated tests

1. Remove dashboard imports/options/command from `cli/main.py`.
2. Remove `DashboardConfig` and `Config.dashboard`.
3. Remove `[dashboard]` from `example.nctl.toml`.
4. Delete the five implementation paths in §5.1.
5. Delete the four dedicated dashboard test files.
6. Update CLI/config/compatibility shared tests.
7. Run CLI/config/compatibility tests.
8. Positively inspect `nctl --help`, `nctl dashboard`, and `nctl serve`.

Gate: the command and config contract are absent, the package has no static dashboard
implementation, both old commands fail normally, and retained commands/config still work.

### Step 3 — Decouple reconcile terminal handling

1. Remove dashboard imports and `ReconcileData.dashboard`.
2. Remove the `_write_dashboard()` call and helper.
3. Remove dashboard warning behavior and obsolete module/function comments.
4. Remove `_stub_dashboard()` and all 23 calls.
5. Delete `test_dashboard_failure_does_not_overwrite_terminal_state`.
6. Update `result.json`/finished-event comments to refer to retained operation inspection rather
   than the deleted server.
7. Run the required reconcile matrix and existing focused executor suite.

Review the diff around final drift, progress calculation, `_finish()`, and
`_persist_terminal_result()` as one unit. No incidental reorder is permitted without a separate
justification and test.

Gate: reconcile imports no dashboard code, emits no dashboard warning/data, and every required
terminal state retains its evidence and ordering.

### Step 4 — Remove active wording and update current nctl docs

1. Update `drift_render.py`, `sources/desired.py`, and the VM inertness test wording without
   changing behavior.
2. Update the four current nctl documentation files in §5.4.
3. Preserve the Phase 1 historical-result regression and clearly classify its literal old field.
4. Search current nctl docs for old command/config/schema/cache language.
5. Confirm root and cross-initiative matches are exactly the known Phase 4 work, not newly
   introduced instructions.

Gate: current nctl package docs direct users to drift/reconcile/ops only, and no active source
comment implies a dashboard consumer or dispatch path.

### Step 5 — Run focused verification

From `nctl/`, run at least:

```bash
uv run pytest -q \
  tests/test_cli_surface.py \
  tests/test_config.py \
  tests/test_compatibility_snapshots.py \
  tests/test_reconcile_executor.py \
  tests/test_operations_index.py \
  tests/test_cli_drift.py \
  tests/test_drift_render.py \
  tests/test_cli_ops.py
```

Additionally run the scenario matrix in §6 with test names recorded in the report. Positive
evidence must show each intended terminal path actually ran; an empty rounds/actions assertion is
valid only for scenarios whose contract requires no action.

Gate: focused tests and all required terminal scenarios pass.

### Step 6 — Run deletion searches and package proof

Search active nctl source, tests, metadata, example config, and current docs for at least:

```text
nctl dashboard
nctl_core.dashboard
nctl_core.dashboard_render
nctl.dashboard.v1
DashboardConfig
DashboardData
StatusPushData
dashboard_url
status_push
render_dashboard
build_dashboard
_write_dashboard
reconciliation_status
reconciliation_checked_at
[dashboard]
index.html
```

Also inspect:

- Typer command registration;
- `Config.model_fields`;
- `ReconcileData.model_fields`;
- Python imports;
- built wheel contents; and
- status-PATCH literals/routes.

Expected active-test exception:

- `tests/test_operations_index.py` may contain a literal old `dashboard` field and
  `reconciliation_status` solely inside the historical opaque-artifact fixture.

Expected out-of-scope matches:

- this initiative's roadmap/plans/reports;
- the refactoring vision;
- historical core-reconcile/dashboard plans and reports;
- root/nintent/current cross-initiative docs explicitly assigned to Phases 3–4;
- nintent migration history and current cache fields assigned to Phase 3; and
- the known generated dashboard path recorded for Phase 5.

Build a wheel in a validated `mktemp -d` directory and prove its file list contains no
`nctl_core/dashboard`, `dashboard_render.py`, or template asset. A plain import of
`nctl_core.cli.main` and `nctl_core.reconcile.executor` must succeed.

Gate: no unexplained active nctl dashboard runtime/schema/config/writer match or packaged asset
remains.

### Step 7 — Run the full suite and final measurements

From `nctl/`, run:

```bash
uv run pytest -q
uv run pytest --collect-only -q
uv lock --check
```

Then:

1. repeat help and removed-command checks;
2. repeat exact CLI/config/reconcile model-field inspection;
3. repeat deletion searches;
4. record final source/test/collected-test/file counts;
5. confirm `pyproject.toml` and `uv.lock` are unchanged unless a documented orphan was found;
6. run `git diff --check`;
7. inspect the full nctl diff for accidental nintent, VM, drift, planner, SSH, or actuation
   changes; and
8. record final root/nctl/nintent status and ownership.

The expected removal of 29 dedicated dashboard tests and one dashboard-degradation test is not a
quota. Any new retained-boundary tests must be accounted for separately.

Gate: full suite, lock check, deletion searches, package proof, model-field checks, and diff
hygiene pass.

### Step 8 — Produce one final Phase 2 report

Create `devdocs/big/remove_unused_surfaces/p2/report.md`, or use the established
`report0.md`–`report8.md` convention if the user explicitly requests per-step reports. The final
report must include:

1. status: `complete`, `partially complete`, `implemented, not deployed`, or `blocked`;
2. execution timestamp and private evidence directory;
3. starting/ending root, nctl, and nintent revisions and dirty-state ownership;
4. exact deleted/edited file inventory and deviations;
5. CLI/config/model-field results;
6. reconcile scenario matrix results;
7. final drift/result/event-ordering evidence;
8. no-HTML/no-PATCH evidence;
9. focused and full test summaries;
10. before/after source/test/collected-test measurements;
11. package/wheel proof;
12. deletion-search exceptions;
13. Phase 3 handoff and intentionally retained nintent residue;
14. confirmation that no live state or generated dashboard was mutated;
15. every omitted, substituted, or failed check; and
16. an exit-criteria table with evidence references.

Raw command output belongs in the private evidence directory. Do not duplicate large test or
artifact payloads into tracked reports.

## 9. Verification matrix

| Area | Required positive proof |
|---|---|
| CLI | exact 11-command set; no `dashboard` or `serve`; both fail as ordinary unknown commands |
| Config | no `dashboard`/`serve` model fields; both obsolete TOML sections fail strict validation |
| Static implementation | no dashboard package, renderer, template, schema, options, tests, or wheel asset |
| Status push | no PATCH body/route/lookup/counter/warning code for reconciliation cache fields |
| Reconcile schema | `nctl.reconcile.v2` retained with exactly the 16 frozen fields and no null/hidden dashboard field |
| Final drift | applicable terminal paths persist fresh final drift and full/scope summaries |
| Terminal evidence | state, `ok`, progress, rounds/actions, SSH evidence, result, and events remain truthful |
| Ordering | `result.json` exists before `finished`; no presentation step is inserted or substituted |
| Terminal matrix | planned, already-converged, converged, manual-review, non-converged/unsupported, and failure paths retain semantics |
| Operation history | `ops list/show` and opaque historical result fixture remain valid |
| Current docs | nctl docs name drift/reconcile/ops inspection paths and no replacement GUI |
| Safety | no live Nautobot/database/Job/desired/Ansible/dashboard-output/event-history mutation |
| Regression | focused suite and full nctl suite pass |

## 10. Exit criteria

Phase 2 is `complete` only when all are checked:

- [ ] All five static dashboard implementation files and four dedicated dashboard test files are
      deleted.
- [ ] `nctl --help` exposes exactly the 11 frozen retained commands.
- [ ] `nctl dashboard` and `nctl serve` both fail as ordinary unknown commands.
- [ ] `DashboardConfig`, `Config.dashboard`, `[dashboard]`, dashboard CLI options, and
      `nctl.dashboard.v1` are absent.
- [ ] Obsolete `[dashboard]` and `[serve]` sections are positively proven invalid.
- [ ] No dashboard package, renderer, template, HTML write, dashboard-owned drift snapshot, or
      packaged asset remains.
- [ ] No status-push writer, cache-field PATCH, row lookup, counter, or warning behavior remains.
- [ ] `ReconcileData` has exactly the 16 Phase 0 frozen fields and keeps schema name
      `nctl.reconcile.v2`.
- [ ] `_write_dashboard()`, its call, dashboard warnings, `_stub_dashboard()`, its 23 calls, and
      the dashboard-degradation-only test are absent.
- [ ] Planned, converged, manual-review, non-converged/unsupported, and failed reconcile paths
      retain their state, summaries, progress, SSH evidence, artifacts, and events.
- [ ] Applicable paths persist fresh final drift; failures after side effects remain truthful.
- [ ] Current `result.json` contains no dashboard key and is persisted before `finished`.
- [ ] Reconcile performs no HTML/dashboard-drift write and no reconciliation-cache PATCH.
- [ ] Historical dashboard-bearing result artifacts remain listable without migration or parsing.
- [ ] Current nctl docs describe only retained inspection paths and promise no replacement GUI.
- [ ] Focused tests and the complete nctl suite pass.
- [ ] Deletion searches and wheel inspection have no unexplained active nctl matches.
- [ ] No live deployment, database/schema change, generated-output cleanup, or operational
      mutation occurred.
- [ ] The final report records exact evidence, exceptions, deviations, and completion status.

Passing a smaller test suite is not sufficient. Completion requires both absence of the retired
surface and positive proof that final drift, result persistence, operation inspection, and
terminal semantics remain intact.

## 11. Handoff to Phase 3

Phase 3 receives:

- an 11-command, CLI-only nctl package;
- no server, subscriber bus, static dashboard, dashboard schema/config, status push, or reconcile
  presentation dependency;
- exact `nctl.reconcile.v2` fields and retained result/event ordering;
- dashboard-free terminal-state and no-PATCH proofs;
- unchanged durable JSONL and `nctl ops` behavior;
- historical result compatibility through opaque artifact listing only;
- the exact nctl revision and dirty-state ownership;
- one final Phase 2 report; and
- explicit confirmation that nintent still temporarily contains the four cache fields,
  filters/tables/templates, dashboard URL/navigation/redirect, and deployment setting.

Phase 3 may then add migration `0016` and remove nintent's cache/UI/link residue without any
remaining nctl writer or reader. It must not deploy independently; matched nintent/nctl revisions
still wait for the coordinated maintenance window in Phase 5.
