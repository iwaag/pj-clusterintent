# cull_desired_dependency — implementation report

Date: 2026-07-31

## Result

**Complete.** `DesiredDependency` and the inert service `requirements`
evaluator contract have been removed in a coordinated breaking change and are
deployed to the local Nautobot scratch environment.

## Changes

- nctl no longer selects `desired_dependencies` from GraphQL, exposes a
  dependency read model, or stores dependency rows in `DesiredSnapshot`.
- Service drift no longer emits `unresolved_dependency`, dependency counts, or
  `requirements_present`; its evaluation scopes now name lifecycle and
  placements only. The manual-review classifier and dependency-only tests were
  removed accordingly.
- nintent no longer has the `DesiredDependency` model, batch/API kind, UI
  routes, navigation item, filter, table, templates, factories, or dependency
  panel. Migration `0022_remove_desireddependency` drops the table and its
  exploratory rows.
- The stale `Analyze Intent Sources` documentation row was deleted because that
  Job does not exist. `CONCEPT.md` and UI contract counts now describe the ten
  retained inspection lists / twenty GET routes.
- The real-profile test now includes the already-declared `manual_toolchain`
  profile, which the surviving placement uses. This fixes a pre-existing test
  expectation mismatch without changing its production configuration.

Local commits:

- nctl: `23802d4` (`Remove desired dependency evaluation`)
- nintent: `aca2fa9` (`Remove desired dependency model`)

## Verification

- `cd nctl && uv run pytest -q --durations=20` — **1015 passed**.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — **127 passed, 10 expected skips**.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` — **189
  passed**. It staged the committed sources, confirmed `makemigrations --check`
  reported no model/migration divergence, built the clean test DB, and exercised
  the retained UI; the Dependencies navigation entry and service dependency
  panel are absent.
- `uv run nctl ops show 01KYV9N12ZFKEJ0D090JKEGNHR --json` successfully read
  pre-change operation evidence.
- `uv run nctl drift --json` successfully queried the still-running old-schema
  Nautobot and emitted no `unresolved_dependency` finding. Existing unrelated
  drift remains (three drifting and three unknown targets).
- The requested residual search over `nintent/`, `nctl/src/`, `nctl/tests/`,
  and `nctl/docs/` returns only Django migration history and the new removal
  migration; `git diff --check` passes.

## Deployment confirmation

- User pushed nintent `aca2fa9`; the Dockerfile pin was updated to its full
  SHA and a `docker compose --env-file ../.env build --no-cache` build resolved
  and installed exactly that revision.
- The Nautobot, worker, and scheduler containers were recreated. The container
  reports the same installed nintent revision.
- `nautobot-server migrate` completed, and `showmigrations` confirms
  `0022_remove_desireddependency` is applied.
- An authenticated local Django client returned HTTP 200 for a desired-service
  detail page. It found neither a Dependencies navigation label nor a
  `desireddependency_list` route.
- Post-deployment `uv run --project nctl nctl drift --json` completed without
  `unresolved_dependency`. Unrelated existing drift remains.

Do not restore the two exploratory dependency rows. If their host/artifact
facts need to become managed intent, obtain an operator decision and express
them in the relevant `DesiredServicePlacement.config` under
`manual_toolchain`.
