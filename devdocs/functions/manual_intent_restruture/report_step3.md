# Report — Step 3: Manual DesiredService CRUD add route

実施日: 2026-06-29
対象: `nintent/nautobot_intent_catalog`
ステータス: **完了**（既存ユニットテスト 203 件 pass / UI はランタイム手動検証対象）

## 目的（plan.md Step 3）

UI から手動でサービスをアドホック作成できるようにする（YAML インポートが
主経路、本ルートは副次）。

## 変更内容

### `urls.py`
- `services/add/` を `views.DesiredServiceEditView`（既存の ObjectEditView）に
  マップし、ルート名 `desiredservice_add` を追加。
- 既存の `nodes/add/`（`desirednode_add`）/ `endpoints/add/`
  （`desiredendpoint_add`）と同一パターン。

既存の `DesiredServiceEditView` と `DesiredServiceForm` をそのまま利用。フォーム
（[forms.py](../../nintent/nautobot_intent_catalog/forms.py) の
`DesiredServiceForm`）は `intent_source` を含む全フィールドを既に公開しており、
追加実装は不要。

## navigation.py（意図的に変更なし）

plan では「optional menu entry near Desired Services」とされているが、本リポジトリ
の nav 規約では:
- 追加可能なモデル（nodes / endpoints）も `_add` ルートのみ持ち、専用の nav
  「追加」項目は持たない。
- nav に独立項目を持つのは *quick-add*（簡易フロー）のみ。

Nautobot の `ObjectListView` は `<app>:<model>_add` ルートが存在すると一覧画面に
「Add」ボタンを自動表示するため、`desiredservice_add` ルート追加だけで UI からの
作成導線は有効になる。冗長な nav 項目を避け、既存モデルとの一貫性を優先して
nav は変更しなかった。

## 検証

- `python3 -m py_compile urls.py navigation.py` → OK
- `python3 -m unittest discover -s nautobot_intent_catalog/tests` → 203 件 pass
  （ローダー／インポーター層に退行なし）

UI ルートおよびビューは Nautobot ランタイム依存のためローカルではユニット検証
不可（no-live-env 制約）。本ルートは既存の add ルートと構造的に同一。

## 後続への申し送り（手動検証項目）

- Nautobot 起動後、`/plugins/intent-catalog/services/add/` で `DesiredServiceForm`
  が表示され、`intent_source`（manual ソース含む）を選択してサービスを作成できる
  こと。
- Desired Services 一覧画面に「Add」ボタンが自動表示されること。
- 次は Step 4–5（nauto のシード撤去と intent YAML への内容移設）。Step 1–3 で
  nintent 側の宣言（YAML）・取り込み・UI 作成の各経路が揃った。
