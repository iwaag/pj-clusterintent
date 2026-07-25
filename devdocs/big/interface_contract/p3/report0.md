# Interface Contract Phase 3 — Step 0 Report: Recapture Boundary, Evidence, and Phase 2 Status

**Date:** 2026-07-26  
**Status:** Complete  
**Evidence Directory:** `.local/interface-contract/p3/20260726_004827/`

---

## 1. Repository & Tooling Baseline Snapshot

All worktrees were verified clean prior to starting Phase 3 implementation.

| Target | Revision / Branch | Status |
|---|---|---|
| Superproject (`pj-clusterintent`) | `27bdc4d` (`main`) | clean |
| `nintent` | `cb573b7516b08eaa30aa706e1d2624585c6864c3` | clean |
| `nctl` | `8175f260b8427b4a93c86df7fb85a1b4cfd9923d` | clean |
| `nauto` | `2635e648469d6e6bad87af113f7427b878b0a387` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

**Tool Versions:**
- Python: `3.14.2`
- uv: `0.11.21`

---

## 2. Documents Reviewed

The following governing documents were reviewed for safety boundaries and non-negotiable constraints:
- `README.md` and `README_DEV.md`
- `.local/localenv_memo.md`
- `devdocs/big/interface_contract/roadmap.md`
- `devdocs/big/interface_contract/p3/plan.md`
- Phase 0, 1, and 2 final reports (`devdocs/big/interface_contract/p0/report.md`, `p1/report.md`, `p2/report.md`)

---

## 3. Pre-Phase 3 Baseline Measurement

### UI Route & Class Orientation
- **Declared UI `path()` calls:** 60 in `nintent/nautobot_intent_catalog/urls.py` (59 active runtime domain/utility routes + 1 fallback `source_list` route).
- **Target Retained Routes:** Exactly 22 read-only GET routes (11 model list routes + 11 model detail routes).
- **Target Removed Routes:** 38 routes to be deleted (all `*_add`, `*_edit`, `*_delete`, `desiredhost_quick_add`, `source_yaml_list`, and review mutation routes).
- **View Classes:** 25 `ObjectEditView` / `ObjectDeleteView` subclasses, plus Quick Host Add & Source YAML views to be deleted.
- **Form Classes:** 13 UI form classes to be deleted if no non-UI consumers remain.

### Pre-execution Test Suite Verification
- **nintent test suite:** `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  - Result: **227 passed, 5 skipped** (Nautobot runtime skips).
- **nctl test suite:** `uv run pytest`
  - Result: **954 passed**.

---

## 4. Open Phase 2 Proof Gaps (To be closed in Step 1)

As identified in Section 2 of `plan.md`:
1. Need table-driven Nautobot-runtime contract suite testing complete list/detail/method/field REST matrix and database non-mutation.
2. Assert reverse failure and 404 response for removed REST families (`DesiredService`, `DesiredEndpoint`, `DesiredComputePlatform`, `DesiredComputeInstance`).
3. Assert GraphQL query behavior for removed `IntentSource` roots vs retained roots.
4. Add fail-closed boundary tests for `nctl` node-link state transitions on errors.
5. Correct stale REST descriptions in `nintent/README_DEV.md`.

---

## 5. Next Steps

Proceed to **Step 1: Freeze and close the Phase 2 contract gaps**, strengthening test coverage and closing all identified proof gaps before deleting any UI components.
