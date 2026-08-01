# Step 0 — Confirm the real workspace facts

Method: SSH to `agpc.local` via `~/.ssh/ansible_key` (user confirmed this method).

```
$ ssh -i ~/.ssh/ansible_key agpc.local "find / -maxdepth 4 -iname 'pj-voxel3dprint' -type d"
/home/eiji/projects/pj-voxel3dprint

$ ssh -i ~/.ssh/ansible_key agpc.local "cd /home/eiji/projects/pj-voxel3dprint && pwd && git config --get remote.origin.url"
/home/eiji/projects/pj-voxel3dprint
https://github.com/iwaag/pj-voxel3dprint.git
```

Recorded values for `.local/desired-state.yaml` (Step 5):

| field | value |
|---|---|
| `expected_path` | `/home/eiji/projects/pj-voxel3dprint` |
| `source_remote_url` | `https://github.com/iwaag/pj-voxel3dprint.git` |
| `desired_node` | `agpc` |

Read-only; no mutation on agpc.
