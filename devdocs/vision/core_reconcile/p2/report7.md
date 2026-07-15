# Phase 2 Report — Step 6 deployment gate and Step 7 (`ansible_agdev` cleanup)

Date: 2026-07-15. Completes the live deployment gate left in
[report6.md](report6.md) and implements [p2/plan.md](plan.md) Step 7 up to its commit boundary.

## Step 6 live deployment gate

After the user pushed nintent commit `69f9843e6bb236fce71f705bf7643c1412672832`, the dev Nautobot
images were rebuilt with `docker compose --env-file ../.env build --no-cache`. The build log pinned
that Git commit and installed `nautobot-intent-catalog-0.6.0`. Web, worker, and scheduler were then
force-recreated and all three returned healthy.

Migration and Job verification:

- `showmigrations nautobot_intent_catalog` showed migrations 0001 through
  `0008_remove_proto_drift_models` applied.
- The installed App reported version `0.6.0`.
- Job discovery returned only `PreviewIntentSourceAnalysis`, `ImportIntentSources`,
  `AnalyzeIntentSources`, `ExportAnsibleHostsIntent`, and `ReconcileDesiredIPAMIntent`.
  The production export/sync and all three Evaluate Jobs are absent.

Live nctl regression with the configured dev API token:

- `nctl status --json` — `ok: true`, Nautobot 3.1.3 authenticated, intent GraphQL present.
- `nctl drift --json` — `ok: true`; five nodes, summary `converged=3`, `unknown=2`, severity
  summary `error=2`, `warning=9`, `info=0`, unchanged from Step 5.
- `nctl render dnsmasq --json` — `ok: true`; 5 DNS records, 3 DHCP reservations, 1 DHCP range.
- `nctl render production --json` — `ok: true`; valid schema 1.0 inventory/report. The current
  dataset has no operational configs/placements, so all production counts are zero.

### `makemigrations --check` finding

`nautobot-server makemigrations nautobot_intent_catalog --check --dry-run` did not return clean. It
proposed a migration 0009 adding inherited `tags` fields and altering inherited `id` and
`_custom_field_data` fields on every surviving PrimaryModel. It did **not** propose any further
change for `IntentEvaluation` or `DeploymentProfileProjection`; migration 0008 itself is applied.

This is an existing model-state alignment issue with the Nautobot 3.1 PrimaryModel inheritance
surface, not a missing Step 6 deletion operation. No generated migration was written into the
installed container, and broad unrelated model migrations were not added to this commit boundary.

## Step 7 cleanup

Deleted the obsolete Ansible→Nautobot production/profile byte-contract path:

- `playbooks/nautobot/export_nintent_production.yml`
- `playbooks/nautobot/verify_deployment_profiles_contract.yml`
- `playbooks/nautobot/sync_nintent_deployment_profiles.yml`
- `playbooks/tasks/nintent_serialize_deployment_profiles.yml`

`vars/deployment_profiles.yml` remains authoritative and is read directly by nctl.

The Makefile retains the useful `production-inventory` and `pipeline` interfaces, but
`production-inventory` now runs:

```text
uv run --project ../nctl nctl render production --config ../nctl.toml --out inventories/generated
```

The obsolete `verify-profiles` target was removed. `README.md`, `README_DEV.md`, and
`docs/production_inventory_contract.md` now describe direct nctl composition, local profile digest
provenance, atomic validation/install, and the absence of export/sync Jobs, projection storage, and
the cross-language byte transport.

## Verification

- Final grep found no references in `ansible_agdev` to the four deleted files, the two deleted Job
  names, or their `deployment_profiles_json` / `deployment_profiles_digest` inputs.
- `git diff --check` in `ansible_agdev` — passed.
- `make -n production-inventory` — resolved to the expected nctl command.
- `make production-inventory` with the dev token — passed and atomically installed a validated
  current `production.yml` plus its report; current counts are all zero as noted above.
- `ansible-playbook --syntax-check playbooks/nautobot/export_nintent_hosts_intent.yml` — passed.
- `ansible-playbook --syntax-check playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml`
  — passed.

## Deferred Phase 1 live apply

`ping -c 1 -W 1000 agdnsmasq.local` failed with `Unknown host`. Therefore the planned
`nctl apply dnsmasq` check/diff and real apply remain environment-gated exactly as allowed by Step
7. The render path itself passed after the nintent 0.6.0 deletion deployment, but no actuation was
attempted without a resolvable target.

## Commit boundary

This is one self-contained `ansible_agdev` boundary: the four obsolete transport files are gone,
the Make pipeline delegates production composition to nctl, and the ownership documentation is
updated and verified. No commit was created. Step 8's broader nctl/nintent/parent documentation and
Phase 2 closeout have not started.
