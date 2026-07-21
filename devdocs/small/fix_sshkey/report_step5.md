# Report — Step 5: reconcile/apply preflight and structured failure

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了（一部スコープ縮小あり、下記参照）**（focused: 53 pass / full suite: 812 pass）

## 目的（plan.md Step 5）

`nctl reconcile --yes` が observation/Nautobot Jobs/inventory 書き込み/playbook
実行の前に、SSH を必要とするアクションの対象ノードが管理 known_hosts に
enroll 済みであることを確認し、未 enroll なら書き込み前にラウンド全体を
`ssh_host_key_unenrolled` で止める。ledger-only アクションは対象外。

## 変更内容

### 1. `nctl_core/ssh_enroll.py`
- `_read_raw_lines` / `_entries_for_lookup_name` を `read_raw_lines` /
  `entries_for_lookup_name` に改名（非private化）し、`ssh_preflight.py` から
  再利用できるようにした。ロジック変更なし。

### 2. `nctl_core/reconcile/ssh_preflight.py`（新規）
- `SSH_REQUIRING_RECONCILER_IDS = {"observe_node", "service_profile",
  "dnsmasq_config"}`。`link_actual_node`（Nautobot メタデータ patch）と
  `reconcile_ipam`（Nautobot Job）は実機に SSH 接続しないため対象外。
- `ssh_required_host_slugs(plan, *, reconciler_ids=None)`: プラン中の
  SSH 必須アクションが触るノード slug 集合を返す。`reconciler_ids` で
  絞り込み可能（実行器は `{"observe_node"}` だけを渡してスキャン対象を
  絞る、後述）。
- `check_ssh_enrollment(cfg, host_slugs, snapshot)`: 読み取り専用。管理
  known_hosts に該当エイリアスのエントリがあるかだけを見る
  （`ready` / `unenrolled`）。
- `verify_offered_keys(cfg, host_slugs, snapshot, probe)`: 既に enroll
  済みのホストについて、mDNS エンドポイントの現在提示鍵を管理鍵と比較する
  読み取り専用の棄却チェック（`ready` / `mismatch` / `unreachable`）。
  スキャンは既存の信頼鍵との不一致しか証明できず、新しい鍵を承認する
  ことは絶対にない。

### 3. `nctl_core/reconcile/executor.py`
- `ReconcileData.ssh_preflight: list[dict]` を追加（drift/action 分類には
  一切影響しない、controller-local な付随情報）。
- `_run_plan_only`（`--yes` 無し）: プランに SSH 必須アクションがあれば
  `check_ssh_enrollment` の結果を `data.ssh_preflight` に載せるが、
  **ブロックしない**（zero-write dry plan のまま）。
- `_run_apply`（`--yes`、ラウンドごと）: プラン構築直後・アクション実行前に
  `check_ssh_enrollment` を実行。未 enroll があれば
  `ssh_host_key_unenrolled`（`nctl ssh enroll <slug>` を含む remediation
  付き）でラウンド全体を停止し、observation/Job/inventory 書き込み/
  playbook を一切呼ばない。
- `render_reconcile_text`: `ssh_preflight: ready=[...] unenrolled=[...]`
  のようなサマリ行を追加。

### 4. `nctl_core/dnsmasq_apply.py`
- `--inventory` で任意のインベントリを渡した場合のみ、
  `dnsmasq_server` グループの各ターゲットホストが `_meta.hostvars` に
  有効な `nintent_desired_node_id`（UUID として検証）と
  `nctl_ssh_host_key_alias` を持つことを要求。欠落・不正なら
  `dnsmasq_inventory_untrusted_host` で拒否。設定済みの既定インベントリ
  （nctl 生成物）はこのガード対象外。

### 5. `nctl_core/observation.py`
- `run_observation()` に defense-in-depth のナローガードを追加:
  bootstrap-eligible チェックの直後、Ansible サブプロセス呼び出しの前に
  `check_ssh_enrollment` を実行し、未 enroll があれば `ValueError` を送出
  （reconcile 側のゲートを経由しない直接呼び出しでも安全）。

### 6. README.md
- `[reconcile]` セクションの直後に「SSH trust preflight」段落を追加。

## スコープを縮小した箇所（申し送り）

plan.md Step 5 は「ラウンド開始時のスキャン検証」と「production regen 後の
再検証」の両方を求めているが、以下の理由で **自動実行フローへの
ライブスキャン組み込みは見送った**:

- production フェーズ（`service_profile`/`dnsmasq_config`）の実際の
  接続先は `production/composer.py` の `resolve_connection_variables`
  （`local_ip -> dns -> mdns -> inventory_hostname` の優先順位＋
  `actual_state_policy`/`selected_endpoint` 依存）でしか正しく求まらず、
  それを preflight 側で複製すると別ルート解決ロジックを持つことになり、
  本 fix の核である「ルート表記より安定 ID を信頼源にする」という原則と
  ちぐはぐになる。
- bootstrap フェーズ（`observe_node`）だけなら mDNS で妥当だが、
  それだけを自動スキャンすると service フェーズは未検証のまま残る。
- 既存の reconcile テストフィクスチャの多くが mDNS エンドポイントを
  持たない最小データで、無条件スキャンを有効にすると偽陽性の
  `unreachable` が大量発生する。

`verify_offered_keys` はテスト済み・利用可能な形で実装済みだが、
`run_reconcile(..., ssh_probe=...)` を明示的に渡したときのみ
（`ssh_probe is not None` のときだけ）`observe_node` 対象への
ライブスキャンが有効になる opt-in 設計にした。デフォルト
（`ssh_probe` 省略）では enrollment 存在チェックのみが自動で走る。
これは Design Decision 5 の「a predictable missing-key failure」という
主シナリオ（実際に Operation `01KY2NZR048X0GKWYBN4DVENW5` で起きたもの）
を確実に防ぐが、"鍵が変わった/違う" というより弱いシナリオの自動検知は
今回のスコープに含めていない。ライブ Phase 3 replay（Step 6 検証項目）で
`ssh_probe` を明示的に渡して検証することを推奨する。

## テスト追加

- `tests/test_ssh_preflight.py`（新規、10 tests）: `ssh_required_host_slugs`
  のフィルタ挙動、`check_ssh_enrollment` の ready/unenrolled/unknown_host、
  `verify_offered_keys` の ready/mismatch/unreachable/未 enroll 時スキップ。
- `tests/test_reconcile_executor.py`: `_config()` に `[ssh]` を追加し既定
  ノード ID を事前 enroll（既存20テストが新ゲートで壊れないように）。
  新規4テスト: `--yes` が未 enroll ホストでラウンド全アクション実行前に
  停止すること（observation 呼び出し回数0を確認）、dry plan は
  `ssh_preflight` を報告するがブロックしないこと、ledger-only プランは
  未 enroll ホストがあってもブロックされないこと。
- `tests/test_dnsmasq_apply.py`: `_inventory_payload()` に有効な SSH
  trust vars を追加（既存の `--inventory` テスト2件を修正）。新規2テスト:
  trust vars 欠落ホストの拒否、既定インベントリはガード対象外であること。
- `tests/test_observation.py`: `_config()` を全フィクスチャホスト
  事前 enroll に変更、新規1テスト: 未 enroll ホストで Ansible 呼び出し
  ゼロのまま `ValueError` になること。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_preflight.py nctl/tests/test_reconcile_executor.py \
    nctl/tests/test_dnsmasq_apply.py nctl/tests/test_observation.py
53 passed in 0.34s

$ uv run --project nctl pytest -q nctl/tests
812 passed, 1 warning in 5.27s
```

## 後続への申し送り

- 上記「スコープ縮小」を Step 6 のドキュメント/ライブ検証で明示し、
  ライブ Phase 3 replay では `nctl ssh enroll --from-known-hosts` に加えて
  `run_reconcile(ssh_probe=default_ssh_probe_runner())` 相当の経路
  （もしくは専用の手動 `ssh-keyscan` 確認）で実鍵の一致を人間が確認する
  こと。
- 将来 production ルート解決を preflight 側でも再利用したくなった場合は、
  `production/composer.py` の接続変数解決ロジックを共有ヘルパーとして
  切り出すのが筋が良い（今回は複製を避けるため見送った）。
