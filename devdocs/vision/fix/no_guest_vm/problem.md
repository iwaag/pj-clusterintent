# Problem: a guest created by a reconcile that died mid-observation can never be reconciled again

Recorded 2026-08-10 (JST) from the incident in
[`unshackle_agent/clusterintent/turn2/report.md`](../../../../../devdocs/episodes/unshackle_agent/clusterintent/turn2/report.md)
(F3), where LXC VMID 110 `agdoomed1` on aghub had to be destroyed by hand with
`sudo /usr/sbin/pct destroy 110` because no `nctl` command could reach it.

## Overview

`nctl reconcile` creates a Proxmox guest, then links it to its
`DesiredComputeInstance` as a side effect of the post-actuation observation
round. If that round does not complete, the guest exists on the hypervisor and
does not exist in Actual State. Every subsequent reconcile then plans nothing
but `observe_node`, and `observe_node` is gated on the guest answering SSH —
which a bare template guest does not do.

**The failure disables its own cure.** There is no supported command that
destroys, links, or forgets the guest. It becomes hypervisor-only residue that
drift reports forever.

This is not a new problem. It has been patched at least once before, at the
symptom (see "Evidence of recurrence"), and the patch does not cover the case
where the create landed in an *earlier* operation.

## Reproduction

Observed exactly, 2026-08-09/10:

1. `nctl reconcile agdoomed1 --yes` creates the guest. The compute action
   returns `{"created": true, "started": true}` (operation
   `01KZMTTEEX0GENS5XMX0VN3DBZ`, event 4).
2. The operation proceeds to post-actuation observation, runs the nodeutils
   collection, retrieves reports, starts the Nautobot Job
   `Ingest Nodeutils Inventory`, and polls it — events 9–16 are all
   `job_poll: status: pending`.
3. The controlling process is killed during that polling. (Here it was
   OpenCode's 120 s shell timeout, but any interruption does it — Ctrl-C, a
   dropped SSH session, a laptop lid.)
4. The ingest never lands in Actual State. Verified before the guest was
   removed: `nctl actual --json --detail` listed guests 100–109 under both
   `clusters/guests` and `facts_raw/proxmox/lxc_containers`, and **not 110** —
   while `nodeutils-pvesh-read /nodes/aghub/lxc` on aghub showed VMID 110
   `agdoomed1` `status: running`.

From then on, with desired state already `lifecycle: retired` /
`desired_presence: absent`:

```
$ nctl reconcile agdoomed1 --allow-destroy --yes
state: failed
error [ssh_host_key_unenrolled]: unenrolled SSH host(s): agdoomed1
```

and `plan.json` contains **one** action, `observe_node`. No destroy action was
ever planned.

```
$ nctl reconcile agdoomed1 --yes          # try to re-observe instead
error [ssh_host_key_unenrolled]: unenrolled SSH host(s): agdoomed1

$ nctl ssh enroll agdoomed1 --from-known-hosts
error[ssh_probe_failed]: ssh-keyscan timed out after 10.0s for agdoomed1.local:22
```

The guest is a bare `ubuntu-22.04-standard` LXC. It has no sshd answering, and
it never will, because it was created to be thrown away.

## The dead-end loop

```
create succeeded ──▶ observation round died ──▶ VM absent from Actual State
      ▲                                                    │
      │                                                    ▼
      │                                    _match_instance finds no candidate
      │                                    → compute_instance_missing
      │                                    → no destroy_required disposition
      │                                    → no destroy action planned
      │                                                    │
      │                                                    ▼
      └──── cannot re-observe: observe_node is SSH-gated on the guest,
            and the guest cannot be enrolled (no sshd)
```

## Root cause

### 1. One fact is hand-copied into three places

"Which hosts does this action actually connect to over SSH?" is decided by each
action's `execute()`. Three separate hand-maintained structures re-state it, and
nothing asserts they agree:

| # | Location | What it hand-encodes |
|---|---|---|
| ① | [`ssh_preflight.py:49`](../../../../nctl/src/nctl_core/reconcile/ssh_preflight.py#L49) `SSH_REQUIRING_RECONCILER_IDS` | which reconcilers need SSH at all |
| ② | [`ssh_preflight.py:89`](../../../../nctl/src/nctl_core/reconcile/ssh_preflight.py#L89) `action_host_slugs()` | which hosts one action touches — falls back to `targets` when `host_slugs` is unset |
| ③ | [`planner.py:233`](../../../../nctl/src/nctl_core/reconcile/planner.py#L233) `compute_transition_target_slugs` | which targets to suppress `observe_node` for |

`ssh_preflight.py`'s own module docstring states the correct principle —
*"Ledger-only reconcilers … never touch a physical node over SSH, so hosts
touched only by those actions are excluded"*. The principle is right. The
membership is wrong, because there is no single place for the knowledge to live.

### 2. `destroy_compute_instance` is gated on a host it never contacts

① includes `destroy_compute_instance`.
[`plan_destroy_compute_instance`](../../../../nctl/src/nctl_core/reconcile/reconcilers.py#L193)
builds the action with `targets=[target]` — the **guest** — and sets no
`host_slugs`, so ② returns the guest's slug.

But [`compute_destroy.py:41,56`](../../../../nctl/src/nctl_core/reconcile/actions/compute_destroy.py#L41-L56)
runs the playbook with `--limit control_host`, where
`control_host = action.parameters["control_desired_node_slug"]` — the
hypervisor. **The destroy path never opens an SSH connection to the guest.**

This is latent for normal guests, which are enrolled anyway because they were
real service hosts. It bites exactly on the guests you most want to destroy:
throwaways, and guests that never finished coming up.

### 3. There is no "actuated but unlinked" state

`create_compute_instance` succeeds on its own terms. The link is produced by a
later, separate round. Nothing records "I created this and then lost track of
it", so a subsequent reconcile cannot distinguish a guest that was never created
from one that was created and orphaned. Both look like `missing_actual_node` +
`compute_instance_missing`.

### 4. There is no observation path that does not go through the guest

`snapshot.actual.virtual_machines` is populated only by the nodeutils collection
+ Nautobot ingest. The hypervisor already exposes the guest list through the
existing privileged read helper — `nodeutils-pvesh-read /nodes/aghub/lxc`
returned VMID 110 correctly throughout this incident. That view is not usable as
a linking source, so a guest that cannot be reached directly cannot be linked
even though the hypervisor can see it perfectly.

### 5. The operation ledger cannot tell you any of this happened

`nctl ops` has only `list` and `show`; nothing can close an operation whose
process died. Operation `01KZMTTEEX0GENS5XMX0VN3DBZ` is still recorded
`state: running`. It is not alone — at the time of writing there are ten or more
such records going back to 2026-07-29, including one left by an
`nctl ssh enroll` that returned a clean error and exited. So "did that reconcile
finish?" has no in-system answer, and the orphaned guest has no in-system
signal.

## Evidence of recurrence

Commit **`b93b3b0` "Defer observation until compute link completes"**
(2026-07-29, `nctl` submodule) is the same bug, patched at the symptom:

```diff
-        if action.reconciler_id == "create_compute_instance" ...
+        if action.reconciler_id in {"create_compute_instance", "link_compute_realization"}
```

Seven lines in `planner.py`, plus a test. The comment immediately above it
already describes today's incident: *"an initial observe action for the same
node would fail before creation and make a valid dry create plan
unexecutable."*

The shape of that fix is **"add one more id to a hand-written set"** — structure
③ above. It only helps when the create action is present in the *same* plan.
Once the create has landed in an earlier operation, there is no create action to
suppress against, `observe_node` is planned, and the preflight kills it.

That is why this keeps coming back: each occurrence is repaired where it was
seen, the sets grow, and nothing checks the sets against reality.

## Proposed solution

Smallest first. A and B are cheap and independent; C is a design question.

### A — point the destroy gate at the host it actually uses

In `plan_destroy_compute_instance`, set
`parameters["host_slugs"] = [control_desired_node_slug]`. `action_host_slugs()`
already prefers `host_slugs` over `targets`, so ② starts returning the
hypervisor and the guest's enrollment stops gating a destroy that never touches
it.

A few lines. Removes the immediate dead end for any guest that *is* linked.

### B — assert the invariant, once

A plan-level property test:

> the set of hosts a plan gates on SSH enrollment == the set of hosts its
> actions actually open SSH connections to.

This is the only change that stops the recurrence rather than the instance. It
makes ① and ③ falsifiable, so the next reconciler that gets the membership
wrong fails in CI instead of in a reconcile six weeks later. It needs each
action to declare its connection hosts in one machine-readable place, which is
also the natural home for the knowledge that is currently hand-copied.

### C — a hypervisor-side linking path

Allow `compute_realization` to link a guest from the platform's own observation
(the Proxmox guest list already available through `nodeutils-pvesh-read`),
without requiring the guest to be independently reachable. This closes root
causes 3 and 4 together: a created-then-orphaned guest becomes linkable, and
therefore destroyable, from the hypervisor's view alone.

This is the real fix and the largest. It should probably wait until there is a
second recorded occurrence of a *linked-guest* need for it — the recorded pain
so far is one throwaway.

### Out of this episode

Closing orphaned operations (root cause 5) is a separate gap with its own
absence of an owner; it is recorded in the turn2 report as F4.

## Notes

- The guest in this incident was destroyed manually by the developer on
  2026-08-10 (`pct destroy 110`, then `nctl prune`), so the live state is no
  longer reproducible. The observations above were captured before removal.
- Nothing here is a permission problem. Every layer behaved as written; the
  written behaviour has a hole shaped like a guest that was created and lost.
