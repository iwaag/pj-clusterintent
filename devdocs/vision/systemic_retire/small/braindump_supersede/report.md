# Braindump supersession — implementation report

Date: 2026-07-29

## Delivered

- Added `BrainDumpDocument.status` with `active` (default) and `superseded`, including migration
  `0018_braindumpdocument_status`.
- Added status to REST/GraphQL projections, Nautobot filtering, and the Braindump table.
- Added the sole server-side transition: `POST /api/plugins/intent-catalog/braindumps/supersede/`.
  It locks and validates all supplied active IDs, creates one active replacement, and marks exactly
  those old rows superseded in one database transaction.  Generic Braindump PATCH and DELETE remain
  unavailable.
- Added `nctl braindump supersede --old OLD_ID ... --title TITLE --authorship ... (--body TEXT | --file PATH)`.
  It validates exact UUIDs, confirms the replacement and every superseded row through fresh GraphQL
  reads, and emits `nctl.braindump.supersede.v1`.
- Ordinary `nctl braindump list` now returns active documents only.  `--include-superseded` exposes
  reference-only history, and direct `show` works for either status.
- Updated the nintent and nctl public documentation.  No Desired, Actual, drift, reconcile,
  nodeutils, Ansible, or Proxmox path was introduced or changed.

## Verification

- `cd nctl && uv run pytest -q --durations=20` — 989 passed.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` — 239 passed,
  14 expected Nautobot-runtime skips.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_braindump`
  — 35 passed.  This includes the transactional success and invalid-old-ID rollback cases.
- `uv run --project nctl nctl braindump supersede --help` and `... list --help` confirmed the new
  command and explicit history option are wired into the CLI.

## Scope note

Supersession only changes the conversational-context status.  It is not a provenance relation,
does not decide contradictions, and grants no authority to retire, unmanage, stop, destroy, or
prune structured cluster state.
