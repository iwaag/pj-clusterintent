# Report 1: Minimal Repository List App

## Summary

Executed [.local/nprojects/plan1.md](plan1.md).

Created the first minimal Nautobot App under `nprojects`. The App is read-only and displays `service_repositories` from the existing [nauto/seed/service_repositories.yaml](../../nauto/seed/service_repositories.yaml) file.

This implementation intentionally does not add database models, migrations, remote Git fetches, or catalog analysis.

## Files Added

```text
nprojects/
├── .gitignore
├── README.md
├── pyproject.toml
└── nautobot_service_catalog/
    ├── __init__.py
    ├── loaders.py
    ├── navigation.py
    ├── urls.py
    ├── views.py
    └── templates/
        └── nautobot_service_catalog/
            └── repository_list.html
```

## Implemented Behavior

- Defines a Nautobot App named `nautobot_service_catalog`.
- Uses `base_url = "service-catalog"`.
- Adds a repository list URL:

```text
/plugins/service-catalog/repositories/
```

- Loads the repository catalog from:

```text
/home/eiji/agdev/temp2/nauto/seed/service_repositories.yaml
```

- Supports override with:

```text
NAUTOBOT_SERVICE_REPOSITORIES_FILE=/path/to/service_repositories.yaml
```

- Accepts `service_repositories` entries as either URL strings or mappings.
- Displays:
  - URL
  - Enabled
  - Ref
  - Owner
  - Service hint
  - Catalog paths
  - Basic file paths
  - Raw URL template presence
- Handles these cases as non-fatal loader results:
  - missing file
  - unreadable file
  - invalid YAML
  - non-mapping YAML root
  - non-list `service_repositories`
  - malformed individual entries

## Verification Performed

Compiled the App modules:

```bash
python3 -m compileall nprojects/nautobot_service_catalog
```

Result: passed.

Loaded the current real YAML:

```text
source= /home/eiji/agdev/temp2/nauto/seed/service_repositories.yaml
repositories= 0
errors= []
```

This matches the current file content:

```yaml
service_repositories: []
```

Tested a temporary sample YAML with two repository entries.

Result:

```text
repositories= 2
errors= []
```

Tested invalid YAML and invalid `service_repositories` type.

Result:

```text
Repository catalog YAML is invalid: ...
service_repositories must be a list.
```

Built a wheel:

```bash
python3 -m pip wheel ./nprojects --no-deps -w /tmp/nautobot_service_catalog_wheel_test
```

Result: passed.

Confirmed the template is included in the built wheel:

```text
nautobot_service_catalog/templates/nautobot_service_catalog/repository_list.html
```

## Not Verified

Nautobot runtime integration was not verified in this workspace because no running Nautobot environment is available here.

The following still needs to be checked inside the actual Nautobot environment:

- `pip install -e /path/to/nprojects`
- Add `"nautobot_service_catalog"` to `PLUGINS`
- Restart Nautobot web and worker processes
- Confirm the App appears under installed Apps
- Open `/plugins/service-catalog/repositories/`
- Confirm navigation works

## Notes

`nautobot_service_catalog/__init__.py` includes a small fallback for local loader-only tests when Nautobot is not installed. In Nautobot, the real `nautobot.apps.NautobotAppConfig` should be imported and used.

`navigation.py` also degrades to an empty `menu_items` tuple if Nautobot's UI navigation classes are unavailable. This keeps local tests simple, but the navigation item should be confirmed against the target Nautobot version.

After the follow-up path fix, the preferred configuration is `PLUGINS_CONFIG`.
If no explicit path is configured, the development fallback is:

```text
./nauto/seed/service_repositories.yaml
```

relative to Nautobot's current working directory.

## Recommended Next Steps

1. Smoke test inside Nautobot.
2. If navigation import or rendering fails, adjust `navigation.py` to match the installed Nautobot version.
3. Keep the repository file path in `PLUGINS_CONFIG` for Nautobot deployments.
4. Add unit tests for `loaders.py`.
5. Align display defaults with `Generate Desired Services`, especially default `catalog_paths` and `basic_file_paths`.
6. Start Plan 2: add a dry-run repository analysis Job that reuses or ports logic from `nauto/jobs/generate_desired_services.py`.

## Follow-up Fix: Repository File Path Resolution

After installing the App in Nautobot, the repository list page looked for:

```text
/opt/nautobot/.local/lib/python3.12/nauto/seed/service_repositories.yaml
```

Cause:

- The first implementation derived the fallback path from `__file__`.
- In the local workspace, `__file__` points into `nprojects/nautobot_service_catalog`.
- In Nautobot, the package is installed under `site-packages`.
- Therefore the fallback path became relative to the installed Python package directory, not the workspace or Git repository.

Fix applied:

- `PLUGINS_CONFIG["nautobot_service_catalog"]["service_repositories_file"]` is now supported and takes precedence.
- `NAUTOBOT_SERVICE_REPOSITORIES_FILE` remains supported as a fallback override.
- The final development fallback is now `Path.cwd() / "nauto/seed/service_repositories.yaml"` instead of a path derived from `site-packages`.

Recommended Nautobot config:

```python
PLUGINS = [
    "nautobot_service_catalog",
]

PLUGINS_CONFIG = {
    "nautobot_service_catalog": {
        "service_repositories_file": "/absolute/path/to/nauto/seed/service_repositories.yaml",
    },
}
```

Verification after fix:

```text
python3 -m compileall nprojects/nautobot_service_catalog
default path from workspace: /home/eiji/agdev/temp2/nauto/seed/service_repositories.yaml
configured absolute path: /tmp/example/service_repositories.yaml
configured relative path: /home/eiji/agdev/temp2/relative/service_repositories.yaml
environment override: /tmp/from-env.yaml
```
