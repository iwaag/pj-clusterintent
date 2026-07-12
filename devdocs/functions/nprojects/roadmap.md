# nprojects Nautobot App Roadmap

## Goal

`nprojects` を Nautobot App として育て、クラスタで稼働させたいサービスの入力リポジトリ一覧、Backstage `catalog-info.yaml` 解析結果、サービス配置候補を Nautobot GUI と API から扱えるようにする。

最初の目的は小さく保つ。まずは [nauto/seed/service_repositories.yaml](../../nauto/seed/service_repositories.yaml) の内容を Nautobot GUI で一覧表示できる状態にする。その後、既存 Job の解析ロジックを段階的に App 側へ移す。

## Current State

- `nauto` は Nautobot Git Repository として登録する Jobs 集。
- `service_repositories.yaml` はリポジトリ入力一覧の source of truth。
- `Generate Desired Services` Job は `catalog-info.yaml` と基本ファイルを軽量取得し、`desired_services.generated.yaml` を生成できる。
- `Service Placement Review` Job は `desired_services.yaml` と Device custom fields を使って配置レビューを行う。
- `nprojects` は現時点ではほぼ空で、Nautobot App としての実装はない。

## Guiding Principles

- 最初は DB 化しない。YAML を読み取り専用で表示するだけにして、App の導入経路を確認する。
- 既存の `nauto` Jobs をすぐ置き換えない。動いている Git Jobs workflow は互換経路として残す。
- App 側に移すロジックは、Job 直下ではなく再利用可能な service 層に置く。
- Nautobot の Device custom fields は host-local facts として扱う。クラスタ全体の desired service intent は専用 YAML または App model に置く。
- Backstage `spec.dependsOn` は desirable state の一部として扱う。最初は dependency metadata として保持し、後続 phase で unresolved component/resource を service candidate や required infrastructure intent に昇格できるようにする。
- DB model は UI 編集、API 利用、change logging、object permission が必要になってから導入する。

## Phase 1: Minimal Read-only App

目的: `service_repositories.yaml` を Nautobot GUI で一覧表示する。

実装範囲:

- `nprojects` に Python package として Nautobot App を作る。
- `NautobotAppConfig` を定義する。
- `/plugins/<base_url>/repositories/` のような URL を追加する。
- YAML を読み込む loader を作る。
- `url`, `enabled`, `ref`, `owner`, `service_hint`, `catalog_paths`, `basic_file_paths` を表形式で表示する。
- navigation から一覧画面へ移動できるようにする。
- YAML が空、存在しない、不正形式のときに画面上で分かるようにする。

この段階でやらないこと:

- DB model 作成。
- migration 作成。
- Nautobot API 追加。
- YAML の GUI 編集。
- GitHub/GitLab への通信。
- `catalog-info.yaml` 解析。

完了条件:

- Nautobot に App をインストールして `PLUGINS` に追加できる。
- GUI で入力リポジトリ一覧が見える。
- `service_repositories: []` の空状態も壊れず表示できる。

## Phase 2: Repository Analysis Preview

目的: 既存 `Generate Desired Services` の解析結果を App GUI で確認できるようにする。

実装範囲:

- `nauto/jobs/generate_desired_services.py` の `RepositorySpec`, fetcher, catalog parser 相当を App の service 層へ移植または共通化する。
- GUI から dry-run 解析を実行する Job を App 側に追加する。
- 解析結果を Job Result ログ、または一時的な画面表示として確認する。
- `catalog-info.yaml` が見つかったか、Backstage Component として解釈できたか、解析不足かを表示する。

この段階でやらないこと:

- 解析結果の永続 DB 保存。
- サービス配置の確定。
- GUI からのリポジトリ編集。

完了条件:

- YAML 一覧から、どのリポジトリが解析可能か確認できる。
- 既存 `Generate Desired Services` と同等の基本的な catalog detection ができる。

## Phase 2.1: Dependency-aware Analysis Output

目的: Backstage `catalog-info.yaml` の `spec.dependsOn` を解析し、desired service candidate の一部として依存関係を出力する。

背景:

- `dependsOn` には `resource:default/minio-s3`, `resource:default/postgresql`, `component:default/keycloak` のような参照が入る。
- これらは対象 service が成立するために必要な dependency であり、最終的には desirable state として扱う必要がある。
- ただし `resource` はクラスタ内に deploy する service なのか、外部/共有 resource なのかを即断できないため、Phase 2.1 では candidate 本体とは分けて dependency metadata として出力する。

実装範囲:

- `spec.dependsOn` を parse し、`kind`, `namespace`, `name`, `raw_ref` に正規化する。
- generated desired service candidate に `dependencies` を追加する。
- `component:*` dependency は unresolved component dependency として analysis summary に出す。
- `resource:*` dependency は required resource dependency として analysis summary に出す。
- malformed dependency ref は解析全体を失敗させず、warning/reason として出す。
- 既存 `nauto` Job の compatibility output でも同じ dependency 情報を出せるようにするか、少なくとも App service 層の出力を source of truth にできる形にする。

この段階でやらないこと:

- dependency を DB model として永続化しない。
- `resource:*` を自動で deploy 対象 service に変換しない。
- `component:*` の repository を自動探索しない。
- placement review で dependency readiness 判定まではしない。

完了条件:

- `dependsOn` がある catalog から `dependencies` 付きの desired service candidate が生成される。
- `resource:default/minio-s3`, `resource:default/postgresql`, `component:default/keycloak` が lossless に正規化される。
- unresolved dependency summary が Job Result ログで確認できる。
- Phase 3 の model 設計で dependency を first-class にできるだけの出力形状が固まる。

## Phase 3: Service Catalog Models

目的: リポジトリ入力と解析済みサービス候補を Nautobot DB の first-class object として扱う。

候補 model:

- `ServiceRepository`
  - `url`
  - `enabled`
  - `ref`
  - `owner`
  - `service_hint`
  - `catalog_paths`
  - `basic_file_paths`
  - `raw_url_template`
  - `last_analysis_status`
  - `last_analyzed_at`

- `DesiredServiceCandidate`
  - `name`
  - `display_name`
  - `role`
  - `source_repository`
  - `catalog_kind`
  - `catalog_metadata_name`
  - `catalog_owner`
  - `prefers_gpu`
  - `min_memory_gb`
  - `analysis_status`
  - `analysis_confidence`
  - `analysis_reasons`
  - `notes`

- `ServiceDependency`
  - `source_service`
  - `kind`
  - `namespace`
  - `name`
  - `raw_ref`
  - `dependency_type`
  - `resolution_status`
  - `resolved_service`
  - `notes`

実装範囲:

- models, migrations, tables, filters, forms, views を追加する。
- YAML import Job を作り、既存 `service_repositories.yaml` から `ServiceRepository` に取り込めるようにする。
- YAML export または compatibility output を用意し、既存 Jobs との橋渡しを残す。
- dependency を candidate 本体から分離して扱えるようにし、component dependency と resource dependency を区別して表示する。

完了条件:

- GUI でリポジトリを追加・編集・削除できる。
- 変更履歴や権限など Nautobot 標準機能の恩恵を受けられる。
- 既存 YAML workflow から移行できる。

## Phase 4: Placement Review Integration

目的: サービス候補と Device facts を照合し、クラスタ内の配置候補を Nautobot App 内で見えるようにする。

実装範囲:

- 既存 `Service Placement Review` の deterministic logic を App service 層へ移す。
- Device custom fields の `memory_gb`, `gpu_count`, `gpu_memory_gb`, `observed_services`, `preferred_services`, `agent_task_state` などを入力として使う。
- `DesiredServiceCandidate` ごとに候補 Device、理由、警告を表示する。
- dependency が未解決、未配置、外部 resource のままなのかを placement review の caution として表示する。
- LLM review は補助情報として扱い、構造化された判定と分離する。

候補 model:

- `ServicePlacementReview`
  - `service`
  - `generated_at`
  - `status`
  - `recommended_device`
  - `fallback_devices`
  - `observed_instances`
  - `reasons`
  - `cautions`
  - `confidence`
  - `raw_review`

完了条件:

- サービスごとに配置候補が GUI で確認できる。
- 自動化エージェントが API で参照できる形に近づく。

## Phase 5: Git Datasource and Automation

目的: Git repository sync と App DB 更新を Nautobot の通常運用に統合する。

実装範囲:

- Nautobot datasource content として service repository catalog を扱う。
- Git sync 時に YAML または catalog metadata を import する。
- 定期 Job で repository analysis と placement review を更新する。
- REST API または GraphQL で外部 automation が結果を取得できるようにする。

完了条件:

- Git を source of truth にしたまま Nautobot App DB と GUI が追従する。
- 配置候補を外部 deploy pipeline や agent が取得できる。

## Migration Strategy

1. `nauto` の既存 Jobs は維持する。
2. `nprojects` App は最初、読み取り専用 GUI として追加する。
3. 解析ロジックを App service 層へ移してから、Jobs は薄い呼び出し元にする。
4. DB model 導入後も YAML import/export を残す。
5. `desired_services.yaml` を即廃止しない。承認済み catalog として使い続け、App 側の生成結果と比較できるようにする。

## Risks

- Nautobot のバージョン差で generic view、table、navigation API が変わる可能性がある。
- App install と Git Repository Jobs の lifecycle が異なるため、デプロイ手順を明確にする必要がある。
- リポジトリ解析で外部 Git provider に通信するため、timeout、token、rate limit、proxy を考慮する必要がある。
- `catalog-info.yaml` の schema はチームごとに揺れるため、最初から過剰に厳密にしないほうがよい。

## Open Questions

- App 名は `nautobot_service_catalog` でよいか。
- `service_repositories.yaml` のパスは App 設定、環境変数、または固定相対パスのどれで指定するか。
- 初期段階で `nprojects` 自体を pip install する運用にするか、Nautobot 環境のローカル path install にするか。
- DB 化したあとも Git YAML を source of truth にするか、Nautobot DB を source of truth に切り替えるか。
