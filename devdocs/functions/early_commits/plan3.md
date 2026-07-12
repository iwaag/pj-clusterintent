# Service Placement Inventory Plan

## Goal

Add lightweight service placement information to the existing Nautobot self-registration flow.

The immediate use case is AI agents choosing where to send work. For example, agents should know that `ollama` normally runs on `PC1` and should use that existing endpoint first, while only starting a new instance when policy and capacity checks allow it.

Nautobot should store relatively stable intent and discovery facts:

- Which host is the preferred home for a service.
- Which endpoint should be used by default.
- Whether the service is manually managed, systemd-managed, or compose-managed.
- Which Docker services are currently present on the host as a recent snapshot.
- What fallback policy an automation agent should follow.

Do not use Nautobot as a high-frequency monitoring database.

## Design Choice

Keep service placement attached to the existing Device inventory first.

Reasoning:

- The current repository already models self-registered machines as Nautobot Devices.
- The scheduler-facing question starts from a host: "What useful services does this host provide?"
- Container and compose state changes frequently, so creating full Nautobot objects for every container is too heavy for the first version.
- A Device custom-field snapshot keeps the implementation small and compatible with the existing seed/self-registration pattern.

Use custom fields for compact searchable facts and `inventory_raw_json` for detailed raw discovery output.

## Nautobot Custom Fields

Add these Device custom fields in `nauto/seed/home_cluster.yaml`.

```yaml
- key: "service_roles"
  label: "Service Roles"
  type: "text"
  description: "Comma-separated stable service roles provided by this Device, such as ai-inference or automation-control"
  content_types:
    - "dcim.device"
- key: "preferred_services"
  label: "Preferred Services"
  type: "json"
  description: "Stable service placement declarations and preferred endpoints for automation agents"
  content_types:
    - "dcim.device"
- key: "docker_engine_state"
  label: "Docker Engine State"
  type: "text"
  description: "Recent self-reported Docker engine state"
  content_types:
    - "dcim.device"
- key: "docker_container_running_count"
  label: "Docker Container Running Count"
  type: "integer"
  description: "Recent count of running Docker containers"
  content_types:
    - "dcim.device"
- key: "docker_container_total_count"
  label: "Docker Container Total Count"
  type: "integer"
  description: "Recent count of all discovered Docker containers"
  content_types:
    - "dcim.device"
- key: "docker_compose_projects"
  label: "Docker Compose Projects"
  type: "text"
  description: "Comma-separated compose project names discovered on this Device"
  content_types:
    - "dcim.device"
- key: "docker_published_ports"
  label: "Docker Published Ports"
  type: "text"
  description: "Compact list of host ports published by local Docker containers"
  content_types:
    - "dcim.device"
- key: "docker_service_summary"
  label: "Docker Service Summary"
  type: "text"
  description: "Compact scheduler-facing summary of important Docker services"
  content_types:
    - "dcim.device"
- key: "service_inventory_updated_at"
  label: "Service Inventory Updated At"
  type: "text"
  description: "Timestamp when service and Docker facts were last collected"
  content_types:
    - "dcim.device"
```

Choose final weights near the existing AI resource fields, after confirming the current `home_cluster.yaml` ordering.

## Preferred Service Data Shape

Represent stable service intent as JSON in `preferred_services`.

Example:

```json
{
  "ollama": {
    "service_role": "ai-inference",
    "preferred": true,
    "endpoint": "http://pc1:11434",
    "startup_policy": "use_existing_first",
    "fallback_policy": "start_new_if_capacity_available",
    "managed_by": "systemd",
    "notes": "Default local inference endpoint for agents"
  }
}
```

Keep this field suitable for hand-authored overrides from `self_inventory.yaml`. It should express intended service placement, not instantaneous load.

## Host-Side Collection

Update `nodeutils/nautobot_self_register.py` to collect a best-effort Docker snapshot.

Discovery should be opt-in by default or safe by default:

- Do not fail registration when Docker is absent.
- Do not fail registration when the user lacks Docker socket permissions.
- Never collect container environment variables.
- Never collect secrets, bind-mounted file contents, or logs.
- Keep command timeouts short.

Recommended Docker commands:

```bash
docker version --format json
docker ps -a --format '{{json .}}'
docker compose ls --format json
```

If `docker compose` is unavailable, skip compose discovery.

Captured per-container fields should be limited to:

- container id short form
- name
- image
- state/status
- labels needed for compose project/service
- published ports
- created time if available from `docker ps`

Do not call `docker inspect` in the first implementation unless a specific missing field requires it. `inspect` returns too much data and increases the chance of accidentally collecting sensitive details.

## Config Overrides

Extend `nodeutils/example.self_inventory.yaml` to allow stable service declarations.

Example:

```yaml
service_roles:
  - ai-inference

preferred_services:
  ollama:
    service_role: ai-inference
    preferred: true
    endpoint: "http://pc1:11434"
    startup_policy: use_existing_first
    fallback_policy: start_new_if_capacity_available
    managed_by: systemd
```

Local config should override or enrich discovered facts. Discovery answers "what is present now"; config answers "what this host is intended to provide."

## Inventory Shape

Add a `services` section to `inventory_raw_json`.

Example:

```json
{
  "services": {
    "service_roles": ["ai-inference"],
    "preferred_services": {
      "ollama": {
        "endpoint": "http://pc1:11434",
        "startup_policy": "use_existing_first"
      }
    },
    "docker": {
      "installed": true,
      "engine_state": "available",
      "container_running_count": 4,
      "container_total_count": 6,
      "compose_projects": ["ai-stack"],
      "published_ports": ["11434/tcp", "3000/tcp"],
      "important_services": [
        {
          "name": "ollama",
          "image": "ollama/ollama:latest",
          "state": "running",
          "ports": ["11434/tcp"],
          "compose_project": "ai-stack"
        }
      ]
    }
  }
}
```

Only a compact subset should be promoted to Device custom fields.

## Important Service Detection

For the first version, keep a small allowlist of scheduler-relevant services.

Initial candidates:

- `ollama`
- `vllm`
- `open-webui`
- `nautobot`
- `grafana`
- `prometheus`
- `postgres`
- `redis`

Match against container name, compose service label, and image name. Keep matching conservative and deterministic.

## AI Resource Summary and Review

Update `ai_resource_summary` generation in `nodeutils` to include service hints such as:

```text
services=ai-inference; preferred=ollama:http://pc1:11434; docker=running:4/6; ports=11434/tcp,3000/tcp
```

Update `nauto/jobs/ai_resource_review.py` so `INPUT_CUSTOM_FIELDS` includes:

- `service_roles`
- `preferred_services`
- `docker_engine_state`
- `docker_container_running_count`
- `docker_container_total_count`
- `docker_compose_projects`
- `docker_published_ports`
- `docker_service_summary`
- `service_inventory_updated_at`

The review prompt should still avoid inventing availability. The LLM may describe preferred service placement, but live capacity decisions must come from monitoring or a scheduler check.

## Scheduler Interpretation

Automation agents should use Nautobot as the service placement source of truth:

1. Query Devices with `preferred_services.ollama.preferred = true` or `service_roles` containing `ai-inference`.
2. Read the preferred endpoint from Nautobot.
3. Check live capacity and health using the monitoring layer before dispatching work.
4. Use the existing endpoint when healthy and under capacity.
5. Start a new service only when the Nautobot policy allows it and capacity checks pass.

Nautobot answers "where should this normally run?" Monitoring answers "is it safe to use right now?"

## Documentation

Update `nauto/README.md`:

- List the new service and Docker custom fields.
- Explain that service placement is inventory data, not monitoring data.
- Add an example `ollama` preferred service entry.

Update `nodeutils/README.md`:

- Document Docker snapshot collection.
- Document required Docker permissions.
- Document that container env, logs, and secrets are not collected.
- Add the `preferred_services` config example.

## Verification

Local checks:

```bash
python3 -m py_compile jobs/*.py
```

In `nodeutils`:

```bash
uv run ruff check .
uv run python -m py_compile nautobot_self_register.py
uv run --env-file .env nautobot-self-register --json
uv run --env-file .env nautobot-self-register --dry-run
```

Manual Nautobot verification:

1. Sync the `nauto` Git Repository.
2. Run `Seed Home Cluster` with `dry_run=false`.
3. Run self-registration on a Docker host.
4. Confirm Docker custom fields are populated.
5. Confirm `inventory_raw_json.services` contains the detailed snapshot.
6. Confirm `AI Resource Review` regenerates once after service facts first appear.
7. Confirm a host without Docker still self-registers successfully.

## Future Extensions

- Add a dedicated Nautobot model or plugin only if Device custom fields become too limiting.
- Add a periodic reconciliation job to flag stale service inventory.
- Add a scheduler-facing resolver service that combines Nautobot placement data with monitoring capacity checks.
- Add explicit service priority and fallback host lists.
- Add per-service ownership and maintenance window metadata.
