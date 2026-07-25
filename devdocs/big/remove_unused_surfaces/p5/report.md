# Phase 5 — Coordinated Deployment (local container update)

Parent: [roadmap.md](../roadmap.md) — Phase 5. Executed at the user's direct request ("push
しました、ローカルのコンテナも更新してもらえますか") after confirming the root superproject was
pushed, following on from [Phase 4](../p4/report.md) (`complete`).

Status: **complete** for the scope requested (local container rebuild + migration + smoke checks).
Root push, DB backup, image rebuild, migration, and restart all done; no rollback needed.

## 1. Pre-deployment state

- Root superproject confirmed pushed by the user: `git fetch && git rev-parse HEAD == origin/main`
  → `06b7e367d07042fec8747b69aae6a1fcf276b84f`.
- Live installed nintent before this step: `ad9d36397d23c269ad748e13acbccc532fa29f52`, migrations
  through `0014_braindump_exchange_diary` (matches every prior phase's rollback tuple).
- Target: nintent `c343c5a56047b0df9ad901dd4459863ef1954053` (pushed, Phase 4 §14 matched tuple),
  migrations `0015_compute_platform_instance_and_endpoint_mac` +
  `0016_remove_reconciliation_dashboard_surfaces`.

## 2. Database backup

`docker exec my_postgres_db pg_dump -U nautobot -d nautobot -F c` → copied out to
`.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump` (custom format,
1,772,665 bytes, mode `0600`, directory mode `0700`). Taken before any image rebuild or migration.

## 3. Image rebuild

`docker compose --env-file ../.env build --no-cache nautobot` (per the known nintent-rebuild-cache
gotcha: always `--no-cache` and check the resolved SHA in the build log, since a cached layer can
silently keep an old commit). Build log confirms:

```
Resolved https://github.com/iwaag/nprojects.git to commit c343c5a56047b0df9ad901dd4459863ef1954053
```

Exact match to the target commit.

## 4. Container recreation

`docker compose --env-file ../.env up -d --force-recreate nautobot nautobot-worker
nautobot-scheduler` — all three containers recreated on the new image (the first plain `up -d` only
recreated `nautobot`; `--force-recreate` was needed to also pick up the new image on the worker and
scheduler containers, which had stayed on the old image otherwise). All three reported `Healthy`.

## 5. Migration

Migrations `0015` and `0016` were applied **automatically** by the container's own startup
entrypoint — `nautobot-server showmigrations nautobot_intent_catalog` immediately after recreation
already showed both `[X]`, and `django_migrations` recorded `applied` timestamps
`2026-07-25 10:31:18` for both, matching the container-recreation window exactly. Confirmed the four
removed columns (`reconciliation_status`/`reconciliation_checked_at` on both `DesiredNode` and
`DesiredService`) are actually gone via `psql \d nautobot_intent_catalog_desirednode`. A manual
`nautobot-server migrate nautobot_intent_catalog` re-run afterward was a no-op (Job-registry refresh
log lines only, no "Applying" lines), confirming migration state is stable.

## 6. Post-deployment live smoke checks (read-only except migration above)

- All three containers `Healthy`, no error/traceback in `docker logs --since 5m`.
- Installed package: `nautobot-intent-catalog` `0.9.0`, `direct_url.json` commit
  `c343c5a56047b0df9ad901dd4459863ef1954053`.
- `nctl status --json`: `ok: true`, Nautobot reachable/authenticated, intent-catalog + GraphQL up.
- `nctl drift --json`: `ok: true`, live drift computed (9 converged, 1 drifting, 1 unknown — pre-
  existing cluster state, unaffected by this deployment).
- `nctl ops list --json`: `ok: true`, reads existing operation history normally.
- REST `GET /api/plugins/intent-catalog/nodes/`: 200, no `reconciliation_status`/
  `reconciliation_checked_at` field in the response.
- GraphQL `{ desired_nodes { id slug } }`: 200, all 5 nodes returned normally.
- UI `GET /plugins/intent-catalog/nodes/` with only a token header: 302 to `/login/?next=...` — the
  expected behavior for token-only auth against a session-based UI view, not an error.
- No process listening on port 8300.

## 7. What was not done (intentionally out of scope for this request)

- No write/desired-state mutation, `nctl reconcile --yes`, Ansible run, or host actuation.
- The generated dashboard directory (`~/.local/state/nctl/dashboard/`) was not touched.
- No "stop writes" maintenance-window ceremony was run beforehand — this is a single-operator local
  experimental cluster with no concurrent writers, and the user's request was scoped to "update the
  local container," not a formal multi-step maintenance window with resume/notify steps.

## Gate

Live nintent is now `c343c5a56047b0df9ad901dd4459863ef1954053` at migration `0016`, all three
containers healthy, REST/GraphQL/CLI smoke checks pass, and the removed dashboard/cache surfaces are
confirmed absent from both code and schema. Rollback evidence (`nautobot_pre_p5_backup.dump`, live
rollback tuple in [p4/report.md](../p4/report.md) §14) is in place but was not needed.
