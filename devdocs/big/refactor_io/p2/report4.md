# Phase 2 Step 4 Report — Deployment and Live Acceptance

## Result

Phase 2 is complete. The local scratch Nautobot image now runs pushed nintent
commit `504e8a1de4f858b0707633933e2d342bb3b67386`, which contains the endpoint
and its tests. The deployment pin in `devenv/nautobot/Dockerfile` was advanced
from stale `525057f` to that verified pushed revision after the first no-cache
build exposed the stale pin. The second no-cache build resolved and verified
the exact pushed SHA before installation.

The scratch database was backed up before deployment to
`.local/p2-nautobot-predeploy-20260730.dump` (ignored, 1.8 MB). Containers were
rebuilt/restarted, `post_upgrade` completed, and the stale `AnalyzeIntentSources`
Job row was removed after the no-longer-registered Job was confirmed absent.
The Phase 1 schema migrations were already present, so migration reported `No
migrations to apply`.

## Live acceptance

- An authenticated JSON `dry_run: true` mixed batch (`desired_node` plus its
  `desired_endpoint`) returned two `create` actions without persisting either
  synthetic `p2-smoke-*` row.
- Repeating it with `dry_run: false` returned `committed`; GraphQL immediately
  returned both normalized rows.
- An explicit endpoint-then-node delete batch returned `committed`; GraphQL
  then returned neither synthetic row.
- `uv run --project nctl nctl drift --json` exited 0 with `ok: true`, proving
  the live nctl read path still works with the reduced schema. Its reported
  existing cluster drift/stale-observation findings are unrelated to this
  synthetic endpoint smoke and were not changed.

No token, request payload archive, or synthetic desired-state row was retained.
