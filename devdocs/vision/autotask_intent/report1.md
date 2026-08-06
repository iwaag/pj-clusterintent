# autotask_intent — Step 1 Report: Explicit check schema in nctl

Status: **complete** (per plan.md Step 1 acceptance criteria).

## What was implemented

`nctl/src/nctl_core/reconcile/profiles.py`:

- `FileExistsCheckSpec` — closed existence-proof check. Exactly one of
  `path` (literal, absolute or `~/`-relative) or `path_from_config` (name of
  a placement `config` key holding the path). `resolve_path()` validates the
  config value (non-empty string, absolute or home-relative) and raises the
  new `CheckResolutionError` otherwise.
- `HttpCheckSpec` — closed HTTP liveness check: non-empty `paths` list, each
  rooted at `/`. Absorbs (in Step 2) the paths `HTTP_PROBE_SPECS` hard-codes
  by service name today. The endpoint itself still comes from the placement's
  declared `DesiredEndpoint` hint.
- `ProfileReconciliation.checks` — a discriminated-union list
  (`kind: file_exists | http`). Restricted to `observe_only` profiles in this
  phase: every current consumer is existence proof, and action profiles keep
  their existing `managed_files`/`bindings` contracts. Unknown `kind` values
  are rejected at load time (closed schema, no silent acceptance).
- `resolve_check_hints(entry, placement_config, context)` — the one place
  check specs are resolved into fully-resolved hint rows. The profile layer
  owns check semantics; downstream consumers get final paths only.

`nctl/src/nctl_core/observation.py`:

- `render_probe_hints` now resolves each active placement's profile `checks`
  against that placement's own `config` and emits a `checks` list under the
  service's probe hint. nodeutils never sees `path_from_config`. A
  missing/empty/relative config value raises `CheckResolutionError` at render
  time — a validation error, not a silent skip (README_DEV lesson 1).

Only the two kinds with a consumer in this plan were built (no speculative
`cron_registered` / `file_fresh` kinds). Existing `install_path`,
`managed_files`, and `bindings` flows are untouched in this step; migration
of the observe-only trio happens in Step 2. The dnsmasq `managed_files`
digest flow stays as-is permanently, per plan.

## Verification

- New Tier B validation tests in `nctl/tests/test_reconcile_profiles.py`:
  parse of `cron_task`/`ollama`-style checks; rejection of checks on action
  profiles, dual/absent path sources, relative literal paths, empty or
  unrooted HTTP paths, and unknown kinds; `resolve_check_hints` substitution
  plus its four `CheckResolutionError` failure modes ({}, empty string,
  non-string, relative value).
- New rendering tests in `nctl/tests/test_observation.py`:
  a `cron_task`-style placement with `config.script_path` renders
  `checks: [{kind: file_exists, path: /home/eiji/mycron/heartbeat.sh}]`
  (the plan's acceptance example), and a placement missing the config key
  makes `render_probe_hints` raise (positive evidence the error path runs).
- Gate (README_DEV matrix, "nctl ordinary", from `nctl/`):
  `uv run pytest -q --durations=20` → **1275 passed** (was 1264 before this
  step; 11 new cases), 0 failed, 0 skipped.

## Notes for later steps

- `render_probe_hints` now iterates active placements directly (previously a
  per-service tuple map) so it can reach `placement.config`; hint output for
  all pre-existing fixtures is byte-identical (full suite green).
- `CheckResolutionError` propagates out of `run_observation` via
  `render_probe_hints`, failing the observation round loudly. Step 3 should
  confirm this surfaces as a classified error in the reconcile executor if a
  bad placement config reaches a live round.
