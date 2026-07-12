# Plan 1: Minimal Repository List App

## Goal

`nprojects` に最小の Nautobot App を作り、[nauto/seed/service_repositories.yaml](../../nauto/seed/service_repositories.yaml) の `service_repositories` を Nautobot GUI で読み取り専用表示する。

このステップでは App として Nautobot に読み込めること、URL/view/template/navigation が機能することを確認する。DB model や migration はまだ作らない。

## Target Behavior

Nautobot GUI に `Service Catalog` または同等のメニューを追加し、リポジトリ一覧ページを表示する。

一覧ページには以下を表示する。

- URL
- Enabled
- Ref
- Owner
- Service hint
- Catalog paths
- Basic file paths
- Raw URL template の有無

空の YAML の場合は「リポジトリが未登録」であることが分かる表示にする。

YAML が読めない場合は 500 で落とすのではなく、画面上にエラーを表示する。

## Non-goals

- Nautobot DB に保存しない。
- GUI から YAML を編集しない。
- `catalog-info.yaml` を取得しない。
- GitHub/GitLab API に通信しない。
- `desired_services.generated.yaml` を生成しない。
- 既存 `nauto` Jobs を変更しない。

## Proposed Package Layout

```text
nprojects/
├── pyproject.toml
├── nautobot_service_catalog/
│   ├── __init__.py
│   ├── navigation.py
│   ├── urls.py
│   ├── views.py
│   ├── loaders.py
│   └── templates/
│       └── nautobot_service_catalog/
│           └── repository_list.html
└── README.md
```

Optional later files:

```text
nautobot_service_catalog/
├── jobs.py
├── models.py
├── tables.py
├── filters.py
├── forms.py
└── api/
```

## Implementation Steps

1. Create Python packaging metadata.

   Add `pyproject.toml` with a minimal editable-installable package. Keep dependencies narrow. Do not pin Nautobot itself inside the package unless the local deployment needs it.

2. Create Nautobot App config.

   In `nautobot_service_catalog/__init__.py`, define a `NautobotAppConfig` subclass.

   Suggested values:

   - `name = "nautobot_service_catalog"`
   - `verbose_name = "Service Catalog"`
   - `base_url = "service-catalog"`
   - `version = "0.1.0"`
   - `description = "Display and analyze cluster service repositories."`

3. Add a YAML loader.

   Implement `load_service_repositories(path: Path)`.

   Behavior:

   - Return a structured result containing `repositories`, `errors`, and `source_path`.
   - Accept both string entries and mapping entries, matching the current Job behavior.
   - Default missing `enabled` to `true`.
   - Default missing lists to empty lists for display. Do not apply full analysis defaults yet unless the UI needs them.
   - If `service_repositories` is missing, treat it as an empty list.
   - If `service_repositories` exists but is not a list, return an error.

4. Resolve the YAML path.

   First implementation can use a conservative default:

   ```text
   ../nauto/seed/service_repositories.yaml
   ```

   from the `nprojects` repository root.

   Also support optional environment override:

   ```text
   NAUTOBOT_SERVICE_REPOSITORIES_FILE=/path/to/service_repositories.yaml
   ```

   Later this should become `PLUGINS_CONFIG["nautobot_service_catalog"]`.

5. Add the view and URL.

   Add a class-based or function-based view that renders `repository_list.html`.

   URL:

   ```text
   /plugins/service-catalog/repositories/
   ```

   URL name:

   ```text
   repository_list
   ```

6. Add navigation.

   Add a navigation item named `Repositories` under a `Service Catalog` grouping if the Nautobot navigation API in the target version supports it.

   If the exact navigation API differs locally, defer navigation and rely on direct URL for the first smoke test.

7. Add template.

   Extend Nautobot's base template and render a simple table.

   Requirements:

   - Show source YAML path.
   - Show parse errors prominently but without exposing secrets.
   - Show empty state.
   - Keep long URLs readable with wrapping.

8. Add README instructions.

   Document local install and Nautobot config:

   ```bash
   pip install -e /path/to/nprojects
   ```

   ```python
   PLUGINS = [
       "nautobot_service_catalog",
   ]
   ```

   If using env override:

   ```bash
   export NAUTOBOT_SERVICE_REPOSITORIES_FILE=/path/to/nauto/seed/service_repositories.yaml
   ```

9. Smoke test outside Nautobot where possible.

   Since Nautobot may not be available in this workspace, test the YAML loader with plain Python.

   Example:

   ```bash
   python - <<'PY'
   from pathlib import Path
   from nautobot_service_catalog.loaders import load_service_repositories
   result = load_service_repositories(Path("../nauto/seed/service_repositories.yaml"))
   print(result)
   PY
   ```

10. Smoke test inside Nautobot.

   In the Nautobot environment:

   - Install the package editable.
   - Add the App to `PLUGINS`.
   - Restart web and worker processes.
   - Visit `/plugins/service-catalog/repositories/`.
   - Confirm empty state is displayed for current `service_repositories: []`.
   - Add one test repository to YAML and confirm it appears after reload or Git sync.

## Suggested Loader Data Shape

```python
{
    "source_path": "/abs/path/to/service_repositories.yaml",
    "repositories": [
        {
            "url": "https://github.com/example/service",
            "enabled": True,
            "ref": None,
            "owner": None,
            "service_hint": None,
            "catalog_paths": ["catalog-info.yaml"],
            "basic_file_paths": ["README.md"],
            "raw_url_template": None,
        }
    ],
    "errors": [],
}
```

For display-only mode, this can be a dataclass instead of a dict. Prefer a dataclass if implementation stays small.

## Acceptance Criteria

- `nprojects` is installable as a Python package.
- Nautobot can import `nautobot_service_catalog`.
- App config is visible under installed Apps.
- Repository list page renders without DB migrations.
- Current empty [service_repositories.yaml](../../nauto/seed/service_repositories.yaml) renders an empty state.
- A sample repository entry renders as one row.
- Invalid YAML or invalid `service_repositories` type produces a clear UI error.

## Follow-up After Plan 1

- Move loader defaults closer to `Generate Desired Services` so GUI and Job interpret YAML identically.
- Add tests for the loader.
- Add an App Job that performs dry-run repository analysis.
- Decide whether App config should use `PLUGINS_CONFIG` rather than environment variables.
