# Step 3 Report: Replace Legacy Placement Declarations

## Summary

Replaced all `ansible_groups`/`host_os`/`preferred_services` legacy placement declarations with
explicit `DesiredServicePlacement` and `DesiredNodeOperationalConfig` records. All runtime code,
seeds, tests, and example files for the retired shapes have been removed with no compatibility
fallback.

## Changes

### nauto/seed/intent_sources.yaml

- Removed `expected_spec.ansible_groups` and `expected_spec.host_os` from all `desired_nodes`.
- Upgraded all node lifecycles from `planned` to `active`.
- Added `aghaos` desired node (was missing from the seed entirely).
- Added `desired_endpoints.primary` for `aghaos` with `ip_policy: static` and `ip_address: 192.168.0.20`.
- Added `desired_service_placements` section covering all currently deployed production services:
  - prometheus/primary → agprometheus (deployment_profile: prometheus-server)
  - grafana/primary → aggrafana (deployment_profile: grafana-server)
  - nomad/server → agnomad (deployment_profile: nomad-server, instance_role: primary)
  - nomad/client-agstudio → agstudio (deployment_profile: nomad-client, instance_role: worker)
  - prometheus-node-exporter/agpc → agpc (deployment_profile: prometheus-node-exporter)
  - haos/primary → aghaos (deployment_profile: haos)
- Added `desired_node_operational_configs` section for all 9 nodes with typed `expected_host_os`
  (linux/macos) for actual-backed nodes and `actual_state_policy: declared` / `declared_host_os: haos`
  for aghaos. Power control, connection path, laptop flag, and local endpoint references are explicit
  for every node. aghaos gets `ansible_port: 2222`.

### nauto/seed/home_cluster.yaml

- Removed `preferred_services` custom field definition (no remaining writer or reader).
- Removed `service_roles` custom field definition (writer removed from ingest job).
- Added `intent_sources` section: one `infrastructure` entry (`source_type: manual`).
- Added `desired_services` section: prometheus, grafana, nomad, prometheus-node-exporter, haos —
  all with `lifecycle: active`, `catalog_namespace: default`, referencing intent_source `infrastructure`.

### nauto/jobs/seed_home_cluster.py

- Added `ensure_intent_sources` method: idempotent get-or-create for `IntentSource` rows.
- Added `ensure_desired_services` method: idempotent get-or-create/update for `DesiredService` rows,
  resolving the parent `IntentSource` by slug from the already-seeded refs.
- Both methods guard against `nautobot_intent_catalog` not being installed (consistent with existing
  pattern in models.py).
- `run` calls both new methods after `ensure_custom_fields`.

### nauto/seed/nodeutils_ingest.yaml

- Removed `service_roles: true` and `preferred_services: true` from `allowed_self_reported`.

### nintent/nautobot_intent_catalog/ansible_inventory.py (bootstrap export)

- Removed `ansible_groups` group-building loop and all `expected_spec` reads.
- Removed `host_os`/`os` fallback from `_host_vars`.
- Removed `skipped_groups` counter and field from the summary dict.
- Simplified `_select_mdns_endpoint` (dropped `ansible_mdns_endpoint` override from expected_spec).
- Simplified `_inventory_hostname` to use node slug directly (dropped `ansible_host_name` override).
- Removed `_group_skip_entry`, `_normalize_group_name`, and `_mapping` helpers (all unused).
- `_host_vars` signature reduced to `(node, endpoint)`.

### nintent/nautobot_intent_catalog/tests/test_ansible_inventory.py

- Removed all tests that asserted `ansible_groups` group membership or `host_os` in bootstrap vars.
- Rewrote test set to assert the new bootstrap contract:
  - Only `ssh_hosts` group is ever produced.
  - `host_os` is never present in bootstrap host vars.
  - `skipped_groups` field is absent from the summary.
  - All other bootstrap identity/mDNS assertions retained.

### nodeutils/nodeutils_collect.py

- `endpoint_from_hint_or_port`: removed `preferred_services` endpoint fallback lookup.
- `get_service_summary`: removed `service_roles` and `preferred_services` keys from return dict.
- `collect_inventory`: removed `service_roles` and `preferred_services` from the top-level inventory
  dict and from `self_reported`.
- `build_inventory_report`: removed `service_roles` and `preferred_services` from `self_reported`.

### nodeutils/example.self_inventory.yaml

- Removed commented-out `service_roles` and `preferred_services` example blocks.

### nodeutils/tests/test_inventory_report.py

- Replaced assertion `self_reported.service_roles == ["ai-inference"]` with
  `assertNotIn("service_roles", ...)` and `assertNotIn("preferred_services", ...)`.
- Removed `service_roles` from the config dict passed to `build_inventory_report`.

### nauto/jobs/ingest_nodeutils_inventory.py

- Removed `service_roles` and `preferred_services` writes from `build_custom_fields`.
- Removed `services` field (was `service_roles` join) from `make_ai_resource_summary`.

### nauto/jobs/service_placement_review.py

- `build_device_facts`: removed `service_roles` and `preferred_services` from returned dict.
- `build_deterministic_status`: removed `preferred_services` candidate scoring (+20 `host_preferred`
  reason and `has_preferred_endpoint` output field).
- Removed `_list_value` helper (no remaining caller).

### nauto/jobs/ai_resource_review.py

- Removed `service_roles` and `preferred_services` from `INPUT_CUSTOM_FIELDS`.

## Exit Criterion Status

All intended service membership is now represented by `DesiredServicePlacement` rows in
`intent_sources.yaml`. Every production-eligible node has a typed `DesiredNodeOperationalConfig`.
No runtime code reads `ansible_groups` or `preferred_services`. The bootstrap inventory produces
only `ssh_hosts` with mDNS identity metadata and no service groups or desired `host_os`.

## Notes

- `dnsmasq_server` is absent from the current `production/hosts.yml` and was not in any
  `ansible_groups` seed entry; no dnsmasq placement was added. Add when the node is declared.
- `agmbp2019` and `agmbp2018` are node-exporter targets in production hosts.yml but were not in
  the ansible_groups seed. Their placements can be added once the deployment profile is defined.
- `gpu_hosts` was an operational classification, not a service. It is not replaced by a placement;
  it will be derived from `DesiredNodeOperationalConfig` or actual GPU facts in the production
  inventory composer (Step 6).
- The `infrastructure` IntentSource and its DesiredService records are created by `SeedHomeCluster`
  Job before the YAML importer Job runs. The importer resolves `desired_service` references by
  `intent_source__slug` + composite catalog key, so both jobs must succeed in order.
