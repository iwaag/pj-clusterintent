# Phase 0 Final Report — Freeze the Removal Contract and Baseline

Parent: [plan.md](plan.md), Step 9 ("Produce the Phase 0 report").

This file is the plan's required final report, named `report9.md` rather than `report.md` to match
this session's requested per-step `report[N].md` naming convention; it fulfills plan §9's Step 9
content requirements in full and is the authoritative Phase 0 record.

## 1. Status

**`complete`.**

All Section 9 exit-criteria boxes are met. One unexpected finding (a live `nctl serve` process) was
surfaced during Step 6, escalated to the operator rather than silently resolved, and closed with
explicit operator approval before the gate was declared met — see §8 and §13.

## 2. Execution timestamp and evidence directory

Executed 2026-07-25, starting 14:50:28 JST. Private evidence directory:
`.local/remove-unused-surfaces/p0/20260725-145028/` (mode `0700`; all files inside `0600`):
`step0-boundary.txt`, `step2-runtime.txt`, `nctl-command-help.txt`, `tracked-token-matches.tsv`,
`manifest.tsv`, `process-audit.txt`, `vm-plan-diff.txt`. (`worktrees.txt`, `jobs.txt`,
`cache-counts.json`, `dashboard-path.txt`, `local-invocation-paths.txt`, `consumer-audit.txt` from
the plan's suggested-file list were folded into the files above rather than kept as separate empty
placeholders — every suggested category is covered.)

## 3. Root/submodule revisions and dirty-state ownership

| Repository | HEAD (end of Phase 0) | Dirty | Owner |
|---|---|---|---|
| superproject | `e6a6fab...` (Step 8 commit) | untracked-only: `p0/plan.md`, `roadmap.md`, `devdocs/vision/` | pre-existing user documentation, not this execution's write |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean | — |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean | — |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | clean | — |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean | — |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean | — |

Re-verified clean/unchanged at both the start (report1.md) and end (this report) of the phase; no
submodule advanced during execution. Full detail: report1.md.

## 4. Live installed nintent revision, migration state, running-Job count

Installed `nautobot-intent-catalog` 0.9.0, commit `ad9d36397d23c269ad748e13acbccc532fa29f52`
(differs from local submodule HEAD as expected — normal pre-rebuild deployment lag, not drift).
Migrations: `0001`–`0014` applied, `0015`/`0016` absent — live is exactly on `0014`.
`makemigrations --check --dry-run`: no changes detected. `JobResult` PENDING/RUNNING count: 0.
Re-verified unchanged at the end of the phase (§7 above). Full detail: report2.md.

## 5. Aggregate cache counts and generated dashboard path

`DesiredNode.reconciliation_status`: `{converged: 5}` (5/5 total, 5/5 `reconciliation_checked_at`
non-null). `DesiredService.reconciliation_status`: `{'': 5, converged: 1}` (6 total, 1/6
`reconciliation_checked_at` non-null). Generated dashboard directory:
`/Users/eiji/.local/state/nctl/dashboard` (exists; `index.html` 13905 bytes, `drift.json` 1106
bytes, names/sizes only — contents not read). Configured `dashboard_url`: unset (no local
`nctl.toml`). Full detail: report2.md.

## 6. Current command/config/dependency surface

`nctl --help` lists 13 commands including `dashboard`/`serve`; nine `nctl.toml` config sections
including `[dashboard]`/`[serve]`; `serve` is a distinct `pyproject.toml` optional-dependency extra
(`fastapi`, `uvicorn[standard]`), also unconditionally duplicated in the `dev` dependency group.
`ReconcileData` has exactly one field beyond the frozen Section 4 target set (`dashboard`);
`RoundSummary`, `EventRecord`, `OperationRecord`, and the `nctl.ops.list.v1`/`nctl.ops.show.v1`
schema names already match the frozen contract exactly. Full detail: report3.md.

## 7. Manifest counts and decisions

102 manifested tracked files across all repositories: **24 delete**, **32 edit**, **42 historical**,
**4 keep-shared** (plus five explicitly protected shared-kernel modules with zero token matches:
`artifacts.py`, `operations_index.py`, `ops_render.py`, `output.py`, `reconcile/lock.py`). The
`delete` set is exactly plan §5's minimum list plus the known `test_events_bus.py` addition plus
one import-trace discovery (`nctl_core/serve/artifacts.py`, a server-only public-artifact allowlist
adapter with no retained importer). Every `nintent` `edit` row was spot-checked by reading the
actual `reconciliation_status`/`dashboard_url` coupling, not inferred from filename.
`ansible_agdev/api/` is a genuinely unrelated FastAPI webhook service — `keep-shared`, not `delete`,
despite matching the generic structural tokens. Dependency-reachability findings: `dev`-group
`fastapi`/`uvicorn` duplicates become removable once `serve` tests are deleted; `httpx` (core
Nautobot client) and `respx` (13 non-deleted test consumers) must both be retained. Full detail:
report4.md, report5.md, report8.md.

## 8. Consumer audit boundary and result

Audited: tracked Makefiles/CI/compose/Ansible/shell wrappers (zero relevant matches beyond
`ansible_agdev/Makefile`'s retained `nctl reconcile`/`render` calls); crontab (empty); user/system
LaunchAgents/LaunchDaemons (none relevant); `launchctl list` (none relevant); processes and port
8300; Docker containers/published ports; tracked reverse-proxy config (none); shell history
(0 exact-command matches for `nctl serve`/`nctl dashboard`).

**One live consumer was found**: an `nctl serve` process (PID 27946/27948) had been running since
2026-07-20 10:18:31 and was the sole `127.0.0.1:8300` listener. Per plan §6, execution paused and
the operator was asked directly rather than silently classifying it as "no consumer" or killing it
unilaterally. The operator confirmed it was accidental/stale and approved stopping it; it was
stopped (`kill 27948 27946`) and re-verified absent (`ps`, `lsof`) before the audit was closed. Full
detail: report6.md.

## 9. Zero-listener result for port 8300

Confirmed zero at both audit-closure time (report6.md) and at this final re-check (§7 command log
above, `lsof -nP -iTCP:8300 -sTCP:LISTEN` returns no rows).

## 10. Frozen Section 4 contracts

Referenced, not redefined: plan.md §4.1 (removed contracts), §4.2 (retained 13-command CLI
surface), §4.3 (`ReconcileData` exact final field set, `dashboard` removed in place, no `v3`),
§4.4 (retained `EventRecord`/`OperationLog` contract, subscriber bus deleted), §4.5 (retained
`nctl_core.operations_index`/`ops_render` contract, server adapters including the newly found
`serve/artifacts.py` deleted), §4.6 (retained inspection path: `drift`/`reconcile`/`ops`/
Braindump), §4.7 (migration `0016` depends directly on `0015`, four-column removal, documented
rollback). Step 3's live capture (report3.md) confirms the current surface is already
field-for-field consistent with this frozen contract except for the named deltas.

## 11. VM Phase 3 current step, amendment summary, coordinated owner/sequence

VM Phase 3's latest complete report is `report3.5.md` (Step 5); Step 6 has not begun (report1.md).
`devdocs/big/vm/p3/plan.md` was amended with all ten plan §7 Step 7 semantic changes: a new
supersession/coordinated-rollout note, and replacement of every dashboard/status presentation
requirement (the `desired_mac_mismatch` contract, deliverables, Steps 5/6/8/11, Phase Handoff) with
structured JSON drift, human-readable CLI drift output, and `nctl ops list/show` evidence. No
compute/endpoint-MAC/migration-`0015`/seed/safety/no-actuation requirement changed. `git diff
--check` passed with no output. Coordinated owner and sequence (plan §3): this initiative owns
`serve`/dashboard/subscriber-bus deletion, the four nintent cache fields, migration `0016`, and
active-documentation contraction; VM Phase 3 continues to own compute/endpoint-MAC/dnsmasq
semantics and its own seed/proof. Required order:
`Phase 0 -> amend VM Phase 3 plan -> remove_unused_surfaces Phases 1-3 -> finish VM Phase 3 Step 6
-> remove_unused_surfaces Phase 4 + VM Phase 3 Step 7 -> one coordinated maintenance window
(nintent revision, migration 0015, migration 0016, matching nctl revision) -> revised VM Phase 3
Step 8+ and remove_unused_surfaces Phase 5`. Full detail: report7.md.

## 12. Confirmation that no live mutation occurred

No database row was written, no migration was opened or applied, no dashboard/serve command ran,
no container was restarted, no Job was triggered. The only state-changing action in the entire
phase was stopping the two stray `nctl serve`/`uv run` processes found in §8/§9, performed with
explicit operator approval as a safety correction (not a plan-scoped mutation) — everything else
was `git`, `docker ps`, `lsof`, `ps`, `crontab -l`, `launchctl list`, `--help`, read-only ORM
aggregation, `showmigrations`, `makemigrations --check --dry-run`, file reads/listings, and tracked
documentation edits (this report series plus `devdocs/big/vm/p3/plan.md`).

## 13. Discrepancies, omissions, and substituted checks

- The plan's suggested evidence file list (`worktrees.txt`, `jobs.txt`, `cache-counts.json`,
  `dashboard-path.txt`, `local-invocation-paths.txt`, `consumer-audit.txt`) was consolidated into
  fewer, more complete files (see §2) rather than kept as separate near-empty placeholders; every
  suggested content category is present somewhere in the evidence set.
- `worktrees.txt` specifically: this repository has no additional git worktrees beyond the normal
  checkout (`git submodule status` in report1.md is the complete worktree-equivalent state for a
  submodule-based repository); no separate file was written for this negative result beyond noting
  it here.
- The live `nctl serve` process (§8) is the one real discrepancy from an assumed "no active
  consumer" baseline. It was not silently resolved: execution stopped, the operator was asked via a
  narrow, context-rich question, and the resolution (operator-approved stop) is fully recorded in
  report6.md and this report. This is the only place completion language required qualification,
  and it does not reduce the final status below `complete` because the gate condition (§9 above) is
  now positively true and the resolution path matches the plan's own required procedure exactly.
- No other discrepancy, omission, or substituted check was found. Read-only substitutions where a
  nominally read-only command would have written a side effect (e.g. using `--help` instead of
  running `nctl dashboard`/`nctl serve`) are documented in report0.md/report3.md, not omissions.

## 14. Exit-criteria table

| Criterion (plan §9) | Status | Evidence |
|---|---|---|
| Exact root/submodule tuple and dirty ownership recorded | met | report1.md, §3 above |
| Running nintent commit, migration state, active Job count recorded | met | report2.md, §4 above |
| Cache counts by status and exact generated directory recorded without contents | met | report2.md, §5 above |
| Current nctl commands, config sections, schemas, server dependencies captured | met | report3.md, §6 above |
| Every source/test/config/current-doc/history/local-deployment match classified | met | report4.md, report8.md, §7 above |
| `test_events_bus.py` and any other newly found dedicated surface included | met | report4.md, report5.md (`serve/artifacts.py`) |
| Shared operation/evidence helpers explicitly protected from deletion | met | report5.md, report8.md |
| User-confirmed no-consumer decision backed by repository/automation/process/listener/container/local-service checks | met | report6.md, §8 above |
| No nctl serve process listening on port 8300 | met | report6.md, §9 above (re-verified) |
| Final `ReconcileData`, JSONL event, operation-index, `ops` contracts frozen | met | plan.md §4, report3.md, §10 above |
| Active VM Phase 3 plan has no removed-surface acceptance requirement | met | report7.md, §11 above |
| VM Phase 3 and this initiative share one explicit migration/deployment sequence | met | report7.md, §11 above |
| No runtime code, database row, migration state, Job, generated dashboard, service, or operation artifact changed | met | §12 above |
| `report.md` records all omissions/discrepancies and uses precise completion language | met (this file) | §13 above |

All fourteen criteria are met. Phase 0 is **complete**; Phase 1 may proceed using the frozen
manifest (report4.md/report5.md/report8.md), the Section 4 contracts, and the amended VM Phase 3
plan (report7.md) without relying on conversational context.
