# Phase 1 Final Report — Remove nctl Serve and the Subscriber Bus

Parent: [plan.md](plan.md) (all steps).

Status: **complete** (local nctl implementation and verification; no live deployment required or
performed, per plan §1).

Per-step naming note: this initiative uses per-step `reportN.md` files (`report0.md`–`report9.md`,
this file), not the plan's literal `report.md`, matching the convention already established in
`p0/` at explicit user request that session.

## 1. Execution timestamp and evidence

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p1/20260725-152425/` (mode `0700`, files `0600`), containing
`revisions.txt`, `dirty-state.txt`, `uv-version.txt`, `baseline-help.txt`,
`baseline-measurements.txt`, `process-check.txt`, `step1-new-tests.txt`, `step2-full-suite.txt`,
`step3-full-suite.txt`, `dependency-before.txt`, `dependency-after.txt`, `lock-diff-stat.txt`,
`lock-diff-full.txt`, `step6-focused-tests.txt`, `step6-deletion-searches.txt`,
`clean-install.txt`, `clean-install-imports.txt`, `clean-install-pip-list.txt`,
`wheel-filelist.txt`, `full-tests.txt`, `final-measurements-collect.txt`, `final-help.txt`,
`final-deletion-searches.txt`, `final-measurements.txt`, `final-repo-status.txt`.

## 2. Starting and ending revisions

| Repository | Starting (Step 0) | Ending (Step 8) | Dirty state |
|---|---|---|---|
| superproject | `80553b6a8e7a86ad7aa82901b9b308caeb8d049a` | `807d2083135c451cb0a1f5f523d3550e64da5e04` | clean |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | `73096304abcf18bb8fd9d504e9df9166fd959919` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean, **unchanged** |

`nintent` has zero commits from this phase, confirmed by both `git status --short` and the
unchanged revision above — matching plan §3.3 (nintent kernel is explicitly out of scope for
Phase 1).

## 3. Deleted and edited file inventory

Exactly the plan's frozen §5.1/§5.2/§5.3/§5.4 manifest, with one deviation (a commit-hygiene
correction, no scope change — see below).

**Deleted (15 files, matching §5.1 exactly):**
`src/nctl_core/serve/{__init__.py,app.py,artifacts.py,dashboard.py,live_dashboard.html,runner.py,
runtime.py,snapshots.py}`, `tests/test_cli_serve.py`, `tests/test_events_bus.py`,
`tests/test_serve_app.py`, `tests/test_serve_dashboard.py`, `tests/test_serve_operations.py`,
`tests/test_serve_runner.py`, `tests/test_serve_ws.py`.

**Edited (runtime/packaging, §5.2):** `src/nctl_core/cli/main.py` (serve imports/options/command
removed, dashboard preserved), `src/nctl_core/config.py` (`ServeConfig`/`Config.serve`/
`_is_loopback_host()`/now-unused imports removed, `DashboardConfig` preserved),
`src/nctl_core/events.py` (reduced to the frozen durable ULID/EventRecord/OperationLog contract),
`pyproject.toml` (serve extra + dev-group FastAPI/uvicorn removed), `uv.lock` (regenerated,
pure-deletion diff), `example.nctl.toml` (`[serve]` removed only).

**Edited (tests, §5.3):** `tests/test_config.py`, `tests/test_compatibility_snapshots.py`,
`tests/test_cli_surface.py` (new file, not in the plan's literal list but explicitly required by
§5.3's own prose — "add a small top-level contract test"), `tests/test_events.py` (regression
additions), `tests/test_operations_index.py` (regression addition). `test_cli_ops.py` needed no
edit, matching the plan's "edit only if a discovered server coupling requires it" — none was
found.

**Edited (docs, §5.4):** `nctl/README.md`, `nctl/docs/compatibility.md`,
`nctl/docs/event-log.md`, `nctl/docs/output-format.md`, `nctl/docs/usage_example.md`.

**Deviation:** the Step 3 commit (`699bc71`) initially captured only the 15 file deletions — an
invalid pathspec (`tests/test_cli_serve.py`, already removed by an earlier `git rm` in the same
shell session) aborted the `git add` that was also meant to stage the `events.py` reduction and
the `test_compatibility_snapshots.py` edits. The working tree already had the correct content
(report3.md's recorded 980-pass run genuinely exercised it), so this was a commit-hygiene gap, not
a missed edit or an untested change. Fixed with an explicit fixup commit (`747b635`) before Step 5
began; see `report5.md` for the full account. No file inventory item was actually skipped.

## 4. CLI/config contract results

- `nctl --help`: 12 retained commands (`status`, `actual`, `drift`, `dashboard`, `reconcile`,
  `lifecycle`, `render`, `apply`, `ops`, `braindump`, `ssh`, `session`), matching plan §3.2 exactly.
  No `serve`.
- `nctl serve`: exit code 2, `Error: No such command 'serve'.` — Typer's ordinary unknown-command
  failure, not a custom retirement message or hidden compatibility path.
- `Config` has no `serve` field; `[serve]` in `nctl.toml` fails strict `extra="forbid"` validation
  (`test_serve_section_is_rejected_as_unknown`).

## 5. Durable event and `ops` results

- `EventRecord`'s 8-field shape, `generate_ulid()`, and `OperationLog.start()`/`emit()`/`finish()`/
  `_write()` are unchanged except for the deleted `_publish()` call after a successful write.
- New regression tests prove `emit()` still returns the record even when persistence fails, and a
  repeated write failure still warns at most once per `OperationLog` instance.
- The subscriber registry (`Subscriber`, `_SubscriberEntry`, `_subscribers`, `_subscribers_lock`,
  `subscribe()`, `_publish()`) and its dedicated test file are fully deleted.
- `nctl_core.operations_index` and `nctl ops list/show` are unchanged and independently tested;
  a new regression test proves a historical `result.json` containing a removed `dashboard` field
  and `reconciliation_status` is listed as an opaque artifact (name + size only), never parsed or
  rejected.

## 6. Dependency before/after and clean-install proof

- Before: `uv.lock` resolved 35 packages; `fastapi`/`uvicorn` reachable via the `serve` extra and
  the dev group.
- After: `uv.lock` resolved 26 packages (−9: `click`, `fastapi`, `httptools`, `python-dotenv`,
  `starlette`, `uvicorn`, `uvloop`, `watchfiles`, `websockets`). `git diff uv.lock` is a
  pure-deletion diff (370 lines removed, 0 added) — no unrelated version changes. `httpx`/`respx`
  remain, reachable only via `nctl` (core Nautobot client / dev group).
- Clean-install proof (Step 7, isolated `mktemp -d` environment, not the developer `.venv`): a
  built wheel installed with exactly 20 core packages (no dev group, no extra) ran
  `nctl --help` (12 commands, no `serve`) and imported `nctl_core.cli.main`, `nctl_core.events`,
  `nctl_core.operations_index`, `nctl_core.ops_render` successfully.
  `importlib.util.find_spec()` confirmed `fastapi`, `starlette`, `uvicorn`, `websockets`,
  `httptools`, `uvloop`, `watchfiles`, and both `python_dotenv`/`dotenv` spellings absent. The
  built wheel's file list contains no `nctl_core/serve/*` entry.

## 7. Focused and full test summaries

- Step 1 (pre-deletion): 43 passed, 3 intentionally failing (each maps to a Section 4 contract
  implemented in Steps 2–3).
- Step 2: `test_config.py` 23 passed, `test_cli_surface.py` 3 passed (both former intentional
  failures now pass); static dashboard scope guard 29 passed.
- Step 3: focused set (`test_events.py`, `test_compatibility_snapshots.py`,
  `test_operations_index.py`, `test_cli_ops.py`) 33 passed; full suite 980 passed.
- Step 6 (plan's exact focused list): 72 passed.
- Step 8 (final): full suite **980 passed**, 980 collected, `uv lock --check` clean.

## 8. Source/test/collected-test before/after measurements

| Metric | Before | After | Delta |
|---|---|---|---|
| `nctl --help` top-level commands | 13 | 12 | −1 (`serve` removed) |
| Collected tests | 1029 | 980 | −49 |
| Tracked source lines | 19186 | 18137 | −1049 |
| Tracked test lines | 21140 | 20025 | −1115 |
| `uv.lock` resolved packages | 35 | 26 | −9 |

The −49 test delta reconciles exactly: −50 dedicated serve/bus tests, −4 compatibility HTTP/WS
tests, +5 net new regression tests (Step 1 added 3 CLI-surface + 2 events + 1 operations-index
tests and replaced 2 old serve-config tests with 1 new one: +3−1+2+1 = +5). These are diagnostic
measurements, not quotas, per plan §2.2.

## 9. Deletion-search exceptions

Zero unexplained active-scope matches. The full plan-specified 16-token search
(`nctl serve`, `nctl_core.serve`, `nctl.serve.v1`, `ServeConfig`, `NCTL_SERVE_TOKEN`, `/api/v1`,
`/api/v1/ws`, `FastAPI`, `Starlette`, `uvicorn`, `WebSocket`, `subscribe(`, `Subscriber`,
`_SubscriberEntry`, `_subscribers`, `_publish(`) against `src/`, `tests/`, `pyproject.toml`,
`uv.lock`, `example.nctl.toml`, `README.md`, `docs/` returns zero matches (Step 6 found and fixed
one leftover docstring mention in `test_compatibility_snapshots.py`; Step 8 reran the full list
clean). A structural import trace (`grep` for `import serve` / `from nctl_core.serve` / relative
serve imports) also returns zero matches.

Repository-wide matches outside `nctl/` (this roadmap and its own `p0`/`p1` reports, the parent
roadmap, the refactoring vision, and other-initiative/historical docs — `braindump`,
`core_reconcile`, `vm/p3/plan.md`, `fix_sshkey`, root `README.md`) are all outside Phase 1's own
scope (plan §5.4 names exactly five nctl-internal files; root `README.md` and cross-initiative
docs are Phase 4 work per the parent roadmap). The explicitly keep-shared `ansible_agdev/api`
FastAPI webhook is present and untouched.

## 10. Static dashboard / Phase 2 boundary confirmation

`nctl dashboard`, `nctl_core.dashboard`, `nctl_core.dashboard_render`, `DashboardConfig`/
`Config.dashboard`, `[dashboard]` in `example.nctl.toml`, `nctl.dashboard.v1`,
`ReconcileData.dashboard`, and all dashboard/reconcile-executor tests are unchanged — verified both
by the Step 3/6/8 dashboard-scope-guard test runs (29 passed each time) and by the Step 8 diff
inspection, which found no `nctl_core/dashboard/`, `dashboard_render.py`, or
`reconcile/executor.py` line in the entire Phase 1 diff.

## 11. No live/state mutation confirmation

No Nautobot access, database migration, Job trigger, desired-state write, Ansible run, or
generated-dashboard mutation occurred at any step — every step operated on local nctl source,
tests, config, docs, and a disposable temp directory (Step 7, explicitly removed after use). The
Step 0 process/port recheck found no `nctl serve` process and no listener on 8300, matching the
Phase 0 finding that the stray process was already stopped.

## 12. Omitted, substituted, or failed checks

None. Every plan Step 0–8 action, gate, and required proof was executed as specified; the one
deviation (§3 above) was a commit-hygiene correction discovered and fixed within the same phase,
not an omission — the corrected commit reproduces exactly what the reports already described and
tested.

## 13. Exit-criteria table

| Exit criterion (plan §9) | Status | Evidence |
|---|---|---|
| All 8 `nctl_core/serve` files + 7 dedicated test files deleted | ✅ | report3.md; §3 above |
| `nctl --help` has no `serve`; all 12 Phase 1 commands remain | ✅ | report2.md, report8.md; `final-help.txt` |
| `nctl serve` fails as unknown command | ✅ | report2.md, report8.md; `final-help.txt` |
| `ServeConfig`/`Config.serve`/serve validation/`[serve]` example absent | ✅ | report2.md |
| `[serve]` config positively proven invalid under strict parsing | ✅ | report2.md; `test_serve_section_is_rejected_as_unknown` |
| No FastAPI/Starlette/uvicorn/WebSocket/`/api/v1`/OpenAPI/live-dashboard/runner/snapshot surface remains | ✅ | report3.md, report6.md, report8.md; `final-deletion-searches.txt` |
| Subscriber registry/queues/threads/callbacks/publish/tests absent | ✅ | report3.md; `final-deletion-searches.txt` |
| `EventRecord`/ULID/ordered JSONL/returned records/finish/one-warning isolation positively tested | ✅ | report1.md, report3.md; `tests/test_events.py` |
| `operations_index`/`ops_render`/`nctl ops list/show` pass retained tests incl. historical `result.json` | ✅ | report1.md, report3.md; `tests/test_operations_index.py` |
| `pyproject.toml`/`uv.lock` have no serve extra or unexplained server-only dependency | ✅ | report4.md; `dependency-after.txt`, `lock-diff-full.txt` |
| Clean plain wheel install runs CLI and retained imports without server packages | ✅ | report7.md; `clean-install*.txt`, `wheel-filelist.txt` |
| Static dashboard / reconcile dashboard coupling untouched for Phase 2 | ✅ | §10 above; report2.md, report3.md |
| Current nctl docs no longer advertise removed server, still describe static dashboard | ✅ | report5.md |
| Focused tests and complete nctl suite pass | ✅ | report6.md, report8.md; `full-tests.txt` |
| Deletion searches have no unexplained active-scope matches | ✅ | report6.md, report8.md; `final-deletion-searches.txt` |
| No live deployment or state mutation occurred | ✅ | §11 above |
| This report records measurements, deviations, exceptions, and completion status | ✅ | this document |

## 14. Handoff to Phase 2

Per plan §10: Phase 2 receives a CLI-only nctl package (12 commands, static dashboard is the sole
remaining dashboard surface), no server dependency/route/runner/live-page/subscriber machinery, a
strict config model where only `DashboardConfig` remains from the retired-feature family, the
frozen durable-event and operation-inspection proofs, the isolated-install proof and regenerated
lock (§6), the deletion-search exceptions (§9), the exact nctl revision
(`73096304abcf18bb8fd9d504e9df9166fd959919`) and dirty-state ownership (clean), this final report,
and explicit confirmation (§10) that `ReconcileData.dashboard`, `_write_dashboard()`, status push,
dashboard schemas/templates/config, and dashboard tests were not removed early.
