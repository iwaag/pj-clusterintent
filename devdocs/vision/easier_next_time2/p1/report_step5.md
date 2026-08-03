# Report — Step 5: scratch Nautobotへのデプロイ

実施日: 2026-08-04
対象: `devenv/nautobot`（scratch Nautobotコンテナ）
ステータス: **完了**

## 目的（p1/plan.md Step 5）

`nintent` の3コミット（Step 1〜3）をpushし、scratch Nautobotコンテナを `--no-cache` で
再ビルド・再起動し、`nautobot-server migrate` を適用する。

## 実施内容

1. **push**（ユーザー承認取得済み）: `git -C nintent push origin main`
   ```
   To https://github.com/iwaag/nintent.git
      37e307b..36e74a0  main -> main
   ```

2. **ビルド**: `docker compose --env-file ../.env build --no-cache`
   ビルドログで解決済みコミットを確認:
   ```
   Resolved https://github.com/iwaag/nintent.git to commit 36e74a070a0807aa4a539789a28678c87a328ebb
   ```
   これは直前にpushした `nintent` HEAD（`36e74a0`）と一致。3イメージ
   （`nautobot-nautobot`, `nautobot-nautobot-worker`, `nautobot-nautobot-scheduler`）とも
   Built。

3. **再起動**: `docker compose --env-file ../.env up -d` で3コンテナを再作成・起動、
   `nautobot-nautobot-1` はHealthyに到達。

4. **マイグレーション**: `docker exec nautobot-nautobot-1 nautobot-server migrate
   nautobot_intent_catalog`。`nautobot-server showmigrations nautobot_intent_catalog` で
   `[X] 0029_workflowepisode` を確認済み（0001〜0029まですべて適用済み）。

## 後続への申し送り

- Step 6でAPI疎通・GUI疎通のライブ検証を行う。
