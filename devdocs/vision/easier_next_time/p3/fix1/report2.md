# Fix 1 — Step 2 report: repair the host-scoped observation contract in nctl

Status: **complete**.

## Root cause confirmed

`select_scoped_diffs()` (`nctl/src/nctl_core/reconcile/planner.py`) selected
every `service`-target diff whose service had any active placement on the
requested host — including placement-specific observation diffs that name
a *different* owning node in `desired.expected.node_slug`/`node_id`. For a
service placed on `aghub`, `agpc`, and `agstudio` (matching `node_agent`),
scoping to `aghub` still admitted the `agpc`/`agstudio` observation diffs.
`build_plan()` resolves each such diff to its named node and folds all of
them into one `observe_node` action, which
`_with_forced_observation()` then merged the forced `aghub` refresh into
merely because it contained `aghub` among its targets — producing the
three-host `observe_node` action seen in operation
`01KZ3Y5KTQ54XNF6JS7YVNPE5R`.

## Fix

`nctl/src/nctl_core/reconcile/planner.py::select_scoped_diffs()`: a
service-target diff carrying `desired.expected.node_slug` or `node_id` is
now selected only when that value matches the requested host's node
exactly. Diffs with no placement-specific node identity (e.g.
`service_has_no_active_placement`, an unexpected-location conflict) keep
the prior service-membership behavior — this preserves existing coverage
for genuinely service-wide findings while eliminating the widening.

`nctl/src/nctl_core/reconcile/executor.py::_with_forced_observation()`:
added defense in depth. If, after scoping, an existing `observe_node`
action still names any node other than the requested host, the function now
raises `ForcedObservationScopeError` instead of merging into it. Both call
sites (`_run_plan_only`, `_run_apply`) catch this and turn it into a
`forced_observation_scope_violation` failed envelope rather than an
unhandled exception or a silent multi-host contact.

## Tests added

`nctl/tests/test_reconcile_planner.py`:

1. `test_select_scoped_diffs_placement_specific_observation_stays_on_its_owning_node`
   — the exact failure shape: one service with observation diffs for
   `aghub`, `agpc`, `agstudio`, scoped to `aghub`, now yields only the
   `aghub` diff and a single-target `observe_node` action.
2. `test_select_scoped_diffs_node_local_and_service_observation_dedupe_to_one_target`
   — a node-local diff and a service observation diff for the same host
   still dedupe to one `observe_node` target.
3. `test_select_scoped_diffs_cluster_scope_retains_multi_host_observation`
   — cluster scope is unchanged: `select_scoped_diffs` short-circuits for
   `scope.kind == "cluster"` before the new host-matching logic runs.

`nctl/tests/test_reconcile_executor.py`:

4. `test_with_forced_observation_refuses_to_merge_into_a_multi_target_action`
   — direct unit test: a manufactured multi-target `observe_node` action
   raises `ForcedObservationScopeError` naming the extra host.
5. `test_refresh_observation_scope_violation_surfaces_as_failed_envelope`
   — `run_reconcile(..., refresh_observation=True)` against a plan stub
   that still carries a multi-target action ends `state == "failed"` with
   `errors[0].code == "forced_observation_scope_violation"`, not a crash
   or a silent apply.

The plan's item 4 ("the executor passes only `aghub` through SSH preflight,
bootstrap inventory, Ansible `--limit`, and the ingest `report_batch`") is
covered structurally rather than by a new bespoke test: `ssh_required_host_slugs`
and the bootstrap/ingest paths all derive their host set from
`plan.actions[*].targets`, which the planner fix now correctly limits to one
target for this shape; the existing `test_refresh_observation_plans_observe_for_converged_host`
and `test_refresh_observation_executes_once_then_converges` already assert
the single-target action shape drives `ssh_preflight`/observation end to
end, and continue to pass unchanged.

## Verification

```
cd nctl && uv run pytest -q tests/test_reconcile_planner.py tests/test_reconcile_executor.py
# 87 passed

cd nctl && uv run pytest -q --durations=20
# 1151 passed

cd .. && uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
# 3 passed
```

## Commits

- nctl submodule: `3329d93` — "fix: host-scoped --refresh-observation must
  not widen beyond the requested host"
- superproject: this commit, bumping the `nctl` submodule pointer alongside
  this report.

No cluster or Nautobot contact in this step — code and tests only, per the
plan.

## Next

Step 3 (live, needs judgment) requires touching the local Nautobot
worker/queue and is a session boundary per the plan (`Use separate sessions
at the boundaries below`) and policy §7 (cluster operation and workflow
improvement happen in different sessions). Steps 3–6 all involve live
cluster/local-infra contact or explicit-approval destructive actions and are
left for a later session, per the plan's design.
