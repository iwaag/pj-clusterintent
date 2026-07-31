# minimize_desired_services — Report

Date: 2026-07-31

## Status

**Partially complete.** The final source contract is deployed to the local
scratch Nautobot, and the operator document has been re-applied without
conflict. The required clean Nautobot runtime gate remains inconclusive because
its container test process stopped before the wrapper could record `cases=`.

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
| `run_nautobot_runtime_gate.sh --clean` | inconclusive — clean DB setup, staged-source import, migration check (`No changes detected`), and 190-case collection ran, but the container test process stopped before the wrapper could record `cases=`; the exact test-owned `test_nautobot` DB was dropped afterward |

## Required handoff

1. Rerun `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` in
   an execution context that allows the container test runner to finish, and
   record its `cases=` count.
2. Address the pre-existing drift/unknown findings separately if full cluster
   convergence is required; this schema rollout did not mutate external nodes.
