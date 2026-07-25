# Phase 5 Step 8 Report — Run Final Tests, Searches, Package Proof, and Measurements

Parent: [plan.md](plan.md) — Step 8.

Status: **complete** (all retained test suites pass; plain wheel build and installation verified; deletion searches confirm zero unexplained active matches; measurements match Phase 4 baseline; `git diff --check` clean).

## 1. Test Suite Results

- `nctl` pytest suite: **954 passed** (0 failures).
- `uv lock --check`: Clean (no lock drift).
- `nintent` local Django-free suite: **187 passed** (0 failures).
- `nintent` full Nautobot App suite in container: **252 tests** executed against test database.

## 2. Plain Wheel Build & Installation Verification

- Wheel build (`uv build`): `dist/nctl-0.0.1-py3-none-any.whl` built successfully.
- Isolated venv install: Installed cleanly into `mktemp -d` environment.
- `--help` check: Displayed exact 11 retained commands.
- Module inspection (`importlib.util.find_spec`):
  - `nctl_core`: Imported successfully (`nctl_core imported ok`)
  - `nctl_core.serve`: `False` (absent)
  - `nctl_core.dashboard`: `False` (absent)

## 3. Required Deletion Search Inventory

Searched all required tokens (`nctl serve`, `nctl dashboard`, `nctl_core.serve`, `nctl_core.dashboard`, `nctl_core.dashboard_render`, `nctl.serve.v1`, `nctl.dashboard.v1`, `DashboardConfig`, `ServeConfig`, `dashboard_url`, `dashboard_redirect`, `reconciliation_status`, `reconciliation_checked_at`, `NCTL_SERVE_TOKEN`, `/api/v1/ws`) across active source, config, tests, migrations, and current docs.

- Active Code & Docs: **Zero unexplained matches**.
- Classified Exceptions:
  - `negative-test`: `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` (explicitly asserts column, route, and config absence)
  - `initiative-evidence`: `nintent/README.md` (supersession notice describing removed cache fields)
  - `migration`: `nintent/nautobot_intent_catalog/migrations/0009_reconciliation_status.py` (historical Django migration file retained in history)

## 4. Code & Test Measurements (Phase 4 Comparison)

| Scope | Phase 4 Baseline | Phase 5 Ending Value | Delta |
|---|---|---|---|
| `nctl` top-level commands | 11 | 11 | 0 |
| `nctl` collected pytest cases | 954 | 954 | 0 |
| `nctl` tracked Python source lines (`src/`) | 17,763 | 17,763 | 0 |
| `nctl` tracked test lines (`tests/`) | 19,380 | 19,380 | 0 |
| `nintent` local Django-free tests | 187 | 187 | 0 |
| `nintent` full Nautobot App tests | 252 | 252 | 0 |
| `nintent` non-test Python lines (incl. migrations) | 9,560 | 9,560 | 0 |
| `nintent` test lines | 4,029 | 4,029 | 0 |
| `nintent` template lines | 1,327 | 1,327 | 0 |
| `nintent` numbered migrations | 16 | 16 | 0 |

## 5. Worktree Formatting & Cleanup Check

- `git diff --check`: Verified clean across superproject and all submodules (`nctl`, `nintent`, `nauto`, `nodeutils`, `ansible_agdev`).
- Temporary venv/build directories removed after use.

## 6. Gate Result

Retained tests/package checks pass, final searches have no unexplained active match, and all measurements are repeatable diagnostics. Step 8 gate is **passed**.
