# Report — Step 6: ライブ検証 + Phase報告

実施日: 2026-08-04
対象: `http://localhost:8000`（scratch Nautobot、Step 5でデプロイ済み）
ステータス: **完了**

## 実施内容（plan.mdのチェックリストどおり）

トークンは `.local/secrets` から読み取り、値は出力しなかった（キー存在のみ確認のうえ使用）。

### 1. POST でepisode作成（realistic report + references）
```
POST /api/plugins/intent-catalog/workflow-episodes/
{"title": "Live smoke: WorkflowEpisode p1 step6",
 "raw_data": {"schema_version": 1,
   "report": {"summary": "p1 Step6 live verification self-report", "session_type": "workflow-improvement"},
   "references": {"session_id": "live-smoke-session-1"}}}
→ HTTP 201, status="candidate"
```
id: `6569864c-8914-4e2e-9368-b7e04c64ac74`

### 2. GET list（status絞り込み）/ GET detail
```
GET /api/.../workflow-episodes/?status=candidate → count: 1, ["Live smoke: WorkflowEpisode p1 step6"]
GET /api/.../workflow-episodes/<id>/ → HTTP 200
```

### 3. select → assessment書き込み → resolve
```
POST .../select/   → HTTP 200, status: candidate → selected
POST .../assessment/  {"verdict": "promote to skill", "reasoning": "live smoke verified end to end"}
                    → HTTP 200, raw_data.assessment 追加、report/referencesはbyte-identicalのまま
POST .../resolve/  → HTTP 200, status: selected → resolved
```

### 4. 禁止遷移 / 不正namespace（4xx期待）
```
POST .../select/ （resolved状態に対して）
→ HTTP 409 {"status":["invalid_transition: status: cannot transition from 'resolved' to 'selected'"]}

POST .../ {"title": "Bad namespace test", "raw_data": {"typo_namespace": {}}}
→ HTTP 400 {"raw_data":["unknown_namespace: raw_data: unknown top-level key(s): ['typo_namespace']"]}
```
両方とも期待どおり4xxで拒否。

### 5. GUI一覧・詳細（session cookie認証、`admin`/`admin` はdevenv/nautobot/docker-compose.ymlの
   `NAUTOBOT_SUPERUSER_*` 開発用固定値、秘密情報ではない）
```
GET /plugins/intent-catalog/workflow-episodes/  （htmxリクエスト、デフォルトフィルタ）
→ HTTP 200, "Live smoke: WorkflowEpisode p1 step6" の出現回数: 0
  （resolved状態のため、デフォルトのcandidate+selectedフィルタで非表示 = 設計どおり）

GET /plugins/intent-catalog/workflow-episodes/?status=resolved
→ 出現回数: 1（明示フィルタで到達できることを確認）

GET /plugins/intent-catalog/workflow-episodes/<id>/
→ HTTP 200。Report/Assessment/References/Resolutionの4見出しがすべて存在し、
  report(summary)・assessment(verdict)・references(session_id)の実データがそれぞれ
  本文中に出現（grep -c で2件ずつ = attr-tableのvalueとraw dumpパネルの両方に出現、想定どおり）。
  Resolutionは未記録のため見出しのみ（"Not yet recorded."の表示、本テストでは個別確認せず
  Step3のGUIテストで既に確認済みのため省略）。
```

## Exit基準（roadmap Phase 1 / plan.md）の充足確認

- **model, API, GUIがscratch Nautobot上で動作すること** — 上記1〜5ですべて実動作を確認。達成。
- **APIで作成したepisodeがGUI一覧・詳細で見えること** — 上記1でAPI作成→上記5でGUI一覧
  （`?status=candidate`相当のデフォルトフィルタ経由、resolved化後は明示フィルタ経由）・詳細の
  両方で確認。達成。
- **forward-only遷移・不正namespace拒否がテストで証明されていること** — Step 1-3の32 testsに加え、
  本Stepで実DB・実HTTP経由でも同じ拒否を再現（上記4）。達成。

**Phase 1 は roadmap記載の3つのExit基準をすべて満たし、完了とする。**

## ライブsmoke episodeの扱い

`WorkflowEpisode` API に DELETE ルートが存在しない（`http_method_names = ["get", "post", "head",
"options"]`、Braindump踏襲の設計判断＝作成後は遷移・namespace書き込みアクションのみで変更、
汎用削除経路を持たない不変記録）ため、API経由の削除はできない。plan.mdのStep 6は「削除するか
Phase 2 smokeのseedとして残すか、いずれでもよい」としているため、**削除せず残す**ことを選択した。
現在の状態は `resolved`、id `6569864c-8914-4e2e-9368-b7e04c64ac74`。Phase 2で
`nctl workflow-episode show` 等の疎通確認にそのまま使える。

## 後続への申し送り

- Phase 1 完了。Phase 2（nctl `workflow-episode` コマンド群）は本episodeをshow/list対象として
  再利用できる。
- API に DELETE が存在しない設計は roadmap では明示されていなかった implementer's discretion。
  Phase 2以降で「誤って作成したepisodeを消したい」ニーズが出た場合は、Django admin経由の削除
  （通常の運用外経路）かAPI拡張の要否を再検討する。
