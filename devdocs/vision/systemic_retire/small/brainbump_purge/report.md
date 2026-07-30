# Braindump purge — implementation report

Date: 2026-07-30

## Delivered

- Added the dedicated nintent endpoint
  `POST|DELETE /api/plugins/intent-catalog/braindumps/{id}/purge/`.
  `POST` is a read-only, server-side plan which reports the exact superseded
  document and Alignment Review presence. `DELETE` locks and re-checks the
  UUID/status, then deletes only that document and its one-to-one review in a
  single transaction.
- Generic Braindump REST `DELETE` remains unavailable. Active documents return
  the explicit `ineligible` result and remain readable; a missing document is
  the successful, scope-preserving `already_purged` no-op.
- Added `nctl braindump purge BRAINDUMP_ID [--yes]`, with typed text/JSON
  output `nctl.braindump.purge.v1`. Without `--yes` it calls the server plan;
  with `--yes` it invokes only the exact-target DELETE endpoint.
- Added focused API, core transport, CLI, and current-consumer contract tests.
  The runtime API test also asserts that DesiredNode, Device, and
  VirtualMachine reads are unchanged by purge.
- Updated the nctl reference, Brainforge guidance, and systemic-retirement
  big plot. Brainforge now requires showing the superseded text and obtaining
  the user's confirmation that it is no longer useful before requesting purge.

## Verification

- `cd nctl && uv run pytest -q --durations=20` — **1015 passed**.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — **127 passed, 10 expected Nautobot-runtime skips**.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_braindump`
  — **39 passed**.
- `uv run --project nctl nctl braindump purge --help` confirmed the command,
  UUID argument, `--yes`, and JSON surface.
- `git diff --check` passed in the superproject, nintent, and nctl worktrees.

## Scope confirmation

Purge has no route into Desired/Actual mutation, drift, reconciliation,
operation evidence, Ansible, Proxmox, or other cluster infrastructure. It adds
no retention period, scheduler, archive, undo path, or soft-delete state.
