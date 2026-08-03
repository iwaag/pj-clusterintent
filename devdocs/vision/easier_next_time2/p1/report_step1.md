# Report — Step 1: モデル + マイグレーション + fast tests

実施日: 2026-08-04
対象: `nintent` (submodule)
ステータス: **完了**（fast suite: 142 pass, skipped=10 — 変更前130 pass, skipped=10）

## 目的（p1/plan.md Step 1）

`WorkflowEpisode(title, status, raw_data)` モデルとマイグレーション `0029` を追加し、
遷移表・namespace検証を Django-free の純粋関数として実装、fast suite を green にする。

## 変更内容

### 1. `nautobot_intent_catalog/workflow_episode_contract.py`（新規）
`compute_contract.py` と同じ設計（Django非依存の純粋モジュール）:
- `STATUS_CANDIDATE`/`SELECTED`/`RESOLVED`/`DISMISSED` 定数、`STATUS_CHOICES`
- `ALLOWED_TRANSITIONS`: `candidate → {selected, dismissed}`,
  `selected → {resolved, dismissed}`, `resolved → {}`, `dismissed → {}`
  （roadmap決定3どおり forward-only、selected→candidateの降格なし）
- `validate_transition(current, new)`: 許可されない遷移を`WorkflowEpisodeContractError`で拒否
- `validate_raw_data_shape(raw_data)`: トップレベルキーが
  `{schema_version, report, assessment, references, resolution}` の部分集合であることのみ検証
  （sub-fieldsはfree-form、roadmap決定4）。namespace値はdict必須、`schema_version`はint必須

### 2. `nautobot_intent_catalog/models.py`
- `WorkflowEpisode(PrimaryModel)` を追加（`@extras_features("graphql")` 付き、Braindump踏襲）
- フィールドは `title`（CharField 255）/ `status`（CharField, choices, default=candidate）/
  `raw_data`（JSONField, default=dict）のみ（roadmap決定1）
- `ALLOWED_TRANSITIONS` はモデルのクラス属性としても公開し、contract モジュールと1つの所有者を共有
- `clean()`: title非空検証 + `validate_raw_data_shape` 呼び出し（直接ORM書き込み時の検証）
- `apply_transition(new_status)`: contract の `validate_transition` を呼び、通れば `status` を更新
  （API側のtransition actionsがStep 2でこれを呼ぶ想定）

### 3. `nautobot_intent_catalog/migrations/0029_workflowepisode.py`（新規）
`0027_desiredworkspace.py` を型として作成。`PrimaryModel` 標準フィールド + `title` / `status`
（choices固定4値、default candidate）/ `raw_data`（JSONField, default dict）。
依存先は直前のマイグレーション `0028_remove_desirednodeoperationaloverride_declared_host_os`。

## テスト追加

### `nautobot_intent_catalog/tests/test_workflow_episode_contract.py`（新規、12 tests、Django非依存）
- 遷移: 許可される全遷移が成功（`test_every_allowed_transition_succeeds`）
- 禁止遷移: `selected→candidate` 降格拒否、`resolved`/`dismissed` からの全遷移拒否（終端状態）、
  自己遷移拒否、未知の現在状態拒否
- namespace検証: 4namespace + schema_version全部入りの正当ペイロード受理、空dict受理、
  非dict raw_data拒否、未知トップレベルキー拒否、非dict namespace値拒否、非int schema_version拒否

## 検証

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 142 tests in 0.004s
OK (skipped=10)
```

変更前は130 pass/skipped=10（`git stash`せず差分で確認: 追加12 testsがそのまま加算、
既存のskip数は変化なし = Django依存テストファイルの収集経路に影響を与えていないことを確認）。

マイグレーション自体の適用可否（`nautobot-server migrate`）はDjango-free環境では検証できない。
Step 2のruntime gate (`--keepdb`) で確認する。

## 後続への申し送り

- Step 2 は REST API（serializer/viewset/transition actions/namespace-write actions）。
  `apply_transition` と `validate_raw_data_shape` をそのまま呼び出す想定で、遷移ロジック・
  namespace検証の「1つの所有者」はこの Step 1 の contract モジュールに置いた。
- `get_absolute_url` は `plugins:nautobot_intent_catalog:workflowepisode` を参照しているが、
  URLパターン自体は Step 3（GUI）で追加する。それまでは未使用（Braindump/DesiredWorkspaceも同型）。
