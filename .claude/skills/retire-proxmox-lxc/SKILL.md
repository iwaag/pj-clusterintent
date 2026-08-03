---
name: retire-proxmox-lxc
description: Retire one Proxmox LXC guest (declare retired/absent, destroy via nctl reconcile --allow-destroy, then nctl prune) with an enumerated manual_review branch table.
version: 2
execution_level: 3
triggers: [proxmox_lxc_retirement, guest_retirement_request, decommission_lxc]
risk: destructive_scoped
prerequisites: [existing_realized_compute_instance]
last_verified: 2026-08-03
verified_against:
  nctl: 3329d93bf3ebf38d284adedc6aa3653abd210cfc
---

**Verified.** Authored 2026-08-03, revised 2026-08-03 (Fix 1 Step 1: added
the missing `dry_run: true` envelope field and the realized-compute
prerequisite below). Used successfully on a real retirement (`agscratch1`,
vmid 199, `aghub`) on 2026-08-03 against `nctl` `3329d93b`: exact destroy,
`converged`, zero-action repeat plan, eligible prune, `pruned`. See
`../../devdocs/vision/easier_next_time/p3/fix1/plan.md` Step 5/6 and
`../../.local/evidence/workflow-episodes/20260803_retire-agscratch1-real-use/selfreport.md`.

**Prerequisite — realized compute instance.** `GUEST`'s Proxmox realization
must already be observed, ingested into Nautobot, and linked to
`DesiredComputeInstance.realized_vm` in a **prior session**, before this
skill's Step 1 begins. A guest that was only just created (or never had its
control node's platform observation ingested) is not yet a valid input —
this skill retires an existing realized guest, it does not create,
observe, or link one. If that link does not already exist, stop before
Step 1 and return the task to a human or capable model to establish it
first; do not fold that recovery into this skill's run.

This skill wraps `README.md` §"Retiring one Proxmox LXC" and `nctl/README.md`
§"Retiring one Proxmox LXC" for an executor — read those for background if
something here is unclear, but everything required to execute is below.

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

Both codes below were observed together in the one audited episode
(`.local/evidence/workflow-episodes/20260803_retire-aghaos/audit.md`); root
cause was the desired state not yet being in a realizable shape.

| code | severity seen | meaning | action |
|---|---|---|---|
| `no_realized_object` | error | the node's `actual_state_policy` is `required` but no realized device or VM is linked yet | **stop.** The guest's realized link isn't established; do not force a destroy against an unlinked node. Return to a human/capable model to establish the link or confirm the guest truly has no realized object, then retry from step 5. |
| `actual_node_not_linked` | warning | the only actual candidate is a `virtualization.virtualmachine`, but `DesiredNode`-level realization only accepts `dcim.device` — VM realization belongs to `DesiredComputeInstance.realized_vm`, not this node link | Alongside `no_realized_object`, informational — no separate action beyond resolving `no_realized_object`. If this code appears **alone** (no `no_realized_object`), **stop** — this is the node/compute realization split that `nctl_core/reconcile/classify.py` deliberately keeps as manual review; do not link the VM candidate as the node's realized object. |
| `compute_instance_missing` | error | no VM candidate exists in the matched Cluster for `DesiredComputeInstance` — the realized-compute prerequisite above was not actually met | **precondition failure — stop.** This is not a wait-and-retry condition and not a defect in the skill. Return to a human or capable model to establish the realized-compute link in a separate session (this skill does not create, observe, or link a VM). Do not retry the dry reconcile expecting it to resolve on its own; do not add a direct `pct`/REST link as a workaround. |
| plan with only a `link_compute_realization`-shaped action, or any plan with **zero** `destroy_compute_instance` actions | n/a | the realized-compute prerequisite was not met, so there is nothing yet to destroy | **precondition failure — stop.** Same handling as `compute_instance_missing`: return to a human or capable model outside this skill's run rather than proceeding. |

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
- The realized-compute prerequisite is not already met (`compute_instance_missing`,
  a link-only plan, or any plan with zero `destroy_compute_instance` actions).
- A `manual_review` code, or combination, not resolved by the branch table.
- A step 6 checkpoint mismatch.
- Reconcile does not reach `converged`, or the repeat dry plan (step 9) is
  nonzero.
- Prune eligibility (step 10) is not `eligible`.

On any stop condition, do not improvise past it: record the gap (self-report
per policy §4) and return the task to a human or a capable model.
