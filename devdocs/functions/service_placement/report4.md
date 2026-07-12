# Step 4 Report: Simplify the Bootstrap Inventory

## Summary

Completed Step 4 of the service-placement redesign. The bootstrap inventory now carries only
`ssh_hosts` plus mDNS reachability and stable identity metadata, the breaking contract is marked by
a bumped schema version, and the Ansible download playbook installs the inventory through an atomic
staging → validate → replace flow that preserves the previous valid file on failure.

No backward-compatibility artifacts were kept: the old schema version is replaced outright (not
dual-accepted), and the previous non-atomic direct-write path was removed rather than retained.

## Status of plan items

Step 4 has five plan items. Items 1 and 2 (drop service placement / service groups and desired
`host_os` from the bootstrap export) were already satisfied as a side effect of the Step 3 legacy
removal in `ansible_inventory.py`; they were re-verified here. Items 3–5 were the actual work of this
step.

| # | Item | Outcome |
|---|------|---------|
| 1 | Bootstrap export emits only `ssh_hosts` + mDNS + identity | Already done in Step 3; verified by tests |
| 2 | Remove desired `host_os` from bootstrap host vars | Already done in Step 3; verified by tests |
| 3 | Increment bootstrap schema version (breaking) | Bumped `1.0` → `2.0` |
| 4 | Update Job, playbook, fixtures, tests to new schema; delete old-schema code | Done; no dual-version acceptance |
| 5 | Atomic local replacement (temp → validate → replace) | Reworked playbook into a block/rescue staging flow |

## Changes

### nintent/nautobot_intent_catalog/ansible_inventory.py

- Bumped `ANSIBLE_HOSTS_INTENT_SCHEMA_VERSION` from `"1.0"` to `"2.0"`. This is the single source of
  truth consumed by both the YAML header (`# schema_version:`) and the JSON payload, so the Job
  output and report both advance together.

### nintent/nautobot_intent_catalog/jobs.py

- `ExportAnsibleHostsIntent.include_skipped` description changed from "Include skipped node and group
  details" to "Include skipped node details" — the bootstrap export no longer produces any groups, so
  the stale "group" wording was removed rather than left as a misleading hint.

### nintent/nautobot_intent_catalog/tests/test_ansible_inventory.py

- Updated the two schema-version assertions (`# schema_version: 2.0` in the rendered YAML and
  `payload["schema_version"] == "2.0"` in the JSON payload). No old-schema assertions were retained.
- The existing contract tests already assert the simplified shape (only `ssh_hosts`, no service
  groups, no `host_os`, no `skipped_groups` summary field); they continue to pass unchanged.

### ansible_agdev/playbooks/export_nintent_hosts_intent.yml

- `nintent_hosts_intent_expected_schema_version` bumped `"1.0"` → `"2.0"`. The schema assertion on the
  downloaded content now requires the new version, so an old-schema artifact is rejected outright.
- Added `nintent_hosts_intent_staging_file` (`.hosts_intent.yml.staging` inside the generated dir, so
  the final rename stays on the same filesystem and is therefore atomic).
- Replaced the previous "write directly to the live file, then validate" tasks with an atomic
  `block`/`rescue`:
  1. write the downloaded content to the staging file;
  2. validate the staging file with `ansible-inventory --list`;
  3. atomically `mv` staging → `hosts_intent.yml` only after validation succeeds.
  On any failure the `rescue` removes the staging file and fails with an explicit message; the
  previous `hosts_intent.yml` is never touched before a validated replacement is ready. The staging
  dir is already covered by `.gitignore` (`inventories/generated/*`), so the staging file is not
  committed.

### ansible_agdev/README.md

- Updated the `export_nintent_hosts_intent.yml` description to schema `2.0`, to describe the
  staged-validate-then-atomic-replace behavior and the preserve-previous-file-on-failure guarantee,
  and to note that the bootstrap inventory carries no service groups or desired `host_os`.

## Verification

- `python3 -m unittest nautobot_intent_catalog.tests.test_ansible_inventory` — 12 tests pass.
- `python3 -c "yaml.safe_load_all(...)"` confirms the playbook YAML parses. `ansible-playbook
  --syntax-check` could not run here because the environment has no Ansible Vault password file
  (`vars/nautobot.yml`); this is an environment limitation, not a playbook defect, and there is no
  execution environment available for a live run.

## Exit Criterion Status

Met. Bootstrap collection succeeds without carrying production service groups and without presenting
desired facts as observed facts: the export contains only `ssh_hosts` with mDNS reachability and
stable nintent identity metadata, the breaking contract is versioned as schema `2.0` with no
dual-version reader, and the download playbook installs the inventory atomically while preserving the
last valid file on validation failure.

## Notes

- No old-schema fixtures existed to delete; the only nintent test fixture
  (`production_inventory_contract_cases.yml`) belongs to the production composer (Steps 1/6), not the
  bootstrap path, and was left untouched.
- The `mv`-based atomic replace assumes the staging file and the destination live in the same
  directory (guaranteed here, both under `inventories/generated/`), which keeps the rename atomic on a
  single filesystem. A future change that relocates either path must preserve that invariant.
