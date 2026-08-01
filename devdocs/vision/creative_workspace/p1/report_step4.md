# Step 4 — Delete the service representation (pause: desired-state write)

Appended the two `op: delete` entries recorded in `p1/report_step0.md` to `.local/desired-state.yaml`
(gitignored, operator input, not committed to this repo):

```yaml
- op: delete
  kind: desired_service_placement
  key:
    desired_service: pj-voxel3dprint
    instance_name: agpc-primary
  values: {}
- op: delete
  kind: desired_service
  key:
    slug: pj-voxel3dprint
  values: {}
```

`instance_name` was `agpc-primary` (looked up live; Step 0 only recorded the placement id, not the
instance name needed as the delete key), not the assumed `pj-voxel3dprint`.

## Preview and apply (paused for explicit approval before each)

```
$ uv run --project nctl nctl desired apply -f .local/desired-state.yaml
dry_run: {'create': 0, 'update': 0, 'delete': 2, 'unchanged': 27, 'conflict': 0}
```

Matches expectation exactly: 2 deletes (the recorded placement + service), everything else
unchanged, no conflicts.

```
$ uv run --project nctl nctl desired apply -f .local/desired-state.yaml --yes
committed: {'create': 0, 'update': 0, 'delete': 2, 'unchanged': 27, 'conflict': 0}
```

## Post-delete verification

```
$ curl ... '{"query":"{ desired_services { slug } }"}'
{"data":{"desired_services":[{"slug":"dnsmasq"},{"slug":"grafana"},{"slug":"haos"},
  {"slug":"node-agent"},{"slug":"nomad"},{"slug":"ollama"},{"slug":"prometheus"},
  {"slug":"prometheus-node-exporter"}]}}
```

`pj-voxel3dprint` is gone from `desired_services`.

```
$ uv run --project nctl nctl drift --json
```

No `pj-voxel3dprint` occurrence anywhere in the output (`grep -c voxel` → `0`), so no
`service_missing` or any other finding remains for it.
