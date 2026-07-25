# Phase 4 Step 4 Report — Approve maintenance, freeze writers, and verify backups

Plan: [plan.md](plan.md), Step 4.

Status: **complete**. Explicit operator approval to enter the maintenance window was obtained
before any live service was stopped. Writers were frozen, a verified PostgreSQL dump and media
archive were captured, both were proved restorable/listable in a disposable database, live
fingerprints were rechecked before and after the freeze and found unchanged, and — per a second
explicit operator decision — live services were resumed at the end of this step rather than left
down, since Step 5 (candidate deployment) is a separate step not yet approved.

## 0. Approval

Before any action, the user was asked whether to proceed with Step 4 given its live-cluster impact
(stopping scheduler/worker/web, taking a real backup). Approved: "Yes, proceed with Step 4."

## 1. Pre-freeze baseline (plan items 1-2)

No routine nctl mutation or VM Phase 3 seed process was running on the host (`ps aux` showed no
`nctl` process, no relevant cron entry). Live `JobResult` query (via `nautobot-server shell
--command`, not `-c`, which collides with the tool's own `-c/--config-path` flag and silently
truncates `config_path` — worth noting for future sessions) showed:

- `active_count` (PENDING/RUNNING) = **0**
- no enabled `ScheduledJob` rows
- latest 5 `JobResult`s all `SUCCESS`, most recent `2026-07-24 18:31:33` (over a day old at freeze
  time) — `AI Resource Review` and `Ingest Nodeutils Inventory`, both event-driven, not polling

Pre-freeze aggregate fingerprint (via live ORM):

| Model | Count |
|---|---:|
| IntentSource | 2 |
| DesiredNode | 5 |
| DesiredEndpoint | 5 |
| DesiredIPRange | 3 |
| DesiredService | 6 |
| DesiredServicePlacement | 1 |
| DesiredNodeOperationalOverride | 0 |
| BrainDumpDocument | 5 |
| AlignmentReview | 5 |
| Device | 5 |
| ObjectChange (total) | 893 |
| ObjectChange (latest `time`) | 2026-07-24 18:31:33.032106+00 |

Declared-root total (2+5+5+3+6+1+0 = 22) matches the plan's Section 5.3 planning-time hypothesis.

## 2. Maintenance boundary (plan items 1, 3, 4)

Recorded in `.local/interface-contract/p4/20260726_step4/maintenance_start.txt`:

- maintenance start (scheduler/worker stop issued): `2026-07-25T18:24:03Z`
- web stop (zero-write interval begins): `2026-07-25T18:24:37Z`
- maintenance end (all three services resumed and healthy): `2026-07-25T18:28:24Z`
- **zero-write interval: ~3m47s** (18:24:37Z–18:28:24Z), during which `nautobot`,
  `nautobot-worker`, and `nautobot-scheduler` were all stopped

Commands used: `docker compose --env-file ../.env stop nautobot-scheduler nautobot-worker`, then
`docker compose --env-file ../.env stop nautobot` — run from `devenv/nautobot`. Stopping the web
container is the chosen way to "quiesce the web write path" (plan item 4): it removes any write
surface entirely rather than relying on a partial in-app freeze, and required no code change.

No new Import/Analyze/IPAM/Ingest/Seed submission was possible during the freeze because all three
Nautobot processes (web, worker, scheduler) were stopped; there was no separate technical lock to
add beyond that.

## 3. Backup (plan items 5-6)

Live database is external to any nintent-managed compose project: PostgreSQL runs in
`my_postgres_db` (`postgres:15-alpine`, host port 5432), database `nautobot`, user `nautobot`
(confirmed via `\conninfo`; version `PostgreSQL 15.17`). Media is the named Docker volume
`nautobot_nautobot_media`.

```
docker exec -e PGPASSWORD=nautobot my_postgres_db pg_dump -U nautobot -d nautobot -Fc \
  -f /tmp/nautobot_p4_step4.dump
docker cp my_postgres_db:/tmp/nautobot_p4_step4.dump <evidence_dir>/nautobot_p4_step4.dump
```

- dump size: 1,783,607 bytes
- `pg_restore -l` on the dump: **2415 TOC entries**, archive timestamp `2026-07-25 18:24:37 UTC`
  (matches the web-stop instant, confirming the dump was taken immediately after quiescing)

Media archive:

```
docker run --rm -v nautobot_nautobot_media:/media_src -v <evidence_dir>:/backup alpine \
  sh -c "cd /media_src && tar czf /backup/nautobot_media_p4_step4.tar.gz . && echo done"
```

The volume is genuinely empty — `find /media_src -type f | wc -l` = 0, containing only three empty
directories (`devicetype-images/`, `health_check_storage_test/`, `image-attachments/`). The
resulting 189-byte archive is the correct, truthful size for an empty volume, not a failure.

SHA-256 checksums recorded in `checksums.sha256`:

```
3238b0e599fec9968c882fabaf9ab7af4ea80b96e59076cfec2f74eb83a006e2  nautobot_p4_step4.dump
09ae03e09dccbd4794e519d47276523166431cdd69b724f36483397df6800d0f  nautobot_media_p4_step4.tar.gz
```

## 4. Disposable restore proof (plan item 7)

```
docker exec my_postgres_db createdb -U nautobot -O nautobot nic_p4_step4_restore
docker cp <evidence_dir>/nautobot_p4_step4.dump my_postgres_db:/tmp/nautobot_p4_step4.dump
docker exec -e PGPASSWORD=nautobot my_postgres_db pg_restore -U nautobot \
  -d nic_p4_step4_restore /tmp/nautobot_p4_step4.dump
```

Exit code 0, no errors (`pg_restore_run.log` is empty — clean run at default verbosity). Verified
against the separately named disposable database:

| Check | Result |
|---|---|
| `nautobot_intent_catalog_intentsource` count | 2 (matches pre-freeze) |
| `nautobot_intent_catalog_desirednode` count | 5 (matches pre-freeze) |
| `dcim_device` count | 5 (matches pre-freeze) |
| `django_migrations` for `nautobot_intent_catalog`, last 3 | `0016_remove_reconciliation_dashboard_surfaces`, `0015_compute_platform_instance_and_endpoint_mac`, `0014_braindump_exchange_diary` — ends at `0016`, matching live |

The disposable database was dropped immediately after verification
(`dropdb -U nautobot nic_p4_step4_restore`) and its absence confirmed via a `pg_database` lookup.
The dump file copied into the Postgres container for the restore test was also removed
(`docker exec my_postgres_db rm /tmp/nautobot_p4_step4.dump`).

## 5. Media archive verification (plan item 8)

`find`/`ls` inside a disposable Alpine container mounting the same volume (before archiving) showed
the three empty directories listed above and 0 files — the archive is listable
(`tar tzf` succeeds; trivial given the 189-byte size) and there is no private content to sample.

## 6. Post-backup fingerprint recheck (plan item 9)

Queried directly against the live `nautobot` database via `psql` (not through the stopped web
container's ORM) immediately after the backup, before resuming services:

| Check | Value | vs. pre-freeze |
|---|---|---|
| `intentsource` count | 2 | unchanged |
| `desirednode` count | 5 | unchanged |
| `dcim_device` count | 5 | unchanged |
| `extras_objectchange` count | 893 | unchanged |
| `extras_objectchange` max `time` | 2026-07-24 18:31:33.032106+00 | unchanged |

No write occurred during the freeze.

## 7. Resume decision (plan item 10 / cutover interval)

The plan's ordering (Section 5.4) keeps writers frozen continuously from Step 4 through Step 7, but
this task instance was scoped to advance exactly one step, and Step 5 (replacing web/worker/
scheduler with the candidate image) is a separate, not-yet-approved live-adjacent action. Rather
than leave live services down indefinitely between sessions, this was raised as a second explicit
decision point; the user chose to resume the current (pre-Step-5) services now:

```
docker compose --env-file ../.env start nautobot nautobot-worker nautobot-scheduler
```

All three came up healthy within ~30s. Post-resume fingerprint recheck (via live ORM) again showed
`IntentSource=2`, `DesiredNode=5`, `Device=5` — unchanged. The exact cutover/zero-write interval
(`2026-07-25T18:24:37Z`–`2026-07-25T18:28:24Z`, ~3m47s) is recorded so Step 4's backup remains a
valid, timestamped rollback point even though the live stack returned to normal operation
afterward; Step 5 will need its own fresh freeze when approved.

## 8. Rollback tuple (plan item 10 / Section 5.1 partial)

Recorded in `rollback_manifest.txt`:

- nintent installed direct-url commit: `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` (package 0.9.0)
- live nintent migrations: through `0016_remove_reconciliation_dashboard_surfaces`
- live nauto GitRepository revision: `2635e648469d6e6bad87af113f7427b878b0a387`
- superproject SHA: `dcd4718f097cce0c6e5300a36e6a653884ea3899`
- live rollback image IDs (unchanged, pre-Step-5): `nautobot-nautobot` /
  `nautobot-nautobot-worker` / `nautobot-nautobot-scheduler` as built before this phase

Redis was not backed up, consistent with plan Section 5.5 ("Redis is not authoritative and is not
restored as state").

## Evidence retention

`.local/interface-contract/p4/20260726_step4/` (directory mode `0700`, files mode `0600`):
`maintenance_start.txt`, `nautobot_p4_step4.dump`, `nautobot_media_p4_step4.tar.gz`,
`checksums.sha256`, `pg_restore_list.txt`, `pg_restore_run.log`, `rollback_manifest.txt`. Checked
for secrets before setting permissions: `pg_restore_list.txt` contains only schema-level table/
index/constraint *names* (e.g. `extras_secret`, `users_token`) from `pg_restore -l`'s TOC listing,
no actual secret/token values. No credential, token, or private prose value appears in any evidence
file. Not committed (matches Section 5.5's "do not commit them").

## What Step 4 does not close

- Step 5 (deploy the exact matched candidate image with writes still frozen) was not started; live
  services are back on the pre-Step-5 image and tuple.
- No candidate image was started against live data; the Step 3 candidate
  (`nic-p4-candidate:20260726b`) remains disposable-only.
- A fresh freeze/backup will be needed at Step 5's own gate per the plan's stated ordering, since
  this step's freeze was explicitly ended early per the second operator decision above.

## Verification

- `docker ps` before/after: the three live `nautobot-*` containers were the only ones
  stopped/restarted; no other container on the host was touched.
- `pg_restore -l`: 2415 TOC entries, matches archive-creation timestamp to the web-stop instant.
- Disposable restore (`nic_p4_step4_restore`): exit 0, counts and migrations match live; database
  dropped and absence confirmed afterward.
- Live fingerprint (`intentsource`/`desirednode`/`device` counts, `extras_objectchange` count and
  max `time`) identical before freeze, immediately after backup, and after resume.
- `checksums.sha256` recorded for both backup artifacts.
- Evidence directory/files permissions set to `0700`/`0600`; grepped for secret-like strings before
  permissioning — only schema object names matched, no real secret values.

Next: Step 5 (deploy the exact matched code with data writes still frozen) — a further live-adjacent
step requiring its own explicit operator approval per plan Section 3.4.
