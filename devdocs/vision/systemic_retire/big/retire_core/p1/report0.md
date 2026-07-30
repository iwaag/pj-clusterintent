# Retire core Phase 1 — Step 0 baseline

Date: 2026-07-30

## Revision and runtime tuple

| component | local checkout | running Nautobot image |
|---|---:|---:|
| superproject | `a09d824` | n/a |
| nintent | `d388049` | `305e457433be57f0ce60e54eff681ac7304008fa` |
| nctl | `df170b8` | n/a |
| nauto | `3bd1820` | `3bd1820fa19bc9603bdf20033a54468afc359c1a` |

The installed nintent revision differs from the local checkout. This is expected: the
scratch image installs nintent from GitHub, and Phase 1's Step 4 must rebuild only after
the local nintent commit has been pushed by the operator.

## Migration baseline

`nautobot_intent_catalog` migrations `0001` through `0020_alter_intentsource_options`
are applied. Migration `0021` does not yet exist.

## Drift baseline

`uv run --project nctl nctl drift --json` completed successfully. Its summary was
`drifting=2`, `converged=9`, and `unknown=4` (severity `error=6`, `warning=5`,
`info=17`). Thus the current scratch database is **not** globally converged, contrary to
the Phase 0 fixture-specific observation. `agfixture`'s compute instance itself remains
converged. The pre-existing differences are retained as the Step 4 comparison baseline;
Phase 1 must not add a new drift code, classification, or action.

## Status

**complete** — baseline captured, including the expected GitHub-installed nintent revision
difference and the current non-global drift.
