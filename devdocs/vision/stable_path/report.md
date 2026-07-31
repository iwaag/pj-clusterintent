# Agent Workdir Resolution 修正報告

## 結論

`nctl agent` の workdir は、ノード個別の設定ではなく OS ごとの共通設定から解決するよう変更した。実現済みノードでは nodeutils が Nautobot に記録した Actual State の `observed_system` を優先し、初回観測前だけ Desired State の `declared_host_os` を bootstrap 用フォールバックとして使う。

これにより、Desired State の OS 宣言が実機と不一致でも、既に観測済みであれば実機 OS に対応する workdir が選ばれる。ノードを追加するたびに `nctl.toml` へ個別パスを追記する必要はない。

## 解決規則

`nctl agent status`、`attach`、`sessions`、`run`、`send`、`abort` が共通で使う target 解決は、次の規則になった。

1. `DesiredNode.realized_device_id` で対応する Actual Device を取得する。
2. nodeutils の `observed_system` が `Linux` なら `[agent].linux_workdir`、`Darwin` なら `[agent].macos_workdir` を使う。
3. Actual OS が未取得または未対応の場合だけ `declared_host_os` を同じ OS マップで解決する。
4. どちらからも Linux/Darwin を解決できなければ、構造化された `agent_workdir_unresolved` を返す。

`~` は OpenCode の HTTP API に渡す directory パラメータであり、リモートシェルによる展開を保証できない。そのため今回の範囲では導入せず、OS ごとの絶対パスを明示する方式を維持した。

## 変更内容

- `nctl/src/nctl_core/agent.py`
  - Actual snapshot を Desired snapshot とともに取得するようにした。
  - `observed_system` / `declared_host_os` を OS ごとの workdir に変換する共通 helper を追加した。
  - `workdir_by_slug` の参照を削除した。
- `nctl/src/nctl_core/config.py`
  - `[agent].workdir_by_slug` を設定スキーマから削除した。
- `nctl/example.nctl.toml`
  - 個別ノード map を削除し、Actual OS 優先・宣言値フォールバックの説明を追加した。
- ルートの ignored `nctl.toml`
  - 冗長だった `agstudio` / `agpc` の個別設定を削除した。OS ごとの `macos_workdir` と `linux_workdir` のみが残る。
- `devdocs/vision/node_agent/p3/report.md`
  - 現行の OS-wide 設定契約に説明を更新した。

## テスト

`nctl` サブプロジェクトで `uv run pytest` を実行し、**1036 passed** を確認した。

追加した回帰テストは以下を検証する。

- `declared_host_os=linux` でも Actual の `observed_system=Darwin` があれば macOS workdir を使う。
- Actual OS がまだ存在しない初回ノードでは `declared_host_os=macos` から macOS workdir を使う。

ワークスペース root での一括 pytest は、今回と無関係な nauto/nodeutils の依存関係不足および同名テストの収集衝突で collection 時に停止したため、対象プロジェクトの完全スイートを検証対象とした。
