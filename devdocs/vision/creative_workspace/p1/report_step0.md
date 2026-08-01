# Step 0 — Live baseline (read-only)

## DesiredService / DesiredServicePlacement rows for pj-voxel3dprint

GraphQL against local Nautobot confirmed both rows exist:

```
$ curl -s -X POST http://localhost:8000/api/graphql/ \
    -H "Authorization: Token $NAUTOBOT_TOKEN" -H "Content-Type: application/json" \
    -d '{"query":"{ desired_services(slug: \"pj-voxel3dprint\") { id slug name lifecycle } desired_service_placements { id desired_service { slug } desired_node { slug } } }"}'
```

- `DesiredService`: id `361c03a9-025f-4c27-a8e1-730d787782ba`, slug `pj-voxel3dprint`, lifecycle `ACTIVE`.
- `DesiredServicePlacement`: id `7cedadf6-4e3c-49fd-a978-c41834bca3cf`, service `pj-voxel3dprint` → node `agpc`.

Exactly one row of each kind. No other rows reference `pj-voxel3dprint`.

## Current drift finding

```
$ uv run --project nctl nctl drift --json
```

Full output saved to `.local/test-strategy/creative_workspace_p1_step0_drift.json` (private, not
committed). Relevant excerpt: target `service`/`pj-voxel3dprint` (id
`361c03a9-025f-4c27-a8e1-730d787782ba`) is `drifting` with one diff:

```json
{
  "code": "service_missing",
  "severity": "error",
  "message": "pj-voxel3dprint: service_missing",
  "desired": {
    "expected": {
      "placement_id": "7cedadf6-4e3c-49fd-a978-c41834bca3cf",
      "node_id": "c82421c3-c42a-4bea-91ce-7468ae8a249c",
      "node_slug": "agpc",
      "deployment_profile": "manual_toolchain",
      "realized_device_id": "cf67fc91-fc72-4c9a-b402-b2c4c1124207",
      "observed_key": "pj-voxel3dprint"
    }
  },
  "actual": {
    "actual": { "findings": [{ "code": "service_missing" }], "observed_at": "2026-07-31T18:37:49+00:00" }
  }
}
```

No other `pj-voxel3dprint`-related finding is present.

## Step 4 delete-op targets (recorded for later use)

- `op: delete`, kind `desired_service_placement`, id `7cedadf6-4e3c-49fd-a978-c41834bca3cf`
- `op: delete`, kind `desired_service`, id `361c03a9-025f-4c27-a8e1-730d787782ba`

Reverse-`KIND_ORDER` delete ordering handles the placement-before-service dependency
automatically; both entries will be written adjacent in the same batch document per the plan.
