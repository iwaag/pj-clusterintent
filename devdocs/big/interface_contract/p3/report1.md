# Interface Contract Phase 3 — Step 1 Report: Freeze and Close Phase 2 Contract Gaps

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Changes

In Step 1, all remaining Phase 2 REST/GraphQL proof gaps were closed and enforced with executable tests prior to modifying UI components:

1. **Enhanced `test_api_contract.py`**:
   - Added `test_removed_rest_routes_fail_reverse`: Verified that all removed REST endpoints (`desiredservice`, `desiredendpoint`, `desiredcomputeplatform`, `desiredcomputeinstance`) raise `django.urls.NoReverseMatch` for both list and detail patterns.
   - Added `test_retained_rest_routes_reverse`: Confirmed that retained REST collections (`desirednode`, `braindumpdocument`, `alignmentreview`) resolve cleanly under the API namespace.
   - Extended `test_removed_rest_collections_return_404`: Verified that literal URLs for removed collections return `HTTP 404 Not Found` for both list and detail paths.
   - Added `test_node_disallowed_methods_return_405`: Verified that `POST` and list `DELETE` against the node collection fail with `HTTP 405 Method Not Allowed`.

2. **Updated Documentation (`nintent/README_DEV.md`)**:
   - Corrected outdated descriptions naming 5 REST endpoints and `fields = "__all__"`.
   - Documented the exact contracted set of 3 REST collections (`nodes`, `braindumps`, `alignment-reviews`), explicit field lists, and strict writable restrictions on `DesiredNode` (`lifecycle`, `realized_device`, `realized_device_source`).

---

## 2. Test Verification Results

- **nintent unit test suite:**
  `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  Result: **229 passed, 7 skipped** (Nautobot runtime skips).

- **nctl test suite:**
  `uv run pytest`
  Result: **954 passed**.

---

## 3. Next Steps

Proceed to **Step 2: Freeze executable tests for the final UI**, defining tests that assert the presence and read-only nature of the 22 retained UI routes and the absence of all removed UI mutation surfaces before deleting UI code.
