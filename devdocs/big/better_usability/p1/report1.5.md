# Phase 1 Step 1.5 — Classify findings and isolate reconcile execution

Parent: [plan.md](plan.md) Step 1.5. Classification of the 16 Phase 1 codes (item 1) was already
landed in `report1.2.md` to close the `UnclassifiedDiffCodeError` window in the same commit as
composer localization; this step covers items 2-6: evidence preservation, blocked-host derivation,
action filtering, split blocking semantics, and truthful re-plan/terminal state.

## What changed

`reconcile/model.py` (`ReconcilePlan`): added `has_global_blocking_findings()` (any manual_review/
unsupported record with `target.kind == "global"`) and `has_local_blocking_findings()` (any record
with `target.kind != "global"`). `has_blocking_findings()` is unchanged (still used where the
global/local distinction doesn't matter) — the serialized plan schema itself is untouched, these
are pure derived queries.

`reconcile/planner.py` (`build_plan`):

- Derives `blocked_node_slugs` from the scope's own `manual_review` list: `target.kind == "node"`
  and `code in PHASE1_LOCAL_CODES` (imported from `production/composer.py`, not redeclared).
  Because every Phase 1 local code is node-targeted, `nctl reconcile HOST` selects only that host's
  blocker automatically (via the existing `select_scoped_diffs` scoping, unchanged) and cluster
  scope naturally sees the complete set.
- Before building each `service_profile`/`dnsmasq_config` action, filters `blocked_node_slugs` out
  of its `host_slugs`. An action left with zero hosts is omitted entirely (`continue`) rather than
  built empty — the reason isn't lost, because the owning node's `ManualReviewRecord` (with its
  `evidence` — desired placement/config context and `actual.stage`, both already populated by
  `_manual_record`'s existing default) remains in `plan.manual_review`/`plan.json` regardless.
- No change was needed to preserve evidence through `ManualReviewRecord.evidence`: `_manual_record`
  already defaults to `{"desired": diff.desired, "actual": diff.actual}`, and Step 1.4's structured
  errors already populate `diff.desired`/`diff.actual` with the placement/config/stage context, so
  this flows through unmodified. Pinned with an explicit assertion in the new tests rather than left
  implicit.

`reconcile/executor.py` (`_run_apply`)'s per-round decision now reads (Decision 5):

1. no actions and no blocking findings at all → `already_converged`/`converged` (unchanged).
2. a **global** blocking finding → `manual_intervention_required` immediately, before any action
   (was: any blocking finding at all, which used to also stop a plan that had independent
   executable actions).
3. no actions remain **and** a local blocking finding is present → `manual_intervention_required`
   (covers both "local blocker, nothing else to do" and, on a later round, "independent progress
   just ran out").
4. otherwise (actions exist, whether or not a local finding accompanies them) → proceed to the
   existing fingerprint/no-progress check and execute the round.
- Round-limit exhaustion (`for...else`): if the last round's plan still carries a local (non-global)
  blocking finding, the terminal state is `manual_intervention_required` instead of the previous
  unconditional `non_converged`/`max_rounds_reached` — covers the plan's explicit edge case where
  independent progress happens to finish exactly on the last permitted round. `plan` is now
  initialized to `None` before the loop so this check is safe even for a degenerate `max_rounds=0`.
- `data.progress_made` needed no change: it was already `bool(data.rounds)`, generic over *why* the
  loop stopped.

## Tests added

`tests/test_reconcile_planner.py`:

- `test_service_action_excludes_a_production_blocked_host` — mixed healthy/blocked host on one
  service action; only the healthy host remains, and the blocked node's manual-review record keeps
  its placement evidence.
- `test_service_action_omitted_when_every_host_is_blocked` — all-blocked service produces no action
  and no `unsupported` record (the reason lives in `manual_review` instead).
- `test_unrelated_automatic_action_survives_alongside_a_blocked_node` — an unrelated
  `link_actual_node` action is still planned when a different node carries a local finding.
- `test_host_scoped_reconcile_selects_only_that_host_blocker` — `PlanScope(kind="host", ...)`
  naturally includes/excludes the right node's blocker via existing scoping.

`tests/test_reconcile_executor.py`:

- `test_local_blocker_allows_independent_action_then_reports_manual_intervention` — round 0 executes
  the healthy node's `link_actual_node` action while the blocked node's finding persists; round 1
  (no more actions) terminates `manual_intervention_required` with `progress_made=True`.
- `test_local_blocker_with_no_actions_terminates_without_mutation` — `missing_operational_config`
  alone, no actions at all: `manual_intervention_required`, zero rounds, zero mutation calls.
- `test_global_blocker_stops_before_any_action_even_with_actionable_drift` — a `global` finding
  alongside an otherwise-actionable `actual_node_not_linked` diff: zero actions execute.
- `test_max_rounds_reached_with_a_known_local_blocker_reports_manual_intervention` — `max_rounds=1`;
  independent progress exhausts the single permitted round while the local blocker remains: terminal
  state is `manual_intervention_required`, not `max_rounds_reached`.

## Test count

```
uv run --project nctl pytest -q nctl/tests
```

Result: **565 passed** (557 after Step 1.4 + 8 new Step 1.5 tests), 1 unrelated pre-existing
warning.

## Outcome vs. exit criteria

- `nctl reconcile` never raises `UnclassifiedDiffCodeError` for these findings (classification
  landed in Step 1.2; `test_every_phase1_local_composer_code_is_classified` pins it) and never runs
  a production action against a blocked node (host-slug filtering above). ✅
- A target-local blocker does not suppress independent healthy-target work; a global blocker still
  suppresses every action. ✅ (executor tests above)
