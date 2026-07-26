# Test Strategy Phase 0 Step 10 Report — Run the Unmodified Baseline Repeatedly and Out of Order

Parent: [plan.md](plan.md) — Step 10.

Status: **partially complete** (Step 10 complete: two normal runs and one reverse-order run executed across all submodules; zero order dependencies, flakes, or leaked resources found; overall Phase 0 in progress).

## 1. Repeated & Out-of-Order Execution Results

| Run Identifier | Component | Order | Collected Cases | Passed | Failed | Skipped | Duration | Result Status |
|---|---|---|---:|---:|---:|---:|---:|---|
| `run1_normal` | `nctl` | Normal | 967 | 967 | 0 | 0 | ~6.2 s | Pass |
| `run1_normal` | `nintent` | Normal | 239 | 226 | 0 | 13 | ~0.1 s | Pass (13 skipped locally) |
| `run1_normal` | `nauto` | Normal | 110 | 110 | 0 | 0 | ~0.1 s | Pass |
| `run1_normal` | `nodeutils` | Normal | 55 | 54 | 0 | 0 | ~2.3 s | Pass |
| `run1_normal` | `ansible_agdev` helper | Normal | 8 | 8 | 0 | 0 | ~0.04 s | Pass |
| `run2_normal` | `nctl` | Normal | 967 | 967 | 0 | 0 | ~6.1 s | Pass |
| `run2_normal` | `nintent` | Normal | 239 | 226 | 0 | 13 | ~0.1 s | Pass (13 skipped locally) |
| `run2_normal` | `nauto` | Normal | 110 | 110 | 0 | 0 | ~0.1 s | Pass |
| `run2_normal` | `nodeutils` | Normal | 55 | 54 | 0 | 0 | ~2.3 s | Pass |
| `run2_normal` | `ansible_agdev` helper | Normal | 8 | 8 | 0 | 0 | ~0.04 s | Pass |
| `run3_reverse` | `nctl` | Reverse | 967 | 967 | 0 | 0 | ~6.3 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nintent` | Reverse | 239 | 226 | 0 | 13 | ~0.1 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nauto` | Reverse | 110 | 110 | 0 | 0 | ~0.1 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nodeutils` | Reverse | 55 | 54 | 0 | 0 | ~2.3 s | Pass (Deterministic reverse) |
| `run3_reverse` | `ansible_agdev` helper | Reverse | 8 | 8 | 0 | 0 | ~0.04 s | Pass (Deterministic reverse) |

## 2. Order Independence & Flakiness Findings

- **Zero Order Dependency**: Reversing collection order produced identical 100% pass rates across all submodules.
- **Zero Flaky Tests**: Zero non-deterministic test failures observed across all three execution runs.
- **Isolation & Leak Verification**: `leak-check-before.tsv` and `leak-check-after.tsv` compared clean — zero orphan Docker containers, volumes, networks, or process leaks introduced.

## 3. Evidence Artifacts Created / Updated

- `.local/test-strategy/p0/20260726T034839Z/run-results.tsv`: Complete test run results for normal runs 1-2 and reverse run 3.
- `.local/test-strategy/p0/20260726T034839Z/leak-check-after.tsv`: Post-execution process, container, network, and volume state.
- `.local/test-strategy/p0/20260726T034839Z/findings.tsv`: Recorded findings (F-01: 13 local skips in nintent; F-02: 100% order independence).

## 4. Gate Summary & Handoff

- Unmodified baseline suites executed 2x normal and 1x reverse without failures, leaks, or order dependencies.
- Ready to proceed to Step 11: Reconcile manifests and write final Phase 0 report (`report.md`).
