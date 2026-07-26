# Test Strategy Phase 0 Step 2 Report — Collect Every Suite in Its Owning Environment

Parent: [plan.md](plan.md) — Step 2.

Status: **partially complete** (Step 2 complete: all test suites statically parsed via AST and collected in their respective owning environments; 1,377 static test definitions reconciled across 5 submodules; overall Phase 0 in progress).

## 1. Inventory Collection Summary

| Component | Static Defs (AST) | Fast Local Collected | Full Environment Collected | Primary Owning Environment | Collection Notes |
|---|---:|---:|---:|---|---|
| `nctl` | 901 | 963 | 963 | `pytest_offline` | 901 AST defs; pytest parametrizations expand node count to 963 |
| `nintent` | 304 | 226 | 304 | `disposable_nautobot_app` | Fast suite runs 226 cases locally (13 skipped); disposable Nautobot App suite collects all 304 cases |
| `nauto` | 110 | 110 | 110 | `unittest_fast` | 110 AST defs; 110 unittest cases |
| `nodeutils` | 54 | 55 | 55 | `pytest_offline` | 54 AST defs; 1 parametrized case expands total to 55 node IDs |
| `ansible_agdev` helper | 8 | 8 | 8 | `unittest_fast` | 8 AST defs; 8 unittest cases |
| **Total** | **1,377** | **1,362** | **1,440** | — | **All 1,377 static definitions reconciled to owning environments** |

## 2. Owning Environments & Environment Gaps

1. **`nctl` (`pytest_offline`)**:
   - Execution command: `cd nctl && uv run pytest --collect-only -q`
   - Collection result: 963 node IDs across 72 test files.
   - All 901 static definitions map cleanly to their pytest node IDs. Parametrizations (e.g., CLI matrix, drift comparators) account for the +62 node ID difference.

2. **`nintent` (`unittest_fast` vs `disposable_nautobot_app`)**:
   - Fast local command: `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
   - Disposable Nautobot App command: `docker exec nautobot-nautobot-1 python3 -c "..."` (Django/Nautobot setup)
   - Fast environment collection: 226 cases. 13 tests are conditionally skipped via `@unittest.skipIf(not HAS_NAUTOBOT)` in local non-Django environments.
   - Disposable Nautobot App environment collection: 304 cases. All 304 static definitions are fully instantiated and collected without skips.

3. **`nauto` (`unittest_fast`)**:
   - Execution command: `cd nauto && python3 -m unittest discover -s tests`
   - Collection result: 110 test cases across 8 test files. Pure domain / ORM-fake suite.

4. **`nodeutils` (`pytest_offline`)**:
   - Execution command: `cd nodeutils && uv run pytest --collect-only -q`
   - Collection result: 55 node IDs across 3 test files (54 static AST definitions). Includes the real privileged helper integration test boundary.

5. **`ansible_agdev` helper (`unittest_fast`)**:
   - Execution command: `cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests`
   - Collection result: 8 test cases in 1 test file.

## 3. Evidence Artifacts Updated

The private evidence directory `.local/test-strategy/p0/20260726T034839Z/` has been updated with:

- `static-tests.tsv`: Complete list of 1,377 statically parsed test functions/methods with file, line number, class name, decorators/marks, and stable test ID.
- `collected-cases.tsv`: List of all runner-collected test cases mapped to their owning environment and static test ID.
- `commands.jsonl`: Appended execution logs for all pytest `--collect-only` and unittest discovery commands.

## 4. Gate Summary & Handoff

- Every tracked test definition (1,377 total) and collected case (1,362 fast / 1,440 full) is reconciled to an owning environment.
- Fast vs. full environment collection gaps for `nintent` (13 skips locally vs. 304 in disposable app) are explicitly identified and visible.
- Ready to proceed to Step 3: Assign tier, contract, boundary, and unique defect (`report3.md`).
