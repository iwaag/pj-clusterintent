# Report — Step 3: 読み取り専用GUI

実施日: 2026-08-04
対象: `nintent` (submodule)
ステータス: **完了**（label test_workflow_episode: 25 pass / full nautobot_intent_catalog runtime gate: 253 pass、`--keepdb`）

## 目的（p1/plan.md Step 3）

`WorkflowEpisode` の list/detail view・table・filterset（Step 2で用意済み）・template・URL・
nav entryを追加し、runtime gate `--keepdb` を green にする（GUI smoke含む）。

## 変更内容

### 1. `nautobot_intent_catalog/tables.py`
`WorkflowEpisodeTable`（`BaseTable`）を追加。列は `id`/`title`/`status`/`created`/`last_updated`、
`default_columns` は `title`/`status`/`created`/`last_updated`（idは常時表示不要のため除外）。

### 2. `nautobot_intent_catalog/views.py`
- `WorkflowEpisodeListView(ObjectListView)`: `queryset`/`filterset`（Step 2の
  `WorkflowEpisodeFilterSet`）/`table`
  - `get_filter_params()` をオーバーライドし、`status` パラメータが指定されていない場合のみ
    `[candidate, selected]` をデフォルト注入（roadmap「Useful facts」のデフォルトフィルタ要件）。
    `?status=resolved` 等の明示指定は上書きせずそのまま尊重されるため、`resolved`/`dismissed`への
    到達経路は塞がない
- `WorkflowEpisodeView(ObjectView)`: `queryset` のみ

### 3. `nautobot_intent_catalog/templates/nautobot_intent_catalog/workflowepisode.html`（新規）
Braindump踏襲のパネル構成。基本属性パネル（title/status/created/last_updated）に続けて
report/assessment/references/resolutionの4パネルを固定順で描画（discuss_idea1 §5どおり、
raw JSONダンプだけでなくセクション分割）。各namespaceは
`{% for key, value in object.raw_data.<namespace>.items %}` という単純なkey/valueテーブルで、
namespace未記録時は「Not yet recorded.」を表示。末尾に `<pre>{{ object.raw_data }}</pre>` の
raw dumpパネルを追加（plan設計ヒントどおり、pretty-print用の追加インフラは作らない）。

### 4. `nautobot_intent_catalog/urls.py` / `navigation.py`
- `workflow-episodes/` (list) / `workflow-episodes/<uuid:pk>/` (detail) を追加
- nav に新規グループ「Workflow Improvement」（weight=150、Braindump=100とDesired State=200の間）
  を追加し、"Workflow Episodes" 1項目を配置

### 5. `nautobot_intent_catalog/tests/test_ui_contract.py`（既存の契約テストを更新）
新規GUIページの追加によりnav・route manifestの契約テストが崩れたため、事実に合わせて更新:
- `RETAINED_UI_ROUTE_NAMES` に `workflowepisode_list`/`workflowepisode` を追加（22→24件）
- `MODEL_URL_PREFIXES` に `"workflowepisode_list": ("workflow-episodes", False)` を追加
  （addルートを一度も持たない新規モデルのため`has_add=False`）
- テスト名を実態に合わせて改名: `test_retained_routes_count_is_22` →
  `_is_24`、`test_navigation_only_links_the_eleven_retained_lists` → `_the_twelve_retained_lists`

## テスト追加

### `nautobot_intent_catalog/tests/test_workflow_episode.py`（追加、`WorkflowEpisodeViewTests` 8 tests）
- 一覧: htmxリクエストでの行表示（Nautobot 3.1の仕様どおり非htmx初回ロードは空シェル）
- **デフォルトフィルタ**: `candidate`ステータスは表示され、`resolved`にした行は表示されないこと
- **明示フィルタでresolvedにも到達できる**こと（`?status=resolved`）
- 詳細: 4namespace全部入りのepisodeで4つの値がすべて表示されること
- 詳細: namespace未記録時に「Not yet recorded.」が表示されること
- 詳細: title/report内の `<script>` 等がエスケープされ、生スクリプトタグが出力されないこと
- 詳細: mutation control（submit/csrf/Add/Edit/Delete）が一切存在しないこと
- 一覧・詳細へのPOSTがミューテーションを起こさないこと

## 検証

```
$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog.tests.test_workflow_episode
Found 25 test(s).
Ran 25 tests in 0.953s
OK
runtime gate result mode=keepdb label=nautobot_intent_catalog.tests.test_workflow_episode cases=25

$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb nautobot_intent_catalog
Found 253 test(s).
Ran 253 tests in 6.723s
OK
runtime gate result mode=keepdb label=nautobot_intent_catalog cases=253
```

`nautobot-server makemigrations --check --dry-run` は両実行とも `No changes detected`。
fast suite（Django-free）は変化なし（142 pass, skipped=10）。

## 後続への申し送り

- Step 4 は最終ゲート（fast suite + runtime gate `--clean`、`cases=` 記録）。本Stepの
  `--keepdb` グリーンを土台に、fresh `test_nautobot` でのmigration検証を行う。
- GUIのnav配置・URL prefixは実装者裁量どおり確定。将来「候補が実際に出た経験」に基づく
  presentation変更はPhase 4の評価で対応する想定（roadmap決定10の範囲内）。
