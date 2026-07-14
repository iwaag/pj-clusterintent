# Phase 0-EX1 Report — Step 1 (Register GraphQL types in nintent)

Date: 2026-07-14. Continues from [p0/report0.3-0.7.md](report0.3-0.7.md); implements
[p0-ex1/plan.md](../p0-ex1/plan.md) Step 1 in `nintent`.

## What was built

- `nautobot_intent_catalog/models.py`: added `@extras_features("graphql")` (imported alongside
  `PrimaryModel` from `nautobot.apps.models`) to all eight desired-state models listed in the
  plan: `IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`,
  `DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange`, and
  `IntentEvaluation`. `DeploymentProfileProjection` is left undecorated, per the plan (advisory
  Ansible-owned snapshot, no FilterSet, not desired state).
- Version bump (breaking-change phase, honesty over compatibility): `pyproject.toml` and
  `nautobot_intent_catalog/__init__.py`'s `IntentCatalogConfig.version` both now read `0.4.0`.
  Note: these two had already drifted before this change (`pyproject.toml` was at `0.3.14`,
  `__init__.py` at `0.3.0`) — both are now aligned at `0.4.0` rather than perpetuating the drift.
  `uv.lock` picked up the matching self-reference version bump automatically via `uv run`.
- No model fields changed and no new models were added, so — as the plan expected — no Django
  migration was needed; `extras_features` only populates Nautobot's in-memory feature registry.

## Verification

- `uv run python3 -m unittest discover -s nautobot_intent_catalog/tests` (the project's actual
  Django-free local test harness — see `README_DEV.md`/`README_QUICK.md`; there is no pytest
  config in this repo) — 203 passed, 0 failures. This confirms the decorator addition didn't break
  any of the Nautobot-less unit tests, but per the plan, it does **not** exercise
  `extras_features`/GraphQL registration itself, since that only activates inside a running
  Nautobot process. That verification is deferred to Step 2 (live schema introspection against the
  dev container).
- Confirmed via `grep` that all 8 target classes carry the decorator immediately above their
  `class` line and that `DeploymentProfileProjection` does not.

## Deviations from plan

None. This step was a pure decorator + version-bump change, exactly as scoped.

## Commit boundary

This is a clean, self-contained commit: `nintent`'s `@extras_features("graphql")` registration +
version bump, with the existing local test suite green. Per the plan's suggested commit order,
this is commit 1 of 3 ("nintent: `@extras_features("graphql")` on the models + version bump").

**Not done yet, deliberately left for the next commit(s):**
- Step 2 — push this commit, rebuild/restart the dev Nautobot container, and introspect the live
  GraphQL schema to record actual field names (`desired_nodes`, relation names, JSONField
  behavior) — requires the user to push per `.local/localenv_memo.md`'s update flow, so it wasn't
  bundled into this session's stopping point.
- Steps 3–4 (nctl's GraphQL introspection probe, `intent_graphql` status field, tests, docs) depend
  on the exact names Step 2 will pin, so they haven't started.

## Exit criteria status

- [ ] All desired-state models queryable at `/api/graphql/` on dev Nautobot — **code-complete,
  not yet live-verified** (needs Step 2's push/rebuild cycle).
- [ ] Joined desired+actual GraphQL query — pending Step 2.
- [ ] `nctl status` GraphQL introspection probe — pending Steps 3–4.
- [x] `uv run` test suite passes in nintent (203 passed); nctl's suite is unaffected by this step.

Next: push this `nintent` commit (needs user), rebuild the dev Nautobot container, and run Step 2's
introspection query.
