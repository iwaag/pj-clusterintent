# hosts_intent.yml implementation report: steps 7-8

## Scope Completed

Implemented the non-runtime parts of Step 7 and Step 8 from `plan.md`.

Completed:

- Documented the generated bootstrap inventory workflow in `ansible_agdev`.
- Updated admin setup docs to use `inventories/generated` instead of
  `inventories/production`.
- Documented `nauto/seed/intent_sources.yaml` as the nintent source for
  name-reserved DesiredNodes and mDNS endpoints.
- Left old production inventory files unreferenced by the default path.

No live Nautobot import/export was run.
No Ansible playbook was executed against hosts.

## Files Changed

`ansible_agdev`:

- `README.md`
- `README_ADMIN.md`

`nauto`:

- `README.md`

## Workflow Now Documented

The operator flow documented in `ansible_agdev/README.md` is:

```bash
NAUTOBOT_URL=https://nautobot.example.local \
NAUTOBOT_TOKEN=your-nautobot-api-token \
ansible-playbook playbooks/export_nintent_hosts_intent.yml
```

This writes:

```text
inventories/generated/hosts_intent.yml
```

Then bootstrap collection can use the generated default inventory:

```bash
NAUTOBOT_URL=https://nautobot.example.local \
NAUTOBOT_TOKEN=your-nautobot-api-token \
ansible-playbook playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

The generated file is ignored by Git. The generated inventory `group_vars` and
vault example are tracked.

## Cleanup Result

`ansible.cfg` already points at:

```text
inventories/generated/hosts_intent.yml
```

The old handwritten inventory:

```text
inventories/production/hosts.yml
```

is no longer the default inventory and is documented as obsolete in
`README_ADMIN.md`.

The old file was not deleted in this pass because there has not yet been a real
environment-backed end-to-end run. The implemented state avoids compatibility
code paths and default references, while keeping physical deletion as a final
operator cleanup after successful import/export/collection.

## Verification

No runtime verification was performed in this pass, per instruction.

Only text search was used to check that the main docs now point at generated
bootstrap inventory paths.

## Remaining Environment-Backed Work

These are intentionally not executed here:

1. Sync/deploy the nintent code with the new `Export Ansible Hosts Intent` Job.
2. Sync the nauto repository so `seed/intent_sources.yaml` is available.
3. Run nintent `Import Intent Sources`.
4. Run `ansible_agdev/playbooks/export_nintent_hosts_intent.yml`.
5. Inspect `inventories/generated/hosts_intent.yml`.
6. Run nodeutils collection and nauto ingest.
7. After a successful run, delete or archive
   `ansible_agdev/inventories/production/hosts.yml` and related production
   group vars if no operator still needs them for manual rollback.
