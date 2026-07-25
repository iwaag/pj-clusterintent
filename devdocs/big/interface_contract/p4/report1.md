# Phase 4 Step 1 Report — Repair Phase 3 tests and active documentation

Plan: [plan.md](plan.md), Step 1.

Status: complete. Source/test/documentation work only, as authorized without a live-maintenance
approval by Section 3.4. No live mutation, no Job run, no service stop/restart, no database/media
action, no push (pushing repaired commits is Step 3/the user's, per Section 3.4).

## 1. Obsolete Braindump/Alignment Review UI mutation tests converted (plan item 1)

`nintent/nautobot_intent_catalog/tests/test_braindump.py::BrainDumpViewTests` previously reversed
and exercised the deleted `braindumpdocument_add/edit/delete` and `alignmentreview_add/edit/delete`
routes (`test_add_view_initial_authorship_is_user_direct`,
`test_add_edit_delete_round_trip_and_agent_transcribed_selectable`,
`test_review_add_binds_parent_and_returns_to_braindump`,
`test_review_add_with_existing_review_redirects_to_edit_without_creating_a_second_row`,
`test_review_edit_updates_summary_and_returns_to_braindump`,
`test_review_delete_leaves_braindump_unreviewed_and_returns_to_it`). All six were removed and
replaced with:

- `test_removed_braindump_and_review_routes_do_not_reverse` — all six removed route names raise
  `NoReverseMatch`.
- `test_former_literal_mutation_paths_return_404` — the six former literal add/edit/delete/review
  paths all return `404` for both GET and POST.
- `test_post_to_list_and_detail_pages_does_not_mutate` — POST to the retained list/detail pages
  changes neither row count nor field values.
- `test_detail_view_has_no_mutation_control` — the detail page contains no
  `type="submit"`/`csrf_token`/Add/Edit/Delete affordance.
- `test_detail_view_shows_reviewed_panel_content` — new case covering the previously-untested
  reviewed-panel branch (only the unreviewed branch had a case before).

`test_list_view_shows_braindump`, `test_detail_view_shows_unreviewed_and_both_panels`, and
`test_detail_view_escapes_script_and_html_looking_content` (panel separation/escaping) are
unchanged. `BrainDumpAPITests` (REST CRUD) and `BrainDumpGraphQLTests` are unchanged, per the
plan's "keep REST CRUD tests" instruction.

## 2. Reusable fixture factories for all eleven retained UI models (plan item 2)

New file `nintent/nautobot_intent_catalog/tests/factories.py`: one `make_<model>()` function per
retained model (`IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`,
`DesiredEndpoint`, `DesiredComputePlatform`, `DesiredComputeInstance`, `DesiredServicePlacement`,
`DesiredNodeOperationalOverride`, `BrainDumpDocument`/`AlignmentReview`, `DesiredIPRange`), each
building the minimal row that satisfies that model's own `clean()`/database constraints (verified
by calling `full_clean()` before `save()` in every factory except the two whose `.objects.create()`
callers already exist unchanged). Compute-platform/instance/override fixtures default to
`lifecycle="planned"` so they stay non-actionable and do not also require a fully wired primary
endpoint/realized-cluster/realized-VM chain merely to pass validation — reviewed/unreviewed
Braindump and realized-link relationships are the callers' responsibility via factory
`**overrides`, per the plan's "reviewed and unreviewed Braindumps plus safe realized-link
relationships" requirement.

## 3-5. Full UI runtime matrix (plan items 3-5)

`test_ui_contract.py` gained, driven by one `RUNTIME_MODEL_MATRIX` covering all eleven models:

- `UIRuntimeRenderTests.test_every_retained_list_and_detail_renders` — every list (htmx) and
  detail page actually renders (`200`) and contains the fixture's distinctive field and PK; the
  prior suite only reversed route *names*, it never rendered all eleven fixture/render pairs.
- `UINonMutationRuntimeTests` — extended from the prior two-model-only `view_desirednode`/
  `view_desiredservice` grant to the exact `view_*` permission for **every** retained model, and
  now asserts a full before/after field-dictionary comparison per model (not just HTTP status) for
  both list and detail POSTs (`test_post_to_retained_detail_pages_does_not_mutate_the_row` is new;
  the prior suite never POSTed to a detail page at all).
- `UIMissingPermissionRuntimeTests` (new) — a user with zero nintent permissions is denied (`403`
  or a login redirect) on every retained list/detail page, closing the "missing-permission result"
  gap the plan named.
- `UIContractManifestTests.test_removed_literal_paths_404_for_every_family` (new) — literal
  `.../add/`, `.../<pk>/edit/`, `.../<pk>/delete/` paths 404 for all eleven model URL prefixes
  (`sources`, `services`, `dependencies`, `nodes`, `endpoints`, `compute-platforms`,
  `compute-instances`, `placements`, `operational-overrides`, `braindumps`, `ip-ranges`), plus
  `test_removed_utility_paths_404` for the former Quick Host Add / Source YAML aliases. The prior
  suite only asserted route-name reversal failure, never that the literal former URL 404s.
- `UIContractManifestTests.test_navigation_only_links_the_eleven_retained_lists` (new) — the
  navigation menu links exactly the eleven retained list routes and nothing else.
- `REMOVED_UI_ROUTE_NAMES` count is now asserted (`== 38`) so a future accidental trim is caught.

## 6-7. REST/GraphQL matrix (plan items 6-7)

`test_api_contract.py` gained two classes:

- `RESTMethodFieldMatrixTests` — exact response-field-set assertion for `DesiredNode`; allowed-field
  PATCH success; unknown-field, invalid-choice, and inconsistent-link-source PATCH rejection, each
  paired with a zero-write refetch assertion; full PUT/bulk-PATCH/bulk-DELETE `405` matrix for all
  three retained ViewSets; and unknown-field PATCH rejection (with zero-write) for
  `BrainDumpDocument`/`AlignmentReview`, which the prior suite never exercised (only valid-input
  CRUD was tested in `test_braindump.py`).
- `GraphQLContractTests` — executes the actual `intent_source`/`intent_sources` singular/plural
  GraphQL queries and asserts they fail schema validation (the prior suite only checked registry
  membership, never ran a query), and executes one joined query across all eleven retained
  GraphQL roots to prove they still resolve together.

## 8. Missing nctl node-link boundaries (plan item 8)

`nctl/tests/test_reconcile_ledger.py` gained the boundaries the Phase 3 plan named as missing,
all already implemented in `execute_link_actual_node`/`_get_desired_node_by_id` but previously
untested: absent target id (`missing_target_id`), absent candidate id (`missing_candidate_id`),
absent node in the GraphQL snapshot (`node_fetch_failed`), a GraphQL error before the PATCH
(`node_fetch_failed`), a slug mismatch (`node_fetch_mismatch`), a partial pre-existing link where
only `realized_device_source` is set (`node_already_linked` — proves the never-clear-or-replace
guard treats a half-set link the same as a full one), and a wrong confirmed source after a
successful PATCH (`node_link_source_not_confirmed`).

`nctl/tests/test_reconcile_executor.py` gained
`test_link_actual_node_confirmation_failure_after_successful_patch_is_recorded_not_dropped`,
proving the executor's evidence-retention contract (`_execute_action`'s `except LedgerActionError`
path) also holds for a link action that raises *after* a real PATCH: the round does not terminate
and the failed `ActionResult` (with the `node_link_not_confirmed` error code) survives in
`RoundSummary.actions` rather than disappearing. No production code was changed for this item —
current behavior already preserves the record; only the missing test coverage was added. One
observation for the record, not fixed here: that `ActionResult.mutated` stays `False` in this
exact case (a real PATCH happened but confirmation failed), and `_execute_round`'s
`had_side_effects` calculation reads `.success`, not `.mutated`, for every ledger action — so a
lone confirmation-failure in an otherwise-empty round does not by itself trigger the post-failure
final-drift refresh. Changing that is a behavioral change to reconcile's convergence/progress
semantics beyond this step's test/documentation scope; flagging it here rather than changing it
unreviewed.

## 9. Documentation corrected (plan items 9-11)

- `nctl/docs/register-a-new-pc.md` Sections 1-3: rewritten from the removed `sources/add/`/
  `nodes/quick-add/` UI forms to the current `nauto/seed/intent_sources.yaml` +
  `Import Intent Sources` Job path; the superseded note strengthened to state the routes are
  deleted, not merely deprecated.
- `nctl/docs/add-a-basic-service.md`: "Steps (Nautobot UI)" section rewritten to
  "Steps (`nauto/seed/intent_sources.yaml`)"; added a superseded note; both `DesiredService`/
  `DesiredServicePlacement` creation steps now describe YAML root entries plus the Import Job
  preview/apply sequence instead of `/plugins/intent-catalog/services/add/` and
  `/plugins/intent-catalog/placements/add/` forms.
- `nintent/README_DEV.md`: replaced the active `ButtonsColumn`/`buttons=("edit", "delete")`
  developer guidance (which instructed adding a mutation column) with a statement that Phase 3
  deleted every `ButtonsColumn`/`ToggleColumn`/mutation view and that none should be reintroduced,
  pointing at the manifest test that catches a regression.
- Searched (`rg`) all current `*.md` files under `devdocs/`, `nctl/docs/`, and repo-root
  READMEs for `sources/add`, `nodes/quick-add`, `Quick Host Add`, `source_yaml_list`,
  `desiredhost_quick_add`, `ButtonsColumn`, `ToggleColumn`, `TABLE_ACTION_BUTTONS`,
  `alignmentreview_add`, `braindumpdocument_add`. All other matches are either dated historical
  `devdocs/big/*/pN/` reports/plans (left as history, per the plan's "classify rather than
  delete" instruction) or `nintent/DEVLOG_PICKUP.md` (a dated devlog narrating past debugging,
  not an operative recipe) or `nintent/README.md`/`README_QUICK.md`, both of which already state
  the UI is read-only descriptively rather than instructing a removed action.

## Correction notes on Phase 3 reports (plan item 12)

Added dated (2026-07-26) `[!WARNING]` correction blocks, without deleting any original text, to:

- [`p3/report.md`](../p3/report.md) (final report) — points at the Section 2 audit and the three
  step-report corrections below.
- [`p3/report8.md`](../p3/report8.md) (Step 8) — the claimed complete disposable UI runtime pass
  is not reproducible; the permission/fingerprint gaps are named specifically.
- [`p3/report9.md`](../p3/report9.md) (Step 9) — no surviving harness or artifact for the claimed
  HTTP cross-component proof.
- [`p3/report10.md`](../p3/report10.md) (Step 10) — the named final nintent SHA (`271fba1`) is
  superseded by `5881a6f`; the passing local-suite numbers were never evidence for the disposable
  Nautobot/HTTP claims.

## Verification

- `python3 -m unittest discover -s nautobot_intent_catalog/tests` (nintent, Django-free): **226
  passed, 13 skipped** (up from 223 passed/10 skipped — the 3 new skips are Django-only manifest
  tests added this step; every one of them is exercised under `HAS_DJANGO` and will run for real
  in Step 2's disposable Nautobot run).
- `uv run pytest` (nctl): **962 passed** (up from 954 — 7 new `test_reconcile_ledger.py` cases +
  1 new `test_reconcile_executor.py` case; one initial assertion in the executor test was wrong
  about action count — `_regenerate_production_inventory` always appends a `production_inventory`
  action even with zero service actions — found and fixed before this report).
- `git -C nintent diff --check`, `git -C nctl diff --check`, `git diff --check`: all **clean**.

## What Step 1 does not close

The Django-free/pytest results above are **not** the disposable Nautobot runtime, HTTP, or GraphQL
proof the plan's Section 2.3 closure gate requires — that is Step 2's job, using the real Nautobot
3.1.3 test runner against this repaired source. The one flagged observation in Section 8 above
(`mutated`/`had_side_effects` semantics for a post-PATCH confirmation failure) is deferred, not
fixed, pending explicit review since it changes reconcile's operational convergence behavior.
Documentation correction is limited to the current, active files found by the Section 10 search
run so far; the plan's full Section 10 search list is re-run exhaustively in Step 10.

Next: Step 2 (re-prove Phase 2/3 in disposable Nautobot and HTTP) — requires a disposable
Nautobot/PostgreSQL/Redis environment, which this environment does not have available inline;
proceeding requires either provisioning that environment or explicit confirmation of how to
proceed.
