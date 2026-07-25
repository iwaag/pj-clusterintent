# Phase 3 Final Report — Remove the nintent Cache and Dashboard Links

Parent: [plan.md](plan.md) (all steps). Reports on root revision `27cd2d9f461a45c862caaa37ab8bd5495b9501d9`.

Status: **implemented, awaiting push** (local nintent implementation, disposable-database proof,
and matched-revision preparation complete per plan §1/§3.3; the nintent commit is not yet pushed,
so per plan §7 Step 8 this cannot be reported `complete`). The live migration and coordinated
deployment remain Phase 5 work, unchanged from the plan's own scope boundary.

## 1. Execution timestamp and evidence

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`), containing
`revisions.txt`, `live-baseline.txt`, `local-baseline.txt`, `step0-baseline-deletion-search.txt`,
`step1-new-tests-pre-change.log`, `step1-braindump-regression.log`,
`step2-removal-tests-post-change.log`, `step2-braindump-regression.log`,
`step2-full-app-suite.log`, `step5-nodes-before.txt`, `step5-nodes-after.txt`,
`step5-services-before.txt`, `step5-services-after.txt`, `step6-removal-tests-final.log`,
`step6-full-app-suite.log`, `step7-final-deletion-search.txt`, `step7-final-measurements.txt`,
`step7-restoration.txt`.

## 2. Starting and ending revisions

| Repository | Starting (Step 0) | Ending (Step 8) | Dirty state |
|---|---|---|---|
| superproject | `f30db90d5e26dd2d2ede7174be2affacfaf53f41` | `27cd2d9f461a45c862caaa37ab8bd5495b9501d9` | clean except the pre-existing user edit to `p3/plan.md` (untouched by this implementation) |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean, **unchanged** |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | clean |

`nctl` has zero commits from this phase, matching plan §3.3 — it was already CLI-only/dashboard-
free/no-PATCH from Phase 2 and needed no further change.

## 3. Live installed nintent commit and migration state, before and after

Unchanged throughout: `nautobot-intent-catalog` `0.9.0`, Git commit
`ad9d36397d23c269ad748e13acbccc532fa29f52`, migrations applied through `0014_braindump_exchange_diary`.
`0015`/`0016` remain unapplied on the live (default-alias `nautobot`) database — reconfirmed at
Step 0, Step 2, Step 5, and Step 7.

## 4. Aggregate pre-removal cache counts (Step 0, read-only)

| Model | Total | Nonblank `reconciliation_status` | Nonblank `reconciliation_checked_at` |
|---|---|---|---|
| DesiredNode | 5 | 5 (`converged`) | 5 |
| DesiredService | 6 | 1 (`converged`) | 1 |

Matches the plan §2.2 baseline exactly; unchanged from Phase 0.

## 5. Exact added/edited/unchanged file inventory

**Added (2):** `nintent/nautobot_intent_catalog/migrations/0016_remove_reconciliation_dashboard_surfaces.py`;
`nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` (32 tests across 12 classes
in one file — plan §5.1 permits a split "for a concrete reason"; no split was needed).

**Edited (10, nintent):** `models.py`, `api/serializers.py`, `filters.py`, `tables.py`,
`templates/nautobot_intent_catalog/desirednode.html`,
`templates/nautobot_intent_catalog/desiredservice.html`, `views.py`, `urls.py`, `navigation.py`,
`__init__.py`. Exact match to plan §5.2.

**Edited (1, root):** `devenv/nautobot/nautobot_config.py` (plan §5.3) — found missing by this
agent's Step 3 execution and fixed in Step 7 once the Step 7 deletion search caught the gap; see
§13 below for this deviation's full record.

**Unchanged (plan §5.5 exceptions, reconfirmed):** `migrations/0009_reconciliation_status.py`,
`migrations/0010_operational_overrides_and_provenance.py`,
`migrations/0015_compute_platform_instance_and_endpoint_mac.py` (all three byte-identical to their
prior committed content, `diff`-confirmed in Step 2), `forms.py`, `api/views.py`, `api/urls.py`,
compute model/form/filter/table/view/serializer/template behavior, Braindump/Alignment Review
implementation, `nctl` source/tests, root/nintent READMEs, and all historical plans/reports.

## 6. Exact `0016` dependency and operations

Depends directly on `("nautobot_intent_catalog", "0015_compute_platform_instance_and_endpoint_mac")`.
Exactly four `migrations.RemoveField` operations
(`DesiredNode.reconciliation_checked_at`, `DesiredNode.reconciliation_status`,
`DesiredService.reconciliation_checked_at`, `DesiredService.reconciliation_status`). No
`RunPython`, data copy, replacement model, rename, default, or compatibility branch.

## 7. Disposable-database setup and forward-migration results

`pg_dump`/`pg_restore` clone of the live `nautobot` database into
`nautobot_p3_step5_scratch` (Step 5), still at `0014` at restore time, carrying the same real
nonblank cache rows recorded in §4. `0015` then `0016` both applied cleanly. All four columns
physically absent after `0016` (`\d` on both tables); ORM `_meta.get_fields()` confirms field
absence; `makemigrations --check --dry-run` reports `No changes detected`.

## 8. Proof that nonblank cache data was exercised and discarded

The clone carried 5 `converged` DesiredNode rows and 1 `converged` DesiredService row into the
scratch database (confirmed present via `\d`+`SELECT ... GROUP BY` immediately before `0016` ran);
the columns holding those values no longer exist immediately after. This is a genuine
data-discarding proof, not a migration run against an empty database (plan §6.3's explicit
requirement).

## 9. Before/after column, row-count, and selected non-cache comparisons

| Check | Before `0016` | After `0016` |
|---|---|---|
| `reconciliation_status`/`reconciliation_checked_at` columns (both tables) | present | **absent** |
| DesiredNode row count | 5 | 5 (unchanged) |
| DesiredService row count | 6 | 6 (unchanged) |
| DesiredNode id/name/slug/lifecycle (all 5 rows) | recorded | byte-identical (`diff`-confirmed) |
| DesiredService id/name/slug/service_type (all 6 rows) | recorded | byte-identical (`diff`-confirmed) |
| `desiredcomputeplatform`/`desiredcomputeinstance` tables (`0015`) | n/a (added by `0015` in this same run) | present |
| `desiredendpoint.mac_address` + `nic_unique_desired_mac_address` constraint | n/a | present |

## 10. UI/URL/navigation/config results

- Node/service list and detail pages render real test rows and contain no "Reconciliation"/"view
  dashboard" text (`NodeServiceUITests`).
- `plugins:nautobot_intent_catalog:dashboard_redirect` fails to reverse; the direct
  `/plugins/intent-catalog/dashboard/` path returns 404, not a redirect
  (`DashboardRedirectRemovalTests`).
- Navigation's Operational Tools group retains only `Quick Host Add`; `nctl Dashboard` is absent;
  Braindump/Desired State groups are intact (`NavigationTests`, `RetainedRoutesTests`).
- `IntentCatalogConfig.default_settings` is `{}` (`AppConfigTests`).
- `devenv/nautobot/nautobot_config.py`'s `PLUGINS_CONFIG` is `{}`; `PLUGINS =
  ["nautobot_intent_catalog"]` (plugin enablement) is untouched.

## 11. REST/GraphQL results

- Real DesiredNode/DesiredService/DesiredComputePlatform REST list and detail reads return actual
  rows and omit both removed fields from the representation and from `OPTIONS`
  `actions.POST` metadata (`RestApiTests`, `ComputeAPIRegistrationTests`).
- Supported GraphQL queries (`desired_nodes`, `desired_services`, `desired_compute_platforms`)
  return non-empty real rows with no `errors` key. Explicit old-field queries
  (`reconciliation_status`/`reconciliation_checked_at`) return a GraphQL validation error
  (`GraphQLTests`).
- Node create + PATCH-update through the REST API both still succeed (`RestApiTests`).

## 12. Braindump/Alignment Review regression results

`nautobot_intent_catalog.tests.test_braindump`: **33/33 passed** every time it was run this phase
(Steps 1, 2, 3, 6) — zero change to Braindump/Alignment Review model, UI, REST, GraphQL, or
authorship behavior.

## 13. Every omitted, substituted, failed, or optional check

- **Deviation A (Step 2/Step 3 combined execution)**: identical in kind to `p2/report8.md`'s
  recorded Step 2/Step 3 deviation — Django cannot import `filters.py`/`views.py` once
  `models.py`'s fields are removed, so `makemigrations` could not even run until Step 3's edits
  also landed. Both steps' edits are separately committed and separately reported
  (`report2.md`/`report3.md`), but neither step's runtime gate could be exercised in isolation.
- **Deviation B (missed §5.3 item, found and fixed)**: this agent's own Step 3 execution missed
  plan §5.3 (`devenv/nautobot/nautobot_config.py`'s `dashboard_url`); Step 7's deletion search
  caught it and it was fixed and committed within Step 7, before this final report. No unexplained
  match remained in the final Step 7 search.
- No optional reverse-schema check was run in Step 5 (plan §6.3 marks it optional); the forward
  proof was sufficient and no rollback claim was made from it.
- No check was substituted or skipped. No live Nautobot/database/Job/desired-state/Ansible/
  dashboard-output mutation was attempted or performed at any step.
- **Push not yet performed** — the sole reason this report is not `complete` (see §14).

## 14. Matched and rollback tuples, and push availability

```text
matched (this phase, ready for Phase 5):
  nintent: 0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e   (NOT YET PUSHED)
  nctl:    7a0f2cf035179fbea5deed4cacb05573f8c8dffa   (Phase 2 final, unchanged)

deployed / rollback (current live state):
  nintent: ad9d36397d23c269ad748e13acbccc532fa29f52   (0.9.0, migrations through 0014)
  nctl:    7a0f2cf035179fbea5deed4cacb05573f8c8dffa   (same revision — no rollback of nctl needed)
```

**The user has not yet pushed the nintent commit.** This agent did not and will not push it
(`.local/localenv_memo.md`; confirmed identical practice in `p1/report8.md`/`p2/report8.md`).
Once pushed, a read-only check of `https://github.com/iwaag/nprojects.git` for commit
`0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` is the only remaining action to upgrade this report's
status from `implemented, awaiting push` to `complete` — no rebuild is required to make that
determination.

## 15. Explicit confirmation of no live mutation

No live rebuild, restart, migration (`0015`/`0016` were only ever applied to disposable clones),
Job trigger, desired-state write, `nctl reconcile --yes`, Ansible run, or host actuation occurred
at any step. Reconfirmed via live migration-state re-checks at Steps 0, 2, 5, and 7, and via the
explicit non-mutation statements recorded in each step's own report.

## 16. Exit-criteria table (plan §9)

| Exit criterion | Status | Evidence |
|---|---|---|
| Phase 2's nctl dashboard-free/no-PATCH handoff still intact | ✅ | report0.md §2 |
| Both models have no reconciliation constants/choices/fields | ✅ | report2.md §1; report5.md §4 (ORM check) |
| `0016` depends directly on `0015` | ✅ | report2.md §2 |
| `0016` is exactly 4 field removals, no replacement/translation | ✅ | report2.md §2 |
| `0009`/`0010`/`0015` unchanged | ✅ | report2.md §2 (byte-diff) |
| Disposable database reaches `0016` through `0015` | ✅ | report5.md |
| Forward proof starts with representative nonblank cache values | ✅ | report5.md §2 |
| All four physical columns absent after migration | ✅ | report5.md §4 |
| Node/service row identity, counts, non-cache data preserved | ✅ | report5.md §4 |
| Compute tables/relations and endpoint MAC (`0015`) remain | ✅ | report5.md §4; report6.md |
| `makemigrations --check --dry-run` reports no changes | ✅ | report2.md §3; report5.md §4 |
| FilterSet metadata has no reconciliation-status filter | ✅ | report3.md §1; test module |
| Node/service tables have no status column/badge/render helper | ✅ | report3.md §1; test module |
| Node/service detail templates have no cache rows/dashboard link | ✅ | report3.md §1; test module |
| Dashboard context/resolver/redirect/URL/nav item absent | ✅ | report3.md §1; test module |
| App defaults and dev config have no `dashboard_url` | ✅ | report3.md §1; report7.md §1 |
| Normal node/service list/detail UI pages render real rows | ✅ | report6.md §4 |
| Normal REST responses/metadata omit fields, retain surviving data | ✅ | report6.md §4 |
| Normal non-empty node/service GraphQL reads work | ✅ | report6.md §4 |
| Explicit GraphQL requests for removed fields fail as unknown | ✅ | report6.md §1 |
| Braindump/Alignment Review boundaries pass | ✅ | report6.md §2 (33/33 across all reruns) |
| Compute UI/API/GraphQL registration remains available | ✅ | report6.md §1 (positive content proof, not just URL reverse) |
| Local and required Nautobot-runtime tests pass | ✅ | 187/187 local; 252/252 full app suite (report6.md §3) |
| Deletion searches have no unexplained active matches | ✅ | report7.md §3 |
| Scratch DB/dump and container package override removed/restored | ✅ | report5.md §5; report7.md §2 |
| Live nintent remains on its original commit through `0014` | ✅ | report0.md, report7.md §2 |
| Exact matched nintent/nctl and rollback tuples recorded | ✅ | report8.md; §14 above |
| User, not the agent, pushed the nintent commit, remote verified | ⏳ | **pending** — user push requested this turn |
| No live rebuild/migration/Job/desired write/nctl apply/Ansible/host mutation | ✅ | §15 above |
| Final report records deviations/omissions/warnings/exceptions/status | ✅ | §13 above; this document |

27 of 28 plan §9 exit criteria are met. The remaining criterion — verified remote push — is the
one item this agent cannot perform. **Phase 3 status: implemented, awaiting push.**
