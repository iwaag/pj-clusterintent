# Creative Workspace — Phase 2 Step 0: Baseline (read-only)

## `nctl drift --json`

`uv run --project nctl nctl drift --json` against the live scratch Nautobot, `fetched_at:
2026-08-01T13:12:59.106302+00:00`. Grepped the full output for `voxel`/`workspace`: zero
occurrences. Confirms the plan's expectation — no workspace evaluator exists yet, so
`pj-voxel3dprint` produces no drift findings at all (neither `service_*`, per Phase 1, nor any
`workspace_*` code, since none is registered).

## `agpc` Device `observed_workspaces` custom field

Fetched via `GET /api/dcim/devices/?name=agpc`, `custom_fields.observed_workspaces`:

```json
{
  "pj-voxel3dprint": {
    "path": "/home/eiji/projects/pj-voxel3dprint",
    "present": true,
    "head_sha": "b9405c5eccfb458397796c29cc43b28486ce4d51",
    "remote_url": "https://github.com/iwaag/pj-voxel3dprint.git",
    "branch": "main",
    "ahead": 5,
    "behind": 0,
    "dirty": false,
    "last_commit_at": "2026-07-22T12:35:48+09:00",
    "checked_at": "2026-08-01T12:54:30+00:00",
    "raw": {
      "upstream": "origin/main",
      "stash_count": 0,
      "submodule_status": [
        "8fc7c45f24b66cc6b285e042f011f23ed51eb323 vdbmat (heads/main)",
        " 3c769ca6d15bca2aeb1034410ca0f20414d84f52 vdbmat-utils (heads/main)"
      ]
    }
  }
}
```

All fields promoted per [p1/report.md](../p1/report.md) §"Handed to Phase 2" are present and
well-formed. `checked_at` is `2026-08-01T12:54:30+00:00`, ~18 minutes before the drift fetch
(`13:12:59`) — well under the 24 h `stale_after_hours` default, so **Step 4's live proof does not
need a `nctl reconcile agpc --refresh-observation` round first**; the existing observation is
already fresh.

`ahead: 5, dirty: false, behind: 0` — under the plan's classification this is `active_development`
(ahead > 0), to be confirmed against the real tree state by the user in Step 4.

## Scope confirmation

Read-only: one `nctl drift --json` invocation and one REST `GET`. No writes, no reconcile round,
no code changes. nctl submodule pointer at `32d3e6d` (unchanged this step).
