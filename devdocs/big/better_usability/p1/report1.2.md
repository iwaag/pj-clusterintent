# Phase 1 Step 1.2 — Localize every Group C failure in the composer

Parent: [plan.md](plan.md) Step 1.2. Builds on [report1.1.md](report1.1.md)'s constants/carrier.

## What changed

`production/composer.py`:

- `missing_operational_config` no longer raises. It becomes a `LocalCompositionError`
  (`stage="operational_config"`) immediately, added as one `skipped` entry and one `errors` entry;
  composition continues to the next node.
- `_compose_host` wraps each stage that can raise a Group C code in its own `try/except
  ContractError`, calling `_localize(exc, <allowlist>, stage=..., evidence=...)`:
  - `evaluate_platform_policy` → `NODE_LOCAL_CODES`, `stage="platform_policy"`
    (`invalid_actual_state_policy`, `unsupported_observed_host_os`, `invalid_platform_power`).
  - `_validated_endpoint` (local + tailscale) → `NODE_LOCAL_CODES`, `stage="endpoint_ownership"`
    (`endpoint_node_mismatch`).
  - `resolve_connection_variables` → `NODE_LOCAL_CODES`, `stage="connection"`
    (`unresolved_connection_path`, `invalid_connection_path`, `invalid_connection_address`).
  - `map_placement_config` (per active placement) → `PLACEMENT_LOCAL_CODES`,
    `stage="placement_config"`, evidence includes the full placement (id, instance_name, profile,
    schema version, desired_state, `config` verbatim — matching the plan's exact JSON shape).
  - `merge_host_variables` → `MERGE_LOCAL_CODES`, `stage="host_merge"`.
  - `_localize` re-raises any code **not** in the stage's allowlist unchanged (Decision 2: an
    unexpected `ContractError` code still aborts the whole run rather than being silently
    downgraded).
- On any `LocalCompositionError`, the eligible-node loop appends exactly one `skipped` entry
  (`reasons=[code]`) and one `errors` entry, marks the node's placements inactive, and `continue`s
  — no partial `ssh_hosts`/selector/service-group membership is ever left behind.
- `report["errors"]` is now populated (was always `[]`) and sorted deterministically by
  `(desired_node_slug, code, stage, placement.instance_name, placement.id)`.

### The `invalid_connection_address` dual-call-site question (p0 §6 flag)

Grepped `_normalize_ip`'s only raise site and its three call sites: all three are inside
`resolve_connection_variables`, which is called exactly once, from `_compose_host` (per node).
**There is currently no separate document-level call site** — Phase 0's caution about "two call
sites" was precautionary, not describing existing dual usage. `test_invalid_connection_address_per_node_call_site_is_local_not_global`
documents this finding so a future document-level IP-normalization addition doesn't get
blanket-classified as local by accident.

### `invalid_placement_config` is unreachable through the composer today

`_compose_host` always calls `dict(placement.config)` before `map_placement_config`, so a typed
`PlacementInput.config` can never reach the contract layer as a non-mapping — `dict(x)` either
raises `ValueError` itself (e.g. for a list) or produces a real `dict`, so
`isinstance(config, dict)` inside `map_placement_config` can never be false via this path. The code
stays in `PLACEMENT_LOCAL_CODES` (Phase 0's classification is about ownership, not reachability),
and `test_invalid_placement_config_is_localized_when_raised` verifies the catch/localize logic
directly by monkeypatching `map_placement_config` to raise it.

## Why classification was added in this same commit (not deferred to Step 1.5)

Confirmed the exact landmine `p0/field-classification.md` §6 and the roadmap warn about:
`drift/comparators.py::production_policy` already converts **every** `report["skipped"][].reasons`
entry into a node-targeted `DiffRecord` today (pre-dates Phase 1). The moment `composer.py` stopped
raising and started adding Group C codes to `skipped`, those diffs immediately became
`Target(kind="node")` — before Step 1.4's dedicated drift wiring was even written. `reconcile/classify.py`
would raise `UnclassifiedDiffCodeError` for any of these 16 codes the first time a plan touched
them. Landing composer localization without classification would have shipped a commit with a real
`UnclassifiedDiffCodeError` window, which the plan's "Suggested commit order" explicitly forbids
("never rely on the next commit to close an `UnclassifiedDiffCodeError` window").

So this commit also updates `reconcile/classify.py`: imports `PHASE1_LOCAL_CODES` from
`production/composer.py` (not redeclared) and registers all 16 codes as
`Classification.MANUAL_REVIEW` with no reconciler. `tests/test_reconcile_classify.py` gained
`test_every_phase1_local_composer_code_is_classified`, which imports the composer's declared set
directly (the existing regex-based scan only targets comparator/evaluator files, not
`composer.py`'s frozensets, so it could not have caught a gap here).

`active_placement_not_applied` (the 16th code, Step 1.3's finding) is registered now too, even
though nothing produces it yet — it does not become reachable until Step 1.3 lands, so there is no
matching landmine risk in the other direction.

## Tests

- Rewrote 4 pre-existing composer tests that asserted the old `raise ContractError`/global-abort
  behavior for `missing_operational_config`, `invalid_platform_power`, `conflicting_host_variable`,
  and `unknown_profile` to assert the new skip+error behavior instead.
- Added a full Group C parameterized matrix (`test_group_c_failure_skips_only_the_bad_node`, 14
  cases covering all 15 codes minus the unreachable `invalid_placement_config` handled separately):
  each case pairs one healthy node with one node built to trigger exactly one code, and asserts the
  healthy node's inventory/group/config output is untouched while the bad node is skipped with a
  matching `skipped`/`errors` pair.
- `test_group_c_matrix_covers_every_declared_local_code` pins the matrix against
  `LOCAL_COMPOSITION_CODES` so a future 16th Group C code can't be added without a matching test
  case.
- `test_group_c_output_is_byte_stable_across_runs` — determinism check.
- `test_group_a_shared_profile_error_still_aborts_globally` /
  `test_group_b_final_output_error_still_aborts_globally` — representative Group A/B errors still
  raise `ContractError` and abort the whole run.
- Updated two now-outdated drift tests (`test_drift_comparators.py`,
  `test_drift_engine.py`) that asserted `invalid_platform_power` produced a `global` target; split
  each into a Group A (still-global) case and a new Group C (now node-targeted) case.

## Test count

```
uv run --project nctl pytest -q nctl/tests
```

Result: **540 passed** (518 baseline + 24 net new/modified assertions across
`test_production_composer.py` and `test_reconcile_classify.py`), 1 unrelated pre-existing warning.

## Outcome vs. exit criteria

- Every one of Group C's 15 codes is now caught only at its target-owned stage and produces a
  node-local structured skip/error; none is global. ✅ (parameterized matrix)
- Representative Group A/B failures still abort globally. ✅
- A mixed good+bad render succeeds, preserves healthy inventory/group/config output, emits no
  partial membership for the skipped node. ✅
- All 16 Phase 1 codes are `MANUAL_REVIEW` in `CODE_CLASSIFICATION`. ✅ (pulled forward from Step
  1.5 to close the landmine window in this commit)
- `active_placement_not_applied` itself does not exist yet — Step 1.3.
