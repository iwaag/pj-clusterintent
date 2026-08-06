# manual_service — 完全手動管理サービスの位置付けと設計報告

日付: 2026-08-06
発端: brainforgeセッション 2026-08-05_61aa（swarmui / comfyui の drift 表示に関する相談）
関連Braindump: `agpcにおけるSwarmUI・ComfyUIの運用とサービス兼用方針（完全手動管理）`
（id: f8829d69-5921-481a-bba0-9e9a9d74bfbc、旧 a19cfa29 を supersede）

## 問題

`nctl drift` で swarmui / comfyui（ともに agpc 上の placement）が常態的に
`service_missing`（error, drifting）と表示される。しかしこの二つは Stability Matrix で
インストールされ、ユーザーが日常的に手動で ON/OFF するツールであり、OFF である
こと自体は予測の範囲内＝正常である。真に drift と呼ぶべきは「agpc から
インストール自体が消えて存在しなくなった」状態だけである。

### 根本原因: OFF と消滅が観測上区別できない

- agpc の nodeutils は swarmui/comfyui を **HTTPエンドポイントプローブのみ**で観測する
  （`nodeutils/service_endpoint_probes.py` — 7801/7821 に GET `/`）。
- プローブ成功 → `observed_services` に `state: active` のエントリ → converged。
- プローブ失敗 → **エントリ自体が作られない**（`nodeutils_collect.py`
  `normalize_observed_services` の http_probe 分岐は status None で continue）。
- nctl のドリフト評価器（`nctl/src/nctl_core/drift/service_placement.py`）は
  `service_missing`（エントリ無し）と `service_not_running`（エントリ有り・停止中）を
  既に区別できるが、観測データが「停止中でもインストールされている」事実を
  運べないため、OFF も消滅も `service_missing` に落ちる。

## 決定（ユーザー合意済み）

swarmui / comfyui は**完全手動管理サービス**と位置付ける。

1. **存在確認だけで converged**。プロセス状態・エンドポイント疎通は問わない。
2. **疎通確認・自動起動・自動インストール等の自動処理を一切行わない**。
   起動が必要なときはユーザーまたはエージェントが SSH / node-agent で明示的に行う
   （nctl コマンド化は不要）。
3. **エントリ消滅（インストールが消えた）だけが drift**（`service_missing`, error のまま）。
4. 管理区分は **service ではなく placement 単位**で持つ。

### placement 単位とした理由

- `DesiredService.management_mode` だと全 placement に一律波及し、「同じツールを
  サーバでは自動管理、ワークステーションでは手動」という将来構成（ollama が候補）を
  塞ぐ。
- 運用の仕方を表す欄（`deployment_profile`, `desired_state`,
  `config_schema_version`）は既に `DesiredServicePlacement` に集まっており、
  置き場所として一貫する。
- ドリフト評価の単位も placement（`evaluate_active_placement`）なので実装が素直。
- なお node 単位の既存 `actual_state_policy`（required/declared、
  `DesiredNodeOperationalConfig`）はノード全体の方針であり流用不可と確認した。

## 設計（未実装）

### nintent

- `DesiredServicePlacement.management_mode` を追加:
  `nctl_managed`（デフォルト）| `manual`。
- migration + batch スキーマ + API/GraphQL 露出。
- 反映には commit → push（ユーザー実施）→ コンテナ rebuild のサイクルが必要
  （ホットリロード無し）。

### nctl

- `evaluation_snapshot` で placement に `management_mode` を載せ、
  `evaluate_active_placement` で `manual` の場合:
  - observed エントリが存在すれば state 不問で gap 無し（converged）。
  - エントリ無しは従来どおり `service_missing`（error）。
- reconcile: `manual` placement にはアクションを計画しない。`service_missing` の
  classification は AUTOMATIC のままでも profile 側に action が無ければ plan 時に
  unsupported へ降格されるが、意味を明示するため manual placement では
  manual_review 扱いとするのが望ましい（再インストールは Stability Matrix での
  人間作業）。

### nodeutils

- `service_probe_hints` に汎用ヒント `install_path`（複数可）を追加し、
  パスが存在すれば `state: installed` のエントリを出す
  （blender の `host_tool: installed` ハードコード観測の汎用化）。
- swarmui / comfyui の HTTP エンドポイントプローブは廃止（疎通チェックを
  行わない方針のため）。エンドポイント情報は desired 側の定義に残るので
  他サービスからの参照には影響しない。
- agpc の probe hints 設定を更新し、Stability Matrix のパッケージディレクトリ
  （例: `StabilityMatrix/Packages/SwarmUI`, `.../ComfyUI`）を `install_path` に指定。
- superproject の nodeutils ピンコミット更新が必要。

### 運用ルール

- 手動管理サービスを provider とする binding は疎通確認なしで宣言する
  （OFF 時に consumer 側で binding gap が出るのを避ける）。

## 実装結果（2026-08-06 完了）

計画どおり全ステップを実施し、完了条件を満たした。

- コミット: nodeutils `47ad460`（install_path ヒント + テスト2件、45件全パス）、
  nintent `bc2cb64`（management_mode + migration 0030 + batch/table）、
  nctl `69808f8`（presence-only 評価 + ヒント生成 + snapshot/export 配線、
  1261テスト全パス）、ansible_agdev `adb57c2`（swarmui/comfyui に
  `install_path: ~/StabilityMatrix/Packages/...`）、superproject `ca8f537`（pin更新）。
- 実際のインストール場所は SSH で実測確認: `/home/eiji/StabilityMatrix/Packages/{SwarmUI,ComfyUI}`。
- Nautobot: nintent コミット SHA を build-arg にして rebuild、`build_info.json` で
  反映確認、migration 0030 適用済み。
- desired-state: 部分 upsert バッチ（update 2件のみを preview 確認後 `--yes`）で
  `swarmui-agpc` / `comfyui-agpc` の placement を `management_mode: manual` に設定。
- 観測リフレッシュ: `nctl reconcile agpc --refresh-observation --yes`
  （operation `01KZA93A0MJYB8STM5DZ77DNXC`）。新 nodeutils が両サービスを
  `state: installed, source: install_path` で観測。

完了確認: 両サービスとも OFF のまま `nctl drift` が **converged**（クラスタ全体
19 converged / 0 drifting / error 0）。エンドポイントプローブは probe hints から
消えたため疎通チェックは行われず、インストールが消えた場合のみ
`service_missing` が復活する。reconcile 上も observe_only プロファイルのため
actuation は一切計画されない（unsupported として明示される）。

起動が必要なときは SSH / node-agent で手動起動する（従来どおり、nctl コマンド化なし）。
