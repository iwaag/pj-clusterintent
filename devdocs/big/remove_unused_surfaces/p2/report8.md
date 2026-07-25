# Phase 2 Final Report — Remove the Static Dashboard and Reconcile Coupling

Parent: [plan.md](plan.md) (all steps).

Status: **complete** (local nctl implementation and verification; no live deployment required or
performed, per plan §1/§3.3).

Per-step naming note: this initiative uses per-step `reportN.md` files (`report0.md`–`report8.md`,
this file), matching the convention established in `p0/`/`p1/` at explicit user request.

## 1. Execution timestamp and evidence

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/` (mode `0700`, files `0600`), containing
`revisions.txt`, `dirty-state.txt`, `uv-version.txt`, `baseline-help.txt`,
`baseline-measurements.txt`, `baseline-dashboard-matches.txt`, `deletion-searches-baseline.txt`,
`step1-new-tests.txt`, `step2-results.txt`, `step3-focused-tests.txt`, `step3-full-tests.txt`,
`step4-full-tests.txt`, `step5-focused-tests.txt`, `step5-full-tests.txt`,
`deletion-searches-final.txt`, `step6-model-inspection.txt`, `step6-wheel-build.txt`,
`wheel-filelist.txt`, `final-tests.txt`, `final-collect.txt`, `final-lock-check.txt`,
`final-help.txt`, `final-measurements.txt`, `final-repo-status.txt`.

## 2. Starting and ending revisions

| Repository | Starting (Step 0) | Ending (Step 7) | Dirty state |
|---|---|---|---|
| superproject | `ced6fe217aee872d752c36929850c018775b6fd7` | `5db19964774577064fde6c64dea2b683ac3cb3b5` | clean |
| `nctl` | `73096304abcf18bb8fd9d504e9df9166fd959919` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean, **unchanged** |

`nintent` has zero commits from this phase — matches plan §3.3 (nintent's cache/UI/link residue is
explicitly Phase 3 territory).

## 3. Exact deleted/edited file inventory and deviations

**Deleted (9 files, matching plan §5.1 exactly):**
`src/nctl_core/dashboard/{__init__.py,html.py,push.py,template.html}`,
`src/nctl_core/dashboard_render.py`, `tests/test_cli_dashboard.py`, `tests/test_dashboard_html.py`,
`tests/test_dashboard_push.py`, `tests/test_dashboard_render.py`.

**Edited (runtime/config, §5.2):** `src/nctl_core/cli/main.py` (dashboard command/options/import
removed, reconcile docstring's dashboard promise removed), `src/nctl_core/config.py`
(`DashboardConfig`/`Config.dashboard` removed), `src/nctl_core/reconcile/executor.py`
(`ReconcileData.dashboard`, `_write_dashboard()`, its call and import removed; module docstring
and two stale "Phase 5 server" comments updated), `src/nctl_core/drift_render.py` (dashboard
cross-reference removed from docstring), `src/nctl_core/sources/desired.py` (dashboard dropped
from an active compute-inertness comment), `example.nctl.toml` (`[dashboard]` section removed).

**Edited (shared tests, §5.3):** `tests/test_cli_surface.py` (11-command retained set, new
dashboard-unknown-command test), `tests/test_config.py` (new `[dashboard]` rejection test),
`tests/test_compatibility_snapshots.py` (removed `nctl.dashboard.v1`; replaced the reconcile
schema's dashboard-bearing floor check with an exact 16-field assertion),
`tests/test_reconcile_executor.py` (deleted `_stub_dashboard()` + 23 calls + the
dashboard-degradation test; added one new dashboard-free artifact/no-PATCH test),
`tests/test_operations_index.py` (unchanged — the historical opaque-artifact test already covered
the plan §4.5 exception with no wording change needed),
`tests/test_vm_p3_compute_stays_inert.py` (dashboard dropped from module docstring, no behavior
change).

**Edited (current docs, §5.4):** `nctl/README.md`, `nctl/docs/compatibility.md`,
`nctl/docs/output-format.md`, `nctl/docs/usage_example.md`. `docs/event-log.md` needed no edit
(re-searched, zero dashboard coupling found, matching the plan's own prediction).

**Deviation (Step 2/3 sequencing, recorded live in report2.md/report3.md):** the plan splits
"remove command/config/implementation" (Step 2) from "decouple reconcile terminal handling" (Step
3), but `cli/main.py` transitively imports `reconcile/executor.py`, which still imported the
just-deleted `dashboard_render` module through the end of Step 2 — so CLI-level import
verification (`nctl --help` etc.) was genuinely blocked from the end of Step 2 until Step 3
removed that import. This was a real interdependency in the plan's own step boundary, not an
implementation mistake: Step 2's config-only verification (24/24 tests) completed and passed in
full; CLI-level verification resumed and passed (74/74, including all four Step-1
previously-intentional failures) once Step 3 landed. No file inventory item was skipped or done
out of its assigned step's scope — only the *verification* of Step 2's CLI-level claim was
deferred one step, and that deferral is recorded in both step reports rather than silently
absorbed into either commit.

No other deviation occurred. Every other plan §5.1–§5.4 item was implemented exactly as specified.

## 4. CLI/config/model-field results

- `nctl --help`: **11 commands** (`status actual drift reconcile lifecycle render apply ops
  braindump ssh session`) — no `dashboard`, no `serve`.
- `nctl dashboard`: exit 2, `Error: No such command 'dashboard'.` — Typer's ordinary
  unknown-command failure, no custom retirement message or hidden path.
- `nctl serve`: exit 2, same ordinary failure (unchanged since Phase 1, reconfirmed here).
- `Config.model_fields`: no `dashboard`/`serve`; both `[dashboard]` and `[serve]` fail strict
  `extra="forbid"` validation (`test_dashboard_section_is_rejected_as_unknown`,
  `test_serve_section_is_rejected_as_unknown`).
- `ReconcileData.model_fields`: exactly the 16 Phase 0 frozen fields (including `ssh_preflight`,
  excluding `dashboard`), asserted by equality (not superset) in
  `test_reconcile_data_fields_are_exactly_the_frozen_set_with_no_dashboard_field`.

## 5. Reconcile scenario matrix results

All seven required §6 terminal scenarios are covered by pre-existing `test_reconcile_executor.py`
tests (report5.md §3 has the full scenario→test mapping) plus one new test added in Step 5:
`test_already_converged_terminal_artifacts_have_no_dashboard_write_or_status_patch`, which
installs a fail-fast `NautobotClient.rest_patch` sentinel, asserts no `dashboard` key in the
serialized envelope, and asserts `index.html`/`drift.json` are absent from the operation artifact
directory while `result.json`/`plan.json`/`drift-final.json` are present. `reconcile/executor.py`
has zero `rest_patch` callers after Step 3 (the only prior caller, `dashboard/push.py`, was
deleted in Step 2), making the no-PATCH proof structural, not just fixture-specific.

## 6. Final drift/result/event-ordering evidence

Preserved unchanged throughout: plan and initial-drift persistence, final full-cluster drift
computation and `final_drift_path`, `summary`/`scope_summary`, `rounds`/`ActionResult`/per-round
SSH evidence, `manual_review`/`unsupported`, truthful `progress_made`, top-level `ssh_preflight`,
state/`ok` mapping, `drift_resolved`/`non_converged` event emission, `result.json` persisted
before `finished`, one terminal `finished` event, reconcile locking, and historical operation
indexing. The diff around `_finish()`/`_persist_terminal_result()` is comment-only (two stale
"Phase 5 server" references updated to name `nctl ops show`) — no reorder, no dropped evidence.

## 7. No-HTML/no-PATCH evidence

- Zero `index.html` or dashboard-owned root `drift.json` write anywhere in the reconcile path
  (proved structurally and by direct artifact-directory inspection, §5 above).
- Zero `reconciliation_status`/`reconciliation_checked_at` writer, route, or literal anywhere in
  `src/` (deletion search, report6.md §1).
- The four remaining `rest_patch` call sites in the whole package
  (`lifecycle.py`, two in `braindump.py`, `reconcile/ledger.py`'s `execute_link_actual_node`
  device-link PATCH) are all intentionally retained, unrelated mutations — none targets the
  retired reconciliation-cache fields.

## 8. Focused and full test summaries

- Step 1 (pre-deletion): 4 new/changed assertions intentionally failed, mapped 1:1 to Steps 2–3;
  29 unrelated tests in the same three files passed.
- Step 2: config-only verification 24/24 passed; CLI-level verification blocked pending Step 3
  (recorded deviation, §3 above).
- Step 3: `test_reconcile_executor.py` 41/41; the four Step-1 frozen files together 74/74 (all
  four previously-intentional failures now genuinely pass); full suite 953/953.
- Step 5 (plan's exact focused command): 112/112. New artifact/no-PATCH test: 1/1.
- Step 7 (final): full suite **954 passed**, 954 collected, `uv lock --check` clean.

## 9. Before/after source/test/collected-test measurements

| Metric | Before (Step 0) | After (Step 7) | Delta |
|---|---|---|---|
| `nctl --help` top-level commands | 12 | 11 | −1 (`dashboard` removed) |
| Collected tests | 980 | 954 | −26 |
| Tracked source lines (`src/`) | 18,137 | 17,763 | −374 |
| Tracked test lines (`tests/`) | 20,025 | 19,380 | −645 |

The −26 test delta reconciles exactly: −29 dedicated dashboard tests (Step 2), −1
dashboard-degradation test (Step 3), +3 net new contract tests (Step 1), +1 new artifact/no-PATCH
test (Step 5) = −26. These are diagnostic measurements, not quotas, per plan §2.2.

## 10. Package/wheel proof

Built in a fresh `mktemp -d` directory: succeeded, 74-entry wheel file list, zero `dashboard`
matches (no `nctl_core/dashboard/*`, `dashboard_render.py`, or template asset packaged). Plain
imports of `nctl_core.cli.main` and `nctl_core.reconcile.executor` succeed.
`pyproject.toml`/`uv.lock` unchanged since Phase 1 — no dashboard-only dependency was found;
`httpx`/`pydantic` remain reachable through other retained consumers.

## 11. Deletion-search exceptions

The plan's 16-token search is clean except three named, expected exceptions (reproduced
identically in both Step 6 and Step 7 reruns):

- `reconciliation_status`: one match, the literal historical opaque-artifact fixture in
  `tests/test_operations_index.py` (plan §4.5/§5.3's named exception — evidence, not a reader).
- `[dashboard]`: two matches, both inside the new `test_dashboard_section_is_rejected_as_unknown`
  (proving the section is now *rejected*).
- `index.html`: three matches, all inside the new dashboard-free artifact test (proving the file
  is *absent*).

Root/cross-initiative matches (`README.md`, `README_DEV.md`, `devdocs/big/{braindump,
better_usability, core_reconcile, vm}/roadmap.md`, `devdocs/big/vm/p3/plan.md`, and this
initiative's own roadmap) are all explicitly out-of-scope Phase 4/historical territory per plan
§3.3/§5.4 — confirmed to contain no newly introduced instruction, only the already-known set the
plan predicted (report4.md §4).

## 12. Phase 3 handoff and intentionally retained nintent residue

Phase 3 receives:

- an 11-command, CLI-only nctl package with no static dashboard, dashboard schema/config, status
  push, or reconcile presentation dependency;
- exact `nctl.reconcile.v2` fields (16, frozen, no `dashboard`) and retained result/event
  ordering;
- dashboard-free terminal-state and structural no-PATCH proofs (§5/§7 above);
- unchanged durable JSONL and `nctl ops` behavior;
- historical result compatibility through opaque artifact listing only;
- the exact nctl revision (`7a0f2cf035179fbea5deed4cacb05573f8c8dffa`) and dirty-state ownership
  (clean);
- this final report; and
- explicit confirmation that **nintent still temporarily contains**: the four cache fields
  (`DesiredNode.reconciliation_status`/`reconciliation_checked_at`,
  `DesiredService.reconciliation_status`/`reconciliation_checked_at`), their filters/tables/
  templates, the dashboard URL/navigation/redirect, and the `dashboard_url` deployment setting —
  none of these were touched this phase (nintent's revision is byte-for-byte unchanged, §2 above),
  matching plan §3.3's explicit out-of-scope boundary. Phase 3 may now add migration `0016` and
  remove this residue without any remaining nctl writer or reader.

## 13. Every omitted, substituted, or failed check

One recorded deviation only (§3 above: Step 2/Step 3 CLI-verification sequencing, due to a genuine
cross-step import dependency in the plan itself, not an omission — every check the plan required
was still executed, just one step later than the plan's own step-2-only gate text implied). No
other check was omitted, substituted, or skipped. No live Nautobot/database/Job/desired-state/
Ansible/dashboard-output mutation was attempted or performed at any step.

## 14. Exit-criteria table

| Exit criterion (plan §10) | Status | Evidence |
|---|---|---|
| All five static dashboard implementation files + four dedicated test files deleted | ✅ | report2.md; §3 above |
| `nctl --help` exposes exactly the 11 frozen retained commands | ✅ | report3.md, report7.md; `final-help.txt` |
| `nctl dashboard` and `nctl serve` both fail as ordinary unknown commands | ✅ | report3.md, report7.md |
| `DashboardConfig`, `Config.dashboard`, `[dashboard]`, dashboard CLI options, `nctl.dashboard.v1` absent | ✅ | report2.md, report4.md, report6.md |
| Obsolete `[dashboard]`/`[serve]` sections positively proven invalid | ✅ | report1.md, report2.md |
| No dashboard package, renderer, template, HTML write, dashboard-owned drift snapshot, packaged asset remains | ✅ | report2.md, report5.md, report6.md; `wheel-filelist.txt` |
| No status-push writer, cache-field PATCH, row lookup, counter, or warning behavior remains | ✅ | report3.md, report5.md, report6.md |
| `ReconcileData` has exactly the 16 Phase 0 frozen fields, keeps schema `nctl.reconcile.v2` | ✅ | report1.md, report3.md, report6.md |
| `_write_dashboard()`/call, dashboard warnings, `_stub_dashboard()`/23 calls, degradation test absent | ✅ | report3.md |
| Planned/converged/manual-review/non-converged/failed paths retain state, summaries, progress, SSH, artifacts, events | ✅ | report5.md |
| Applicable paths persist fresh final drift; failures after side effects remain truthful | ✅ | report5.md §3 (existing test coverage) |
| Current `result.json` has no dashboard key, persisted before `finished` | ✅ | report5.md §2 |
| Reconcile performs no HTML/dashboard-drift write, no reconciliation-cache PATCH | ✅ | report5.md, report6.md |
| Historical dashboard-bearing result artifacts remain listable without migration/parsing | ✅ | report6.md §1 (`test_operations_index.py` exception) |
| Current nctl docs describe only retained inspection paths, promise no replacement GUI | ✅ | report4.md |
| Focused tests and complete nctl suite pass | ✅ | report5.md, report7.md; `final-tests.txt` |
| Deletion searches and wheel inspection have no unexplained active matches | ✅ | report6.md, report7.md |
| No live deployment, database/schema change, generated-output cleanup, or operational mutation occurred | ✅ | §13 above; every step report's evidence section |
| Final report records exact evidence, exceptions, deviations, and completion status | ✅ | this document |

Every plan §10 exit criterion is met. Phase 2 status: **complete**.
