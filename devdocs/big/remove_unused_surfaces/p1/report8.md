# Phase 1 Step 8 — Run the full suite and record final measurements

Parent: [plan.md](plan.md), Step 8.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Full suite

- `uv run pytest -q`: **980 passed**, zero failures/errors.
- `uv run pytest --collect-only -q`: **980 tests collected**, matching the passed count exactly.
- `uv lock --check`: resolved 26 packages, no diff — lock stays in sync with `pyproject.toml`.

## Repeated CLI/deletion checks

- `nctl --help`: same 12 retained commands as every prior step, no `serve`.
- `nctl serve`: exit code 2, `Error: No such command 'serve'.`
- Full 16-token deletion search (same list as Step 6) across `src/`, `tests/`, `pyproject.toml`,
  `uv.lock`, `example.nctl.toml`, `README.md`, `docs/`: **zero matches for every token**.
- `uv tree --locked --invert --package fastapi` / `uvicorn`: empty (absent from the lock).
- `uv tree --locked` (full): only `httpx`, `pydantic`, `pyyaml`, `typer` (runtime) and `pytest`,
  `respx` (dev group) — no server package anywhere in the graph.

## Final measurements

| Metric | Baseline (Step 0) | Final (Step 8) | Delta |
|---|---|---|---|
| `nctl --help` top-level commands | 13 (incl. `serve`) | 12 (no `serve`) | −1 |
| Collected tests | 1029 | 980 | −49 |
| Tracked source lines | 19186 | 18137 | −1049 |
| Tracked test lines | 21140 | 20025 | −1115 |
| `uv.lock` resolved packages | 35 | 26 | −9 |

The −49 test delta (not the raw −54 removed + 5 added figure from Step 3, since Step 6 made no
test-count change) is expected: it is not a target, only the arithmetic result of deleting 50
server/bus tests and 4 compatibility HTTP/WS tests while adding 5 net new regression tests
(Steps 1 and 3 reports have the exact per-file breakdown).

## Diff hygiene

- `git diff --check` across the full Phase 1 range (`cb655c6..HEAD` in `nctl`): clean, no
  whitespace errors.
- `git diff --stat cb655c6..HEAD` in `nctl`: 31 files changed, confined to `README.md`,
  `docs/*.md`, `example.nctl.toml`, `pyproject.toml`, `uv.lock`, `src/nctl_core/cli/main.py`,
  `src/nctl_core/config.py`, `src/nctl_core/events.py`, the deleted `src/nctl_core/serve/*` tree,
  and the seven deleted/edited test files. No `nctl_core/dashboard/`, `dashboard_render.py`,
  `reconcile/executor.py`, or any nintent file appears — no accidental Phase 2 or kernel scope
  crept in.
- `git status --short` in the root superproject, `nctl`, and `nintent`: all three clean (fully
  committed). `nintent` has zero commits from this phase, confirming it stayed out of scope as
  required.

## Gate

Focused tests, full suite, lock check, clean-install proof (Step 7), deletion searches, and diff
hygiene all pass. Proceeding to Step 9 (final report).
