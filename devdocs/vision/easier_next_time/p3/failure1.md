# Easier Next Time — Phase 3 Step 2: Failure Report

Status: **blocked**, per README_DEV.md §9 (an external condition — a stuck
Nautobot ingest job — actually prevents further safe progress; this is not a
recoverable local test-fixture issue to paper over). Work stopped here at the
user's direction rather than continuing to poke at a degraded Nautobot.

## What was attempted

Step 2 of `p3/plan.md`: a real use of `.claude/skills/retire-proxmox-lxc/` in
this same session (deviating from policy §7's time-separation rule — the user
explicitly authorized this deviation mid-session; see chat record, not
reproduced here). Two natural retirement candidates the user first proposed
(`ahkeadhcp`, `agk3s`) turned out to be Proxmox guests with no `DesiredNode`
in nctl at all (`unknown_host`) — real actual VMs (`agkeadhcp` vmid 107,
`agk3s` vmid 105, per `nctl actual --json`) that predate nctl management and
are out of this skill's scope (it only operates on already-declared guests).
Per the user's choice, fell back to the plan's documented alternative: create
a scratch LXC, then retire it with the skill.

## What succeeded

1. **Scratch guest created.** `agscratch1` (vmid 199, control node `aghub`)
   was declared via the canonical creation batch
   (`nctl/README.md` §"Adding one Proxmox LXC guest") and actually created in
   Proxmox — `nctl reconcile agscratch1 --yes` operation
   `01KZ3XHADPAMV7MHDB7KDP2J0Y` shows the Ansible `create_lxc.yml` result
   `"created": true` and the guest started. The reconcile itself ended
   `non_converged`/`no_progress` (guest-OS-level Device linking needs SSH
   enrollment this scratch guest never got — expected per README's
   "`waiting_for_manual_initial_access`" note — not itself a problem).
   - One authoring error surfaced and was fixed live: the first creation
     batch used `ip_policy: static` with an address inside the
     `dhcp_reservable_pool` range (`192.168.0.199`), which nctl correctly
     flagged (`static_endpoint_in_dhcp_pool`). Switched to a genuinely static
     address in the `static_pool` range (`192.168.0.5`) instead, matching a
     prior working example (`.local/workspace/.../agdummy-desired-state.yaml`).
2. **Retirement declared.** `.claude/skills/retire-proxmox-lxc/`'s two-upsert
   batch (`lifecycle: retired` + `desired_presence: absent`) was applied
   cleanly.
   - **Real skill-body gap found:** the SKILL.md's embedded retirement YAML
     is missing the `dry_run: true` envelope field that
     `nctl desired apply` requires (`error: document must be a Phase 0 batch
     envelope with dry_run and operations`). The creation-batch example in
     `nctl/README.md` has it; the retirement-batch example (both in
     `nctl/README.md` and copied into the skill) does not. This is a genuine
     Level-3-defeating gap: a weaker executor following the skill literally
     would stop on this error with no guidance. **Not yet fixed in the
     skill body** — per plan prohibition 4, the Step 2 executor does not
     edit the skill mid-use, and Step 2 never reached a clean finish to hand
     off to Step 3 for the fix.
3. **The skill's own stop discipline worked correctly.** The destructive dry
   reconcile (`nctl reconcile agscratch1 --allow-destroy --json`, operation
   `01KZ3XYBZXZ2V0ZR90W3PGTS7Z`) returned `manual_review` code
   `compute_instance_missing` ("no VM candidate exists in matched Cluster") —
   not one of the two codes in the skill's branch table. Per the skill's own
   rule ("any other manual_review code: stop"), execution correctly stopped
   here rather than improvising past it. This is itself a valid, informative
   Level 3 outcome, not a skill defect.

## Where it actually failed

Root cause of `compute_instance_missing`: the guest's Proxmox realization
was never ingested into Nautobot as a `VirtualMachine` (the earlier create
reconcile ended `non_converged` before that step). Diagnosing this as the
capable-model fallback (per the skill's stop-condition intent), two remediation
attempts were made, both outside the skill's declared scope (prohibition 3,
"do not widen scope beyond the one declared GUEST slug") and both failed:

1. `nctl reconcile agscratch1 --refresh-observation --yes` (operation
   `01KZ3Y03VWJNCA155QWAD6XNG1`) — failed on `ssh_host_key_unenrolled`: the
   guest's own OS was never SSH-enrolled (expected for a scratch guest that
   was never taken through initial access setup).
2. `nctl reconcile aghub --refresh-observation --yes` (operation
   `01KZ3Y5KTQ54XNF6JS7YVNPE5R`) — this is the control node, so its scope
   pulled in real neighboring infrastructure (`aghub`, `agpc`, `agstudio`).
   All three hosts' `Ingest Nodeutils Inventory` Nautobot job **timed out
   after 300 seconds** (`ingest failed: Nautobot Job 'Ingest Nodeutils
   Inventory' did not finish within 300.0 seconds`). A follow-up
   `nctl status --json` (read-only connectivity check) then did not return
   within 20 seconds either, though `docker ps` shows the Nautobot
   containers reporting `healthy`. This looks like a stuck/backlogged
   Nautobot job queue, not a code defect in the skill or in `nctl` — an
   external condition per README_DEV.md §10 class 1 (production/external
   target), not something to route around by retrying blindly.

Per the user's instruction, work stopped here rather than continuing to
retry against a degraded Nautobot.

## Current live cluster state (as left)

- `agscratch1`: `DesiredNode.lifecycle = retired`,
  `DesiredComputeInstance.desired_presence = absent`, **not converged** — no
  `realized_vm` link exists, so no destroy has been planned or executed.
- The actual LXC (**vmid 199, host `aghub`, still running**) has **not** been
  destroyed. It is a disposable scratch resource (created solely for this
  Step 2 attempt), not production, but it is still consuming resources on
  `aghub` until cleaned up.
- No `--allow-destroy --yes`, no `prune`, and no other destructive command
  was run in this episode — only dry plans and one non-destructive
  observation attempt reached actuation (the guest creation itself).
- Nautobot's ingest job queue was observed stuck/slow at the time of
  stopping; unknown whether this is transient or ongoing.

## What Phase 3 still needs

1. **This is not a completed Step 2.** No self-report was written to
   `.local/evidence/workflow-episodes/` because the episode did not reach a
   state worth measuring "did the skill reduce improvisation" against — it
   was cut short by external infrastructure, not by the skill's design.
2. Before retrying: confirm Nautobot's job queue/worker is healthy (separate
   diagnostic, outside this roadmap).
3. Once healthy, re-run `nctl reconcile agscratch1 --allow-destroy --json`
   to see whether `compute_instance_missing` resolves on its own now that
   more time has passed (ingest may simply have been slow, not stuck), before
   trying `aghub`-scope remediation again.
4. Fix the SKILL.md `dry_run: true` gap (found above) as part of whatever
   session finally completes a clean Step 2 — this is a real, confirmed
   defect independent of the Nautobot issue and should not wait on it.
5. `agscratch1` (vmid 199, `aghub`) needs cleanup one way or another: either
   finish the nctl-managed retirement once Nautobot recovers, or (since it is
   disposable scratch state) a direct Proxmox cleanup if the nctl path stays
   blocked — implementer's/user's call in that later session.

Phase 3 exit criteria (one real recorded use, `last_verified` set) are **not
met**. Steps 0–1 (`3441e28`) remain valid and complete; Step 2 must be
retried in a future session once the external blocker is understood.
