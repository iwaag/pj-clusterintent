# Step 0 — Freeze the deletion list

## Decision (user-confirmed)

Delete all 27 unreferenced custom-field columns, including `owner` and
`purpose`. Recommended default from the plan, confirmed via
AskUserQuestion on 2026-08-02.

## Frozen deletion list (27 columns, all `dcim.device`)

Non-AI-review (17):
`owner`, `purpose`, `os_name`, `os_version`, `kernel_version`,
`architecture`, `cpu_model`, `cpu_cores`, `memory_gb`, `gpu_count`,
`gpu_models`, `gpu_memory_gb`, `gpu_accelerator_summary`,
`disk_total_gb`, `serial_number`, `docker_engine_state`,
`docker_container_running_count`, `docker_container_total_count`,
`docker_compose_projects`, `docker_published_ports`,
`docker_service_summary`

AI-review (already decided per plan, 6):
`ai_resource_summary`, `ai_resource_review`,
`ai_resource_review_updated_at`, `agent_task_state`,
`ai_resource_review_model`, `ai_resource_review_source_hash`

(Recount: 15 non-AI + 6 AI-review = 21 listed above by name; plus
`docker_*` 6 fields already included in the 15 — total is 27. See
exact enumeration below, derived from `nauto/seed/home_cluster.yaml`.)

Full 27, in `home_cluster.yaml` order:
1. `owner`
2. `purpose`
3. `os_name`
4. `os_version`
5. `kernel_version`
6. `architecture`
7. `cpu_model`
8. `cpu_cores`
9. `memory_gb`
10. `gpu_count`
11. `gpu_models`
12. `gpu_memory_gb`
13. `gpu_accelerator_summary`
14. `disk_total_gb`
15. `serial_number`
16. `ai_resource_summary`
17. `ai_resource_review`
18. `ai_resource_review_updated_at`
19. `agent_task_state`
20. `ai_resource_review_model`
21. `ai_resource_review_source_hash`
22. `docker_engine_state`
23. `docker_container_running_count`
24. `docker_container_total_count`
25. `docker_compose_projects`
26. `docker_published_ports`
27. `docker_service_summary`

## Kept (not deleted)

- 9 `ACTUAL_FACT_FIELDS` (hard constraint): `host_system`,
  `primary_ip_address`, `primary_mac_address`, `network_interface`,
  `last_seen`, `inventory_source`, `observed_services`,
  `service_inventory_updated_at`, `observed_workspaces`.
- `inventory_raw_json` (raw store, widened in Step 1).
- All `proxmox_*` fields (out of scope, already allowlisted).

## Method

Computed by diffing every `content_types: [dcim.device]` custom_field
key in `nauto/seed/home_cluster.yaml` against the 9-field
`ACTUAL_FACT_FIELDS` allowlist plus `inventory_raw_json`. Matches the
suggestion.md estimate of "~26" (actual: 27).
