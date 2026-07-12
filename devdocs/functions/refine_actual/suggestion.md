# actual state 管理を堅実にしていく方針

現状の `nodeutils -> nauto -> Nautobot` の流れでは、収集した actual state をまず Device の custom field にまとめている。これは開発初期としては扱いやすい。collector の出力を壊さず保存でき、Nautobot 側の標準モデル設計に悩む前に、収集できている情報の品質や揺れを確認できる。

ただし、最終的に「Nautobot には収集した actual state、nintent には desired state を置き、両者を比較可能にする」ことを目指すなら、MAC アドレスや IP アドレスを custom field だけに閉じ込め続けるのは弱い。Nautobot には Interface や IPAM という標準モデルがあり、そこに載せたほうが比較、検索、関連付け、将来の自動化が素直になる。

## 基本方針

custom field は actual state の唯一の正規化先ではなく、収集生データ、要約、互換用の退避場所として扱うのがよい。

MAC アドレスは、最終的には Device/VM にぶら下がる Interface の `mac_address` として表現する。`primary_mac_address` custom field は、初期段階のフォールバックや「nodeutils が選んだ primary interface の要約」として残してもよいが、DHCP 予約や endpoint 評価の第一候補は Interface 側に寄せていく。

IP アドレスは、最終的には IPAM の IPAddress として表現する。desired endpoint の IP と actual IP を比較するなら、文字列 custom field より IPAM のほうが重複、prefix、割当先、DNS 名との関係を管理しやすい。

`inventory_raw_json` のような custom field は引き続き有用。標準モデルへ展開した後でも、collector が実際に何を報告したかを監査するためのスナップショットとして残す価値がある。

## 段階的な移行イメージ

最初の段階では、今の custom field 集約方式を維持しつつ、nintent 側は `primary_mac_address` や `primary_ip_address` を actual facts のフォールバックとして読めるようにする。この状態なら、Interface/IPAM が未整備でも DHCP 予約や基本的な差分評価を進められる。

次の段階では、`nauto` の nodeutils ingest job が `facts.network.interfaces` を Nautobot Interface に展開する。Interface 名、MAC アドレス、enabled 状態、収集元、最終更新時刻を扱えるようにする。collector 側の interface 名が OS ごとに揺れる可能性があるため、最初から過度に同一視せず、Device 内での名前と MAC を中心に保守的に upsert する。

さらに進める段階で、`primary_ip_address` や interface ごとの address を IPAM IPAddress に展開する。IPAddress は Interface との関連付けまで作れると、desired endpoint と actual interface の対応がかなり明確になる。最初は primary IP だけを対象にして、全 interface の全 address 反映は後回しでもよい。

最終的には、nintent の評価ロジックは次の優先順位で actual facts を見る形が望ましい。

1. Nautobot 標準モデル: Device/VM, Interface, IPAM
2. nodeutils 由来の正規化済み custom field: `primary_mac_address`, `primary_ip_address`
3. `inventory_raw_json`: デバッグ、監査、未展開データ確認用

## 注意点

Interface/IPAM への展開は、単に custom field をコピーするだけではなく、upsert と削除・無効化の扱いを慎重に決める必要がある。collector が一時的に情報を取り逃がしただけで Nautobot から Interface や IPAddress を消すと、actual state の履歴や desired state との比較が不安定になる。

削除よりも、まずは `last_seen`、`inventory_source`、`observed_missing` のような状態管理で「今回の収集では見えなかった」ことを表現するほうが安全。十分に安定してから、不要になった actual object の retire/archive 方針を決める。

DHCP 予約の観点では、Interface が複数 MAC を持つ場合や primary interface の判定が曖昧な場合を無理に自動選択しないほうがよい。nintent 側で「MAC 候補が複数ある」「primary が不明」という partial/conflict を出し、人間が desired endpoint 側で明示できる余地を残す。

この移行は一度にやる必要はない。まずは custom field で動く比較を維持しつつ、actual state の中でも重要度が高い MAC、primary IP、Interface から順に Nautobot 標準モデルへ展開していくのが現実的。
