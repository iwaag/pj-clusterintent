# Report — Step 4: production inventory uses the identical alias

実施日: 2026-07-22
対象: `nctl`, `ansible_agdev` (submodules)
ステータス: **完了**（focused: 108 pass / full nctl suite: 796 pass）

## 目的（plan.md Step 4）

production インベントリの `ssh_hosts` にも、bootstrap と同じ2変数
（`nctl_ssh_host_key_alias` / `ansible_ssh_common_args`）を、同じ
DesiredNode UUID から導出して追加する。production インベントリスキーマを
`2.0` → `3.0` に bump し、`ansible_host` が `.local` → `.home.arpa`/IP/
Tailscale に変わってもエイリアス/trust 引数はバイト同一であることを回帰
テストで固定する。

## 変更内容

### 1. `nctl_core/production/contract.py`
- `PRODUCTION_INVENTORY_SCHEMA_VERSION` を `"2.0"` → `"3.0"` に bump し、
  モジュール docstring に fix_sshkey Step 4 の変更点を追記
  （`PRODUCTION_REPORT_SCHEMA_VERSION` は既存どおり独立して `"3.0"`）。
- 閉じたホスト変数集合 `_BASE_HOST_VARIABLES` に `nctl_ssh_host_key_alias` /
  `ansible_ssh_common_args` を追加。

### 2. `nctl_core/production/composer.py`
- `compose_production_inventory()` に
  `ssh_known_hosts_file: str | None = None`（キーワード専用）を追加し、
  `_compose_host()` に伝播。値がある場合のみ
  `derive_host_key_alias(node.id)` でエイリアスを導出し、
  `base_vars` に2変数を追加（bootstrap の `hosts_intent.py` と同じ
  `ssh_trust.build_ansible_ssh_common_args` を再利用、別実装を持たない）。
  省略時（`None`）は2変数とも出力せず、UUID 検証も走らない。
  - Step 3 と同じ理由で optional 設計を採用: `nctl_core.drift.comparators`
    の `production_policy` が drift 計算のためだけに内部で production
    インベントリを組み立てており、そこでは実 UUID を要求する必然性が
    無い（ディスクにレンダーされない内部計算のため）。実際の
    `nctl render production` 呼び出し元（`production_render.py`）だけが
    実値を渡す必須呼び出し元とした。
- `nctl_core/production_render.py`: `compose_production_inventory()` 呼び出しに
  `ssh_known_hosts_file=str(cfg.ssh.resolved_known_hosts_file())` を追加。

### 3. `ansible_agdev/docs/production_inventory_contract.md`
- `nintent_inventory_schema_version` の例示を `"3.0"` に更新し、新しい
  「SSH trust host variables (schema 3.0)」節を追加。エイリアス/
  `ansible_ssh_common_args` の形と、`nctl/README.md` の SSH trust
  configuration 節・`nctl ssh enroll --help` への誘導のみを記載（enrollment
  ライフサイクルの本格ドキュメント化は Step 6）。

## テスト変更・追加

- `tests/test_production_composer.py`:
  - `NodeInput.id` を `"node-<slug>"` 形式から `uuid.uuid5` ベースの決定的
    UUID（`_node_id()`）に変更（`derive_host_key_alias` の UUID 検証を
    満たすため）。中心の `compose()` ヘルパーおよび直接
    `compose_production_inventory(...)` を呼ぶ6箇所すべてに
    `ssh_known_hosts_file=SSH_KNOWN_HOSTS_FILE` を追加。
  - schema バージョンアサーションを `"3.0"` に更新。
  - 新規3テスト: `ssh_known_hosts_file` 省略時に SSH host vars が出ない
    こと、node ID からの導出と厳格オプション全部の確認、**production が
    IP を選択していても bootstrap（mDNS 選択）と同一ノードIDなら
    `nctl_ssh_host_key_alias`/`ansible_ssh_common_args` がバイト同一である
    こと**（plan.md 明示の回帰テスト）。
- `tests/test_production_contract.py`: `test_production_inventory_schema_is_closed`
  の `nintent_inventory_schema_version` フィクスチャを `"3.0"` に更新。
- `tests/test_production_render.py` / `tests/test_cli_render_production.py`:
  変更不要（実 `Config.load()` 経由で `cfg.ssh` のデフォルトが効くため）。
- `tests/test_drift_comparators.py` / `test_drift_engine.py` /
  `test_p4_mixed_node_orchestration.py`: 変更不要
  （`ssh_known_hosts_file` を optional にしたことで
  `production_policy` の内部合成が影響を受けない）。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_production_composer.py nctl/tests/test_production_contract.py \
    nctl/tests/test_production_render.py nctl/tests/test_cli_render_production.py \
    nctl/tests/test_drift_comparators.py nctl/tests/test_drift_engine.py nctl/tests/test_p4_mixed_node_orchestration.py
108 passed in 0.35s

$ uv run --project nctl pytest -q nctl/tests
796 passed, 1 warning in 5.49s
```

## 後続への申し送り

- `compose_production_inventory(ssh_known_hosts_file=None)` は
  「実運用は必須、drift 内部合成/一部テストは省略可」という非対称な契約に
  なった。Step 5 の reconcile preflight や、将来 production 合成を呼ぶ
  新しい経路を追加する際は、その経路がディスクへレンダーする
  ものかどうかで必須/省略を判断すること。
- `ansible_agdev/README.md` / `README_ADMIN.md` のライフサイクル本文更新は
  Step 6 に持ち越し。
