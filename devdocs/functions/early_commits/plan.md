# AI Resource Review Job Hook Plan

## Goal

When a Device is created or updated by host self-registration, Nautobot should automatically ask an external LLM service such as Ollama to produce a concise agent-facing review of the device's suitability for automated tasks and projects.

The LLM-generated output will be stored in a new Device custom field named `ai_resource_review`.

## Design Choice

Use a Nautobot Job Hook Receiver.

Reasoning:

- The workflow starts from a Nautobot object change event.
- The logic needs direct access to the changed Device and its custom fields.
- The result should be written back into Nautobot.
- Keeping the first implementation inside a Nautobot Job avoids adding a separate webhook receiver service.

Keep `ai_resource_summary` as the deterministic machine-readable summary. Use `ai_resource_review` only for LLM-generated qualitative review text.

## Proposed Custom Fields

Add these fields to `seed/home_cluster.yaml`.

```yaml
- key: "ai_resource_review"
  label: "AI Resource Review"
  type: "text"
  description: "LLM-generated review of device suitability for automated agent workloads"
  weight: 246
  content_types:
    - "dcim.device"
- key: "ai_resource_review_updated_at"
  label: "AI Resource Review Updated At"
  type: "text"
  description: "Timestamp when ai_resource_review was last generated"
  weight: 247
  content_types:
    - "dcim.device"
- key: "ai_resource_review_model"
  label: "AI Resource Review Model"
  type: "text"
  description: "External LLM model used to generate ai_resource_review"
  weight: 249
  content_types:
    - "dcim.device"
```

Do not use the LLM review as the primary scheduling input. Scheduling should prefer structured fields such as `cpu_cores`, `memory_gb`, `disk_total_gb`, `agent_task_state`, and `ai_resource_summary`.

## Job Layout

Add a new Job file:

```text
jobs/ai_resource_review.py
```

Register it from:

```text
jobs/__init__.py
```

The Job should subclass `JobHookReceiver` and implement `receive_job_hook()`.

High-level flow:

1. Receive the object change event.
2. Confirm the changed object is a Device.
3. Skip if the object was changed only by the review-writing Job itself.
4. Read only selected Device fields and custom fields.
5. Build a compact prompt.
6. POST the prompt to Ollama or another configured LLM endpoint.
7. Store the response in `ai_resource_review`.
8. Store generation metadata in `ai_resource_review_updated_at` and `ai_resource_review_model`.
9. Save the Device.

## Configuration

Use environment variables on the Nautobot server.

```bash
AI_RESOURCE_REVIEW_URL=http://ollama.example.local:11434/api/generate
AI_RESOURCE_REVIEW_MODEL=llama3.1:8b
AI_RESOURCE_REVIEW_TIMEOUT=30
```

Keep the first version simple and server-local. Do not store API tokens in the Git repository.

## Prompt Inputs

Send only the fields needed for task assignment.

Recommended inputs:

- Device name
- Role
- Location
- Status
- Tags
- `agent_task_state`
- `ai_resource_summary`
- `os_name`
- `os_version`
- `architecture`
- `cpu_model`
- `cpu_cores`
- `memory_gb`
- `disk_total_gb`
- `last_seen`
- `purpose`

Avoid sending:

- Full `inventory_raw_json`
- API tokens
- Raw interface lists unless needed later
- Long comments or unrelated metadata

## Suggested Prompt Shape

```text
You are reviewing a computer resource for an automation scheduler.

Return a concise review in 3 short lines:
1. capability: summarize compute capacity and OS suitability
2. best_for: list suitable task types
3. cautions: mention limitations or stale data only if relevant

Use only the provided facts. Do not invent availability.

Facts:
{facts}
```

The prompt should make availability explicit: the model may mention `agent_task_state`, but it must not infer idleness from hardware specs.

## Loop Prevention

Device updates made by the review Job can trigger the same Job Hook again. Prevent loops with at least one of these guards:

- Skip if the changed fields are only `ai_resource_review`, `ai_resource_review_updated_at`, or `ai_resource_review_model`.
- Skip if `ai_resource_summary` and core resource fields have not changed since the last review.
- Store a deterministic source hash, for example `ai_resource_review_source_hash`, and skip when unchanged.

Preferred first implementation:

Add `ai_resource_review_source_hash` as a text custom field and compute it from the exact prompt facts. If the stored hash equals the newly computed hash, skip.

## Error Handling

- Use a short HTTP timeout.
- On LLM call failure, log a warning in the Job Result and do not modify the Device.
- On invalid LLM response, log a warning and do not modify the Device.
- Truncate the review before saving if it exceeds a chosen max length, for example 2000 characters.

## Nautobot UI Setup

After deploying the Job:

1. Sync the `nauto` Git Repository in Nautobot.
2. Run `Seed Home Cluster` with `dry_run=false` to create the new custom fields.
3. Enable the new `AI Resource Review` Job record if needed.
4. Create a Job Hook:
   - Content type: `dcim.device`
   - Events: create and update
   - Job: `AI Resource Review`
   - Enabled: true
5. Test with one Device update from `nodeutils`.

## Verification Plan

1. Run the seed Job and confirm the custom fields exist.
2. Register or update one host with:

```bash
uv run --env-file .env nautobot-self-register --verbose
```

3. Confirm a Job Result was created for the hook.
4. Confirm the Device has:
   - `ai_resource_summary`
   - `ai_resource_review`
   - `ai_resource_review_updated_at`
   - `ai_resource_review_model`
5. Update the Device again without changing resource facts and confirm the hash guard skips regeneration.

## Future Extensions

- Move the LLM call to an external summarizer service if model latency or dependency management becomes a problem.
- Add structured scheduler fields such as `agent_max_parallel_tasks`, `agent_labels`, or `agent_allowed_workloads`.
- Add a periodic Job that refreshes stale reviews for all eligible Devices.
- Add a manual Job Button to regenerate review for a single Device.
