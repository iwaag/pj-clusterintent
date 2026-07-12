# Batch Nodeutils Ingest Report: Steps 1-4

## Scope

Implemented steps 1 through 4 from `plan.md`.

This change removes Nautobot-server-local report ingestion from the runtime
contract and replaces it with one API-submitted batch payload.

## Implemented Changes

### Step 1: Nautobot Job input contract

Updated `nauto/jobs/ingest_nodeutils_inventory.py`:

- Removed `report_path`.
- Removed `report_text`.
- Removed server-side report file and directory reading.
- Added `report_batch` as the only external report input.
- Added strict batch parsing for this shape:

```yaml
reports:
  - source: agpc
    text: |
      {"schema_version": "nodeutils.inventory.v1", "...": "..."}
```

Batch entries must be mappings with non-empty string `source` and `text`
fields.

### Step 2: Per-report isolation and summary logging

Kept the existing per-report validation behavior:

- report parse failures skip only that report
- stale reports skip only that report
- unsupported schemas skip only that report
- oversized reports skip only that report

Added batch summary logging:

- total report count
- ingested report count
- skipped report count
- dry-run state

Dry-run behavior still rolls back the transaction after evaluating the batch.

### Step 3: Ansible API batch ingest

Updated `ansible_agdev/playbooks/collect_nodeutils_and_ingest_nautobot.yml`:

- Removed the local staging directory setup.
- Removed `fetch` to the Ansible control node.
- Removed the entire Nautobot-server copy play.
- Added `slurp` from each target host's `nodeutils_output_path`.
- Builds one `report_batch` on localhost from hostvars.
- Sends one Nautobot Job API request with `report_batch`.
- Keeps raw report content hidden with `no_log: true`.

The playbook now depends only on Nautobot API reachability, not SSH or file
access to the Nautobot server or container host.

### Step 4: Documentation

Updated:

- `ansible_agdev/README.md`
- `ansible_agdev/README_ADMIN.md`
- `nauto/README.md`

The docs now describe API batch ingest and no longer present copying reports to
the Nautobot server as the primary workflow.

## Verification

Passed:

```bash
python3 -m py_compile nauto/jobs/ingest_nodeutils_inventory.py
```

Passed:

```bash
cd ansible_agdev
ANSIBLE_CONFIG=/tmp/empty-ansible.cfg \
ANSIBLE_ROLES_PATH=roles \
ansible-playbook -i inventories/production/hosts.yml \
  --syntax-check playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

Passed with no matches:

```bash
rg -n "report_path|report_text|nodeutils_report_local_dir|nautobot_nodeutils_report_dir|nautobot_server_group|Copy nodeutils reports|/var/tmp/nodeutils-reports" \
  nauto ansible_agdev -g '*.py' -g '*.yml' -g '*.yaml' -g '*.md'
```

## Notes

The normal `ansible-playbook --syntax-check` command reads
`ansible_agdev/ansible.cfg`, which points at `~/.ansible/vault_pass.txt`.
That file is not present in this environment, so syntax-check was run with a
temporary empty Ansible config and explicit `ANSIBLE_ROLES_PATH=roles`.

No end-to-end Nautobot API dry run was executed because this environment does
not provide a reachable Nautobot URL and token.

## Remaining Work

Continue with step 5:

- Add or update tests for `report_batch` parsing.
- Cover malformed batch payloads.
- Cover mixed valid/invalid report batches.
- Cover per-entry `max_report_bytes` enforcement.

Then complete step 6:

- Re-run repository-wide cleanup searches.
- Remove any remaining obsolete copy/staging references that appear outside the
  runtime docs.

## Follow-up Update

The Ansible playbook default was changed after runtime feedback:

- `nautobot_ingest_dry_run` now defaults to `false`.
- Successful Ansible runs are expected to apply Nautobot Device changes.
- Operators can still set `-e nautobot_ingest_dry_run=true` for production
  rollouts, policy changes, or first-time validation.

This keeps Nautobot Job dry-run available as a safety tool without making this
Ansible automation report success while leaving no committed result.
