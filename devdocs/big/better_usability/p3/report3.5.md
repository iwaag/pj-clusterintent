# Phase 3 Step 3.5 — Drift/reconcile isolation after lifecycle changes

Parent: [plan.md](plan.md), Step 3.5.

## Relationship to existing coverage

`test_production_composer.py` (Phase 1/2) already extensively proves the general "one bad node
never aborts a healthy neighbor" guarantee (`test_endpoint_failure_neighbor_does_not_change_healthy_output`,
`test_group_c_failure_skips_only_the_bad_node`, `test_active_placement_on_ineligible_lifecycle_emits_finding`)
and is unaffected by this phase's nintent-side default change, since `nctl` only consumes whatever
lifecycle value a node's `DesiredSnapshot` row carries. Step 3.5 adds the specific transition
framing the plan asks for — the same node/placement data evaluated before, during, and after a
lifecycle change — plus reconcile-planner isolation and the command-scoping guarantee, in a new
`tests/test_phase3_lifecycle_transition.py` (7 tests).

## Transition sequence (`comparators.production_policy`)

Same node (`agdnsmasq`) and active placement, lifecycle flipped twice:

1. `planned` → `active_placement_not_applied` present (baseline, matches the live
   `p3/report3.1.md` finding).
2. `active` → the warning disappears — lifecycle was its sole blocker.
3. `planned` again → the warning reappears with the same evidence shape. This proves the finding
   tracks live lifecycle state exactly, with no memoization or one-way suppression.

## Mixed active-good/active-bad reconcile isolation

Two `active` nodes: `aghealthy` (has a matching `ActualDevice`, diff `actual_node_not_linked` →
automatable `link_actual_node`) and `agbad` (diff `missing_interface_candidate` → manual review,
not automatable).

- **Cluster-scoped plan**: `plan.actions == [link_actual_node for aghealthy]`,
  `plan.manual_review == [agbad]`, `plan.unsupported == []`. The locally blocked node is pruned to
  manual review; it neither blocks nor appears in the actuated action list.
- **Host-scoped plan** (`--host aghealthy`): identical action list, empty manual review — confirms
  `select_scoped_diffs` correctly excludes the unrelated blocked neighbor from a single-host dry
  plan, not just the cluster-wide one.

## Command-scoping guarantee (plan.md Decision 3)

- `{"invalid_lifecycle", "unknown_node", "lifecycle_update_rejected",
  "lifecycle_confirmation_mismatch"}.isdisjoint(CODE_CLASSIFICATION.keys())` — none of the four
  lifecycle command errors is a registered reconcile diff code.
- Structural guard: `nctl_core.lifecycle` exposes neither `CODE_CLASSIFICATION` nor
  `run_comparators` — it has no dependency on the drift registry or reconcile classifier, so it
  cannot accidentally grow into one over time.

## Result

Full nctl suite: **607 passed** (600 baseline + 7 new), no regressions. The five items materially
new to this step (before/after/round-trip transition, cluster and host-scoped isolation, and the
command-scoping guard) are proven directly; the general isolation guarantee they build on remains
covered by the existing Phase 1/2 suite, which was re-run unchanged.
