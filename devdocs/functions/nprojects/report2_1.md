# Report 2.1: Dependency-aware Analysis Output

## Summary

Executed [.local/nprojects/plan2_1.md](plan2_1.md).

Backstage `catalog-info.yaml` の `spec.dependsOn` を解析し、generated desired service candidate に `dependencies` として出力するようにした。

App service layer と legacy `nauto` Job の両方に同じ dependency output を追加した。DB model、migration、dependency 自動解決、placement readiness 判定はまだ追加していない。

## Files Updated

```text
nprojects/
├── README.md
└── nautobot_service_catalog/
    ├── __init__.py
    ├── analysis.py
    └── tests/
        └── test_analysis.py

nauto/
└── jobs/
    └── generate_desired_services.py
```

## Implemented Behavior

Desired service candidates now always include:

```yaml
dependencies: []
```

When `spec.dependsOn` exists, each entry is normalized into:

```yaml
- raw_ref: resource:default/minio-s3
  kind: resource
  namespace: default
  name: minio-s3
  dependency_type: resource
  resolution_status: unresolved
```

Supported input forms:

```text
kind:namespace/name
kind:name
namespace/name
name
```

Kind-less refs default to:

```text
kind=component
namespace=default
```

Malformed refs are reported under:

```yaml
analysis:
  malformed_dependencies:
    - raw_ref: ...
      reason: invalid_entity_ref
```

Malformed refs do not fail repository analysis.

## Repository Analysis Summary

Repository analysis now includes dependency aggregate fields when a service is generated:

```yaml
dependency_count: 3
component_dependency_count: 1
resource_dependency_count: 2
unresolved_dependencies:
  - component:default/keycloak
  - resource:default/minio-s3
  - resource:default/postgresql
malformed_dependencies: []
```

## Current Catalog Smoke Shape

The current upstream `agservice-storage` catalog contains:

```yaml
dependsOn:
  - resource:default/minio-s3
  - resource:default/postgresql
  - component:default/keycloak
```

Using a fake fetcher with that catalog content, output included:

```text
dependency_count=3
component_dependency_count=1
resource_dependency_count=2
unresolved_dependencies=[
  component:default/keycloak,
  resource:default/minio-s3,
  resource:default/postgresql,
]
```

and candidate dependencies:

```text
resource:default/minio-s3
resource:default/postgresql
component:default/keycloak
```

## Verification Performed

Ran App unit tests:

```bash
python3 -m unittest discover -s nautobot_service_catalog/tests
```

Result:

```text
Ran 9 tests in 0.002s
OK
```

Compiled App modules:

```bash
python3 -m compileall nautobot_service_catalog
```

Result: passed.

Built App wheel:

```bash
python3 -m pip wheel . --no-deps -w /tmp/nautobot_service_catalog_wheel_test
```

Result:

```text
nautobot_service_catalog-0.2.1-py3-none-any.whl
```

Compiled legacy Job:

```bash
python3 -m compileall jobs/generate_desired_services.py
```

Result: passed.

Confirmed upstream raw catalog could be read from:

```text
https://raw.githubusercontent.com/iwaag/agservice-storage/main/catalog-info.yaml
```

## Not Verified

Full real repository analysis through the GitHub API was not verified because this environment hit:

```text
HTTP Error 403: rate limit exceeded
```

The parser and output shape were verified with unit tests and a fake fetcher using the real catalog content.

Nautobot runtime Job execution should still be checked after deploying the updated App.

## Notes

`resource:*` dependencies are intentionally kept as unresolved resource dependencies. The implementation does not yet decide whether they are external resources, shared cluster services, or deployable services.

`component:*` dependencies are also unresolved for now. A later phase can resolve them to `DesiredServiceCandidate` or `ServiceDependency.resolved_service` once models exist.
