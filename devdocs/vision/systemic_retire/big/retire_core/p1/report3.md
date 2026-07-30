# Retire core Phase 1 — Step 3 nctl read and evidence

Date: 2026-07-30

## Completed work

nctl `49f4355` requests `desired_presence` from GraphQL, maps it into the typed
`DesiredComputeInstance` (default `present` for older/missing rows), and validates it with the
fixture-bound mirrored contract. An invalid value becomes a target-scoped
`DesiredSourceIssue`; only that instance row is dropped.

`compute_realization_summary` now includes `desired_presence` and effective lifecycle on the
desired side for an instance summary. No drift code, severity, classification, plan, action,
or CLI option changed.

## Verification

| command | result |
|---|---|
| focused collection/source/evaluation/conformance tests | 27 passed |
| `uv run pytest -q --durations=20` (nctl) | 989 passed in 5.90s |

Focused cases prove GraphQL/default round-trip, invalid-row isolation, and summary projection.

## Status

**complete** — nctl can read and report the new intent while preserving existing present-state
compute behavior.
