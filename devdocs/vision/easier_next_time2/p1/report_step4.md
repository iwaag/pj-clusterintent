# Report — Step 4: 最終ゲート

実施日: 2026-08-04
対象: `nintent` (submodule)
ステータス: **完了**（fast suite: 142 pass, skipped=10 / runtime gate `--clean`: 253 pass）

## 目的（p1/plan.md Step 4）

nintent fast suite + runtime gate `--clean`（fresh `test_nautobot`でのmigration検証込み）を実行し、
`cases=` 件数を記録する。

## 検証

### fast suite（Django-free）
```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 142 tests in 0.004s
OK (skipped=10)
```
Step 1開始前のベースライン（130 pass, skipped=10）から、`test_workflow_episode_contract.py`
の12 testsのみが純増。skip数は不変（既存の`test_api_contract.py`/`test_ui_contract.py`由来で
WorkflowEpisode追加とは無関係）。

### runtime gate `--clean`
```
$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean nautobot_intent_catalog
（test_nautobotを一旦DROPし、0001から0029_workflowepisodeまで全マイグレーションをfreshに適用）
Migration passed: No approval_required jobs or scheduled jobs found.
Found 253 test(s).
Ran 253 tests in 6.986s
OK
runtime gate result mode=clean label=nautobot_intent_catalog cases=253
```
`cases=253`（Step 3終了時点の`--keepdb`実行と同数）で、fresh DBでもゼロ収集でなく実際に
253件が走ったことを確認。`nautobot-server makemigrations --check --dry-run` も
`No changes detected`（このスクリプト実行中に毎回自動チェックされている）。

## Phase 1 Exit基準（roadmap/plan.md記載分）の充足状況

1. **model, API, GUIがscratch Nautobot上で動作すること** — 本Stepまでのruntime gateで
   model/API/GUIすべてが実DBスキーマ上でグリーン。ただしこれは runtime gate（一時ステージ）
   上の検証であり、実際のscratch Nautobotコンテナへのデプロイと最終疎通確認はStep 5/6で行う。
2. **APIで作成したepisodeがGUI一覧・詳細で見えること** — `WorkflowEpisodeViewTests`で
   モデル経由作成→detail描画のテストは通過済み。API POST→GUI表示の疎通そのものは
   Step 6のライブ検証で確認する。
3. **forward-only遷移・不正namespace拒否がテストで証明されていること** — 達成済み
   （Step 1: 純粋関数12 tests、Step 2: API層12 tests、Step 3: GUI 8 tests、計32 testsが
   `test_workflow_episode_contract.py`+`test_workflow_episode.py`に集約）。

## 後続への申し送り

- Step 5はデプロイ（`git push`はユーザー依頼、`docker compose build --no-cache`、コンテナ再起動、
  `nautobot-server migrate`）。ここからは実行前に一時停止しユーザーに確認する。
- Step 6のライブ検証で、上記exit基準2の「APIで作成→GUI表示」を実際のscratch Nautobot
  (`http://localhost:8000`) 上で確認する。
