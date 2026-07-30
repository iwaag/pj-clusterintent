# Retire core Phase 1 — Step 1 contract and fixture

Date: 2026-07-30

## Completed work

- nintent `8c52531` owns `present|absent` desired-presence validation and the pure
  `desired_presence_requires_retired()` lifecycle pairing rule.
- nctl `c360de9` mirrors those read-time rules and replays the owner-generated
  conformance fixture.
- The fixture covers valid/invalid presence and every presence × effective-lifecycle
  combination. `absent` is accepted only with `retired`; `retired + present` remains
  legal.

## Verification

| command | result |
|---|---|
| `python3 -m unittest nautobot_intent_catalog.tests.test_compute_contract` | 65 passed |
| `uv run pytest -q tests/test_compute_conformance.py` (nctl) | 1 passed |
| `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` | 1 passed |

## Status

**complete** — the fixture binds both implementations; no persistence, drift, planner, action,
or VM-presence behavior was changed in this step.
