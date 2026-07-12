# Report — Step 2: `desired_services` import root

実施日: 2026-06-29
対象: `nintent/nautobot_intent_catalog`
ステータス: **完了**（ユニットテスト 203 件 すべて pass）

## 目的（plan.md Step 2）

intent YAML に `desired_services` ルートを追加し、固定／手動サービスを宣言して
`Import Intent Sources` で取り込めるようにする。識別キーはモデルの一意制約
`(intent_source, catalog_namespace, catalog_metadata_name, service_type)` に一致。

## 変更内容

### 1. `loaders.py`
- `DesiredServiceEntry` dataclass を追加（識別フィールド + 表示/ライフサイクル +
  任意の catalog 系フィールド）。
  - 必須: `intent_source`(slug), `catalog_metadata_name`, `service_type`,
    `name`, `display_name`
  - 既定値: `catalog_namespace="default"`, `lifecycle="proposed"`,
    `slug`（未指定時は `name` から導出）
  - 任意: `catalog_kind`/`catalog_owner`/`catalog_lifecycle`/`source_ref`/
    `source_catalog_path`/`prefers_gpu`/`min_memory_gb`/`notes`
- `_normalize_desired_service_entry` を追加（`_strict_mapping_errors` による
  allowed/required 厳格チェック、`service_type` を `_SERVICE_TYPES` で検証、
  `lifecycle` を `_LIFECYCLES_SERVICE`（proposed を含む）で検証、slug/name は
  小文字スラッグ検証）。
- `load_intent_sources` に `desired_services` セクション解析を追加。
- `_duplicate_service_errors` で識別キー重複を検出。
- `IntentSourceLoadResult` に `desired_services` フィールドを追加。
- ヘルパー `_optional_number` と定数 `_LIFECYCLES_SERVICE` / `_SERVICE_TYPES`
  を追加。

### 2. `importers.py`
- `desired_service_entry_identity(entry, intent_source_id)` を追加（4 つの識別
  キーを返す）。
- `desired_service_entry_defaults(entry)` を追加（識別キー以外のモデル defaults）。
- 既存の解析用 `desired_service_identity` / `desired_service_defaults`（catalog
  ネスト dict 形状）とは別関数とし、コードベース既存の「dataclass ごとに
  identity/defaults」規約に合わせた。

### 3. `jobs.py`
- `_import_intent_rows` で `desired_services` を **intent_sources の後・
  desired_service_placements の前** にインポート（同一ドキュメント内サービスを
  placement が解決できる順序）。
- 所有元 `IntentSource` を `source_by_key`（slug ルックアップ）で解決。未知 slug
  参照時は明示的に `ValueError`。
- `services_created/updated/unchanged` カウントを集計に追加。
- インポートサマリーログに `desired_services` 件数を追加。

## テスト追加

### `tests/test_loaders.py`
- `desired_services` ブロックの正常パース（slug 導出・namespace/lifecycle 既定値）
- 必須フィールド欠落エラー
- 未知キー拒否
- 識別キー重複検出

### `tests/test_importers.py`
- `desired_service_entry_identity` / `desired_service_entry_defaults` の出力検証

## 受け入れ基準（plan.md Step 2）

- ローダーが `desired_services` ブロックをパース → 充足
- importer ヘルパーが正しい identity/defaults を生成 → 充足
- 同一ドキュメント内宣言サービスへの placement 解決 → インポート順序で担保。
  解決機構 `_resolve_desired_service`（`intent_source__slug` + catalog 識別）は
  既存の `test_jobs_import.py::test_service_resolution_uses_the_complete_qualified_identity`
  で検証済み。

## 検証

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 203 tests in 0.022s
OK
```

純粋ユニットテストのみ（制約準拠）。

## 後続への申し送り

- `_import_intent_rows` の end-to-end（実 DB upsert + transaction）はローカル
  ユニット未検証。既存テストスイートも本関数を end-to-end ではフェイク化して
  いないため、同一方針を維持。Step 7 の手動検証で、同一 YAML 内の service →
  placement 取り込みがべき等に成功することを確認すること。
- `min_memory_gb` はモデル上 `DecimalField`。ローダーは float を渡し、`full_clean`
  時に Decimal へ強制される想定（ローカルでは DB 非依存のため未検証）。
- 次は Step 3（任意の手動 DesiredService 追加 UI ルート。安価なら実施、でなければ
  defer）／または Step 4–5（nauto 側のシード撤去と intent YAML への内容移設）。
  本 Step で nintent 側の宣言・取り込み基盤が揃ったため、Step 5 の移設先が利用可能。
