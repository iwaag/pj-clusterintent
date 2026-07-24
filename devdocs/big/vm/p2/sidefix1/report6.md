# Phase 2 Sidefix1 Step 6 Report: Review, Commit, and Deploy nauto

Status: deployed. The reviewed/tested `nauto` revision is now the installed Job revision in the
local Nautobot instance. No persistent virtualization ingest has run.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 6 ("Review, commit, and deploy
nauto").

## 1. Commit granularity (fixplan Step 6.1-6.2)

`problem_fixplan.md`'s own wording asks for "one reviewable blocker-fix commit." This project's
established convention (confirmed by `git log` before Phase 2/sidefix1 and reused for Steps 0-5 of
this fix) is one commit per plan step instead, so the reader can follow each step's diff and
verification independently. Squashing the four already-made `nauto` commits (Steps 0-3) would mean
rewriting already-reviewed history. Asked the user directly; the decision was to keep the four
step commits as-is rather than rewrite history, and push them together as a set — matching how
Steps 1-7 of the parent `plan.md` phase were pushed and reviewed in `report2.1.md`-`report2.7.md`.

`nauto` `HEAD` after Steps 0-3:

```
1d2052c vm p2 sidefix1 step 3: sanitize preview-created Cluster ids
b5026e7 vm p2 sidefix1 step 2: remove the dry_run early return, add new-device precondition
189df05 vm p2 sidefix1 step 1: centralize preview ownership, remove lower-level dry_run suppression
b30a8b7 vm p2 sidefix1 step 0: red test reproducing the dry-run Proxmox early-return blocker
```

Each commit's own diff and the Steps 4-5 real-ORM evidence (`report4.md`, `report5.md`) together
constitute the review this step required.

## 2. Push (fixplan Step 6.3)

Per this project's standing practice (`.local/localenv_memo.md`: "pushはユーザーに依頼する前提で進める"),
pushing is the user's own action, never automatic. The user pushed the four commits themselves;
`git fetch origin && git log --oneline @{u}..HEAD` in `nauto` showed zero unpushed commits
afterward, confirming `origin/main` now matches local `HEAD` (`1d2052ce469fe0ee03d554ed069c7a03fa198053`)
exactly.

## 3. Nautobot Git Repository sync (fixplan Step 6.4)

`POST /api/extras/git-repositories/<id>/sync/` was issued against the tracked `main` repository
(`https://github.com/iwaag/nauto`). The resulting job stayed `PENDING` — a stale Celery consumer
issue in this dev container unrelated to `nauto`'s own code (the worker had been idle since an
earlier session and stopped consuming its `default` queue; `celery inspect active_queues` showed
it correctly bound, but no task logs appeared for several minutes). A `docker restart
nautobot-nautobot-worker-1` (a container-level operation, not a data change) cleared this; the
worker immediately consumed the pending sync task and it completed `SUCCESS`. `current_head` moved
from the pre-sidefix1 pin `4cea3b68b1bc766aedf75d8ea166b0e68d735bc2` to
`1d2052ce469fe0ee03d554ed069c7a03fa198053`, matching local `nauto` `HEAD` exactly.

## 4. Installed revision confirmation (fixplan Step 6.5)

`GET /api/extras/jobs/?name=Ingest%20Nodeutils%20Inventory` confirms the `Ingest Nodeutils
Inventory` Job is `"installed": true, "enabled": true` at the freshly-synced revision. No other
Job registration changed.

## What this step does not cover

- No dry-run or apply execution of `Ingest Nodeutils Inventory` through the deployed Job
  registration — that is fixplan Step 7 (resuming Phase 2 Step 9), which remains gated behind its
  own separate approval per Section 3.3/Section 8.
- No Proxmox, `aghub`, or unrelated Nautobot ledger row changed by this step; only the Git
  Repository sync (pulls source into Nautobot's Job registry) and a worker container restart
  occurred.

## Gate

The deployed Job is the exact reviewed revision: proven (`current_head` == local `nauto` `HEAD` ==
the four sidefix1 Step 0-3 commits, `installed`/`enabled` both `true`). No persistent
virtualization ingest has yet run.

Step 6 is satisfied. Proceeding to Step 7 (resume Phase 2 Step 9: live dry-run preview, review,
separate approval, then apply) remains gated behind its own explicit approval gates per the
fixplan.
