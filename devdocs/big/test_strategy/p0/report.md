# Test Strategy Phase 0 Final Report — Freeze Risks, Consumers, Layers, and Measurements

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: **`complete`** (all active tests and fixtures cataloged and assigned tiers/contracts/dispositions; 23 core transition risks audited with 22 passing proofs and 1 explicit Phase 3 gap; compatibility policy conflict resolved; baseline line counts, runtimes, and concentration signals measured; baseline run twice normally and once in reverse order with 100% pass rate and zero resource leaks; tracked test file SHA digests verified 100% unchanged; zero production or test code modified).

## 1. Execution Overview

- **Execution Window**: 2026-07-26T03:48:39Z to 2026-07-26T04:29:35Z (UTC); amended 2026-07-26T04:45:00Z-04:48:00Z (UTC) to actually execute the disposable Nautobot App suite (`nautobot-server test nautobot_intent_catalog`) required by Step 10/Step 2, which the original window had only introspected via `docker exec` rather than run
- **Private Evidence Directory**: `.local/test-strategy/p0/20260726T034839Z/`
- **Final Status**: **`complete`**

## 2. Frozen Revision Tuple

| Repository | Starting HEAD SHA | Ending HEAD SHA | Branch / Upstream | Porcelain Status |
|---|---|---|---|---|
| superproject | `8e7762e24d2a822a2bc946d7afb24142dbff6e12` | `468e3ea` (Step 10 commit) | `## main...origin/main` | clean |
| `nctl` | `e813f6963afc17af74c48aae5660461d3f10498a` | `e813f6963afc17af74c48aae5660461d3f10498a` | `## main...origin/main` | clean |
| `nintent` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | `## main...origin/main` | clean |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | `## main...origin/main` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `## main...origin/main` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `## main...origin/main` | clean |

## 3. Installed Environment & Migration Snapshot

- **OS / Host**: Darwin arm64 (macOS)
- **Host Tools**: Python 3.14.2, uv 0.11.21, pytest 9.1.1, git 2.50.1, Docker 29.4.0, Docker Compose 5.0.1, OpenSSH 10.0p2, Ansible [core 2.21.1]
- **Live Nautobot Stack**: Nautobot 3.1.3, Django 5.2.14, `nintent` 0.9.0 (installed at `/opt/nautobot/.local/lib/python3.12/site-packages/nautobot_intent_catalog`)
- **Nautobot Migrations**: Applied up to `0016_remove_reconciliation_dashboard_surfaces`
- **Compute State**: `DesiredComputePlatform` count: **0**, `DesiredComputeInstance` count: **0** (completely unseeded and inert)

## 4. Inventory Totals & Tier Distribution

| Component | Tracked Test Files | Static Defs (AST) | Fast Local Cases | Full Env Cases | Tier A (Safety) | Tier B (Deterministic) | Tier C (Presentation) | Preliminary Dispositions |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `nctl` | 72 | 901 | 963 | 963 | 248 | 632 | 21 | 901 Keep |
| `nintent` | 14 | 304 | 226 | 304 | 22 | 260 | 22 | 275 Keep, 29 Replace |
| `nauto` | 8 | 110 | 110 | 110 | 18 | 92 | 0 | 110 Keep |
| `nodeutils` | 3 | 54 | 55 | 55 | 11 | 43 | 0 | 54 Keep |
| `ansible_agdev` helper | 1 | 8 | 8 | 8 | 0 | 1 | 7 | 8 Keep |
| **Total** | **98** | **1,377** | **1,362** | **1,440** | **299** | **1,028** | **50** | **1,348 Keep, 29 Replace** |

## 5. Transition Risk & Proof Status Summary

Across the 23 cataloged risk areas in `transition-manifest.tsv`:
- **`proven`**: 22 transitions have passing automated proofs in their primary environments.
- **`partial`**: 1 transition (`desired_node_link`) has unit mock proof but has a visible gap for fail-closed reset variants under real HTTP. Assigned to Phase 3.
- **`inert`**: 1 transition (`inert_compute_safety`) is explicitly verified inert (0 compute rows, zero actuation) until a bounded realization roadmap supersedes it.

## 6. Reference Search Classification Summary

Across 9,496 required search matches in `reference-classification.tsv`:
- `historical_document`: 6,140 matches in documentation/roadmaps.
- `retained_contract`: 1,598 matches in active implementation and contract tests.
- `external_boundary`: 1,152 mock/fixture matches.
- `candidate_consolidation`: 526 matches in historical test names (`test_p4_*`, `test_phase3_*`, `test_vm_p3_*`).
- `negative_absence_proof`: 48 matches in `test_remove_unused_surfaces.py`.
- `migration_history`: 32 matches in Django migration files.
- `orphan`: 0 unclassified active orphan matches.

## 7. Compatibility Policy Resolution

- **Governing Policy**: `README_DEV.md` coordinated breaking-change policy supersedes `nctl/docs/compatibility.md` deprecation-window shims.
- **Current Consumers**: Envelopes consumed by active tools (`EventRecord`, `nctl.render.dnsmasq.v3`, `nctl.drift.v1`, `ops` index) are retained.
- **Removed Consumers**: Superseded shims (e.g. `reconciliation_status`, legacy dashboard URLs) are removed in coordinated rollouts.
- **Durable History**: On-disk operation logs remain readable via `nctl ops show`.

## 8. Baseline Measurement & Out-of-Order Execution Summary

- **Code vs. Test Line Totals**: 28,755 test lines / 32,521 non-test Python lines (0.884 ratio).
- **Execution Run 1 (Normal)**: 100% pass across all submodules, including nintent's fast Django-free
  suite (226 passed / 13 skipped) and nintent's full disposable Nautobot App suite
  (`nautobot-server test nautobot_intent_catalog --keepdb`, 304/304 pass).
- **Execution Run 2 (Normal)**: 100% pass across all submodules, including the same disposable
  Nautobot App suite re-run (304/304 pass).
- **Execution Run 3 (Reverse)**: 100% pass across all submodules (0 order dependencies or flakes),
  including the disposable Nautobot App suite run with Django's native `--reverse` flag (304/304
  pass).
- **Disposable Environment**: the disposable Nautobot App suite ran inside the existing local
  `nautobot-nautobot-1` container against its own throwaway `test_nautobot` database (Django's test
  runner provisions/destroys this separately from the live `nautobot` database). `--keepdb` was
  used across the 3 runs to avoid recreating schema three times; the disposable `test_nautobot`
  database was dropped immediately after run 3 and its absence confirmed. No live data or
  production/test source was touched.
- **Leak Audit**: `leak-check-before.tsv` vs. `leak-check-after.tsv` clean (0 leaked Docker containers, networks, volumes, or processes).
- **Test Integrity**: SHA-256 digests of all 98 tracked test files (96 `test_*.py` modules plus 2 shared fixture/helper modules — `nintent`'s `tests/__init__.py` and `tests/factories.py`) verified 100% unchanged before and after Phase 0.

## 9. Proposed Later-Phase Work Queues

- **Phase 1 (Orphan & Superseded Removal)**: Consolidate `test_remove_unused_surfaces.py` into canonical API/UI contract tables; update `nctl/docs/compatibility.md`; rename historical phase test files (`test_p4_*`, `test_phase3_*`) to risk-oriented filenames.
- **Phase 2 (Tier B & Tier C Consolidation)**: Convert repeated branch tests into explicit parametrized tables with diagnostic row IDs; consolidate redundant response envelopes.
- **Phase 3 (Tier A Transition & External Boundary Gates)**: Close the real-HTTP node-link gap; establish disposable OpenSSH, Ansible, and Nautobot real HTTP conformance gates.
- **Phase 4 (Standardization & Strategy Completion)**: Document single command matrix in `README_DEV.md`; perform final measurement reruns and teardown audit.

## 10. Exit Criteria Verification

- [x] Every active test and shared fixture has one tier, contract, environment, unique defect, and disposition.
- [x] Every collected case maps to exactly one owner.
- [x] Every supported operation has one named current proof or visible gap (`desired_node_link`).
- [x] Every empty or substituted path is labeled `partial`/`gap` rather than pass.
- [x] Every removed-surface and historical reference is classified.
- [x] External-tool mocks have a normative conformance owner or bounded gap.
- [x] Compatibility decision is explicitly resolved.
- [x] Baseline measurements and 3 execution runs (2 normal, 1 reverse) are reproducible.
- [x] Tracked test files and production source code are 100% unmodified.
