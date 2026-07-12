# nintent IPAM intent roadmap

このメモは、nintent に IPAM intent を拡張するためのロードマップ。
具体的な実装手順よりも、何を desired state として扱いたいのか、
Nautobot IPAM と nintent の責務をどう分けるのかを整理する。

## 背景

自宅サーバーや小規模ラボでは、物理機器、Nautobot、DHCP サーバーが
まだ完全に立ち上がっていない段階でも、次のような構想を先に決めたい。

- `192.168.0.1-99` は静的固定 IP 用
- `192.168.0.100-199` は DHCP 予約可能
- `192.168.0.200-250` は予約なしの動的 DHCP プール
- 特定の PC やサービス endpoint は予約 DHCP にしたい
- 一部の endpoint は DNS だけ管理したい

Nautobot IPAM には、任意の開始 IP と終了 IP を持つ `IPRange` モデルはない。
Gemini との会話に出てきた `IPRange` は、Nautobot actual/IPAM の既存モデルとしては
採用できない。

ただし、「任意の IP 範囲を設計意図として持ちたい」という要求自体は
nintent の desired state に近い。そこで、Nautobot に存在しない `IPRange` を
actual model として期待するのではなく、nintent 側の intent model として
`DesiredIPRange` のような抽象を追加する方向を検討する。

## 基本方針

nintent は、Nautobot IPAM の代替ではなく、IPAM に載せる前後の
ネットワーク設計 intent を保持する。

- `DesiredIPRange`: アドレス帯の設計意図
- `DesiredEndpoint`: node や service が持つべき個別 endpoint の設計意図
- Nautobot `Prefix`: IPAM 上のネットワークまたはプールの台帳
- Nautobot `IPAddress`: 実際に予約、割当、観測された IP アドレスの台帳
- dnsmasq export: intent から生成される deterministic artifact
- evaluation: intent、IPAM、actual observation の差分

この分担にすると、Nautobot IPAM のモデル制約に合わせるためだけに
設計 intent を CIDR prefix に無理やり分割しなくてよい。
一方で、Nautobot に反映する段階では Prefix や IPAddress へ reconcile する
別 Job を用意できる。

## DesiredIPRange の狙い

`DesiredIPRange` は、まだ DHCP サーバーや Nautobot Prefix が未整備でも、
アドレス帯の用途を nintent に書けるようにするためのモデル。

想定する情報:

- name / slug
- start_address
- end_address
- range_policy
- lifecycle
- description / notes
- generate_dnsmasq
- dnsmasq lease time や option などの export metadata
- 将来的な scope: namespace, location, site, VRF, tenant 相当

`range_policy` の初期候補:

- `static_pool`: 静的固定 IP 用の領域
- `dhcp_reservable_pool`: DHCP 予約を置いてよい領域
- `dhcp_dynamic_pool`: 予約なしで動的配布する領域
- `excluded`: 明示的に使わない、または特殊用途として避ける領域

`dhcp_dynamic_pool` は dnsmasq の `dhcp-range=` 生成対象になる。
`dhcp_reservable_pool` は通常 `dhcp-range=` にはしないが、
`DesiredEndpoint.ip_policy=dhcp_reserved` の妥当性チェックに使う。

## DesiredEndpoint の ip_policy

`DesiredEndpoint` には、個別 endpoint の IP 運用方針を表す
`ip_policy` を追加する。

初期候補:

- `static`: 手動固定 IP。DNS record は出せるが DHCP 予約は出さない
- `dhcp_reserved`: DHCP 予約。`dhcp-host=` 生成対象
- `external`: nintent/IPAM の管理外、または外部管理

このフィールドの目的は、現在 `generate_dnsmasq` に混ざっている
「DNS record を出すか」と「DHCP 予約を出すか」を分離すること。

- `generate_dnsmasq`: dnsmasq 向け DNS record を出すか
- `dnsmasq_record_type`: `host-record`, `address`, `cname` など
- `ip_policy`: IP 割当や DHCP 予約としてどう扱うか

これにより、静的 IP の endpoint には DNS record だけを出し、
DHCP 予約 endpoint には MAC が一意に決まった場合だけ `dhcp-host=` を出す、
という判断が明確になる。

## Evaluation の目標

endpoint evaluation は、IP と MAC の候補確認だけでなく、
IP policy と range policy の整合性も見る。

評価したい例:

- `dhcp_reserved` endpoint の IP が `dhcp_reservable_pool` 内にある
- `dhcp_reserved` endpoint の IP が `dhcp_dynamic_pool` に入っていたら警告または conflict
- `static` endpoint の IP が DHCP pool に入っていたら警告
- endpoint の IP がどの `DesiredIPRange` にも入っていなければ警告
- IP が複数の `DesiredIPRange` に重なっていたら conflict
- `dhcp_reserved` endpoint で MAC 候補が一意なら `dhcp-host=` 生成可能
- `static` endpoint では MAC があっても `dhcp-host=` は生成しない

初期段階では、これらを厳密な失敗にしすぎない。
設計中の home lab では Nautobot 側や actual state が未整備なことがあるため、
まずは `gap_summary` と `recommended_actions` に warning 的なメモを出す。

## dnsmasq export の目標

dnsmasq export は、IPAM を変更せず、評価済み desired state から
deterministic な artifact を生成する。

生成対象:

- `host-record=` / `address=` / `cname=`: `DesiredEndpoint` から生成
- `dhcp-host=`: `DesiredEndpoint.ip_policy=dhcp_reserved` から生成
- `dhcp-range=`: `DesiredIPRange.range_policy=dhcp_dynamic_pool` から生成

現在の `dnsmasq-records.conf` に全部まとめるか、
`dnsmasq-ranges.conf` を別 artifact にするかは実装時に決める。
ただし JSON payload には、DNS records、DHCP reservations、DHCP ranges を
別配列として持たせたほうが、Ansible や監査から扱いやすい。

## Nautobot IPAM との関係

`DesiredIPRange` は Nautobot `Prefix` の完全な代替ではない。
役割は、CIDR にきれいに切れない構想や、IPAM 作成前の設計意図を保持すること。

将来的には別 Job で reconcile できる。

- `DesiredIPRange` を Nautobot Prefix 群へ展開する
- `dhcp_dynamic_pool` は `Prefix.type=Pool` と role/tag へ反映する
- `dhcp_reservable_pool` も role/tag 付き Prefix として反映する
- `DesiredEndpoint.ip_policy=dhcp_reserved` は `IPAddress.type=DHCP` 相当として作成またはリンクする
- 既存 Prefix/IPAddress と衝突する場合は自動上書きしない

ただし、最初の段階で Nautobot Prefix reconcile まで入れる必要はない。
まずは nintent の desired model、evaluation、dnsmasq export を成立させる。

## 段階的ロードマップ

### Phase 1: Intent model を定義する

目標:

- `DesiredEndpoint.ip_policy` の意味を決める
- `DesiredIPRange` の最小モデルを決める
- YAML import/export の表現を決める
- endpoint の IP 運用方針を `static`、`dhcp_reserved`、`external` の
  いずれかとして明示させる

この段階の成果は、実装よりも概念の安定化。
`generate_dnsmasq`、`dnsmasq_record_type`、`ip_policy` の責務を明確にする。

### Phase 2: Evaluation に range awareness を足す

目標:

- endpoint の IP がどの desired range に入るか判定する
- range がない、重複する、policy が合わない場合に gap を出す
- `dhcp_reservation_ready` を `ip_policy` と range policy で補強する
- warning 的な情報を `observed_facts` と `gap_summary` に残す

この段階では、Nautobot IPAM を変更しない。
desired state の中だけで矛盾や危険な割当を見つけられるようにする。

### Phase 3: dnsmasq export を拡張する

目標:

- `DesiredIPRange.range_policy=dhcp_dynamic_pool` から `dhcp-range=` を生成する
- `DesiredEndpoint.ip_policy=dhcp_reserved` のみ `dhcp-host=` 生成対象にする
- `static` endpoint は DNS record だけを生成できるようにする
- JSON payload に `dhcp_ranges` を追加する
- Ansible 側が固定 `dnsmasq_dhcp_ranges` ではなく export artifact を使えるようにする

export は引き続き dry-run artifact 生成に専念する。
IPAM 作成や actual state 更新は行わない。

### Phase 4: IPAM reconcile を追加する

目標:

- `DesiredEndpoint.ip_address` から Nautobot `IPAddress` を作成またはリンクする
- `DesiredIPRange` を Nautobot `Prefix` 群へ安全に反映する方法を用意する
- 既存 Prefix/IPAddress との衝突や所有者不一致は自動修正しない
- reconcile 結果は Job log と evaluation action に残す

この段階で初めて、nintent の intent を Nautobot IPAM の台帳へ反映する。

### Phase 5: 適用確認を閉じる

目標:

- Ansible が適用した dnsmasq artifact の hash や job_result_id を追跡する
- dnsmasq ホスト上の配置済みファイルと export を照合する
- DNS 応答、DHCP lease、nodeutils の actual facts を評価に取り込む
- desired range、desired endpoint、IPAM、actual observation の差分を一貫して見られるようにする

ここまで進むと、nintent は「構想を書く場所」から
「構想、IPAM 台帳、dnsmasq 適用、actual observation を結ぶ評価面」になる。

## 避けたい設計

### Nautobot IPAM に存在しないモデルを前提にする

Nautobot に `IPRange` がある前提で設計しない。
任意範囲の intent が必要なら、nintent 側に `DesiredIPRange` として持つ。

### Prefix だけに構想を押し込む

任意範囲を CIDR Prefix に機械的に分割すれば表現はできるが、
設計意図の読みやすさは落ちる。
Nautobot IPAM へ反映する段階では Prefix 分割が必要でも、
人間が構想を書く段階では `start_address` / `end_address` の range intent を
許したほうが自然。

### generate_dnsmasq に意味を詰めすぎる

`generate_dnsmasq=True` だけで DNS record、DHCP reservation、IPAM 予約の
すべてを意味させると、endpoint の意図が曖昧になる。
DNS 出力と IP 割当方針は `generate_dnsmasq` と `ip_policy` で分ける。

### export に副作用を持たせる

`Export dnsmasq Records` が IPAM を作成、変更、削除し始めると、
dry-run artifact 生成、台帳更新、適用確認の境界が曖昧になる。
IPAM 更新は別 Job に分ける。

## まとめ

今回の結論は、Gemini が出した `IPRange` を Nautobot の existing model として
信じるのではなく、自宅ラボの設計 intent として必要な抽象を
nintent 側に明示的に持つ、ということ。

`DesiredIPRange` と `DesiredEndpoint.ip_policy` を入れることで、
DHCP 動的プール、DHCP 予約可能領域、静的 IP 領域、個別 endpoint の予約意図を
同じ desired state の中で評価できるようになる。
