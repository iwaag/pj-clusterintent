# Easier Next Time 2 — Phase 4 Report: One Real Cycle and Evaluation

実施日: 2026-08-04
ステータス: **完了** — Phase 4 完了。easier_next_time2 roadmap 全体が完了。

## 実施したサイクル

roadmap.md Phase 4 の exit 基準どおり、実データでの一回のサイクルを最初から
最後まで実行した:

1. **self-report** (`p4/report_step1.md`) — 本Phase 4セッション自身の作業を
   対象に `nctl workflow-episode create` でepisode
   `2249af5f-4ff5-41aa-8e83-55b1c57dd656`
   （"easier_next_time2 roadmap: Phase 4 real cycle"）を作成。既存の2件の
   episode（`6569864c...`, `3915b1e4...`）はPhase 1/2のlive smoke検証で
   作られた例示データであり、実際のself-reportではなかったため、これが
   本パイプライン最初の本物のself-reportとなった。
2. **GUI survey + select** (`p4/report_step2.md`) — episodeのGUI URLを
   ユーザーに提示して確認を依頼し、`select`操作の実行主体を確認した。
   ユーザーはエージェントへの委任を選択し、エージェントが
   `nctl workflow-episode select`を実行した（`candidate` → `selected`）。
3. **workflow-improvement session** (`p4/report_step3.md`) —
   `agentdocs/workflow-improvement/README.md`の標準ループに従い、
   `nctl session new workflow-improvement --topic p4-real-cycle`で開始、
   `show --json`でreport/referencesを取得、改善を実施
   （`agentdocs/workflow-improvement/README.md`のKnown gotchasに1項目追記、
   コミット `6364dff`）、`resolution`/`assessment`を書き込み、
   `resolve`で`selected` → `resolved`に遷移させた。

## サイクルから見つかったもの

**実際に見つかった問題（1件）**: NautobotのGUI list/detail view
（`/plugins/intent-catalog/workflow-episodes/...`）はブラウザセッション認証を
要求し、`Authorization: Token`ヘッダを付けたcurlでは302（ログイン画面への
redirect）が返るのみで、エージェントは非対話的にGUIの見た目を検証できない。
これはPhase 1-3では気づかれていなかった――例示コマンドはすべて
`show --json`のようなAPI経由の確認で済んでいたため。今回初めて実際に
「人間がGUIを見て選ぶ」ステップを踏もうとして発覚した。

**適用した修正（最小限、1件）**: `agentdocs/workflow-improvement/README.md`
のKnown gotchasに、上記の制約と「GUI surveyは本質的にhuman-in-the-loopの
ステップとして扱い、エージェントの代役は`list/show --json`での代替確認に
留まる（GUI presentation自体の検証にはならない）」という指針を追記した
（コミット `6364dff`）。GUI本体・nctlコマンド・DBスキーマには変更を加えて
いない――見つかった問題はドキュメントの不足であり、コードの欠陥ではなかった
ため。

**見つからなかったもの**: `nctl workflow-episode`のCRUD/遷移コマンド自体、
raw_dataのnamespace構造、forward-only transitionの制約は、実データで一度
通しても問題なく機能した。修正は不要だった。

## column-promotion candidate の有無

**なし。** raw_data中のどのフィールドについても、頻繁なfilter/aggregation/
決定的処理の必要が生じておらず、column昇格の候補は現れなかった。これは
governing decision 1（最小モデル、実際に使われてから昇格）の想定どおりの
結果である。現時点でepisodeは実質1件（他の2件はexample/smoke由来）しか
存在しないため、判断material自体が乏しいことも影響している――次に本物の
self-reportが複数件たまった時点で再評価する価値がある。

## 未検証のまま残った点

- GUIのブラウザレンダリング自体（一覧のフィルタUI、詳細のreport/assessment/
  references/resolutionセクション表示）は、Nautobotのセッション認証を
  非対話的に突破する手段がなく、今回も未検証のまま。これはPhase 1/2で
  デプロイ時に一度確認済みとされているが、本Phase 4では再確認していない。
  今後、人間が実際にブラウザで開いて確認するのが唯一の検証手段であり続ける。

## nctl push状況

本Phase 4ではnctl/nintentサブモジュールへの変更はなく（agentdocsの変更は
rootスーパープロジェクト側のファイル）、両サブモジュールとも
`origin/main`と一致したまま。一方でrootスーパープロジェクトは本Phase 4の
5コミット分、`origin/main`より進んでいる（push未実施）。pushはユーザーに
依頼する運用のため、本報告と併せて確認をお願いしたい。

## roadmap全体の完了

Phase 4の実施をもって、easier_next_time2 roadmap（Phase 1〜4）はすべて
完了した。roadmap.mdの最終行が述べるとおり、以後はこのWorkflowEpisode
パイプラインが標準的な実務（"standing practice"）として運用され、本roadmap
自体はここで終了する。今後も本Phase 4で見つかったGUI認証の制約のように、
実際に使ってみて初めて分かる小さな摩擦が出てくることが想定されるが、
それらは個別の`workflow-improvement`サイクルで拾えばよく、新たなroadmap
phaseを必要としない。
