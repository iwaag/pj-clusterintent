# Service Management Memo

## Current State

`nauto/seed/desired_services.yaml` is currently the cluster-level desired service catalog.
It answers "what services should exist somewhere in the home cluster?" and is separate from
Device-local facts such as `preferred_services` and `observed_services`.

The current flow is:

- `desired_services.yaml` defines desired cluster services such as `ollama` and `hatchet`.
- `ServicePlacementReview` loads that YAML file.
- Device custom fields provide self-reported host facts, service preferences, and observed service inventory.
- The review job compares desired services against those Device facts and logs deterministic status plus optional LLM review output.

This is a lightweight and reasonable design while the catalog is small and edited mostly as code.

## Recommendation

Do not convert this immediately.

Keep `desired_services.yaml` as the source of truth for now. It is easy to review in git, simple to seed, and avoids introducing a Nautobot plugin lifecycle before the service model has stabilized.

Move to a Nautobot plugin with custom models only when at least one of these becomes important:

- Desired services need to be edited from the Nautobot UI.
- Other automation needs to query desired services through the Nautobot REST/GraphQL API.
- Service placement decisions should be stored historically instead of only logged.
- Desired services need object permissions, change logs, relationships, or ownership metadata.
- Service definitions need links to Devices, Locations, Roles, or Teams as first-class Nautobot objects.
- The catalog grows beyond a small static YAML list.

## Proposed Plugin Model

If/when this becomes a plugin, model the catalog explicitly rather than storing the YAML blob in a custom field.

Suggested model: `DesiredService`

- `name`
- `display_name`
- `role`
- `required`
- `min_instances`
- `max_instances`
- `min_memory_gb`
- `prefers_gpu`
- `default_port`
- `protocol`
- `healthcheck_path`
- `healthcheck_expected_status`
- `prefer_existing`
- `allow_start_new`
- `avoid_laptops`
- `prefer_always_on`
- `notes`

Possible later model: `ServicePlacementReviewResult`

- `desired_service`
- `generated_at`
- `status`
- `recommended_primary`
- `recommended_fallbacks`
- `observed_instances`
- `cautions`
- `confidence`
- `model`
- `raw_review`

The review result model should be added only if the result needs to be queried or audited later. If logs are enough, skip it.

## Migration Path

1. Keep the current YAML schema stable.
2. Add validation around `desired_services.yaml` before introducing a database model.
3. When plugin conversion is justified, create a Nautobot plugin app under `nauto`.
4. Add `DesiredService` model, migration, table, filter, form, and views.
5. Add a seed/import job that imports existing `desired_services.yaml` rows into `DesiredService`.
6. Update `ServicePlacementReview.load_desired_services()` to read from the DB by default.
7. Keep YAML import as a compatibility path during the transition.
8. Only add `ServicePlacementReviewResult` after there is a concrete consumer for persisted review results.

## Notes

Avoid representing cluster-level desired services as Device custom fields. Device fields should remain host-local facts or preferences. Cluster intent belongs either in the YAML catalog or in a dedicated Nautobot plugin model.
