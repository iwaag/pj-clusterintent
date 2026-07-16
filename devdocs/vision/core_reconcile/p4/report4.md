# Phase 4 Report — Step 4 (tighten `converging` and event semantics)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 4. This is the fourth suggested commit
boundary. `converging` no longer comes from scanning arbitrary event `data` for a slug mention;
it is now derived only from a structurally validated `actuation_completed` event, and
`docs/event-log.md` documents the full `nctl reconcile` event vocabulary ahead of Step 5's
executor actually emitting it.

## What was built

### `nctl_core.drift.operations.latest_convergent_actuation_for_target`

Replaces the old `latest_operation_timestamp_for_target`, which treated any event whose `data`
contained the target slug anywhere (list, nested dict, etc.) as evidence of an in-flight change.
The new function:

- only looks at events named `actuation_completed`;
- only matches a target via the explicit `data.target_slugs` list, not a free-form scan;
- always resolves the **chronologically latest** such event across every `*.jsonl` file for that
  target, regardless of which file or line it appears on;
- returns a result only if that latest event has `data.success is True`,
  `data.requires_observation is True`, and a well-formed non-empty `data.claimed_diff_codes` list
  of strings — otherwise returns `None`, even if an earlier event for the same target would have
  qualified.

Because only the single latest matching event is consulted, a later failed or cancelled
actuation always supersedes an earlier success for the same target — there is no separate
"invalidation scan," it falls out of always picking the newest record.

### `nctl_core.drift.status.derive_status`

Now calls the new lookup and additionally requires every current error-severity diff's `code` to
be a member of the actuation's `claimed_diff_codes` before returning `CONVERGING`. An unrelated
error diff (one the matched actuation never claimed) keeps the target `drifting`/`unknown` even
while a claimed diff on the same target would, alone, have qualified. Ledger-only actions (Decision
5's `link_actual_node` PATCH, IPAM Job) are unaffected by this rule by construction: nctl refetches
and reports their real result immediately, so those actions are expected to omit
`requires_observation` (or set it `false`) and never need to appear as `converging`.

### `docs/event-log.md`

Added a "`nctl reconcile` event vocabulary (Phase 4)" section documenting `plan_created`,
`round_started`, `action_started`/`action_completed`, `actuation_completed` (with its exact
`target_slugs`/`claimed_diff_codes`/`requires_observation`/`success` field contract),
`observation_completed`, `drift_resolved`, and `non_converged`, plus an explicit note that
`converging` is never derived from a generic event mentioning a slug. This fixes the field
contract in place before Step 5's registry and Step 7's executor start emitting these events, so
later steps implement against an already-reviewed shape rather than inventing it ad hoc.

## Tests

`tests/test_drift_operations.py` was rewritten around the new function and pins:

- a successful, observation-requiring, claim-carrying actuation is found and its fields returned;
- no match when no actuation names the target;
- **a generic event (e.g. `step_started`) mentioning the slug in `data` is ignored** — the exact
  defect this step fixes;
- a failed actuation (`success: false`) never qualifies;
- **a later failed actuation invalidates an earlier successful one** for the same target;
- an actuation without `requires_observation: true` (the ledger-only-action shape) never
  qualifies;
- latest-across-multiple-files selection, malformed-line tolerance, and a missing/absent
  `claimed_diff_codes` never qualifying.

`tests/test_drift_status.py` keeps the existing non-event-log cases (no error diffs, warning/info
only, unknown code, plain drifting) and adds the plan's named dangerous cases end-to-end through
`derive_status`:

- a generic event mentioning the slug never produces `CONVERGING`;
- a failed actuation never produces `CONVERGING`;
- **one claimed error + one unclaimed error on the same target stays `DRIFTING`**, not
  `CONVERGING`;
- a successful actuation followed by a newer observation timestamp is not `CONVERGING` (already
  covered by the existing timestamp-ordering rule, re-verified against the new lookup);
- the pre-existing claimed-actuation-newer-than-observation case still returns `CONVERGING`.

Service-timestamp freshness for `converging` was already exercised end-to-end by Step 3's service
target `observed_at` derivation (`tests/test_drift_engine.py`, `tests/test_service_placement.py`);
Step 4 changes only how the actuation side of the comparison is found and validated, not how a
service's `observed_at` is computed, so no new service-specific case was needed here.

Verification:

- `cd nctl && uv run pytest -q` — **333 passed** (up from 325 at Step 3: 21 in the two rewritten
  files replacing 12 previously, net +8 covering the new dangerous cases);
- `cd nctl && python3 -m compileall -q src tests` — passed;
- `git diff --check` (parent and nctl) — passed.

## Deliberate non-work

- no reconciler registry, `ReconcileAction`/`ReconcilePlan` schema, or planner (Step 5);
- no code that actually emits `plan_created`/`round_started`/`action_started`/
  `actuation_completed`/`observation_completed`/`drift_resolved`/`non_converged` yet — Step 4
  only fixes the *rule* that consumes `actuation_completed` and documents the contract every
  later step must honor when it starts emitting these events;
- no `deployment_profiles.yml` reconciliation metadata (Step 5);
- no ledger reconcilers, `nctl reconcile` CLI, or dashboard wiring (Steps 6–7);
- no commit, push, or Nautobot deployment — this boundary is nctl-only and requires no
  cross-repo rebuild cycle.

## Files changed in this boundary

nctl:

- rewrote `src/nctl_core/drift/operations.py`
  (`latest_operation_timestamp_for_target` → `latest_convergent_actuation_for_target`);
- updated `src/nctl_core/drift/status.py`'s docstring and `derive_status` to consult the new
  lookup and enforce claimed-code matching;
- rewrote `tests/test_drift_operations.py` and `tests/test_drift_status.py`;
- extended `docs/event-log.md` with the Phase 4 event vocabulary section.

Parent repository:

- added this report. No commit was created.
