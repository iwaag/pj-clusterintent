# cull_desired_dependency — Implementation Plan

Implements [devdocs/vision/minimize_system/opinion1.md](../../opinion1.md). Read it first; this
document does not restate the evidence.

Goal: delete `DesiredDependency` end to end, plus the dead `requirements` stub that sits in the same
evaluator.

## Why this is worth doing

The braindump→intent step is an agent translating free text into structured rows, non-deterministically.
Every schema surface that *looks* authoritative but drives no outcome is a place that translation can go
wrong at zero cost to itself: the agent writes plausible dependency rows, nothing rejects them, nothing
acts on them, and the drift channel fills with warnings no action can clear. Removing the surface removes
the wrong answer from the answer space.

Existing rows carry no value worth protecting — current intent and actual data are exploration filler.
Delete freely. No data migration, no compatibility shim, no deprecation window.

This is a coordinated breaking change under [README_DEV.md:87-104](../../../../../README_DEV.md#L87-L104):
update every producer and consumer to the final contract in one rollout and delete the superseded
implementation. Leave no dual reader, shadow field, deprecated alias, or legacy serializer behind.
Django migration history and past reports are not artifacts — keep them.

## Ordering constraint (the only hard one)

**nctl first, then nintent.** nctl's GraphQL query selects `desired_dependencies`
([nctl/src/nctl_core/sources/desired.py:142-152](../../../../../nctl/src/nctl_core/sources/desired.py#L142)).
If nintent drops the model first, every `nctl drift` against the running instance fails until nctl catches
up. Land Step 1 before deploying Step 2.

Everything else — how to split commits, how to restructure tests, whether to do the whole thing in one
migration — is the implementer's call.

## Step 1 — nctl

Remove:

- `sources/desired.py` — the `desired_dependencies` GraphQL block, the `DesiredDependency` model,
  `_build_dependency`, `DesiredSnapshot.dependencies` (line 320).
- `drift/evaluation.py` — `_dependency_facts`, and `dependencies` / `dependency_counts` /
  `requirements` from `_expected_service_facts` (lines 56-92).
- `drift/service_evaluation.py` — the `dependencies` and `resolved_services_by_id` parameters, the
  dependency loop, `dependency_counts` and `requirements_present` from the summary (40-41).
- `drift/evaluation_snapshot.py:157-161` — `dependencies_by_service` and the two kwargs at the call site.
- `reconcile/classify.py:140` — the `unresolved_dependency` code.
- `DesiredService.requirements` in `sources/desired.py:268-270` (the stub kept "until the evaluator
  contract is independently simplified" — this is that moment).

`evaluation_scope` is set in **two** places and both name dependencies:
`service_evaluation.py:42` (`"service_lifecycle_requirements_dependencies"`) and
`evaluation_snapshot.py:200` (`"service_lifecycle_dependencies_and_placements"`). Rename both.

Tests: 11 files under `nctl/tests/` reference `desired_dependencies` / `DesiredDependency`. Most carry
only `"desired_dependencies": []` fixture noise; delete the key. `test_drift_evaluation.py` and
`test_drift_evaluation_snapshot.py` have real assertions to remove.

**No envelope bump is needed.** Verified 2026-07-31: `deterministic_summary` never reaches
`drift_render.py`, so `dependency_counts` / `requirements_present` are not part of the published
`nctl.drift.v1` payload documented at
[nctl/docs/output-format.md:82](../../../../../nctl/docs/output-format.md#L82), and
`tests/test_current_consumer_contracts.py` has no dependency assertions. Re-check both before
concluding the same; if the shape does move, [nctl/docs/compatibility.md](../../../../../nctl/docs/compatibility.md)
requires writer + every current reader + docs + the contract test to change in one rollout, with the
version label advanced rather than duplicated.

One genuine carve-out exists: compatibility.md keeps `nctl ops show` able to read **existing on-disk
operation evidence**. Run it against an operation directory under `<events.log_dir>/` that predates the
change. If it still renders, do nothing. Only if it breaks, add the smallest historical reader — never a
live writer or a restored field.

Verify: `cd nctl && uv run pytest -q --durations=20`.

## Step 2 — nintent

Remove (surface list in [opinion1.md §3](../../opinion1.md)):

- `models.py:159-213` — the `DesiredDependency` class. The `DesiredService.dependencies` reverse
  relation goes with it.
- `batch.py` — `desired_dependency` from `KIND_ORDER` (13), `_KEYS` (50), `_FIELDS` (63),
  `_CREATE_REQUIRED` (75), the model map (202-206), `resolved_service` / `source_service` in
  `_REFERENCE_KIND` (219), and the two `desired_service` cascade entries (276).
- `api/views.py:65` — `_BATCH_MODELS` entry.
- `views.py` — `DesiredDependencyListView` / `DesiredDependencyView` (77-88) and imports (10, 23, 36).
- `urls.py:15-16`; `navigation.py:37-40` (the "Dependencies" nav item).
- `tables.py` — `DesiredDependencyTable` (71-92), and `dependency_count` on `DesiredServiceTable`
  (47-51, 60, 67).
- `filters.py` — `DesiredDependencyFilterSet` (66-88) and the import (14).
- `templates/…/desireddependency.html`; the Desired Dependencies panel in `desiredservice.html:111-157`.
- Tests: `tests/test_ui_contract.py`, `tests/factories.py`, `tests/test_templates.py`.
- One migration dropping the table. Rows go with it — no pre-deletion batch op needed.
- Docs: `CONCEPT.md` — the bullet at 13, the import sentence at 36, the `DesiredDependency` chapter
  (80-101), and the Current Boundaries entry (324). Also `README_DEV.md` and `DEVLOG_PICKUP.md`.
- `README_QUICK.md:36` — the "Jobs retained in nintent" table still lists `Analyze Intent Sources`,
  which writes "`DesiredDependency` rows". That Job does not exist; `jobs.py` holds only
  `ReconcileDesiredIPAMIntent`. Delete the row — it is precisely the kind of leftover artifact the
  policy forbids.

## Step 3 — deploy and confirm

nintent deploys from GitHub, not from the local checkout: commit → **ask the user to push** → rebuild.
Use `docker compose build --no-cache` and check the log for the resolved commit SHA — the build silently
caches a stale nintent otherwise.

Then: `nautobot-server migrate` in the container, restart, and run `nctl drift --json`.

## Verification gates

Per the matrix in [README_DEV.md:48-62](../../../../../README_DEV.md#L48-L62):

| gate | where | command |
|---|---|---|
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` |
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` |
| Nautobot runtime clean | repo root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |

The runtime gate is **required**, not optional: this change adds a migration and alters the App, which
is what rows 56-57 of that matrix cover. The Django-free suite loads neither Django nor Nautobot, so it
cannot prove the migration applies or the UI still renders. Record the gate's reported `cases=` count —
a green exit with zero collected cases proves nothing. If the expected-skip count for the fast suite
moves off **10**, update [README_DEV.md:52](../../../../../README_DEV.md#L52).

Compute conformance, OpenSSH, and Ansible gates are not required — this change touches none of those
boundaries.

## Exit criteria

- `grep -ri "desireddependency\|desired_dependency\|unresolved_dependency\|requirements_present"` over
  `nintent/`, `nctl/src/`, `nctl/tests/`, `nctl/docs/` returns only migration files and historical
  devdocs.
- All three gates above pass, with the runtime gate's `cases=` count recorded.
- `nctl drift` runs clean against the rebuilt instance and emits no `unresolved_dependency` finding.
- `nctl ops show` still reads a pre-change operation directory.
- The Nautobot UI has no Dependencies nav item and the service detail page renders.
- Every worktree is clean.

Report status in the vocabulary of [README_DEV.md:282-300](../../../../../README_DEV.md#L282-L300).
`implemented, not deployed` is the honest state until the container is rebuilt and migrated; only claim
`complete` once every criterion above was actually exercised.

## Notes for the implementer

- The two live rows (`blender-tool`, `vdbmat-openvdb-cycles` on `pj-voxel3dprint`) express *host and
  artifact requirements* — "this binary must exist", "this image must be available". If that intent is
  worth keeping, it belongs in `DesiredServicePlacement.config` under the `manual_toolchain` profile, not
  in a resurrected dependency table. Ask the user; don't decide silently. Losing it is an acceptable
  outcome.
- Real actuation ordering already lives in `deployment_profile_reconciliation.<profile>.dependencies`
  ([ansible_agdev/vars/deployment_profiles.yml](../../../../../ansible_agdev/vars/deployment_profiles.yml))
  and is cycle-checked. Nothing in this plan touches it — that graph is the surviving one.
- After this lands, `lifecycle` is the only service-level drift signal left. Don't remove it as
  collateral.
