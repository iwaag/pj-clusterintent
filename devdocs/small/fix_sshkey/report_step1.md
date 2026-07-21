# Report — Step 1: configuration and pure SSH identity helpers

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了**（focused: 50 pass / full suite: 767 pass）

## 目的（plan.md Step 1）

DesiredNode UUID から決定的な `HostKeyAlias` を導出する純関数群と、それを設定する
`[ssh]` セクションを追加する。エンドポイント名（`.local` / `.home.arpa` / IP）を
一切トラスト識別子に混ぜないことを、この段階のテストで固定する。

## 変更内容

### 1. `nctl_core/config.py`
- `SshConfig`（`StrictModel`）を追加:
  - `known_hosts_file: Path = "~/.local/state/nctl/ssh/known_hosts"`
  - `keyscan_timeout_seconds: float = 10.0`（`gt=0, le=120`）
  - `lock_path: Path = "~/.local/state/nctl/ssh.lock"`
  - `resolved_known_hosts_file()` / `resolved_lock_path()`（`expanduser()`）
- `Config.ssh: SshConfig = SshConfig()` を追加（他の任意セクション同様、`[ssh]`
  省略時もデフォルトで動作）。

### 2. `nctl_core/ssh_trust.py`（新規）
純粋・I/O なしのヘルパー:
- `validate_desired_node_id` / `derive_host_key_alias`: UUID 検証と
  `nctl-node-<uuid>` エイリアス導出。スラッグ・`.local`/`.home.arpa` 名・IP・
  Device ID・MAC はこの導出に一切関与しない。
- `derive_lookup_name(alias, port)`: port 22 は素のエイリアス、非デフォルト
  port は `[alias]:port`。
- `build_ansible_ssh_common_args(alias, known_hosts_path)`: `HostKeyAlias` /
  `UserKnownHostsFile` / `StrictHostKeyChecking=yes` / `CheckHostIP=no` /
  `UpdateHostKeys=no` を1関数に集約し、`shlex.quote` で各 `-o key=value` を
  安全にクオート。
- `compute_sha256_fingerprint`: 公開鍵 base64 blob から OpenSSH 形式
  `SHA256:<base64-no-pad>` を計算。
- `parse_known_hosts_line` / `ParsedHostKeyLine`: 通常の known_hosts /
  keyscan 行のみをパース。空行・コメント・`@cert-authority`/`@revoked`
  マーカーは `None` を返して除外、既知鍵種別以外や base64 破損行は
  `SshTrustError` で明示的に拒否（黙って読み飛ばさない）。
- `is_hashed_hostname_entry`: `HashKnownHosts` 形式（`|1|...`）の判定。
- `ManagedEntry` / `find_managed_entry`: 管理ファイルのエントリ照合は
  エイリアス（+任意で鍵種別）の完全一致のみで行い、エンドポイント名は
  一切参照しない。

### 3. `nctl/example.nctl.toml`, `nctl/README.md`
- `[ssh]` セクション例をコメント付きで追加（credential ではなく local trust
  state であること、`known_hosts_file` は git 管理対象外であることを明記）。
- README に「SSH trust configuration」節を追加（`[ansible configuration]` /
  `[dashboard configuration]` と同じ体裁）。

## テスト追加

### `nctl/tests/test_ssh_trust.py`（新規、35 tests）
- UUID/エイリアス決定性、大文字小文字正規化、非UUID拒否
- 異なる node ID で異なるエイリアス、エイリアスにエンドポイント名が
  含まれないことの明示アサーション
- port 22 / 非デフォルト port のルックアップ名、不正 port 拒否
- `ansible_ssh_common_args` の厳格オプション全出現、スペース入りパスの
  クオート、空入力拒否
- SHA-256 フィンガープリントの既知ベクタ一致、不正 base64/空 blob 拒否
- known_hosts 行パース: 通常行、複数ホスト名、空行/コメント/マーカー除外、
  欠損フィールド・未知鍵種別・不正 base64 の拒否
- ハッシュ化ホスト名判定、管理エントリのエイリアス一致検索・別エイリアス
  非一致・重複エントリ時の先頭一致

### `nctl/tests/test_config.py`（追加 4 tests）
- `[ssh]` 省略時のデフォルト値とパス展開
- 上書き値とチルダ展開
- `keyscan_timeout_seconds` の境界値拒否（`0`, `121`）
- 未知キー拒否（`unknown`）

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
50 passed in 0.23s

$ uv run --project nctl pytest -q nctl/tests
767 passed, 1 warning in 5.81s
```

## 後続への申し送り

- Step 2（`nctl ssh enroll`）は本ステップの `ssh_trust.py` ヘルパーを
  そのまま再利用する想定。まだ known_hosts ファイルへの実 I/O・ロック・
  サブプロセス呼び出しは実装していない。
- `SshConfig` は `Config` に接続済みだが、`hosts_intent.py` /
  `production/composer.py` はまだこの設定を消費しない（Step 3/4 で対応）。
