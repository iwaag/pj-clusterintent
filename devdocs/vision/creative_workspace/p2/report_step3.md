# Creative Workspace — Phase 2 Step 3: `nctl workspaces` view

nctl commit pending (bundled with this report's superproject commit below).

## What was built

`nctl/src/nctl_core/workspaces_render.py` (new), in the `relations_render.py` style:

- `build_workspaces(cfg, *, host=None)` — reuses `fetch_and_compute_drift` for the snapshot and
  `generated_at` (the same call `nctl drift` makes), then calls
  `workspace_evaluation.evaluate_all_workspaces` directly on that snapshot — the *identical* pure
  function `drift.comparators.workspace_intent_matching` calls. Same deterministic inputs, same
  function, so `nctl drift` and `nctl workspaces` cannot disagree about a workspace's convergent
  state by construction (this is the `relations_render.py` precedent for "cannot disagree": it
  recomputes bindings directly rather than re-parsing `DriftResult`, not because the shapes differ
  but because a projection is honestly a second read of the same evaluation).
- `render_workspaces_data` — pure projection, one `WorkspaceRow` per declared workspace: `slug`,
  `name`, `node`, `desired_presence`, `presence` (`present`/`missing`/`unknown`), `identity`
  (`matched`/`mismatch`/`unknown` + `identity_reason` for the unknown case), `activity_class` +
  `activity_reasons`, `freshness` (`fresh`/`stale`/`missing`/`not_observed`), `checked_at`, and
  `gap_codes` (the exact convergent codes for that workspace — a reader can cross-check against
  `nctl drift` directly). Rows sorted by slug; `--host` filters by `node`.
- `render_workspaces_text` — text renderer that spells out the unknown-identity reason
  ("unknown (not a git repo)" / "unknown (no remote configured)") rather than a bare ✓/✗, per the
  plan's explicit ask.
- `nctl.workspaces.v1` envelope schema, `nctl workspaces` CLI command (`--host`, `--json`) wired in
  `cli/main.py` exactly like `relations`' ~6 lines.

## Engine change beyond the plan's literal Step 3 scope

`drift/engine.py`'s `_group_by_target` seeded `node`/`service`/`compute_platform`/
`compute_instance` targets up front (zero diffs ⇒ `converged`) so silence never means "nobody
looked" — documented in the module's own docstring. Workspaces were not seeded, so a fully
converged workspace (no gaps at all) was **invisible in `nctl drift`'s target list**, discovered
by manually diffing live `nctl drift --json` against `nctl workspaces --json` in this step (both
should show `pj-voxel3dprint`; only `workspaces` did). Added workspace to the same up-front seeding
loop — this is squarely within exit criterion 2 ("`nctl drift` and `nctl workspaces` derive from
the same evaluation and cannot disagree"): a workspace missing from one and present in the other
*is* a disagreement, just one of omission rather than contradiction. Confirmed live afterward: both
commands now show `pj-voxel3dprint`/`agpc` as `converged`.

## Tests

- `tests/test_workspaces_render.py` (10 cases): row projection from a canned snapshot (present +
  matched + activity class; missing presence; identity-unknown with reason; stale freshness; the
  retired/absent/no-observation `not_observed` case; `--host` filter; slug sort order; empty-rows
  envelope; two text-renderer assertions kept loose per README_DEV lesson — content, not exact
  formatting).
- `tests/test_cli_workspaces.py` (4 cases): default text output, `--json`, `--host` passthrough,
  exit code 1 on a failed envelope — mirrors `test_cli_relations.py` exactly.
- `tests/test_drift_engine.py` (+1 case): a workspace with no gaps is seeded as `converged` with
  `diffs == []`, guarding the engine fix above.
- `tests/test_cli_surface.py`: `workspaces` added to `RETAINED_COMMANDS` (a closed-set test that
  would otherwise fail on any new top-level command).

## Gate

`uv run pytest -q` in `nctl/`: **1150 passed** (up from 1135 after Step 2).

## Live smoke (read-only, not the Step 4 formal proof)

```
$ nctl workspaces
pj-voxel3dprint @agpc  presence=present  identity=matched  activity=active_development  freshness=fresh
summary: converged=1

$ nctl drift --json | jq '.data.targets[] | select(.target.kind=="workspace")'
{"target": {"kind": "workspace", "slug": "pj-voxel3dprint", ...}, "status": "converged", "diffs": []}
```

Both agree. Step 4 will redo this formally with user confirmation of the activity class against the
real tree state.

## Deviations from the plan

- The `drift/engine.py` seeding fix (above) — not explicitly named in the plan's Step 3 text, but
  required to actually satisfy exit criterion 2 rather than merely not contradicting it.
- `build_workspaces` calls the evaluation module directly rather than re-deriving rows from
  `DriftResult`'s diffs — the plan named both as acceptable ("or the evaluation module directly —
  but then both paths must share the snapshot fetch"); the snapshot fetch is shared via the same
  `fetch_and_compute_drift` call.
