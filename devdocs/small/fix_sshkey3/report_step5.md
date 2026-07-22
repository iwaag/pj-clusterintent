# Report — Step 5: add dnsmasq content drift and automatic reconciliation

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 13 new/touched test files, 61 tests / full suite: 913 pass)

## Goal (plan.md Step 5)

Make process state (daemon running) and managed-content state (deployed
records-file digest) two independently-represented `nctl drift` dimensions
for `dnsmasq_config`-profiled services, resolve content drift to the
existing `dnsmasq_config` reconciler (no second planner), and require a
post-actuation observation so a deploy proves convergence before the next
round's drift check.

## Changes

### 1. `nctl_core/drift/service_placement.py`
- Added `ContentSpec` (`managed_file_key`, `desired_digest`) and
  `_evaluate_content_drift`: independent of the existing process-state gap
  logic in the same function, appending to the same placement report's
  `gaps` list. Codes: `service_config_observation_missing` (no managed-file
  result at all -- distinct from `service_missing`, which means the
  *process* wasn't observed running), `service_config_missing` (nodeutils
  explicitly reported `status: missing`), `service_config_unreadable`
  (`status: unreadable` or `too_large`), `service_config_mismatch`
  (`status: present` but `sha256` differs from desired).
- `evaluate_active_placement`/`evaluate_placement_drift` gained an optional
  `content_spec`/`content_spec_by_service_id` parameter (default `None` ->
  zero behavior change for every non-dnsmasq service).

### 2. `nctl_core/drift/evaluation_snapshot.py`
- `evaluate_all_services` gained `profile_reconciliation: dict[str,
  ProfileReconciliation] | None`. New `_content_spec_by_service_id` builds
  one `ContentSpec` per service with an active placement on a
  `managed_files`-declaring profile, computing the desired digest via
  `dnsmasq_render.compute_dnsmasq_render(snapshot).content_sha256` lazily
  (at most once per drift run, only if at least one placement needs it) --
  imported locally inside the helper to break an import cycle
  (`dnsmasq_query.py` -> `evaluation_snapshot.py` -> `dnsmasq_render.py` ->
  `dnsmasq_query.py`).
- `_observed_evidence` now also surfaces `desired_content_digest`/
  `observed_content_digest`/`observed_content_status` when present, so
  `nctl drift --json` shows the exact digests being compared -- never file
  content, only the metadata nodeutils reported.
- The per-placement gap-to-diff severity mapping treats
  `service_config_observation_missing` as `"unknown"` (matching
  `service_observation_missing`'s existing OBSERVATION severity), every
  other new code as `"missing"` (matching the existing AUTOMATIC default).

### 3. `nctl_core/drift/context.py`
- `DriftContext` gained `profile_reconciliation: dict[str,
  ProfileReconciliation]` and `profile_reconciliation_error: str | None`
  (contract item 1).

### 4. `nctl_core/drift_render.py`
- `fetch_and_compute_drift` now also loads `load_profile_reconciliation`
  (only after `load_deployment_profiles` succeeds -- reconciliation is
  validated against that exact profile-name set) and threads both the
  result and any `ProfileReconciliationError` into `DriftContext`.

### 5. `nctl_core/drift/comparators.py`
- `service_intent_matching` now yields one `kind="global"`
  `deployment_profile_reconciliation_unavailable` ERROR diff when
  `context.profile_reconciliation_error` is set, and passes
  `profile_reconciliation=None` to `evaluate_all_services` in that case --
  no content-drift code is ever emitted without real metadata behind it,
  and the global diff alone already blocks every scope (Decision 1), so an
  unavailable contract can never read as silent convergence.

### 6. `nctl_core/reconcile/classify.py`
- `service_config_observation_missing` added to `_OBSERVATION_CODES`
  (routes to `observe_node`, matching `service_observation_missing`).
- `service_config_missing`/`service_config_unreadable`/
  `service_config_mismatch` added to `_SERVICE_PROFILE_CODES` (routes to
  `service_profile`, exactly like `service_missing`/`service_not_running`
  already do). `plan_service_profile` (`reconcilers.py`, unchanged) already
  resolves any `service_profile`-classified code group to the
  `dnsmasq_config` reconciler generically whenever the target service's
  deployment profile declares `action.kind == "dnsmasq_config"` -- no
  second, dnsmasq-only planner was needed, exactly as the plan requires.
- `deployment_profile_reconciliation_unavailable` needs no table entry:
  it's always `target.kind == "global"`, and `classify()` already
  special-cases every global diff as `MANUAL_REVIEW` regardless of code.

### 7. `nctl_core/reconcile/reconcilers.py`
- `DNSMASQ_CONFIG`'s `requires_observation` flipped `False` -> `True`: a
  dnsmasq deploy now always triggers the post-actuation nodeutils
  collection/ingest (already correctly host-slug-scoped since Step 2's
  `action_host_slugs` fix), so the next round's drift compares against the
  freshly observed digest instead of stale evidence.

## Test changes

- `tests/test_service_placement.py`: 8 new tests -- running+matching digest
  converges; changed digest is `service_config_mismatch`; process and
  content dimensions are independently evaluated (stopped+matching-digest
  is process-only drift; running+changed-digest is content-only drift);
  missing managed-file observation is distinct from a missing service;
  explicit `missing` status; `unreadable`/`too_large` both map to
  `service_config_unreadable`; two placements give one converged + one
  mismatched result independently; no `content_spec` means zero content
  codes ever appear (existing non-dnsmasq services unaffected).
- `tests/test_drift_evaluation_snapshot.py`: 3 new tests -- content drift
  wired through `evaluate_all_services` against the *real*
  `compute_dnsmasq_render` digest (not a hand-picked test constant);
  mismatch surfaces in `gap_codes`; `profile_reconciliation=None` never
  produces a content code (contract item 1's "no metadata, no invented
  drift" half).
- `tests/test_drift_comparators.py`: 1 new test -- an unavailable
  `profile_reconciliation_error` produces exactly one global
  `deployment_profile_reconciliation_unavailable` ERROR diff.
- `tests/test_reconcile_classify.py`: unchanged, but its existing
  source-scanning `test_every_producible_diff_code_is_classified` already
  auto-validates every new literal code above is classified (no separate
  edit needed there).
- `tests/test_reconcile_planner.py`: `test_service_profile_dnsmasq_config_action`
  updated: `requires_observation` is now `True`, not `False`.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_service_placement.py nctl/tests/test_drift_evaluation_snapshot.py \
    nctl/tests/test_drift_comparators.py nctl/tests/test_reconcile_classify.py nctl/tests/test_reconcile_planner.py
61 passed

$ uv run --project nctl pytest -q nctl/tests
913 passed, 1 warning in 5.58s
```

Lint/type check: not run (no ruff/mypy dependency, consistent with every
prior step).

## Step 5 exit criteria

- [x] Changing a generated DNS/DHCP directive necessarily changes `nctl
  drift`: `compute_dnsmasq_render`'s digest (Step 3) changes whenever the
  rendered conf changes, and the content-drift check compares it against
  the nodeutils-observed digest independent of process state.
- [x] `nctl reconcile --yes` deploys it and proves the observed digest
  before declaring convergence: `dnsmasq_config` actions now require
  post-actuation observation, so the next round's drift recomputation is
  against fresh evidence, not the pre-deploy state.

## Known gap / deferred to Step 6

I did not write a full multi-round executor integration test simulating
"drift shows mismatch -> apply deploys -> post-actuation observation runs
-> next round's drift shows converged" end-to-end through
`nctl_core.reconcile.executor.run_reconcile` with mocked Ansible/Nautobot
across three rounds. The individual mechanics are each covered elsewhere
(round-loop convergence logic by other reconciler tests, `action_host_slugs`
correctness by Step 2's tests, `dnsmasq_config` planning by
`test_reconcile_planner.py`, content-drift codes by this step's own tests),
but that specific full-pipeline sequence is unverified by an automated
test. Step 6's Live verification B is the authoritative version of exactly
this sequence, run against real `agdnsmasq` -- I judged the marginal value
of a heavy synthetic-fixture integration test lower than getting to that
real verification, given this is nctl-only, no-live-risk work and the live
check is coming regardless. Flagging this explicitly rather than silently
skipping it.

## Handoff to Step 6

- Step 6's live verification requires the full v2 rollout (Step 4's
  nodeutils/nauto push + Job redeploy, still pending) to be live before
  `nctl reconcile agdnsmasq` can produce a real `service_config_mismatch`
  diff against the actual host.
- `nctl drift --json` on a dnsmasq placement now exposes
  `desired_content_digest`/`observed_content_digest`/
  `observed_content_status` in the diff's `actual.actual` evidence --
  Step 6's live verification should cite these fields directly as proof,
  not just the diff code.
