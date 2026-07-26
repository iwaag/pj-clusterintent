# Test Strategy Phase 0 Step 5 Report — Classify Removed-Surface and Historical References

Parent: [plan.md](plan.md) — Step 5.

Status: **partially complete** (Step 5 complete: all 9,496 search term matches across active source, tests, migrations, and documentation classified in `reference-classification.tsv`; overall Phase 0 in progress).

## 1. Search Match Classification Breakdown

| Classification Category | Match Count | Meaning & Handling in Test Strategy |
|---|---:|---|
| `historical_document` | 6,140 | Historical devdocs and roadmaps; retained as historical evidence, not active consumers. |
| `retained_contract` | 1,598 | Active production code and retained contract tests; preserved. |
| `external_boundary` | 1,152 | Mocked boundaries (`MagicMock`, `Mock`, `monkeypatch`, `respx`); cataloged for Phase 3 boundary audit. |
| `candidate_consolidation` | 526 | Historical phase filenames (`test_p4_*`, `test_phase3_*`, `test_vm_p3_*`) and removed-surface test wrappers; to be renamed/consolidated in Phase 1/2. |
| `negative_absence_proof` | 48 | Explicit absence assertions (e.g. `test_remove_unused_surfaces.py`); reduced to canonical absence owners in Phase 1. |
| `migration_history` | 32 | Historical Django migration files (`0001` through `0016`); retained in migration history. |
| `orphan` | 0 | Zero unclassified active orphan matches found. |
| **Total** | **9,496** | **Every required search match explicitly classified.** |

## 2. Key Term Audit Highlights

- **Removed Surfaces (`serve`, `dashboard`, `DesiredHostQuickAdd`, `source_yaml`, `PreviewIntentSourceAnalysis`, `GenerateDesiredServices`)**:
  - Active source code: **0 unexplained matches** (all removed in `remove_unused_surfaces` phases).
  - Test suites: Survived only in `test_remove_unused_surfaces.py` as explicit negative absence assertions (`negative_absence_proof`).
- **Historical Phase Test Names (`test_p4_*`, `test_phase3_*`, `test_vm_p3_*`)**:
  - 14 test files carry historical phase names. Their lasting contracts protect core reconcile safety, IPAM, and inert compute, and will be renamed to domain/risk-oriented filenames in Phase 1 without deleting their unique assertions.
- **External Mock Boundaries (`MagicMock`, `Mock`, `monkeypatch`, `respx`, `subprocess`, `ssh-*`, `ansible-*`)**:
  - 1,152 matches represent mock fixtures. Each is mapped in Step 8 to determine whether a disposable real-tool boundary (OpenSSH, Ansible, Nautobot real HTTP) is required.

## 3. Evidence Artifact Created

- `.local/test-strategy/p0/20260726T034839Z/reference-classification.tsv`: Complete list of 9,496 matches with term, repository, file, line number, context snippet, classification, and disposition note.

## 4. Gate Summary & Handoff

- Every required-search match is classified into one of the 7 official Section 6.4 categories. No active match is unclassified.
- Ready to proceed to Step 6: Build the risk and transition manifest (`report6.md`).
