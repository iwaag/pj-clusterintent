# Report — Step 2: REST API

実施日: 2026-08-04
対象: `nintent` (submodule)
ステータス: **完了**（label test_workflow_episode: 17 pass / full nautobot_intent_catalog runtime gate: 245 pass、`--keepdb`）

## 目的（p1/plan.md Step 2）

`WorkflowEpisode` の REST API（CRUD + 遷移アクション + namespace書き込みアクション、
top-level namespace / schema_version検証込み）を追加し、runtime gate `--keepdb` を green にする。

## 変更内容

### 1. `nautobot_intent_catalog/api/serializers.py`
- `WorkflowEpisodeSerializer`（`NautobotModelSerializer`）を追加
  - `fields = (id, title, status, raw_data, created, last_updated)`、
    `read_only_fields` に `status` を含める（PATCH経由の直接status変更を構造的に封じる）
  - `to_internal_value`: 許可キーは `{title, raw_data}` のみ（Braindumpの
    `_check_allowed_mutation_keys` を再利用）。`status` を含む作成リクエストは400で拒否
    （roadmapの「ignore/reject client-supplied status on create」のうちrejectを選択）
  - `validate_raw_data`: Step 1の `workflow_episode_contract.validate_raw_data_shape` を呼ぶ
    （1つの所有者を維持）

### 2. `nautobot_intent_catalog/api/views.py`
- `WorkflowEpisodeViewSet(NautobotModelViewSet)` を追加
  - `http_method_names = ["get", "post", "head", "options"]`（Braindump踏襲）。
    PUT/PATCH自体が存在しないため、`raw_data`全体置換や`status`直接変更の経路が構造的に無い
  - 遷移アクション: `select` / `resolve` / `dismiss`（すべて `POST detail`）。
    共通の `_transition()` が `select_for_update()` + `workflow_episode_contract.validate_transition`
    を呼び、違反時は現在状態を含む409を返す
  - namespace書き込みアクション: `report` / `assessment` / `references` / `resolution`
    （すべて `POST detail`）。共通の `_write_namespace()` がリクエストボディ全体をその
    namespaceの値として丸ごと置換（decision 5どおりdeep mergeではない）。他namespaceは
    `{**episode.raw_data, namespace: ...}` でそのまま温存し、`validated_save()`（`clean()`経由で
    namespace検証も再実行）で保存
  - リクエストボディが dict でない場合は400（`report`等のnamespace書き込みアクション）

### 3. `nautobot_intent_catalog/filters.py`
- `WorkflowEpisodeFilterSet` を追加（`id`/`title`/`status` + `q`によるtitle部分一致検索）。
  Step 3のGUI一覧・API一覧の両方で使う

### 4. `nautobot_intent_catalog/api/urls.py`
- `router.register("workflow-episodes", views.WorkflowEpisodeViewSet)` を追加

## テスト追加

### `nautobot_intent_catalog/tests/test_workflow_episode.py`（新規、17 tests、runtime gate専用）
Braindumpの `test_braindump.py` と同じ `try/except ImportError` ガード形式。

- **モデル系（Tier B、5 tests）**: statusデフォルトcandidate、raw_dataデフォルト空dict、
  空文字/空白のみtitle拒否、未知namespace拒否、非dict namespace値拒否、正当payload受理
- **API系（Tier A、12 tests）**:
  - create→read、PATCH/PUT/DELETEがすべて405で拒否されること
  - `status`をcreateペイロードに含めると400で拒否されoutcomeも作成されないこと
  - 未知namespaceを含むcreateが400
  - `select→resolve`の完全ラウンドトリップ、`candidate→dismissed`の直接遷移
  - **2回目のselectが409で拒否**され、statusが`selected`のまま変化しないこと
  - **`resolve`をselectなしで呼ぶと409**（candidateのまま）
  - **PATCHでのstatus変更が405**で拒否されること
  - **namespace書き込みが対象namespaceのみ更新し、他namespaceはbyte-identicalに残る**こと
    （decision 5の保証を直接アサート）
  - namespace書き込みがdeep mergeでなく丸ごと置換であること（既存キーが消えることを確認）
  - namespace書き込みのボディが非オブジェクトなら400

## 検証

```
$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_workflow_episode
Found 17 test(s).
Ran 17 tests in 0.514s
OK
runtime gate result mode=keepdb label=nautobot_intent_catalog.tests.test_workflow_episode cases=17

$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog
Found 245 test(s).
Ran 245 tests in 6.368s
OK
runtime gate result mode=keepdb label=nautobot_intent_catalog cases=245
```

両実行とも `nautobot-server makemigrations --check --dry-run` が `No changes detected` を
返しており、Step 1のマイグレーション `0029_workflowepisode` がモデル定義と一致していることを
併せて確認した。

## 後続への申し送り

- Step 3 は読み取り専用GUI（list/detail view, table, template, URL, nav）。
  `WorkflowEpisodeFilterSet` は本Stepで既に用意済みのため、GUI一覧はそのまま使える。
  デフォルトfilterで `candidate` + `selected` のみ表示する要件（roadmap「Useful facts」）は
  view側のデフォルトqueryset/filter paramsで実装する。
- fast suite（Django-free）は本Stepでは変化なし（142 pass, skipped=10のまま）。
  API/viewsetコードはDjango依存のためfast suiteの対象外。
