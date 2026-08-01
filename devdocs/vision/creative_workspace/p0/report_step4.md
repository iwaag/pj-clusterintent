# Step 4 — Rebuild, migrate, runtime gate

Nintent commit `5a550e956d06860ab1a883dd07f42161173fb531` ("Add DesiredWorkspace model,
migration, and batch writer wiring") was found already pushed to `origin/main` at the start of
this step (`git -C nintent log origin/main -1` matched local HEAD), so the Step 3 pause was
already resolved and Step 4 could proceed without further user action.

## Rebuild

```
$ cd devenv/nautobot && docker compose --env-file ../.env build --no-cache
```

Confirmed resolved SHA in the build log:

```
Resolved https://github.com/iwaag/nintent.git to commit 5a550e956d06860ab1a883dd07f42161173fb531
Successfully installed nautobot-intent-catalog-0.9.0
```

Matches the pushed nintent HEAD — no stale-cache issue.

## Up + migrate

```
$ docker compose --env-file ../.env up -d
$ docker compose --env-file ../.env exec nautobot nautobot-server migrate
```

`showmigrations nautobot_intent_catalog` confirms `[X] 0027_desiredworkspace` applied, last in
sequence after `0026_braindumpdocument_completed_status` as expected.

## Runtime gates (from superproject root)

```
$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
runtime gate result mode=keepdb label=nautobot_intent_catalog cases=215

$ ./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean
runtime gate result mode=clean label=nautobot_intent_catalog cases=215
```

Both gates: `OK`, 215 cases (up from the pre-Step-1/2 baseline; the increase includes the new
Django-gated `DesiredWorkspace` tests). `--clean` exercised the full migration chain from empty
DB through `0027_desiredworkspace`, satisfying the migration-proof requirement. No stray
`test_nautobot` cleanup was needed.

Nothing to commit in nintent for this step (no source changes, only container/DB state).
Proceeding to Step 5 (declare `pj-voxel3dprint`), which is a live desired-state write and pauses
for user confirmation before `--yes`.
