# P4 — Additional completion work

This log records work performed after the original Step 8 report. It is the
authoritative running record for additional work needed to close Phase 4;
`report.md` retains only genuinely unavailable or blocked proof.

## 2026-07-28 — production ownership and service evaluator

- Extracted production route selection and connection-variable resolution to
  `nctl_core.production.routes`. Composer and inventory-trust preflight share
  the same owner.
- Extracted composition input/result types to `nctl_core.production.model` and
  report-record translation to `nctl_core.production.report`. The composer now
  constructs inventory and coordinates outcomes; report translation cannot
  affect inventory construction.
- Extracted `evaluate_service_intent` to
  `nctl_core.drift.service_evaluation`; snapshot orchestration and its direct
  tests import the new owner.
- No re-export or compatibility import was retained for moved public symbols.
- Verification after these moves: `cd nctl && uv run pytest -q --durations=10`
  — 974 passed.

## Remaining active work

1. Extract node and endpoint drift evaluators, then move their remaining
   candidate/ranking rules to the appropriate single-purpose owners.
2. Separate the remaining inventory-composition coordination from its host
   assembly helpers if doing so leaves a real, independently testable reason to
   change.
3. Re-run the Phase 4 baselines and required gates; only a runtime-gate failure
   that is reproduced and evidenced remains in `report.md`.

## 2026-07-28 — runtime gate recovery

Both local scratch runtime-gate modes now pass:

- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb`
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean`

The clean mode dropped only the test-owned `test_nautobot` database before
running. `makemigrations --check --dry-run` reported no changes in both modes,
and the staged exact-local-source app test returned success. The earlier runtime
database failure is no longer an unavailable proof and must not remain as a
blocker in `report.md`.
