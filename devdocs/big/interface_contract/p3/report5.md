# Interface Contract Phase 3 — Step 5 Report: Make Tables, Navigation, and Templates Explicitly Read-Only

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Changes

In Step 5, all list tables, navigation groups, and detail templates were made explicitly read-only with zero mutation controls or action columns:

1. **Cleaned List Tables (`tables.py`)**:
   - Removed `ButtonsColumn`, `ToggleColumn`, `actions` columns, `pk` columns, and `TABLE_ACTION_BUTTONS` constant across all 11 domain list tables.
   - Retained all identity links, display fields, counts, and sorting attributes.

2. **Cleaned Custom Templates**:
   - **`braindumpdocument.html`**: Removed review mutation buttons (`Add review`, `Edit review`, `Delete review`). Maintained separate, autoescaped panels for the user Braindump body and AI Alignment Review summary.
   - **`desirednode.html`**: Removed the `Add an exception` link targeting `desirednodeoperationaloverride_add`. Replaced with a neutral read-only statement: `"Common operational values are derived. No operational override exists."`

3. **Updated Tests (`test_ui_contract.py`)**:
   - Added static test `test_tables_have_no_action_or_toggle_columns` verifying `ButtonsColumn`, `ToggleColumn`, and `TABLE_ACTION_BUTTONS` do not exist in `tables.py`.

---

## 2. Test Verification Results

- **nintent unit test suite:**
  `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  Result: **223 passed, 10 skipped** (Nautobot runtime skips).

- **nctl test suite:**
  `uv run pytest`
  Result: **954 passed**.

---

## 3. Next Steps

Proceed to **Step 6: Update current documentation and dependent plans**, reviewing and editing `README.md`, `README_DEV.md`, and dependent plan documents.
