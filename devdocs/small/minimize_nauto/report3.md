# Step 3 — Delete the frozen column list

## Code changes (committed by user as `nauto` `step3` 15f5938, pushed)

- `nauto/seed/home_cluster.yaml`: removed all 27 frozen custom-field
  entries (Step 0 list). Remaining `dcim.device` custom fields, parsed
  from the live YAML: exactly `last_seen`, `primary_mac_address`,
  `primary_ip_address`, `network_interface`, `host_system`,
  `inventory_source`, `inventory_raw_json`,
  `service_inventory_updated_at`, `observed_services`,
  `observed_workspaces` — the 9 `ACTUAL_FACT_FIELDS` +
  `inventory_raw_json`, nothing else.
- `nauto/jobs/ingest_nodeutils_inventory.py`: removed the
  corresponding writes from `build_custom_fields` (no more
  `os_name`/`os_version`/`kernel_version`/`architecture`/`cpu_*`/
  `memory_gb`/`gpu_*`/`disk_total_gb`/`serial_number`/`owner`/`purpose`/
  `docker_*` custom-field keys), and deleted the now-dead
  `make_docker_service_summary` (its only caller,
  `docker_service_summary`, is gone).
- `nauto/jobs/seed_home_cluster.py`: added `prune_custom_fields`,
  called from `ensure_custom_fields`. Bounded to a hardcoded
  `RETIRED_CUSTOM_FIELD_KEYS` set (the Step 0 frozen 27) intersected
  with "not currently in the YAML" — deliberately narrower than "any
  `dcim.device` field absent from YAML" so it can never delete a field
  owned by another app or a future field someone forgets to add back
  to the YAML.
- Superproject pointer bumped to `nauto` `15f5938` (user commit
  `4274ac0`, already pushed).

Verification: `python3 -m unittest discover -s tests` (from `nauto/`):
**112 passed**, 0 failures, 0 errors.

## Live run

1. **Git Repository sync**: `POST /api/extras/git-repositories/<id>/sync/`
   against `main` (`https://github.com/iwaag/nauto`). `SUCCESS` on
   first attempt (worker already warm). `current_head` moved to
   `15f59382740c116864547f0b32ecd349e4ba4b2f`, matching local `nauto`
   `HEAD`. `Seed Home Cluster` and `Ingest Nodeutils Inventory` both
   confirmed `installed: true, enabled: true` at that revision.

2. **Seed Home Cluster run** (`update_existing: true`): `SUCCESS`.
   Custom-field count went from 60 to 33 (exactly 27 fewer). Job log
   shows 27 `Deleted retired custom field <key>` lines, one per Step 0
   key, no more and no fewer. `proxmox_*` (18 fields) and two
   other-app fields (`preferred_services`, `service_roles`, not owned
   by this seed) were untouched — confirmed both before and after via
   `GET /api/extras/custom-fields/`.

3. **Device cascade check**: sampled 3 Devices
   (`agbach.local`, `agdnsmasq`, `aghub`) via
   `GET /api/dcim/devices/` — each now shows exactly the 9 allowlist
   keys + `inventory_raw_json` (+ the two other-app fields), confirming
   Nautobot's `CustomField` delete cascade stripped the retired keys
   from `_custom_field_data` with no per-device cleanup needed, per
   Step 0 fact 2.

4. **Ingest re-run against a real report**: ran `nodeutils collect`
   locally on this machine (`agstudio.home.arpa`), wrapped it as a
   `report_batch`, and submitted it to `Ingest Nodeutils Inventory`.
   `SUCCESS`. Job log: `matched_device=agstudio.home.arpa action=update
   ... changed_fields=custom_fields.last_seen,
   custom_fields.observed_services,
   custom_fields.service_inventory_updated_at,
   custom_fields.inventory_raw_json`. `Batch summary: total=1 created=0
   updated=1 unchanged=0 skipped=0`. No errors, no writes to any
   deleted field.

5. **inventory_raw_json widening confirmed live**: fetched the
   updated `agstudio.home.arpa` Device —
   `custom_fields.inventory_raw_json.facts` now contains `cpu`,
   `memory`, `os_name` (previously dropped by the pre-Step-1
   cherry-picking), alongside the fields that were always there
   (`hardware`, `gpu`, `disk`, `network`, `software`, `services`,
   `workspaces`) plus the newly-included `architecture`,
   `kernel_version`, `os_version`, `system`, `timezone`,
   `uptime_seconds`.

## Cross-suite check

`uv run pytest -q` in `nctl/`: 1149 passed, 1 failed
(`test_reconcile_profiles.py::test_real_repo_file_validates` —
`ansible_agdev/vars/deployment_profiles.yml` references unknown
profiles `comfyui`/`swarmui`). Confirmed unrelated: `ansible_agdev` is
untouched by this work (`git status` clean, no diff), and the failure
is about deployment-profile names, nothing to do with custom fields or
`inventory_raw_json`. Pre-existing drift in a file the user has open
separately — not a scope violation of this plan.

## Not yet done

Field-list bullets in `nauto/README.md` still list the deleted
columns — deferred to Step 4 per plan ordering.
