# Report — Step 1: Manual / URL-less IntentSource declarations

実施日: 2026-06-29
対象: `nintent/nautobot_intent_catalog`
ステータス: **完了**（ユニットテスト 198 件 すべて pass）

## 目的（plan.md Step 1）

intent YAML の `intent_sources` ルートで、`url` を持たない手動
（`source_type: manual`）のスラッグ識別ソースを宣言できるようにする。

## 変更内容

### 1. `loaders.py`
- `IntentSourceEntry` を拡張:
  - `url` を `str | None = None`（任意化）
  - `slug` / `name` / `source_type`（デフォルト `git_repository`）を追加
- `_normalize_intent_source_entry` を書き換え:
  - 未知キーを厳格に拒否（他の strict ルートと同様のメッセージ形式
    `intent_sources entry N has unknown fields: ...`）
  - `source_type` を `{git_repository, manual}` から検証（デフォルト
    `git_repository`）
  - `git_repository` は従来どおり `url` 必須、`manual`（非 Git）は `slug`
    必須・`url` 任意
  - `slug` 指定時は小文字スラッグ形式を検証
- モジュール定数 `_INTENT_SOURCE_TYPES` / `_INTENT_SOURCE_KEYS` を追加

### 2. `importers.py`
- `intent_source_defaults` のハードコード `source_type="git_repository"` を撤廃し、
  エントリの `source_type` を反映:
  - Git: 従来どおり `url` から name/slug を導出（`name`/`slug` の明示指定も尊重）
  - manual: `slug` を識別子に、name は `name → service_hint → slug` でフォールバック
  - manual では `url` を defaults に含めない（モデルの nullable url は None のまま）

### 3. `jobs.py`
- `_import_intent_rows` の IntentSource upsert を source_type 別に分岐:
  - Git は `{"url": ...}`、manual は `{"slug": ...}` を identity に使用
- `disable_missing` を `url__in` 単独から `url__in` かつ `slug__in` の二重除外に変更
  （url=None の manual ソースが誤って無効化されるのを防止）
- `_entry_from_intent_source` が `slug` / `name` / `source_type` も引き継ぐよう更新

## テスト追加

### `tests/test_loaders.py`
- manual ソース（url なし）が正常に正規化される
- manual ソースで `slug` 欠落時にエラー
- Git ソースで `url` 欠落時にエラー（従来挙動維持）
- 未知キーの拒否

### `tests/test_importers.py`
- manual ソースの `intent_source_defaults`（slug/name/source_type、url 不在）
- manual の name フォールバック（slug → name）

## 受け入れ基準（plan.md Step 1）

`{slug: infrastructure, name: Infrastructure, source_type: manual}` が
エラーなく正規化され、importer defaults が `source_type=manual` / url なし /
slug `infrastructure` を返すこと → **充足**
（`test_loader_accepts_manual_intent_source_without_url` /
`test_intent_source_defaults_for_manual_source`）

## 検証

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 198 tests in 0.021s
OK
```

制約どおり純粋ユニットテストのみ。Nautobot ランタイム挙動（`update_or_create`
での実 DB upsert、Job 実行、UI）はローカル未検証で、後続の手動検証対象。

## 後続への申し送り

- jobs.py の identity 分岐（実 DB upsert 経路）はランタイム制約によりローカル
  ユニットテスト不可。Step 7 の手動検証項目として `Import Intent Sources` 実行で
  manual ソースが slug でべき等 upsert されることを確認すること。
- スキーマ変更は発生せず（モデルは既に `manual` / nullable url をサポート）、
  plan の「スキーマ変更ゼロ」前提を維持。
- 次は Step 2（`desired_services` インポートルートの追加）。本 Step で manual
  `IntentSource` の宣言基盤が整ったため、その所有元として参照可能。
