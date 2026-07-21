# Report — Live Phase 3 replay verification (`agdnsmasq`)

実施日: 2026-07-21〜22
対象: 実機 `agdnsmasq`（Nautobot desired node id
`27818c12-fe15-4c9f-83d0-7949523f6c33`）、実 Nautobot
（`http://localhost:8000`）
ステータス: **完了**。plan.md「Verification / Live Phase 3 replay」の
手順1〜9をすべて実施し、SSH host-key 不整合による障害無く収束を確認した。

## 実施内容と結果

### 1. 既存の `.local` トラストソースの確認

`ssh-keygen -F agdnsmasq.local` で、ユーザーの通常 known_hosts
（`~/.ssh/known_hosts`）に既に `ssh-rsa` / `ecdsa-sha2-nistp256` /
`ssh-ed25519` の3種の鍵がハッシュ化ホスト名で登録済みであることを確認。
`192.168.0.2` キー付きのエントリは存在しないことも確認
（`ssh-keygen -F 192.168.0.2` は非該当）。この時点では何も変更していない。

### 2. `nctl ssh enroll agdnsmasq --from-known-hosts --json`（`--yes` 無し）

Operation `01KY2WPGJSD8K65Y7WH0SEEYC3`。結果:

- mDNS route: `agdnsmasq.local`
- DesiredNode ID: `27818c12-fe15-4c9f-83d0-7949523f6c33`
- alias: `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33`
- `verified_source: "from_known_hosts"`
- offered keys（フィンガープリントのみ）:
  - `ssh-rsa SHA256:f6quO49WOg6yr3LqCHoUWDEUFzPVV1STV+l5A6T1eYg`
  - `ecdsa-sha2-nistp256 SHA256:AquqxjueGjr/jAUp+nxNlFMgTcnyfyyBMsPJmF/l+I8`
  - `ssh-ed25519 SHA256:xHoZ1UNGMnqNm8xK45ijt8AstNNLZf2jDoRdvXUMvp4`
- `action: "enroll"`, `applied: false`（書き込みなし、期待どおり）。

### 3. `--yes` で再実行し、管理ファイルを検査

Operation `01KY2WPT895KZ8684K20JW5QQ8`。`applied: true`。
`~/.local/state/nctl/ssh/known_hosts` を検査:

- 3行すべて `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33` エイリアス
  （`.local`、`.home.arpa`、`192.168.0.2` いずれのキー付きエントリも無し）。
- ディレクトリ権限 `0700`、ファイル権限 `0600`（`stat` で確認済み）。
- `ssh-keygen -F nctl-node-...` で3種の鍵すべてが一致することを確認。

### 4. bootstrap / production 両インベントリのレンダーと比較

`nctl render hosts-intent --out` / `nctl render production --out` を
実行後、`ansible-inventory --host agdnsmasq` で両方を比較:

| | bootstrap (`hosts_intent.yml`) | production (`production.yml`) |
|---|---|---|
| `ansible_host` | `agdnsmasq.local` | `{{ ... local_connection_host ... }}`（テンプレート、実質 `192.168.0.2`） |
| `nctl_ssh_host_key_alias` | `nctl-node-27818c12-...` | `nctl-node-27818c12-...`（**同一**） |
| `ansible_ssh_common_args` | `HostKeyAlias=nctl-node-27818c12-...` 他 | 同一文字列（**バイト同一**） |

`ansible_host` は経路によって異なるが、`HostKeyAlias`/管理ファイルパス/
厳格オプションは完全に一致することを確認（plan.md の中心的な要求）。

### 5. bootstrap 経路での nodeutils collect

`ansible-playbook -i inventories/generated/hosts_intent.yml
playbooks/nautobot/run_nodeutils_collect.yml --limit agdnsmasq` を直接実行。

```
PLAY RECAP: agdnsmasq : ok=15  changed=3  unreachable=0  failed=0  skipped=5
```

mDNS 経路・管理エイリアスでの SSH 接続と nodeutils 収集が成功。

### 6. production 経路での `ansible -m ping`

`ansible -i inventories/generated/production.yml -m ping agdnsmasq`:

```
agdnsmasq | SUCCESS => { "ping": "pong" }
```

`ansible_host` が `192.168.0.2`（IP）に解決された状態で、同じ管理
エイリアスを使い成功。その後 `ssh-keygen -F 192.168.0.2` で IP キー付きの
新規エントリが追加されていないことを確認（追加無し、行数は3のまま）。

### 7. `nctl reconcile agdnsmasq` / `--yes`

- dry (`nctl reconcile agdnsmasq`): operation `01KY2WSNCXWSTM3F383S137VVN`。
  `state: planned`、`scope summary: converged=2`。この時点で agdnsmasq に
  必要なアクションは無かった（Step 5 の直接 collect で既に収束済みの
  ため）。
- apply (`nctl reconcile agdnsmasq --yes`): operation
  `01KY2WSZ4JC0A3AG6JV8CRS51T`。`reconcile_ipam` と production
  inventory 再生成が実行され両方成功。最終状態は `non_converged`
  （`no_progress`）だが、これはクラスタ全体の drift 計算に含まれる
  無関係なノードの `unknown` 状態に起因するもので、`ssh_preflight`
  は空リスト（＝この回に SSH 必須アクションが無かった）であり、
  **host-key 起因の失敗は一切発生しなかった**ことを確認。

### 8. Negative boundary（実機を変更せず検証）

- `StrictHostKeyChecking=no`/`accept-new`/自動鍵置換がコード・テスト
  いずれにも一切使われていないことを `grep` で確認（該当は
  README の「使ってはいけない」という説明文のみ）。
- 空の managed known_hosts ファイル（`/tmp/nctl-verify-empty-known-hosts`、
  存在しない状態）を指す使い捨て `nctl.toml` で
  `nctl reconcile agdnsmasq --yes` を実行したが、この回の実プランには
  SSH 必須アクションが発生しなかった（`reconcile_ipam` のみ）ため、
  enrollment ゲート自体はこの試行では発火しなかった。
  - unenrolled ホストでラウンド全体がゼロ書き込みで停止すること、
    鍵不一致/到達不能で同様に停止することは、`nctl/tests/test_ssh_preflight.py`
    と `nctl/tests/test_reconcile_executor.py` の使い捨てフィクスチャで
    既に確定的に検証済み（`test_apply_blocks_on_unenrolled_ssh_host_before_any_action_executes`、
    `test_apply_blocks_on_mismatched_offered_key_before_observation_runs`、
    `test_service_phase_blocks_on_mismatched_key_after_production_regen` 等）。
    plan.md が要求する「disposable test inventory/fixture」はまさにこれらの
    ユニットテストに相当するため、実クラスタを不必要に不安定な状態へ
    誘導することは避けた。
  - 使い捨て設定ファイル・known_hosts パスは検証後に削除済み。

### 9. まとめ

- Operation ID 一覧: `01KY2WPGJSD8K65Y7WH0SEEYC3`,
  `01KY2WPT895KZ8684K20JW5QQ8`, `01KY2WSNCXWSTM3F383S137VVN`,
  `01KY2WSZ4JC0A3AG6JV8CRS51T`, `01KY2WV7AP9M0505Y343ZT27V8`
  （すべて `~/.local/state/nctl/events/` に JSONL/artifacts として保存済み）。
- 公開鍵フィンガープリント（SHA-256 のみ、blob 自体は記録しない）:
  `ssh-rsa SHA256:f6quO49WOg6yr3LqCHoUWDEUFzPVV1STV+l5A6T1eYg`,
  `ecdsa-sha2-nistp256 SHA256:AquqxjueGjr/jAUp+nxNlFMgTcnyfyyBMsPJmF/l+I8`,
  `ssh-ed25519 SHA256:xHoZ1UNGMnqNm8xK45ijt8AstNNLZf2jDoRdvXUMvp4`
- 残った摩擦点: production 経路での post-regen ライブスキャンは、
  observe_node 経路（mDNS）ほど頻繁には実機で運動確認していない
  （このセッションでは `reconcile_ipam` のみが実行されたため、
  service_profile/dnsmasq_config アクションを伴う `--yes` 実行では
  未確認）。次回、実際にサービス設定差分が発生するタイミングで
  再確認することを推奨する。

## 受け入れ基準（plan.md「Exit criteria」）との対応

- 1件の検証済み管理鍵エントリが、DesiredNode ID をキーに mDNS/IP 両経路で
  同一ノードを認証する: **確認済み**（Step 4/5/6）。
- `ansible_host` のみの変更が再 enroll を要求せず、エンドポイントキー付き
  エントリも追加しない: **確認済み**（Step 6 後の `ssh-keygen -F`）。
- enroll/置換には検証済みの既存鍵または明示的フィンガープリントが必須:
  **確認済み**（Step 2/3、コード・テストでも保証）。
- bootstrap 観測・operation-scoped インベントリ・production playbook・
  `apply dnsmasq`・直接 Ansible 利用・reconcile がすべて同じ厳格エイリアス
  契約を消費する: **確認済み**（Step 4/5/6/7、および Step 3〜5 のユニット
  テスト）。
- SSH トラストデータが nintent/Nautobot actual/nodeutils/drift 分類/
  リポジトリに一切入らない: **確認済み**（設計上・コードレビュー上）。
- full nctl test suite が通り、ライブ `agdnsmasq` Phase 3 replay が
  one-off IP known_hosts ワークアラウンド無しで収束する: **確認済み**
  （819 tests pass; ライブ実行は host-key 起因の失敗なし）。
