# Report — Step 2: make observation-time store failures round-safe

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 4 new pass / full suite: 933 pass)

## Goal (plan.md Step 2)

Close outstanding problem #2: `run_observation` performs its own
defense-in-depth `check_ssh_enrollment` call, which can raise
`SshStoreReadError`. `_run_observation_action` previously caught only
`ValueError`, so that exception could escape the action boundary — in a
post-actuation observation this could happen after a successful dnsmasq
deployment, defeating `RoundOutcome`'s evidence-retention guarantee (the
whole round, including the just-succeeded deployment, would be lost to an
unhandled exception propagating out of `run_reconcile`).

## Changes

### `nctl_core/reconcile/executor.py`

- Added `ExecutedAction` (`result: ActionResult`, `terminal_errors:
  list[EnvelopeError]`) — the private action-execution outcome the
  corrected contract calls for, so a store failure's control flow is a
  typed field, not an error-message string.
- `_execute_action` now returns `ExecutedAction` instead of `ActionResult`
  for every branch (`observe_node`, `link_actual_node`, `reconcile_ipam`,
  `service_profile`/`dnsmasq_config`, and the `LedgerActionError`/
  `NautobotJobError`/`NautobotError` catch-all) — every non-observation
  branch sets `terminal_errors=[]`.
- `_run_observation_action` now returns `ExecutedAction` and distinguishes
  two exception classes from `run_observation`:
  - `ValueError` (e.g. `ssh_host_key_unenrolled`, `no target hosts`):
    unchanged behavior — a failed `ActionResult` with no `terminal_errors`,
    so the round continues past this one action, exactly as before.
  - `SshStoreReadError` (new): a failed `ActionResult`
    (`error="ssh_store_read_failed: ..."`) *and*
    `terminal_errors=[EnvelopeError(code="ssh_store_read_failed", ...)]`.
- `_execute_round`'s bootstrap-action loop, service-action loop, and the
  post-actuation observation call site (previously all discarding
  `ActionResult` directly) now unpack `ExecutedAction`: the `result` is
  always appended to `summary.actions` (and folded into `had_side_effects`)
  *before* `terminal_errors` is inspected; a non-empty `terminal_errors`
  returns a `RoundOutcome` immediately with that round's `summary` intact.

No change was needed in `observation.py`: `run_observation`'s own
`check_ssh_enrollment` call already raised `SshStoreReadError` uncaught
(now via `load_managed_ssh_store`, since Step 1) — the fix is entirely at
the `_run_observation_action`/`_execute_round` boundary that receives it.

## Test changes (`tests/test_reconcile_executor.py`)

- `test_successful_ledger_action_retained_when_observation_store_fails`:
  calls `_execute_round` directly with a two-action bootstrap plan
  (`link_actual_node` then `observe_node`); `run_observation` raises
  `SshStoreReadError`. Asserts both `ActionResult`s are in
  `summary.actions` (link succeeded, observe failed with
  `ssh_store_read_failed` in its error), `had_side_effects is True`, and
  `terminal_errors == [ssh_store_read_failed]`.
- `test_post_actuation_observation_store_failure_retains_deployment_evidence`:
  calls `_execute_round` directly with one `dnsmasq_config` action
  (`build_dnsmasq_apply` stubbed to succeed), production regeneration
  stubbed via the existing `_patch_production_render` helper, and
  `run_observation` raising `SshStoreReadError` for the post-actuation
  scan. Asserts `production_inventory` and `dnsmasq_config` both succeeded
  and are retained, the synthesized `observe_node` result is last and
  failed, `had_side_effects is True`, and `terminal_errors ==
  [ssh_store_read_failed]`.
- `test_final_drift_refresh_failure_after_store_failure_reports_unknown`:
  full `run_reconcile`, with `_execute_round` itself stubbed to a crafted
  `RoundOutcome` (one successful `link_actual_node` result,
  `terminal_errors=[ssh_store_read_failed]`, `had_side_effects=True`) and
  the second `fetch_and_compute_drift` call (the post-failure final-drift
  refresh) returning an `EnvelopeError`. Asserts the run reports both
  `ssh_store_read_failed` and `final_drift_unknown`, the one round's
  successful action is retained, `progress_made is True`, and
  `final_drift_path == ""`. This exercises `_run_apply`'s existing
  (fix_sshkey3 Step 2) final-drift-refresh logic, which was previously
  unreachable for a store failure specifically because the exception
  escaped before reaching it — confirms it now composes correctly with
  Step 2's fix.
- `test_pre_round_store_failure_still_starts_no_round`: full
  `run_reconcile` with a corrupt (invalid-UTF-8) store and an
  observation-requiring diff; asserts `ssh_store_read_failed`, zero
  rounds, and `progress_made is False` — the pre-round gate (unchanged by
  this step) still fails closed before any round starts, distinct from the
  new mid-round/post-actuation cases above.

## Verification

```
$ uv run pytest -q tests/test_reconcile_executor.py -k \
    "store_fail or observation_store or ledger_action_retained or pre_round_store or final_drift_refresh_failure"
4 passed in ...s

$ uv run pytest -q tests
933 passed, 1 warning in 5.80s   # full suite (Step 1 baseline 929 + 4 new)
```

Lint/type check: still none configured in `nctl/pyproject.toml`'s
`[dependency-groups] dev` (unchanged from every prior step).

## Step 2 exit criteria

- [x] Every started round is represented after every managed-store
  failure point — bootstrap and post-actuation observation both now
  return `ExecutedAction`/`RoundOutcome` instead of letting
  `SshStoreReadError` escape `_execute_round`; every already-appended
  `ActionResult` (including a successful mutation) survives into
  `data.rounds`.
- [x] No successful mutation disappears because observation re-read the
  store — proved directly for both the bootstrap-phase (ledger action)
  and service-phase (dnsmasq deployment) cases, and the existing
  final-drift-refresh/`final_drift_unknown` logic is proved to compose
  correctly with the newly-reachable store-failure path.
- [x] A pre-round store failure still starts no round and reports no
  progress (regression-checked, unchanged).

## Handoff to Step 3

Outstanding problems #3 and #4 (the dnsmasq destination path duplicated
between `deployment_profile_reconciliation` and
`deploy_dnsmasq_records.yml`, and a scoped dnsmasq action not owning one
exact host set end to end) are unaffected by this step and are Step 3's
scope, spanning `nctl` and `ansible_agdev`.
