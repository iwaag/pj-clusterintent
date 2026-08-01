# Creative Workspace — Phase 2 Step 4: Gate, live proof, push

## nctl ordinary gate

`uv run pytest -q` in `nctl/`: **1150 passed**. This phase touches only nctl, so the README_DEV
matrix ends here — no runtime gate (no nintent/nauto surface changed).

## Live proof (read-only)

Observation was already fresh from Step 0 (`checked_at` ~18 min old at baseline, well under the
default 24 h `stale_after_hours`), so no `nctl reconcile agpc --refresh-observation` round was
needed before this proof.

`nctl drift --json` and `nctl workspaces --json` against the live scratch Nautobot:

- `nctl workspaces`: `pj-voxel3dprint @agpc  presence=present  identity=matched
  activity=active_development  freshness=fresh` (`ahead=5, behind=0, dirty=false`).
- `nctl drift --json`'s `kind="workspace"` target: `{"slug": "pj-voxel3dprint", "status":
  "converged", "diffs": []}` — agrees with `workspaces` exactly (exit criterion 2, and the
  `engine.py` seeding fix from Step 3 is what makes the workspace visible here at all).
- **User-confirmed** the `active_development` classification (`ahead=5, dirty=false`) matches the
  real state of the `pj-voxel3dprint` tree on `agpc` right now (exit criterion 1).
- No new unrelated finding appeared: comparing this run's `drift --json` summary/severity_summary
  against Step 0's baseline —

  | | baseline (Step 0) | this run |
  |---|---|---|
  | `converged` | 10 | 11 |
  | `drifting` | 2 | 2 |
  | `unknown` | 3 | 3 |
  | `severity_summary` | `{error:5, warning:5, info:6}` | identical |

  The only change is `converged` 10→11 — exactly the new `pj-voxel3dprint` workspace target,
  everything else byte-identical. No informational status code appears among the drift severities
  (exit criterion 3, and both the `test_workspace_evaluation.py` and `test_drift_comparators.py`
  regression guards from Step 2 hold this structurally, not just this once).

## Exit criteria — final check

| # | Criterion | Evidence |
|---|---|---|
| 1 | Live run shows `pj-voxel3dprint`/`agpc` present, identity-matched, truthful activity class (user-confirmed). | Above. |
| 2 | `nctl drift` and `nctl workspaces` derive from the same evaluation and cannot disagree. | Same `evaluate_all_workspaces` call over the same snapshot in both (Step 3); live values identical this run. |
| 3 | Informational status never appears among convergent drift codes. | `_WORKSPACE_SEVERITY_BY_CODE`/comparator never reads `activity_class`; two regression tests assert no activity-class string is ever a gap/diff code; live severity_summary unchanged. |
| 4 | nctl ordinary gate passes. | 1150 passed, above. |

All four **complete**.

## Push

nctl at commit `f468772` (superproject pointer bumped in `d2a131c`), pending push.
