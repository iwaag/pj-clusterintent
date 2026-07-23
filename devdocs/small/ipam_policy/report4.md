# Step 4 — Pin Endpoint Coverage Through Planning and Execution

## Changes

`nctl/src/nctl_core/reconcile/reconcilers.py`:

- `plan_reconcile_ipam(target, diffs)` now takes the `reconcile_ipam`-classified
  `DiffRecord`s for the target instead of a bare code list. Since only an
  eligible create/link gap is ever classified `AUTOMATIC` for this reconciler
  (Step 3 routes an unsatisfied-observation gap to `manual_review` instead),
  every diff here already carries `endpoint_id`/`endpoint_name`/`ip_policy`/
  `ip_address` in `diff.desired["expected"]`. The action now pins
  `eligible_endpoint_ids` (sorted) plus a fuller `eligible_endpoints` list
  (with each entry's `gap_code`) in both `evidence` and `parameters`.

`nctl/src/nctl_core/reconcile/planner.py`:

- Updated the one call site to pass `group_diffs` instead of `codes`.

`nctl/src/nctl_core/reconcile/ledger.py`:

- `execute_reconcile_ipam` reads `action.evidence["eligible_endpoint_ids"]`
  and verifies, before returning:
  - every pinned id has a matching `plans[].desired_endpoint.id` row
    (`ipam_summary_coverage_mismatch` if not — "every eligible endpoint id
    pinned by the planner appears in the plan rows");
  - `summary.summary.endpoints` agrees with the plan-row count (same error
    code);
  - zero plan rows when nothing was pinned is also
    `ipam_summary_coverage_mismatch` (the empty-Job-artifact case).
  `IpamReconcileResult` gained `eligible_endpoint_ids`, `applied_endpoint_ids`
  (pinned endpoints that reached `create_ip_address_applied`/
  `link_ip_address_applied`/`noop`), and `unresolved_expected_endpoints`
  (pinned endpoints that did not) — computed only over the pinned set, so an
  extra, not-yet-eligible endpoint on the same node skipping for its own
  reason (a different, unpinned id) never counts against this action.

`nctl/src/nctl_core/reconcile/executor.py`:

- `ActionResult` gained `mutated: bool`, independent of `success`, so a
  partially-applied action's real mutation isn't erased by a sibling failure.
  `progress_made` is now `any(success or mutated ...)` instead of
  `any(success ...)`.
  - The `reconcile_ipam` branch now sets `success = not
    unresolved_expected_endpoints` (a conflict/skip on a *pinned* endpoint
    fails the action even though the Job process itself returned normally —
    "a successful JobResult alone must not make the ActionResult successful")
    and `mutated = bool(applied_endpoint_ids)` (an applied endpoint still
    counts as progress even if a sibling on the same node conflicts).
    `detail` carries `conflicts`/`skipped`/`eligible_endpoint_ids`/
    `applied_endpoint_ids`/`unresolved_expected_endpoints` for evidence.
  - A round-level failed-but-mutated `reconcile_ipam` action does not itself
    abort the round early (matching the existing `link_actual_node`
    exception-handling precedent: independent actions on healthy targets
    still run); the next round's fresh drift/fingerprint comparison is what
    ultimately surfaces "no progress" (`non_converged`) if the same conflict
    persists, rather than the executor inventing a bespoke mid-round abort
    path for this one reconciler.

## Test changes

- `tests/test_reconcile_planner.py`: `test_reconcile_ipam_action_pins_exact_eligible_endpoint_ids`
  and `test_reconcile_ipam_never_pins_a_manual_review_only_endpoint` (a
  manual-review-classified sibling endpoint on the same node is never pinned).
- `tests/test_reconcile_ledger.py`: `test_reconcile_ipam_rejects_missing_pinned_endpoint_id`,
  `test_reconcile_ipam_rejects_endpoint_count_mismatch`,
  `test_reconcile_ipam_rejects_zero_endpoint_artifact_when_none_pinned`,
  `test_reconcile_ipam_separates_applied_from_unresolved_pinned_endpoints`,
  `test_reconcile_ipam_unpinned_extra_endpoint_skip_does_not_count_as_unresolved`.
- `tests/test_reconcile_executor.py`: `test_reconcile_ipam_partial_conflict_is_not_reported_as_success`
  and `test_reconcile_ipam_fully_applied_is_success_and_mutated` (direct
  `_execute_round` calls, `execute_reconcile_ipam` mocked at the ledger
  boundary, mirroring the existing `_direct_round_setup` pattern).
- **Real multi-round test** (plan.md's "Real Multi-round Test" scenario):
  `test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint` mocks only
  the Nautobot snapshot fetch (`nctl_core.drift_render.build_source_snapshot`)
  and the Job execution boundary (`ledger.execute_reconcile_ipam`, since
  running the real Django Job is out of reach for a unit test), and lets the
  real drift engine (`evaluate_endpoint_intent`'s eligibility gate),
  `classify()`, the planner's endpoint-id pinning, and the executor's
  coverage-aware success/mutated computation all run unmodified:
  - Round 0: a `static` endpoint with explicit `192.0.2.10` and a matching
    `ActualDevice.primary_ip_address` observation, no `IPAddress` yet ->
    `missing_actual_ip_address` -> `reconcile_ipam` pins exactly `["ep-1"]` ->
    the (mocked) Job applies it -> action `success=True`, `mutated=True`.
  - Round 1: a fresh Nautobot fetch reporting the `IPAddress` and
    `realized_ip_address` link now in place -> no `missing_actual_ip_address`
    -> `reconcile_ipam` is not planned again -> `already_converged`, zero
    rounds.

## Verification

```
$ uv run pytest tests/ -q
984 passed
```

No pre-existing test needed behavioral changes beyond the `plan_reconcile_ipam`
signature change (no external callers besides `planner.py`).

## Notes / scope boundary

- "Observation changing between drift and Job execution" (one of plan.md's
  required negative scenarios) is exercised at the nintent layer by Step 2's
  write-time recheck (`plan_endpoint_ipam_reconcile` is called again inside
  the Job immediately before any write, using observations read fresh from
  Nautobot at that moment) rather than by a dedicated nctl-side test — nctl's
  planner/executor only ever see the Job's *result* artifact, not its
  intermediate state, so this scenario's proof point is Django-side and
  belongs in the Nautobot-backed verification phase, not the local suite.
- The `ipam_reconcile_observation_ambiguous` basis remains structurally
  unreachable from real data today (`ActualVirtualMachine` carries no custom
  fields under the current actual-source schema, so only one observation
  source, the realized Device, can ever contribute a candidate) — same
  documented limitation as `evaluation.py`'s existing VM-scoring note. It is
  still implemented and classified for when a future schema adds VM facts.

## Status

Step 4 complete at the code level, including the plan's required real
multi-round test. Step 5 (documentation) and the Nautobot-backed/live
verification phases remain. Not yet deployed.
