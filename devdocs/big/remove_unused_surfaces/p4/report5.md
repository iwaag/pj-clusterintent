# Phase 4 Step 5 — Run final deletion and retained-contract searches

Parent: [plan.md](plan.md) Step 5.

Executed 2026-07-25. Evidence added to
`.local/remove-unused-surfaces/p4/20260725-172224/`: `deletion-search-after.tsv` (same 26-token,
6-repository search re-run after Steps 2–4's edits).

## 1. Re-run vs. Step 1 baseline

Diffed the distinct-file lists between `deletion-search-before.tsv` (Step 1) and
`deletion-search-after.tsv` (this step):

- `nintent/README_QUICK.md` dropped out — its only remaining `dashboard` word is the bare word
  (not one of the 26 exact tokens); its `nctl dashboard`/`dashboard_url` token matches are gone
  (Step 2 removed them).
- This phase's own `report1.md`–`report4.md` appear (new, self-documenting the removal — expected
  `initiative-evidence`).
- `devdocs/big/vm/roadmap.md` newly appears, matching only `nctl serve` inside the new
  removed-surfaces note's own sentence (line 21) — an explanatory supersession notice naming the
  retired surface solely to prevent reintroduction, allowed under plan §6.3.

No other file's match set changed. `nintent/README.md` still contains 2 `dashboard`-adjacent lines
(both inside the new "Current status and operation evidence" section, explicitly framed as removed)
— unchanged in count from Step 2's own report.

## 2. Runtime/module/package re-check

- `grep -rn` across `nctl/src/nctl_core/` for `dashboard`, `serve`, `FastAPI`, `uvicorn`,
  `Starlette`, `WebSocket`: zero real matches — every hit is a substring of `observed`/`reserved`/
  `server-side operation lock once...` prose (`reconcile/lock.py:4`, historical-tense, describing a
  Phase 5 idea that was never built there and is now moot).
- `nctl/pyproject.toml` and `nctl/uv.lock`: zero matches for `fastapi`/`uvicorn`/`starlette`/
  `websockets`/`httptools`/`uvloop`/`watchfiles`/`python-dotenv`, confirming Phase 1's dependency
  removal still holds.
- `nintent/nautobot_intent_catalog/` (excluding `migrations/` and `tests/`): zero matches for
  `reconciliation_status`, `reconciliation_checked_at`, `dashboard_url`, `dashboard_redirect` —
  confirms Phase 3's model/view/URL/nav/setting removal still holds after this phase's
  documentation-only edits.

## 3. Active VM/Braindump/core-reconcile documents, matches read in context

| File | Matches (exact tokens) | Context |
|---|---|---|
| `devdocs/big/core_reconcile/roadmap.md` | 4 (`nctl dashboard` ×1, `nctl serve` ×3) | 2 inside the Phase 3/5 "Original goal" historical description (bracketed by the new superseded headers); 2 inside the Vision/design-conventions explanatory notes added in Step 3 |
| `devdocs/big/braindump/roadmap.md` | 2 (`nctl serve` ×2) | both inside the Phase 4 supersession paragraph/struck-through bullet |
| `devdocs/big/vm/roadmap.md` | 1 (`nctl serve`) | inside the new removed-surfaces note |
| `devdocs/big/vm/p3/plan.md` | 2 (`nctl serve`, `reconciliation_status`) | both inside the top supersession note, updated in Step 3 |

Every remaining match in these four files is a supersession/explanatory notice naming the retired
surface solely to prevent reintroduction (plan §6.3), or historical description bracketed by an
explicit superseded header. No operative "add/build/keep this surface" instruction remains in any
active document.

## 4. `git diff --check`

Clean (no output) in the superproject and all five submodules.

## 5. Final classified exception table

| Classification | Count (post-edit) | Basis (plan §6.3) |
|---|---:|---|
| `initiative-evidence` (this phase's own explanatory notices + reports) | 4 roadmap/plan notices + this phase's `plan.md`/`report0–5.md` | "a current supersession notice that names the retired surface solely to prevent reintroduction" / "the parent roadmap, refactoring vision, this plan, and Phase 4 report explaining removal" |
| `historical` (Phase 3/5 "Original goal" text, all completed phase reports) | ~105 files (unchanged from Step 1) | "historical plans/reports/fixtures whose active roadmap marks the goal superseded" |
| `migration` | 3 (`0009`, `0010`, `0016`) | "applied migration history" / "the explicit removal migration" |
| `negative-test` | 1 (`test_remove_unused_surfaces.py`) | "a negative assertion proving absence" |
| `initiative-evidence` (opaque fixture) | 1 (`test_operations_index.py`) | "the historical opaque-artifact fixture" |
| `keep-unrelated` | ~5 (`ansible_agdev/api/*`, `nauto`/`nodeutils` `published_ports`, nctl `observe_node`/subscriber-prose false positives) | "an unrelated component match with a named retained consumer" / not an actual token match |

No unexplained active-code, current-document, runtime import, schema, model field, config reader,
dependency, or template match remains.

## Gate

No unexplained active match remains; all exceptions fit plan §6.3. Step 5 gate met.
