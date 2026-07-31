# minimize_desired_services — Report

Date: 2026-07-31

## Status

**Implemented, not deployed.** The final source contract is implemented and
the local unit suites pass. Deployment and the required clean Nautobot runtime
test remain pending because the nintent image installs from GitHub and the new
nintent commit has not been pushed.

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

- nintent: `ee23e4d Simplify desired service identity`
- nctl: `a9dd4af Read desired services by slug identity`

## Verification

| Gate | Result |
|---|---|
| `cd nctl && uv run pytest -q --durations=20` | passed — 1015 tests |
| `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` | passed — 128 tests, 10 expected skips |
| source sweep (excluding migrations) | passed — no removed-field references remain in nintent, nctl source/tests/docs |
| `run_nautobot_runtime_gate.sh --clean` | inconclusive — clean DB setup and `makemigrations --check --dry-run` reached `No changes detected`, but the container test runner outlived the local gate process before it emitted a case count; the exact test-owned `test_nautobot` DB was dropped afterward |

## Required handoff

1. Push nintent commit `ee23e4d` to GitHub.
2. Rebuild and restart the local Nautobot image from `devenv/nautobot/` with
   `docker compose build --no-cache` and `docker compose --env-file ../.env up -d`.
   Confirm the build resolved the pushed nintent SHA.
3. Run `nautobot-server migrate`, then rerun
   `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` and record
   its `cases=` count.
4. Preview and commit `.local/desired-state.yaml` with `nctl desired apply`,
   then verify `nctl drift` and a dry `nctl reconcile`.
