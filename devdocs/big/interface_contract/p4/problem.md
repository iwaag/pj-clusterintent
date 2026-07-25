# Phase 4 Step 1 — Open Problem: `link_actual_node` mutation evidence lost on post-PATCH confirmation failure

Found while adding [report1.md](report1.md) Section 8's missing nctl node-link boundary tests.
Not fixed in Step 1 (test/documentation scope only); recorded here for an explicit decision
before Step 2 or later relies on `reconcile`'s progress/convergence accounting.

## Where

`nctl/src/nctl_core/reconcile/executor.py`, `_execute_action()`'s
`except (LedgerActionError, NautobotJobError, NautobotError)` branch (around line 805), together
with `_execute_round()`'s `had_side_effects` accumulation (lines 552 and 618) and
`_run_apply()`'s `data.progress_made` computation (line 500).

## What happens

`execute_link_actual_node()` (`nctl_core/reconcile/ledger.py`) does, in order:

1. GraphQL precondition read (refuse to replace an existing link).
2. `PATCH /api/plugins/intent-catalog/nodes/<id>/` — this is the actual write.
3. A post-PATCH GraphQL refetch that must confirm the exact link landed.

If step 3 disagrees with what step 2 just wrote, it raises `LedgerActionError` with code
`node_link_not_confirmed` or `node_link_source_not_confirmed`. At that point **the PATCH in step
2 has already succeeded and the database row is already mutated** — the error is about
confirmation, not about whether a write happened.

`_execute_action()` catches this and builds:

```python
result = ActionResult(
    action_id=action.id,
    reconciler_id=action.reconciler_id,
    action_kind=action.action_kind,
    target_slugs=target_slugs,
    success=False,
    error=f"{code}: {exc}",
)
```

`ActionResult.mutated` is not set here, so it defaults to `False` — even though a real write just
happened. Two consumers then read `mutated`/`success` in a way that under-counts this case:

- `_execute_round()`: `had_side_effects = had_side_effects or executed.result.success` (both the
  bootstrap-phase and service-phase loops) — reads `.success`, not `.mutated`.
- `_run_apply()`: `data.progress_made = any(action.success or action.mutated for ... )` — this one
  *does* check `.mutated`, but since `.mutated` was never set `True` for this action, it doesn't
  help.

Net effect: a round whose only action is a `link_actual_node` that PATCHed successfully but
failed confirmation is reported with `had_side_effects=False`. Per the comment at
`_run_apply()` lines 453-463, `had_side_effects` is what decides whether a fresh post-mutation
drift snapshot is fetched before the run reports failure — so this specific failure mode can
report a stale, pre-mutation drift as if it were current, even though the live row was actually
changed.

## Why this wasn't just fixed here

The `mutated` field exists specifically to distinguish "a write happened" from "the action fully
succeeded" — precedent: `reconcile_ipam`'s `ipam_policy p6 Step 4` decision, which sets
`mutated=bool(ipam_result.applied_endpoint_ids)` independent of `success` for exactly this reason
(a partially-applied IPAM Job run still mutated some rows even though the action as a whole
isn't `success`). The same reasoning applies to `link_actual_node`'s post-PATCH confirmation
failure — but fixing it means either:

- setting `mutated=True` in `_execute_action`'s except branch specifically for
  `node_link_not_confirmed`/`node_link_source_not_confirmed`, and/or
- changing `_execute_round`'s `had_side_effects` checks from `.success` to `.mutated`.

The second change is not local to `link_actual_node` — it would also change behavior for every
other reconciler's failed-but-partially-mutated case (e.g. `reconcile_ipam`, where
`had_side_effects` today is likewise driven by `.success` only, so a partial IPAM apply that
overall fails also doesn't currently trigger a post-failure drift refresh by itself). That is a
behavioral change to `reconcile`'s convergence/progress semantics across multiple reconcilers, not
a test-coverage gap, and outside Interface Contract Phase 4 Step 1's authorized scope (source/
test/documentation repair only, per `plan.md` Section 3.4). It also was not part of Interface
Contract Phase 3's original scope at all — `link_actual_node`/`reconcile_ipam` execution belongs
to the separate `ipam_policy`/reconcile-executor line of work, not to the nintent UI/API/GraphQL
contraction this Phase 4 plan governs.

## Current state

- Not fixed. No production code changed.
- Test coverage added instead:
  `nctl/tests/test_reconcile_executor.py::test_link_actual_node_confirmation_failure_after_successful_patch_is_recorded_not_dropped`
  proves the failed `ActionResult` (with its error code) survives in `RoundSummary.actions` and
  does not terminate the round — i.e. the record itself is not silently dropped, only its
  `mutated`/`had_side_effects` accounting undercounts it.
- `mutated=False` on `ActionResult` for this exact failure path is asserted implicitly (the test
  does not assert on `mutated`, but the fixture's monkeypatched `execute_link_actual_node` raises
  before returning a result, so the code path exercised is exactly the one described above).

## Decision needed

1. Fix `link_actual_node`'s post-PATCH-confirmation-failure `ActionResult.mutated`, leaving
   `had_side_effects`'s `.success`-only check as-is elsewhere (narrowest fix, but
   `had_side_effects` still won't pick it up since it also reads `.success`).
2. Fix both: set `mutated=True` for this failure code *and* change `had_side_effects` to read
   `.mutated` — but audit every other reconciler's failure path (at minimum `reconcile_ipam`) for
   the same gap before changing shared round logic.
3. Leave as-is and treat a post-PATCH confirmation failure as an operational anomaly serious
   enough that a stale drift snapshot on report is an acceptable, rare cost (current behavior).
4. Something else — e.g. surface a distinct terminal/manual-review state for "write succeeded,
   confirmation failed" instead of folding it into ordinary action failure.

This is a separate decision from Interface Contract Phase 4's own step sequence and does not
block Step 2.
