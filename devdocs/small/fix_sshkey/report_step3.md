# Report — Step 3: bootstrap inventory uses the stable alias

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了**（focused: 41 pass / full suite: 793 pass）

## 目的（plan.md Step 3）

`export_hosts_intent()` が生成する `ssh_hosts` の各ホストに、DesiredNode
UUID から導出した `nctl_ssh_host_key_alias` と `ansible_ssh_common_args` を
付与する。スキーマを `4.0` → `5.0` に bump し、operation-scoped
`events/<operation>/bootstrap/hosts_intent.yml` を含む全経路（永続化された
生成インベントリだけでなく）でこの値を反映させる。

## 変更内容

### 1. `nctl_core/hosts_intent.py`
- `HOSTS_INTENT_SCHEMA_VERSION` を `"5.0"` に bump し、モジュール docstring
  に schema 5.0 の変更点を追記。
- `export_hosts_intent()` に `ssh_known_hosts_file: str | None = None`
  （キーワード専用）を追加。実呼び出し元（`hosts_intent_render.py` /
  `observation.py`）は必ず実値を渡す前提とし、省略はテスト専用。
- `_host_vars()` が `ssh_known_hosts_file` を受け取り、値がある場合のみ
  `derive_host_key_alias(node.id)` でエイリアスを導出し
  `nctl_ssh_host_key_alias` / `ansible_ssh_common_args`
  （`ssh_trust.build_ansible_ssh_common_args` を1箇所で呼ぶ）を host_vars に
  追加。値が無い場合は従来どおり2キーとも出力しない。

### 2. `nctl_core/hosts_intent_render.py` / `nctl_core/observation.py`
- 両呼び出し元で `ssh_known_hosts_file=str(cfg.ssh.resolved_known_hosts_file())`
  を渡すよう変更。`observation.py::run_observation()` はこの `export` を
  そのまま `events/<operation>/bootstrap/hosts_intent.yml` の描画にも使う
  ため、operation-scoped インベントリにも同じ vars が乗る。

### 3. `nctl_core/ssh_enroll.py`（Step 2 のバグ修正）
Step 3 の作業中に発見: 管理ファイルへの書き込みが常に素の `alias` を
エントリ名として使っており、非デフォルト port のとき OpenSSH の
`[alias]:port` ブラケット記法（Step 1 の `derive_lookup_name`）を無視して
いた。`_entries_for_alias`/`_lines_excluding_alias`/`_write_managed_file`
を `lookup_name` ベースに改名・修正し、`build_ssh_enroll` 内の呼び出しを
`lookup_name` に統一。回帰テスト
`test_non_default_port_writes_bracketed_lookup_name` を追加。

## テスト変更・追加

- `tests/test_hosts_intent.py`: `node()`/`endpoint()` ヘルパーに任意の
  `id`/`node_id` を追加し、schema バージョン文字列アサーションを `5.0` に
  更新。新規4テスト: `ssh_known_hosts_file` 省略時に SSH host vars が
  出ないこと、node ID からの決定的導出とエンドポイント名変更（`.local` →
  `.home.arpa`）後もエイリアス不変であること、異なる node ID は異なる
  エイリアスになること、`ansible_ssh_common_args` に設定済みパスと厳格
  オプション全部が含まれること。
- `tests/test_hosts_intent_render.py`: `_fake_config()` に `ssh` 名前空間を
  追加、`_snapshot()` の node id を有効な UUID に変更、実際の
  `build_hosts_intent_render()` 呼び出しテストで schema `5.0` と SSH host
  vars（alias/`ansible_ssh_common_args`/known_hosts パス）を検証するよう拡張。
- `tests/test_observation.py`: `_snapshot()` の node id を
  `uuid.uuid5` ベースの決定的 UUID に変更（旧 `node-<host>` 文字列は
  `derive_host_key_alias` の UUID 検証を通らないため）。関連する
  `DesiredServicePlacement.node_id` / `render_probe_hints` 呼び出しも追従。
- `tests/test_ssh_enroll.py`: 非デフォルト port の書き込みがブラケット
  記法 `[alias]:port` を使うことを検証する回帰テストを追加。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_hosts_intent.py nctl/tests/test_hosts_intent_render.py
25 passed in 0.23s

$ uv run --project nctl pytest -q nctl/tests/test_observation.py nctl/tests/test_cli_render_hosts_intent.py
11 passed in 0.19s

$ uv run --project nctl pytest -q nctl/tests
793 passed, 1 warning in 5.16s
```

## 後続への申し送り

- `export_hosts_intent()` の `ssh_known_hosts_file` はデフォルト `None`
  （テスト専用の省略）。Step 4 の production 側は plan どおり必須の閉じた
  変数セットとして実装し、bootstrap 側とバイト同一のエイリアス/
  `ansible_ssh_common_args` になることを回帰テストで確認すること。
- Step 3 では `ansible_port` を考慮していない（bootstrap は常に既定
  port 22 で `HostKeyAlias`＝素のエイリアスを使う設計で問題ない。
  `[alias]:port` のブラケット記法が必要になるのは enroll が書き込む
  known_hosts エントリ名だけで、`ansible_ssh_common_args` 自体は port に
  依存しない——今回の Step 2 バグ修正で確認済み）。
