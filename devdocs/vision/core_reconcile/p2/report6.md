# Phase 2 Report — Step 6 (delete the nintent proto-engines)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 6 up to the local commit boundary.

## What changed

`nintent` is now the desired-state ledger and transactional Job layer; production composition and
desired-vs-actual evaluation no longer exist there.

- Deleted the `ExportProductionInventory` and `SyncDeploymentProfiles` Jobs, the
  `EvaluateNodeIntent`, `EvaluateEndpointIntent`, and `EvaluateServiceIntent` Jobs, and their Job
  registration/imports/helpers.
- Deleted `production_inventory.py`, `production_inventory_contract.py`, `actual_facts.py`,
  `deployment_profiles.py`, and `evaluations.py`. Their production/evaluation/contract test suites
  and fixture were deleted as already-ported coverage lives in `nctl`.
- Removed `IntentEvaluation` and `DeploymentProfileProjection` from the ORM and added migration
  `0008_remove_proto_drift_models.py`, which deletes both tables after migration 0007.
- Removed the evaluation list/detail/edit/delete UI (model form, filter, table, views, URLs,
  navigation, and detail template).
- Removed `ReconcileDesiredIPAMIntent`'s evaluation upsert side effect and its evaluation counters.
  The IP-address plan/apply behavior and `ipam-reconcile-summary.json` output remain intact.
- Bumped both package metadata and Nautobot App metadata from 0.5.0 to 0.6.0.

The strict DesiredService/DesiredEndpoint reference validation used by the YAML ledger importer was
not production-composition logic. The small surviving subset (`ContractError`, deterministic JSON,
reference-shape validation, and unique-reference checking) moved to `intent_contract.py`. This
avoids retaining the deleted production byte-contract module merely for unrelated import-boundary
rules.

## Deployment-profile projection consumer found during deletion

The implementation-time grep required by Step 6 found one consumer beyond the sync Job:
`DesiredServicePlacementQuickAddView` loaded `DeploymentProfileProjection` to build a dynamic
profile/config form. Once the projection and the Ansible→Nautobot byte contract are removed, that
form has no valid source.

The projection-dependent Quick Service Placement form/view/URL/navigation/template and its
operation were therefore deleted in the same boundary. The ordinary `DesiredServicePlacement`
model, importer, GraphQL exposure, CRUD form/views, and templates remain. This preserves the ledger
schema while removing the UI path that would otherwise import a deleted module or present an empty
profile picker. Documentation cleanup for this UI and the other removed surfaces remains Step 8.

## Verification

- `uv run python -m unittest discover -s nautobot_intent_catalog/tests` in `nintent` — **92 passed**.
- `uv run python -m compileall -q nautobot_intent_catalog` — passed.
- `git diff --check` in `nintent` — passed.
- `uv run python -c "import nautobot_intent_catalog as n; print(n.IntentCatalogConfig.version)"`
  — printed **0.6.0**.
- `uv run pytest -q` in `nctl` — **236 passed**. This is the consumer-side regression gate showing
  the Step 2/4 GraphQL queries and render/drift logic do not depend on the deleted models/modules.
- A final source grep found the removed names only in historical migrations 0001/0006 and the new
  deletion migration 0008, as expected.

The local package has no Django/Nautobot dependency, so `makemigrations --check` and applying
migration 0008 cannot be proven in that environment. Those checks belong to the single deployment
cycle below.

## Deployment gate (not run yet)

Per `.local/localenv_memo.md`, the running Nautobot installs nintent from GitHub rather than mounting
this checkout. The remaining Step 6 live verification therefore requires this sequence after the
user commits/pushes the nintent change:

1. Rebuild the dev Nautobot image with `--no-cache` and restart web/worker/scheduler.
2. Run `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run` and migrate.
3. Confirm Job discovery contains neither production/sync nor Evaluate Jobs.
4. Confirm `nctl status`, `nctl drift`, `nctl render dnsmasq`, and `nctl render production` remain
   healthy against the migrated instance.

No rebuild/restart was attempted before push: it would reinstall the old GitHub revision and could
not validate these local changes.

## Commit boundary

This is one self-contained `nintent` boundary: both persisted proto-engines, their projection and UI
surfaces, the IPAM evaluation side effect, and the obsolete pure-processing modules are removed;
migration 0008 and the 0.6.0 bump are included; all locally runnable `nintent` and `nctl` tests are
green.

No commit was created. Step 7 (`ansible_agdev` byte-contract playbook/task deletion) has not started,
because the suggested order makes it a separate submodule commit after this nintent push/deployment
gate.
