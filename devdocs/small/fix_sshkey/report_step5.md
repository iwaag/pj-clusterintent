# Report — Step 5: reconcile/apply preflight and structured failure

実施日: 2026-07-22
対象: `nctl` (submodule)
ステータス: **完了**（focused: 117 pass / full suite: 819 pass）

## 目的（plan.md Step 5）

`nctl reconcile --yes` が observation/Nautobot Jobs/inventory 書き込み/
playbook 実行の前に、SSH を必要とするアクションの対象ノードが管理
known_hosts に enroll 済みであることを確認し、未 enroll なら書き込み前に
ラウンド全体を `ssh_host_key_unenrolled` で止める。加えて、既に enroll
済みでも「現在提示されている鍵」が管理鍵と一致するかをスキャンで確認し、
不一致/到達不能を書き込み前に検知する。ledger-only アクションは対象外。

## 経緯: 一度スコープ縮小 → ユーザー判断で完全自動化に変更

当初、production フェーズの実接続先解決ロジック（`composer.py` の
`resolve_connection_variables` 周辺）を preflight 側で複製するリスクを
理由に、ライブスキャン（`verify_offered_keys`）を `nctl reconcile --yes`
の自動フローには繋がず opt-in（`ssh_probe` 明示指定時のみ）として実装し、
一度コミットした。ユーザーに状況を説明したところ、「先に共通化してから
完全自動化する」方針を選択されたため、以下の共通化を行った上で完全自動化
した。

## 変更内容

### 1. `nctl_core/production/composer.py`
- `_compose_host` 内でインラインだった接続解決ロジックを
  `resolve_effective_route(node, effective) -> dict[str, Any]`
  として関数化・公開。`_compose_host` はこれを呼ぶだけになった
  （ロジック変更なし、コピー無し）。これにより
  `nctl_core.reconcile.ssh_preflight` が production の実際の接続先解決
  ロジックを**再利用**でき、別の・食い違う可能性のある実装を preflight
  側に持たずに済む。

### 2. `nctl_core/ssh_enroll.py`
- `_read_raw_lines` / `_entries_for_lookup_name` を `read_raw_lines` /
  `entries_for_lookup_name` に改名（非private化、`ssh_preflight.py` から
  再利用するため）。

### 3. `nctl_core/reconcile/ssh_preflight.py`（新規）
- `SSH_REQUIRING_RECONCILER_IDS = {"observe_node", "service_profile",
  "dnsmasq_config"}`。`link_actual_node`/`reconcile_ipam` は実機に SSH
  接続しないため対象外。
- `ssh_required_host_slugs(plan, *, reconciler_ids=None)`: プラン中の
  SSH 必須アクションが触るノード slug 集合を返す。**重要な修正**:
  `service_profile`/`dnsmasq_config` アクションの `targets` はサービス
  自体（`kind="service"`）であり、実際のノード slug は
  `action.parameters["host_slugs"]` にしか入っていない
  （`reconcilers.plan_service_profile` 参照）。当初の実装は
  `target.kind == "node"` だけを見ていたため、これらのアクションの対象
  ホストを一切拾えていなかった（enrollment ゲートも素通りしていた）。
  `host_slugs` パラメータを優先して読む形に修正。
- `check_ssh_enrollment(cfg, host_slugs, snapshot)`: 読み取り専用。管理
  known_hosts に該当エイリアスのエントリがあるかだけを見る。
- `resolve_production_routes(source_snapshot, host_slugs, generated_at)`:
  `production.adapter.build_production_node_inputs` +
  `production.composer.try_resolve_operational_values` +
  `resolve_effective_route` を使い、production が実際に選ぶ
  `ansible_host` を得る。解決できないノードは黙って結果から除外される
  （エラーにしない — 呼び出し側が unreachable として扱う）。
- `verify_offered_keys(cfg, host_slugs, snapshot, probe, *,
  route_overrides=None)`: 既に enroll 済みのホストについて、
  `route_overrides` があればその接続先を、無ければ mDNS エンドポイントを
  スキャンし、管理鍵と比較する（`ready`/`mismatch`/`unreachable`）。
  スキャンは既存の信頼鍵との不一致しか証明できず、新しい鍵を承認する
  ことは絶対にない。

### 4. `nctl_core/reconcile/executor.py`
- `ReconcileData.ssh_preflight: list[dict]` を追加（drift/action 分類には
  一切影響しない、controller-local な付随情報）。
- `run_reconcile(..., ssh_probe: SshProbeRunner | None = None)`:
  省略時は `default_ssh_probe_runner()`（実 `ssh-keyscan`）を使用 —
  ライブスキャンは既定で有効。
- `_run_plan_only`（`--yes` 無し）: enrollment チェックのみを
  `data.ssh_preflight` に載せる。ブロックしない（zero-write のまま、
  スキャンも行わない）。
- `_run_apply` のラウンド先頭（プラン構築直後・アクション実行前）:
  1. `check_ssh_enrollment` で全 SSH 必須ホストの enroll 状態を確認。
     未 enroll があれば `ssh_host_key_unenrolled` でラウンド全体を停止
     （observation/Job/inventory 書き込み/playbook を一切呼ばない）。
  2. `observe_node` 対象だけを mDNS 経由で `verify_offered_keys` により
     スキャン。不一致/到達不能があれば `ssh_host_key_mismatch`/
     `ssh_host_key_unreachable` でラウンド全体を停止。
- `_execute_round`: `_regenerate_production_inventory` の直後・
  `service_actions`（`service_profile`/`dnsmasq_config`）実行前に、
  `resolve_production_routes` で実際の接続先を解決し
  `verify_offered_keys(..., route_overrides=routes)` で再スキャン。
  不一致/到達不能があれば `_SshPostRegenScanFailed` を送出し、
  `_run_apply` 側でラウンド全体を失敗として停止する
  （IPAM で新しく作られたルートは regen 前には検証できない、という
  plan.md の指摘どおり、regen 後・最初の production playbook 実行前に
  再検証する）。
- `render_reconcile_text`: `ssh_preflight: ready=[...] unenrolled=[...]`
  のようなサマリ行を追加。

### 5. `nctl_core/dnsmasq_apply.py`
- `--inventory` で任意のインベントリを渡した場合のみ、
  `dnsmasq_server` グループの各ターゲットホストが `_meta.hostvars` に
  有効な `nintent_desired_node_id`（UUID として検証）と
  `nctl_ssh_host_key_alias` を持つことを要求。欠落・不正なら
  `dnsmasq_inventory_untrusted_host` で拒否。設定済みの既定インベントリ
  はこのガード対象外。

### 6. `nctl_core/observation.py`
- `run_observation()` に defense-in-depth のナローガード
  （enrollment チェックのみ、スキャンはしない）を追加。reconcile 側の
  ゲートを経由しない直接呼び出しでも安全。

### 7. README.md
- 「SSH trust preflight」段落を追加し、enrollment チェックとライブ
  スキャン（bootstrap/mDNS 経由・production regen 後の実ルート経由）の
  両方が既定で自動的に走ることを明記。

## テスト追加

- `tests/test_ssh_preflight.py`（新規、15 tests）: `ssh_required_host_slugs`
  の `host_slugs` パラメータ読み取り（service_profile/dnsmasq_config の
  正しい対象抽出）とフィルタ挙動、`check_ssh_enrollment` の
  ready/unenrolled/unknown_host、`verify_offered_keys` の
  ready/mismatch/unreachable/未 enroll 時スキップ/`route_overrides` 経由
  でのスキャン、`resolve_production_routes` が composer と同じ接続先を
  返すこと・解決不能ノードは結果から除外されること。
- `tests/test_reconcile_executor.py`: 全テスト共通の autouse fixture
  `_fake_ssh_probe` を追加（既定で FIXTURE_KEY_BLOB を提示する偽
  `ssh-keyscan`。実ネットワークに出ない）。`_snapshot()` を全ノードに
  自動で mDNS エンドポイントを付与するよう拡張。新規6テスト:
  `--yes` が未 enroll ホストでラウンド全アクション実行前に停止すること、
  鍵不一致で observation 実行前に停止すること、production regen 後の
  鍵不一致で service_profile playbook 実行前に停止すること、dry plan は
  `ssh_preflight` を報告するがブロックしないこと、ledger-only プランは
  未 enroll ホストがあってもブロックされないこと。
- `tests/test_dnsmasq_apply.py`: `_inventory_payload()` に有効な SSH
  trust vars を追加。新規2テスト: trust vars 欠落ホストの拒否、既定
  インベントリはガード対象外であること。
- `tests/test_observation.py`: `_config()` を全フィクスチャホスト
  事前 enroll に変更、新規1テスト: 未 enroll ホストで Ansible 呼び出し
  ゼロのまま `ValueError` になること。

## 検証

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_preflight.py nctl/tests/test_reconcile_executor.py \
    nctl/tests/test_production_composer.py nctl/tests/test_dnsmasq_apply.py nctl/tests/test_observation.py
117 passed in 0.39s

$ uv run --project nctl pytest -q nctl/tests
819 passed, 1 warning in 5.64s
```

## 後続への申し送り

- `resolve_production_routes` は解決できないノードを黙って結果から除外し
  `verify_offered_keys` 側で `unreachable`（`no_resolvable_route`）として
  扱う。実運用では bootstrap-eligible なノードは通常 mDNS フォールバック
  があるため致命的ではないが、production 側の facts が古い/欠落している
  状態が続くと regen 後スキャンが恒常的に `unreachable` を返す可能性が
  ある。これは正しい fail-closed 挙動だが、運用上の誤検知に見えないよう
  Step 6 のドキュメントで明示すること。
- ライブ Phase 3 replay（`agdnsmasq`）で、この完全自動化されたゲートが
  実際の agdnsmasq ノードに対して `ready` を返すことを確認すること
  （enroll 済みかつ mDNS/production 経路のどちらでも正しい鍵を提示する
  ことの実地検証）。
