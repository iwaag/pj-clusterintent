# Workflow Agent idea — Discussion 1

Date: 2026-08-04

## 1. 問題意識

Easier Next Time により、過去に難しかった処理を後から runbook や bounded command
へ昇格させる継続改善の仕組みはできた。一方、現在の安価なローカル LLM
エージェントは、読むコンテキスト、ルール、禁止事項が少し増えるだけでも実行の
確実性が下がりやすい。エージェント自身に必要なコンテキストを選ばせる方法も、
選択そのものに推論を使うため、必ずしも負荷削減になっていない可能性がある。

この問題に対し、元の `idea.txt` は次の分離を提案した。

1. ユーザーの依頼が確定したら、その要約を workflow agent に渡す。
2. workflow agent が関連する手順書や設定を選び、短く具体的な計画を返す。
3. main agent はその計画を実行し、実行中には原則として再計画しない。
4. 計画外の状態に遭遇したら、即興で復旧せず、失敗箇所と実行時証拠を報告する。

狙いは、実行エージェントの推論負荷を下げることと、失敗が計画側にあったのか、
計画に従った実行側にあったのかを後から評価しやすくすることである。

## 2. 最初のレビューで賛成した点

計画と実行の分離という中心案には賛成である。特に以下は、既存の Easier Next
Time 方針および Level 3 の考え方と整合する。

- 実行前に、その回で必要なコンテキストと手順を小さく確定する。
- executor に全資料の探索と手順構成を同時に行わせない。
- 実行中の自由な再計画を避け、列挙済みの分岐や retry だけを許す。
- 想定外の状態では safe stop し、次の計画サイクルに証拠を渡す。
- 計画と実行を別々に評価できる記録を残す。

これは、以前の Easier Next Time 設計で延期された task card、workflow selection、
small-model execution package を、実在するローカル executor の問題に基づいて再検討
する提案と位置付けられる。

## 3. 最初のレビューで示した懸念

最初のレビューでは、自由文で生成されたコマンドを小型 executor がそのまま実行
するだけでは、誤った計画を忠実に実行する危険があると指摘した。そのため、既知の
workflow については、workflow ID、typed parameters、固定された手順、成功条件を
含む task card を使い、可能な部分を検証可能にする案を示した。

また、次を提案した。

- 「明らかな危険操作か」を executor に毎回推論させず、risk、approval、
  allowed/forbidden commands、stop conditions などを card に明記する。
- 失敗後の復帰を全面禁止するのではなく、明記された retry と分岐だけを許す。
- 評価時に planning defect、workflow contract defect、execution/environment defect
  を分ける。
- LLM planner 自体は決定論的 control backend である `nctl` から分離する。

## 4. ユーザーからの要望と修正

上記レビューに対し、次の要望が示された。

### 4.1 非決定論的な処理を排除しない

既知の workflow について既存手順を選択し、パラメータを埋めるという考え方には
同意する。ただし、それを「前例のない処理は許容しない」という仕組みにしては
ならない。

エージェントが柔軟な非決定論的処理によって新しい問題を解決することは、システム
に必要な能力である。その成功や苦労を後から評価し、再発する価値のある処理だけを
runbook や bounded command に変えることが Easier Next Time の本来の方針である。
決定論化は未知の処理を実行するための前提条件ではなく、実行後に検討する改善候補
である。

### 4.2 初版の task card を小さくする

risk、approval、allowed commands、forbidden commands、hash、retry 上限などを最初
からすべて schema に入れる案は、扱うパラメータが多すぎる可能性がある。
初版は、この分離が実際に小型 executor の確実性を上げるかを検証できる最小限の
情報に絞るべきである。不足は実際の失敗から追加する。

### 4.3 再計画と復帰の境界

executor が実行中に独自の再計画をしないことには同意する。ただし、計画に最初
から書かれた分岐や bounded retry は実行してよい。想定外の失敗後に必要なら、
executor の内部判断ではなく、新しい明示的な planning cycle を開始する。

### 4.4 障害分類も最初は単純にする

planning / contract / execution の三分類は分析上は有用だが、初版から必須の分類体系
にすると仕組みが重くなる懸念がある。まずは「計画の問題だったか」「計画には従った
が実行時に止まったか」を判別できればよい。runbook の陳腐化など第三の原因が実際に
繰り返し現れた場合に分類を増やす。

## 5. 修正後の基本原則

この議論を踏まえ、workflow agent は決定論化装置ではなく、**計画時の広い推論と
実行時の狭い推論を分離する装置**と考える。

### 5.1 既知の処理

該当する skill、runbook、`nctl` の bounded command がある場合、workflow agent は
それを優先して選び、今回の対象とパラメータを具体化する。既知の禁止事項、承認境界、
成功条件も必要な範囲で計画へ含める。

### 5.2 未知または一度限りの処理

既存 workflow に当てはまらない依頼も拒否しない。workflow agent は必要な資料を
調べ、非決定論的に新しい手順を組み立ててよい。この場合、その計画は Level 1–2
相当の探索を含み、既存 workflow と同じ確実性があるとは表示しない。

executor は、その新しい計画を実行する際にも計画外の再構成は行わない。計画が不足
していれば止まり、結果を workflow agent または人間へ返す。そこで新しい計画を作る
ことは許される。つまり、柔軟性は planning cycle 間に残し、個々の execution cycle
は小さく境界づける。

### 5.3 Easier Next Time との接続

非決定論的な計画で解決したこと自体は問題ではない。完了後の WorkflowEpisode で、
どこに推論、試行錯誤、追加コンテキストが必要だったかを記録する。二度目と感じた
処理や、頻度・失敗影響・推論負荷の積が大きい処理だけを、後日の別セッションで
runbook または bounded command に昇格させる。初回の未知処理を禁止したり、その場
で runbook 化したりしない。

## 6. 最終提案：最小の planning/execution protocol

初版では汎用 workflow engine や厳密な command sandbox を作らず、次の一往復を
成立させる。

```text
confirmed user request
  -> workflow agent plans
  -> concise plan artifact
  -> executor follows the plan
  -> completed | stopped
  -> execution report
```

想定外の停止後に続行する場合は、暗黙に同じ execution を延長せず、報告を入力として
次の planning cycle を明示的に開始する。

### 6.1 入力

入力はユーザー依頼の短い要約を基本とする。少なくとも、目的、対象、ユーザーが明示
した制約を失わないことが必要である。workflow agent はリポジトリ資料や現在状態を
必要に応じて調べてよい。要約だけでは重要な曖昧さを解消できない場合は、計画を推測
で確定せず、確認が必要であると返す。

### 6.2 出力

初版の plan artifact は、人間と executor の両方が読める短い Markdown または
単純な構造化テキストとし、必須項目を次の四つに限定する。

1. `goal` — 今回どの状態を目指すか。
2. `steps` — 実行順の短い具体的手順。既存 workflow を使う場合はその名前を含める。
3. `stop conditions` — 続行せず報告する条件。既知の分岐と bounded retry は steps
   側に書く。
4. `success evidence` — 何を確認すれば完了と言えるか。

外部・破壊的操作で既存ポリシー上の承認が必要な場合だけ、該当 step に
`approval required` を付ける。初版では汎用 risk enum、全 command の allowlist、
workflow hash、細かな障害分類を必須にしない。必要性が実際の失敗で示されたものから
追加する。

### 6.3 executor の規則

- plan artifact と、各 step の実行に直接必要な最小コンテキストだけを読む。
- steps の順序、記載された分岐、bounded retry に従う。
- 計画外の調査、別コマンドへの置換、復旧、適用範囲の拡大を独自に行わない。
- 既存の安全規則やユーザー承認を plan が省略していても無効化しない。
- 完了または停止時に、実行した step、停止箇所、主要な構造化出力、関連する
  `nctl` operation ID を報告する。secret や private payload は複製しない。

この規則は未知の処理を禁止するものではない。未知の処理を考える責任を planning
phase に置き、execution phase がその場で別の計画を発明しないという境界である。

### 6.4 最初の評価

まず少数の依頼で、同じ依頼を現行方式と分離方式の双方で実行または replay し、次を
比較する。

- executor に渡したコンテキスト量。
- 計画した step の省略、順序違反、計画外操作の有無。
- success evidence を実際に確認したか。
- 想定外の状態で即興せず停止・報告できたか。
- 未知の依頼を不必要に拒否せず、planning phase で新しい計画を作れたか。

最初から大きな schema や router を完成させるのではなく、この比較で具体的に現れた
失敗を次の設計入力とする。

## 7. 実装境界についての保留事項

`nctl wfagent <request-file>` は利用イメージとして分かりやすいが、コマンド名と配置は
まだ固定しない。LLM planning は非決定論的であり、drift、actuation、evidence の
決定論的 backend である `nctl` と責任が異なるため、独立した `wfagent`、`cagent`
の機能、または `nctl` から呼ぶ薄い frontend のいずれが適切かを実装計画で決める。

同様に、task card schema、workflow catalog、厳密な allowlist、planner/executor 間の
API、small-model replay gate は、最小 protocol の効果が確認されてから追加を判断する。

## 8. 提案の要約

採用すべき中心案は、次の三点である。

1. 広いコンテキストを使う非決定論的 planning と、狭い計画に従う execution を分ける。
2. executor は列挙済みの分岐以外では再計画せず、停止結果を次の明示的 planning cycle
   へ返す。
3. 未知の処理は planning phase で許容し、成功後に Easier Next Time が必要性を評価
   して初めて決定論化する。

したがって、目標はすべての運用を事前に決定論化することではない。探索能力を残した
まま、各 execution cycle の推論負荷と責任範囲を小さくし、再発した処理だけを後から
より確実な workflow へ昇格させることである。
