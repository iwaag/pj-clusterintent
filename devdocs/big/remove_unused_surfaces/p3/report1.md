# Phase 3 Step 1 — Freeze focused removal and retained-path tests

Parent: [plan.md](plan.md) Step 1.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`), containing
`step1-new-tests-pre-change.log`, `step1-braindump-regression.log`.

## 1. New test module

`nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` (nintent commit
`339b7464ec018bf9cc71ef5f41b185d21e308950`), guarded by the same `try/except ImportError` pattern
as `test_braindump.py`. 29 tests across 10 classes, one test name per plan §5.4 item:

`ModelFieldRemovalTests` (4), `FilterMetadataTests` (2), `TableColumnTests` (3),
`NodeServiceUITests` (4), `DashboardRedirectRemovalTests` (2), `NavigationTests` (2),
`AppConfigTests` (1), `RestApiTests` (5, including item 14's create/update proof),
`GraphQLTests` (4), `RetainedRoutesTests` (2).

## 2. Local discovery stays clean

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: **187 passed** (unchanged — the
new module's Nautobot/DRF imports raise `ImportError` outside a Nautobot environment and are
caught by the module-level guard, so zero new tests run locally, but import/discovery itself
raised no error).

## 3. Pre-change Nautobot-runtime run (scratch container override, not local source-mount)

Per plan §6.2 (nintent is installed via `pip install git+...`, not a volume mount): backed up the
container's installed `nautobot_intent_catalog` package to `.orig-backup`, then `docker cp`'d the
Step-0/Step-1 local source (fields/UI/links still present — no deletion yet) over it, `chown`ed to
`nautobot:nautobot`. Ran with `NAUTOBOT_ALLOWED_HOSTS` extended to include
`nautobot.example.com`/`testserver` (Nautobot's test client's `HTTP_HOST`, per the same environment
note as braindump Phase 1 step 1.7) and `--keepdb` so `nautobot-server test` provisions its own
disposable `test_nautobot` database (the `nautobot` Postgres role already has `CREATEDB` from that
prior phase). The live `nautobot` database was never touched.

Two bugs in the new test module were found and fixed before this run was accepted:

- `RestApiTests` only granted `view_*` permissions, so `test_node_create_and_update_still_work`
  (a retained-path test, not a removal assertion) failed with 403 and both OPTIONS-metadata tests
  errored with `KeyError: 'actions'` (DRF omits the `actions` key when the user has no add
  permission). Fixed by adding `add_desirednode`/`change_desirednode`/`add_desiredservice` to the
  fixture's `add_permissions()` call.

## 4. Result: `nautobot-server test nautobot_intent_catalog.tests.test_remove_unused_surfaces --keepdb`

**29 tests, 24 failures, 0 errors, 5 passed.** The 24 failures are exactly the removal assertions
(fields/constants/filters/table columns/badge helpers/UI text/dashboard route/navigation
item/App default/REST field omission/REST OPTIONS omission/GraphQL old-field rejection) — every
one fails for the expected pre-change reason (the field/link/route/setting is still present). The
5 passes are exactly the retained-path proofs that don't depend on removal: node create/update,
both supported GraphQL reads, and both retained-route/navigation-group checks.

| Failing test | Pre-change reason |
|---|---|
| `test_desired_node_has_no_reconciliation_fields` / `..._service_...` | fields still on both models |
| `test_desired_node_has_no_reconciliation_constants` / `..._service_...` | constants still on both models |
| `test_desired_node_filterset_has_no_reconciliation_status` / `..._service_...` | still in `Meta.fields`/`base_filters` |
| `test_desired_node_table_has_no_reconciliation_column` / `..._service_...` | still in table columns/fields/default_columns |
| `test_no_reconciliation_badge_helpers_remain` | `RECONCILIATION_BADGE_CLASSES`/`_render_reconciliation_status` still present |
| `test_node_{list,detail}_page_renders...` / `test_service_{list,detail}_page_renders...` | "Reconciliation"/"view dashboard" text still rendered |
| `test_dashboard_redirect_route_name_is_not_reversible` | route still reverses |
| `test_direct_dashboard_path_returns_404` | `/dashboard/` still 302s (not 404) |
| `test_operational_tools_group_has_quick_host_add_and_no_dashboard_item` | `nctl Dashboard` still in the group |
| `test_navigation_module_has_no_dashboard_url_helper` | `_configured_dashboard_url` still defined |
| `test_default_settings_has_no_dashboard_url` | `default_settings == {"dashboard_url": None}` |
| `test_node_list_and_detail_omit_removed_fields` / `..._service_...` | both fields still in REST representation |
| `test_node_options_metadata_omits_removed_fields` / `..._service_...` | both fields still in OPTIONS `actions.POST` |
| `test_explicit_reconciliation_status_field_fails_node_validation` / `..._checked_at_...service` | old-field GraphQL query still succeeds (no error) |

## 5. Retained-path regression: `test_braindump`

`nautobot-server test nautobot_intent_catalog.tests.test_braindump --keepdb`: **33/33 passed**,
unchanged from the braindump Phase 1 baseline — confirms the new test module's fixtures/imports
introduced no collateral breakage.

## 6. Environment state

Container override remains in place (`nautobot_intent_catalog.orig-backup` backup present) for use
by Steps 2/5/6, which also require Nautobot-runtime access; full restoration is Step 7 per the
plan's own step boundary. Live migration state reconfirmed unchanged at `0014` throughout (no
migration command was run this step).

## Gate

Every intentional failure maps 1:1 to Step 2/3 residue with no unexplained failure; all
retained-path tests (create/update, GraphQL, routes/navigation groups, and the full `test_braindump`
module) are green before deletion begins. Step 1 gate met.
