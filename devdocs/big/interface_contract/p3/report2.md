# Interface Contract Phase 3 — Step 2 Report: Freeze Executable Tests for Final UI

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Changes

In Step 2, executable tests for the final read-only UI contract were created and frozen prior to deleting UI views, forms, and routes:

1. **Created `test_ui_contract.py`**:
   - Defined `RETAINED_UI_ROUTE_NAMES` manifest containing exactly 22 GET inspection routes (11 list routes + 11 detail routes).
   - Defined `REMOVED_UI_ROUTE_NAMES` manifest containing all 38 mutation and utility routes to be deleted (`*_add`, `*_edit`, `*_delete`, `desiredhost_quick_add`, `source_yaml_list`, `alignmentreview_*`, and fallback `source_list`).
   - Added `test_retained_routes_count_is_22`: Asserts the retained manifest length is exactly 22.
   - Added `test_retained_routes_can_be_reversed`: Asserts every retained list and detail route resolves via Django `reverse()`.
   - Added `UINonMutationRuntimeTests.test_post_to_retained_list_pages_does_not_mutate`: Asserts retained list GET pages reject POST requests or handle them without modifying underlying model rows.

---

## 2. Test Verification Results

- **nintent unit test suite:**
  `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  Result: **231 passed, 8 skipped** (Nautobot runtime skips).

- **nctl test suite:**
  `uv run pytest`
  Result: **954 passed**.

---

## 3. Next Steps

Proceed to **Step 3: Remove ordinary model mutation views, forms, and URLs**, deleting all `ObjectEditView`, `ObjectDeleteView`, forms, and mutation URL declarations from `nintent`.
