# Phase 1 Step 1.1 — Freeze the baseline and local-failure contract

Parent: [plan.md](plan.md) Step 1.1.

## 1. Baseline test counts (before any Phase 1 code change)

```
uv run --project nctl pytest -q nctl/tests
```

Result: **518 passed** (plus 1 unrelated `StarletteDeprecationWarning`), matching the plan's stated
Phase 0 baseline exactly. No nintent code changes are made in Phase 1, so the nintent suite (88
tests per Phase 0 report0.8.md) was not re-run; it is a regression check outside this phase's
implementation surface, per the plan's "Current state" section.

## 2. Reconfirmed the 57 `raise ContractError` call sites and the Group A/B/C split

```
grep -n "raise ContractError" nctl/src/nctl_core/production/*.py
```

Result: 1 in `composer.py` (the `missing_operational_config` check), 56 in `contract.py` — 57
total, matching `p0/field-classification.md` §6 exactly. Re-read §6's Group A (13 codes, shared
deployment-profile schema), Group B (13 codes, final closed-output-contract validation), and Group
C (15 codes, per-node/per-placement composition) tables against the current source line numbers:
no drift since Phase 0 — the classification artifact did not need updating before implementation.

## 3. Constants for the three target-local code groups (`production/composer.py`)

Added, next to `PRODUCTION_ELIGIBLE_LIFECYCLES`:

- `NODE_LOCAL_CODES` (8 codes: `missing_operational_config`, `invalid_actual_state_policy`,
  `unsupported_observed_host_os`, `invalid_platform_power`, `endpoint_node_mismatch`,
  `unresolved_connection_path`, `invalid_connection_path`, `invalid_connection_address`)
- `PLACEMENT_LOCAL_CODES` (6 codes: `unknown_profile`, `unsupported_config_schema`,
  `invalid_placement_config`, `unknown_config_key`, `missing_required_config`,
  `invalid_profile_value_type`)
- `MERGE_LOCAL_CODES` (1 code: `conflicting_host_variable`)
- `LOCAL_COMPOSITION_CODES` = the union (15 codes, matches Group C exactly)
- `ACTIVE_PLACEMENT_NOT_APPLIED` = `"active_placement_not_applied"` (Step 1.3's new code)
- `PHASE1_LOCAL_CODES` = `LOCAL_COMPOSITION_CODES | {ACTIVE_PLACEMENT_NOT_APPLIED}` (16 codes) —
  the single vocabulary `reconcile/classify.py` and the test suite import rather than redeclaring
  (roadmap.md's mandatory check 2: "a node-level error absent from `CODE_CLASSIFICATION` makes
  planning fail closed").

These live in `composer.py` ("close to the composer" per the plan) and are imported by
`reconcile/classify.py` and by tests — no second unconnected 15/16-code list exists anywhere else
in the tree.

## 4. Internal structured finding/error carrier

Added `LocalCompositionError(Exception)` in `production/composer.py`: `code`, `message`, `stage`,
`evidence` (a JSON-safe dict). It is raised internally by `_compose_host`'s per-stage catch blocks
and caught by the eligible-node loop, which turns it into one `report["skipped"]` entry and one
`report["errors"]` entry (Step 1.2). It is an internal implementation detail, not a second public
diff schema — nothing outside `composer.py` imports or handles it directly.

## Outcome

No behavior changed in this step; it is preparation only. Proceeded directly to Step 1.2 in the
same commit, because implementing structured local errors without also registering their
classification would reopen the exact `UnclassifiedDiffCodeError` landmine the roadmap and plan
both call out by name — see `report1.2.md`.
