# Phase 1 Step 2 Report — nctl Read-Side Alignment

## Result

Complete. nctl's GraphQL desired-state query and transport models no longer
select or expose fields removed by the nintent schema reduction. Ledger linking
now guards and confirms actual links by their relation IDs alone and sends no
`*_source` field. Compute reads use the fixed Proxmox/v1 code contract rather
than persisted discriminators. Production placement input/report validation no
longer carries `instance_role` or `assignment_source`.

## Verification

- `cd nctl && uv run pytest -q --durations=20` — passed: 987 tests.
- `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py`
  — passed: 1 test.
