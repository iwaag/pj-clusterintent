# Remove Unused Surfaces Phase 1 Implementation Plan: Remove nctl Serve and the Subscriber Bus

Parent: [roadmap.md](../roadmap.md) — Phase 1.

Predecessor: [Phase 0 final report](../p0/report9.md) — `complete`.

Status: proposed; local nctl implementation and verification only.

## 1. Goal and required transition

Remove the complete nctl-owned ASGI, HTTP, WebSocket, live-browser-dashboard, and server-side
operation-runner surface. Remove the in-memory event subscriber bus that exists only for that
server, while preserving JSONL event persistence and CLI operation inspection.

The Phase 1 transition is:

```text
before
  nctl CLI
  + static dashboard command
  + nctl serve command
  + FastAPI/Starlette/uvicorn HTTP and WebSocket server
  + live browser dashboard
  + server-side snapshot/artifact/operation adapters
  + process-wide subscriber queues and worker threads
  + JSONL event logs and nctl ops

after Phase 1
  nctl CLI
  + static dashboard command (removed in Phase 2, not this phase)
  + JSONL event logs and nctl ops
  + no serve command, server package, server configuration, server dependency,
    server-side runner, or in-memory subscriber machinery
```

The observable outcome is a plain nctl installation whose CLI imports and help work without
FastAPI, Starlette, uvicorn, or WebSocket packages. `nctl --help` still exposes all retained
commands, including the temporarily retained static `dashboard`, but no longer exposes `serve`.
`nctl ops list/show` continues to inspect durable JSONL and artifact history, including historical
operation directories created before this removal.

This phase is deletion of an unused contract, not deprecation. Do not retain a hidden command,
config alias, import shim, placeholder package, alternate API version, disabled route, or
subscriber compatibility wrapper.

## 2. Governing inputs and starting baseline

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- [Phase 0 plan](../p0/plan.md), especially its frozen Section 4 contracts;
- every Phase 0 report, treating [report9.md](../p0/report9.md) as the authoritative summary;
- `nctl/README.md`;
- `nctl/docs/compatibility.md`;
- `nctl/docs/event-log.md`;
- `nctl/docs/output-format.md`;
- `nctl/docs/usage_example.md`;
- `nctl/src/nctl_core/events.py`;
- `nctl/src/nctl_core/operations_index.py`;
- `nctl/src/nctl_core/ops_render.py`; and
- every current file under `nctl/src/nctl_core/serve/` and its dedicated tests.

Phase 0 is authoritative where its final report or frozen contract refines the parent roadmap.
Historical core-reconcile reports describe why the server was built but do not preserve it as a
current requirement.

### 2.1 Planning-time repository snapshot

Observed while this plan was written on 2026-07-25:

| Repository | Revision | State relevant to Phase 1 |
|---|---|---|
| superproject | `0e04215a7b54a59797303c0dd407070b15e888bf` | pre-existing untracked refactoring/removal documentation |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean; not changed in Phase 1 |

This is orientation only. Step 0 must recapture revisions and dirty state immediately before
implementation. Do not overwrite or absorb unrelated user changes if the worktrees have moved.

No live deployment is required. Phase 0 confirmed that the stale `nctl serve` process was stopped
and port 8300 had no listener. Recheck this read-only at Step 0; finding a new listener blocks
implementation until its ownership is resolved.

### 2.2 Current implementation and measurement baseline

At the planning-time nctl revision:

- `nctl --help` has 13 top-level commands, including `dashboard` and `serve`;
- `nctl/src/nctl_core/serve/` has eight tracked files;
- the serve package, live HTML, six dedicated server test files, and subscriber-bus test file
  contribute 15 files and 2,551 lines;
- those seven deleted test files collect 50 test functions;
- the full nctl suite collects 1,029 tests;
- tracked nctl Python source is 19,186 lines and tracked test Python is 21,140 lines;
- `ServeConfig` owns host, port, bearer-token resolution, CORS, and loopback-only unauthenticated
  validation;
- `nctl_core.events` owns one durable path (`EventRecord` and `OperationLog`) and one server-only
  path (`Subscriber`, `_SubscriberEntry`, global registry/lock, queues, worker threads,
  `subscribe()`, and `_publish()`); and
- the compatibility snapshot test currently imports FastAPI and freezes `nctl.serve.v1`,
  OpenAPI routes, WebSocket registration, operation POST, and health response contracts.

The package metadata currently gives the server two dependency roots:

```text
[project.optional-dependencies].serve
  fastapi
  uvicorn[standard]

[dependency-groups].dev
  fastapi
  uvicorn[standard]
```

The planning-time lock graph confirms these server-only chains:

```text
fastapi -> starlette
uvicorn[standard] -> httptools, python-dotenv, uvloop, watchfiles, websockets
```

`httpx` and `respx` are not server-only: the retained Nautobot client and thirteen non-dashboard
tests use them. Keep both. `anyio`, `click`, `h11`, and other shared transitive packages must be
judged by the regenerated lock graph rather than deleted by name.

Measurements are diagnostic evidence, not quotas. The expected loss of 50 server/bus tests is
correct because their contract is deleted; any replacement regression tests must each protect a
named retained or removed boundary.

## 3. Scope, non-goals, and phase boundary

### 3.1 In scope

- delete all eight tracked files under `nctl/src/nctl_core/serve/`;
- delete the serve CLI command, its options, imports, startup envelope, and runtime adapter;
- remove `ServeConfig`, `Config.serve`, token resolution, CORS, port, and loopback validation;
- make `[serve]` an invalid unknown top-level configuration section through the existing
  `extra="forbid"` policy;
- remove the `[serve]` example section;
- remove the `serve` optional dependency extra and FastAPI/uvicorn development dependencies;
- regenerate `uv.lock` and prove server-only packages are no longer reachable;
- delete the in-memory subscriber bus and its dedicated tests;
- preserve and strengthen focused JSONL event tests;
- delete server-only snapshot lookup, artifact allowlisting, operation runner, and in-process
  single-flight gates;
- remove serve/API/WebSocket compatibility snapshots;
- update current nctl documentation enough that it does not advertise or freeze the removed
  server contract;
- prove the retained operations index and `ops list/show` behavior independently of the server;
  and
- produce one Phase 1 report with exact before/after evidence and deviations.

### 3.2 Explicitly retained in Phase 1

Phase 2 owns the static dashboard family. Therefore this phase must retain:

- the `nctl dashboard` command and its current options;
- `nctl_core.dashboard`;
- `nctl_core.dashboard_render`;
- `DashboardConfig` and `Config.dashboard`;
- `[dashboard]` in `example.nctl.toml`;
- `nctl.dashboard.v1`;
- dashboard-owned `index.html` and `drift.json` generation;
- status push;
- `ReconcileData.dashboard` and reconcile terminal dashboard generation;
- dashboard tests and dashboard-specific portions of mixed tests; and
- the existing generated dashboard directory, untouched.

Editing a mixed file does not transfer Phase 2 behavior into Phase 1. In particular:

- `cli/main.py` loses only `ServeConfig`, `nctl_core.serve.runtime`, serve options, and the
  `serve()` command;
- `config.py` loses only the serve model and serve-only imports/helpers;
- `test_config.py` loses serve behavior tests but keeps dashboard config tests;
- `test_compatibility_snapshots.py` loses serve/HTTP/WS imports, schemas, paths, and tests but
  keeps dashboard and the current `ReconcileData.dashboard` snapshot; and
- `example.nctl.toml` loses only `[serve]`.

This intentional intermediate state makes the top-level Phase 1 CLI surface 12 commands:

```text
status
actual
drift
dashboard
reconcile
lifecycle
render
apply
ops
braindump
ssh
session
```

Phase 2 will remove `dashboard` and reduce the final surface to the 11 commands frozen in Phase 0.

### 3.3 Out of scope

- static dashboard deletion or reconcile dashboard decoupling;
- nintent model, migration, API, filter, table, template, navigation, or setting changes;
- migration `0016` or any live migration;
- VM Phase 3 desired-MAC/dnsmasq work;
- broad interface contraction or test-suite consolidation;
- replacement HTTP, MCP, daemon, socket, file-watcher, notification, or TUI surfaces;
- changes to reconcile locking, planning, action ordering, SSH policy, or actuation;
- deletion or rewriting of historical event logs and operation artifacts;
- cleanup of `~/.local/state/nctl/dashboard`;
- container rebuilds, Nautobot restarts, Jobs, desired-state writes, Ansible, or live reconcile;
  and
- push or deployment.

## 4. Phase 1 contracts

### 4.1 CLI and configuration

`nctl --help` must omit `serve`, and invoking `nctl serve` must return Typer's normal unknown-command
usage failure. Do not replace it with a custom retirement message because that would retain a
hidden command contract.

The config model must contain no `ServeConfig` or `serve` field. Since `Config` remains a strict
model, an existing `[serve]` section must fail validation as an extra input. It must not be
ignored, logged as a warning, or mapped to a deprecated alias.

Remove imports that existed only for server validation:

- `ipaddress`;
- `Literal`;
- `model_validator`; and
- `ConfigInvalidError` or `ValidationError` imports at CLI call sites only if they no longer have
  a retained use.

Check actual remaining uses before removing an import; do not infer solely from the old serve code.

### 4.2 Durable event contract

Retain `EventRecord` with exactly the Phase 0 frozen fields:

```text
ts
operation_id
op
seq
event
level
message
data
```

Retain:

- `generate_ulid()`;
- `OperationLog.start()`, `emit()`, `finish()`, and `_write()`;
- one append-ordered JSONL file per operation;
- per-operation monotonic sequence numbers;
- the `EventRecord` returned by `emit()` even if persistence fails;
- file-write failure isolation; and
- at most one warning per `OperationLog` instance after repeated write failures.

Delete:

- `Subscriber`;
- `_SubscriberEntry`;
- `_subscribers`;
- `_subscribers_lock`;
- `subscribe()`;
- `_publish()`;
- `threading`, `deque`, and `Callable` when no retained use remains;
- subscriber queue/drop/callback warnings; and
- the `_publish(record)` call after a successful file append.

File persistence must not become conditional on any listener. Removing publication must not change
the JSON serialization, `seq` behavior, warning isolation, or returned record.

### 4.3 Operations and artifacts

Keep these modules unchanged unless a narrowly necessary testability correction is found:

```text
nctl_core.artifacts
nctl_core.operations_index
nctl_core.ops_render
nctl_core.output
nctl_core.reconcile.lock
```

Delete the server adapters, not the underlying evidence:

- `serve/artifacts.py` public HTTP allowlisting;
- `serve/snapshots.py` latest-snapshot/result readers;
- `serve/runner.py` operation submission and in-process gating;
- HTTP response and replay helpers in `serve/app.py`; and
- live dashboard asset loading in `serve/dashboard.py`.

`nctl ops list/show` must continue to:

- validate operation IDs;
- tolerate corrupt or partial JSONL lines;
- index log-only, artifact-only, and combined layouts;
- list recursive artifact names and sizes;
- read an `after_seq` cursor;
- emit no operation merely because history is inspected; and
- list a historical `result.json` that contains the removed server-era/dashboard fields without
  parsing, rewriting, or rejecting its contents.

### 4.4 Packaging

After `uv lock`:

- there is no `serve` extra in project metadata or lock metadata;
- the development group has no FastAPI or uvicorn entry;
- `fastapi`, `starlette`, `uvicorn`, `websockets`, `httptools`, `uvloop`, `watchfiles`, and
  `python-dotenv` are absent unless a newly discovered retained dependency independently requires
  one;
- a plain wheel install imports the CLI, events module, operation index, and ops renderer without
  server packages; and
- `nctl --help` runs from that isolated installation.

If a listed package remains, inspect `uv tree --locked --invert --package <name>` and record the
retained owner. Do not force-remove a genuinely shared package from the lock.

## 5. File-level implementation inventory

### 5.1 Delete

Delete the whole server implementation:

```text
nctl/src/nctl_core/serve/__init__.py
nctl/src/nctl_core/serve/app.py
nctl/src/nctl_core/serve/artifacts.py
nctl/src/nctl_core/serve/dashboard.py
nctl/src/nctl_core/serve/live_dashboard.html
nctl/src/nctl_core/serve/runner.py
nctl/src/nctl_core/serve/runtime.py
nctl/src/nctl_core/serve/snapshots.py
```

Delete tests whose only subject is the removed contract:

```text
nctl/tests/test_cli_serve.py
nctl/tests/test_events_bus.py
nctl/tests/test_serve_app.py
nctl/tests/test_serve_dashboard.py
nctl/tests/test_serve_operations.py
nctl/tests/test_serve_runner.py
nctl/tests/test_serve_ws.py
```

These 15 paths are the Phase 0 frozen delete set for Phase 1. A newly discovered file may be added
only after tracing its importers and classifying it under the same delete/edit/keep-shared/history
rules.

### 5.2 Edit runtime and packaging

| File | Required Phase 1 edit |
|---|---|
| `nctl/src/nctl_core/cli/main.py` | remove serve imports, option aliases, command, token preflight, startup emit, and uvicorn call; preserve dashboard |
| `nctl/src/nctl_core/config.py` | remove `ServeConfig`, `Config.serve`, serve token/host/CORS validation, and now-unused imports/helper; preserve `DashboardConfig` |
| `nctl/src/nctl_core/events.py` | reduce to durable ULID/EventRecord/OperationLog behavior |
| `nctl/pyproject.toml` | remove the `serve` optional extra and direct FastAPI/uvicorn dev dependencies; keep core and `respx` |
| `nctl/uv.lock` | regenerate from the edited metadata, without unrelated upgrades |
| `nctl/example.nctl.toml` | remove only the `[serve]` section |

Use a normal lock regeneration without `--upgrade`; dependency removal must not become an
unrelated version-refresh initiative.

### 5.3 Edit and add focused tests

| File | Required Phase 1 test change |
|---|---|
| `nctl/tests/test_config.py` | remove default/validation/token assertions for `cfg.serve`; add a positive assertion that `[serve]` is rejected as an unknown top-level section |
| `nctl/tests/test_compatibility_snapshots.py` | remove FastAPI/httpx-ASGI imports used only by serve, `ServeData`, `nctl.serve.v1`, `/api/v1` path set, and four HTTP/WS tests; retain all dashboard and reconcile fields for Phase 2 |
| `nctl/tests/test_events.py` | assert JSONL order/shape, returned `EventRecord`, and one-warning write-failure isolation after the bus is gone |
| `nctl/tests/test_operations_index.py` | add a historical `result.json` fixture containing an old dashboard-shaped field and prove it is listed as an opaque artifact |
| `nctl/tests/test_cli_ops.py` | retain as the CLI-level proof for list/show and cursor behavior; edit only if a discovered server coupling requires it |
| `nctl/tests/test_cli_surface.py` | add a small top-level contract test: retained commands remain, `dashboard` remains for Phase 2, `serve` is absent, and direct `serve` invocation is an unknown command |

The CLI-surface test protects a unique failure mode: deleting server modules while accidentally
leaving a Typer command registration or lazy import behind. The config rejection test protects the
separate failure mode of silently accepting an obsolete configuration contract.

Do not move subscriber tests into `test_events.py`. Queue capacity, callback exception isolation,
fan-out, unsubscribe, and worker lifecycle are deleted behavior, not durable-log requirements.

### 5.4 Current nctl documentation

Edit the serve-specific portions of:

```text
nctl/README.md
nctl/docs/compatibility.md
nctl/docs/event-log.md
nctl/docs/output-format.md
nctl/docs/usage_example.md
```

Required changes:

- remove `nctl serve` installation and command examples;
- remove the realtime API, route, auth, CORS, OpenAPI, WebSocket, replay, live dashboard, and
  in-process gate contracts;
- remove `nctl.serve.v1`;
- describe JSONL as durable disk evidence consumed by the CLI/`nctl ops`, not by external
  subscribers;
- describe `operations_index` as a retained CLI helper rather than a shared CLI/server helper; and
- preserve all static dashboard documentation until Phase 2.

This is the minimum same-phase documentation update needed to keep the nctl package internally
truthful. Phase 4 still owns repository-wide consolidation, supersession notices, root/nintent
documentation, and active-roadmap cleanup after Phases 2 and 3.

## 6. Safety and evidence handling

Create one git-ignored evidence directory:

```text
.local/remove-unused-surfaces/p1/<YYYYMMDD-HHMMSS>/
```

Set the directory to mode `0700` and regular evidence files to `0600`. Record concise outputs for:

```text
revisions.txt
dirty-state.txt
baseline-help.txt
baseline-measurements.txt
dependency-before.txt
focused-tests.txt
full-tests.txt
deletion-searches.txt
dependency-after.txt
clean-install.txt
final-help.txt
final-measurements.txt
```

The tracked Phase 1 report may contain revisions, public package names/versions, file/test/line
counts, command names, test summaries, and sanitized paths. It must not contain:

- Nautobot or serve token values;
- `.local/secrets` contents;
- authorization headers;
- process environments;
- dashboard HTML or `drift.json` contents;
- Braindump or Alignment Review prose;
- raw SSH key material; or
- unrestricted operation-artifact contents.

This phase requires no secret and should not read `.local/secrets`.

Do not delete the existing dashboard directory, event logs, operation artifact directories, SSH
trust store, or any broader nctl state path. Temporary wheel-install directories may be created
with `mktemp -d`; validate the exact returned path before removing only that directory.

## 7. Procedure

### Step 0 — Reconfirm the boundary and starting state

1. Record the current root, nctl, and nintent revisions and dirty state.
2. Confirm nctl has no pre-existing edits. If it is dirty, identify ownership and either preserve
   non-overlapping work or stop before touching overlapping files.
3. Confirm Phase 0 remains `complete` and its frozen contract has not been superseded.
4. Re-run the Phase 0 Phase 1 manifest search and import trace. Confirm the 15 delete paths still
   exist and have no retained importer.
5. Record `uv --version`, `uv run nctl --help`, collected test count, source/test line counts, and
   the server dependency reverse tree.
6. Confirm no `nctl serve` process and no TCP listener on port 8300.
7. Create the private evidence directory and verify its permissions.

Gate: nctl ownership is clear, no live server has reappeared, and no newly discovered importer
requires an ownership decision.

### Step 1 — Add retained-boundary regression tests

Before deleting implementation code:

1. add the CLI surface test;
2. replace serve config behavior tests with the obsolete-section rejection test;
3. add the durable event returned-record and one-warning failure tests; and
4. add the historical `result.json` operation-index test.

Run the new tests against the current implementation and record which assertions intentionally
fail because `serve` still exists. Tests for already-retained behavior must pass. Do not weaken an
assertion merely to make the pre-deletion run green.

Gate: every new test maps to one contract in Section 4 and no new test preserves server behavior.

### Step 2 — Remove CLI and configuration entry points

1. Remove serve imports and command registration from `cli/main.py`.
2. Remove `ServeConfig`, `Config.serve`, `_is_loopback_host()`, and serve-only imports from
   `config.py`.
3. Remove `[serve]` from `example.nctl.toml`.
4. Update mixed tests to remove only serve cases.
5. Run config and CLI-surface tests.
6. Run `nctl --help` and the expected-failure `nctl serve`; positively inspect the exit code and
   message.

Gate: the CLI has no serve entry point, obsolete config fails closed, and the static dashboard
still loads and appears in help.

### Step 3 — Delete the server and subscriber bus

1. Delete the entire `nctl_core/serve` directory.
2. Delete all six dedicated serve/CLI test files.
3. Delete `test_events_bus.py`.
4. Reduce `events.py` to the frozen durable contract.
5. Remove server/OpenAPI/WebSocket portions of `test_compatibility_snapshots.py`.
6. Run event, compatibility, operations-index, and ops CLI tests.
7. Run static dashboard tests as a scope guard.

Gate: no server package/import/route/schema/test remains, durable event tests pass, `ops` remains
independent, and Phase 2 dashboard tests still pass.

### Step 4 — Remove dependencies and regenerate the lock

1. Remove the optional `serve` extra.
2. Remove direct FastAPI and uvicorn entries from the development group.
3. Run `uv lock` without an upgrade flag.
4. Run `uv lock --check`.
5. Inspect `uv tree --locked` and the reverse tree of each suspected server-only transitive
   dependency.
6. Confirm `httpx` and `respx` remain with their retained owners.
7. Review the lock diff. It must reflect reachability removal, not broad unrelated upgrades.

Gate: metadata and lock contain no server dependency root or unexplained server-only transitive
package.

### Step 5 — Update current nctl documentation

Remove only serve/API/subscriber claims from the five nctl documentation files listed in Section
5.4. Preserve dashboard instructions for Phase 2. Search the resulting current nctl documentation
for removed schema, route, command, dependency-extra, and subscriber symbols.

Gate: current nctl docs no longer instruct a user or agent to install, run, call, authenticate to,
or subscribe to the deleted server.

### Step 6 — Run focused verification and deletion searches

From `nctl/`, run at least:

```bash
uv run pytest -q \
  tests/test_cli_surface.py \
  tests/test_config.py \
  tests/test_events.py \
  tests/test_operations_index.py \
  tests/test_cli_ops.py \
  tests/test_compatibility_snapshots.py \
  tests/test_cli_dashboard.py \
  tests/test_dashboard_render.py
```

Then verify absence across tracked runtime source, tests, package metadata, example config, and
current nctl docs for:

```text
nctl serve
nctl_core.serve
nctl.serve.v1
ServeConfig
NCTL_SERVE_TOKEN
/api/v1
/api/v1/ws
FastAPI
Starlette
uvicorn
WebSocket
subscribe(
Subscriber
_SubscriberEntry
_subscribers
_publish(
```

Use structural import searches in addition to string searches. Generic words such as `server`,
`service`, `subscribe`, or `websocket` may appear in unrelated domain prose; classify exact
matches rather than deleting by substring.

Expected matches outside the nctl active scope are limited to this roadmap, the parent roadmap,
the refactoring vision, Phase 0 evidence/reports, and historical reports. The unrelated
`ansible_agdev/api` FastAPI webhook is explicitly keep-shared and must not be changed.

Gate: every active-scope match is either absent or a documented Phase 2 static-dashboard
reference; no server/subscriber runtime residue remains.

### Step 7 — Prove a clean plain installation

Use a fresh `mktemp -d` directory, not nctl's existing `.venv`:

1. build one wheel from the edited source;
2. create a new virtual environment;
3. install only that wheel and its core dependencies, with no dev group or extra;
4. run the installed `nctl --help`;
5. import `nctl_core.cli.main`, `nctl_core.events`, `nctl_core.operations_index`, and
   `nctl_core.ops_render`;
6. use `importlib.util.find_spec()` or the environment's package list to prove FastAPI, Starlette,
   uvicorn, websockets, httptools, uvloop, watchfiles, and python-dotenv are absent;
7. inspect the built wheel file list to confirm it contains no `nctl_core/serve` asset; and
8. remove only the validated temporary directory after recording sanitized results.

Do not use the developer environment as this proof: it may still contain packages from an older
sync and would allow accidental imports to pass.

Gate: the plain installed console script and retained imports work with no server package present.

### Step 8 — Run the full suite and record final measurements

From `nctl/`, run:

```bash
uv run pytest -q
uv run pytest --collect-only -q
uv lock --check
```

Then:

1. repeat top-level help and unknown-command checks;
2. repeat dependency and deletion searches;
3. record final collected tests, source lines, test lines, and dependency inventory;
4. inspect `git diff --check`;
5. inspect the complete nctl diff for accidental Phase 2 or kernel changes; and
6. verify root/nctl/nintent status so unrelated changes remain attributable.

The full suite must pass. A lower collected count is expected because deleted contracts lose 50
tests, but no numeric target defines success.

Gate: focused tests, full suite, lock check, clean-install proof, deletion searches, and diff
hygiene all pass.

### Step 9 — Produce one Phase 1 report

Create `devdocs/big/remove_unused_surfaces/p1/report.md` containing:

1. status: `complete`, `partially complete`, `implemented, not deployed`, or `blocked`;
2. execution timestamp and private evidence directory;
3. starting and ending root/nctl/nintent revisions and dirty-state ownership;
4. deleted and edited file inventory, including any deviation from Section 5;
5. CLI/config contract results;
6. durable event and `ops` results;
7. dependency before/after and clean-install proof;
8. focused and full test summaries;
9. source/test/collected-test before/after measurements;
10. exact deletion-search exceptions;
11. confirmation that the static dashboard and Phase 2 coupling remain intentionally present;
12. confirmation that no live service, database, Job, desired state, generated dashboard, or
    operation evidence was mutated;
13. every omitted, substituted, or failed check; and
14. an exit-criteria table with evidence references.

Do not create one tracked report per edit. Raw command output belongs in the private evidence
directory; the report summarizes the decision-relevant results.

## 8. Verification matrix

| Area | Required positive proof |
|---|---|
| CLI removal | help lists the 12 Phase 1 commands including `dashboard`, excludes `serve`, and direct `serve` invocation is an ordinary unknown-command failure |
| Configuration removal | `Config` has no `serve` field and a TOML `[serve]` section fails strict validation |
| Server deletion | no `nctl_core/serve` package, asset, import, HTTP route, OpenAPI snapshot, WebSocket contract, runner, snapshot reader, or public-artifact adapter remains |
| Event retention | start/emit/finish append ordered JSONL; `seq`, returned record, data, finish state, and one-warning write-failure isolation remain |
| Subscriber deletion | no callback type, registry, lock, queue, worker thread, subscribe/unsubscribe, fan-out, drop, or publish code/test remains |
| Operation inspection | index and `ops list/show` pass log-only, artifact-only, corrupt-line, cursor, and historical-result cases without server imports |
| Packaging | no serve extra or direct server dev dependency; regenerated lock has no unexplained server-only package |
| Plain install | isolated wheel install runs help and imports retained modules while server packages are absent |
| Phase boundary | static dashboard command/config/modules/tests and `ReconcileData.dashboard` remain unchanged for Phase 2 |
| Regression | focused suite and full nctl suite pass |
| Safety | no live service, database, Nautobot, Job, desired state, Ansible, dashboard output, event history, artifact history, or SSH state is mutated |

## 9. Exit criteria

Phase 1 is `complete` only when all are checked:

- [ ] All eight tracked `nctl_core/serve` files and seven dedicated serve/bus test files are
      deleted.
- [ ] `nctl --help` has no `serve`, while all 12 intended Phase 1 commands remain.
- [ ] `nctl serve` fails as an unknown command rather than entering a compatibility path.
- [ ] `ServeConfig`, `Config.serve`, serve token/CORS/host/port validation, and `[serve]` examples
      are absent.
- [ ] Obsolete `[serve]` config is positively proven invalid under strict parsing.
- [ ] No FastAPI, Starlette, uvicorn, WebSocket, `/api/v1`, OpenAPI, live-dashboard, server-runner,
      or server-snapshot runtime surface remains in nctl.
- [ ] The subscriber registry, queues, threads, callbacks, publish path, and dedicated tests are
      absent.
- [ ] `EventRecord`, ULID generation, ordered JSONL, returned records, finish behavior, and
      one-warning write-failure isolation are positively tested.
- [ ] `operations_index`, `ops_render`, and `nctl ops list/show` pass their retained tests,
      including an old dashboard-shaped `result.json` artifact.
- [ ] `pyproject.toml` and `uv.lock` contain no serve extra or unexplained server-only dependency.
- [ ] A clean plain wheel installation runs the CLI and retained imports without server packages.
- [ ] Static dashboard behavior and reconcile dashboard coupling remain untouched for Phase 2.
- [ ] Current nctl documentation does not advertise the removed server and still truthfully
      describes the temporary static-dashboard surface.
- [ ] Focused tests and the complete nctl suite pass.
- [ ] Deletion searches have no unexplained active-scope matches.
- [ ] No live deployment or state mutation occurred.
- [ ] `report.md` records measurements, deviations, exceptions, and precise completion status.

Passing tests alone is insufficient if the intended deletion searches or isolated-install proof
were skipped. Conversely, the expected decrease in line or test count is not sufficient if JSONL,
`ops`, CLI, or strict-config behavior regressed.

## 10. Handoff to Phase 2

Phase 2 receives:

- a CLI-only nctl package with the static dashboard as the sole remaining dashboard surface;
- no server dependency, route, runner, live page, or subscriber machinery;
- a strict config model in which only `DashboardConfig` remains from the retired feature family;
- the frozen durable event and operation-inspection proofs;
- an isolated-install proof and regenerated dependency lock;
- the Phase 1 deletion-search exceptions;
- the exact nctl revision and dirty-state ownership;
- one final Phase 1 report; and
- explicit confirmation that `ReconcileData.dashboard`, `_write_dashboard()`, status push,
  dashboard schemas/templates/config, and dashboard tests were not removed early.

Phase 2 may then delete the static dashboard and reconcile coupling without needing to disentangle
ASGI, WebSocket, subscriber, or server dependency behavior.
