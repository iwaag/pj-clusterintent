# Retire core Phase 1 — Step 2 persistence and write validation

Date: 2026-07-30

## Completed work

nintent `7c88023` adds `DesiredComputeInstance.desired_presence` with choices
`present|absent`, default `present`, and migration `0021_desiredcomputeinstance_desired_presence`.
The canonical batch writer accepts the field without making it a create-required field.

The shared topology validator now rejects `desired_presence='absent'` unless the already
computed effective lifecycle is `retired`, before the non-actionable-lifecycle early return.
The error identifies `desired_presence` and the effective lifecycle. Read-only tables, filters,
and detail views display the new value. Braindump behavior is untouched.

## Runtime verification

`./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
nautobot_intent_catalog.tests.test_batch` passed **12 cases**. The staged local source passed
`makemigrations --check --dry-run` with no changes detected. The cases cover the default,
all non-retired effective lifecycles, unknown values, an atomic `retired + absent` batch commit,
and the absent-only batch rollback.

## Status

**complete** — persistence and supported-write-path validation are ready for deployment. The
migration has only been exercised in the test-owned database so far; scratch deployment and the
canonical live writer proof remain Step 4.
