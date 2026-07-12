# Plan 2.1: Dependency-aware Analysis Output

## Goal

Backstage `catalog-info.yaml` の `spec.dependsOn` を解析し、generated desired service candidate に dependency 情報を含める。

この計画は Phase 3 の DB model 化に入る前の割り込みタスクとして実行する。dependency は最終的に desirable state の一部になるため、model 設計前に出力 schema を固める。

## Background

現在の Plan 2 実装では、Backstage `Component` entity から service/website/worker candidate は生成できるが、以下のような dependency は出力に反映していない。

```yaml
spec:
  dependsOn:
    - resource:default/minio-s3
    - resource:default/postgresql
    - component:default/keycloak
```

これは現時点では未実装範囲だったが、最終的には deploy されるべき service や準備されるべき infrastructure/resource として扱う必要がある。

## Target Behavior

`dependsOn` を持つ catalog entity から、desired service candidate に `dependencies` を追加する。

Example output:

```yaml
desired_services:
  - name: agservice-storage
    display_name: Storage Service
    role: service
    dependencies:
      - raw_ref: resource:default/minio-s3
        kind: resource
        namespace: default
        name: minio-s3
        dependency_type: resource
        resolution_status: unresolved
      - raw_ref: resource:default/postgresql
        kind: resource
        namespace: default
        name: postgresql
        dependency_type: resource
        resolution_status: unresolved
      - raw_ref: component:default/keycloak
        kind: component
        namespace: default
        name: keycloak
        dependency_type: component
        resolution_status: unresolved
```

Repository analysis summary should also include aggregate dependency information:

```yaml
dependency_count: 3
component_dependency_count: 1
resource_dependency_count: 2
unresolved_dependencies:
  - component:default/keycloak
  - resource:default/minio-s3
  - resource:default/postgresql
```

## Scope

Implement in the App service layer first:

- [nprojects/nautobot_service_catalog/analysis.py](../../nprojects/nautobot_service_catalog/analysis.py)
- [nprojects/nautobot_service_catalog/tests/test_analysis.py](../../nprojects/nautobot_service_catalog/tests/test_analysis.py)

Then decide whether to mirror the change into the legacy Git Job:

- [nauto/jobs/generate_desired_services.py](../../nauto/jobs/generate_desired_services.py)

If the App service output is already the path used in Nautobot, the legacy Job update can be deferred. If existing automation still reads `desired_services.generated.yaml` from `nauto`, update the legacy Job in the same pass to keep compatibility.

## Non-goals

- Do not add DB models or migrations.
- Do not auto-create missing dependency services.
- Do not auto-discover repositories for `component:*` dependencies.
- Do not decide whether `resource:*` is internal, external, shared, or deployable.
- Do not run placement review based on dependency readiness yet.
- Do not fail analysis just because one dependency ref is malformed.

## Data Model for This Phase

Add a small normalized dependency shape.

Fields:

- `raw_ref`: original Backstage reference string.
- `kind`: normalized lower-case kind, for example `component` or `resource`.
- `namespace`: namespace from the ref. Default to `default` when Backstage shorthand omits namespace.
- `name`: entity name.
- `dependency_type`: initially same as `kind`, reserved for later mapping.
- `resolution_status`: initially `unresolved`.

Supported Backstage refs:

```text
kind:namespace/name
kind:name
namespace/name
name
```

Normalization rules:

- `resource:default/minio-s3` -> `kind=resource`, `namespace=default`, `name=minio-s3`
- `component:default/keycloak` -> `kind=component`, `namespace=default`, `name=keycloak`
- `component:keycloak` -> `kind=component`, `namespace=default`, `name=keycloak`
- `keycloak` -> `kind=component`, `namespace=default`, `name=keycloak`

The default kind for kind-less dependency refs should be `component`, matching Backstage's common entity reference behavior.

Malformed refs should produce:

```yaml
malformed_dependencies:
  - raw_ref: ...
    reason: invalid_entity_ref
```

and should not be added to `dependencies`.

## Implementation Steps

1. Add dependency parsing helpers.

   In `analysis.py`, add:

   ```python
   @dataclass(frozen=True)
   class CatalogDependency:
       raw_ref: str
       kind: str
       namespace: str
       name: str
       dependency_type: str
       resolution_status: str = "unresolved"
   ```

   Add parser functions:

   - `_parse_dependency_ref(raw_ref: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]`
   - `_entity_dependencies(entity: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]`

   Keep return values JSON/YAML-friendly. A dataclass is fine internally, but candidate output should be plain dicts.

2. Include dependencies in desired service candidate.

   Update `_entity_to_desired_service()`:

   - Read dependencies from `entity["spec"]["dependsOn"]`.
   - Add `dependencies` list to the generated service.
   - If malformed refs exist, add them under `analysis["malformed_dependencies"]`.
   - Add analysis reason `backstage_dependencies_found` when at least one dependency is parsed.
   - Add analysis reason `backstage_dependency_refs_malformed` when malformed refs exist.

3. Add aggregate dependency summary to repository analysis.

   Update `analyze_repository()` after services are generated:

   - Count dependencies across generated services.
   - Count by kind/type.
   - Add unresolved dependency refs.
   - Add malformed dependency refs.

   Suggested fields:

   ```yaml
   dependency_count: 3
   component_dependency_count: 1
   resource_dependency_count: 2
   unresolved_dependencies:
     - component:default/keycloak
   malformed_dependencies: []
   ```

4. Keep output stable when no dependencies exist.

   For services without `dependsOn`, prefer:

   ```yaml
   dependencies: []
   ```

   This keeps downstream consumers simple and makes Phase 3 model import less conditional.

5. Add tests.

   Extend `test_analysis.py` with cases for:

   - `resource:default/minio-s3`
   - `resource:default/postgresql`
   - `component:default/keycloak`
   - shorthand `component:keycloak`
   - kind-less `keycloak`
   - malformed dependency ref
   - no `dependsOn`

   Verify:

   - parsed dependency fields
   - candidate contains `dependencies`
   - repository analysis contains counts
   - malformed refs do not crash analysis

6. Decide on legacy Job compatibility.

   Check the current operational path:

   - If Nautobot is using the App Job output, document that `nauto/jobs/generate_desired_services.py` remains legacy.
   - If automation still runs `Generate Desired Services`, update its `_entity_to_desired_service()` and tests/manual smoke path to emit the same `dependencies` field.

   Keep any legacy Job patch minimal and mechanically equivalent to the App parser.

7. Verification.

   Run:

   ```bash
   python3 -m unittest discover -s nautobot_service_catalog/tests
   python3 -m compileall nautobot_service_catalog
   python3 -m pip wheel . --no-deps -w /tmp/nautobot_service_catalog_wheel_test
   ```

   Run a real YAML smoke check against:

   ```text
   ../nauto/seed/service_repositories.yaml
   ```

   Confirm `agservice-storage` output includes:

   ```text
   resource:default/minio-s3
   resource:default/postgresql
   component:default/keycloak
   ```

## Acceptance Criteria

- Desired service candidates always include a `dependencies` list.
- `dependsOn` entries are normalized into `raw_ref`, `kind`, `namespace`, `name`, `dependency_type`, and `resolution_status`.
- `resource:default/minio-s3`, `resource:default/postgresql`, and `component:default/keycloak` appear in generated output for the current catalog.
- Repository analysis summary includes dependency counts and unresolved dependency refs.
- Malformed dependency refs are reported but do not fail repository analysis.
- Existing no-dependency catalog behavior remains compatible.
- Unit tests cover dependency parsing and candidate output.

## Follow-up After Plan 2.1

- If dependency output looks stable, use it as the input shape for Phase 3 `ServiceDependency`.
- Decide whether `resource:*` dependencies should become a separate `RequiredResourceCandidate` model or remain dependencies attached to services.
- Add dependency readiness checks during Phase 4 placement review.
