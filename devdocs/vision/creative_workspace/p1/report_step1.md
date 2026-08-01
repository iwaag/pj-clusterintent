# Step 1 — nodeutils collector

## Changes (`nodeutils` `5ebd415`)

- `workspace_probe_hints(config)`: reads `config["workspace_probe_hints"]` (name → `{path, ...}`),
  same shape/validation style as `service_probe_hints`.
- `run_git(path, args, timeout=8)`: bounded `git -c safe.directory=<path> -C <path> <args>` via the
  existing `run_command` helper (returns `None` on any failure/missing binary, never raises).
- `observe_workspace(hint, collected_at)`: closed, never-raising observation.
  - `path` missing/relative or directory absent → `present: false`.
  - directory present, not a git repo → `present: true`, `raw.is_git: false`, no identity fields.
  - git repo → `present: true`, `head_sha`, `remote_url`, `last_commit_at`, `branch`,
    `dirty` (from `git status --porcelain=v2 --branch`), `ahead`/`behind` (only when an upstream is
    configured), plus `raw.submodule_status`, `raw.stash_count`, `raw.upstream`.
  - each git subcommand failing independently degrades to a partial result (tested).
- `get_workspace_summary(config, collected_at)`: `{name: compact_dict(observe_workspace(...))}` for
  every hinted workspace.
- Wired into `collect_inventory` (`inventory["observed_workspaces"]`) and `build_inventory_report`
  (`facts["workspaces"]`), same top-level promotion pattern as `observed_services`. Flows through
  the existing `bounded_value`/`MAX_REPORT_BYTES` enforcement with no special-casing.
- Removed `"pj-voxel3dprint"` from `IMPORTANT_SERVICE_NAMES` in the same commit — it is now
  observed exclusively via `observed_workspaces`, per the plan's coordinated-rollout note.
- `SCHEMA_VERSION` left at `nodeutils.inventory.v2` — this is an additive section, matching the
  plan's stated criterion (`nctl/src/nctl_core/dumps.py` checks the version string only).

## Deviations from the plan

None. All "Proposed observation shape" promoted fields are implemented; `raw` carries submodule
status, stash count, and upstream branch name as the generous-but-bounded extras.

## Tests

`nodeutils` ordinary gate:

```
$ uv run pytest -q --durations=20
76 passed in 3.23s
```

11 new cases in `tests/test_inventory_report.py::ObserveWorkspaceTests`, using real `git init`
fixtures in `tmp_path` (no git mocking), covering: missing path, non-git directory, present clean,
present dirty + ahead of a real bare-repo upstream, one git subcommand failing while others
succeed, malformed `workspace_probe_hints` entries filtered out, summary keying, and the
`IMPORTANT_SERVICE_NAMES` removal.
