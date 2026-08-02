# Cluster Agent refined idea への意見

対象: `refined_idea.txt`（2026-08-03 時点）
参照: `original_idea.txt`, `README.md`, `README_DEV.md`, `.local/localenv_memo.md`

## 総評

方向性は健全で、このリポジトリの既存の設計原則とよく整合している。特に
「契約が固まる前に Go CLI を作らない」「共有 token ではなくノード単位の
鍵 + mTLS」「証明書 identity を自己申告 slug ではなく DesiredNode UUID に
結び付ける」の三点は、fix_sshkey 系で学んだ「trust identity は安定した
DesiredNode UUID であり、route identity と分離する」という教訓の自然な
延長であり、強く支持する。

一方で、現状の文書は **ノードからの依頼経路の認証** に厚く、
**依頼が認証された後に cluster-agent が何をしてよいか（認可・実行境界）**
と **スマートフォンからの人間経路** が相対的に薄い。前者は安全性の本丸
なので、実装前にもう一段具体化すべきと考える。

## 強く同意する点

- **nctl と配布クライアントの分離。** `nctl` は司令塔でクラスターを操作する
  CLI、`cluster-agent-client` は司令塔へ「依頼を運ぶ」だけの通信クライアント、
  という責務分離は正しい。配布クライアントに nctl 相当の権限や知識を
  持たせない限り、ノード側の侵害が即クラスター操作能力の奪取にならない。
- **curl-first の段階的検証。** API・認証・セッション継続・失敗形を一台の
  ノードから curl で固めてから wrapper → Go CLI へ進む順序は、
  「契約凍結 → 実装」というこのプロジェクトの Phase 0 の流儀そのもの。
  URL や秘密をバイナリへ埋め込まない方針も正しい。
- **OpenCode ランタイムの分離再利用。** node-agent のインスタンス共用を避け、
  cluster-agent 専用のプロセス・設定・セッション保存領域に分け、OpenCode
  自体は loopback 限定にする構成は、権限範囲が全クラスターに及ぶことを
  考えると最低限必要な分離であり妥当。
- **会話セッションを desired/actual ledger に入れない。** 会話は operation で
  あり drift ではない、という整理は既存の Braindump の扱いとも一貫している。
- **HTTPS REST + 非同期（依頼 ID）を基本とし、WebSocket/WebRTC を初期
  スコープ外にする判断。** 長時間 turn は「依頼 ID を返して後で取得」で
  十分であり、これは既存の `nctl ops list` / `nctl ops show` の
  operation-evidence パターンと同型。後述のとおり、むしろ積極的に
  同じ形へ寄せることを勧める。
- **workspace 単位 identity の後回し。** 同一 Unix ユーザー内で鍵を分けても
  境界にならない、という認識は正確で、偽の分離を作らない判断として正しい。

## 懸念と提案

### 1. 認可・実行境界を「別の境界である」で止めず、初期ルールを明文化する

文書は「認証されたことはクラスターを自由に操作できることを意味しない」
「どの nctl 操作を計画・実行するかは別の認可・操作境界」と述べるに
とどまっている。ここが一番事故の起きる場所なので、初期スコープとして
次のような明示ルールを提案する。

- ノード発の依頼に対する cluster-agent の応答は、初期は
  **読み取り（status / drift / relations / 既存サービスの案内）と計画の提示まで**
  に限定する。
- desired state の書き込み、`reconcile --yes`、破壊操作は、ノード発依頼を
  直接のトリガーにしない。cluster-agent が計画を作り、**人間が既存の対話
  経路（VS Code またはスマホ経路）で承認して初めて実行**する。
- この制限は「node-agent からの無制限な自動 cluster mutation はスコープ外」
  という現行記述より一段強く、「初期は承認なしの mutation はゼロ」と
  明記する。

理由はもう一つある。ノード発の依頼本文は cluster-agent の LLM に入る
**信頼できない自然言語入力**であり、prompt injection によって依頼者の
権限を超えた操作を誘発しうる。mTLS はノードの identity を保証するが、
本文の意図の正当性は保証しない。「読み取り + 計画まで、実行は人間承認」
という境界は、この injection リスクに対する最も単純で確実な緩和策になる。

### 2. 依頼を nctl ops と同型の evidence 付き記録にする

「監査」を API の担当として一語で挙げているが、具体形は既に手元にある。
各依頼（および各 turn）に ID を発行し、`<log_dir>/<request_id>/` 形式の
durable evidence（発信ノード identity、受領時刻、本文ハッシュまたは本文、
cluster-agent の応答、実行された nctl 操作への参照）を残し、
`nctl ops` 同様に一覧・参照できるようにすることを提案する。
「Preserve evidence after side effects」（README_DEV 教訓 7）をこの新しい
境界にも最初から適用しておくと、後から監査を足す作業が不要になる。

### 3. 認証台帳の置き場所と検査可能性を早めに決める

「nintent は DesiredNode の存在を所有し、認証台帳は信頼中の公開鍵を所有
する」という分担は managed known_hosts store の設計と同じ形で良い。ただし
次を初期に決めておくべき。

- 台帳の実体（ファイルか DB か）、所有者（cluster-agent API か nctl か）、
  および壊れた台帳と空の台帳の区別（教訓 6「fail closed, but truthfully」）。
- 人間が台帳を確認する手段。nintent モデルにするなら README_DEV の
  「新モデルには最小 read-only GUI」規則が適用される。nintent の外に
  置くなら、少なくとも `nctl` などから列挙・検査できる CLI 面を用意する。
  「API/CLI からしか見えない台帳」は DesiredWorkspace で踏んだ轍になる。
- 失効・rotation は trust boundary の Tier A 対象なので、実際の TLS
  スタックを使った conformance テスト（`test_openssh_conformance.py` の
  mTLS 版: 実鍵・実証明書・loopback サーバで、未失効/失効済/期限切れ/
  未登録/UUID 不一致の各パスを positive evidence 付きで検証）を最初から
  計画に含める。モックだけの mTLS テストは教訓 2（tests can preserve a
  wrong shared assumption）の再演になる。

### 4. 人間（スマホ）経路の identity が未定義

enrollment 節はノード認証のみを扱っており、VPN 越しブラウザの人間の
認証は書かれていない。人間はノードではないので、同じ mTLS 台帳には
乗らない。提案:

- 人間経路とノード経路を **別の identity クラス**として最初から区別する
  （認可ルールが違う: 人間は承認権限を持ち、ノードは持たない）。
- 初期は VPN 到達性 + 単一オペレーター前提の簡素な認証（クライアント
  証明書を人間端末にも一枚発行する、あるいは passkey/basic 認証）で
  よいが、「どちらの経路で来た依頼か」を evidence に必ず記録する。
- ノード経路の実装を人間経路の設計完成でブロックしない。逆も同じ。

### 5. セッション直列化と cluster-agent プロセスの寿命

同一セッション内 turn の直列化は正しいが、次の運用的な問いに初期段階で
答えを持っておくとよい。

- 実行中 turn がある状態で司令塔プロセス（または OpenCode）が再起動した
  とき、依頼 ID で照会したクライアントは何を見るか。「不明」ではなく
  「中断」を返せるか（教訓 7 の evidence 保全と同じ話）。
- セッションの TTL と上限数。ノードが自動でセッションを開ける以上、
  無制限に溜まる。ノード単位 rate limit を挙げているのは良いが、
  セッション数・保存領域にも上限を置く。
- 複数ノードからの同時依頼はセッションが別なら並列でよいのか、
  cluster-agent（= 一つの作業ディレクトリ上のエージェント）として
  グローバルに直列化するのか。nctl reconcile が絡む turn は事実上
  グローバル直列が安全だと思われる。

### 6. 最初の一歩の提案

このプロジェクトの流儀（contract-freeze → 段階実装 → live 検証）に
合わせるなら:

1. **Phase 0（契約凍結）**: API の resource（request/session/turn）、
   状態遷移、エラー形、identity クラス、初期認可ルール（読み取り + 計画
   のみ）を短い契約文書に固める。この段階では実装しない。
2. **Phase 1**: 司令塔 loopback のみで API + OpenCode 分離インスタンスを
   動かし、司令塔上の curl で全契約を検証する（TLS なし、認証スタブ可）。
3. **Phase 2**: mTLS と認証台帳を追加し、conformance テストを整備。
   実ノード 1 台（疎通確認済みの agpc が候補）から curl で enrollment
   から依頼までを通す。
4. **Phase 3 以降**: Ansible での wrapper 配布、スマホ経路、必要に
   なってから SSE / Go CLI。

「S3 互換ストレージが欲しい」ユースケースは、読み取り + 案内だけで
完結する（既存サービスの参照は `nctl relations` の情報で足りる）ため、
初期認可ルールの制限下でも最初の価値実証としてそのまま成立する。
これは偶然ではなく良い設計の兆候で、最初のマイルストーンをこの
ユースケース一本に絞ることを勧める。

## 小さな指摘

- 証明書 identity の URI に DesiredNode UUID を含める案は良いが、UUID は
  `nctl prune` でノードの Desired 記録ごと消える可能性がある。台帳側で
  「UUID が存在しない証明書は自動的に無効」となることを API の接続時
  検査（「DesiredNode が現在依頼可能な状態か」）の仕様に含めておけば、
  prune が事実上の失効を兼ねる。この関係を一文書いておく価値がある。
- 「本文はコマンド引数より標準入力/ファイル優先」はプロセス一覧への
  漏洩対策として細かいが正しい。同じ理由で、curl 検証段階でも本文や
  トークンをシェル履歴・引数に残さない形（`--data @file` 等）を最初から
  習慣にしておくとよい。
- 名称 `cluster-agent-client` は仮称として十分。Go 化の際も「client」で
  あって「ctl」ではない命名を維持すると、nctl との誤解（議論の経緯に
  あった混同）の再発を防げる。
