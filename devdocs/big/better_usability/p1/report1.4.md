# Phase 1 Step 1.4 — Carry findings through drift, target status, and dashboard

Parent: [plan.md](plan.md) Step 1.4. Builds on [report1.3.md](report1.3.md).

## What changed

`drift/comparators.py::production_policy` rewritten:

1. `build_production_node_inputs(snapshot)` now runs unconditionally, before the
   `if not context.profiles` guard (it's pure and has no profile dependency).
2. **Degraded-profile path** (`context.profiles` empty): instead of returning `[]` immediately,
   calls `unapplied_placement_findings(node_inputs)` directly and yields each as a WARNING diff —
   the lifecycle gate must not depend on loading deployment profiles (Decision 4). When profiles
   *are* present, the composer's own copy (already merged into `report["drift"]`) is consumed
   instead; the two paths never both run, so there's no duplicate emission.
3. **Structured local errors first**: every `report["errors"]` entry becomes its own
   `Target(kind="node")`, `Severity.ERROR` diff with the report's exact `message`, `evidence` under
   `desired`, and `{"stage": ...}` under `actual`. The `(node_slug, code)` pairs it covers are
   recorded in `structured_error_keys`.
4. **Generic skip-reason conversion, deduplicated**: `report["skipped"][].reasons` still convert to
   generic diffs exactly as before, *except* any `(node_slug, reason)` pair already emitted as a
   structured error above is skipped — the same failure never appears twice.
5. **Drift dispatch by code**: `_drift_entry_diff` replaces the old code-blind OS-mismatch template.
   `desired_actual_os_mismatch` keeps its existing shape; `active_placement_not_applied` gets its
   own `_active_placement_not_applied_diff` (WARNING, `desired={"placement": ...}`,
   `actual={"node_lifecycle", "eligible_lifecycles", "application_status": "not_applied"}`). Any
   other code raises `AssertionError` rather than silently rendering with the wrong template — a
   composer/comparator vocabulary defect must fail loudly, per the plan's explicit requirement.

`drift/status.py`: **no code change**. `derive_status` already keys off `Severity.ERROR` only, and
none of the 15 Group C codes are in `UNKNOWN_CODES` (they mean "we have the data and it's invalid",
not "we lack actual data"), so they resolve to `DRIFTING` by the existing fallthrough; a
WARNING-only `active_placement_not_applied` already resolves to `CONVERGED` by the existing
"no error-severity diffs" rule. Pinned with two new tests
(`test_phase1_local_composition_error_is_drifting_not_unknown`,
`test_active_placement_not_applied_warning_alone_is_converged`) rather than left implicit.

`dashboard/html.py` and `dashboard/push.py`: **no code change**. The dashboard template renders
generically from the embedded `nctl.drift.v1` JSON (message/code/severity/desired/actual, already
escaped client-side per the existing hostile-message test); status push iterates
`drift_data.targets` (one row per `Target`, already node-only for every diff this phase adds) —
there is no separate "placement row" to accidentally invent. Added
`test_active_placement_not_applied_renders_with_warning_severity_and_evidence` to close this gate
with an explicit assertion rather than relying on the pre-existing generic tests alone.

## Why classification/dispatch was pulled into the same commit as Step 1.3

Confirmed by reading `production_policy` before this step: it already forwards every
`report["drift"]` entry into a `DiffRecord`, using a message template hard-coded to
`expected_host_os`/`observed_host_os`. Landing Step 1.3's composer change alone (already done, same
session) without this step's dispatch fix would have shipped `active_placement_not_applied`
findings rendered as `"active_placement_not_applied (expected None, observed None)"` the first time
one actually occurred — silently wrong output, not a crash, so nothing in the existing test suite
would have caught it. Both steps are one commit.

## Tests added

- `tests/test_drift_comparators.py`: `test_production_policy_local_error_yields_structured_error_not_generic_skip`,
  `test_production_policy_active_placement_not_applied_is_warning_and_converged_safe`,
  `test_production_policy_active_placement_not_applied_survives_empty_profiles`,
  `test_drift_entry_dispatch_rejects_unknown_composer_drift_code`.
- `tests/test_drift_status.py`: 2 tests (above).
- `tests/test_dashboard_html.py`: 1 test (above).

## Test count

```
uv run --project nctl pytest -q nctl/tests
```

Result: **557 passed** (550 after Step 1.3 + 7 new Step 1.4 tests), 1 unrelated pre-existing
warning.

## Outcome vs. exit criteria

- Every Phase 1 finding defines target kind, severity, message/evidence, source list, render-report
  effect, and drift/status/dashboard effect, and is tested. ✅
- `active_placement_not_applied` reaches `nctl drift` (text/JSON), status derivation, and the
  dashboard without special-casing anywhere outside `comparators.py`. ✅
- Reconcile classification for these codes is not yet exercised through the planner/executor — that
  is Step 1.5.
