# Plan 3: Service Catalog Models

## Goal

`nprojects` の Nautobot App に DB model を追加し、リポジトリ入力、解析済み desired service candidate、dependency を Nautobot の first-class object として扱えるようにする。

このステップでは [nauto/seed/service_repositories.yaml](../../nauto/seed/service_repositories.yaml) を即座に廃止しない。Git YAML は source of truth として残し、App 側に import して GUI で閲覧・編集・履歴管理できる土台を作る。

## Important Context

Phase 2 の直後に割り込みとして Phase 2.1 が実行済み。

Phase 2.1 で Backstage `catalog-info.yaml` の `spec.dependsOn` が解析され、desired service candidate に以下の dependency output が追加された。

```yaml
dependencies:
  - raw_ref: resource:default/minio-s3
    kind: resource
    namespace: default
    name: minio-s3
    dependency_type: resource
    resolution_status: unresolved
```

そのため Plan 3 では dependency を後続追加ではなく初期 DB 設計に含める。`component:*` と `resource:*` はどちらも first-class な `ServiceDependency` として保存するが、この時点では自動解決や placement readiness 判定はしない。

## Current Starting Point

Plan 1 で実装済み:

- `nautobot_service_catalog` App config
- `/plugins/service-catalog/repositories/`
- YAML loader
- repository list template
- `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]`
- `NAUTOBOT_SERVICE_REPOSITORIES_FILE` fallback

Plan 2 で実装済み:

- `nautobot_service_catalog.analysis`
- `Analyze Service Repositories` dry-run Job
- Backstage `Component` catalog detection
- desired service candidate preview

Plan 2.1 で実装済み:

- `spec.dependsOn` dependency parsing
- candidate `dependencies` output
- repository analysis dependency summary
- legacy `nauto/jobs/generate_desired_services.py` compatibility output

## Target Behavior

Nautobot GUI で以下を扱える。

- `ServiceRepository` 一覧、詳細、作成、編集、削除
- `DesiredServiceCandidate` 一覧、詳細
- `ServiceDependency` 一覧、詳細
- YAML から `ServiceRepository` を import する Job
- repository analysis output から `DesiredServiceCandidate` と `ServiceDependency` を保存する Job

最初の DB 化では、YAML import と analysis import を明確に分ける。

- YAML import: repository input を `ServiceRepository` に取り込む。
- Analysis import: repository を解析し、candidate と dependency を DB に反映する。

## Non-goals

- `service_repositories.yaml` を廃止しない。
- Git YAML と DB の source of truth をこの段階で完全に切り替えない。
- REST API や GraphQL を独自実装しない。
- placement review はまだ統合しない。
- dependency readiness 判定はまだ行わない。
- `resource:*` dependency を自動で deploy 対象 service に変換しない。
- `component:*` dependency の repository を自動探索しない。
- 外部 Git provider sync lifecycle との本格統合はまだ行わない。

## Proposed Package Layout

```text
nprojects/
└── nautobot_service_catalog/
    ├── analysis.py
    ├── filters.py
    ├── forms.py
    ├── jobs.py
    ├── models.py
    ├── tables.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    │   └── 0001_initial.py
    ├── templates/
    │   └── nautobot_service_catalog/
    │       ├── desiredservicecandidate.html
    │       ├── desiredservicecandidate_list.html
    │       ├── servicedependency.html
    │       ├── servicedependency_list.html
    │       ├── servicerepository.html
    │       └── servicerepository_list.html
    └── tests/
        ├── test_analysis.py
        ├── test_loaders.py
        └── test_models.py
```

Template names can follow the Nautobot generic view conventions for the installed version. If generic object views provide enough default rendering, keep custom templates minimal.

## Models

### ServiceRepository

Purpose: input repository record imported from YAML or edited in GUI.

Suggested fields:

- `url`: unique repository URL.
- `enabled`: boolean, default `true`.
- `ref`: optional branch, tag, or commit.
- `owner`: optional owner hint from YAML.
- `service_hint`: optional service name hint from YAML.
- `catalog_paths`: JSON/list field.
- `basic_file_paths`: JSON/list field.
- `raw_url_template`: optional string.
- `last_analysis_status`: optional status string.
- `last_analyzed_at`: optional datetime.
- `last_analysis_summary`: JSON field for lightweight summary.

Notes:

- Keep `url` unique for now.
- Preserve configured path lists exactly enough to export back to YAML.
- Do not store secrets in `raw_url_template` or summary fields.

### DesiredServiceCandidate

Purpose: parsed candidate generated from Backstage catalog analysis.

Suggested fields:

- `name`: slug/service identifier.
- `display_name`: human-readable name.
- `role`: service, website, worker, or other supported role.
- `source_repository`: foreign key to `ServiceRepository`.
- `source_ref`: resolved ref used during analysis.
- `source_catalog_path`: catalog file path.
- `catalog_kind`: Backstage entity kind.
- `catalog_namespace`: Backstage metadata namespace, default `default`.
- `catalog_metadata_name`: Backstage metadata name.
- `catalog_owner`: owner from catalog.
- `catalog_lifecycle`: lifecycle from catalog.
- `catalog_spec_type`: service, website, worker, etc.
- `prefers_gpu`: boolean.
- `min_memory_gb`: optional number.
- `analysis_status`: status string.
- `analysis_confidence`: confidence string.
- `analysis_reasons`: JSON/list field.
- `analysis_warnings`: JSON/list field.
- `notes`: optional text.
- `last_analyzed_at`: datetime.

Suggested uniqueness:

- Unique per `source_repository`, `catalog_namespace`, `catalog_metadata_name`, `catalog_spec_type`.

This avoids duplicate candidates on repeated imports while still allowing different repositories to expose similarly named catalog entities.

### ServiceDependency

Purpose: normalized dependency metadata from Phase 2.1 output.

Suggested fields:

- `source_service`: foreign key to `DesiredServiceCandidate`.
- `kind`: normalized Backstage kind, for example `component` or `resource`.
- `namespace`: normalized namespace, default `default`.
- `name`: normalized entity name.
- `raw_ref`: original dependency ref.
- `dependency_type`: initially same as kind.
- `resolution_status`: `unresolved`, `resolved`, `external`, `ignored`, or later statuses.
- `resolved_service`: optional self/foreign key to `DesiredServiceCandidate`.
- `notes`: optional text.

Suggested uniqueness:

- Unique per `source_service`, `kind`, `namespace`, `name`.

Do not require `resolved_service`. Phase 2.1 intentionally leaves `component:*` and `resource:*` unresolved.

## Implementation Steps

1. Add model foundations.

   Create `models.py` with `ServiceRepository`, `DesiredServiceCandidate`, and `ServiceDependency`.

   Prefer Nautobot base classes when available in the target version, such as `PrimaryModel`, so change logging, custom fields, tags, and object permissions integrate cleanly. If local imports cannot be verified without Nautobot, keep pure helper code isolated and validate model import in the Nautobot runtime.

2. Add initial migration.

   Generate `0001_initial.py` in a Nautobot/Django environment.

   Review the migration before committing it:

   - No accidental environment-specific defaults.
   - JSON fields have safe defaults.
   - FK delete behavior is explicit.
   - indexes and uniqueness constraints match the intended import behavior.

3. Add tables, filters, and forms.

   Add Nautobot-compatible table/filter/form classes for:

   - `ServiceRepository`
   - `DesiredServiceCandidate`
   - `ServiceDependency`

   Initial list pages should prioritize operational fields:

   - repositories: URL, enabled, owner, service hint, last analysis status, last analyzed time
   - candidates: name, role, repository, catalog owner, analysis status, dependency count
   - dependencies: source service, kind, namespace, name, resolution status, resolved service

4. Replace or complement YAML repository list view.

   Keep the existing direct YAML repository list available only as a bootstrap or diagnostic view if useful.

   Add DB-backed object views for `ServiceRepository`. The main navigation should point to the DB-backed repository list after import exists.

   If removing the old route would make debugging harder, keep it under a name like:

   ```text
   /plugins/service-catalog/repositories/source-yaml/
   ```

5. Add YAML import Job.

   Add a Job such as:

   ```text
   Import Service Repositories
   ```

   Behavior:

   - Load configured YAML using the existing loader.
   - Upsert `ServiceRepository` by `url`.
   - Update enabled/ref/owner/service_hint/path fields.
   - Optionally disable DB repositories no longer present in YAML, controlled by a boolean Job variable.
   - Log created, updated, unchanged, disabled, and error counts.

   This Job should not fetch remote repositories.

6. Add analysis persistence Job.

   Extend or add a Job such as:

   ```text
   Analyze and Import Service Candidates
   ```

   Behavior:

   - Read enabled `ServiceRepository` rows from DB.
   - Convert them into the existing analysis service input shape.
   - Run the Phase 2 analyzer.
   - Upsert `DesiredServiceCandidate` rows.
   - Replace dependencies for each updated candidate with the Phase 2.1 `dependencies` output.
   - Save malformed dependency refs in candidate warnings or analysis summary, not as `ServiceDependency` rows.
   - Update `ServiceRepository.last_analysis_status`, `last_analyzed_at`, and `last_analysis_summary`.

   Keep the existing dry-run `Analyze Service Repositories` Job available until the DB import path is verified.

7. Add export or compatibility output.

   Add one of these compatibility paths:

   - YAML export Job from DB back to a `service_repositories` shaped payload.
   - Read-only preview/log output showing the DB rows in the same shape as existing YAML.

   Do not overwrite the source YAML by default. If file writing is supported, require an explicit output path.

8. Add tests.

   Pure Python tests should continue covering loader and analysis behavior.

   Add Django/Nautobot tests where the environment supports them:

   - model creation and string representation
   - uniqueness behavior
   - YAML import creates and updates `ServiceRepository`
   - analysis import creates candidate rows
   - Phase 2.1 dependencies create `ServiceDependency` rows
   - malformed dependencies are retained as warnings and do not create dependency rows
   - repeated analysis import is idempotent

   If Nautobot is not available in this workspace, document which tests must run in the real Nautobot environment.

9. Update navigation and README.

   Update navigation to include:

   - Service Repositories
   - Desired Service Candidates
   - Service Dependencies
   - Jobs entry guidance if appropriate for the Nautobot version

   Update [nprojects/README.md](../../nprojects/README.md) and [nprojects/README_DEV.md](../../nprojects/README_DEV.md):

   - migration commands
   - import workflow
   - DB-backed GUI workflow
   - continued role of Git YAML as source data
   - dependency limitations from Phase 2.1

10. Verification.

   Outside Nautobot, keep the existing checks:

   ```bash
   python3 -m unittest discover -s nautobot_service_catalog/tests
   python3 -m compileall nautobot_service_catalog
   python3 -m pip wheel . --no-deps -w /tmp/nautobot_service_catalog_wheel_test
   ```

   In the Nautobot environment, run:

   ```bash
   nautobot-server makemigrations nautobot_service_catalog
   nautobot-server migrate
   nautobot-server nbshell
   ```

   Then verify:

   - App imports.
   - migrations apply cleanly.
   - object views render.
   - `Import Service Repositories` creates rows from YAML.
   - `Analyze and Import Service Candidates` creates `DesiredServiceCandidate`.
   - `resource:default/minio-s3`, `resource:default/postgresql`, and `component:default/keycloak` create unresolved `ServiceDependency` rows for `agservice-storage`.

## Suggested Import Semantics

YAML import should be conservative.

```text
YAML entry present, DB row absent      -> create row
YAML entry present, DB row present     -> update source-controlled fields
YAML entry absent, DB row present      -> leave unchanged by default
YAML entry absent, disable_missing=yes -> set enabled=false
```

Analysis import should be idempotent.

```text
candidate key absent      -> create
candidate key present     -> update analysis/catalog fields
dependency set changed    -> replace dependencies for that candidate
malformed dependency refs -> store warning, do not create dependency row
```

## Acceptance Criteria

- Initial migrations create `ServiceRepository`, `DesiredServiceCandidate`, and `ServiceDependency`.
- GUI list/detail/create/edit/delete works for `ServiceRepository`.
- GUI list/detail works for `DesiredServiceCandidate` and `ServiceDependency`.
- YAML import Job can import current `service_repositories.yaml`.
- Analysis import Job can persist at least one candidate from `agservice-storage`.
- Dependencies from Phase 2.1 output are persisted as unresolved `ServiceDependency` rows.
- Re-running imports does not create duplicate repositories, candidates, or dependencies.
- Existing dry-run analysis Job remains usable.
- Documentation explains that Git YAML remains source data during this phase.

## Follow-up After Plan 3

- Decide whether GUI editing or Git YAML remains authoritative after the DB path is proven.
- Add API exposure if Nautobot's generic API support is sufficient or implement App API endpoints.
- In Phase 4, use `ServiceDependency` during placement review as caution/readiness input.
- Consider a separate model for required infrastructure resources only if `resource:*` dependencies need lifecycle, ownership, or readiness fields beyond generic dependency metadata.
