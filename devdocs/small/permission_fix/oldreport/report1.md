# Permission Fix Investigation Report 1

Date: 2026-07-23

## Status

**Partially complete.**

- The original Proxmox failure on `aghub` is confirmed but not fixed:
  `pvesh` still requires root while the collection task runs as `nodeutils_user`.
- The unrelated agpc stale-nodeutils problem is resolved live.
- Two workflow defects that could recreate collector/reader skew were fixed in the current nctl
  worktree and verified locally and on agpc.
- The changes are not committed or pushed.

## Corrected diagnosis

`agpc` is Ubuntu 24.04.4, has neither `/etc/pve` nor `pveversion`, and nodeutils reports Proxmox
`detected=false`. It never enters the failing `pvesh` path.

Before repair:

- remote `/opt/nodeutils`: `95a2dfcd4fead2d44358351f3d6793b4f8465135`
  (`p4s2`, 2026-07-16);
- superproject/GitHub nodeutils commit:
  `e7b91860397abddee07801b438914e59e734ce57`;
- remote `/var/lib/nodeutils/inventory.json`: `nodeutils.inventory.v1`;
- controller `/var/lib/nodeutils/agpc.json`: `nodeutils.inventory.v1`;
- last successful agpc collection: 2026-07-22 00:41 JST, before the v2 commit
  `09d9227018711a9a78c7dea20e5f9c231ad41a50` at 12:20 JST.

The earlier agpc `Missing sudo password` failure no longer reproduces: current Ansible normal-user
execution and vault-backed root become both succeed.

## Workflow defects

### 1. Mutable collector version

The Ansible playbook defaulted `nodeutils_version` to `HEAD`. The supported nctl observation path
did not override it, so upstream nodeutils could advance to a new schema independently of the
local nctl reader.

### 2. No explicit refresh for a converged host

After agpc SSH enrollment, a normal dry run returned:

```text
scope: agpc
state: planned
scope summary: converged=1
```

It planned no `observe_node` action. Therefore `nctl reconcile agpc --yes` would not update
nodeutils or replace the v1 report when drift was already considered converged.

### 3. SSH enrollment was a missing prerequisite, not an update defect

The nctl-managed alias for agpc was absent. Strict SSH correctly rejected the production
inventory, while the ordinary `~/.ssh/known_hosts` entry matched all currently offered agpc keys.
The alias was enrolled with:

```bash
uv run --project nctl nctl ssh enroll agpc --from-known-hosts --yes
```

This remains an explicit verified trust operation; no automatic or unverified key acceptance was
added.

## Implemented changes

### Reproducible nodeutils deployment

- Added `nctl_core.repo_versions`.
- Resolve the `nodeutils` gitlink from the superproject `HEAD`, not the submodule working-tree HEAD.
- Allow a packaged controller to provide only a full 40- or 64-character Git object ID through
  `[reconcile].nodeutils_version`.
- Fail before Ansible when the pinned version cannot be resolved; never fall back to `HEAD`.
- Pass `nodeutils_version=<full SHA>` to `run_nodeutils_collect.yml`.
- Record the resolved SHA in `collection_started` and the observation action result.

### Explicit observation refresh

Added:

```bash
nctl reconcile HOST --refresh-observation
nctl reconcile HOST --refresh-observation --yes
```

The flag:

- requires host scope;
- adds one forced `observe_node` action even if drift is converged;
- records `evidence.forced_refresh=true` in the plan;
- applies only to round 0, avoiding an infinite refresh loop; and
- uses the normal SSH preflight, collection, validation, cache, ingest, production regeneration,
  and fresh-drift workflow.

### Documentation and remediation

- Corrected the quick guide: dry reconcile reads and plans but does not run nodeutils.
- Documented first-time verified SSH enrollment.
- Documented the pinned collector contract and refresh command.
- Expanded `ssh_host_key_unenrolled` remediation to name `--from-known-hosts`/`--fingerprint`
  verification and the required `--yes` apply step.
- Corrected `problem.md` so agpc and controller-local legacy dumps are not attributed to `pvesh`.

## Automated verification

Focused tests cover:

- gitlink SHA resolution;
- rejection of a non-gitlink and non-full override;
- propagation of the pinned SHA into Ansible and operation evidence;
- forced observation planning for an already-converged host;
- exactly one forced observation followed by normal convergence; and
- rejection of cluster-wide refresh without a host.

Final test result:

```text
963 passed, 1 warning
```

The warning is the pre-existing Starlette/httpx deprecation warning in `test_serve_ws.py`.
`git diff --check` and Python bytecode compilation also passed.

## Live verification

### Dry plan

Operation `01KY6ZMJ9CCKJFFRYVV29D2Y41`:

- scope: agpc;
- `ssh_preflight: ready=[agpc]`;
- one `observe_node` action despite `scope summary: converged=1`;
- `evidence.forced_refresh=true`;
- no writes.

The resolved collector commit was:

```text
e7b91860397abddee07801b438914e59e734ce57
```

### First apply and infrastructure interruption

Operation `01KY6ZMQ39ABH8SARYGRP618P5` successfully:

- updated remote `/opt/nodeutils` to the pinned commit;
- generated remote schema v2;
- retrieved and validated the report; and
- atomically replaced controller `/var/lib/nodeutils/agpc.json` with schema v2.

The Nautobot ingest Job remained `PENDING` for 300 seconds because the healthy-looking worker was
not consuming Redis's `default` queue. The operation truthfully ended `non_converged`; its
observation action retained:

- `collected=true`;
- the pinned nodeutils SHA;
- the cache path; and
- the Job timeout error.

The Nautobot worker container was restarted. It drained the queue, and the agpc ingest completed
with `updated=1`.

Operational side effect: two previously queued aghub IPAM Jobs were also consumed. One created the
192.168.0.10 IP record; the other reported a duplicate uniqueness conflict. aghub state should be
reviewed separately.

### Successful bounded replay

Operation `01KY700E999CA4KDRRQ98745DH` completed:

```text
state: converged
ssh_preflight: ready=[agpc]
[ok] observe_node
[ok] regenerate_production_inventory
```

Action evidence:

- `nodeutils_version`:
  `e7b91860397abddee07801b438914e59e734ce57`;
- `collected=true`;
- `ingest_outcome=updated`;
- no host or pipeline error.

Post-run state:

- remote checkout matches the superproject pin;
- remote report is `nodeutils.inventory.v2`;
- controller `agpc.json` is `nodeutils.inventory.v2`; and
- `nctl drift --host agpc` reports `converged`.

## Remaining work

1. Design and implement the Proxmox privilege boundary without leaving root-owned checkout,
   virtualenv, cache, config, or report files that break later non-root steps.
2. Add the missing `permission_fix/plan.md` before changing the `aghub` playbook execution user.
3. Review the two replayed aghub IPAM Job results.
4. Decide how to quarantine or retire controller-local legacy dumps. In particular,
   `/var/lib/nodeutils/inventory.json` still identifies `agstudio.local` and remains schema v1, so
   it continues to appear in `sources.observed_errors` even though agpc is converged.
