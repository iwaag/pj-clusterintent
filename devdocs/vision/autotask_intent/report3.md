# autotask_intent — Step 3 Report: Drift evaluation for checks + `cron_task` profile

Status: **complete** (per plan.md Step 3 acceptance criteria).

## What was implemented

`nctl/src/nctl_core/drift/service_placement.py` (`evaluate_active_placement`):

- Check-observed entries reuse the existing gap vocabulary; no new codes.
  - Any `file_exists` result with `status != "present"` in the entry's
    `checks` list — or an entry `state` of `missing` — produces
    `service_missing`, **including for manual placements**: the entry itself
    is positive evidence the check ran, so its failure must not read as
    presence. A richer running-state detection (e.g. `source: process`)
    cannot mask a failed existence proof.
  - `state == "present"` (all existence checks passed; only emitted by
    check-observed observe-only profiles) counts as convergence and no
    longer falls into `service_not_running`. Action profiles never emit
    check-only states, so their `installed`/`failed` handling is unchanged.
  - Executed check results are surfaced as `observed_checks` evidence in the
    placement report.

`ansible_agdev/vars/deployment_profiles.yml`:

- New `cron_task` profile: `group: cron_task_hosts`,
  `config_schema_version: "1"`, one required string config key
  `script_path` (mapped to `cron_task_script_path`).
- New reconciliation entry: `observe_only: true`,
  `checks: [{kind: file_exists, path_from_config: script_path}]`.
- `~` expansion owner (plan Step 4 decision, documented here): nctl renders
  the configured path verbatim (validated absolute or `~/`-relative);
  **nodeutils expands `~` at observation time** via `os.path.expanduser`,
  because it runs as the login user on the target node. The observed
  evidence records the expanded path.

## Verification

- New real control-loop test (README_DEV lesson 8),
  `nctl/tests/test_cron_task_control_loop.py`: loads the **real repo**
  profile metadata, renders hints for a `cron_task` placement with
  `config.script_path` → asserts the config-resolved `file_exists` hint →
  simulated observation without the file → `service_missing` (with
  `observed_checks` evidence) and `build_plan` planning **zero actions**
  (observe_only stays visible as `unsupported`) → simulated observation with
  the file → `satisfied`, no gaps. Plus a focused case: a running process
  with a failed existence check is still `service_missing`.
- nctl ordinary gate (`nctl/`): `uv run pytest -q` → **1275 passed**.
- Scratch acceptance (plan): declared `heartbeat-cron` (`DesiredService`) +
  `heartbeat-cron-agpc` placement (profile `cron_task`,
  `config.script_path: ~/mycron/heartbeat.sh`) via
  `nctl desired apply -f .local/desired-state.yaml` (previewed
  `create: 2, update: 0`, then `--yes` → `committed: {create: 2}`).
  `nctl drift --json` now reports for `heartbeat-cron`:
  `status: drifting`, code `service_missing`, expected placement on `agpc`
  with `deployment_profile: cron_task` — exactly the negative the plan
  requires before any script is placed.

## Deviations and findings (recorded, not blocking)

- The stale `.local/desired-state.yaml` had drifted from the DB (agdnsmasq
  endpoint `gateway_address`/`ip_address` prefix). The DB is the desired
  correct source; the file was re-synced to it before applying, keeping the
  apply a pure 2-create.
- **Defect found in the export→apply round-trip:** `nctl desired export`
  emits `slug` (services) and `desired_service`/`instance_name` (placements)
  in both `key:` and `values:`; the batch **create** path then fails with
  HTTP 409 `TypeError: ... got multiple values for keyword argument`.
  Upsert-as-update tolerates it, so this only bites when re-applying an
  export to a database missing the row — i.e. exactly the documented
  recovery scenario. Worked around by keeping identity fields only under
  `key:`. Deferred to Step 5's follow-up list.
- Unrelated cluster drift now visible (`service_observation_stale` for
  dnsmasq/ollama/node-agent + cascading binding gaps): the last nodeutils
  observation (2026-08-06T00:55Z) aged past the 24 h staleness window during
  this session. Distinguished per README_DEV reporting rules from the
  feature under test; Step 4's fresh observation clears it.
