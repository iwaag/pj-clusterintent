# Interface Contract Phase 3 — Step 3 Report: Remove Ordinary Model Mutation Views, Forms, and URLs

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Changes

In Step 3, all ordinary model mutation views, edit/delete forms, and URL patterns were removed from `nintent`:

1. **Cleaned `views.py`**:
   - Removed imports for `ObjectEditView`, `ObjectDeleteView`, `FormView`, and all `nautobot_intent_catalog.forms` classes.
   - Deleted all 25 `ObjectEditView` / `ObjectDeleteView` subclasses across all 11 domain models (`IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`, `DesiredComputePlatform`, `DesiredComputeInstance`, `DesiredServicePlacement`, `DesiredNodeOperationalOverride`, `DesiredIPRange`, and `BrainDumpDocument`).
   - Deleted `AlignmentReviewAddView`, `AlignmentReviewEditView`, and `AlignmentReviewDeleteView`.
   - Retained only 11 `ObjectListView` subclasses and 11 `ObjectView` subclasses along with read-only context calculation helpers.

2. **Simplified `urls.py`**:
   - Removed all `*_add`, `*_edit`, and `*_delete` URL patterns.
   - Removed `alignmentreview_add`, `alignmentreview_edit`, and `alignmentreview_delete` patterns.
   - Contracted active UI route declarations to exactly the 22 read-only GET routes.

3. **Deleted `forms.py`**:
   - Verified via repository search that all form classes in `forms.py` existed solely for removed UI mutation views.
   - Deleted `nautobot_intent_catalog/forms.py` completely.

4. **Updated `test_ui_contract.py`**:
   - Added `test_removed_routes_fail_reverse` asserting that all 38 removed UI route names raise `NoReverseMatch`.

---

## 2. Test Verification Results

- **nintent unit test suite:**
  `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  Result: **232 passed, 9 skipped** (Nautobot runtime skips).

- **nctl test suite:**
  `uv run pytest`
  Result: **954 passed**.

---

## 3. Next Steps

Proceed to **Step 4: Delete Quick Host Add and Source YAML UI**, removing `DesiredHostQuickAddView` (helper operations/tests) and `source_yaml_list` templates/routes end-to-end.
