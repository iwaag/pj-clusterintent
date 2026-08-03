# Report — Step 2: Writes (`create`, namespace writes)

実施日: 2026-08-04
対象: `nctl`（ローカル source）
ステータス: **完了**

## 実施内容

### client / errors
- `workflow_episode_client.py` に `create_workflow_episode`（`POST /`、非2xxで
  `workflow_episode_create_rejected_error`）と `write_workflow_episode_namespace`
  （`POST /<id>/<namespace>/`、404を`workflow_episode_not_found_error`、非2xxを
  `workflow_episode_write_rejected_error`）を追加。両errorとも400は
  `workflow_episode_validation_failed` にマップ（Braindumpの`write_error()`と同型）。

### core（`workflow_episode.py`）
- 入力解決を一本化: `resolve_json_object_input(field_name, literal, file)`
  （リテラルJSON文字列 or `--file`のどちらか一方必須、JSONパース＋dict型チェック）と、
  neither可の`resolve_optional_json_object_input`（`create`のraw_data省略に対応）。
  Braindumpの`resolve_text_input`と同じ「exactly one of」規約だが、JSON object前提な点が異なる
  ため専用関数として実装（テキストとJSONを同じ関数で扱うと型チェックが濁るため）。
- `create_episode(client, *, title, raw_data: dict|None)` — titleの非空チェック→POST→
  レスポンスをそのままrecord化。confirmation refetchは行わない（plan.mdの「trusting the 2xx
  response body is acceptable in this experimental environment」を採用）。
- `write_namespace(client, episode_id, namespace, payload: dict)` — id検証→POST→record化。

### CLI設計判断
plan.mdの「pick one style and keep it consistent with the namespace-write commands」を受け、
`--report`/`--references`個別オプションは採用せず、**raw_data全体を一つのJSONオブジェクトとして
渡す一本の様式**に統一した:
- `nctl workflow-episode create --title T [--raw-data '{"report": {...}, ...}' | --file doc.json]`
  （両方省略可＝raw_data未指定でPOST）
- `nctl workflow-episode write <id> <namespace> (--data '{...}' | --file ns.json)`
  （`namespace`は`report`/`assessment`/`references`/`resolution`の位置引数、Typer Enumで
  それ以外を利用不可に）

4namespace全部をStep 2で実装した（plan.mdの「if it costs nothing extra」に該当、
`_write_namespace`ビューが1関数で4アクションに共通のため実装コストが同一）。

### テスト
- `tests/test_workflow_episode.py`: 12 test追加（入力解決8、create4、write3 — 実数は下記結果参照）。
- `tests/test_cli_workflow_episode.py`: create/write のtext出力・オプション伝搬・エラー時exit code
  ・不正namespace（Typer Enumバリデーションで自動的にexit 2）を追加。

## テスト結果

```
uv run pytest -q tests/test_workflow_episode.py tests/test_cli_workflow_episode.py tests/test_cli_surface.py
→ 39 passed  (Step 1時点18 → +21)

uv run pytest -q --durations=10
→ 1186 passed  (Step 1時点1165 → +21、回帰なし)
```

## 後続への申し送り

- Step 3で`select`/`resolve`/`dismiss`のtransition commandsと409マッピング
  （`workflow_episode_transition_ineligible_error`、`workflow_episode_errors.py`にfactory済み）を追加。
- `report`/`references`のnamespace writeもすでに使用可能（`nctl workflow-episode write <id> report ...`
  等）。plan.md Step 4のsmokeシナリオでは`assessment`を使う想定だが、他namespaceも同じコマンドで到達可能。
