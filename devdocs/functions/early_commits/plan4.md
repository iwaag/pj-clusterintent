# Desired Service Catalog and Placement Review Plan

## Goal

Add a Nautobot-side source of truth for services that should exist somewhere in the home automation cluster, independent of any individual Device.

The system should answer four separate questions:

- What services should exist somewhere?
- What capabilities and observed services does each Device currently report?
- Which Devices are good candidates for each desired service?
- Which service placements are missing, stale, unhealthy, or only partially satisfied?

This plan intentionally separates service intent from host inventory. A desired service such as `ollama` or `hatchet` must not live only inside a Device custom field, because it represents cluster-level desired state, not a property of one machine.

## Data Model

Use four layers.

| Layer | Owner | Example |
| --- | --- | --- |
| Desired Service Catalog | Nautobot server / Git seed | `ollama should exist somewhere for ai-inference` |
| Device Capability | Device self-registration | `pc1 has 64 GB RAM and an NVIDIA GPU` |
| Observed Service | Device self-registration | `pc1 currently has ollama running on port 11434` |
| Placement Review | Nautobot Job output | `ollama: primary candidate pc1, fallback pc2` |

The first implementation should keep the Desired Service Catalog in a YAML file under `nauto/seed/`. This keeps the model reviewable in Git and avoids writing a Nautobot plugin before the shape settles.

## Desired Service Catalog

Create a new file:

```text
nauto/seed/desired_services.yaml
```

Initial shape:

```yaml
desired_services:
  - name: ollama
    display_name: "Ollama"
    role: ai-inference
    required: true
    min_instances: 1
    max_instances: 2
    min_memory_gb: 16
    prefers_gpu: true
    default_port: 11434
    protocol: http
    healthcheck:
      path: /api/tags
      expected_status: 200
    placement_policy:
      prefer_existing: true
      allow_start_new: true
      avoid_laptops: false
    notes: "Local LLM inference endpoint for agents."

  - name: hatchet
    display_name: "Hatchet"
    role: automation-control
    required: true
    min_instances: 1
    max_instances: 1
    min_memory_gb: 4
    prefers_gpu: false
    default_port: 8080
    protocol: http
    healthcheck:
      path: /healthz
      expected_status: 200
    placement_policy:
      prefer_existing: true
      allow_start_new: false
      prefer_always_on: true
    notes: "Workflow control plane for automation jobs."
```

Keep this catalog independent from Devices. It may reference service roles and constraints, but it should not name a specific Device unless there is a hard pin or exclusion.

Optional fields for later:

- `hard_pinned_devices`
- `excluded_devices`
- `required_tags`
- `forbidden_tags`
- `requires_service`
- `backup_priority`
- `maintenance_window`
- `secrets_profile`

## Device-Side Fields

Keep Device fields limited to facts about the Device.

Existing fields that remain useful:

- `service_roles`
- `preferred_services`
- `docker_engine_state`
- `docker_container_running_count`
- `docker_container_total_count`
- `docker_compose_projects`
- `docker_published_ports`
- `docker_service_summary`
- `service_inventory_updated_at`
- `inventory_raw_json`

Add a JSON custom field for normalized observed services:

```yaml
- key: "observed_services"
  label: "Observed Services"
  type: "json"
  description: "Normalized services recently observed on this Device by self-registration"
  weight: 261
  content_types:
    - "dcim.device"
```

`preferred_services` should be treated as local host preference or override. It is not the cluster-wide desired service list.

## Observed Service Shape

Extend `nodeutils/nautobot_self_register.py` to produce a normalized `observed_services` map.

Example:

```json
{
  "ollama": {
    "state": "running",
    "source": "docker",
    "endpoint": "http://pc1:11434",
    "ports": ["11434->11434/tcp"],
    "container_name": "ollama",
    "compose_project": "ai-stack",
    "compose_service": "ollama",
    "checked_at": "2026-06-16T02:30:00+00:00"
  },
  "hatchet": {
    "state": "active",
    "source": "systemd",
    "endpoint": "http://pc1:8080",
    "unit": "hatchet.service",
    "checked_at": "2026-06-16T02:30:00+00:00"
  }
}
```

Initial detection sources:

- Docker containers, using the existing `docker ps` parsing.
- Docker compose project and service labels.
- Systemd units on Linux with `systemctl list-units --type=service --state=running`.
- Listening ports with `ss -ltnp` on Linux when available.
- Launchd can be deferred unless macOS service observation becomes necessary.

Detection should stay conservative:

- Never collect environment variables.
- Never collect container logs.
- Never read bind-mounted files.
- Do not use `docker inspect` in the first pass unless a specific required field cannot be obtained safely otherwise.
- Time out service discovery commands quickly.
- Registration should succeed even if service discovery fails.

## Nautobot Jobs

Add a new Job:

```text
nauto/jobs/service_placement_review.py
```

Responsibilities:

1. Load `seed/desired_services.yaml`.
2. Query active self-registered Devices.
3. Read each Device capability, service preference, Docker summary, observed services, last seen time, and AI resource review fields.
4. Build deterministic candidate facts.
5. Ask an LLM for a placement review and reasoning.
6. Store or log the review in a bounded, machine-readable form.

Keep this separate from `AIResourceReview`. The existing job reviews one Device. The new job reviews the cluster against desired service state.

## Placement Review Output

Start by logging the output and optionally storing it in a small set of Nautobot custom fields or a generated report file.

Preferred JSON shape:

```json
{
  "generated_at": "2026-06-16T02:35:00+00:00",
  "model": "llama3.1:8b",
  "services": {
    "ollama": {
      "status": "satisfied",
      "observed_instances": [
        {
          "device": "pc1",
          "endpoint": "http://pc1:11434",
          "state": "running"
        }
      ],
      "recommended_primary": "pc1",
      "recommended_fallbacks": ["pc2"],
      "cautions": ["Check live GPU utilization before dispatching large inference jobs."],
      "confidence": "medium"
    },
    "hatchet": {
      "status": "missing",
      "observed_instances": [],
      "recommended_primary": "pc2",
      "recommended_fallbacks": [],
      "cautions": ["No running instance was observed in the latest self-registration data."],
      "confidence": "low"
    }
  }
}
```

Statuses:

- `satisfied`
- `under_replicated`
- `over_replicated`
- `missing`
- `stale`
- `conflicting`
- `unknown`

The LLM may recommend and explain, but it must not be allowed to directly start, stop, or move services. Any automation that acts on the recommendation needs a deterministic policy check first.

## Deterministic Pre-Scoring

Before calling the LLM, compute simple scores so the model is reviewing structured evidence rather than inventing capacity.

Candidate facts per desired service:

- Device name.
- Device role and tags.
- Last seen age.
- Agent task state.
- CPU cores.
- Memory GB.
- GPU count, models, and GPU memory.
- Service roles.
- Preferred service declarations.
- Observed service state.
- Docker engine state.
- Published ports.
- Whether the desired service is already running.
- Whether the Device appears stale.

Example deterministic flags:

- `meets_min_memory`
- `has_gpu_when_preferred`
- `already_running`
- `has_preferred_endpoint`
- `recently_seen`
- `agent_available`
- `docker_available`

These flags should be passed to the LLM as facts. The model should produce ranking and cautions, not raw discovery.

## Server-Side Seeding

Extend or add a Nautobot seed job path.

Option A, preferred first:

- Keep `SeedHomeCluster` focused on Nautobot primitives and Device custom fields.
- Add `desired_services.yaml` as a plain Git data file.
- Let `ServicePlacementReview` load it directly.

Option B, later:

- Add a Nautobot plugin with custom models:
  - `DesiredService`
  - `DesiredServiceConstraint`
  - `ServicePlacementReview`
- Migrate the YAML data into those models.

Do not start with Option B unless the UI and API ergonomics become more important than keeping the first implementation small.

## Nodeutils Changes

Update `nodeutils/nautobot_self_register.py`.

Implementation steps:

1. Add `hatchet` to `IMPORTANT_SERVICE_NAMES`.
2. Normalize Docker important services into `observed_services`.
3. Add optional systemd discovery on Linux.
4. Add optional port-to-service hints from config.
5. Promote `observed_services` to Device custom fields.
6. Keep detailed discovery in `inventory_raw_json`.

Suggested config extension:

```yaml
service_probe_hints:
  ollama:
    endpoint: "http://pc1:11434"
    healthcheck_path: /api/tags
  hatchet:
    endpoint: "http://pc1:8080"
    systemd_unit: hatchet.service
```

Probe hints are host-local facts or hints. They are not the global desired service catalog.

## Nauto Changes

Implementation steps:

1. Add `observed_services` to `nauto/seed/home_cluster.yaml`.
2. Add `nauto/seed/desired_services.yaml`.
3. Add `nauto/jobs/service_placement_review.py`.
4. Register the new Job in `nauto/jobs/__init__.py`.
5. Add environment variables for the LLM endpoint, mirroring `AIResourceReview`.
6. Document the workflow in `nauto/README.md`.

Suggested environment variables:

```bash
SERVICE_PLACEMENT_REVIEW_URL=http://localhost:11434/api/generate
SERVICE_PLACEMENT_REVIEW_MODEL=llama3.1:8b
SERVICE_PLACEMENT_REVIEW_TIMEOUT=45
SERVICE_PLACEMENT_REVIEW_LOG_PROMPT=false
```

## Prompt Contract

The placement review prompt should require JSON output only.

Rules for the model:

- Use only provided facts.
- Do not invent live capacity.
- Treat stale Device reports as caution or unknown.
- Distinguish desired state from observed state.
- Prefer existing healthy services when policy says `prefer_existing`.
- Do not recommend starting new instances when `allow_start_new` is false.
- Include a short caution when a recommendation depends on monitoring checks.

The job should validate that the response is JSON and truncate or reject oversized fields.

## Automation Boundary

The first version should not automatically start or stop services.

Allowed first-version actions:

- Report missing desired services.
- Recommend candidate Devices.
- Identify stale or conflicting observations.
- Produce a machine-readable review for another scheduler or human to inspect.

Deferred actions:

- Starting Docker compose projects.
- Enabling systemd units.
- Moving a service between Devices.
- Updating firewall or reverse proxy configuration.
- Writing back a selected primary placement as policy.

## Testing

Nodeutils tests or manual checks:

- Docker absent: registration succeeds and `observed_services` is empty.
- Docker unavailable due to permission: registration succeeds.
- Running `ollama` container: `observed_services.ollama` appears.
- Running `hatchet` systemd unit: `observed_services.hatchet` appears.
- `--dry-run` includes `observed_services`.

Nauto tests or dry runs:

- `SeedHomeCluster` creates the new custom field.
- `ServicePlacementReview` handles an empty desired catalog.
- `ServicePlacementReview` handles no Devices.
- `ServicePlacementReview` marks a required service as `missing`.
- Existing observed `ollama` satisfies `min_instances: 1`.
- Stale `last_seen` causes `stale` or caution output.
- Invalid LLM JSON is logged and not saved as a successful review.

## Rollout

1. Add the desired service catalog YAML with `ollama` and `hatchet`.
2. Add `observed_services` custom field and run `SeedHomeCluster` with `dry_run=true`.
3. Apply `SeedHomeCluster` with `dry_run=false`.
4. Update nodeutils and run `--dry-run` on one host.
5. Run real self-registration on one host.
6. Confirm Device custom fields contain `observed_services`.
7. Add and run `ServicePlacementReview` manually.
8. Review the output before connecting it to any scheduler.

## Open Questions

- Should placement review output be stored in a Nautobot custom field, a Job Result log only, or a generated file committed elsewhere?
- What is the staleness threshold for self-reported service data: 15 minutes, 1 hour, or 24 hours?
- Which hosts should be considered always-on versus opportunistic?
- Should `preferred_services` eventually be renamed to `host_service_preferences` to avoid confusion with the global desired catalog?
- Should health checks be performed by nodeutils, by the Nautobot job, or by a separate monitoring system?
