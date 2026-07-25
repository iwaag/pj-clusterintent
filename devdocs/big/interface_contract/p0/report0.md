# Phase 0 Step 0 — Establish the evidence boundary and recapture the baseline

Parent: [plan.md](plan.md), Step 0.

Private evidence directory: `.local/interface-contract/p0/20260725T122031Z/` (mode `0700`, files
`0600`).

Timestamp: `2026-07-25T12:20:38Z` (2026-07-25 21:20 JST). Documents reviewed per plan §4 recorded in
`00_timestamp_and_docs.txt`.

## Revisions and dirty state

| Repository | Revision | Branch | State |
|---|---|---|---|
| superproject | `d73ea3d0937407d3a0d1de8b3bd743ec6907c234` | `main` | dirty: one untracked path, `devdocs/big/interface_contract/p0/` (this plan's own directory; not an overlapping edit) |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | `main` | clean |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | `main` | clean |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | `main` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `main` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `main` | clean |

All revisions match the plan §4.1 planning-time snapshot exactly. The single untracked path is this
plan's own report directory, not an overlapping change, so no ownership/overlap decision is
required. Gate condition (no unexplained dirty change / no mixed installed nintent revision) is
satisfied.

## Installed nintent revision (per container)

`pip freeze | grep nprojects` inside each Nautobot container independently:

| Container | Installed nintent revision | Package version |
|---|---|---|
| `nautobot-nautobot-1` (web) | `c343c5a56047b0df9ad901dd4459863ef1954053` | `nautobot-intent-catalog` 0.9.0 |
| `nautobot-nautobot-worker-1` | `c343c5a56047b0df9ad901dd4459863ef1954053` | `nautobot-intent-catalog` 0.9.0 |
| `nautobot-nautobot-scheduler-1` | `c343c5a56047b0df9ad901dd4459863ef1954053` | `nautobot-intent-catalog` 0.9.0 |

All three match the checked-in `nintent` submodule pointer exactly. No mixed revision. Container
image IDs and creation timestamps differ slightly between web (`sha256:bde75...`, created
2026-07-25T11:14:06Z) and worker/scheduler (`sha256:7cc4a...` / `sha256:909f8...`, created
2026-07-25T11:02:19Z), but the installed application package revision is identical across all
three, so this is not a mixed-revision condition.

## Platform versions and migrations

- Nautobot `3.1.3`, Django `5.2.14`.
- PostgreSQL `15.17` (`my_postgres_db`, external container per `.local/localenv_memo.md`).
- `nautobot_intent_catalog` migrations applied through `0016_remove_reconciliation_dashboard_surfaces`
  — matches the roadmap's expected baseline exactly (0001–0016, all `[X]`).

## Container/service health

`docker ps`: `nautobot-nautobot-1`, `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1`
all `Up About an hour (healthy)`. No rebuild or restart performed. (Unrelated host containers for
other local projects — `hatchet-*`, `keycloak`, `minio`, `gitea`, `portainer`, etc. — are also
running but out of scope and unmodified.)

## Jobs, JobHooks, ScheduledJobs, JobResults

Read via `nautobot-server shell --command` (read-only ORM query, no mutation):

- Registered `nautobot_intent_catalog.jobs` classes: 11 total, of which 4 are `installed=True`
  (`Analyze Intent Sources`, `Import Intent Sources`, `Preview Intent Source Analysis`,
  `Reconcile Desired IPAM Intent`) and 7 are `installed=False` stale Job records with no matching
  current source class (`Evaluate Endpoint/Node/Service Intent`, `Export Ansible Hosts Intent`,
  `Export Production Inventory`, `Export dnsmasq Records`, `Sync Deployment Profiles`) — carried
  forward to Step 1 classification, not resolved here.
- `JobHook`: one, `AI Resource Auto Review`, `enabled=True`, bound to Job `AI Resource Review` —
  matches the roadmap's explicit-deferral baseline.
- `ScheduledJob`: none.
- Most recent 15 `JobResult` rows: last activity `2026-07-24 18:31:33 UTC` (`AI Resource Review`,
  `SUCCESS`), i.e. ~18 hours before this audit's timestamp. No `JobResult` was created during or
  after evidence capture.
- Currently `PENDING`/`RUNNING` `JobResult` count: **0**.

## GitRepository (nauto Job/seed source)

One `GitRepository` named `main`, remote `https://github.com/iwaag/nauto`, branch `main`,
`current_head = 251b056549f1b01f604b42b486fdc12d667db521` — matches the checked-in `nauto`
submodule pointer exactly.

## Non-mutation confirmation

Only read commands were used: `git status`/`rev-parse`/`branch`/`remote` (superproject and every
submodule), `docker ps`/`inspect`/`exec pip show|freeze`, `nautobot-server --version`,
`nautobot-server showmigrations`, and `nautobot-server shell --command` running only Django ORM
`.objects.filter()/.all()/.count()` reads. No REST mutation, Job run, migration, rebuild, or
restart occurred.

## Gate

All evidence is tied to one exact repository/live tuple: superproject `d73ea3d0`, five submodules
each matching their installed/deployed revision, Nautobot `3.1.3` at migration `0016`, nintent
`c343c5a5` installed identically on web/worker/scheduler, zero running Jobs, and the `nauto`
GitRepository pointer matching the checked-in submodule. No unexplained dirty change or mixed
installed nintent revision. Proceeding to Step 1.
