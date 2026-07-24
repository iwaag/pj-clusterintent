# Phase 2 Sidefix2 Step 6 Report: Review, Commit, and Deploy nauto

Status: deployed. The reviewed/tested `nauto` revision is now the installed Job revision in the
local Nautobot instance. No persistent virtualization ingest has run.

This report covers [`plan.md`](plan.md) Step 6 ("Review, commit, and deploy nauto").

## 1. Commit granularity and review (plan Step 6.1-6.2)

Following the precedent set by sidefix1 `report6.md` (one commit per plan step rather than a
single squashed commit, so each step's diff and its own report/verification stay independently
reviewable), `nauto` carries three sidefix2 commits on top of the sidefix1 baseline (`1d2052c`):

```
c62e707 vm p2 sidefix2 step 3: merge guest counts/changed_fields only after savepoint success
3da5d56 vm p2 sidefix2 step 1+2: Namespace/host-aware IP resolution and desired-set convergence
e86b559 vm p2 sidefix2 step 0: reproduce Namespace/host IP-matching and count-leak defects
```

Full-diff review at `HEAD` (`git diff 1d2052c..HEAD --stat`):

```
jobs/ingest_nodeutils_inventory.py        |  76 +++++++-
jobs/proxmox_interfaces.py                | 131 ++++++++++---
jobs/proxmox_upsert.py                    |  42 +++-
tests/test_ip_namespace_host_identity.py  | 313 ++++++++++++++++++++++++++++++
tests/test_proxmox_interface_ip_upsert.py |  83 +++++++-
5 files changed, 589 insertions(+), 56 deletions(-)
```

Re-verified clean at `HEAD` immediately before push:

```
cd nauto
python3 -m unittest discover -s tests
# Ran 101 tests in 0.009s, OK
python3 -m py_compile jobs/*.py
# no output (success)
git diff --check
# no output (success)
git status --short
# (empty)
```

## 2. Push (plan Step 6.4)

Per `.local/localenv_memo.md` ("pushはユーザーに依頼する前提で進める"), pushing is the user's own
action, never automatic. The user pushed `nauto`, `nctl`, and the superproject themselves;
`git fetch origin && git status -sb` in all three repositories showed `## main...origin/main` with
no ahead/behind marker afterward, confirming `origin/main` matches local `HEAD` exactly in each.

## 3. Nautobot Git Repository sync (plan Step 6.5)

`POST /api/extras/git-repositories/7c7000bc-46b0-4d9b-aabc-9055441cb452/sync/` (the tracked `main`
repository, `https://github.com/iwaag/nauto`) completed `SUCCESS` on the first attempt — no worker
restart was needed this time (unlike sidefix1 Step 6, where a stale Celery consumer required
`docker restart nautobot-nautobot-worker-1`). `current_head` moved from the pre-sidefix2 pin
`1d2052ce469fe0ee03d554ed069c7a03fa198053` to `c62e7070a67a933617479283be6816a39107812b`, matching
local `nauto` `HEAD` exactly.

## 4. Installed revision confirmation (plan Step 6.6)

`GET /api/extras/jobs/?name=Ingest%20Nodeutils%20Inventory` confirms the `Ingest Nodeutils
Inventory` Job is `"installed": true, "enabled": true`, with `last_updated` matching the sync
timestamp. No other Job registration changed.

## What this step does not cover

- No dry-run or apply execution of `Ingest Nodeutils Inventory` through the deployed Job
  registration — that is Step 7 (resuming sidefix1 Step 7 / Phase 2 Step 9), which remains gated
  behind its own separate approval per Section 3.3/Section 8 of `plan.md`.
- No Proxmox, `aghub`, or unrelated Nautobot ledger row changed by this step; only the Git
  Repository sync (pulls source into Nautobot's Job registry) occurred.

## Gate

The deployed Job is byte-for-byte the reviewed revision: proven (`current_head` == local `nauto`
`HEAD` == `c62e7070a67a933617479283be6816a39107812b`, `installed`/`enabled` both `true`). No
persistent virtualization ingest has yet run.
