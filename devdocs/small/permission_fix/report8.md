# Permission Fix Step 8 Report: Ownership and Repeatability Proof

Date: 2026-07-23

## Status

**Complete. `aghub` proven repeatable with no ownership drift.**

## Method

Captured full ownership/mode state on `aghub` after Step 7's live apply (the "before" baseline for
this step), then ran a second full collection (`ansible-playbook run_nodeutils_collect.yml
-e target_hosts=aghub -e nodeutils_version=<pinned SHA>`, i.e. a second `uv sync --frozen` plus a
second `nodeutils collect` through the same helper/sudoers boundary), then captured the same state
again and diffed.

## Before/after comparison

```text
/opt/nodeutils                          eiji:root 755   (unchanged)
/opt/nodeutils/.venv                    eiji:eiji 755   (unchanged)
/var/lib/nodeutils                      eiji:root 700   (unchanged)
/var/lib/nodeutils/inventory.json       eiji:eiji 600   (unchanged; mtime advanced -- fresh report)
/usr/local/libexec/nodeutils-pvesh-read root:root 755   (unchanged)
/etc/sudoers.d/nodeutils-pvesh          root:root 440   (unchanged)
checkout HEAD                           36e1c5752ba895780eea21b8e994926b93cc1c53 (unchanged, still pinned)
```

`find /opt/nodeutils -not -user eiji` and `find /var/lib/nodeutils -not -user eiji` both returned
empty before and after — no root-owned descendant exists in either directory at any point.

The only difference between the two captures is `inventory.json`'s modification time, which
advanced from the second collection writing a fresh report — expected, and not an ownership
regression.

## Requirements checked

- **No new root-owned descendant** in checkout, `.venv`, config, cache, or report paths — confirmed
  by the empty `find ... -not -user eiji` results both times.
- **Report owner remains `nodeutils_user`** — `inventory.json` stayed `eiji:eiji 0600` across both
  collections.
- **A second `uv sync --frozen` succeeds as `nodeutils_user`** — part of the same
  `run_nodeutils_collect.yml` run; the play recap showed `failed=0` and the `Sync nodeutils
  dependencies with uv` task is `changed_when: false` (ran cleanly, no drift).
- **A second collection succeeds without ownership repair** — the play's Step 3 post-collection
  ownership assertions (added specifically to fail loudly on a root-owned leak rather than silently
  `chown` it) passed on both runs with no remediation task ever invoked; there is no `chown` task in
  the play at all, by design.
- **Helper/sudoers ownership and modes remain unchanged** — `root:root 0755` and `root:root 0440`
  respectively, identical before and after.

## Definition of Done cross-check

Revisiting `plan_pvesh.md`'s Definition of Done against Steps 0-8:

- allowlisted helper and sudoers boundary implemented and tested — Steps 1, 5, 6.
- generic non-Proxmox collection unchanged — Step 2 test
  `test_auto_mode_skips_non_proxmox_host` plus Step 3's role no-op path for non-Proxmox hosts.
- nodeutils and Ansible tests pass from documented working directories — Step 5
  (`nodeutils`: 31 passed; `nctl`: 964 passed, 1 pre-existing warning;
  `ansible-playbook --syntax-check`: clean).
- exact committed/pushed nodeutils SHA deployed — Step 4/6/7/8: `aghub` checked out at
  `36e1c5752ba895780eea21b8e994926b93cc1c53`, pushed to `origin/main`, matching the superproject
  gitlink and `resolve_nodeutils_version()`.
- live positive and negative privilege checks pass — Step 6.
- `aghub` produces and ingests a fresh schema-v2 report — Steps 6 and 7.
- the original `no_realized_object`, `no_realized_device`, and `missing_actual_node` findings are
  resolved — Step 7: `aghub` drift shows `converged` with zero error/warning findings.
- a fresh drift and no-repeat round prove the supported control loop — Step 7.
- no root-owned nodeutils checkout, virtualenv, config, cache, or report artifact created — this
  step.
- operation artifacts contain no secrets — Step 6's secrets grep.
- the implementation report distinguishes Proxmox completion from unrelated cluster drift — Step 7
  explicitly calls out `agbach`/`dnsmasq` as separate, pre-existing, unrelated drift.

All Definition of Done items are satisfied. The plan (`devdocs/small/permission_fix/plan_pvesh.md`)
is complete for the Proxmox `pvesh` permission fix on `aghub`.

## Outstanding items not in scope of this plan

Per `report1.md`'s "Remaining work" (items 3-4) and this plan's own scope note, the following were
already resolved separately and are not part of this plan:

- The two previously replayed `aghub` IPAM Job results were reviewed in Step 0 of this plan and
  found to need no remediation (idempotent create/conflict pair).
- Controller-local legacy dump quarantine (`agstudio`) was resolved in `report2.md` (superseded
  report, moved to `oldreport/`).

Nothing else from the original `problem.md` remains open.
