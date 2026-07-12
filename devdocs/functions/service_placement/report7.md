# Step 7 Report: Production Export Workflow

## Summary

Completed Step 7. Added the Nautobot `Export Production Inventory` Job that validates the canonical
deployment-profile JSON + digest, builds the pure composer inputs from persisted nintent and Nautobot
state, and publishes `production.yml` plus a generation-addressed JSON report. Added the
`export_nintent_production.yml` localhost playbook that serializes the profile map, runs the Job,
downloads and cross-verifies both artifacts, validates the inventory, installs the immutable report,
and atomically replaces the local `production.yml`. Factored the shared JobResult/FileProxy transport
out of both export playbooks, and added a `make pipeline` target for the full refresh.

The composer itself (Step 6) was unchanged; this step is the Job + Ansible workflow that drives it.

## Status of plan items

| # | Item | Outcome |
|---|------|---------|
| 1 | Job accepts canonical profile JSON + digest, validates, calls composer, publishes inventory + report | `ExportProductionInventory` in `jobs.py` |
| 2 | Ansible playbook: serialize+digest, run Job, download both, verify gen id/digest/schema, validate, install report, atomic replace | `export_nintent_production.yml` |
| 3 | Factor shared JobResult/FileProxy polling + download out of both playbooks | `tasks/nautobot_run_job.yml`, `tasks/nautobot_download_file.yml`; both playbooks include them |
| 4 | Never delete/truncate previous valid inventory on Job/download/schema/validation failure | asserts abort before any write; install uses staged validate → report install → atomic mv with rescue |
| 5 | Concise command/Make target for the full pipeline | `Makefile` `pipeline: bootstrap-inventory collect-ingest production-inventory` |

## Changes

### nintent/nautobot_intent_catalog/jobs.py

- New imports: `uuid`, `collections.defaultdict`, the `production_inventory` input dataclasses and
  renderers, `read_actual_facts`, and `parse_profile_job_input`.
- `ExportProductionInventory(Job)`: two `StringVar` inputs (`deployment_profiles_json`,
  `deployment_profiles_digest`). `run` validates the payload via `parse_profile_job_input` (a bad
  payload or digest mismatch fails the whole Job before any file is written), assembles node inputs,
  generates a `uuid4` generation id and a timezone-aware `generated_at`, calls
  `compose_production_inventory`, and `create_file`s `production.yml` and `<generation_id>.json`. It
  logs the summary/provenance and warns on skipped hosts and drift. Registered in the `jobs` tuple.
- Module-level builder helpers: `_device_custom_fields` (reads `custom_field_data`/`cf`),
  `_production_endpoint_input`, `_production_operational_config_input`, `_production_realized_state`
  (Device → actual facts via `read_actual_facts`; realized VM → `virtual_machine` so the composer
  skips it with `unsupported_actual_type`; otherwise `None`), and `_build_production_node_inputs`
  (one operational-config map + placements grouped by node, joined into `NodeInput`s ordered by slug).

### ansible_agdev/playbooks/tasks/nautobot_run_job.yml (new)

- Shared transport: look up a Job by name, run it with a `job_data` mapping, resolve the JobResult id
  from body or URL, poll until terminal, assert success. Output: `nautobot_job_result_id`. Poll
  retries/delay are overridable via `nautobot_job_poll_retries`/`nautobot_job_poll_delay`.

### ansible_agdev/playbooks/tasks/nautobot_download_file.yml (new)

- Shared transport: look up the JobResult's FileProxy by name + regex, download it, expose
  `nautobot_download_content`.

### ansible_agdev/playbooks/export_nintent_hosts_intent.yml

- Refactored to `include_tasks` the two shared task files instead of the inlined lookup/run/poll/
  file-proxy/download tasks. The schema assert and staged-validate-then-atomic-replace behavior from
  Step 4 are unchanged. Poll vars renamed to the shared `nautobot_job_poll_*` names.

### ansible_agdev/playbooks/export_nintent_production.yml (new)

- Serializes `deployment_profiles` to canonical JSON with
  `to_json(sort_keys=true, separators=[',', ':'], ensure_ascii=false, allow_nan=false)` and computes
  its SHA-256 with `hash('sha256')` — the exact byte/digest contract already proven by
  `verify_deployment_profiles_contract.yml` against Python's `canonical_json`.
- Runs the Job with both inputs, downloads `production.yml`, parses `all.vars`, asserts the schema
  version, profile digest, and report path match the request, then downloads the generation-addressed
  `<generation_id>.json` report and asserts it shares the same generation id, digest, and schema.
- Install block: stage `production.yml`, validate it with `ansible-inventory --list`, install the
  immutable report under `production.reports/<generation_id>.json` (`force: false`), then atomically
  `mv` the staged file over `production.yml`. The rescue removes the staging file and fails, leaving
  the previous `production.yml` untouched.

### ansible_agdev/Makefile (new)

- `pipeline` runs `bootstrap-inventory` → `collect-ingest` → `production-inventory`. Individual
  targets and `verify-profiles` are also exposed. `ANSIBLE_PLAYBOOK` is overridable.

### ansible_agdev/README.md

- Documented `export_nintent_production.yml`, the shared transport task files, and `make pipeline`.

## Verification

- `python3 -m py_compile jobs.py` and `import nautobot_intent_catalog.jobs` succeed (Nautobot absent →
  `jobs = ()`, builder helpers present).
- Full nintent suite: 170 tests pass (unchanged from Step 6; the Job is a thin Django/Nautobot
  adapter over the already-tested pure composer, so it has no separate unit test).
- All four playbook/task YAML files parse, and `ansible-playbook --syntax-check` passes for both
  export playbooks (only the expected "generated inventory not yet present" warning; the earlier vault
  error was an `ansible.cfg` password-file path, not a playbook defect — `vars/nautobot.yml` is not
  vaulted).
- `git check-ignore` confirms `production.yml`, `production.reports/*`, and the staging file are
  ignored by the existing `inventories/generated/*` rule.
- No execution environment is available, so there is no live Job run or end-to-end playbook execution.

## Exit Criterion Status

Met. The production playbooks consume a validated local snapshot: `production.yml` is downloaded,
cross-checked against its report and the requested profile digest/schema, validated with
`ansible-inventory --list`, and atomically installed, with the previous file preserved on any
failure. Composition happens inside the Job, so there is no implicit inventory-time Nautobot API call
during playbook parsing.

## Notes

- The Job is intentionally a thin adapter: all contract logic lives in the pure, fully unit-tested
  `production_inventory` and `production_inventory_contract` modules, which the Job and the composer
  share. `_build_production_node_inputs` is the only new Nautobot-coupled surface.
- Report cleanup ("remove unreferenced old reports after a successful replacement") is intentionally
  not implemented; the plan marks it optional ("may"), and generation-addressed reports are immutable
  and small. The active inventory always references an installed report.
- Step 8 will point production execution explicitly at `inventories/generated/production.yml` and add
  `group_vars/all/main.yml` connection/`ansible_user` resolution; this step only produces and installs
  the artifact.
