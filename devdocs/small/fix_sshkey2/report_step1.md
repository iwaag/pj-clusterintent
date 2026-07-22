# Report — Step 1: correct SSH identity helpers and configuration paths

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了**（focused: 61 pass / full suite: 830 pass）

## 目的（plan.md Step 1）

`derive_lookup_name(alias, port)` が非デフォルトポートで `[alias]:port` を生成し、
実際の OpenSSH 接続（`HostKeyAlias` 設定時はポートを一切見ない）と食い違っていた
bug #1 を修正する。管理ストア専用のルックアップと、legacy 昇格専用のルックアップを
別 API に分離し、`[ssh]` の相対パスを設定ファイル基準で解決する（bug #5）。

## 変更内容

### 1. `nctl_core/ssh_trust.py`
- `derive_lookup_name(alias, port)` を削除。
- `managed_lookup_name(alias)` を追加: 常に素のエイリアスを返す（port 引数なし）。
  管理ストアは `ansible_port` に一切依存しない。
- `legacy_lookup_name(effective_host, effective_port, host_key_alias)` を追加:
  effective `HostKeyAlias` があればそれをそのまま（ポート付与なし）、なければ
  port 22 は素のホスト名、それ以外は `[host]:port`（portable OpenSSH の
  `get_hostfile_hostname_ipaddr()` と同じ規約）。
- `EffectiveSshConfig` / `parse_effective_ssh_config(output)` を追加: `ssh -G` の
  出力から `hostname` / `port` / `hostkeyalias` / `userknownhostsfile`（複数可）を
  純粋にパースする。まだ `ssh_enroll.py` の実プローブには接続していない
  （Step 2 で `--from-known-hosts` の port-aware 化に使用予定）。

### 2. `nctl_core/config.py`
- `resolve_local_path(path, config_dir)` を追加（`~` 展開 → 絶対パスはそのまま →
  相対パスは `config_dir` 基準で解決、の3規則）。
- `SshConfig.resolved_known_hosts_file()` / `resolved_lock_path()` に
  `config_dir: Path` 引数を追加（`AnsibleConfig` の既存パターンに合わせた）。
- `Config.resolved_ssh_known_hosts_file()` / `resolved_ssh_lock_path()` を追加
  （`self.source_path.parent` を渡す唯一の呼び出し窓口）。全呼び出し元
  （`observation.py`, `hosts_intent_render.py`, `production_render.py`,
  `ssh_enroll.py`, `reconcile/ssh_preflight.py`）をこれに切り替え。
- `Config.load()` が `find_config()` の戻り値を `.resolve()` するようにし、
  `source_path` が常に絶対パスになることを保証（cwd 非依存の前提を成立させる）。

### 3. `nctl_core/reconcile/ssh_preflight.py`
- `_resolve_alias_and_lookup_name()` から `override.ansible_port` に基づく
  lookup_name 計算を削除し、`managed_lookup_name(alias)` を使用。管理ストアの
  enrollment チェック（`check_ssh_enrollment` / `verify_offered_keys` 双方が
  内部で呼ぶ）が非デフォルトポートのノードで `[alias]:port` を探しに行く
  bug を修正。

### 4. `nctl_core/ssh_enroll.py`（コンパイル整合のための最小限の追随）
- `derive_lookup_name(alias, port)` の呼び出しを `managed_lookup_name(alias)` に
  置換。管理ストアの書き込み/読み出しキーが常に素のエイリアスになる
  （これは同時に Step 2 の要件の一部を先取りして満たす）。
- `--from-known-hosts` の legacy 検索（`find_legacy_trusted_keys` /
  `SshProbeRunner.known_hosts_files_for`）はまだ port なしの `ssh -G host` の
  ままで、Step 2 で `parse_effective_ssh_config` / `legacy_lookup_name` に
  接続する。

### 5. `example.nctl.toml`
- `[ssh]` セクションのコメントに相対パス解決規則（設定ファイル基準、cwd
  非依存）を追記。

## テスト変更

### `nctl/tests/test_ssh_trust.py`
- `derive_lookup_name` 系3テストを削除。
- 追加: `managed_lookup_name`（素のエイリアス、空文字拒否）、
  `legacy_lookup_name`（port 22/非デフォルト、effective HostKeyAlias 優先、
  空ホスト・不正 port 拒否）、`parse_effective_ssh_config`（全フィールド抽出、
  HostKeyAlias 省略時のデフォルト、空行/不正行の無視）で計17テスト追加。

### `nctl/tests/test_config.py`
- `cfg.ssh.resolved_known_hosts_file()` の呼び出しを
  `cfg.resolved_ssh_known_hosts_file()` に更新。
- 追加: 相対パスが設定ファイルディレクトリ基準で解決されること（cwd を変えても
  変わらない）、絶対パスがそのまま保たれること、スペース入りパス、
  `Config.source_path` が相対 `--config` 指定でも絶対パスになること。

### `nctl/tests/test_ssh_enroll.py` / `test_ssh_preflight.py`
- `cfg.ssh.resolved_known_hosts_file()` 呼び出しを更新。
- 非デフォルトポートのテスト2件を、旧・誤った期待値（`[alias]:2222` を
  ブラケット付きで書き込む）から、修正後の正しい期待値（常に素のエイリアス）
  に書き換え。

### `nctl/tests/test_hosts_intent_render.py`
- フェイク `Config` の `ssh=SimpleNamespace(resolved_known_hosts_file=...)` を
  `resolved_ssh_known_hosts_file=...`（トップレベル属性）に更新。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
61 passed in 0.08s

$ uv run --project nctl pytest -q nctl/tests
830 passed, 1 warning in 5.50s
```

Lint/型チェック: `nctl/pyproject.toml` の `[dependency-groups] dev` に
ruff/mypy 等は含まれておらず、プロジェクト依存としてインストールされていない
ため未実行（Step 5 でまとめて記録）。

## Step 1 exit criteria チェック

- [x] 管理ストアの生成・ルックアップコードが `[nctl-node-...]:port` を
  生成しない（`ssh_enroll.py` の書き込み経路、`ssh_preflight.py` の照会経路
  ともに `managed_lookup_name` 経由）。
- [x] 旧・引数なし SSH パスリゾルバの呼び出しが残っていない
  （`grep -rn "cfg\.ssh\.resolved_known_hosts_file()\|cfg\.ssh\.resolved_lock_path()"`
  は src/ に0件）。
- [x] focused テスト全通過。

## 後続への申し送り

- Step 2 では `ssh_enroll.py` の `--from-known-hosts` を
  `parse_effective_ssh_config` / `legacy_lookup_name` に接続し、port-aware な
  legacy 昇格検索に直す。あわせて `SshProbeRunner.known_hosts_files_for`
  （host のみ）を `effective_config`（host, port）に置き換える。
- Step 2 では旧・誤った `[alias]:port` エントリの明示的な obsolete 削除
  （再検証済み enrollment 後のみ）も実装する。
