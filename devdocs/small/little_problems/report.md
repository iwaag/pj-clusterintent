# Service Endpoint Probe Separation Report

## Status

Complete. The service-specific HTTP endpoint probe definitions no longer live
in the collector orchestration module.

## Changes

- Added `nodeutils/service_endpoint_probes.py` with a closed `HTTP_PROBE_SPECS`
  registry and the bounded HTTP probe executor.
- Moved the Ollama, SwarmUI, and ComfyUI path definitions out of
  `nodeutils_collect.py`. The collector now imports and invokes the probe
  boundary without branching on service names.
- Added the new module to the setuptools `py-modules` list.
- Updated tests to exercise the separated boundary, assert the exact registered
  URLs, and prove that an unregistered service causes no HTTP request.
- Added concise guidance to `README_DEV.md`: retain the static registry at the
  current scale, and move validated probe specifications into deployment-profile
  observation metadata only when system growth justifies that cross-component
  contract.

## Compatibility and scope

This is intentionally a small refactor. Probe paths, three-second timeout,
HTTP-error handling, normalized observation output, and unknown-service behavior
are unchanged. Dynamic plugin loading and deployment-profile schema changes are
out of scope.

Other service-specific observation code in `nodeutils_collect.py` (user-service,
host-tool, and Docker-image detection) was not moved because it has different
observation contracts and is not required to resolve this memo's endpoint-probe
coupling.

## Verification

- `cd nodeutils && uv run pytest -q tests/test_inventory_report.py` — 40 passed.
- `cd nodeutils && uv run pytest -q --durations=20` — 78 passed.
- `cd nodeutils && uv run ruff check service_endpoint_probes.py` — passed.

An initial broader Ruff check also reported six pre-existing formatting/unused-
variable findings in `nodeutils_collect.py` and `tests/test_inventory_report.py`;
none was in the new module or caused by this separation, so unrelated cleanup
was left out of this change.
