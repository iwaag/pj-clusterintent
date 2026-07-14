# core_reconcile 開発ロードマップ

## 前提

- **破壊的変更フェイズ**: 後方互換性は一切考慮しない。スキーマ・CLI・API はフェーズごとに自由に壊してよい。
- **実験的システム**: 商用製品ではない。セキュリティは「LAN内運用・平文で困る認証情報を吐かない・Nautobot トークンを Git に入れない」程度の最低限でよい。
- 実装コストより設計としての満足度・将来の拡張性を優先する。

## ビジョン

nintent が持つ desired state と、nodeutils / Nautobot が持つ actual state の差分(drift)を計算する **Reconciliation Engine を唯一の真実** とし、その出力を3方向に配る:

1. **人間** — drift を可視化するダッシュボード(当面は静的HTML、将来は3D/音声UI)
2. **AI** — 構造化JSONを読んで診断・例外処理を行う
3. **自動化** — 定型ワークフロー(dnsmasq 設定生成など)を決定的に実行する CLI `nctl`

AIの役割は「毎回手順を組み立てる実行者」から「`nctl` を呼び、収束しないケースだけ差分JSONを読んで診断する例外処理係」へ格上げする。

### 将来UIを見据えた設計規約(全フェーズ共通)

将来のフロントエンド(ゲームエンジンによる3D表現・音声指示など)を「差分エンジン出力の購読者の一種」にできるよう、最初から守る:

1. **core ライブラリ + 薄いCLI の分離** — 実装は `nctl_core`(Python ライブラリ)に置き、CLI は薄いラッパー。将来は同じ core を HTTP/WebSocket API が包む。
2. **全出力のJSONスキーマ化** — すべてのコマンドは `--json` で安定スキーマを返す。人間向けテキストは JSON からの整形に過ぎない。
3. **長時間処理のイベントログ化** — reconcile 等には operation ID を振り、`started / step_completed / drift_resolved / failed` などのイベントを JSON Lines で吐く。当面の消費者はログファイルとAI、将来はリアルタイムUI。

---

## Phase 0: 足場づくり

**ゴール: `nctl` の骨格と設計規約の確立。**

- 親リポジトリ(pj-clusterintent)直下に `nctl/` を新設(`nctl_core` ライブラリ + CLI エントリポイント、uv 管理)。
- Nautobot GraphQL クライアント、nodeutils ダンプの読み込み、設定ファイル(`nctl.toml`: Nautobot URL/トークン参照、インベントリパス等)の共通層。
- JSON 出力・イベントログ(JSON Lines + operation ID)の共通フォーマットを定義し、以後の全コマンドに強制する。
- `nctl status` (Nautobot 疎通・サブモジュール状態の確認)を最初のコマンドとして実装し、規約の実例とする。

**Exit criteria**: `nctl status --json` が安定スキーマで動く。イベントログの書式がドキュメント化されている。

## Phase 1: dnsmasq ワークフローの焼き込み

**ゴール: 最頻出の定型作業を決定的な1コマンドにし、AIのトークン消費と非再現性を即座に解消する。**

- `nctl render dnsmasq` — nintent の desired endpoints を GraphQL で取得し、Jinja2 テンプレートで DHCP 予約 / DNS 対応表を生成。
- `nctl apply dnsmasq --diff` — 現行設定との diff を表示(dry-run 既定)、承認後に該当 playbook を実行。Nautobot 往復と playbook 呼び出し順序はすべて内部に隠蔽。
- Claude Code 用の薄いスキル(`.claude/skills/`)を定義し、「dnsmasq 更新して」が常に同じコマンド列に落ちるようにする。

**Exit criteria**: dnsmasq 更新が人間・AIどちらからも `nctl` 2コマンドで完結し、dry-run diff で内容を事前確認できる。

## Phase 2: Reconciliation Engine(差分エンジン)

**ゴール: desired vs actual の drift 計算を単一のエンジンに集約する。**

- nintent desired / Nautobot actual / nodeutils ダンプの3ソースを突き合わせ、ノード・サービスごとに `converged / drifting / converging / unknown` を判定。
- 差分の内容(例:「desired では DHCP 予約ありだが actual に MAC 未登録」)を構造化JSONの差分リストとして出力: `nctl drift [--host X] --json`。
- nintent のモデル定義を共有ライブラリ化し、desired スキーマの二重定義を避ける(破壊的変更フェイズなので nintent 側の再構成も躊躇しない)。
- 判定ルールはプラガブルに(リソース種別ごとの comparator を追加登録できる構造)。

**Exit criteria**: `nctl drift --json` がクラスタ全体の drift を1回の実行で返し、AIがそれだけを読んで状況説明できる。

## Phase 3: 可視化ダッシュボード

**ゴール: 人間が Nautobot を巡回せず1画面で状況把握できる。**

- `nctl dashboard` — Phase 2 の差分JSONから静的HTMLを生成。クラスタ全体を緑/黄/赤で一覧し、クリックで差分詳細を文章表示。
- reconcile / drift 実行のたびに再生成。ホスティングは手元ファイルまたはLAN内の静的配信で十分(認証なしで可)。
- Nautobot 側は nintent プラグインに reconciliation status フィールドとダッシュボードへのリンクのみ追加(Nautobot は台帳、可視化は外、と割り切る)。

**Exit criteria**: ダッシュボードだけでクラスタの健全性と drift 内容が把握できる。

## Phase 4: 自動収束ループ

**ゴール: drift 検出から解消までを1コマンドに。AIを例外処理係にする。**

- `nctl reconcile [host]` — drift 検出 → 必要な playbook 群を正しい順序で実行 → nodeutils で再調査 → 収束確認、までを1オペレーションとして実行。全ステップをイベントログに記録。
- dnsmasq 以外の定型ワークフロー(ノード初期セットアップ、サービス配置など)を順次 reconciler として登録。
- 失敗・非収束時は operation のイベントログと drift JSON を残して停止。AIがそれを読んで診断する運用フローを確立(診断用スキルの整備)。
- 任意: cron / スケジューラによる定期 drift 検出と通知。

**Exit criteria**: 正常系は人間・AIの介在なしに `nctl reconcile` で収束し、異常系のみAI診断に回る。

## Phase 5: リアルタイムAPI層(将来UIへの布石)

**ゴール: 3D・音声などの高度なUIが「新しい購読者」として接続できる状態にする。**

- `nctl serve` — `nctl_core` を包む HTTP API(状態スナップショット・drift 取得・reconcile 起動)+ WebSocket(イベントストリーム配信)。認証は最低限(トークン1本程度)。
- イベントスキーマを凍結に向けて整理(このフェーズ以降、UI開発が始まったら互換性を意識し始める境界)。
- 参考実装として、WebSocket を購読してブラウザでライブ更新されるダッシュボード(Phase 3 の動的版)を1枚作り、購読者APIの実用性を検証する。

**Exit criteria**: 外部プロセスが API 経由で「現在状態の取得」「変更の指示」「進行イベントの購読」をすべて行える。ゲームエンジン製UIはこのAPIの上に(バックエンド変更なしで)構築可能。

---

## フェーズ順序の意図

- Phase 1 を差分エンジンより先に置くのは、効果(トークン消費・再現性)が最も早く出るのが dnsmasq ワークフローだから。
- Phase 2〜3 で「状況把握」問題を解き、Phase 4 で「定型ワークフロー」問題を一般化して解く。
- Phase 5 は将来UIの計画が具体化するまで着手しなくてよいが、Phase 0 の設計規約を守っていれば追加コストは薄いAPI層のみで済む。
