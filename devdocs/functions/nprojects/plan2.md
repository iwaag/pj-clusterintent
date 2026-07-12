# Plan 2: Repository Analysis Preview Job

## Goal

`nprojects` の Nautobot App に、`service_repositories.yaml` の各リポジトリを dry-run 解析する Job を追加する。

このステップでは [nauto/jobs/generate_desired_services.py](../../nauto/jobs/generate_desired_services.py) の軽量解析ロジックを App 側の service 層へ移し、GUI または Job Result ログから「どのリポジトリが Backstage catalog として解析できるか」を確認できるようにする。

DB model、migration、解析結果の永続保存はまだ作らない。

## Current Starting Point

Plan 1 で以下は実装済み。

- `nautobot_service_catalog` App config
- `/plugins/service-catalog/repositories/`
- YAML loader
- repository list template
- `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]`
- `NAUTOBOT_SERVICE_REPOSITORIES_FILE` fallback

現在の実データは空。

```yaml
service_repositories: []
```

そのため Plan 2 の検証では、一時 YAML またはテスト用エントリを使う。

## Target Behavior

Nautobot Jobs 画面から `Analyze Service Repositories` のような App Job を実行できる。

Job は configured repository file を読み込み、各 enabled repository について以下を実行する。

- default branch を可能なら取得する。
- `catalog_paths` の候補から最初に取得できる `catalog-info.yaml` を探す。
- `basic_file_paths` の候補から存在確認できるファイルを取得する。
- Backstage `Component` entity を読み取る。
- `type` が `service`, `website`, `worker` の entity から desired service candidate 相当のプレビューを生成する。
- disabled repository は fetch せず `skipped` として扱う。

Job Result ログには以下を出す。

- repository count
- generated service candidate count
- repository analysis summary
- dry-run candidate preview
- fetch できなかった repository の理由

## Non-goals

- 解析結果を DB に保存しない。
- `DesiredServiceCandidate` model を作らない。
- Nautobot REST API や GraphQL を追加しない。
- repository list 画面から解析を直接起動しない。
- GUI から `service_repositories.yaml` を編集しない。
- 既存 `Generate Desired Services` Job を削除しない。
- 既存 `desired_services.yaml` や `desired_services.generated.yaml` の運用を変更しない。
- LLM review や placement review は扱わない。

## Proposed Package Layout

```text
nprojects/
└── nautobot_service_catalog/
    ├── analysis.py
    ├── jobs.py
    ├── loaders.py
    └── tests/
        ├── test_analysis.py
        └── test_loaders.py
```

`tests/` は Nautobot なしで実行できる pure Python テストを優先する。Nautobot runtime が必要な Job import テストは、環境がある場合だけ追加する。

## Implementation Steps

1. Align repository loader defaults.

   `loaders.py` の `RepositoryEntry` を解析にも使える形に寄せる。

   `nauto` Job と同じ default を App 側に定義する。

   ```python
   DEFAULT_CATALOG_PATHS = ("catalog-info.yaml", "backstage/catalog-info.yaml")
   DEFAULT_BASIC_FILE_PATHS = (
       "README.md",
       "readme.md",
       "package.json",
       "docker-compose.yml",
       "compose.yaml",
       "Chart.yaml",
   )
   ```

   Display-only では空配列でもよかったが、解析では defaults を適用する。画面表示と解析の見え方がずれないように、repository list でも default paths を表示するか、少なくとも「default」と分かる表示に更新する。

2. Create reusable analysis service.

   `analysis.py` を追加し、既存 Job から以下を移植する。

   - `FetchedFile`
   - `_plain_value`
   - `_slugify`
   - `_headers`
   - `_request_text`
   - `_github_owner_repo`
   - `_gitlab_project_path`
   - `_candidate_refs`
   - `RepositoryFileFetcher`
   - `_catalog_entities`
   - `_entity_to_desired_service`
   - `_repository_name`

   App 側では `RepositoryEntry` を入力として受ける。`nauto` Job の `RepositorySpec` と二重管理しないため、必要なら `RepositoryAnalysisSpec` などの小さな dataclass に変換する関数を用意する。

3. Add high-level analyzer function.

   Job から直接細かい helper を呼ばないよう、service 層に以下のような関数を作る。

   ```python
   def analyze_repositories(
       repositories: list[RepositoryEntry],
       fetch_timeout: float,
   ) -> RepositoryAnalysisResult:
       ...
   ```

   返却値には以下を含める。

   - `repository_analysis`
   - `desired_services`
   - `errors`
   - `generated_at`

   `RepositoryAnalysisResult` は dataclass にする。ログ出力しやすいように `to_dict()` または `asdict()` で JSON/YAML 化できる形にする。

4. Add Nautobot App Job.

   `jobs.py` を追加し、Nautobot がある環境では Job class を登録できるようにする。

   Suggested Job:

   ```text
   Analyze Service Repositories
   ```

   Variables:

   - `repository_file`: optional string. Emptyなら `PLUGINS_CONFIG` または env fallback を使う。
   - `fetch_timeout`: integer, default `10`
   - `include_candidate_preview`: boolean, default `true`

   Behavior:

   - `load_service_repositories()` で YAML を読む。
   - loader error があれば Job を失敗または warning にする。repository file 自体が読めない場合は失敗扱いがよい。
   - `analyze_repositories()` を呼ぶ。
   - summary と details を JSON で Job Result ログに出す。
   - ファイル書き込みはしない。

5. Keep Nautobot import fallback narrow.

   この workspace では Nautobot が入っていない可能性があるため、既存の local test 方針は維持する。

   ただし `jobs.py` は Nautobot runtime で正しく import される必要がある。Nautobot がない環境で pure Python テストが壊れないよう、Job class 以外の解析ロジックを `analysis.py` に閉じ込める。

6. Add tests for pure Python behavior.

   Nautobot なしで最低限以下を確認する。

   - loader が `catalog_paths` と `basic_file_paths` defaults を適用する。
   - disabled repository は `skipped` になり fetcher を呼ばない。
   - `catalog-info.yaml` がない場合は `insufficient` になる。
   - `catalog-info.yaml` に service component がある場合は candidate が生成される。
   - service name は slugified される。
   - non-service component は candidate にならない。

   外部通信を避けるため、`RepositoryFileFetcher` を直接ネットワークに出さず、fake fetcher または small test helper を使う。

7. Compile and package check.

   実装後に以下を実行する。

   ```bash
   python3 -m compileall nprojects/nautobot_service_catalog
   python3 -m pip wheel ./nprojects --no-deps -w /tmp/nautobot_service_catalog_wheel_test
   ```

   pytest を追加した場合は以下も実行する。

   ```bash
   python3 -m pytest nprojects/nautobot_service_catalog/tests
   ```

8. Nautobot runtime smoke test.

   実際の Nautobot 環境で確認する。

   - `pip install -e /path/to/nprojects`
   - `PLUGINS` に `"nautobot_service_catalog"` があることを確認する。
   - `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]` を絶対パスで設定する。
   - Nautobot web と worker を再起動する。
   - Jobs 画面に `Analyze Service Repositories` が出ることを確認する。
   - 空 YAML で repositories=0, services=0 の dry-run が成功することを確認する。
   - テスト用 repository entry を追加して catalog detection のログを確認する。

## Suggested Data Shapes

Repository analysis item:

```yaml
repository: example-service
url: https://github.com/example/example-service
enabled: true
status: catalog_parsed
reasons:
  - desired_services_generated
default_branch: main
ref: main
catalog_path: catalog-info.yaml
checked_files:
  - README.md
  - catalog-info.yaml
fetched_basic_files:
  - README.md
catalog_entity_count: 1
generated_service_count: 1
```

Desired service preview:

```yaml
name: example-service
display_name: Example Service
role: service
required: true
min_instances: 1
max_instances: 1
prefers_gpu: false
protocol: http
source_repository:
  url: https://github.com/example/example-service
  ref: main
  catalog_path: catalog-info.yaml
catalog:
  kind: Component
  metadata_name: example-service
  spec_type: service
  lifecycle: production
  owner: platform
analysis:
  status: catalog_derived
  confidence: medium
  reasons:
    - backstage_component_catalog_found
```

## Acceptance Criteria

- `nautobot_service_catalog.analysis` can analyze repositories without importing Nautobot.
- App Job can be imported in a Nautobot environment.
- Empty `service_repositories: []` completes with repositories=0 and services=0.
- Disabled repositories are reported as skipped without remote fetch.
- A Backstage `Component` with `spec.type: service`, `website`, or `worker` generates a service candidate preview.
- Missing `catalog-info.yaml` results in `status: insufficient` and a clear reason.
- The implementation performs no DB migrations and creates no persistent records.
- The existing `nauto` Jobs remain available and unchanged unless a separate compatibility refactor is explicitly planned.

## Risks and Mitigations

- Network calls can hang or fail.
  Use `fetch_timeout`, catch provider errors, and summarize failures per repository.

- GitHub/GitLab API rate limits may affect tests.
  Unit tests must use fakes. Runtime smoke tests should use one or two known repositories only.

- Nautobot Job APIs may differ by installed version.
  Keep `analysis.py` independent and make `jobs.py` the only version-sensitive layer.

- Loader defaults can change behavior from Plan 1 display-only mode.
  Update the template or labels so operators understand defaulted paths are being used.

## Follow-up After Plan 2

- Add a repository detail or analysis preview page if Job logs are too hard to read.
- Consider writing generated dry-run YAML to a temporary artifact only if Nautobot Job Result supports it cleanly.
- Decide whether to refactor `nauto/jobs/generate_desired_services.py` to call App service code, or keep duplication until Phase 3.
- Start Phase 3 only after the analysis data shape has proven stable enough for models.
