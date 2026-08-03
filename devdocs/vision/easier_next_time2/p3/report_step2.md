# Report — Step 2: policy.md §4 + README_DEV.md + skill citation reword

実施日: 2026-08-04
ステータス: **完了**

## 実施内容

### `devdocs/vision/easier_next_time/policy.md` §4
- トリガー条件の一文（"non-trivial cluster workを行ったsession終了時、painful
  またはsecond-occurrenceのときは常に"）は verbatim で維持。
- markdown template（selfreport.md）を `nctl workflow-episode create --title ...
  --raw-data '{...}'` の例に置換。`report` namespaceは旧templateの各フィールド
  （occurred_at, tags, outcome（§2語彙）, summary, improvised_parts, skills_used,
  second_occurrence_feeling）を保持し、`references` namespaceは旧「References」
  箇条書き（nctl operation IDs, Braindump/desired-state IDs, session）を保持。
  サブ構造はfree-form（decision 4）である旨を明記。
- 「episode directoryが監査単位」→「WorkflowEpisode IDが監査単位」に変更。
  multi-task-per-session / multi-session-per-taskの原則はそのまま維持。
- 後日のreview → `nctl workflow-episode write <id> assessment --data '{...}'`
  （§2属性 + promotion verdict）に変更。`workflow-improvement` agentdocs
  manualへのリンクを追加。
- `create`失敗時の扱いを1文で追加（decision 6どおり: セッション内で報告して
  進む、オフラインdraft機構なし）。
- §5/§6/§8を確認したが、旧local directoryへの言及はなし（§8の「Retrospective
  artifacts reference operation IDs; they do not copy evidence」は既に新schemeと
  整合、変更不要）。§2/§3も変更なし。

### `README_DEV.md` §"Easier Next Time: end sessions with a self-report"
- 送信先の一文を「create a WorkflowEpisode via `nctl workflow-episode create`」
  に変更、`agentdocs/workflow-improvement/README.md`へのリンクを追加する一文を
  挿入。「don't build runbooks mid-task」の一文はそのまま維持。

### `.claude/skills/retire-proxmox-lxc/SKILL.md`
- 2箇所の`.local/evidence/workflow-episodes/...`パス参照を、パスに依存しない
  historical citationへ書き換え:
  - フロントマター直後の検証済み文: "2026-08-03 `agscratch1` retirement
    self-report (WorkflowEpisode)" — 具体的なファイルパスを削除。
  - manual_review branch tableの監査episode参照: "2026-08-03 `aghaos`
    retirement audit (WorkflowEpisode)" — 同様にパス依存を削除。
  いずれも「いつ検証されたか」の記述性は維持しつつ、対象ディレクトリが
  いつ削除されてもドキュメントが壊れないようにした（decision 8）。

## テスト

純粋なdocumentation変更のため、テスト実行不要（plan.mdの前提どおり、コード
変更なし）。

## この時点でのExit基準の充足

plan.mdが列挙した「新sessionが参照する、旧schemeへの言及が残っているドキュメント」
3件（policy.md §4、README_DEV.md、SKILL.md 2箇所）をすべて本stepで書き換えた。
Step 3でrepo全体のgrepにより確認する。

## 後続への申し送り

Step 3で `grep -rn "evidence/workflow-episodes\|selfreport\.md"` を実行し、
残る参照がすべてhistorical recordであることを示す。nctlのPhase 2コミットは
まだunpushedのまま（本phaseでの新規push発生なし、p2から持ち越しのリマインド）。
