# Phase 3 Step 3 — Remove filters, tables, templates, views, URLs, navigation, and settings

Parent: [plan.md](plan.md) Step 3.

Executed 2026-07-25. nintent commit: `fc9488756ecc2af4509fc2237ff8b34d81cc33b8`. Private evidence
directory: `.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`),
containing `step2-removal-tests-post-change.log`, `step2-braindump-regression.log`,
`step2-full-app-suite.log` (produced with both Step 2 and Step 3's edits in place, per the
deviation recorded in `report2.md` — Django cannot import `filters.py`/`views.py` with the fields
already removed from `models.py`, so this step's edits were required before either step's runtime
gate could run).

## 1. Exact file-by-file inventory (matches plan §5.2 exactly, 9 files)

- `filters.py`: removed `reconciliation_status` from `DesiredNodeFilterSet.Meta.fields` and
  `DesiredServiceFilterSet.Meta.fields`. Every other filter/search method unchanged.
- `tables.py`: removed `RECONCILIATION_BADGE_CLASSES`, `_render_reconciliation_status()`, both
  declared `reconciliation_status` columns, both `render_reconciliation_status()` methods, and the
  `reconciliation_status` entry from both `fields`/`default_columns` tuples. Removed the
  `django.utils.html.format_html` import (its only caller was the deleted helper).
- `templates/nautobot_intent_catalog/desirednode.html` /
  `templates/nautobot_intent_catalog/desiredservice.html`: removed the Reconciliation Status and
  Reconciliation Checked At `<tr>` rows (including the conditional `(view dashboard)` link) from
  both detail templates. Realized-device/compute/operational-override/placement/endpoint panels
  are untouched.
- `views.py`: removed `DesiredServiceView.get_extra_context()` and
  `DesiredNodeView.get_extra_context()` (both returned only `{"dashboard_url": ...}`),
  `_configured_dashboard_url()`, and `dashboard_redirect()`. Removed the now-unused
  `Http404`/`HttpResponseRedirect` import (grep-confirmed no other caller). `settings` import
  retained — still used by `_configured_source_file()`.
- `urls.py`: removed the `path("dashboard/", views.dashboard_redirect, name="dashboard_redirect")`
  entry only; every node/service/compute/Braindump route unchanged.
- `navigation.py`: removed `_configured_dashboard_url()`, `_dashboard_items`, the `settings`
  import (no longer used), and the `+ _dashboard_items` tuple concatenation on the Operational
  Tools group. Braindump, Desired State, and Quick Host Add groups/items unchanged.
- `__init__.py`: `default_settings` changed from `{"dashboard_url": None}` to `{}` — no obsolete
  key retained.
- `api/serializers.py`: removed the docstring sentence claiming `reconciliation_status`/
  `reconciliation_checked_at` "stay writable because nctl dashboard is their intentional sole
  writer." Serializer class, `intent_source` ID-based field, and `read_only_fields` unchanged.

No file outside this list and `report2.md`'s `models.py`/`0016` was touched.

## 2. Re-read diff for adjacent-surface safety (plan §7 Step 3.8)

Re-read the full diff around `DesiredNodeView`/`DesiredServiceView` and the Operational Tools
group: `desirednode`/`desiredcomputeplatform`/`desiredcomputeinstance` views and their
`queryset`/`select_related`/`prefetch_related` are byte-identical except for the removed
`get_extra_context()` method; `Quick Host Add` remains the sole retained Operational Tools item.

## 3. Test gate (evidence produced with Step 2 + Step 3 combined, see report2.md's deviation note)

- `nautobot-server test nautobot_intent_catalog.tests.test_remove_unused_surfaces --keepdb`:
  **29/29 passed** (0 failures — all 24 of Step 1's intentional pre-change failures now pass;
  the 5 always-passing retained-path tests remain green).
- `nautobot-server test nautobot_intent_catalog.tests.test_braindump --keepdb`: **33/33 passed**,
  unchanged.
- `nautobot-server test nautobot_intent_catalog --keepdb` (complete app suite): **249/249 passed**.
- `nautobot-server check`: clean (0 issues).
- Live (default-alias `nautobot`) migration state reconfirmed unchanged at `0014` throughout —
  `nautobot-server test` operates only on its own disposable `test_nautobot` database.

## Gate

No current runtime reader/presenter/link/setting for the retired reconciliation cache remains;
shared node/service, compute, and Braindump/Alignment Review paths are unchanged and positively
exercised (249/249 app-suite pass). Step 3 gate met.
