# DesiredEndpoint と IPAM の責務分離を明確にする追加提案

既存の `suggestion.md` は、nodeutils が収集した actual state を custom field
だけに閉じ込めず、Nautobot 標準モデルである Interface や IPAM に段階的に
展開していく方針として妥当。

この追加メモでは、その方針を踏まえて、`DesiredEndpoint` と Nautobot IPAM
をどう分担させるかを整理する。

## 結論

`DesiredEndpoint` は IPAM があるから不要、とは考えないほうがよい。

IPAM は IP アドレス資源の台帳であり、`DesiredEndpoint` は desired node が
持つべき接続面の intent である。両者は似た情報を持つが、抽象度と責務が違う。

- `DesiredEndpoint`: どの desired node に、どの用途の endpoint がほしいか
- `IPAddress`: IPAM 上でその IP が予約または割当済みか
- `Interface`: actual node 上でどの MAC/interface が観測されたか
- `IntentEvaluation`: desired、IPAM、actual observation の差分

したがって、`DesiredEndpoint` を消して `IPAddress` の custom field に寄せる
より、`DesiredEndpoint.realized_ip_address` で IPAM オブジェクトへリンクする
現在の方向を強化するほうがよい。

## DesiredEndpoint が持つべきもの

`DesiredEndpoint` は、IPAM だけでは表しにくい intent を保持する場所として使う。

- endpoint の用途: `primary`, `management`, `service`, `vpn`, `mdns`
- desired node との所属関係
- DNS 名、mDNS 名、VPN alias
- protocol / port のような接続メタデータ
- dnsmasq export 対象かどうか
- dnsmasq record type
- IPAM オブジェクトが未作成でも保持したい desired IP

特に `DesiredEndpoint.ip_address` は、IPAM 作成前でも intent を書ける
ステージング値として有用。これは IPAM と重複しているというより、
「まだ realized object がない desired value」と見ると扱いやすい。

## IPAM が持つべきもの

IPAM 側は、desired intent ではなく IP アドレス資源の状態を表す。

- prefix 内でその IP が存在するか
- 重複がないか
- 予約済みか、実割当済みか
- DNS 名など IPAM 標準属性で表せる情報
- Device/VM interface への割当
- Nautobot 標準検索、関連、監査の対象

このため、IPAM は dnsmasq 適用確認後まで空にしておくより、
desired endpoint が `approved` または `active` になった時点で
予約台帳として更新するほうが自然。

ただし、その時点で「実際に DNS/DHCP が効いている」とはみなさない。
IPAM 更新と実適用確認は別の状態として扱う。

## 推奨する状態の流れ

最初は単純な 1 node + 1 primary endpoint の運用を想定してよい。

```text
DesiredEndpoint 作成
  -> IPAM reconcile で IPAddress を作成または既存リンク
  -> desired endpoint の realized_ip_address を設定
  -> Evaluate Endpoint Intent
  -> Export dnsmasq Records
  -> Ansible などで dnsmasq へ反映
  -> nodeutils / DNS query / lease 確認で actual を収集
  -> Evaluate Endpoint Intent を再実行
```

この流れでは、IPAM reconcile の時点は「予約・割当予定の台帳更新」、
dnsmasq 適用後の評価は「actual state が desired に追いついたかの確認」と
役割を分ける。

## 追加 Job の候補

`Export dnsmasq Records` に IPAM 作成を混ぜるより、別 Job として
`Reconcile Desired Endpoints to IPAM` を追加するほうがよい。

この Job の責務:

- `DesiredEndpoint.ip_address` を parse する
- 対応する `IPAddress` が存在するか探す
- 存在しなければ作成する
- 存在して一意に安全なら `realized_ip_address` にリンクする
- IP が重複、prefix 不明、所有者不一致、複数候補なら自動変更しない
- 失敗理由を `IntentEvaluation.recommended_actions` に寄せる

`Export dnsmasq Records` は引き続き dry-run artifact の生成に専念させる。
dnsmasq export が副作用として IPAM を変更し始めると、生成、予約、適用確認の
境界が曖昧になる。

## どちらを authoritative にするか

初期段階では、`DesiredEndpoint.ip_address` を desired value として扱う。
IPAM reconcile 後は、`DesiredEndpoint.realized_ip_address` が存在するなら
IPAM 側を realized object として優先する。

評価ロジック上は次のように扱うと分かりやすい。

1. expected: `DesiredEndpoint.ip_address`
2. realized allocation: `DesiredEndpoint.realized_ip_address`
3. actual observation: Interface/IPAM assignment、nodeutils facts、DNS/DHCP 確認

`DesiredEndpoint.ip_address` と `realized_ip_address.address` が違う場合は
`conflict`。IPAM に同じ IP があるがリンクされていない場合は `partial`。
IPAM にない場合は `partial` として `create_or_link_ip_address` を推奨する。
この方向は現在の `evaluate_endpoint_intent()` の考え方と合っている。

## IPAM の status の扱い

Nautobot 側で利用できる status は環境依存があり得るため、実装時は固定名に
依存しすぎないほうがよい。ただし概念としては以下を分けたい。

- desired から確保しただけ: reserved / planned
- 実 interface に割り当たっている: active
- deprecated / retired な desired node に紐づく: deprecated 相当

最初の実装では、無理に status 自動遷移まで入れず、
IPAddress 作成・リンクと評価結果の記録に絞ってもよい。
status 遷移は運用が見えてから追加したほうが安全。

## DNS 名の扱い

dnsmasq 向け DNS 名は `DesiredEndpoint.dns_name` を主入力として維持する。
IPAM の `dns_name` は、reconcile 時に合わせられるなら合わせる。

ただし、IPAM 側の DNS 名と `DesiredEndpoint.dns_name` が異なる場合は
即時上書きではなく `conflict` として扱うほうが安全。IPAM は他の用途から
更新される可能性があり、dnsmasq intent と IPAM DNS 名のどちらを優先するかは
運用判断が必要になる。

初期ポリシー:

- IPAM 作成時は `DesiredEndpoint.dns_name` を入れる
- 既存 IPAddress の DNS 名が空なら補完する
- 既存 IPAddress の DNS 名が異なるなら自動上書きせず評価で conflict

## 削除・解放の扱い

`DesiredEndpoint` が retired/deprecated になったときに、IPAM の `IPAddress`
を即削除するのは避ける。

まずは以下のような保守的な扱いがよい。

- `DesiredEndpoint` は残す、または lifecycle 側で retired にする
- `IPAddress` は削除せず status 変更またはタグ/メモで解放候補にする
- dnsmasq export からは lifecycle 条件で除外する
- 実際の IPAM 削除は別 Job または人間の review を挟む

actual state は一時的に観測できないことがあるため、自動削除を早く入れると
評価が不安定になる。

## 実装順序の提案

### Step 1: IPAM reconcile Job を追加

`DesiredEndpoint.ip_address` から `IPAddress` を作成またはリンクする Job を
追加する。最初は primary endpoint と generate_dnsmasq 対象に限定してもよい。

完了条件:

- 一意な未リンク IPAddress はリンクされる
- 存在しない IPAddress は作成される
- 重複や DNS 名不一致は自動上書きされない
- 実行結果がログと評価 action で確認できる

### Step 2: endpoint evaluation の事実を少し拡張

現在の endpoint evaluation は IPAddress 候補と MAC 候補を見ている。
ここに IPAM reconcile の観点を明示する。

- `observed_facts.ipam_allocation_status`
- `observed_facts.ipam_dns_name`
- `gap_summary.gaps[].code = ipam_dns_name_mismatch`
- `recommended_actions[].action = reconcile_ipam_address`

既存の `create_or_link_ip_address` は残しつつ、IPAM reconcile Job が処理できる
action として整理するとよい。

### Step 3: dnsmasq export の IP ソースを明確化

当面は `DesiredEndpoint.ip_address` を使い続けてよい。
ただし、`realized_ip_address` がリンク済みで expected と一致している場合は、
export metadata にその IPAddress ref を入れると監査しやすい。

重要なのは、export が IPAM を変更しないこと。
export は評価済みの desired state から deterministic artifact を作るだけにする。

### Step 4: 適用確認を別評価として追加

dnsmasq ファイル生成済み、Ansible 適用済み、実際の DNS/DHCP 確認済みは
それぞれ別の状態。

最初は Ansible 側が `dnsmasq-export.json` の job_result_id や hash を記録し、
後から Nautobot Job が「どの export が適用済みか」を評価できる形にする。

確認方法の候補:

- dnsmasq ホスト上の配置済みファイル checksum
- `dig` による DNS 応答確認
- DHCP lease file の MAC/IP/name 確認
- nodeutils が報告する primary IP / MAC との一致

ここまでできると、IPAM は予約台帳、dnsmasq は適用機構、nodeutils は観測、
nintent は desired と評価、という分担がはっきりする。

## 避けたい設計

### IPAM だけに desired endpoint を畳み込む

`IPAddress` custom field に endpoint type、desired node、dnsmasq record type、
generate flag などを詰め込むと、IPAM が intent app の内部モデルのようになる。
短期的にはモデル数が減るが、service endpoint や management endpoint が増えた時に
表現が苦しくなる。

### dnsmasq export 時に IPAM を暗黙更新する

export は本来 dry-run 可能な生成処理であり、副作用を持たせると運用上の
予測可能性が落ちる。IPAM 更新は reconcile Job として明示的に実行するほうがよい。

### 適用確認後まで IPAM を空にする

IPAM が予約台帳として機能せず、IP 重複や prefix 管理を dnsmasq 適用直前まで
検出しにくくなる。IPAM は「実際に ping できる IP だけを載せる場所」ではなく、
使う予定の IP を安全に確保する場所としても使う。

## まとめ

`suggestion.md` の actual state 正規化方針に、この追加方針を重ねると、
次の分担になる。

- nintent: desired node / desired endpoint / evaluation
- Nautobot IPAM: IP アドレス資源の予約・割当台帳
- Nautobot Interface: actual MAC/interface の正規化先
- nodeutils custom field: raw facts とフォールバック
- dnsmasq export: deterministic deployment artifact
- Ansible 等: artifact の適用
- 再評価 Job: 適用済みか、desired と actual が一致したかの確認

この分担なら、`DesiredEndpoint` は IPAM と重複する余計なモデルではなく、
IPAM と actual state を束ねて評価するための intent 側のアンカーとして残せる。
