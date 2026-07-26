# Test Strategy Phase 0 Step 10 Report — Run the Unmodified Baseline Repeatedly and Out of Order

Parent: [plan.md](plan.md) — Step 10.

Status: **complete** (Step 10 complete: two normal runs and one reverse-order run executed across all submodules, including nintent's fast Django-free suite and its full disposable Nautobot App suite; zero order dependencies, flakes, or leaked resources found).

## 1. Repeated & Out-of-Order Execution Results

| Run Identifier | Component | Order | Collected Cases | Passed | Failed | Skipped | Duration | Result Status |
|---|---|---|---:|---:|---:|---:|---:|---|
| `run1_normal` | `nctl` | Normal | 967 | 967 | 0 | 0 | ~6.2 s | Pass |
| `run1_normal` | `nintent` (fast, Django-free) | Normal | 239 | 226 | 0 | 13 | ~0.1 s | Pass (13 skipped locally) |
| `run1_normal` | `nintent` (disposable Nautobot App, `nautobot-server test nautobot_intent_catalog --keepdb`) | Normal | 304 | 304 | 0 | 0 | 5.764 s | Pass |
| `run1_normal` | `nauto` | Normal | 110 | 110 | 0 | 0 | ~0.1 s | Pass |
| `run1_normal` | `nodeutils` | Normal | 55 | 54 | 0 | 0 | ~2.3 s | Pass |
| `run1_normal` | `ansible_agdev` helper | Normal | 8 | 8 | 0 | 0 | ~0.04 s | Pass |
| `run2_normal` | `nctl` | Normal | 967 | 967 | 0 | 0 | ~6.1 s | Pass |
| `run2_normal` | `nintent` (fast, Django-free) | Normal | 239 | 226 | 0 | 13 | ~0.1 s | Pass (13 skipped locally) |
| `run2_normal` | `nintent` (disposable Nautobot App, `--keepdb`) | Normal | 304 | 304 | 0 | 0 | 6.039 s | Pass |
| `run2_normal` | `nauto` | Normal | 110 | 110 | 0 | 0 | ~0.1 s | Pass |
| `run2_normal` | `nodeutils` | Normal | 55 | 54 | 0 | 0 | ~2.3 s | Pass |
| `run2_normal` | `ansible_agdev` helper | Normal | 8 | 8 | 0 | 0 | ~0.04 s | Pass |
| `run3_reverse` | `nctl` | Reverse | 967 | 967 | 0 | 0 | ~6.3 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nintent` (fast, Django-free) | Reverse | 239 | 226 | 0 | 13 | ~0.1 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nintent` (disposable Nautobot App, `--keepdb -r`) | Reverse | 304 | 304 | 0 | 0 | 6.424 s | Pass (Django `-r` reverse) |
| `run3_reverse` | `nauto` | Reverse | 110 | 110 | 0 | 0 | ~0.1 s | Pass (Deterministic reverse) |
| `run3_reverse` | `nodeutils` | Reverse | 55 | 54 | 0 | 0 | ~2.3 s | Pass (Deterministic reverse) |
| `run3_reverse` | `ansible_agdev` helper | Reverse | 8 | 8 | 0 | 0 | ~0.04 s | Pass (Deterministic reverse) |

The disposable Nautobot App suite was run inside the existing local `nautobot-nautobot-1` container
via `docker exec nautobot-nautobot-1 nautobot-server test nautobot_intent_catalog --keepdb [-r]`.
Django's test runner provisions and tears down its own throwaway `test_nautobot` database distinct
from the live `nautobot` database; the live database and rows were never touched. `--keepdb` was
used between runs 1-3 to avoid re-creating the schema three times; the disposable `test_nautobot`
database was dropped immediately after run 3 (see Section 3).

## 2. Order Independence & Flakiness Findings

- **Zero Order Dependency**: Reversing collection order produced identical 100% pass rates across all submodules, including the disposable Nautobot App suite (Django's native `-r`/`--reverse` flag).
- **Zero Flaky Tests**: Zero non-deterministic test failures observed across all three execution runs.
- **Isolation & Leak Verification**: `leak-check-before.tsv` and `leak-check-after.tsv` compared clean — zero orphan Docker containers, volumes, networks, or process leaks introduced. The disposable `test_nautobot` Postgres database created by `--keepdb` was dropped via `DROP DATABASE IF EXISTS test_nautobot;` against `my_postgres_db` after run 3; its absence was confirmed with `psql -l`.

## 3. Evidence Artifacts Created / Updated

- `.local/test-strategy/p0/20260726T034839Z/run-results.tsv`: Complete test run results for normal runs 1-2 and reverse run 3, now including the `nintent_disposable_nautobot_app` rows (304/304 pass each run).
- `.local/test-strategy/p0/20260726T034839Z/collected-cases.tsv`: Appended 304 `disposable_nautobot_app` rows for nintent, one per static test owner.
- `.local/test-strategy/p0/20260726T034839Z/commands.jsonl`: Appended the 3 `nautobot-server test` invocations and the `test_nautobot` teardown command.
- `.local/test-strategy/p0/20260726T034839Z/leak-check-after.tsv`: Post-execution process, container, network, and volume state.
- `.local/test-strategy/p0/20260726T034839Z/findings.tsv`: Recorded findings (F-01: 13 local skips in nintent's fast suite, all instantiated and passing in the disposable Nautobot App suite; F-02: 100% order independence across all environments, including the disposable Nautobot App suite).

## 4. Gate Summary & Handoff

- Unmodified baseline suites executed 2x normal and 1x reverse without failures, leaks, or order dependencies.
- Ready to proceed to Step 11: Reconcile manifests and write final Phase 0 report (`report.md`).
