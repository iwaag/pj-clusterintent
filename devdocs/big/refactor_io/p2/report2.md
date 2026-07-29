# Phase 2 Step 2 Report — Endpoint Contract Tests

## Result

Complete. The batch endpoint now has Django-free YAML parser coverage and
Nautobot runtime API coverage. Runtime cases prove unauthenticated rejection,
read-only-token denial, zero-write dry run, mixed create/update/delete commit,
full-artifact conflict responses with atomic no-write behavior, JSON/YAML
artifact equivalence, malformed YAML and validation 400 responses, unsupported
media-type 415, and non-POST 405 behavior.

## Verification

- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — passed: 127 tests, 14 expected skips (unchanged).
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_batch_api`
  — passed: 5 cases (staged local sources).
- `git -C nintent diff --check` — passed.
