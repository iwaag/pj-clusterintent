# Immutable Braindump — implementation report

Date: 2026-07-29

## Result

Implemented the immutable Braindump contract.  A created `BrainDumpDocument` remains readable and
cannot be changed or physically deleted through the supported REST, UI, or nctl surfaces.
Alignment Review create/replace/delete behaviour is unchanged.

## Changes

- `BrainDumpDocumentViewSet` now allows only `GET` and `POST`; detail `PATCH`, `PUT`, and `DELETE`,
  plus bulk mutations, return `405 Method Not Allowed`.
- Removed nctl Braindump update/delete transports, core operations, renderers, schemas, CLI commands,
  confirmation path, output contracts, and documentation. `nctl braindump update` and
  `nctl braindump delete` are ordinary unknown commands.
- Updated the nintent Braindump guidance: corrections or changed wishes require a new Braindump;
  until supersession is delivered, both statements remain visible and an ambiguous relationship
  requires user clarification.
- Updated the systemic-retirement state note to reflect that no public Braindump deletion path
  remains. No migration was needed.

## Verification

- `cd nctl && uv run pytest -q tests/test_braindump.py tests/test_cli_braindump.py tests/test_current_consumer_contracts.py`
  — 66 passed.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — 239 passed, 14 expected Nautobot-dependent skips.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_braindump`
  — 32 passed.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_api_contract`
  — 21 passed.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_desired_node_link_http.DesiredNodeLinkRealHttpTests.test_authorized_prose_writes_do_not_change_real_drift_or_plan`
  — 1 passed; a Braindump write leaves real drift and reconciliation planning unchanged.

## Commits

- nctl: `db45c8b` — `Remove mutable braindump CLI paths`
- nintent: `d7436a3` — `Make braindump REST documents immutable`
- nintent: `7958a05` — `Cover immutable braindump runtime contract`
- nintent: `8baca14` — `Align braindump API contract tests`
