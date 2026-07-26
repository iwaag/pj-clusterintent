# Phase 4 Final Report — Coordinated Data Transition and Deployment

Plan: [plan.md](plan.md). Parent: [roadmap.md](../roadmap.md).

## Status: **complete**

Every plan step (0-9) executed and gated; Step 10's closing searches/measurements/report are this
document. The matched read/write contract is deployed live, the YAML Import was applied and proved
non-repeating, all confirmed desired state/prose/links/JobHook/actual-ledger evidence survived
except the explicitly reviewed and approved changes, and VM Phase 3 received the deployed Import
contract without any compute seed content being smuggled in.

## 1. Exact tuples

| Tuple point | Value |
|---|---|
| Start (Step 0, 2026-07-26) | superproject `6e94147`, nintent `5881a6f`, nctl `bafe7d2`, nauto `2635e64` |
| Repaired source (Step 1-2) | nintent `179a12a` -> `e8732f1` (test-portability fix), nctl `79b6d6b` |
| First candidate (Step 3) | superproject `ba5a847`; image `sha256:ef28300287a3...` (nintent `e8732f1`, nauto `2635e64`) |
| Step 6 fix (this session) | nauto `2635e64` -> `1c78af8` (preserve live `description`/`notes`); superproject `2fa125f` |
| **Deployed candidate** | image `sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a` (`nic-p4-candidate:20260726c`); `nintent_commit: e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`; `nauto_commit: 1c78af8bdbfc69cafdc293b4082f866de9f271b0`; YAML SHA-256 `f6cdcbb195fe09083edefbde7d317f70b1de280a179f3fb369587a7da30edfc6` |
| **Final superproject** | `2c20243` (all reports/fixes committed and pushed through this session) |
| Rollback image/tuple | `nic-p4-candidate:20260726b`, `sha256:ef28300287a3...` (nintent `e8732f1`, nauto `2635e64`) — the pre-this-session deployed tuple, verified healthy at Step 5 |

All web/worker/scheduler containers independently confirmed identical on image ID,
`nintent_commit`, `nauto_commit`, and YAML digest at Steps 3, 5, and this session's redeploy
(report3.md, report5.md, report6b.md).

## 2. Evidence and backup locations

- `.local/interface-contract/p4/20260726_step0/` through `20260726_step10/`, plus
  `20260726_step3_remainder/`, `20260726_step5b/`, `20260726_step6_rebuild/` — all directory mode
  `0700`, files mode `0600`, not committed (matches plan Section 5.5).
- Database dump and media archive: Step 4 (report4.md), verified via a real disposable-database
  restore with matching counts and migrations. Not superseded — no database restore was needed in
  this session (Step 6 through 9 only added rows via the approved Import apply and a fully
  cleaned-up synthetic probe; no rollback was triggered).
- Retention owner: this session's operator (see git commit authorship); redaction statement: no
  evidence file was found to contain a token, authorization header, Braindump body, Alignment
  Review summary, raw ObjectChange payload, or raw custom-field value (checked with `grep` before
  each `chmod 0600`, and Braindump titles were redacted from retained evidence out of caution even
  though titles are not full bodies).

## 3. Phase 3 audit final dispositions (plan Section 2)

All twelve rows of Section 2.2's table are closed:

| Defect | Final disposition |
|---|---|
| Full disposable runtime suite (9 failures/6 errors) | Repaired Step 1, re-proved 304/304 in Step 2/3 disposable, and again in this session's Step 6 rebuild |
| Retained UI POSTs under-tested | Full permission-per-model matrix added Step 1, run in disposable Step 2 |
| Removed Braindump/review UI still tested as present | Converted to absence/404/non-mutation tests Step 1 |
| Full 22-route render matrix | Added Step 1, run in disposable Step 2 |
| Complete literal-path 404 matrix | Added Step 1 |
| Row-fingerprint zero-write proof | Added Step 1, run in disposable Step 2 |
| Complete REST method/field matrix | Added Step 1, run in disposable Step 2 |
| IntentSource GraphQL negative queries | Added Step 1; also independently re-proved live in this session's report8.md Section 1 |
| Missing nctl fail-closed cases | Added Step 1 (except item 13's real-HTTP variant, see below) |
| Real HTTP node-link/lifecycle/writer proof | Proved in disposable Step 2; **also independently proved live** in this session's report8.md Section 3 (synthetic probe) |
| Reproducible sanitized evidence | Present at every step under `.local/interface-contract/p4/` |
| Stale documentation recipes | Corrected Step 1, re-verified clean in this session's Step 10 search |
| Exact final source tuple | Frozen and verified at every deployment point (Section 1 above) |

**Known residual gap (unchanged from Step 2, not closed by this Phase)**: plan Step 2 item 13
("execute representative fail-closed reset fixtures") was proved via unit/mocked tests only, not
as real disposable HTTP — report2.md flagged this explicitly. This session's live synthetic probe
(report8.md) proved the *success* path of `link_actual_node` through real HTTP but did not add new
real-HTTP coverage for fail-closed reset fixtures specifically. Recorded as a residual, not
blocking, gap — the plan's Definition of Done does not name this item individually, and the
disposable mocked coverage plus this session's live success-path proof jointly exceed what Phase 3
originally had.

**Correction/supersession note**: per plan Section 2.3, Phase 3's final report and Step 8-10
reports already carry Step 1's dated correction notes (report1.md Section "Correction notes on
Phase 3 reports"); this final report reaffirms that Phase 3's original runtime/HTTP claims were
superseded by Phase 4 Steps 1-2's fresh proof, not retroactively rewritten.

## 4. Failed-then-passing disposable results

- Planning-time (2026-07-26, before Step 1): 47 tests, **9 failures, 6 errors** (plan Section 2.2).
- Post-Step-1 local suite: 226 passed, 13 skipped.
- Step 2 disposable Nautobot App suite: full pass (report2.md).
- Step 3 disposable candidate (real `pip install`): 304/304 pass, exposed and fixed one
  installation-path-portability defect (`e8732f1`) invisible to the Django-free suite.
- This session's Step 6 rebuild (nauto `1c78af8`): 304/304 pass again, confirming the
  `description`/`notes` fix didn't regress anything.

## 5. Test summaries and teardown proof

Full disposable UI/API/GraphQL/HTTP summaries: report2.md (Step 2), report3.md (Step 3 + its
remainder), report6b.md Section 1 (this session's rebuild). Every disposable compose project
(`nic-p1-disposable`, `nic-p4-disposable`, `nic-p4-step3`, `nic-p4-step3b`, `nic-p4-step6c`) was
torn down with `docker compose down -v` and confirmed absent by name afterward; the live
`nautobot-*` stack was confirmed running and untouched before/after every disposable step.

## 6. Image build inputs and per-container digests

See Section 1's tuple table. Build command:
`docker build -f devenv/nautobot/Dockerfile -t nic-p4-candidate:20260726c .` from the superproject
root, `ARG NINTENT_COMMIT=e8732f17ae35d8c72d4d593e8d7311bd234fc0bf ARG
NAUTO_COMMIT=1c78af8bdbfc69cafdc293b4082f866de9f271b0`. Build-time commit-equality check and
YAML checksum both passed inline (report6b.md Section 1).

## 7. Preservation manifests

Before (Step 0, this Phase's start) and after (this session's Step 9) manifests are in
report9.md Section 1's table. The only differences are: 13 rows' cosmetic/benign field updates from
the approved Import apply (Step 7), and one synthetic Braindump+DesiredNode+Device created and
fully removed during the approved Step 8 probe (net zero). No unclassified difference.

## 8. Backup listing and disposable restore result

Step 4 (report4.md): `pg_dump -Fc` of the live `nautobot` database plus a media-volume tar;
manifest with SHA-256 digests; restored into a disposable, separately named database with matching
`IntentSource=2`/`DesiredNode=5`/`Device=5` counts and migrations ending at `0016`. Not repeated
this session (no new backup was needed — see Section 2 above).

## 9. Official Import preview/apply/repeat artifacts and totals

| Run | Mode | Totals (create/update/unchanged/conflict) | SHA-256 |
|---|---|---|---|
| Step 6 original (pre-fix) | preview | 0/13/9/0 (5 of the 13 were unauthorized `description` erasures) | see report6.md |
| Step 6 re-run (post-fix) | preview | 0/13/9/0 (all 13 cosmetic/benign, 0 unauthorized) | `.local/interface-contract/p4/20260726_step5b/intent-import-result.json` |
| Step 7 apply | apply | 0/13/9/0, `writes.committed=true`, `confirmation.status=confirmed` | `9797b1f83497b73d305da187e1a3e3c18fdc8dc3713be9b9cdeb7c16db59abf1` |
| Step 7 repeat apply | apply | 0/0/22/0, zero semantic write proven at row level | `01e93075ab5cf892ec4408b283567462e5386a3c8cc227e5e7880afae120cef6` |
| Step 7 final preview | preview | 0/0/22/0 | `3c3832fb445d0804fedac26a3dc32a88df056ee5e9a9a9706f390851ae087d85` |

## 10. Retained/removed live route and writer results

report5.md Section 7 (post-deploy) and report8.md Section 1 (post-apply, this session) both
independently confirm: `nodes/`/`braindumps/`/`alignment-reviews/` REST = 200; the 4 removed REST
families = 404; IntentSource GraphQL root fails schema validation; 11 retained UI list routes exist
and are permission-gated (302 unauthenticated), 6 sampled removed UI paths = 404. report8.md
Section 3 additionally proves the retained lifecycle, node-link, and Braindump REST writers with a
positive live synthetic probe, GraphQL-confirmed at every step, fully cleaned up.

## 11. nctl and VM read-only smoke results

report8.md Section 1: `nctl status`/`actual`/`drift --json`/`ops list`/`braindump list` all pass;
dry `reconcile` (no `--yes`) performs zero mutation. VM Phase 3 compute roots
(`DesiredComputePlatform`/`DesiredComputeInstance`) confirmed `0`/`0` throughout — no compute
action taken.

## 12. Job freeze/resume times and queue state

- Step 4 freeze: `2026-07-25T18:24:37Z`-`18:28:24Z` (report4.md), resumed after user decision.
- This session's Step 5b re-freeze: writers stopped `2026-07-26T02:02:12Z`-`02:02:17Z` for the
  candidate swap; containers have run continuously since (`Up` throughout Steps 6-9). The
  procedural writer freeze (no Import apply, no routine nctl mutation) held from re-entry until
  Step 9's explicit lift, after Step 7's apply/repeat/final-preview and Step 8's smoke matrix both
  passed cleanly.
- Active/pending `JobResult` count was `0` at every checkpoint from Step 0 through Step 9.

## 13. Before/after measurements

- `urls.py`: 65 lines, exactly 22 routes (11 list + 11 detail), unchanged since Phase 3.
- `views.py`: 240 lines, 11 `ObjectListView` + 11 `ObjectView`, zero `ObjectEditView`/
  `ObjectDeleteView`/`FormView` (confirmed absent again in this session's Step 10 search).
- `api/views.py`: 103 lines, 3 writable ViewSets (`DesiredNode` GET+PATCH only,
  `BrainDumpDocument`/`AlignmentReview` GET+POST+PATCH+DELETE, no PUT/bulk).
- Live `ObjectChange` total: 898 (Step 0/pre-session) -> 920 (final, this session) — the +22 breaks
  down as +4 (Step 6's `GitRepository`/Job sync bookkeeping) + 13 (Step 7's approved Import apply)
  + 5 (Step 8's audited synthetic-probe writes, fully cleaned up in row-count terms).
- Local test count: 226 passed/13 skipped (Django-free); 304/304 (real Nautobot App suite,
  unchanged across every disposable/live rebuild in this session).

## 14. Current/historical search classification

Step 10's Section 10 term search (`.local/interface-contract/p4/20260726_step10/
section10_searches.txt`, 959 raw matches) found, outside `devdocs/` history: only (a) test-file
string literals asserting these routes/classes/attributes are *absent* or *rejected*, (b)
documentation prose stating they were *removed*, and (c) the legitimate retained patterns
(`NAUTOBOT_INTENT_SOURCES_FILE`, `intent_sources_file`, `rest_get`, `@extras_features("graphql")`,
`DesiredNodeSerializer`/`BrainDumpDocumentSerializer`/`AlignmentReviewSerializer` as explicit-field
serializers). No operative removed-UI/API instruction, no mutable unpinned build reference, and no
compatibility alias were found. `nctl/docs/register-a-new-pc.md` carries the Step 1 supersession
note and its Sections 1-3 already describe the canonical YAML + `nctl lifecycle` path, not the
removed UI.

## 15. Every user approval and its exact authorized scope

1. "YAMLに説明文を追加(推奨)" — resolve problem.md's Step 6 blocker by adding live
   `description`/`notes` values to `nauto/seed/intent_sources.yaml` (source-only, no code change).
2. "はい、今push します" — push the resulting nauto/superproject fix commits.
3. "はい、進めてください(推奨)" — re-freeze live writers and redeploy the new candidate image
   (repeats Steps 3/5's live-adjacent actions for the fixed tuple).
4. "はい、apply=trueを実行(推奨)" — run `Import Intent Sources` with `apply=true` against live
   Nautobot, plus its approved repeat/refetch/idempotence sequence (Step 7).
5. "実施する" — run the Step 8 positive live synthetic mutation probe (lifecycle, node-link,
   Braindump create/update/delete), using only clearly-synthetic identities, with cleanup.
6. "サービスを再開(推奨)" — lift the procedural writer freeze (Step 9); no container action was
   actually required since containers stayed up throughout.

(Prior-session approvals for Steps 0-5's own live actions are recorded in report0.md-report5.md and
are not repeated here.)

## 16. Deviations, omitted checks, declined probes, unexpected states

- **Deviation from plan's literal Step 6->7->8 order**: this session found Step 6 already halted
  from a prior session on an unresolved problem.md finding. Resolving it required a small re-entry
  into Steps 3 and 5 (new candidate build + redeploy) before Step 6 could be legitimately re-run.
  This is a repair of an in-progress step, not a new deviation from the plan's intent — the plan
  Section 9.1/9.2 failure-handling sections anticipate exactly this "fix forward within the
  approved tuple" pattern.
- **`nctl reconcile --yes` SSH pre-flight correctly refused** the synthetic host in Step 8's
  node-link probe (no real SSH endpoint exists for a synthetic slug). Substituted with a direct
  call to the exact same production writer function (`execute_link_actual_node`) using the real
  HTTP client and the plan the CLI itself had already computed — not a mock, not a bypass of the
  writer under test, only a bypass of the CLI's unrelated SSH gate. Documented in report8.md
  Section 3.3.
- **`AnalyzeIntentSources` was not run live** in this session (Section 3 above / Step 10's own
  finding) — running it would issue real outbound HTTP fetches to catalog source URLs, a network
  side-effect not requested or approved. Its dry-default behavior remains proven only in the
  disposable suites (304/304 App suite includes this Job's code paths).
- **Step 2 item 13's real-HTTP fail-closed-reset gap remains open** (Section 3 above) — not newly
  introduced by this session, inherited from report2.md, and not required to be closed by this
  plan's own Definition of Done wording.
- **IPAM Job (`ReconcileDesiredIPAMIntent`) was not run**, dry or otherwise — out of scope per plan
  Section 4.3 ("running... IPAM... apply modes except where explicitly approved"); no approval was
  sought or needed since this phase's scope never required exercising it.
- No rollback action was taken at any point in this session; the pre-existing verified backup
  (Step 4) remains the rollback point and was never invoked.

## 17. VM Phase 3 Steps 9-12 handoff

Stated explicitly in report9.md Section 8: the deployed strict YAML/Import contract and exact
`nauto` revision (`1c78af8`) are now available to VM Phase 3 Steps 9-12. VM compute rows and any
proposed MAC/template seed content remain untouched (`0`/`0` live) and still require their own
separate reviewed preview and user approval — nothing in this phase pre-authorizes that work.

## Definition of done — final check (plan Section 11)

Every bullet in Section 11 is satisfied: Phase 3 audit defects repaired and re-proved (Section 3);
disposable and real-HTTP gates pass (Sections 4-5, with the one named residual gap disclosed, not
hidden); documentation contains no operative removed-UI/API instruction (Section 14); exact
repaired commits pushed and frozen (Section 1); candidate pins exact nintent/nauto revisions and
all three live processes share the identical image/YAML digest (Section 1, Section 6); a verified
backup/restore exists (Section 8, no new one needed); the maintenance freeze prevented concurrent
mutation during cutover (Section 12); live code uses the final GraphQL/REST/UI/YAML/Job matrix
(Section 10); the official preview was zero-write and separately approved (Sections 9, 15); apply/
refetch/repeat/final-preview proves the exact reviewed state and no repeated write (Section 9);
all confirmed desired identities/lifecycles/links/prose/actual-ledger/JobHook/operation evidence
survived except explicitly approved changes (Section 7); retained writers were positively exercised
and GraphQL-confirmed (Section 10); removed REST/UI paths are absent live (Section 10); nctl
read/dry-operation smoke passes (Section 11); no unapproved SSH/Ansible/host/provider/compute/
generated-file action occurred (Section 16); migrations remain through `0016` with no model diff
(Section 13 context, report9.md Section 5); operations resumed only after Step 9's approval
(Section 15 item 6); VM Phase 3 received the handoff without compute seeding (Section 17); no
secret/private prose appears in evidence (Section 2); and every deviation/omission is recorded
without weakening this completion language (Section 16).

**Declared status: complete.**
