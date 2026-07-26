# Test Strategy Phase 0 Step 4 Report — Reproduce Measurements

Parent: [plan.md](plan.md) — Step 4.

Status: **partially complete** (Step 4 complete: baseline line counts, test ratios, runtimes, concentration signals, skips, and xfails measured and recorded in private evidence; overall Phase 0 in progress).

## 1. Line & Test Count Measurement Comparison

| Component | Total Py Files | Tracked Test Files | Static Defs (AST) | Test Lines | Non-Test Py Lines | Source-to-Test Ratio |
|---|---:|---:|---:|---:|---:|---:|
| `nctl` | 140 | 72 | 901 | 19,706 | 17,783 | 1.108 |
| `nintent` | 53 | 14 | 304 | 5,407 | 9,419 | 0.574 |
| `nauto` | 18 | 8 | 110 | 2,579 | 3,010 | 0.857 |
| `nodeutils` | 5 | 3 | 54 | 917 | 2,157 | 0.425 |
| `ansible_agdev` helper | 3 | 1 | 8 | 146 | 152 | 0.961 |
| **Total** | **219** | **98** | **1,377** | **28,755** | **32,521** | **0.884** |

Line counts are strictly computed over Git-tracked `.py` files. Ansible YAML playbooks and shell scripts are intentionally excluded from the Python ratio.

## 2. Runtime & Slowest Test Signals

| Component | Execution Command | Result Summary | Wall Runtime |
|---|---|---|---:|
| `nctl` | `cd nctl && uv run pytest -q` | 967 passed | ~6.40 s |
| `nintent` | `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` | 226 run, 13 skipped | ~0.10 s |
| `nauto` | `cd nauto && python3 -m unittest discover -s tests` | 110 passed | ~0.10 s |
| `nodeutils` | `cd nodeutils && uv run pytest -q` | 54 passed (55 collected node IDs) | ~2.36 s |
| `ansible_agdev` helper | `cd ansible_agdev && python3 -m unittest discover -s roles/...` | 8 passed | ~0.04 s |

- **`nodeutils` slowest test**: `test_pvesh_helper_integration.py` dominates nodeutils runtime (~2.2s) because it executes the real privileged helper integration boundary. This runtime is justified by its risk tier (Tier A external tool boundary).
- **`nctl` slowest tests**: Repository status tests (~0.27–0.31s each) due to subprocess git spawns. Real multi-round engine/executor tests run fast (~0.03–0.05s).

## 3. Fixture & Test File Concentration Signals

Top largest tracked test files to investigate for potential consolidation during Phase 2:

1. `nctl/tests/test_reconcile_executor.py` (2,355 lines) — many Tier A paths share local stubs.
2. `nintent/.../tests/test_loaders.py` (1,270 lines) — closed-schema YAML loader variants.
3. `nctl/tests/test_dnsmasq_apply.py` (1,033 lines) — renderer, trust, Ansible, and CLI concerns.
4. `nctl/tests/test_production_composer.py` (1,023 lines) — deterministic branch variants.

## 4. Evidence Artifacts Created

- `.local/test-strategy/p0/20260726T034839Z/measurements.tsv`: Exact per-component file counts, test lines, non-test lines, and ratios.
- `.local/test-strategy/p0/20260726T034839Z/runtime-summary.tsv`: Execution duration and result status by component.
- `.local/test-strategy/p0/20260726T034839Z/skips-xfails.tsv`: Recorded skip reasons (13 fast-suite skips in nintent).

## 5. Gate Summary & Handoff

- All line counts, ratios, runtimes, and concentration signals are reproducible from private evidence scripts.
- Ready to proceed to Step 5: Classify removed-surface and historical references (`report5.md`).
