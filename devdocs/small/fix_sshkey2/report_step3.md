# Report — Step 3: atomically bind production regeneration to preflight

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 217 pass / full suite: 846 pass)

## Goal (plan.md Step 3)

Fix bug #2: reconcile regenerated the production inventory from fresh data,
but then scanned the post-regeneration SSH route from the snapshot fetched
at the start of the round, so an IPAM/observation update in the same round
could make the installed inventory and the scanned route disagree. Fix
bug #3: `verify_offered_keys()` silently fell back to mDNS whenever a slug
was absent from an explicit production route map, instead of failing
closed. Also stop every service action (not just the SSH scan) when
production regeneration itself fails.

## Changes

### `nctl_core/production_render.py`
- Added `ProductionRenderContext` (frozen dataclass): bundles `envelope`,
  `generation_id`, `generated_at`, and `source_snapshot` -- everything a
  post-regeneration route resolution needs to stay pinned to one generation.
- Added `build_production_render_context(cfg, snapshot)`: the single
  internal API that composes from an *already-fetched* `SourceSnapshot`.
  Both `build_production_render` (normal `nctl render production`, still the
  public entry point CLI/serve call) and the reconcile executor now go
  through this one function, so they can never compose from two different
  snapshots for what is supposed to be one generation.
- `build_production_render(cfg)` is now a thin wrapper: resolve token, fetch
  one `SourceSnapshot`, close the client, delegate to
  `build_production_render_context(cfg, snapshot).envelope`. Behavior for
  existing callers (CLI, serve) is unchanged.

### `nctl_core/reconcile/ssh_preflight.py`
- Added `RouteOverrides` (frozen dataclass wrapping `routes: dict[str, str]`).
  `verify_offered_keys(..., route_overrides: RouteOverrides | None = None)`
  now distinguishes bootstrap mode (`None` -> select the mDNS endpoint) from
  production mode (a `RouteOverrides` instance, even wrapping an empty dict
  -> a missing slug is `no_resolvable_production_route`, never mDNS). The
  previous `dict | None` parameter with `route_overrides = route_overrides or
  {}` could not make this distinction: an explicitly empty map and "no map at
  all" both collapsed to `{}` and silently fell back to mDNS -- exactly
  bug #3. A dedicated wrapper type makes the falsy-empty-dict case
  unambiguous by construction, per the plan's explicit preference for
  "separate route-mode types so falsy values cannot change modes."

### `nctl_core/reconcile/executor.py`
- `_regenerate_production_inventory(cfg)` now returns
  `tuple[ActionResult, ProductionRenderContext | None]` instead of just
  `ActionResult`. It fetches its own fresh `SourceSnapshot` (as before, via
  `NautobotClient`/`build_source_snapshot`, now inlined here instead of
  buried inside the old `build_production_render`), composes via
  `build_production_render_context`, and returns `None` for the context
  whenever there is nothing safe to resolve a same-generation route from:
  a deployment-profiles load failure, no profiles configured, a token/fetch
  failure, or a failed render/atomic-install.
- `_execute_round` now branches on that context:
  - `render_context is None` and there are service actions to run ->
    immediately raises `_SshPostRegenScanFailed` with a new
    `production_regeneration_unavailable` error, running zero service
    actions.
  - `render_context is not None` -> `resolve_production_routes` is called
    with `render_context.source_snapshot` and `render_context.generated_at`
    -- the exact snapshot/generation that was just composed and written --
    never the round-start `snapshot` parameter. The service-action loop
    itself moved inside this branch, so a render failure structurally cannot
    reach any service action.

## Test changes

### `nctl_core/reconcile/ssh_preflight.py` tests (`test_ssh_preflight.py`)
- Existing `route_overrides={...}` call sites now wrap in `RouteOverrides(...)`.
- `test_verify_offered_keys_unreachable_when_route_override_missing_and_no_mdns`
  now asserts `no_resolvable_production_route` (was `no_resolvable_route`,
  the pre-fix bug's actual detail for this exact input).
- New tests (4): `test_verify_offered_keys_empty_production_map_never_falls_back_to_mdns`
  (plan's required regression test -- empty explicit map stays unreachable
  even with a real mDNS endpoint present, keyscan never runs);
  `test_verify_offered_keys_bootstrap_mode_none_still_falls_back_to_mdns` and
  `test_verify_offered_keys_bootstrap_mode_unreachable_detail_when_no_mdns`
  (bootstrap mode, `route_overrides=None`, is unaffected either way);
  `test_verify_offered_keys_slug_missing_from_partial_map_does_not_escape_to_mdns`
  (plan's required regression test -- one of two targets missing from an
  otherwise-populated map does not escape to mDNS while the other target is
  scanned normally).

### `nctl_core/reconcile/executor.py` tests (`test_reconcile_executor.py`)
- Added `_patch_production_render(monkeypatch, snapshot_factory)`: stubs
  both `build_source_snapshot` and `build_production_render_context`
  together, since `_regenerate_production_inventory` now performs its own
  fetch-then-compose rather than one opaque call to the old
  `build_production_render`. The two existing tests that patched
  `build_production_render` directly (`test_service_phase_blocks_on_mismatched_key_after_production_regen`,
  `test_independent_service_action_failure_does_not_block_the_other`) were
  updated to this helper -- the old attribute no longer exists on the
  executor module.
- Both updated tests also needed a resolvable production route (a
  `declared_host_os="haos"` operational override, needing no realized/actual
  facts) to genuinely exercise route-based scanning; without it,
  `resolve_production_routes` legitimately found nothing for either test's
  node fixture even before this step, and the *old*, buggy
  `verify_offered_keys` silently masked that by falling back to mDNS -- the
  exact bug bug #3 fixes. Confirmed via `git stash` that
  `resolve_production_routes` already returned `{}` for the un-augmented
  fixture on the pre-Step-3 commit.
- New tests (2), both plan-required regressions:
  - `test_production_write_failure_starts_no_service_ansible_process` --
    `write_production_artifacts` returning an error yields
    `production_regeneration_unavailable` and zero `AnsibleRunner` calls.
  - `test_service_phase_scans_freshly_regenerated_route_not_round_start_snapshot`
    -- the round-start snapshot's node endpoint has `ip_address="10.0.0.1"`;
    the separately-fetched regeneration snapshot has `"10.0.0.2"`. Asserts
    `ssh-keyscan` is called against `10.0.0.2` and never `10.0.0.1`, and the
    service action (a real, successful `AnsibleRunner.run`) executes.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py \
    nctl/tests/test_ssh_enroll.py nctl/tests/test_ssh_preflight.py \
    nctl/tests/test_production_contract.py nctl/tests/test_production_composer.py \
    nctl/tests/test_production_render.py nctl/tests/test_dnsmasq_apply.py \
    nctl/tests/test_reconcile_executor.py
217 passed in 0.57s

$ uv run --project nctl pytest -q nctl/tests
846 passed, 1 warning in 5.73s
```

Lint/type check: still not run -- no ruff/mypy in `nctl/pyproject.toml`'s dev
group (see Step 1 report).

## Step 3 exit criteria

- [x] The executor no longer passes the round-start snapshot to
  post-regeneration scanning (`resolve_production_routes` is now always
  called with `render_context.source_snapshot`).
- [x] The installed inventory and scanned route have the same generation ID
  and source context (`ProductionRenderContext` bundles both; the write and
  the route resolution both derive from the one context object).
- [x] A missing route, generation failure, or key mismatch stops before
  service actuation (`render_context is None` -> no service actions at all;
  `no_resolvable_production_route` -> `ssh_host_key_unreachable`,
  unreachable/mismatch both raise `_SshPostRegenScanFailed` before the
  service-action loop, which is now structurally inside the success branch).

## Handoff to Step 4

- `dnsmasq_apply.py`'s current `_has_valid_ssh_trust_vars()` boolean check
  is untouched; Step 4 replaces it with a structured per-host validator and
  reuses `resolve_production_routes`/`RouteOverrides` (the pure route helper
  this step relied on) for its own pre-Ansible offered-key check, on both
  the configured inventory and `--inventory`.
