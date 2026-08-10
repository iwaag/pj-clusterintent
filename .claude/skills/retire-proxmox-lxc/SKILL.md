---
name: retire-proxmox-lxc
description: Retire one Proxmox LXC guest (declare retired/absent, destroy via nctl reconcile --allow-destroy, then nctl prune) with an enumerated manual_review branch table.
version: 3
execution_level: 3
triggers: [proxmox_lxc_retirement, guest_retirement_request, decommission_lxc]
risk: destructive_scoped
prerequisites: []
last_verified: 2026-08-10
verified_against:
  nctl: 7782d72 (+ no_guest_vm fix, working tree at verification)
---

**Verified.** Authored 2026-08-03, revised 2026-08-03 (Fix 1 Step 1) and
2026-08-10 (no_guest_vm: the "realized compute instance in a prior session"
prerequisite is gone — an unlinked or orphaned guest is now recoverable with
supported commands, see "Unrealized guest recovery" below). Used successfully
on a real retirement (`agscratch1`, vmid 199, `aghub`) on 2026-08-03 against
`nctl` `3329d93b`, and on the orphan-recovery retirement (`agdoomed2`, vmid
112, `aghub`) on 2026-08-10. See
`../../devdocs/vision/easier_next_time/p3/fix1/plan.md` Step 5/6 and
`../../devdocs/vision/fix/no_guest_vm/report.md`.

**Unrealized guest recovery.** A guest whose Proxmox realization is not yet
(or no longer) in Actual State — including one created by a reconcile that
died mid-observation — no longer stops this skill. `nctl reconcile GUEST`
plans the evidence refresh on the platform's **control node** automatically,
and `nctl reconcile CONTROL_NODE --refresh-observation --yes` forces the same
hypervisor-side collection explicitly. Run one of those, then retry the dry
reconcile from step 5. The guest itself never has to answer SSH.

This skill wraps `README.md` §"Retiring one Proxmox LXC" and
`nctl/docs/add-and-retire-proxmox-lxc.md` §"Retiring one Proxmox LXC" for an executor — read those
for background if something here is unclear, but everything required to execute is below.

## Typed inputs

- `GUEST` — the desired-node slug to retire.
- `VMID` — the expected Proxmox VMID of the guest's compute instance.
- `CONTROL_NODE` — the expected control-node slug (the Proxmox host that owns
  the guest).

If any of the three is not known before starting, **stop** — ask the user or
a capable model to supply it. Do not guess or derive it from a partial match.

## Permitted commands (exact, run from repo root)

```
uv run --project nctl nctl desired apply -f FILE --json
uv run --project nctl nctl desired apply -f FILE --yes --json
uv run --project nctl nctl reconcile GUEST --allow-destroy --json
uv run --project nctl nctl reconcile GUEST --allow-destroy --yes --json
uv run --project nctl nctl reconcile GUEST --json
uv run --project nctl nctl reconcile GUEST --yes --json
uv run --project nctl nctl reconcile CONTROL_NODE --refresh-observation --yes --json
uv run --project nctl nctl prune GUEST --json
uv run --project nctl nctl prune GUEST --yes --json
```

No other command (no `pct`, no direct SSH, no Ansible invocation) is
permitted by this skill.

## Fixed step order

1. **Write the retirement batch.** Save to `.local/retire-GUEST.yaml`
   (git-ignored; substitute the real slug for `GUEST` everywhere, including
   the filename):

   ```yaml
   dry_run: true
   operations:
     - op: upsert
       kind: desired_node
       key: {slug: GUEST}
       values: {lifecycle: retired}
     - op: upsert
       kind: desired_compute_instance
       key: {desired_node: GUEST}
       values: {desired_presence: absent}
   ```

2. **Dry apply:** `nctl desired apply -f .local/retire-GUEST.yaml --json`.
   Confirm it names only these two upserts, nothing else.

3. **STOP — user approval required** before the batch write (`--yes`).

4. **Apply:** `nctl desired apply -f .local/retire-GUEST.yaml --yes --json`.

5. **Dry destructive reconcile:** `nctl reconcile GUEST --allow-destroy --json`
   (no `--yes` — this never reaches Proxmox by itself).
   - If `data.manual_review` is non-empty, go to the **manual_review branch
     table** below and do not proceed past it without a resolution it names.
   - If empty, with exactly one `destroy_compute_instance` action, continue.
     A `link_compute_realization` action for the same guest alongside the
     destroy is expected when the guest's ledger link was missing (matched by
     vmid/name): the link is planned first so prune can later collect the
     VirtualMachine record. It is not a deviation; still exactly one destroy.

6. **Checkpoint — fill in before proceeding, from the fresh `plan.json` you
   just produced in step 5 (do not reuse an earlier plan's numbers):**

   ```
   planned target slug          = ___   expected (GUEST)         = ___   equal? ___
   planned evidence.vmid        = ___   expected (VMID)          = ___   equal? ___
   planned evidence.control_desired_node_slug = ___   expected (CONTROL_NODE) = ___   equal? ___
   ```

   All three equal → proceed. Any mismatch → **stop**, do not run
   `--allow-destroy --yes`.

7. **STOP — user approval required** before the destructive apply.

8. **Actuate:** `nctl reconcile GUEST --allow-destroy --yes --json`. Confirm
   the operation reaches state `converged`.
   - If destruction succeeded but observation/convergence failed, do not
     submit a second destroy: retain the operation evidence, re-run
     `nctl reconcile GUEST --refresh-observation --yes` to refresh
     observation instead (per `README.md`).

9. **Repeat dry reconcile:** `nctl reconcile GUEST --json`. Confirm
   `data.plan.actions` has length 0. A nonzero length means step 8 did not
   fully converge — stop, do not repeat the destroy, treat existing evidence
   as partial progress per README.md.

10. **Dry prune:** `nctl prune GUEST --json`. Confirm `eligibility` is
    `eligible`.

11. **STOP — user approval required** before the prune apply.

12. **Prune:** `nctl prune GUEST --yes --json`. Confirm state `pruned`.

## Success evidence (machine-checkable, from `--json` output / `nctl ops show OPERATION_ID`)

- Step 8/9 reconcile: final state `converged`, repeat dry-reconcile action
  count `0`.
- Step 12 prune: final state `pruned`.

All three must hold for this skill's use to count as a completed retirement.

## manual_review branch table

Both codes below were observed together in the one audited episode (the
2026-08-03 `aghaos` retirement audit, WorkflowEpisode); root cause was the
desired state not yet being in a realizable shape.

| code | severity seen | meaning | action |
|---|---|---|---|
| `no_realized_object` | error | the node's `actual_state_policy` is `required` but no realized device or VM is linked yet | **stop.** The guest's realized link isn't established; do not force a destroy against an unlinked node. Return to a human/capable model to establish the link or confirm the guest truly has no realized object, then retry from step 5. |
| `actual_node_not_linked` | warning | the only actual candidate is a `virtualization.virtualmachine`, but `DesiredNode`-level realization only accepts `dcim.device` — VM realization belongs to `DesiredComputeInstance.realized_vm`, not this node link | Alongside `no_realized_object`, informational — no separate action beyond resolving `no_realized_object`. If this code appears **alone** (no `no_realized_object`), **stop** — this is the node/compute realization split that `nctl_core/reconcile/classify.py` deliberately keeps as manual review; do not link the VM candidate as the node's realized object. |
| `compute_instance_missing` | error | no VM candidate exists in the matched Cluster for `DesiredComputeInstance` — Actual State has not (or no longer) observed the guest; hypervisor-side evidence is stale or the guest was orphaned mid-creation | **run the unrealized-guest recovery** (see above): `nctl reconcile GUEST --yes` (plans the control-node evidence refresh automatically) or `nctl reconcile CONTROL_NODE --refresh-observation --yes`, then retry from step 5. If the refreshed drift still reports `compute_instance_missing`, the guest genuinely does not exist on the hypervisor — proceed to `nctl prune GUEST` (steps 10-12) instead of a destroy; there is nothing to destroy. Never add a direct `pct`/REST link as a workaround. |
| plan with only a `link_compute_realization`-shaped or `observe_node`-shaped action, or any plan with **zero** `destroy_compute_instance` actions | n/a | the guest's realization evidence is not yet current, so nothing is pinned to destroy this round | **not a failure** — execute the planned round (`--yes`; an `observe_node:compute-evidence` action is a read-only hypervisor collection), then retry the dry reconcile from step 5. If repeated rounds never produce a destroy action and drift still names the guest, stop and return to a human with the operation evidence. |

**Any other `manual_review` code**, or either of the first two codes
appearing in a combination not listed above: **stop**
(`manual_intervention_required`, policy §5). Return the task to a human or
capable model. Do not improvise a resolution — enumerating every nctl error
code is explicitly out of scope for this skill; an unenumerated code is not a
bug in the skill, it is the skill doing its job.

## Prohibitions

1. No secrets, tokens, or private keys in this skill or any Git-tracked file
   it produces; the retirement batch file stays under `.local/`
   (git-ignored).
2. Do not run any `--yes` command (`desired apply --yes`,
   `reconcile --allow-destroy --yes`, `prune --yes`) without explicit,
   fresh user approval for that specific step — approval for an earlier step
   does not carry forward.
3. Do not widen scope beyond the one declared `GUEST` slug — no wildcard or
   multi-guest batches.
4. Do not submit a second destroy as recovery from a partial failure (see
   step 8).
5. Do not skip or fake the step 6 checkpoint by reusing numbers from an
   earlier plan; re-read the plan produced in the immediately preceding step.
6. This skill covers retirement only. Guest creation, SSH enrollment
   recovery, and other workflows are out of scope — do not extend this skill
   ad hoc.

## Stop conditions

- Any typed input (`GUEST`, `VMID`, `CONTROL_NODE`) unknown at the start.
- The unrealized-guest recovery was run and repeated rounds still produce
  neither a `destroy_compute_instance` action nor a prune-eligible state.
- A `manual_review` code, or combination, not resolved by the branch table.
- A step 6 checkpoint mismatch.
- Reconcile does not reach `converged`, or the repeat dry plan (step 9) is
  nonzero.
- Prune eligibility (step 10) is not `eligible`.

On any stop condition, do not improvise past it: record the gap (self-report
per policy §4) and return the task to a human or a capable model.
