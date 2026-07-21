# Report — Step 6: operator documentation

実施日: 2026-07-22
対象: `nctl`, `ansible_agdev` (submodules)
ステータス: **完了**（ドキュメントのみ、テストへの影響なし: full suite 819 pass 維持）

## 目的（plan.md Step 6）

`nctl/README.md`、`ansible_agdev/README.md`、`ansible_agdev/README_ADMIN.md` に
以下のライフサイクルを記載する:

```text
discover by mDNS
  -> verify fingerprint / promote existing trusted .local key
  -> nctl ssh enroll
  -> observe and reconcile IPAM/DNS/DHCP
  -> connect by DNS/IP/Tailscale under the same HostKeyAlias
```

ハードウェア交換/鍵ローテーション（`--replace`）、管理ファイル紛失からの
復旧（再enrollのみ、`StrictHostKeyChecking=no` 等は禁止）、直接 Ansible
利用は生成済みインベントリ限定であることも文書化する。

`devdocs/big/braindump/p3/memo.py` の更新は plan.md の指示どおり
**ライブ検証後に行う**ため、本 Step ではまだ変更していない。

## 変更内容

### 1. `nctl/README.md`
- 「SSH trust configuration」節に以下のサブセクションを追加:
  - **Lifecycle**: 上記のライフサイクル図と各段階の説明
    （`--from-known-hosts` と `--fingerprint` の使い分け、enroll 後は
    `.local`/`.home.arpa`/IP/Tailscale のどれでも同じ `HostKeyAlias` で
    接続すること）。
  - **Hardware replacement and key rotation**: 同じ DesiredNode スロットに
    別ハードウェアを割り当てると意図的に鍵不一致になること、
    `--replace --fingerprint ... --yes` が3条件すべて揃って初めて
    置換できること。
  - **Recovering from a lost or corrupted managed file**: 唯一の復旧手段は
    再 enroll であり、`StrictHostKeyChecking=no`/`accept-new`/未検証
    スキャンのコピーは代替にならないこと。
  - **Direct Ansible use**: 両インベントリが同じ閉じた厳格ホスト変数を
    持つため直接 `ansible`/`ansible-playbook` 実行も fail-closed になる
    こと、手書きインベントリは対象外であること
    （`nctl apply dnsmasq --inventory` の拒否と対応）。

### 2. `ansible_agdev/README_ADMIN.md`
- 既存の「SSH key setup」/「SSH key distribution」（クライアント認証鍵
  = Ansible が接続する側の鍵）の直後に「SSH host-key trust」節を新設。
  混同を避けるため、これがクライアント鍵ではなく**サーバー側の身元検証**
  （相手が本当にそのノードかを確認する側）であることを明記した上で、
  ライフサイクル図、enroll コマンド例、ハードウェア交換手順、
  管理ファイル紛失時の復旧、直接 Ansible 利用時の fail-closed 挙動を
  簡潔にまとめ、詳細は `nctl/README.md`/`nctl ssh enroll --help` を参照
  するよう誘導（重複記載を避ける）。

### 3. `ansible_agdev/README.md`
- 冒頭の「Initial SSH...setup is documented in README_ADMIN.md」という
  既存のポインタ文が SSH host-key trust もカバーする形になっている
  （README_ADMIN.md 側に新設したため、こちらは変更不要と判断）。

## 検証

ドキュメントのみの変更のため、コード・テストへの影響はなし。

```
$ uv run --project nctl pytest -q nctl/tests
819 passed, 1 warning in 5.31s
```

## 後続への申し送り

- `devdocs/big/braindump/p3/memo.py` の更新（open handoff を完了レポートへの
  ポインタに置き換え、元のインシデント事実は保存）は、ライブ Phase 3
  replay（`agdnsmasq` に対する `nctl ssh enroll` → 観測 → reconcile の
  実地検証）の完了後に行う。
- ライブ検証時のコマンド・operation ID・フィンガープリント（SHA-256 のみ）・
  結果は `devdocs/small/fix_sshkey/report_verification.md` に記録する
  （plan.md の Verification セクションの指示どおり）。
