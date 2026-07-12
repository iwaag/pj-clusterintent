# Plan 5: Repository-Driven Desired Service Generation

## Goal

Add a lightweight repository catalog flow that can derive desired cluster services from service repositories without cloning entire repositories.

## Design

- Keep repository intent in `nauto/seed/service_repositories.yaml`.
- Make only `url` required for each repository entry.
- Resolve defaults in code:
  - `enabled: true`
  - default branch from provider API when possible
  - fallback refs: `HEAD`, `main`, `master`
  - catalog paths: `catalog-info.yaml`, `backstage/catalog-info.yaml`
  - basic files: `README.md`, `readme.md`, `package.json`, `docker-compose.yml`, `compose.yaml`, `Chart.yaml`
- Fetch only selected files through provider/raw HTTP endpoints.
- Treat missing `catalog-info.yaml` as insufficient analysis, not as a hard failure.
- Generate `nauto/seed/desired_services.generated.yaml` with:
  - generation metadata
  - per-repository analysis status
  - desired service entries derived from Backstage `Component` entities
- Keep `nauto/seed/desired_services.yaml` as the approved manual source until merge/approval behavior is intentionally added.

## Implementation Steps

1. Add `nauto/seed/service_repositories.yaml` with URL-only examples and documented optional fields.
2. Add a Nautobot Job, `Generate Desired Services`, that:
   - loads the repository catalog
   - fetches candidate files without full clone
   - parses Backstage catalog YAML
   - logs repository analysis
   - optionally writes generated desired services YAML
3. Register the Job in `nauto/jobs/__init__.py`.
4. Update `nauto/README.md` with the new repository-catalog workflow.
5. Run static syntax checks for the new/changed Python files.

## Follow-Up

- Add a merge/approval job if `desired_services.generated.yaml` proves useful.
- Promote repository/service catalog state into a Nautobot plugin model only after other services need to query it through Nautobot REST/GraphQL.
