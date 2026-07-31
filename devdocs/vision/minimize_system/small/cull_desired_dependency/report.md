# cull_desired_dependency — implementation report

Date: 2026-07-31

## Result

**Implemented, not deployed.** `DesiredDependency` and the inert service
`requirements` evaluator contract have been removed in a coordinated breaking
change. The local nintent and nctl commits are ready for deployment, but the
running Nautobot image still installs nintent from GitHub. Per the local
environment policy, pushing that commit is an operator action and was not
performed here.

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

## Deployment handoff

1. Push nintent commit `aca2fa9` (and the superproject pointer after its local
   commit) to the repository used by the Nautobot Dockerfile.
2. From `devenv/nautobot`, run `docker compose --env-file ../.env build
   --no-cache`, verify the resolved nintent SHA is `aca2fa9`, then restart the
   stack.
3. Run `nautobot-server migrate` in the Nautobot container and confirm the
   Dependencies navigation item is gone and a desired-service detail page
   renders.
4. Run `uv run --project nctl nctl drift --json`; it should still run cleanly
   against the rebuilt instance and contain no `unresolved_dependency` code.

Do not restore the two exploratory dependency rows. If their host/artifact
facts need to become managed intent, obtain an operator decision and express
them in the relevant `DesiredServicePlacement.config` under
`manual_toolchain`.
