# Report — Step 2: explicit enrollment core and CLI

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了**（focused: 21 pass / full suite: 788 pass）

## 目的（plan.md Step 2）

`nctl ssh enroll HOST` を実装する。未検証の `ssh-keyscan` 結果は `--yes` を
付けても絶対にトラストを作らず、既に信頼済みの `.local` エントリ一致
（`--from-known-hosts`）または明示 `--fingerprint` のみを検証済みソースとする。

## 変更内容

### 1. `nctl_core/hosts_intent.py`
- `_select_mdns_endpoint` を `select_mdns_endpoint`（非private）に改名。
  Step 1 の設計どおり、enroll 経路がブートストラップと同一の mDNS
  エンドポイント選択規則を再利用する（別実装を作らない）。

### 2. `nctl_core/ssh_enroll.py`（新規）
- `SshProbeRunner`: `ssh-keyscan` / `ssh -G` / `ssh-keygen -F` の注入可能な
  サブプロセス境界（3種の `Callable`）。実装はすべて argv 直接実行
  （シェル経由なし）。デフォルト実装 `default_ssh_probe_runner()` も提供。
- `scan_offered_keys`: 現在提示されている鍵を bounded timeout で観測。
  `TimeoutExpired` を `SshTrustError` に変換。
- `find_legacy_trusted_keys`: `ssh -G` で実効 `UserKnownHostsFile` を解決し、
  `ssh-keygen -F` でホスト名一致エントリ（ハッシュ化名を含む）を取得。
- `select_verified_offered_keys`: legacy 一致（型+blob 完全一致）または
  fingerprint 一致でのみ「検証済み」を返す。
- 管理ファイル I/O: `_read_raw_lines` / `_entries_for_alias` /
  `_lines_excluding_alias` / `_write_managed_file`。対象エイリアスの行だけを
  差し替え、無関係な行・コメントは逐語保存。書き込みは `artifacts.py` の
  `atomic_write_private`（親 0700・ファイル 0600・fsync・atomic rename）を再利用。
- `build_ssh_enroll(cfg, host, *, from_known_hosts, fingerprints, replace,
  apply_changes, probe=None, operation_id=None) -> Envelope[SshEnrollData]`:
  - node/endpoint/port を解決（DesiredNode 不明は `unknown_host`、mDNS
    エンドポイント欠落は `node_without_mdns`、両方 usage 相当）。
  - 検証済み鍵が無ければ `host_key_unverified` を返し、書き込みを一切行わない
    （`--yes` の有無に関係なく）。
  - 既存管理エントリが無ければ `enroll`、完全一致なら `noop`（べき等）、
    異なる鍵なら `conflict`。`conflict` は `--replace` 無しでは常に失敗
    （`host_key_conflict`）。
  - `--yes`（`apply_changes=True`）のときのみ `cfg.ssh.lock_path` を
    `reconcile.lock.acquire_reconcile_lock`（汎用実装のため転用）でロックし、
    ロック境界の内側でスキャン・検証・書き込みまでを再実行（"re-check inside
    the write boundary"）。dry plan（`--yes` 無し）はロックを取らず書き込みも
    しない。
  - `OperationLog`（`nctl.ssh.enroll.v1` 用、`events.log_dir` 配下 JSONL）に
    started/decided/planned/applied/failed を記録。managed known_hosts
    ファイル自体や生スキャン出力はアーティファクト化しない。
  - `SshEnrollData` は鍵種別+SHA-256 フィンガープリントの文字列のみを保持し、
    生の公開鍵 blob はテキスト・JSON いずれの出力にも含まれない。
- `render_ssh_enroll_text`: node/endpoint/port/alias/lookup_name/verified
  source/offered・managed keys/applied・replaced を1コマンドで表示。

### 3. `nctl_core/cli/main.py`
- `ssh_app` Typer グループを追加し `app.add_typer(ssh_app, name="ssh")`。
- `ssh enroll HOST [--from-known-hosts] [--fingerprint ... (repeatable)]
  [--replace] [--yes] [--json]` を実装。既存の `reconcile`/`apply dnsmasq` と
  同じ dry-plan/apply 規約（`--yes` 無し = zero-write）に揃えた。
- 終了コード: `unknown_host` / `node_without_mdns` は `EXIT_USAGE`（2）、他の
  失敗は `EXIT_FAILURE`（1）、成功は `EXIT_OK`。

## テスト追加

### `nctl/tests/test_ssh_enroll.py`（新規、16 tests）
unknown_host / node_without_mdns の usage エラー、未検証スキャンは `--yes`
でも書き込まれないこと、fingerprint 一致での enroll、平文・ハッシュ化
legacy エントリの昇格、legacy 不一致時の失敗、既存同一エントリの noop、
`--replace` 無しでの conflict 失敗、`--replace` はあるが検証済みソースが無い
場合も失敗、`--replace` + 検証済みソースでの対象エイリアスのみの置換
（無関係エントリ・コメントの保存を検証）、dry plan がゼロ書き込みである
こと、非デフォルト port のルックアップ名、keyscan タイムアウト、破損した
keyscan 出力の拒否、JSON 出力に生 blob が含まれないこと。

### `nctl/tests/test_cli_ssh_enroll.py`（新規、5 tests）
text/JSON 出力、フラグの受け渡し（`--from-known-hosts`/`--fingerprint`
repeatable/`--replace`/`--yes`）、`unknown_host` の exit code 2、
`host_key_unverified` の exit code 1。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_enroll.py nctl/tests/test_cli_ssh_enroll.py
21 passed in 0.15s

$ uv run --project nctl pytest -q nctl/tests
788 passed, 1 warning in 5.12s
```

`python -m nctl_core.cli.main ssh enroll --help` の手動確認済み。

## 後続への申し送り

- Step 3/4 で `hosts_intent.py` / `production/composer.py` が
  `derive_host_key_alias` / `build_ansible_ssh_common_args` を消費する際、
  `select_mdns_endpoint` の公開シグネチャ変更（改名のみ、ロジック不変）を
  前提にしてよい。
- Step 5 の reconcile preflight は `ssh_enroll.py` の
  `_entries_for_alias`/`scan_offered_keys` 相当のロジックを再利用できるが、
  現状は enroll 内部のプライベート関数のため、preflight 実装時に共有が
  必要なら公開ヘルパーとして切り出すこと。
- ライブ Phase 3 replay（`nctl ssh enroll agdnsmasq --from-known-hosts`）は
  Step 6 検証フェーズまで未実施。
