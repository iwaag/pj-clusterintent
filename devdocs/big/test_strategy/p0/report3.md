# Test Strategy Phase 0 Step 3 Report — Assign Tier, Contract, Boundary, and Unique Defect

Parent: [plan.md](plan.md) — Step 3.

Status: **partially complete** (Step 3 complete: all 1,377 static test definitions assigned tier, contract ID, operation kind, unique defect, boundary, primary environment, and preliminary disposition in `test-ownership.tsv`; overall Phase 0 in progress).

## 1. Ownership & Tier Distribution Summary

| Component | Total Static Tests | Tier A (Safety/Mutation) | Tier B (Deterministic) | Tier C (Presentation) | Primary Environment |
|---|---:|---:|---:|---:|---|
| `nctl` | 901 | 248 | 632 | 21 | `pytest_offline` |
| `nintent` | 304 | 22 | 260 | 22 | `disposable_nautobot_app` |
| `nauto` | 110 | 18 | 92 | 0 | `unittest_fast` |
| `nodeutils` | 54 | 11 | 43 | 0 | `pytest_offline` |
| `ansible_agdev` helper | 8 | 0 | 1 | 7 | `unittest_fast` |
| **Total** | **1,377** | **299** | **1,028** | **50** | — |

## 2. Operation Kind Classification

- **`automatic_transition`**: 172 tests (dnsmasq reconciliation, IPAM non-DHCP endpoint linking, cluster/host scoping, fresh drift verification).
- **`explicit_mutation`**: 126 tests (SSH enrollment, Import/Analyze preview-apply transactions, actual-ledger linking, evidence retention).
- **`read_only_deterministic`**: 1,078 tests (YAML loading, renderers, drift comparators, GraphQL/REST schema serialization, CLI output formatting).
- **`unsupported_inert`**: 1 test (`test_vm_p3_compute_stays_inert.py` protecting compute safety prior to bounded realization roadmap).
- **`manual_safe_stop`**: 0 tests assigned as primary owner (safe stops are captured as expected state outputs within Tier A transitions).

## 3. Preliminary Dispositions

- **`keep`**: 1,348 tests (own a reachable unique contract at the appropriate layer).
- **`replace`**: 29 tests (candidates for Phase 1/2 consolidation into canonical API/UI contract tables, e.g. `test_remove_unused_surfaces.py`).
- **`delete`**: 0 tests (no test deleted during Phase 0 read-only audit).
- **`defer`**: 0 tests.

## 4. Evidence Artifact Created

- `.local/test-strategy/p0/20260726T034839Z/test-ownership.tsv` containing all 1,377 static test definitions mapped to their assigned tier, contract ID, operation kind, unique defect, side-effect boundary, positive evidence requirement, and disposition.

## 5. Gate Summary & Handoff

- Every active test has exactly one primary owner, tier, contract, operation kind, unique defect, and preliminary disposition.
- Ready to proceed to Step 4: Reproduce measurements (`report4.md`).
