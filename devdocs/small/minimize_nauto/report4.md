# Step 4 — Docs + close-out

## Changes

- `nauto/README.md`: replaced the 35-entry Device Custom Field list
  with the frozen 10 (the 9 `ACTUAL_FACT_FIELDS` + `inventory_raw_json`)
  and added a note pointing to `inventory_raw_json.facts` as the home
  for everything else, plus a pointer to
  `devdocs/small/minimize_nauto/` for rationale.
- Already handled in Step 2: removed the `jobs/ai_resource_review.py`
  tree entry, its description paragraph, the `AI_RESOURCE_REVIEW_*` env
  var block, and the Job Hook setup step from `README.md`.
- Checked `README_DEV.md` and root `README.md` for references to any
  retired field name (`ai_resource_*`, `agent_task_state`,
  `docker_engine_state`, `docker_service_summary`, `owner`, `purpose`,
  `os_name`, `cpu_model`, `gpu_count`, `serial_number`, etc.) — none
  found; nothing to update there.
- Checked `nodeutils/nodeutils_collect.py`, which has its own local
  `docker_service_summary`/`owner`/`purpose` keys in its **own**
  self-inventory summary (a separate data structure, not the Nautobot
  custom field written by nauto's ingest job). Out of scope per the
  plan's scope note (nauto only) — left untouched.

## Roadmap status

All 5 steps (0-4) of `devdocs/small/minimize_nauto/plan.md` are
complete:

- Step 0: 27-field deletion list frozen with user (`report0.md`).
- Step 1: `inventory_raw_json` widened to the full `facts` dict, code +
  tests, 112 nauto tests pass (`report1.md`).
- Step 2: AI review feature retired — code, tests, README, env vars;
  live Job Hook deleted by the user (`report2.md`).
- Step 3: 27 frozen custom fields deleted live via `Seed Home Cluster`'s
  new prune mechanism; verified against real Devices; `Ingest
  Nodeutils Inventory` re-run against a real report with a clean pass;
  widened `inventory_raw_json` confirmed live on `agstudio.home.arpa`
  (`report3.md`).
- Step 4: docs brought in line with the new 10-field allowlist (this
  report).

Final state: `nauto`'s `dcim.device` Custom Fields are exactly the 9
`ACTUAL_FACT_FIELDS` (`host_system`, `primary_ip_address`,
`primary_mac_address`, `network_interface`, `last_seen`,
`inventory_source`, `observed_services`, `service_inventory_updated_at`,
`observed_workspaces`) plus `inventory_raw_json`. All `proxmox_*`
fields and other-app fields (`preferred_services`, `service_roles`)
are untouched. `nctl` still never reads `inventory_raw_json`
(unchanged policy). The AI review Job Hook and its code are gone.

Test suites: `nauto` 112/112 passing throughout; `nctl` 1149/1150
passing, with the one failure (`test_reconcile_profiles.py`) confirmed
unrelated pre-existing drift in `ansible_agdev/vars/deployment_profiles.yml`
(this work never touched `ansible_agdev`, `nctl`, or `nintent`).
