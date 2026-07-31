# minimize_desired_services — Report

Date: 2026-07-31

## Status

**Complete.** The final source contract is deployed to the local scratch
Nautobot, the operator document has been re-applied without conflict, and every
required gate has passed.

The clean Nautobot runtime gate was inconclusive on the first attempt — its
container test process stopped before the wrapper could record `cases=`. It was
rerun on 2026-07-31 in a context that let the runner finish and reported
`cases=190` with `OK`, closing the only outstanding criterion. The earlier stop
was an execution-context artifact, not a defect in this change.

## Delivered

- `DesiredService.slug` is unique and is the sole batch identity; the former
  Backstage identity fields and `IntentSource` model are removed.
- Migrations are ordered after the already-landed desired-dependency removal:
  `0023_desiredservice_slug_unique` removes the composite constraint then adds
  the unique slug index; `0024_remove_desiredservice_backstage_identity`
  removes the four fields and the model.
- nctl no longer requests, parses, or evaluates the removed fields.
- The batch API accepts slug references and has a regression test rejecting the
  removed four-part identity; no dual reader remains.
- Removed read-only source pages/navigation, stale service/node UI fields, the
  dead contract module, factories, and documentation/agent recipes.
- `.local/desired-state.yaml` now uses `slug` keys and scalar placement
  references.

## Commits

- nintent: `b809fae Simplify desired service identity`
- nctl: `a9dd4af Read desired services by slug identity`

## Verification

| Gate | Result |
|---|---|
| `cd nctl && uv run pytest -q --durations=20` | passed — 1015 tests |
| `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` | passed — 128 tests, 10 expected skips |
| source sweep (excluding migrations) | passed — no removed-field references remain in nintent, nctl source/tests/docs |
| local image rebuild | passed — no-cache build resolved nintent `b809fae3869cd7f251db331ee46e576bed359508`; Nautobot is healthy |
| live local migration | passed — migrations `0023` and `0024` applied; `DesiredService.slug.unique` is `True` and retained fields are `name`, `slug`, `lifecycle` |
| desired-state apply | passed — preview and confirmed apply both returned 22 unchanged, 0 conflicts |
| `nctl drift` / `nctl reconcile` | ran — cluster remains `converged=8`, `drifting=3`, `unknown=3`; the findings are existing observation/service state, not schema or batch-contract failures |
| `run_nautobot_runtime_gate.sh --clean` | passed on rerun — migration check `No changes detected`, `Ran 190 tests … OK`, `runtime gate result mode=clean label=nautobot_intent_catalog cases=190` |

The source sweep needs no exclusions: it returns zero hits outside Django
migration history.

A `test_rejects_the_removed_legacy_desired_service_identity` test initially
survived this rollout, sending the four removed key names to prove no dual
reader remained. It was deleted afterwards as a compatibility artifact in its
own right. `batch.py` contains no legacy-specific handling — the rejection comes
entirely from the generic `tuple(key) != _KEYS[kind]` check at `batch.py:93`, so
the test pinned no unique code path and existed only to keep the dead names
alive in the tree. It was the sole coverage of that generic branch, so it was
replaced by `test_rejects_a_key_that_is_not_the_declared_identity`, which
exercises the same line with neutral keys (wrong name, superset, empty value).
Coverage is preserved; the removed vocabulary is not.

## Required handoff

1. Address the pre-existing drift/unknown findings separately if full cluster
   convergence is required; this schema rollout did not mutate external nodes.
