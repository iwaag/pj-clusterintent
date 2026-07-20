# Phase 1 Step 1.6 — Test the full failure and orchestration matrix

Parent: [plan.md](plan.md) Step 1.6.

Most of this step's required coverage was already added incrementally alongside each
implementation step (composer matrix in `report1.2.md`, unapplied-intent matrix in `report1.3.md`,
drift/dashboard tests in `report1.4.md`, planner/executor isolation tests in `report1.5.md`). This
step closes the remaining gaps identified by re-reading the plan's explicit checklist against what
existed.

## Gaps found and closed

1. **Mixed snapshot through the real engine, not just `production_policy()` directly.**
   Added `test_mixed_snapshot_isolates_local_error_and_unapplied_intent_through_the_engine` to
   `test_drift_engine.py`: three nodes (healthy, one with a Group C `unknown_profile` error, one
   `planned` node with an active placement) through `compute_drift()`. Asserts no `global` target
   appears, the healthy node's status is evaluated independently (`CONVERGED`), the bad node is
   `DRIFTING` with its `unknown_profile` diff, and the planned node stays `CONVERGED` with a visible
   `WARNING`-severity `active_placement_not_applied` diff carrying full placement evidence.
2. **No duplicate `active_placement_not_applied` when profiles are present.** The plan explicitly
   calls out confirming "the fallback path does not duplicate findings when profiles are available."
   Added `test_active_placement_not_applied_not_duplicated_when_profiles_are_present` — with a real
   profile map supplied, exactly one finding is emitted (via the composer's own
   `report["drift"]`), not two (composer's copy plus a second pass through the degraded-profile
   helper).
3. **Every one of the 16 Phase 1 codes reaches planning without `UnclassifiedDiffCodeError`.**
   `report1.2.md`'s test exercises `classify()` directly; `report1.5.md`'s tests exercise a handful
   of codes through `build_plan`. Added
   `test_every_phase1_local_code_reaches_planning_without_unclassified_error` to
   `test_reconcile_planner.py`, parameterized over all 16 codes (with the one `WARNING`-severity
   code, `active_placement_not_applied`, included) — each lands in `plan.manual_review` with no
   automatic action and no exception.
4. **Dry plan succeeds despite a local composition error** (orchestration case 1 from the plan's
   list). Added `test_dry_plan_succeeds_despite_a_local_composition_error` to
   `test_reconcile_executor.py`: `apply_changes=False` with a `missing_operational_config` diff
   present still returns `state="planned"`, `ok=True`.

## Checklist cross-reference (plan Step 1.6)

- **Composer isolation** — parameterized fixtures for all 15 Group C codes, healthy node intact,
  bad node fully absent, `skipped`/`errors` correct, byte-stable output, Group A/B still global:
  covered in `report1.2.md`.
- **Unapplied intent** — lifecycles, active/disabled, `config={}`, multiple placements, eligible
  control node, empty profile context, deterministic order, node-type-only exclusion: covered in
  `report1.3.md`/`report1.4.md`; no-duplicate-with-profiles closed here (item 2 above).
- **Drift/dashboard** — mixed comparator run, warning visibility, dashboard rendering: covered in
  `report1.4.md`; full-engine integration closed here (item 1 above).
- **Reconcile planner/executor**, the plan's 7 numbered cases:
  1. local error + no actions → dry plan succeeds, apply is `manual_intervention_required` without
     mutation: closed here (item 4) + `report1.5.md`.
  2. bad node + independent healthy action → healthy action and production regeneration execute,
     terminal `manual_intervention_required` after progress: `report1.5.md`.
  3. service action spans blocked/healthy hosts → only healthy remain, all-blocked omitted:
     `report1.5.md`.
  4/5. host-scoped reconcile includes/excludes the right blocker: `report1.5.md`.
  6. global error + actionable drift → zero actions: `report1.5.md`.
  7. every code reaches planning without `UnclassifiedDiffCodeError`: closed here (item 3).

## Test count

```
uv run --project nctl pytest -q nctl/tests
```

Result: **569 passed** (565 after Step 1.5 + 4 new tests), 1 unrelated pre-existing warning.

## Live/fake-mutation note

All executor-level tests use `monkeypatch`-substituted mutation calls (`execute_link_actual_node`,
`AnsibleRunner`, `run_observation`, dashboard/render stubs) — no test in this phase performs a real
Nautobot write, Job trigger, or Ansible run. Live/read-only verification against the configured
development environment is Step 1.7.
