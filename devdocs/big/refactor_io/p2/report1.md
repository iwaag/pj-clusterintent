# Phase 2 Step 1 Report — Endpoint

## Result

Complete. `POST /api/plugins/intent-catalog/desired-state/batch/` is now a
plain authenticated DRF view registered alongside the existing router routes.
It accepts JSON and the three supported YAML media types, decodes all of them
to the same batch document, checks the required per-kind model permissions,
and delegates planning/application directly to `plan_batch()`/`apply_batch()`.

`dry_run` remains solely a body field. The endpoint returns the complete batch
artifact, maps blocked/rolled-back results to HTTP 409, returns ordinary DRF
400/415 responses for malformed input or unsupported media types, requires
authentication, and rejects a non-write-enabled API token before it can apply.
Neither request nor result is persisted.

## Verification

- `python3 -m compileall -q nintent/nautobot_intent_catalog/api` — passed.
- `git -C nintent diff --check` — passed.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_api_contract`
  — passed: 20 cases (staged local sources; route registration and existing
  API contract coverage).
