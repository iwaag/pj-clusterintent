# Step 6 — Live rollout and proof

All three sub-steps paused for explicit approval before touching the live scratch Nautobot /
real `agpc` node; approved at each point.

## 1. Nautobot Git Repository re-sync + seed job

```
$ curl -X POST .../api/extras/git-repositories/7c7000bc-.../sync/
job_result status: PENDING -> SUCCESS
```

`current_head` after sync: `2f453f1fa0a0488fbe208ee852ba48f4c9245e64` (matches the pushed nauto
`main`, containing Step 3's `observed_workspaces` seed entry).

```
$ curl -X POST .../api/extras/jobs/d04c044a-.../run/ -d '{"data": {"seed_file": "seed/home_cluster.yaml", "update_existing": true}}'
job_result status: PENDING -> SUCCESS
```

Confirmed the custom field now exists:

```
$ curl .../api/extras/custom-fields/
observed_workspaces  Observed Workspaces  {'value': 'json', 'label': 'JSON'}
```

## 2. `nctl reconcile agpc --refresh-observation`

Dry plan first:

```
$ uv run --project nctl nctl reconcile agpc --refresh-observation
plan: 1 action -- observe_node (forced observation refresh), mutates=true, no other action
```

Approved, then applied:

```
$ uv run --project nctl nctl reconcile agpc --refresh-observation --yes
operation_id: 01KYYP7D1X411ZJ11F5K4VH084
state: converged
round 0: 2 action(s)
    [ok] observe_node (observe_node)
    [ok] regenerate_production_inventory (production_inventory)
ok: True
```

## 3. Positive evidence

**Probe config actually rendered for agpc** (`probe-config/agpc.yaml` in the operation artifacts):

```yaml
workspace_probe_hints:
  pj-voxel3dprint:
    path: /home/eiji/projects/pj-voxel3dprint
```

**Operation evidence recorded the expected nodeutils version** (`result.json`):

```json
{"action_id": "observe_node", "detail": {"nodeutils_version": "5ebd4154ca14aad1fed028580d361d00c02d05a5"}, "success": true}
```

Matches the nodeutils Step 1 commit exactly, and `ingest_outcome: "updated"`.

**`agpc` Device's `observed_workspaces` custom field** (fetched live after the round):

```json
{
  "pj-voxel3dprint": {
    "present": true,
    "path": "/home/eiji/projects/pj-voxel3dprint",
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

Confirmed with the user: present/ahead=5/dirty=false/branch=main matches the tree's real current
state on agpc.

**Fresh `nctl drift --json`**: `ok: true`, zero occurrences of `voxel` anywhere in the output — no
`service_missing` (already true since Step 4) and no new unrelated finding introduced by this
phase's changes.

## Deviations from the plan

None. All three sub-steps ran exactly as planned; no loop-back to Step 3 was needed (ingest
accepted the report on the first attempt).
