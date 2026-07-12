# Report — Step 4 & 5: nauto のシード撤去と intent YAML への内容移設

実施日: 2026-06-29
対象: `nauto/jobs/seed_home_cluster.py`, `nauto/seed/home_cluster.yaml`,
`nauto/seed/intent_sources.yaml`
ステータス: **完了**（YAML はnintentローダーで検証 / nintent 203件 pass）

## 目的（plan.md Step 4–5）

- Step 4: `nauto` の `Seed Home Cluster` から intent シード（IntentSource /
  DesiredService 作成）を撤去し、taxonomy ブートストラップのみに縮小。
- Step 5: 固定サービスの intent 内容を nintent の intent YAML
  (`intent_sources.yaml`) へ移設（所有権の移動）。`dnsmasq` を追加。

## 変更内容

### Step 4 — `jobs/seed_home_cluster.py`
- `nautobot_intent_catalog.models`（`DesiredService` / `IntentSource`）の
  try/except import を削除（撤去メソッド専用だったため）。
- `run` 内の呼び出し `ensure_intent_sources(...)` /
  `ensure_desired_services(...)` を削除。
- メソッド `ensure_intent_sources` / `ensure_desired_services` を削除。
- taxonomy ブートストラップ（statuses / location_types / locations / roles /
  manufacturers / device_types / tags / custom_fields）は維持。
- `slugify` は taxonomy 側 ensure メソッドが使用しているため保持。
- 破壊的変更フェーズの方針に従い、後方互換シムは残さず完全削除。

### Step 5a — `seed/home_cluster.yaml`
- `intent_sources` ブロックと `desired_services` ブロックを削除。
- 残存トップキー: location_types / locations / statuses / roles /
  manufacturers / device_types / tags / custom_fields（taxonomy のみ）。

### Step 5b — `seed/intent_sources.yaml`（nintent の intent source-of-truth）
- `intent_sources: []` を、manual ソース `slug: infrastructure`
  （`source_type: manual`, url なし）に置換。
- `desired_services` ブロックを追加。移設したサービス:
  prometheus / grafana / nomad / prometheus-node-exporter / haos に加え、
  **dnsmasq**（本作業の動機となった欠落サービス）を新規追加。
- 既存の `desired_service_placements`（同ファイル内）は同一の識別キー
  （intent_source=infrastructure, catalog_namespace=default,
  catalog_metadata_name, service_type=service）で移設サービスを参照するため、
  解決可能。

## 検証

nintent の実ローダーで `intent_sources.yaml` をパース:

```
errors: []
intent_sources: [('infrastructure', 'manual', None)]
desired_services: 6 件（dnsmasq/prometheus/grafana/nomad/
                          prometheus-node-exporter/haos, 全て active）
placements without a declared service: []   # 全 placement が宣言済みサービスに解決
```

- `home_cluster.yaml`: YAML 妥当・intent_sources/desired_services 不在を確認。
- `seed_home_cluster.py` / `jobs/__init__.py`: `py_compile` OK。
- nintent ユニットテスト: 203 件 pass（退行なし）。
- nauto 既存テスト（`test_nodeutils_ingest_batch.py` /
  `test_service_placement_eval.py`）は seed_home_cluster と無関係。撤去メソッドを
  参照する nauto テストは存在しないため、Step 7 の「SeedHomeCluster テスト更新」は
  対象なし。

## 留意点 / 申し送り

- `jobs/generate_desired_services.py` は `desired_services` 名称を含むが、plan の
  Non-goal（git 解析重複の整理）であり本作業では未変更。
- intent YAML ファイルが物理的に `nauto/seed/` 配下に残る点は plan の Non-goal
  （所有権は nintent、配置の移動は後続）。
- **運用ロールアウト（plan Step 6 / Risks）**: デプロイ後、固定サービス intent は
  更新後 YAML に対し `Import Intent Sources` を実行して初めて反映される。旧
  `Seed Home Cluster` はもう作成しないため、デプロイ直後に intent が一時的に
  失われないよう実行順序の周知が必要。識別キー（IntentSource slug=infrastructure、
  サービスの catalog 識別）は旧シードと一致するため、`Import Intent Sources` は
  既存行を **in-place で更新**（重複や孤児なし）する想定。
- 実 DB での upsert べき等性（Step 6 の確認）と Job 実行は no-live-env 制約により
  ローカル未検証。手動検証項目として残す。
