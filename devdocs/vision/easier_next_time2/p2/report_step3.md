# Report — Step 3: Transitions (`select` / `resolve` / `dismiss`) + full suite

実施日: 2026-08-04
対象: `nctl`（ローカル source）
ステータス: **完了**

## 実施内容

### client / errors
- `workflow_episode_client.py` に `transition_workflow_episode(client, episode_id, action, *,
  new_status)` を追加。404を`workflow_episode_not_found_error`、**409を
  `workflow_episode_transition_ineligible_error`**（Braindumpの`complete_ineligible_error`と同型）、
  その他非2xxを`workflow_episode_transition_rejected_error`にマップ。`new_status`はメッセージ用
  （"selected"/"resolved"/"dismissed"）で`action`（URL上のパスセグメント、"select"/"resolve"/"dismiss"）
  とは独立させた。

### core（`workflow_episode.py`）
- `_transition()`共通ヘルパー＋`select_episode`/`resolve_episode`/`dismiss_episode`の3薄いラッパー。
  Step 2の`create`/`write_namespace`同様、confirmation refetchなしでPOSTレスポンスをそのまま
  record化（403書き込みも同じ設計方針で統一）。

### render / CLI
- `WorkflowEpisodeTransitionData`（episode, changed）を3遷移で共有、schemaのみ
  `nctl.workflow_episode.{select,resolve,dismiss}.v1`で分離。
- `nctl workflow-episode select|resolve|dismiss <id> [--json]`。braindumpの`complete`と異なり
  `--yes`確認は付けていない（plan.mdの「Confirmation prompts are unnecessary...only review-delete
  gates」に従う。破壊的でも外部到達的でもない前進のみの状態遷移）。
- `WORKFLOW_EPISODE_USAGE_CODES`に`workflow_episode_transition_ineligible`はStep 1時点で
  先取り登録済みだったので変更不要（exit code 2 = usage、409を正しくスクリプトから判別可能）。

### テスト
- `tests/test_workflow_episode.py`: 遷移3コマンドの正常系、409→ineligible、404→not_found、
  不正id、で7 test追加。
- `tests/test_cli_workflow_episode.py`: 3コマンドのtext出力＋ineligibleのexit code、で4 test追加。

## テスト結果

```
uv run pytest -q tests/test_workflow_episode.py tests/test_cli_workflow_episode.py tests/test_cli_surface.py
→ 49 passed  (Step 2時点39 → +10)

uv run pytest -q --durations=10
→ 1196 passed  (Step 2時点1186 → +10、回帰なし)
```

## roadmap Phase 2 / plan.mdのExit基準

- **nctl ordinary suiteがpass** — 上記1196 passed で達成（`--durations=20`は実行時間が短く
  上位10件のみ表示、20件指定でも実質同じ結果）。
- **create → list → show → select → resolve のround tripがscratch Nautobot上でsmoke検証済み**
  — 未実施。Step 4（live smoke）で実施する。

## 後続への申し送り

- Step 4でシード episode（`6569864c-8914-4e2e-9368-b7e04c64ac74`、Phase 1で作成、resolved）の
  show/listと、新規episodeでのcreate→list→show--json→select→write(assessment)→resolve→
  show--jsonのround tripをライブ実行する。禁止遷移（resolvedへのselect）と不正namespace payload
  も1件ずつ確認する。
- 全コマンド実装済み: `list`/`show`/`create`/`write`/`select`/`resolve`/`dismiss`（7コマンド）。
