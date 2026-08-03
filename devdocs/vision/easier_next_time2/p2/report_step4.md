# Report — Step 4: ライブ検証 + Phase報告

実施日: 2026-08-04
対象: `http://localhost:8000`（scratch Nautobot）、`uv run --project nctl nctl workflow-episode ...`
ステータス: **完了**

トークンは `nctl.toml` → `.local/secrets` 解決を使用し、値は出力しなかった（`nctl status` の
`authenticated: True` で疎通のみ確認）。

## 実施内容（plan.mdのチェックリストどおり）

### 1. Phase 1シード episode（`6569864c-8914-4e2e-9368-b7e04c64ac74`、resolved）
```
nctl workflow-episode show 6569864c-...
→ status: resolved、report/assessment/referencesの3セクションに実データ、resolutionは
  "(not yet recorded)"

nctl workflow-episode list
→ workflow episodes: 0   （デフォルトフィルタ candidate+selected では非表示 = 設計どおり）

nctl workflow-episode list --status resolved
→ workflow episodes: 1（seedが出現）
```

### 2. 新規episodeでの完全round trip
```
nctl workflow-episode create --title "Live smoke: WorkflowEpisode p2 step4" \
  --raw-data '{"schema_version":1,"report":{"summary":"..."},"references":{"session_id":"p2-step4-smoke"}}'
→ created ... status=candidate
id: 3915b1e4-8285-431b-bd7a-23203900c08d

nctl workflow-episode list
→ workflow episodes: 1（デフォルトフィルタでcandidateが出現）

nctl workflow-episode show <id> --json
→ raw_data.report / raw_data.references が投入どおりに出現

nctl workflow-episode select <id>      → "is now selected"
nctl workflow-episode write <id> assessment --data '{"verdict":"promote to skill","reasoning":"..."}'
                                        → "wrote assessment ...; status=selected"
nctl workflow-episode resolve <id>     → "is now resolved"

nctl workflow-episode show <id> --json
→ status: resolved、report/references は投入時とbyte-identical、assessment が新規追加。
  4状態遷移（create→candidate, select→selected, write→(値は増えるが状態はselected維持),
  resolve→resolved）すべて確認。
```

### 3. 禁止遷移 / 不正namespace payload（4xx相当・非ゼロexit期待）
```
nctl workflow-episode select <resolved化した同episode>
→ error[workflow_episode_transition_ineligible]: ... cannot transition to 'selected' from its
  current status
  exit code: 2

nctl workflow-episode write <id> report --data '[1,2,3]'
→ error[invalid_namespace_payload]: data must be a JSON object
  exit code: 2
```
両方とも期待どおりusage exit code（2）で拒否。後者はclient側バリデーション（配列はJSON
objectでないため即座に拒否）で、p1のサーバ側`unknown_namespace`検証（未知キー）とは別の防御層
だが、mapped error code・非ゼロexitという確認観点は満たしている。

## smoke episodeの扱い

WorkflowEpisode APIにDELETEルートが存在しない（p1報告と同じ設計）ため削除不可。
plan.md Step 4の指示どおり削除せず残す。id `3915b1e4-8285-431b-bd7a-23203900c08d`、
タイトルで smoke であることが明示済み、状態は `resolved`。

## roadmap Phase 2 Exit基準の充足確認

- **nctl ordinary suiteがpass** — Step 3報告のとおり `uv run pytest -q --durations=20` で
  1196 passed。本Stepでの変更はなし（live実行のみ、コード変更なし）。
- **create → list → show → select → resolve のround tripがscratch Nautobot上でsmoke検証済み**
  — 上記2で実データにて確認。達成。

**Phase 2 は roadmapの2つのExit基準をすべて満たし、完了とする。**

## Phase 2 まとめ

`nctl workflow-episode` コマンド群（`list` / `show` / `create` / `write` / `select` / `resolve` /
`dismiss`、計7コマンド）を4ステップ・4コミット（nctl側）+4コミット（root pointer bump）で実装。
GraphQLを使わずREST一本（読み書き）、raw_data全体を1つのJSONオブジェクトとして扱う入力様式に
統一、confirmation refetchなし（POSTレスポンスをそのまま信頼）、`--yes`確認プロンプトなし
（非破壊的CRUDのため）。roadmapの核心要件「an agent can fetch report / assessment / references
from nothing but an episode ID」は`nctl workflow-episode show <id> --json`で満たしている。

## 後続への申し送り

- Phase 2完了。Phase 3（agentdocs `workflow-improvement` セッションタイプ + policy.md/README_DEV.md
  自己報告先の書き換え）が次。
- nctlのpushはユーザーに依頼する必要がある（`.local/localenv_memo.md`のpush方針どおり、
  本Phase中は未push）。
