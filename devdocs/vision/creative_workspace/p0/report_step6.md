# Step 6 — GraphQL proof + phase report

## GraphQL proof

Endpoint note: `/graphql/` (the web GraphiQL UI route) requires a session + CSRF cookie and
rejected a bare token-authenticated POST with a CSRF failure page. The REST-token-authenticated
route is `/api/graphql/`; used that instead.

```
$ curl -s -X POST http://localhost:8000/api/graphql/ \
    -H "Authorization: Token $TOKEN" -H "Content-Type: application/json" \
    -d '{"query":"{ desired_workspaces { slug lifecycle source_remote_url expected_path desired_presence desired_node { slug } } }"}'
```

```json
{
  "data": {
    "desired_workspaces": [
      {
        "slug": "pj-voxel3dprint",
        "lifecycle": "ACTIVE",
        "source_remote_url": "https://github.com/iwaag/pj-voxel3dprint.git",
        "expected_path": "/home/eiji/projects/pj-voxel3dprint",
        "desired_presence": "PRESENT",
        "desired_node": { "slug": "agpc" }
      }
    ]
  }
}
```

Matches Step 0's recorded facts and Step 5's applied values exactly. Auto-generated plural is
`desired_workspaces`, per the model meta, as expected.

## Phase 0 summary

All exit criteria from `p0/plan.md` met:

1. Batch apply (dry preview, then `--yes`) created the `pj-voxel3dprint` row — preview showed
   `{'create': 1, 'update': 0, 'delete': 0, 'unchanged': 26, 'conflict': 0}`, apply committed the
   same.
2. GraphQL query against the local Nautobot returned it (above).
3. nintent test gates passed: Django-free fast gate (130 tests, 10 expected skips) and Nautobot
   runtime gate, both `--keepdb` and `--clean` (216 cases each, `OK`). `--clean` exercised the
   full migration chain including `0027_desiredworkspace`.

## Deviations from the plan

- **Bug found and fixed mid-phase** (Step 5): `api/views.py`'s `_BATCH_MODELS` permission-check
  registry was a second, independent kind→model map that Step 2 didn't know about and didn't
  update — any `desired_workspace` batch operation 500'd. Fixed (`nintent` `c17f646`) with a
  regression test (`BatchModelRegistryTests.test_batch_models_covers_kind_order`) asserting
  `_BATCH_MODELS` stays a superset-equal to `batch.py`'s `KIND_ORDER`, so a future new kind that
  misses this registry fails the gate instead of surfacing as a live 500. See
  [report_step5.md](report_step5.md) for the full root-cause writeup.
- UI (admin/views/tables/templates/navigation) was skipped in Step 1, per the plan's stated
  option — see [report_step1.md](report_step1.md) for confirmation.
- Everything else matched the plan as written; no other deviations.

## Scope confirmation

nintent-only change plus `.local/desired-state.yaml` (gitignored operator input, not committed)
and the superproject submodule pointer. No nodeutils/nauto/nctl evaluation changes, consistent
with the plan's stated Phase 0 scope (observation is Phase 1, evaluation is Phase 2).

Phase 0 is complete.
