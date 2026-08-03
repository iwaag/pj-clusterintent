# Easier Next Time 2 — 議論の経緯と提案

Status: `idea.txt` を起点とした第1回議論の記録。ここではユーザーが直接述べた
要望、その変遷、議論から導いた設計提案を区別して記録する。まだ実装計画では
なく、フィールド名、API名、状態語彙などはロードマップ作成時に確定する。

## 1. 背景

[`../easier_next_time/roadmap.md`](../easier_next_time/roadmap.md) では、痛みや
二度目の発生を感じた運用をworkflow episodeとして記録し、後日の別セッションで
監査して、必要ならskillまたはboundedなnctlコマンドへ昇格させる仕組みを作った。

しかし現在のself-report、audit、reviewは
`.local/evidence/workflow-episodes/` 以下の個別ファイルである。人間が改善対象を
選ぶにはファイルを一つずつ開いて内容を確認する必要があり、episodeが増えるほど
人間にもエージェントにも探索と管理の負担が増える。

今回の議論は、既存の改善方針を置き換えるものではない。その改善ループに、
人間が候補を俯瞰して選び、選ばれたepisodeを開発エージェントへ渡すための
永続的な受付・管理面を加える提案である。

## 2. ユーザーが直接述べた要望と、その変遷

以下は、議論中にユーザーが直接示した要望・判断である。提案者側の推測とは
区別する。

### 2.1 最初の要望 — 初期段階から俯瞰とフィルタリングが欲しい

ユーザーは最初に、次の問題と希望を示した。

- レポートがまだ少ない段階でも、個別ファイルを開いて改善対象を管理することを
  考えるだけで負担を感じる。
- episodeが増えれば、エージェントを使って調べる場合もさらに面倒になると予想
  している。
- 最小実装を志向していたが、レポートの俯瞰とフィルタリングは初期段階から
  必要だと考え直した。
- そのため、nintentに最低限のデータモデルを追加したい。
- 高機能なダッシュボードは求めず、nintentのread-only GUIで一覧と詳細を閲覧
  できれば十分である。
- 一覧の対象は全セッションではなく、問題または改善余地のあるworkflow episode
  だけでよい。
- 人間は一覧からepisode IDを選び、`pj-clusterintent`上で開発エージェントとの
  改善セッションを開始したい。
- `agentdocs`には、`brainforge`に続く二つ目のセッションタイプとして、この改善
  セッションの手順を追加したい。

この段階で求められていたのは、一般的なセッションログ基盤ではなく、改善候補を
扱う小さなキューと、その人間向けread-onlyビューであった。

### 2.2 最初の提案への修正 — カラムを増やしすぎずraw dataを使う

最初の提案では、`outcome`、`current_level`、`target_level`、
`execution_mode`、各種参照など、多数の属性を独立カラムとして持つ案を示した。

これに対してユーザーは、次のnintentの既存設計方針を明示した。

- まずraw dataへ情報を広く保持する。
- フィルタリングまたは決定論的処理で実際に消費される値だけを、後からカラムへ
  昇格させる。
- したがって、利用実績のない属性を初期モデルのカラムとして先回りして固定する
  のは望ましくない。

同時にユーザーは、この情報を単なる観測raw dataと同一視しているわけではない
ことも明確にした。workflow episodeはdesired stateではなく、直接の決定論的な
reconcile入力でもない。しかし、desired stateをactual stateへreconcileする経路を
継続的に改善するための重要な情報であり、Braindumpと同様、nintentの設計思想の
中で保持する価値があるという判断である。

この指摘を受け、初期モデルは少数の基本カラムと一つのJSON raw dataへ縮小する
方向に修正した。

### 2.3 保存方針の発展 — DBを索引ではなく正本にしたい

次の段階でユーザーは、データベースを導入する以上、本当にローカルでなければ
ならないものを除き、ローカルファイル管理をやめてDBへ一元化したいという希望を
示した。

これは当初の「DBは一覧用の索引、詳細レポートはローカルファイル」という案から
の重要な発展である。最終的な希望は次のように整理できる。

- DBはローカルファイルへの単なるポインター集ではなく、workflow episodeの意味
  ある報告、評価、改善判断、解決結果の正本になる。
- 人間はnintent GUIで候補を選び、エージェントはepisode IDからDB上の必要情報を
  取得できる。
- ローカルファイルは、環境上どうしてもローカルに生まれる証拠、一時作業、秘密
  情報に限定する。

## 3. 合意した設計方向

議論を通じて、次の方向が妥当だという結論になった。

### 3.1 `WorkflowEpisode`はnintent上の独立した重要情報である

`WorkflowEpisode`はdesired stateにもactual stateにも含めない。また、reviewの
内容が直接driftやreconcile actionを発生させることも認めない。

その役割は、運用中に発見された痛みや改善余地を、後日の改善作業へ接続する
ことである。

```text
cluster operation
  -> 問題または改善余地のあるworkflow episode
  -> nintent上のWorkflowEpisode
  -> 人間による候補選択
  -> workflow-improvementセッション
  -> policy / agentdocs / skill / nctl / 実装の改善
  -> 次回の、より決定論的なreconcile
```

この意味でBraindumpとの共通点がある。どちらも直接のactuation authorityではない
が、ユーザーの意図またはシステム改善を、決定論的なdesired/actual control loopへ
正しく接続するための重要な意味情報である。

### 3.2 最小モデル

初期モデルは、`PrimaryModel`が提供するID、`created`、`last_updated`に加えて、
原則として次の3フィールドだけを持つ案とする。

| field | 初期カラムにする理由 |
|---|---|
| `title` | 人間が一覧でepisodeを識別するための基本表示値 |
| `status` | 改善候補キューの絞り込みと状態遷移で直ちに使うため |
| `raw_data` | report、assessment、references、resolutionなど、まだ昇格根拠のない情報を保持するため |

`status`の候補は、現時点では次の程度を想定する。

- `candidate` — 問題または改善余地が報告され、まだ選ばれていない。
- `selected` — 人間が改善対象に選び、改善セッションの対象になっている。
- `completed` — 改善と必要な検証が完了した。
- `dismissed` — 調査の結果、改善不要または現状維持と判断した。

語彙はロードマップで既存のcompletion languageとの整合を再確認して確定する。

### 3.3 raw dataの初期構造

`raw_data`は自由な一枚のメモではなく、上位名前空間とschema versionだけを定める。
下位フィールドは実際の利用に合わせて拡張する。

```json
{
  "schema_version": 1,
  "report": {
    "occurred_at": "...",
    "tags": ["painful", "second-occurrence"],
    "outcome": "safe_stop",
    "summary": "...",
    "improvised_parts": "...",
    "skills_used": []
  },
  "assessment": {
    "current_level": 2,
    "target_level": 3,
    "reason": "..."
  },
  "references": {
    "session_ids": [],
    "operation_ids": [],
    "braindump_ids": [],
    "desired_objects": []
  },
  "resolution": {
    "summary": "...",
    "skill": null,
    "commits": []
  }
}
```

この例は初期入力の目安であり、各キーをDBカラムとして固定する提案ではない。
`outcome`や`target_level`などは、実際に頻繁なフィルター、集計、または決定論的処理
の入力になった時点でのみカラムへ昇格させる。

専用APIは呼び出し側に`raw_data`全体を毎回置換させず、`report`、`assessment`、
`resolution`など、担当する名前空間だけを更新する方がよい。後段の改善セッション
が元のself-reportを誤って消すことを避けられる。初期段階では履歴専用の関連モデル
までは追加せず、現在値とNautobotの変更履歴を利用する。

### 3.4 DBを正本にする

workflow episodeについては、nintent DBを次の情報の正本とする。

- 運用セッションからのself-report相当の内容
- 後日の監査とexecution level / target levelの評価
- 改善する、現状維持にする、却下するという判断と理由
- 改善作業の結果と検証結果
- 関係するsession、nctl operation、Braindump、desired object、skill、commitへの参照
- 改善候補としての現在の処理状態

これに伴い、新規episodeについて
`.local/evidence/workflow-episodes/<episode>/selfreport.md`、`audit.md`、`review.md`
を恒久的な正本として作る運用は廃止する。必要ならDB登録前の一時ドラフトとして
ローカルファイルを使えるが、登録成功後はDBだけを更新し、二重の正本を作らない。

既存の3 episodeは移行時にDBへimportする。元ファイルを即座に削除する必要はない
が、import sourceとして凍結し、その後は更新しない。削除またはarchiveの時期は
移行計画で決める。

### 3.5 ローカルとGitに残すもの

一元化は、すべてのバイトをDBへ投入することではない。情報の意味と既存の所有者
に従って、次はDBへ複製しない。

| 保存先 | 残すもの | 理由 |
|---|---|---|
| local | Codex/Claude等が生成するsession transcript | 実行環境側で生成され、サイズ、形式、private proseの扱いが異なるため |
| local | `nctl ops`のplan/result/events等 | 既存のoperation evidenceが正本であり、大きな証拠本体を複製しないため |
| local | 改善セッション中のdraft、test output、build artifact | 一時的または再生成可能な作業物であるため |
| local | token、秘密鍵、その他secret | DBを含む別領域へ複製しないため |
| Git | policy、agentdocs、skill、設計文書、実装コード | review、versioning、matched rolloutが必要な再利用可能知識であるため |

DBの`references`には、可能な限りmachine-localな絶対パスではなく、session ID、
operation ID、Braindump ID、object ID、Git commitなどの安定した識別子を保存する。
operation evidenceの本文やsession transcript本文はコピーしない。

## 4. 操作面の提案

`WorkflowEpisode`はdesired-state batchに混ぜない。Braindumpと同様に専用REST APIと
nctlコマンドを持たせ、Nautobot GUIはread-onlyとする。

初期コマンド面は概念的に次を想定する。正確な名前と、各操作のplan/apply境界は
ロードマップで決める。

```text
nctl workflow-episode create
nctl workflow-episode list
nctl workflow-episode show EPISODE_ID
nctl workflow-episode select EPISODE_ID
nctl workflow-episode complete EPISODE_ID
nctl workflow-episode dismiss EPISODE_ID
```

report、assessment、resolutionを別段階で書く場合は、それぞれを明示した専用操作に
分けてもよい。GUIからのadd/edit/deleteは提供せず、書き込み規則と検証をnctl/API
側に一元化する。

## 5. 最小GUI

初期GUIは高度なダッシュボードではなく、read-onlyのlist/detailでよい。

一覧には少なくとも次を表示する。

- episode ID
- title
- status
- created
- last_updated

既定表示は`candidate`と`selected`とし、`completed`と`dismissed`もstatus filterで
参照できるようにする。detailでは`raw_data`を単純なJSON dumpのまま見せるだけで
なく、`report`、`assessment`、`references`、`resolution`の各セクションとして
人間が読める形に表示する。

初期フィルターはstatusと通常の検索に絞る。たとえばtarget level別の絞り込みが
実際に繰り返し必要になったら、その時点で`target_level`をカラムへ昇格させて
filtersetへ追加する。

## 6. 二つ目のagent session type

`agentdocs`には、仮称`workflow-improvement`を`brainforge`に続く二つ目の明示的な
session typeとして追加する。

想定する開始と終了の流れは次の通りである。

1. 人間がnintent GUIで`candidate`を俯瞰する。
2. 改善対象のepisode IDを選び、状態を`selected`へ進める。
3. `pj-clusterintent`で
   `nctl session new workflow-improvement --topic <episode-id>`相当の操作により、
   独立した改善セッションを開始する。
4. エージェントは`nctl workflow-episode show <episode-id> --json`相当の操作で、
   report、assessment、referencesをDBから読む。
5. 必要な場合だけ参照先のsession transcriptまたは`nctl ops` evidenceを読む。
6. policy、agentdocs、skill、nctlまたは各submoduleを改善し、該当するテストと
   acceptance evidenceで結果を確認する。
7. DB上の`resolution`と`status`を更新する。

このsession typeは、元のcluster operationと後日のworkflow improvementを分離する
既存のtime-separation規則を具体化する。元episodeの証拠を書き換えたり、改善判断を
直接desired stateまたはactual stateへ反映したりしてはならない。

## 7. 既存ポリシーへの影響

実装時には、既存のEasier Next Time policyにある次の運用を更新する必要がある。

- セッション終了時のself-report保存先を、ローカルepisode directoryからnintentの
  `WorkflowEpisode`作成へ変更する。
- 「episode directoryが監査単位」という表現を、「WorkflowEpisode IDが監査単位」
  へ変更する。
- 後日の`review.md`追加を、DB上の`assessment`更新へ変更する。
- localに残すsession transcriptとoperation evidenceは、本文をコピーせず安定IDで
  参照する規則を維持する。
- cluster operation中にその場でrunbookを改善せず、別の
  `workflow-improvement`セッションで行う規則は維持する。

これは既存ポリシーの目的を変更するものではなく、記録と選択の媒体を、探索しにくい
ローカルファイル群から、一覧・取得・状態管理が可能なnintentへ移す変更である。

## 8. 初期スコープ外

最小実装では次を行わない。

- 全セッションの自動収集または一般的なsession log database化
- session transcriptや`nctl ops` evidence本文のDB複製
- グラフ、スコア、集計中心の高機能ダッシュボード
- 利用実績のないJSON属性の先行カラム化
- WorkflowEpisodeからdesired stateやreconcile actionを自動生成すること
- task card routerやsmall-model replay基盤の同時実装
- 添付ファイル管理基盤または全文検索基盤の先行実装

## 9. ロードマップ作成時に確定する事項

次は本議論では方向だけを示し、実装計画で決定する。

- モデル名、`raw_data`名、status語彙の最終形
- JSON上位構造のvalidationとschema migration方針
- report、assessment、resolutionの書き込みAPIを分ける範囲
- 既存3 episodeのimport方法と、元ローカルファイルのarchive/削除時期
- episode作成をどの運用セッションで必須にするか、その失敗時のsafe-stop規則
- nintent、nctl、GUI、agentdocs、policy変更の実装順序とテスト境界

## 10. 結論

ユーザーの要望は、単なるダッシュボード追加から、workflow improvementに関する
価値ある情報をnintentへ一元化する提案へ発展した。ただしnintentの既存方針に従い、
初期モデルを多数の固定カラムで作らない。

現時点の推奨最小構成は次である。

```text
WorkflowEpisode(title, status, raw_data)
  + dedicated REST/nctl operations
  + read-only Nautobot list/detail GUI
  + agentdocs/workflow-improvement
  + existing local reportsのDB移行
  + Easier Next Time policyの保存先更新
```

この構成により、人間は候補を俯瞰してepisode IDを選べ、エージェントは同じIDから
必要情報を取得できる。一方、カラム昇格、追加自動化、詳細なroutingは、実際の
フィルタリングまたは決定論的処理の需要が確認されるまで延期できる。
