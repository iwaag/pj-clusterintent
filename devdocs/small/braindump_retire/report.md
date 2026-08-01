# Braindump `complete` コマンド実装報告

`opinion.md` のレビューを踏まえ、提言Aを精緻化した案（ダミー行を作らない `complete` コマンド）を実装した。plan.md は作成せず、この報告のみ残す。

## 実装内容

### nintent（サーバ側）

- `models.py`: `BrainDumpDocument` に `STATUS_COMPLETED = "completed"` と `completion_reason`（`TextField`, blank許容）を追加。
- `migrations/0026_braindumpdocument_completed_status.py`: 上記フィールド追加のマイグレーション。ランタイムゲートで `makemigrations --check` が "No changes detected" を確認済み。
- `api/serializers.py`: `BrainDumpCompleteSerializer`（`reason` 必須・空白のみ拒否）を追加。`BrainDumpDocumentSerializer` に読み取り専用の `completion_reason` を追加。
- `api/views.py`:
  - `BrainDumpDocumentViewSet.complete`（`POST /braindumps/{id}/complete/`）を追加。`active` の対象行のみ許可し、`reason` を記録して `completed` へ直接遷移。新しい Braindump 行は作らない。対象が `active` でない場合は `409 Conflict`（`purge` と同じ流儀）。
  - `BraindumpPurgeView` の適格判定を `status in (superseded, completed)` に拡張。
- `tests/test_braindump.py`: `complete` の正常系・非active拒否・空白reason拒否、および `purge` が `completed` を受理するケースを追加。

### nctl（クライアント側）

- `sources/braindump.py`: GraphQL query に `completion_reason` を追加、`BraindumpStatus` に `"completed"` を追加。
- `braindump_client.py` / `braindump_errors.py`: `complete_braindump()` REST呼び出しと `braindump_complete_ineligible` / `braindump_complete_rejected` / `braindump_complete_confirmation_mismatch` エラーを追加（`purge` の命名規約に合わせた）。
- `braindump.py`: `complete_braindump()` ドメイン関数（`--reason` 必須検証 → REST POST → GraphQL再フェッチで `status=="completed"` かつ `completion_reason` 一致を確認、不一致ならfail-closed）。`BrainDumpRecord`/`BraindumpCompleteData` に `completion_reason` を追加。`list_braindumps` は既存の `status=="active"` フィルタのままで `completed` も自動的に除外される（`--include-superseded` で両方とも含まれる）。
- `braindump_render.py`: `build_braindump_complete` / `render_braindump_complete_text`、`nctl.braindump.complete.v1` envelope。`show` テキスト表示に `completion_reason`（completedの場合のみ）を追加。
- `cli/main.py`: `nctl braindump complete ID --reason TEXT [--yes]` を新設。`review-delete` と同じ `_confirm_destructive` ゲート（`--json` は `--yes` 必須、人間向けは確認プロンプト）。`braindump_complete_ineligible` を usage exit コードに追加。
- `README.md`: braindumpセクションのコマンド一覧・`list`/`purge`の説明を更新。

## 決定した論点（レビュー時に指摘した曖昧さの解消）

- `completed`/`archived` の両論併記はやめ、**`completed` 一本**に決定（意味の重複を避けるため）。
- `purge` 可否は明確化：`completed` になった行は `superseded` と同様に purge 対象。履歴として残すか物理削除するかは、既存の `purge` の narrow-exception 位置づけをそのまま踏襲（ユーザーが明示的に `purge --yes` した時だけ消える）。
- 破壊的操作の唯一の脱出ハッチは既存の `--yes` 一本のみ。`--force` のような第二フラグは追加していない。

## テスト結果

- `nintent`: Django-free suite `python3 -m unittest discover -s nautobot_intent_catalog/tests` → 129 tests, OK (skipped=10, 既存想定通り)。
- `nintent`: Nautobotランタイムゲート `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb`（App全体、exact-local-source）→ **210 tests, OK**。`makemigrations --check --dry-run` は "No changes detected"。
- `nctl`: `uv run pytest -q --durations=20`（全体）→ **1105 tests, OK**。

## 未実施・申し送り

- **コミットはしていない**（実行のみの依頼だったため）。差分は `nintent/`（5ファイル、うち1つ新規migration）と `nctl/`（10ファイル）に留まっている。
- nintentは GitHub 経由インストール構成のため、この変更を実クラスタの Nautobot に反映するには、ユーザーによる push → `docker compose build`（`--no-cache` 推奨）→ 再起動が別途必要（ローカルのランタイムゲートは exact-local-source を直接テストしているため、この点は未検証のまま）。
- `devdocs/small/braindump_retire/opinion.md` 自体は更新していない（提言のレビューと実装決定はこの report.md に記録した）。
