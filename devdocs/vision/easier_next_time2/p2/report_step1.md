# Report — Step 1: Transport + reads (`list` / `show`)

実施日: 2026-08-04
対象: `nctl`（ローカル source、`uv run --project nctl`）
ステータス: **完了**

## 実施内容

Braindumpモジュール群（`braindump_client.py`/`braindump.py`/`braindump_render.py`/
`braindump_errors.py`/`cli/main.py`）を精査したうえで、plan.mdのDesign hints
（「REST for both reads and writes」）に従い、GraphQLを経由せずREST一本で読み書きする
WorkflowEpisode版のモジュール群を新規作成した。

### 新規ファイル
- `nctl/src/nctl_core/workflow_episode_client.py` — REST transport。
  `list_workflow_episodes`（`GET /api/plugins/intent-catalog/workflow-episodes/`、
  `response.json()["results"]` を返す）、`get_workflow_episode`（`GET .../<id>/`、404を
  `workflow_episode_not_found_error` にマップ）の2関数のみ（writes/transitionsはStep 2-3で追加）。
- `nctl/src/nctl_core/workflow_episode_errors.py` — `WorkflowEpisodeError` 単一例外型
  + エラーコードのfactory関数群（今回使うのは `invalid_workflow_episode_id` /
  `workflow_episode_not_found`。write/transition系のfactoryはStep 2-3で使うため先に用意）。
- `nctl/src/nctl_core/workflow_episode.py` — `WorkflowEpisodeRecord` /
  `WorkflowEpisodeListItem` / `WorkflowEpisodeListData` / `WorkflowEpisodeShowData`
  （pydantic）、`validate_workflow_episode_id`、`list_episodes`（`statuses: frozenset[str] | None`
  でクライアント側フィルタ、`None`で全件）、`show_episode`。API側のfilterset（`status`は完全一致
  1値のみ）を使わず、Braindumpのstatusフィルタ同様クライアント側フィルタを採用（複数status
  同時指定・`--all`をシンプルに実現するため）。
- `nctl/src/nctl_core/workflow_episode_render.py` — envelope構築（`nctl.workflow_episode.list.v1`
  / `.show.v1`）と text render。`show`のtext renderはreport/assessment/references/resolutionの
  4セクションをJSON pretty-printで表示（raw_dataをそのままenvelopeに載せる、plan.mdの
  「show --json is the agent contract」どおり）。

### CLI配線（`cli/main.py`）
- `workflow_episode_app = typer.Typer(...)` を追加、`app.add_typer(..., name="workflow-episode")`。
- `nctl workflow-episode list [--status ... (repeatable)] [--all] [--json]`
  （デフォルト: `candidate` + `selected`、plan.md/roadmapのGUIデフォルトフィルタと一致）。
- `nctl workflow-episode show <id> [--json]`。
- `WORKFLOW_EPISODE_USAGE_CODES` + `_workflow_episode_exit_code()`（`_braindump_exit_code()`と同型）。

### テスト
- `tests/test_workflow_episode.py`（新規、8 tests）: id検証、`list_episodes`のstatusフィルタ
  （2値指定・`None`で全件）、`show_episode`の正常系・404・不正id。respxで
  `NautobotClient.rest_get` をモック。
- `tests/test_cli_workflow_episode.py`（新規、8 tests）: list/showのtext出力、`--status`
  repeatable、`--all`、`--json`のenvelope一致、show異常系のexit code
  （usage系→2、`nautobot_connection_error`→1）。coreは `main.build_workflow_episode_*` を
  monkeypatchでモック（`test_cli_braindump.py`と同じ境界）。
- `tests/test_cli_surface.py`: `RETAINED_COMMANDS` に `"workflow-episode"` を追加。

## テスト結果

```
uv run pytest -q tests/test_workflow_episode.py tests/test_cli_workflow_episode.py tests/test_cli_surface.py
→ 18 passed

uv run pytest -q --durations=20
→ 1165 passed
```
（既存suiteの回帰なし。旧basline件数は未記録だが、新規16 testsぶん増えている計算と整合。）

## この時点でのExit基準の充足

roadmap Phase 2の「an agent can fetch report / assessment / references from nothing but an
episode ID」は、`nctl workflow-episode show <id> --json` で `raw_data` をそのまま返すことで
本Stepの時点ですでに満たしている（plan.mdの「This step alone satisfies the "agent fetches
everything from an ID" requirement」どおり）。write/transition系はStep 2-3で追加する。

## 後続への申し送り

- Step 2（`create` / namespace writes）は本Stepのclient/errors/coreモジュールに関数を追加する形。
- `WorkflowEpisodeError` / usage codesリストは write/transition系のコードをすでに見込んで
  用意済み（`workflow_episode_validation_failed` 等）だが、実際にraiseする箇所はStep 2-3で追加。
