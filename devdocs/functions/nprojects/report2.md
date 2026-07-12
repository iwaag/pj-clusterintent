# Report 2: Repository Analysis Preview Job

## Summary

Executed [.local/nprojects/plan2.md](plan2.md).

Added a dry-run repository analysis path to the `nprojects` Nautobot App. The App can now reuse the configured `service_repositories.yaml`, fetch lightweight repository files, parse Backstage `Component` catalog entries, and log desired service candidate previews from a Nautobot Job.

This implementation does not add database models, migrations, API endpoints, or persistent analysis records.

## Files Added

```text
nprojects/nautobot_service_catalog/
├── analysis.py
├── jobs.py
└── tests/
    ├── __init__.py
    ├── test_analysis.py
    └── test_loaders.py
```

## Files Updated

```text
nprojects/
├── README.md
├── pyproject.toml
└── nautobot_service_catalog/
    ├── __init__.py
    ├── loaders.py
    └── templates/
        └── nautobot_service_catalog/
            └── repository_list.html
```

## Implemented Behavior

- Added `nautobot_service_catalog.analysis` as a Nautobot-independent analysis service.
- Added `Analyze Service Repositories` Nautobot Job in `jobs.py`.
- Added loader defaults matching the existing `Generate Desired Services` Job:
  - `catalog-info.yaml`
  - `backstage/catalog-info.yaml`
  - `README.md`
  - `readme.md`
  - `package.json`
  - `docker-compose.yml`
  - `compose.yaml`
  - `Chart.yaml`
- Marked defaulted path lists in the repository list template.
- Added pure Python tests for loader defaults and analysis behavior.
- Bumped App/package version to `0.2.0`.

## Job Behavior

The Job reads the configured repository catalog from either:

- explicit `repository_file` Job input, or
- `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]`, or
- `NAUTOBOT_SERVICE_REPOSITORIES_FILE`, or
- development fallback `./nauto/seed/service_repositories.yaml`.

It logs:

- repository analysis summary
- per-repository analysis details
- desired service candidate preview
- loader or analysis warnings

It does not write `desired_services.generated.yaml`.

## Verification Performed

Ran unit tests:

```bash
python3 -m unittest discover -s nautobot_service_catalog/tests
```

Result:

```text
Ran 6 tests in 0.001s
OK
```

Compiled modules:

```bash
python3 -m compileall nautobot_service_catalog
```

Result: passed.

Built wheel:

```bash
python3 -m pip wheel . --no-deps -w /tmp/nautobot_service_catalog_wheel_test
```

Result: passed.

Confirmed the wheel includes:

```text
nautobot_service_catalog/analysis.py
nautobot_service_catalog/jobs.py
nautobot_service_catalog/templates/nautobot_service_catalog/repository_list.html
```

Imported `jobs.py` without Nautobot installed:

```text
jobs= ()
```

This confirms local imports degrade safely when Nautobot is unavailable.

## Real YAML Smoke Test

Current [nauto/seed/service_repositories.yaml](../../nauto/seed/service_repositories.yaml) contains one repository:

```text
https://github.com/iwaag/agservice-storage
```

Local analysis smoke test produced:

```text
repositories=1
analyses=1
desired_services=1
analysis_errors=[]
```

The generated candidate was:

```text
name=agservice-storage
display_name=Storage Service
role=service
catalog_owner=iwaag
catalog_lifecycle=experimental
source_ref=main
source_catalog_path=catalog-info.yaml
```

## Not Verified

Nautobot runtime integration was not verified in this workspace because no running Nautobot environment is available here.

The following still needs to be checked inside the actual Nautobot environment:

- Job discovery shows `Analyze Service Repositories`.
- Job executes successfully from the Nautobot Jobs UI.
- Job can read `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]`.
- Job Result logs render the JSON analysis clearly enough for operator review.
- Worker process has outbound network access to the configured Git providers.

## Recommended Next Steps

1. Smoke test the Job inside Nautobot.
2. If the Job is not discovered, adjust App Job registration for the installed Nautobot version.
3. If Job logs are too hard to inspect, add an analysis preview page.
4. Decide whether to refactor the existing `nauto` `Generate Desired Services` Job to call this App service layer.
5. Start Phase 3 only after the analysis result shape is stable enough for DB models.
