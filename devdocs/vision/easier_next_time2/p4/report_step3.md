# Report — Step 3: workflow-improvement session end to end

実施日: 2026-08-04
ステータス: **完了**

## 実施内容

`agentdocs/workflow-improvement/README.md`の"Standard loop for one turn"を
そのまま実行した。

1. `nctl session new workflow-improvement --topic p4-real-cycle` — scratch
   space `.local/workspace/workflow-improvement/2026-08-03_p4-real-cycle_cc96/`
   を作成。
2. `nctl workflow-episode show 2249af5f-4ff5-41aa-8e83-55b1c57dd656 --json` で
   `report`/`references`を取得（Step 1で書いた内容をそのまま確認）。
3. 判断: **改善あり**。Step 2で実際に踏んだ「GUIはブラウザセッション認証を
   要求し、tokenヘッダでは302になる」という制約は、エージェントが
   `workflow-improvement`を将来実行する際に同じ空振りをしないよう記録する
   価値がある、と判断した。
4. 改善実施: `agentdocs/workflow-improvement/README.md`の"Known gotchas"に
   1項目追記（コミット `6364dff`）。policy.md/nctl/GUI本体には変更なし
   （見つかった問題はドキュメントの不足であり、コード側の欠陥ではなかった
   ため）。
5. `resolution`書き込み:
   ```
   nctl workflow-episode write 2249af5f-4ff5-41aa-8e83-55b1c57dd656 resolution --data '{...}'
   ```
   summary、commits（`6364dff`）、column_promotion_candidate（「なし」）を記録。
6. `assessment`書き込み（policy §2属性）:
   `level=2`（agent-led orchestration、runbook未選択）、
   `human_guidance=judgment_required`（GUI selectの委任先などユーザー判断を
   要した）、`execution_mode=nctl`、`outcome=completed`、
   `target_level="2 - 一回性のphase完了評価であり自動化不要"`。
7. `nctl workflow-episode resolve 2249af5f-4ff5-41aa-8e83-55b1c57dd656` —
   `selected` → `resolved`に遷移。

## 確認した禁止事項の遵守

- `report`namespaceは書き換えていない（読み取りのみ）。
- 改善はdesired/actual stateへの直接書き込みではなく、agentdocsの記述変更に
  留めた。
- 本タスク自身のrunbookをそのタスク実行中に改善する行為ではない（対象は
  workflow-improvement自身の手順文書であり、time-separationの規則に反しない
  ―― self-reportと改善は別のnctl session（`workflow-improvement`セッション）
  として明示的に分離した）。

## コミット

- `6364dff` — agentdocs修正（前ステップで既にコミット済み）。
- 本report_step3.mdの追加コミットのみ、このステップで新たに作成する。
