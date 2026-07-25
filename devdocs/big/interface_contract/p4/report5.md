# Phase 4 Step 5 Report — Deploy the exact matched code with data writes still frozen

Plan: [plan.md](plan.md), Step 5.

Status: **complete**. The already-tested candidate image (`nic-p4-candidate:20260726b`,
`sha256:ef28300287a39646b9a1c0f58bdcd2b80e4ab5b9e3e16227796962bc53a9f952`) now runs identically as
`nautobot`, `nautobot-worker`, and `nautobot-scheduler`. No rebuild occurred during the window — the
already-built and disposable-verified image was retagged onto the compose-expected image names, so
`docker compose up` reused it rather than invoking `docker compose build`. No Import apply or
retained REST/UI writer ran. Live domain-row fingerprints are unchanged from Step 4's baseline; the
only live writes were the explicitly approved `GitRepositorySync` Job's own bookkeeping rows.

## 0. Approvals

Two explicit operator decisions were obtained, per plan Section 3.4 and this project's
live-action pause convention:

1. Before starting Step 5 at all: approval to re-freeze writers and deploy the candidate image
   ("Yes, proceed with Step 5").
2. Mid-step, when the live nauto `GitRepository` was found stale (`current_head` = `251b056...`,
   several commits behind the approved `2635e64...`): approval to run the built-in
   `Git Repository: Sync` Job to bring it to the approved commit (a sandbox classifier had blocked
   the unattended `runjob` invocation as a live-mutating action). Approved: "Yes, run the Git
   Repository sync."

## 1. Pre-swap fingerprint check (plan context)

Before touching any container, live fingerprints were re-read directly via `psql` and compared
against Step 4's recorded post-resume baseline:

| Check | Value | vs. Step 4 baseline |
|---|---:|---|
| `intentsource` | 2 | unchanged |
| `desirednode` | 5 | unchanged |
| `dcim_device` | 5 | unchanged |
| `extras_objectchange` count | 893 | unchanged |
| `extras_objectchange` max `time` | 2026-07-24 18:31:33.032106+00 | unchanged |
| active/pending `JobResult` | 0 | unchanged |

No write occurred on the live stack between Step 4's resume and Step 5's start.

## 2. Maintenance freeze (plan items 1, part of "writes still frozen")

Recorded in `.local/interface-contract/p4/20260726_step5/maintenance_start.txt`:

```
docker compose --env-file ../.env stop nautobot-scheduler nautobot-worker
docker compose --env-file ../.env stop nautobot
```

- scheduler/worker stop issued: `2026-07-25T18:37:12Z`
- web stop issued: `2026-07-25T18:37:15Z`
- all three stopped: `2026-07-25T18:37:23Z`

## 3. Candidate deployment without rebuild (plan item 1)

```
docker tag nic-p4-candidate:20260726b nautobot-nautobot:latest
docker tag nic-p4-candidate:20260726b nautobot-nautobot-worker:latest
docker tag nic-p4-candidate:20260726b nautobot-nautobot-scheduler:latest
docker compose --env-file ../.env up -d --no-build nautobot
docker compose --env-file ../.env up -d --no-build nautobot-worker nautobot-scheduler
```

All three (`nautobot-nautobot-1`, `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1`)
came up and reported `healthy` within ~30s of each `up`. `docker compose`'s image-name convention
(`<project>-<service>`) meant the pre-existing candidate tag was picked up directly; no
`docker compose build` step ran, so the Dockerfile's `ARG NINTENT_COMMIT`/`ARG NAUTO_COMMIT`
defaults were never re-resolved against a mutable branch during the window.

## 4. Matched-image and migration verification (plan items 2-6)

`.local/interface-contract/p4/20260726_step5/deploy_verification.txt`:

| Check | web | worker | scheduler |
|---|---|---|---|
| `docker inspect --format '{{.Image}}'` | `sha256:ef28300287a3...` | `sha256:ef28300287a3...` | `sha256:ef28300287a3...` |
| `build_info.json` `nintent_commit` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | same | same |
| `build_info.json` `nauto_commit` | `2635e648469d6e6bad87af113f7427b878b0a387` | same | same |
| `intent_sources.yaml.sha256` | `598391e0...455b` | same | same |

All three report the identical image ID and identical embedded revision/YAML digests — the
Section 5.1 image-parity requirement holds live, not just in the disposable triplet.

- `nautobot-server showmigrations nautobot_intent_catalog` (web): ends at
  `0016_remove_reconciliation_dashboard_surfaces`, unchanged from live pre-deployment.
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run` (web): `No changes
  detected`, exit 0.
- Installed `nautobot-intent-catalog` `direct_url.json` (web): `vcs_info.commit_id` =
  `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`, matching `build_info.json`.
- `settings.PLUGINS_CONFIG` (web): `{'intent_sources_file': '/opt/nautobot/intent_sources.yaml'}` —
  the explicit, identical canonical path is live in the App config, not just present as a file.

## 5. nauto Job sync and discovery (plan items 7-8)

`.local/interface-contract/p4/20260726_step5/job_discovery.txt` (before sync) showed the nauto
`GitRepository` named `main` at `current_head = 251b056549f1b01f604b42b486fdc12d667db521` — a
commit several revisions behind the approved `2635e648469d6e6bad87af113f7427b878b0a387`, which was
independently confirmed to equal `origin/main` via a local `git fetch` of the `nauto` submodule.
This matches the staleness problem already flagged in plan Section 3.3; it was not a new drift.

After the explicitly approved `nautobot-server runjob -u admin -d
'{"repository": "7c7000bc-46b0-4d9b-aabc-9055441cb452"}' nautobot.core.jobs.GitRepositorySync`:

- `GitRepository.current_head` = `2635e648469d6e6bad87af113f7427b878b0a387` — matches the approved
  tuple exactly (`git_sync_after.txt`).
- Job log: "Generate Desired Services: Marking Job record as no longer installed" — expected, since
  Phase 1 removed nauto's duplicate desired-state writer; its Job class no longer exists at
  `2635e64`.
- No `Seed Home Cluster` or `Ingest Nodeutils Inventory` run occurred — the sync only refreshes the
  Git checkout and Job/GraphQL-query/config-context registrations, per its own log output ("main:
  Data refresh from main complete!"), not their job classes' `run()` bodies.
- Exactly three `nautobot_intent_catalog.jobs` entries have `installed=True`: `Import Intent
  Sources`, `Analyze Intent Sources`, `Reconcile Desired IPAM Intent`. All other
  `nautobot_intent_catalog.jobs` records (`Evaluate Service Intent`, `Export Production Inventory`,
  etc.) remain `installed=False`, matching the plan's expected Job set.
- `installed=True` nauto Jobs: `AI Resource Review`, `Ingest Nodeutils Inventory`, `Seed Home
  Cluster` — matching Section 4.2's retained JobHook/Job expectations.

## 6. Write-attribution check for the sync (plan gate: "live row fingerprints unchanged")

```sql
select oc.action, ct.app_label, ct.model, count(*)
from extras_objectchange oc join django_content_type ct on ct.id = oc.changed_object_type_id
where oc.time > '2026-07-25 18:31:33'
group by 1,2,3;
```

Result: `update extras gitrepository 1`, `update extras job 4` — exactly the `GitRepository` row
itself plus the four Job records the sync log named as refreshed/marked-uninstalled. Zero rows
touched in any `nautobot_intent_catalog` desired/actual/Braindump/Alignment Review table.
`extras_objectchange` total rose from 893 to 898 (+5, exactly these five rows); `intentsource`,
`desirednode`, and `dcim_device` counts are unchanged at 2/5/5.

## 7. Read-only smoke (plan item 9)

`.local/interface-contract/p4/20260726_step5/readonly_smoke.txt`:

- `nautobot-server health_check`: `DatabaseBackend`, `DefaultFileStorageHealthCheck`,
  `MigrationsBackend`, `RedisBackend` all `working`.
- `nautobot-server check --deploy`: the same 4 `security.W00x` warnings as every prior disposable
  run (`W004`, `W008`, `W012`, `W016`); no new issue.
- GraphQL (`graphql_check.txt`): `{ desired_nodes { id name } }` returns the expected 5 rows
  (`agbach`, `agdnsmasq`, `aghub`, `agpc`, `agstudio`); `{ intent_sources { id } }` correctly errors
  with `Cannot query field 'intent_sources' on type 'Query'.` — the IntentSource GraphQL root
  remains absent live, matching Phase 2's contraction.
- REST route matrix (live, via a real superuser token):

  | Route | Status |
  |---|---:|
  | `nodes/` | 200 |
  | `braindumps/` | 200 |
  | `alignment-reviews/` | 200 |
  | `desired-services/` | 404 |
  | `desired-endpoints/` | 404 |
  | `desired-compute-platforms/` | 404 |
  | `desired-compute-instances/` | 404 |

  Exactly the three retained collections respond; all four removed families 404 live, not just in
  the disposable proof.

## 8. Final fingerprint and active-Job recheck

Post-smoke: `intentsource=2`, `desirednode=5`, `dcim_device=5`, `extras_objectchange=898`
(unchanged since the approved sync) — no additional write occurred from the read-only GraphQL/REST
probes. `extras_jobresult` `PENDING`/`RUNNING` count: 0.

## What Step 5 does not close

- No Import/Analyze/IPAM apply ran — writes remain frozen; only the approved `GitRepositorySync`
  Job executed, and it touched no nintent-owned row.
- Routine nctl mutation and VM Phase 3 seed work remain paused (unchanged from Step 4).
- Step 6 (official live YAML preview, `apply=false`) has not been run.

## Evidence retention

`.local/interface-contract/p4/20260726_step5/` (directory mode `0700`, files mode `0600`):
`maintenance_start.txt`, `pre_swap_fingerprint.txt`, `deploy_verification.txt`,
`git_sync_before.txt`, `git_repo_sync.log`, `git_sync_after.txt`, `job_discovery.txt`,
`graphql_check.txt`, `readonly_smoke.txt`. No token, credential, private prose, or raw
ObjectChange payload appears in any evidence file — only aggregate counts, route names, schema
fields, and public revision hashes. Not committed (matches Section 5.5).

## Verification

- `docker inspect --format '{{.Image}}'` identical across all three live containers.
- `build_info.json`/`intent_sources.yaml.sha256` identical across all three live containers.
- `makemigrations --check --dry-run`: clean; `showmigrations`: ends at `0016`.
- `GitRepository.current_head` after sync == approved `2635e648469d6e6bad87af113f7427b878b0a387`
  == local `git fetch origin main` result for the `nauto` submodule.
- Exactly 3 `nautobot_intent_catalog` Jobs `installed=True`; expected nauto Jobs `installed=True`.
- `extras_objectchange` diff since Step 4 baseline is exactly the sync's own 5 bookkeeping rows;
  `intentsource`/`desirednode`/`dcim_device` counts unchanged throughout.
- GraphQL/REST live route matrix matches the frozen Phase 2 contract exactly.
- `extras_jobresult` active/pending count is 0 before and after.

Next: Step 6 (run the official live YAML preview with `apply=false` and obtain separate apply
approval) — a further live-adjacent step requiring its own explicit operator approval per plan
Section 3.4.
