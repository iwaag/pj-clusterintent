# Phase 1 Step 0 — Reconfirm the boundary and starting state

Parent: [plan.md](plan.md), Step 0.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/` (mode `0700`,
files `0600`).

## Revisions and dirty state

| Repository | Revision | Dirty |
|---|---|---|
| superproject | `80553b6a8e7a86ad7aa82901b9b308caeb8d049a` | clean |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean |

All three match the plan's §2.1 planning-time snapshot exactly. `nctl` has no pre-existing edits,
so no ownership/overlap decision is required.

## Phase 0 status

Phase 0 remains `complete` (see `p0/report9.md`); its frozen manifest (24 delete / 32 edit / 42
historical / 4 keep-shared) has not been superseded.

## Manifest and import-trace recheck

All 15 Phase 1 delete paths (8 `nctl_core/serve/` files + 7 dedicated test files) exist and are
unchanged from Phase 0's listing. A fresh import trace
(`grep -rn "nctl_core\.serve\|from \.\.serve\|from \.serve\|import serve" src/ tests/` excluding
the `serve/` package itself) finds importers only in the two files the plan already designates for
editing rather than deletion:

- `src/nctl_core/cli/main.py:57` — `from nctl_core.serve.runtime import ...` (Step 2 edit target);
- `tests/test_compatibility_snapshots.py:36-37` — `from nctl_core.serve.app import create_app`,
  `from nctl_core.serve.runtime import ServeData` (Step 3 edit target).

No newly discovered importer requires an ownership decision.

## Baseline measurements

- `uv --version`: `uv 0.11.24 (Homebrew 2026-06-23 aarch64-apple-darwin)`.
- `uv run nctl --help`: 13 top-level commands, including `dashboard` and `serve` — matches plan
  §2.2 exactly.
- `uv run pytest --collect-only -q`: **1029 tests collected**, matches plan §2.2 exactly.
- Tracked nctl source: **19186 lines**; tracked nctl tests: **21140 lines** — both match plan §2.2
  exactly.
- `uv tree --locked --invert --package fastapi`: reachable only via `nctl (extra: serve)` and
  `nctl (group: dev)`.
- `uv tree --locked --invert --package uvicorn`: reachable only via `nctl[standard] (extra: serve)`
  and `nctl[standard] (group: dev)`.

Both server dependency roots match the plan's frozen expectation with no other reverse-dependency
path.

## Live-process recheck

`ps aux | grep -i "nctl serve"` (excluding the grep process itself) and
`lsof -iTCP:8300 -sTCP:LISTEN` both returned no matches. No live server has reappeared since the
Phase 0 Step 6 incident (stray process stopped 2026-07-25).

## Gate

nctl ownership is clear (clean, no overlapping edits), Phase 0's frozen manifest is confirmed
current, no live server has reappeared, and no newly discovered importer requires an ownership
decision. Proceeding to Step 1.
