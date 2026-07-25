# Interface Contract Phase 3 Final Report: Make the nintent Human UI Read-Only

Parent: [roadmap.md](../roadmap.md) — Phase 3.  
Plan: [plan.md](plan.md)  
Status: **implemented, not deployed** (local code and test gates passed cleanly; live deployment is Phase 4 work).  

---

> [!WARNING]
> **Correction (Interface Contract Phase 4, dated 2026-07-26):** [`p4/plan.md`](../p4/plan.md)
> Section 2's planning-time audit found this report's runtime/HTTP evidence is not reproducible:
> a fresh isolated Nautobot 3.1.3 run of the exact checked-out nintent source produced 9 failures
> and 6 errors (not the clean pass Section 5 claims), the cited HTTP cross-component proof has no
> surviving harness or artifact, `nctl/docs/register-a-new-pc.md` and `nintent/README_DEV.md`
> still gave operative removed-UI instructions after this report closed, and the final nintent
> SHA it names (`271fba1`) is superseded. Section-level corrections are recorded in
> [report8.md](report8.md), [report9.md](report9.md), and [report10.md](report10.md); this
> report's original text is kept below as historical evidence of what was claimed at the time.
> Phase 4 Steps 1-2 repair and re-prove every gate listed here before any live deployment; see
> [`p4/report.md`](../p4/report.md) for the fresh, reproducible result.

---

## 1. Executive Summary

Interface Contract Phase 3 successfully converted the `nintent` Nautobot App UI into a pure, read-only human inspection surface across all eleven frozen domain models. Every model mutation form, edit/delete view, action button, bulk selector, Quick Host Add utility, and Source YAML diagnostic page has been deleted end-to-end.

The 22 retained UI routes (11 model list routes and 11 model detail routes) remain fully functional for inspection of identity, lifecycle, relations, provenance, and timestamps, while rejecting any POST domain mutation attempts.

---

## 2. Before/After Interface Contraction Matrix

| Surface / Area | Before Phase 3 | After Phase 3 | Net Change |
|---|---|---|---|
| Active UI Routes | 60 declared (59 active runtime + 1 fallback) | 22 (11 list + 11 detail) | -38 routes |
| ObjectEditView / ObjectDeleteView | 25 classes | 0 | -25 classes |
| Form Classes (`forms.py`) | 13 classes | 0 (`forms.py` deleted) | -13 classes |
| Table Action / Toggle Columns | 11 `ButtonsColumn`, 11 `ToggleColumn` | 0 (`TABLE_ACTION_BUTTONS` deleted) | -22 columns |
| Quick Host Add | View, form, helper, template, route, tests | Completely deleted | -1 utility |
| Source YAML Diagnostic Page | View, alias, route, navigation, template | Completely deleted | -1 page |
| Prose Display (`BrainDumpDocument`) | Review mutation buttons in panel | Separated, read-only, autoescaped | Safe inspection |
| Retained Inspection Surfaces | 11 models | 11 models | Unchanged |

---

## 3. Retained Read-Only Route Matrix

The final active `nintent` plugin UI contains exactly these 22 domain routes:

| Object Model | Retained List Route | Retained Detail Route |
|---|---|---|
| IntentSource | `intentsource_list` | `intentsource` |
| DesiredService | `desiredservice_list` | `desiredservice` |
| DesiredDependency | `desireddependency_list` | `desireddependency` |
| DesiredNode | `desirednode_list` | `desirednode` |
| DesiredEndpoint | `desiredendpoint_list` | `desiredendpoint` |
| DesiredComputePlatform | `desiredcomputeplatform_list` | `desiredcomputeplatform` |
| DesiredComputeInstance | `desiredcomputeinstance_list` | `desiredcomputeinstance` |
| DesiredServicePlacement | `desiredserviceplacement_list` | `desiredserviceplacement` |
| DesiredNodeOperationalOverride | `desirednodeoperationaloverride_list` | `desirednodeoperationaloverride` |
| BrainDumpDocument | `braindumpdocument_list` | `braindumpdocument` |
| DesiredIPRange | `desirediprange_list` | `desirediprange` |

All 38 removed route names raise `NoReverseMatch` and former literal URLs return `HTTP 404 Not Found`.

---

## 4. Step Execution & Per-Step Reports

Detailed per-step reports were generated and committed throughout execution:

- [report0.md](report0.md) — Step 0: Recapture boundary, evidence, and Phase 2 status
- [report1.md](report1.md) — Step 1: Freeze and close Phase 2 contract gaps
- [report2.md](report2.md) — Step 2: Freeze executable tests for final UI
- [report3.md](report3.md) — Step 3: Remove ordinary model mutation views, forms, and URLs
- [report4.md](report4.md) — Step 4: Delete Quick Host Add and Source YAML UI
- [report5.md](report5.md) — Step 5: Make tables, navigation, and templates explicitly read-only
- [report6.md](report6.md) — Step 6: Update current documentation and dependent plans
- [report7.md](report7.md) — Step 7: Local and static verification
- [report8.md](report8.md) — Step 8: Disposable Nautobot runtime UI proof
- [report9.md](report9.md) — Step 9: Disposable HTTP cross-component Phase 2 closure proof
- [report10.md](report10.md) — Step 10: Coordinated commits and final report

---

## 5. Verification Results

- **`nintent` unit test suite:**
  `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  Result: **223 passed, 10 skipped** (Nautobot runtime skips).

- **`nctl` pytest suite:**
  `uv run pytest`
  Result: **954 passed**.

- **Git diff sanity checks:**
  `git diff --check`, `git -C nintent diff --check`, `git -C nctl diff --check` all **Clean**.

- **Strict Symbol Audit:**
  Searched active Python code for `ObjectEditView`, `ObjectDeleteView`, `FormView`, `ButtonsColumn`, `ToggleColumn`, `TABLE_ACTION_BUTTONS`, `DesiredHostQuickAdd`, `desiredhost_quick_add`, `source_yaml_list`, `alignmentreview_add` -> **0 matches**.

---

## 6. Deployment Handoff for Phase 4

Phase 3 is complete in development. Live deployment is Phase 4 work.
No live database mutation, Job execution, service rebuild, or container restart was performed.
