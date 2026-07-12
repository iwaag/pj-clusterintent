# Report 3: Service Catalog Models

## Summary

Executed [.local/nprojects/plan3.md](plan3.md).

`nprojects` の Nautobot App に DB-backed catalog workflow を追加した。`ServiceRepository`, `DesiredServiceCandidate`, `ServiceDependency` の model 定義、初期 migration、table/filter/form/view、DB import Job、analysis persistence Job を追加した。

Git YAML はまだ source data として残している。既存 dry-run Job も維持している。

## Files Added

```text
nprojects/nautobot_service_catalog/
├── filters.py
├── forms.py
├── importers.py
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── models.py
├── tables.py
└── tests/
    └── test_importers.py
```

## Files Updated

```text
nprojects/
├── README.md
├── README_DEV.md
├── pyproject.toml
└── nautobot_service_catalog/
    ├── __init__.py
    ├── jobs.py
    ├── navigation.py
    ├── urls.py
    └── views.py
```

## Implemented Behavior

Added DB models:

- `ServiceRepository`
- `DesiredServiceCandidate`
- `ServiceDependency`

Added import helpers in `importers.py` so analysis output can be mapped into model defaults without tying the conversion logic to Django ORM calls.

Added Nautobot Jobs:

- `Import Service Repositories`
  - Reads configured `service_repositories.yaml`.
  - Upserts `ServiceRepository` by `url`.
  - Can optionally disable DB repositories missing from YAML.

- `Analyze and Import Service Candidates`
  - Reads enabled `ServiceRepository` rows.
  - Runs the existing Phase 2 analyzer.
  - Upserts `DesiredServiceCandidate`.
  - Replaces each candidate's dependencies with the Phase 2.1 `dependencies` output.
  - Updates repository `last_analysis_status`, `last_analyzed_at`, and `last_analysis_summary`.

Kept existing Job:

- `Analyze Service Repositories`
  - Still dry-run only.
  - Still does not persist DB records.

Added DB-backed GUI routes when Nautobot generic views are available:

```text
/plugins/service-catalog/repositories/
/plugins/service-catalog/candidates/
/plugins/service-catalog/dependencies/
```

Kept direct YAML diagnostic view:

```text
/plugins/service-catalog/repositories/source-yaml/
```

## Dependency Handling

Phase 2.1 dependency output is now persisted as `ServiceDependency`.

Example refs:

```text
resource:default/minio-s3
resource:default/postgresql
component:default/keycloak
```

They remain unresolved by default. The implementation does not yet resolve `component:*` to another candidate, classify `resource:*` as internal/external, or perform placement readiness checks.

Malformed dependencies are retained in candidate analysis warnings and are not saved as `ServiceDependency` rows.

## Verification Performed

Ran pure Python unit tests:

```bash
python3 -m unittest discover -s nautobot_service_catalog/tests
```

Result:

```text
Ran 12 tests in 0.002s
OK
```

Compiled App modules:

```bash
python3 -m compileall nautobot_service_catalog
```

Result: passed.

Built wheel:

```bash
python3 -m pip wheel . --no-deps -w /tmp/nautobot_service_catalog_wheel_test
```

Result:

```text
nautobot_service_catalog-0.3.0-py3-none-any.whl
```

Confirmed wheel includes:

```text
nautobot_service_catalog/models.py
nautobot_service_catalog/migrations/0001_initial.py
nautobot_service_catalog/jobs.py
nautobot_service_catalog/importers.py
nautobot_service_catalog/filters.py
nautobot_service_catalog/forms.py
nautobot_service_catalog/tables.py
```

Confirmed `jobs.py` still imports without Nautobot installed:

```text
jobs= ()
```

## Not Verified

This workspace does not have Django or Nautobot installed, so the following must be checked in the real Nautobot environment:

- `nautobot-server makemigrations nautobot_service_catalog --check --dry-run`
- `nautobot-server migrate nautobot_service_catalog`
- App model import under the installed Nautobot version.
- Generic object views render correctly.
- Navigation entries render correctly.
- Job discovery shows all three Jobs.
- `Import Service Repositories` creates/updates DB rows.
- `Analyze and Import Service Candidates` persists candidates and dependencies.
- `agservice-storage` creates unresolved dependency rows for:
  - `resource:default/minio-s3`
  - `resource:default/postgresql`
  - `component:default/keycloak`

## Notes

The initial migration was written in this workspace without a Nautobot runtime. If the installed Nautobot version's `PrimaryModel` abstract fields differ, regenerate the migration in the real environment and review the diff before applying it.
