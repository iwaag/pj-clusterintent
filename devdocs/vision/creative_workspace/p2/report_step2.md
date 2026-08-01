# Creative Workspace — Phase 2 Step 2: Shared evaluation + drift comparator

nctl commit pending (this step's changes not yet committed as of writing this section header — see
below for the final SHA).

## What was built

`nctl/src/nctl_core/drift/workspace_evaluation.py` (new) — `evaluate_workspace` (one declared
workspace → one `WorkspaceEvaluation`) and `evaluate_all_workspaces` (fan-out over
`snapshot.desired.workspaces`), following `binding_evaluation.py`'s shape: one small pure function,
directly testable, no registry/`DiffRecord` knowledge. Per workspace it produces:

- **Presence verdict** (`workspace_missing` when desired present + observed `present: false`).
- **Identity verdict** (`workspace_identity_mismatch` when normalized remote URLs differ;
  `workspace_identity_unknown` — the open edge's own code, chosen over folding into mismatch — when
  `raw.is_git is False` or `remote_url` is absent; unknown never a mismatch).
- **Retired-present** (`workspace_retired_present`, desired absent + observed present; carries no
  `recommended_actions` field at all, since `DiffRecord` has none to attach — the report-only
  contract holds by construction).
- **Freshness** (`workspace_observation_missing` / `workspace_observation_stale`, same
  `age_hours`/`stale_after_hours` shape as `binding_evaluation.py`/`service_placement.py`; no
  realized device ⇒ `workspace_observation_missing` with `reason: "no_realized_device"`).
- **Activity classification** (`activity_class` + `activity_reasons`, a wholly separate field never
  read by the comparator): `active_development` (ahead>0 or dirty), `behind_origin` (behind>0, not
  active), `idle` otherwise; no-upstream classifies from `dirty` alone per the open edge's chosen
  resolution.

All five are independent dimensions computed in the same pass, mirroring
`service_placement.py`'s "process state and managed-file content are two independent actual-state
dimensions" precedent — a stale observation still gets a presence/identity verdict, and vice versa.

A malformed entry (`present` not a bool) degrades to `workspace_observation_missing` for that
workspace only, never a crash or an evaluation of undefined fields (`Known pitfalls` §1).

## Comparator

`@register("workspace")` `workspace_intent_matching` in `comparators.py`: one `DiffRecord` per gap
in `WorkspaceEvaluation.gaps`, `Target(kind="workspace", slug=..., name=..., id=...)`, severity from
a closed `_WORKSPACE_SEVERITY_BY_CODE` map matching the plan's table exactly
(`workspace_missing`/`workspace_identity_mismatch` → error; everything else → warning).
`activity_class`/`activity_reasons` are never touched by the comparator — the only way an
informational string could reach `DiffRecord.code` is if a future change starts iterating them,
which the regression test below guards against.

## Plumbing

- `DriftContext.workspace_observation_max_age_hours` (default 24), threaded from
  `ReconcileConfig.workspace_observation_max_age_hours` (new, same default/bounds as
  `service_observation_max_age_hours`) via `drift_render.py`'s `fetch_and_compute_drift` — its own
  knob, not reusing the service one, since workspace and service observation freshness are separate
  domains (`Known pitfalls` §3: no shared service vocabulary).
- `evaluation_snapshot.py`'s private `_parse_now` renamed to public `parse_now` and reused by
  `workspace_intent_matching` — the same `context.generated_at` → `datetime` parsing, now shared
  across two comparator modules rather than duplicated.
- `example.nctl.toml` and `tests/test_config.py` updated with the new config knob.

## Tests

`tests/test_workspace_evaluation.py` (20 cases, table-driven where useful):
- Each drift code fires and doesn't (`workspace_missing`, `workspace_identity_mismatch`,
  `workspace_identity_unknown` for both the not-a-git-repo and no-remote-url edges,
  `workspace_retired_present`, `workspace_observation_missing`/`_stale`).
- `workspace_retired_present` carries no `recommended_actions` key (asserted directly).
- Activity classes incl. the no-upstream edge (5-case parametrize table).
- Stale vs fresh boundary (both sides of `stale_after_hours`).
- No realized device → `workspace_observation_missing` with the right `reason`.
- Malformed `present` degrades to `workspace_observation_missing`, not a crash.
- SSH ↔ HTTPS remote URL normalization, both directions.
- Retired + absent + no observation entry → silent (the common case per `Known pitfalls` §4).
- **Regression guard for exit criterion 3**: `test_no_informational_status_string_ever_appears_as_a_gap_code`
  runs every activity-triggering scenario and asserts no gap code intersects `ACTIVITY_CLASSES`.

`tests/test_drift_comparators.py` (+4 cases): `workspace_intent_matching` registered under
`"workspace"`; silent when converged; `workspace_missing` diff carries `target.kind == "workspace"`
and `severity == "error"`; a second exit-criterion-3 regression guard at the comparator/`DiffRecord`
boundary (ahead+dirty entry, asserts no diff code is an activity-class string).

## Gate

`uv run pytest -q` in `nctl/`: **1135 passed** (up from 1111 after Step 1 — 20 new
`test_workspace_evaluation.py` cases + 4 new `test_drift_comparators.py` cases +
`test_config.py`'s one extended assertion).

## Deviations from the plan

- **`workspace_identity_unknown`** chosen as the open edge's own code (the plan's two options),
  rather than folding into `workspace_identity_mismatch` with a distinguishing reason — keeps the
  severity split clean (mismatch is genuinely divergent/error; unknown is merely uninformative/
  warning) without a reader having to inspect `reason` to tell them apart.
- **`workspace_observation_max_age_hours`** is its own `ReconcileConfig`/`DriftContext` field, not a
  reuse of `service_observation_max_age_hours` — the plan's freshness precedent said "use it [the
  per-entry `checked_at`], not the device-level ingest timestamp" but didn't mandate sharing the
  threshold knob itself, and a separate knob keeps workspace and service tuning independent per the
  "don't leak service vocabulary" pitfall.
- `evaluation_snapshot._parse_now` → `parse_now` (public rename, no behavior change) so
  `comparators.py` can reuse it instead of re-parsing `context.generated_at` a second way.
