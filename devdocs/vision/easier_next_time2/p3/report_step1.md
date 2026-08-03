# Report — Step 1: `agentdocs/workflow-improvement/README.md`

実施日: 2026-08-04
ステータス: **完了**

## 実施内容

### 新規ファイル
- `agentdocs/workflow-improvement/README.md` — 第2のsession type manual。
  `agentdocs/brainforge/README.md` を構造テンプレートとして踏襲: rule → time
  separation（policy §7の具体化） → 「触ってよい3つのもの」テーブル →
  prohibitions（policy由来のみ、新規なし） → scratch area → 標準ループ（1turn）
  → key commands（plan.mdが確定したPhase 2最終コマンド面を正確に引用） →
  stop conditions → known gotchas（no DELETE、forward-only transition、
  デフォルトlist filter、`write`のwholesale置換）。
  discuss_idea1.md §6のライフサイクル（人間がGUIでcandidateを俯瞰 → select →
  `nctl session new workflow-improvement` → `show --json`で読む → 必要な場合
  だけtranscript/opsを読む → policy/agentdocs/skill/nctl/submoduleを改善 →
  `resolution`更新 → `resolve`）をそのまま反映。dismiss経路（reasoning未記録の
  dismissを許さない）も明示。

### 修正ファイル
- `agentdocs/README.md` — dispatcherの1行を `README.txt` → `README.md` に修正
  （plan.mdが指摘した既存の不整合。brainforgeは実際には`README.md`を使っている）。

## Live dry-check

plan.mdの助言どおり、マニュアルに引用した2つのseed episode IDを実際の
scratch Nautobotに対して確認した:

```
$ uv run --project nctl nctl workflow-episode list --status resolved --json
→ 2 items: 3915b1e4-8285-431b-bd7a-23203900c08d ("Live smoke: WorkflowEpisode p2 step4"),
           6569864c-8914-4e2e-9368-b7e04c64ac74 ("Live smoke: WorkflowEpisode p1 step6")
  両方 status: resolved

$ uv run --project nctl nctl workflow-episode show 3915b1e4-8285-431b-bd7a-23203900c08d --json
→ ok: true, raw_data に report/assessment/references/schema_version を確認

$ uv run --project nctl nctl workflow-episode --help
→ list / show / create / write / select / resolve / dismiss の7サブコマンドを確認。
  plan.mdが引用したコマンド面と完全一致。
```

マニュアルに引用したコマンド・IDはすべて実行確認済み（known-good）。

## この時点でのExit基準の充足

新session typeマニュアルは追加済み。plan.mdの禁止事項（旧local-fileワークフローへの
依存、`.local/evidence/workflow-episodes/`への依存）はいずれも本マニュアルに現れない
ことを確認した。

## 後続への申し送り

Step 2でpolicy.md §4 / README_DEV.md / retire-proxmox-lxc SKILL.mdの旧scheme参照を
書き換える。今回追加したマニュアルはpolicy.mdの§1–§3・§5–§6にリンクするのみで、
§4のself-report記述には触れていない（Step 2の対象）。
