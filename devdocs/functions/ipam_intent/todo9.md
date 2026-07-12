# Step 9 Todo: Close The Applied-State Loop

Step 9 は今回はスキップする。

目的は、nintent が `desired`、`exported`、`deployed`、`observed` を区別できるようにし、
どの段階が未適用または stale なのかを evaluation に出すこと。

## Priority 1: Track Deployed Artifact Identity

まずは dnsmasq artifact が実際に deploy されたかを追跡する。

必要な作業:

- Ansible deploy 後に `job_result_id`、artifact filename、SHA256 checksum、配置先 path、target host、deploy time を記録する。
- 記録形式は最初は JSON report でよい。
- `deploy_nintent_dnsmasq_records.yml` の実行結果として、controller 側または target 側に report を残す。
- latest export の checksum と deployed checksum を比較できる形にする。

初期完了条件:

- `dnsmasq-records.conf` がどの JobResult 由来で、どの checksum で、どの host に置かれたか分かる。

## Priority 2: Import Or Evaluate Deployment Facts In nintent

次に、deploy report を nintent 側で評価できるようにする。

候補:

- 新しい model を追加して deployed artifact facts を保存する。
- もしくは初期段階では Job が JSON report を読み、`IntentEvaluation` に observed facts として保存する。

必要な evaluation:

- latest export が存在しない。
- deployed artifact が存在しない。
- latest export checksum と deployed checksum が違う。
- deployed artifact の `job_result_id` が latest export と違う。
- target host ごとの deployment が stale。

初期 gap code 候補:

- `missing_dnsmasq_export`
- `missing_dnsmasq_deployment`
- `stale_dnsmasq_deployment`
- `dnsmasq_artifact_checksum_mismatch`
- `dnsmasq_artifact_job_result_mismatch`

## Priority 3: Verify Runtime dnsmasq State

artifact 配置確認の次に、dnsmasq runtime が期待どおり動いているかを見る。

候補:

- target host 上の `/etc/dnsmasq.d/nintent-records.conf` checksum を収集する。
- `dnsmasq --test` 結果を収集する。
- `systemctl is-active dnsmasq` を収集する。
- reload/restart time を収集する。

初期完了条件:

- nintent evaluation が「export は最新だが target host の deployed file が古い」などを説明できる。

## Priority 4: Verify DNS Answers

runtime file が一致していることを確認した後に DNS answer を見る。

候補:

- Ansible または別 collector で `dig @<dnsmasq_host> <dns_name>` を実行する。
- `host-record`、`address`、`cname` の expected answer と observed answer を比較する。
- TTL や upstream recursion ではなく、まず nintent 管理 record の answer 一致に絞る。

初期 gap code 候補:

- `missing_dns_answer`
- `dns_answer_mismatch`
- `dns_query_failed`

## Priority 5: Verify DHCP Lease And Node Observation

最後に DHCP lease と nodeutils actual facts を合わせる。

候補:

- dnsmasq lease file を収集して MAC/IP/name を読む。
- `DesiredEndpoint.ip_policy=dhcp_reserved` の MAC/IP/name と lease を比較する。
- nodeutils の observed primary IP/MAC と desired endpoint、IPAM facts を比較する。

初期 gap code 候補:

- `missing_dhcp_lease`
- `dhcp_lease_ip_mismatch`
- `dhcp_lease_mac_mismatch`
- `node_observed_ip_mismatch`
- `node_observed_mac_mismatch`

## Suggested Minimal First Slice

Step 9 を再開するなら、最初は以下だけでよい。

1. Ansible deploy report に `job_result_id` と SHA256 checksum を出す。
2. nintent 側で latest export checksum と deployed checksum を比較する。
3. `IntentEvaluation` に `exported` と `deployed` の observed facts を入れる。
4. stale/missing deployment の gap を出す。

DNS query、lease file、nodeutils との突合はその後でよい。
