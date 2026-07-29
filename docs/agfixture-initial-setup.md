# agfixture 初期設定マニュアル

> **目的**: Proxmox LXC コンテナ `agfixture` (VMID 109) の初期アクセス設定手順を、人間が具体的に実行できるように説明する

---

## 1. agfixture 概要

| 項目 | 値 |
|---|---|
| **ノードスラッグ** | `agfixture` |
| **ノードタイプ** | `service_host` (virtual_machine) |
| **Lifecycle** | `approved` |
| **Proxmox クラスタ** | `aghub-proxmox` (制御ノード: `aghub`) |
| **VMID** | `109` |
| **ゲストタイプ** | LXC コンテナ |
| **テンプレート** | `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst` |
| **リソース** | 1 vCPU, 512 MiB RAM, 8 GiB root disk (`local-lvm`) |
| **ブリッジ** | `vmbr0` |
| **MAC アドレス** | `bc:24:11:00:01:09` |
| **IP アドレス** | `192.168.0.9` (static) |
| **DNS 名** | `agfixture.home.arpa` |
| **mDNS 名** | `agfixture.local` |
| **generate_dnsmasq** | `false` |

---

## 2. 現状 (drift 結果より)

- Proxmox 上に LXC コンテナは**作成済み・起動済み**
- Nautobot 上に VirtualMachine として登録済み (VM ID: `3a6aa5b1-f128-4d23-82f7-9c97acff3a68`)
- **ただし**: `waiting_for_manual_initial_access` ステータス
  - ゲストのネットワーク設定、コンソールユーザー/SSH キー設定、SSH 登録、初回 nodeutils 収集が**未実施**
  - この状態では production inventory からも除外されている (意図的な安全停止)

---

## 3. 初期設定手順

### 手順 1: Proxmox Web UI 経由でコンソールにアクセス

1. `aghub` の Proxmox VE Web UI (通常 `https://<aghub-ip>:8006`) にログイン
2. `Containers` タブで VMID `109` (`agfixture`) を選択
3. **Shell** または **Console** ボタンをクリックしてターミナルコンソールを開く

### 手順 2: 初回ユーザー設定

Ubuntu LXC テンプレート初回起動時に以下の設定を行う:

1. **root パスワードの設定**
   ```bash
   passwd
   ```

2. **必要に応じてユーザー追加** (任意)
   ```bash
   adduser <username>
   usermod -aG sudo <username>
   ```

### 手順 3: ネットワーク設定

静的 IP `192.168.0.9` でネットワークを設定:

```bash
# /etc/netplan/01-netconfig.yaml 等の形式で設定例:
network:
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.0.9/24]
      routes: [{ to: 0.0.0.0/0, via: 192.168.0.1 }]
      nameservers:
        addresses: [192.168.0.2]
  version: 2
```

適用:
```bash
netplan apply
```

確認:
```bash
ip addr show eth0
ping 8.8.8.8
```

### 手順 4: SSH 設定

1. **SSH サーバーインストール** (未インストールの場合)
   ```bash
   apt update && apt install -y openssh-server
   systemctl enable ssh
   systemctl start ssh
   ```

2. **SSH キーの設定**
   - 公開キーを `~/.ssh/authorized_keys` に追加
   - 使用される秘密キー: `~/.ssh/ansible_key` (ansible_agdev 用) または専用のユーザーキー

3. **SSH 設定確認**
   ```bash
   # /etc/ssh/sshd_config で以下を確認:
   # PermitRootLogin prohibit-password (または required-password)
   # PasswordAuthentication no (キー認証のみ)
   ```

### 手順 5: SSH 登録 (nctl 経由)

agfixture に SSH できたら、nctl からホストキーを登録:

```bash
cd /Users/eiji/projects/pj-clusterintent
uv run --project nctl nctl ssh enroll agfixture --from-known-hosts --yes
```

確認:
```bash
uv run --project nctl nctl status
```

### 手順 6: 初回 nodeutils 収集

agfixture 上で nodeutils を実行し、システム情報を収集:

1. **agfixture 上で nodeutils をセットアップ**
   ```bash
   # nodeutils リポジトリからスクリプトを取得またはuv環境をセットアップ
   # 必要に応じて:
   cd /tmp
   git clone https://github.com/iwaag/nodeutils.git
   cd nodeutils
   uv sync
   ```

2. **インベントリ収集実行**
   ```bash
   uv run python nodeutils_collect.py --output /var/lib/nodeutils/
   ```

3. **収集結果が `/var/lib/nodeutils/` に出力されることを確認**

### 手順 7: Nautobot へのインジェスト

agfixture の収集結果を Nautobot に反映:

```bash
cd /Users/eiji/projects/pj-clusterintent
uv run --project nctl nctl reconcile agfixture --refresh-observation --yes
```

このコマンドは:
1. agfixture の nodeutils 収集結果を Nautobot にインジェスト
2. agfixture の drift を再計算
3. 問題がなければ `converged` 状態になる

確認:
```bash
uv run --project nctl nctl drift --host agfixture --json
```

---

## 4. 完了チェックリスト

- [ ] Proxmox コンソールにアクセス可能
- [ ] root パスワードが設定済み
- [ ] IP `192.168.0.9` でネットワークが動作
- [ ] SSH 接続が可能 (`ssh root@192.168.0.9`)
- [ ] `nctl ssh enroll` が成功
- [ ] nodeutils 収集結果が `/var/lib/nodeutils/` に出力
- [ ] `nctl reconcile agfixture` が `converged` を返す
- [ ] Nautobot UI (`http://localhost:8000`) で agfixture の情報が更新されている

---

## 5. トラブルシューティング

| 問題 | 対処 |
|---|---|
| `ssh: connect to host 192.168.0.9 port 22: Connection refused` | SSH サーバーが起動していない。コンソールから `systemctl start ssh` |
| `Permission denied (publickey)` | SSH キーが `authorized_keys` に登録されていない。コンソールから確認・追加 |
| `nctl reconcile` が `waiting_for_manual_initial_access` のまま | nodeutils 収集結果が Nautobot にインジェストされていない。`/var/lib/nodeutils/` の存在確認 |
| LXC コンテナが起動しない | Proxmox UI で `Stop` → `Start` を再実行。ログ (`/var/log/pveproxy/access.log`) 確認 |
| IP アドレスが割り当てられない | DHCP サーバー (`agdnsmasq`) が動作しているか確認。静的設定が反映されているか確認 |

---

## 6. 参考情報

- **Braindump**: "Confirmed wish: retain agfixture LXC VMID 109" (ID: `9cda91ef-9d86-4667-b61b-771a146f54b7`)
- **意図**: 廃棄可能な LXC ゲストを1台作成・保持する。Phase 5 では retain (保持) Disposition。
- **Proxmox クラスタ**: `aghub-proxmox` は `aghub` (192.168.0.10) 上の Proxmox VE
- **DNS**: `agfixture.home.arpa` / `agfixture.local` (dnsmasq 登録なし: `generate_dnsmasq: false`)

---

## 7. 関連ファイル

| ファイル | 説明 |
|---|---|
| `nauto/seed/intent_sources.yaml` | agfixture の desired state 定義 |
| `nauto/seed/home_cluster.yaml` | Nautobot 基本設定 (roles, tags, custom_fields) |
| `nctl/docs/usage_example.md` | nctl コマンド使用例 |
| `agentdocs/brainforge/README.md` | brainforge セッションマニュアル |
| `README.md` | プロジェクト概要 |