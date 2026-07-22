# Report — Step 2: generation-exact SSH targets and durable round evidence

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: `test_production_composer.py` + `test_ssh_preflight.py` +
`test_reconcile_executor.py` + `test_dnsmasq_apply.py` + `test_compatibility_snapshots.py` +
`test_serve_operations.py` + `test_serve_runner.py`: 300 pass / full suite: 890 pass)

## Goal (plan.md Step 2)

Replace the split `resolve_production_routes(SourceSnapshot) +
verify_offered_keys(old_snapshot, route_overrides=...)` production API with one
immutable, single-generation `ResolvedSshTarget` built during production
composition itself, so a post-regeneration scan can never combine a fresh
route with a stale port/identity. Stop discarding a round's already-succeeded
action evidence when a later step in that same round fails, and fix the
post-actuation observation target bug (service slug instead of host slugs).

## Changes

### 1. `nctl_core/production/composer.py`
- Added `ResolvedSshTarget` (`slug`, `desired_node_id`, `alias`, `route`,
  `port`, `generation_id`) and a `ProductionComposition.ssh_targets: dict[str,
  ResolvedSshTarget]` field.
- `NodeOutcome` gained `resolved_route`/`resolved_port`; `_compose_host` now
  returns `(host_vars, host_os, route)` -- the `ansible_host` it resolves and
  pops before returning is captured, not discarded.
- After the eligible-node loop, one `ResolvedSshTarget` is built per node
  actually present in `ssh_hosts` (never a skipped/out-of-scope node), using
  `derive_host_key_alias(node.id)`, the captured route, `effective.
  ansible_port.value or 22`, and this composition's own `generation_id`.
  Empty when `ssh_known_hosts_file` is `None` (the drift comparator's
  internal, never-rendered composition).

### 2. `nctl_core/production_render.py`
- `ProductionRenderContext` gained `ssh_targets: dict[str, ResolvedSshTarget]
  = field(default_factory=dict)`, populated from `composition.ssh_targets` on
  a successful `build_production_render_context` call (empty on every failure
  path, matching `envelope.ok is False`).

### 3. `nctl_core/reconcile/ssh_preflight.py`
- Removed `RouteOverrides` and `resolve_production_routes` entirely.
- `verify_offered_keys` is now bootstrap-only (no `route_overrides`
  parameter): always the mDNS endpoint, exactly what bootstrap ever needed.
- Added `verify_resolved_ssh_targets(cfg, host_slugs, ssh_targets, probe,
  round_index=...)`: the one production-mode scan, reading only from a
  `ResolvedSshTarget` map. A slug missing from the map is
  `no_resolvable_production_target` -- never mDNS, never any other
  fallback.
- Added `action_host_slugs(action)`, extracted from `ssh_required_host_slugs`'s
  per-action host-list logic so the executor's post-actuation observation
  step (item 8) can share the exact same `host_slugs`-vs-target-loop rule.
- `SshPreflightEntry` gained `phase`, `round`, `route`, `port`,
  `generation_id`, `managed_fingerprints`, `offered_fingerprints` (contract
  item 7's richer public preflight record). `verify_resolved_ssh_targets`
  populates all of them (SHA-256 fingerprints only, never raw key blobs);
  other call sites leave them at their defaults.

### 4. `nctl_core/reconcile/executor.py`
- `RECONCILE_SCHEMA` bumped `nctl.reconcile.v1` -> `nctl.reconcile.v2`
  (contract item 7's schema bump, since `SshPreflightEntry` gained fields
  and `RoundSummary` gained `ssh_preflight`).
- Added `RoundOutcome` (`summary`, `terminal_errors`, `had_side_effects`).
  `_execute_round` now *always* returns one instead of raising
  `_Interrupted`/`_SshPostRegenScanFailed` for interruption, an unavailable
  production regeneration, a post-regen SSH scan failure, or a
  `SshStoreReadError` -- every one of those still returns whatever actions
  already ran in `summary`. `_run_apply` appends `outcome.summary` to
  `data.rounds` unconditionally, then checks `terminal_errors`.
- If a failed round's outcome has `had_side_effects=True`, `_run_apply` now
  performs one extra `fetch_and_compute_drift(cfg)` call and uses *that* as
  the final drift, instead of the pre-mutation drift fetched at the top of
  the same (failed) round. If the refresh itself fails, `final_drift_path`
  is left unset and a `final_drift_unknown` error is appended -- the
  pre-mutation drift is never mislabeled as final.
- `data.progress_made` is now `any(action.success for round in data.rounds
  for action in round.actions)` -- not `bool(data.rounds)` (a round with zero
  successful actions, e.g. a pre-mutation store-read failure, no longer
  counts as progress).
- The post-regeneration scan calls `verify_resolved_ssh_targets(cfg,
  service_scan_targets, render_context.ssh_targets, ssh_probe,
  round_index=round_index)` instead of `resolve_production_routes(...) +
  verify_offered_keys(..., route_overrides=RouteOverrides(routes))`. Its
  result is stored on `RoundSummary.ssh_preflight` (route/port/generation/
  fingerprints, no raw blobs) as well as feeding `_ssh_scan_errors`.
- `_ssh_scan_errors` unchanged from Step 1 (still maps `STATUS_UNENROLLED`
  too -- now exercised by the production scan as well as the bootstrap one).
- Post-actuation observation host derivation now uses `action_host_slugs(action)`
  instead of `target.slug for target in action.targets` -- fixes the bug
  where a `service_profile`/`dnsmasq_config` action's observation ran (or
  silently no-opped) against the *service* slug instead of the node host
  list.
- `RoundSummary` gained `ssh_preflight: list[dict] = Field(default_factory=list)`.

## Test changes

- `tests/test_production_composer.py`: 3 new tests -- `ssh_targets` populated
  for every included node with the right alias/route/generation; a node
  skipped by a `NODE_LOCAL_CODES` local composition error never gets a
  target while a sibling included node still does; `ssh_targets` is empty
  when no `ssh_known_hosts_file` is supplied.
- `tests/test_ssh_preflight.py`: removed the `RouteOverrides`/
  `resolve_production_routes` tests; added `verify_resolved_ssh_targets`
  tests -- scans the target's own route/port/generation (not the
  round-start snapshot's), old-port-vs-new-generation-port, missing-from-map
  rejection, partial-map does not leak to another target's route, unenrolled,
  mismatch. `verify_offered_keys` kept its two bootstrap-mode tests
  (mDNS route, unreachable detail), updated for the dropped parameter.
- `tests/test_reconcile_executor.py`:
  - `_patch_production_render`'s stub now builds a real `ssh_targets` map via
    the same pure `resolve_effective_route`/`try_resolve_operational_values`
    pipeline the composer uses (previously relied on the removed
    `resolve_production_routes`).
  - `test_service_phase_blocks_on_mismatched_key_after_production_regen` and
    `test_production_write_failure_starts_no_service_ansible_process`
    updated from `rounds == []` to asserting the round is retained with the
    regeneration action and its success value (item 6); the mismatch case
    also asserts `progress_made is True` and a fresh `final_drift_path`
    (item 7).
  - `test_apply_blocks_on_unenrolled_ssh_host_before_any_action_executes` /
    `test_ssh_preflight_summary_is_populated_on_success` (dnsmasq_apply)
    updated for `SshPreflightEntry`'s new default fields.
  - `test_service_phase_scans_freshly_regenerated_route_not_round_start_snapshot`
    updated: post-actuation observation now genuinely runs against `["agweb"]`
    (previously silently misrouted to `["good-svc"]`), so `playbook_run_calls`
    is 3, not 1; also asserts the round's `ssh_preflight` entry has the right
    route/generation/fingerprints and no raw key blob substring.
  - New `test_interruption_mid_round_retains_actions_completed_before_it`:
    two independent service actions, interrupted after the first's playbook
    runs -- the round is retained with the successful regeneration and the
    one completed service action.
  - New unit tests: `test_ssh_scan_errors_maps_unenrolled_status_too`,
    `test_apply_reports_ssh_store_read_failed_when_managed_store_is_corrupt`
    (both already added in Step 1, unaffected here).
- `tests/test_compatibility_snapshots.py`, `tests/test_serve_operations.py`,
  `tests/test_serve_runner.py`: schema key bumped to `nctl.reconcile.v2`.
- `src/nctl_core/cli/main.py`: `--json` help text updated to `nctl.reconcile.v2`.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_production_composer.py nctl/tests/test_ssh_preflight.py \
    nctl/tests/test_reconcile_executor.py nctl/tests/test_dnsmasq_apply.py \
    nctl/tests/test_compatibility_snapshots.py nctl/tests/test_serve_operations.py nctl/tests/test_serve_runner.py
300 passed

$ uv run --project nctl pytest -q nctl/tests
890 passed, 1 warning in 5.85s
```

Lint/type check: not run (same reason as Step 1 -- no ruff/mypy dependency in
this project).

## Step 2 exit criteria

- [x] No production scan reads route, port, or identity from the round-start
  snapshot (`verify_resolved_ssh_targets` reads only `ResolvedSshTarget`
  from `render_context.ssh_targets`; `resolve_production_routes`/
  `RouteOverrides` no longer exist).
- [x] Every started round is represented in output (`RoundOutcome` always
  returned and always appended to `data.rounds`, including interruption,
  regeneration failure, SSH scan failure, and store-read failure).
- [x] Live verification can prove the exact generation/route/port/key
  decision from artifacts alone (`RoundSummary.ssh_preflight` carries
  phase/round/route/port/generation_id/managed_fingerprints/
  offered_fingerprints; no raw key blobs anywhere in the record).

## Handoff to Step 3

- Step 3 (deterministic dnsmasq bytes) is independent of this step's SSH
  changes; it touches `dnsmasq.py`/`dnsmasq_render.py`/`dnsmasq_apply.py`.
  `dnsmasq_apply.py`'s SSH preflight path (Step 1's inventory-trust
  contract) is unaffected by Step 2 -- it never used
  `resolve_production_routes`/`RouteOverrides` (it always used its own
  `inventory_trust.check_inventory_ssh_preflight`, unrelated to
  `ResolvedSshTarget`).
- Step 5 (dnsmasq content drift) will need `RoundSummary.ssh_preflight`
  and `ReconcileData.ssh_preflight` to stay populated exactly as they are
  now when a `dnsmasq_config` action is added to `service_scan_targets` --
  no further executor change should be needed there, since
  `SSH_REQUIRING_RECONCILER_IDS` already includes `dnsmasq_config`.
