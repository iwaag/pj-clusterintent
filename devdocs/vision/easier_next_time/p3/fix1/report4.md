# Fix 1 — Step 4 report: recover agscratch1 into an eligible pre-use fixture

Status: **complete**.

Two write actions in this step each got separate explicit user approval
before running, per the plan's requirement that restoring the fixture and
linking its realization each be reviewed individually.

## 1. Re-read current state (read-only)

A fresh dry `nctl reconcile agscratch1 --json` (before any write) already
showed an exact `destroy_compute_instance:agscratch1` action with
`evidence.vmid=199`, `evidence.observed_proxmox_node=aghub`, and a matched
`virtual_machine_id`. This was a byproduct of Step 3: the worker restart
drained the old queued `aghub`/`agpc`/`agstudio` ingest Job (already
submitted before Step 2's planner fix, so it did not exercise or re-trigger
the host-scope-widening bug), which updated the underlying VM record's
`custom_fields`. Per the plan ("a current exact destroy dry plan means the
realization recovered; do not perform redundant observation"), no new
`--refresh-observation` was run in this step.

Confirmed via the Nautobot REST API (status/fields only, no report bodies):
the linked `VirtualMachine` (`db05fdbf-84b8-4dde-b1cc-059bb24c5450`, name
`agscratch1`) has `status = Active`.

## 2. Restore agscratch1 to active/present (approved)

`agscratch1`'s desired lifecycle was still `retired`/absent from the earlier
failed episode — restoring it first was necessary so the later real skill
run performs an actual transition rather than finding it pre-retired.

Canonical two-operation batch (inverse of the retirement document in
`nctl/README.md`/the skill):

```yaml
dry_run: true
operations:
  - op: upsert
    kind: desired_node
    key: {slug: agscratch1}
    values: {lifecycle: active}
  - op: upsert
    kind: desired_compute_instance
    key: {desired_node: agscratch1}
    values: {desired_presence: present}
```

Dry preview: `{'create': 0, 'update': 2, 'delete': 0, 'unchanged': 0, 'conflict': 0}`.
Applied the identical document with `dry_run: false` and `--yes`:
`{'create': 0, 'update': 2, 'delete': 0, 'unchanged': 0, 'conflict': 0}`.

A follow-up dry `nctl reconcile agscratch1 --json` then showed the plan
flip from `destroy_compute_instance` to a single non-destructive
`link_compute_realization` action (`requires_observation: false`,
`instance_link_state: absent`, `platform_link_state: linked_to_expected`,
matched by `vmid=199`) — i.e. `DesiredComputeInstance.realized_vm` was not
actually persisted yet; only a vmid-matched drift candidate existed.

## 3. Link the realization (approved)

Ran `nctl reconcile agscratch1 --yes`, applying only the
`link_compute_realization` ledger action (`mutates: true`,
`requires_observation: false` — no Proxmox/SSH/Ansible contact, ledger
write only). Result: `state: converged`, `ok: true`.

A fresh dry `nctl reconcile agscratch1 --json` immediately after shows
**zero actions and zero manual_review entries** for `agscratch1` — fully
converged as an active/present, realization-linked fixture.

## 4. Uniqueness / conflict check

`GET /api/virtualization/virtual-machines/?name=agscratch1` → `count: 1`,
the same `db05fdbf-84b8-4dde-b1cc-059bb24c5450` id. No duplicate VM, no
second scratch guest was created (prohibition 4 upheld).

## Fixture contract — all five conditions met

- VMID 199 exists exactly once as an LXC on `aghub` (confirmed via the
  unique VM record, status Active).
- No conflicting desired or actual identity (unique name/id above).
- Fresh control-node evidence was ingested (Step 3's drained Job, dumps
  ~45 min old at the time, now consumed).
- `DesiredComputeInstance.realized_vm` is linked (Step 4.3's
  `link_compute_realization`, confirmed by the zero-action/zero-review
  fresh plan).
- The guest's desired lifecycle/presence was restored to `active`/`present`
  before any skill invocation (Step 4.2), so Step 5 will perform a real
  transition.

No `pct`, direct REST/PATCH bypass, or guest-SSH contact was used. Both
writes were ledger-only (Nautobot desired state / drift-derived link), not
Proxmox mutations.

## Next

Step 5 (a new session): invoke the revised `retire-proxmox-lxc` skill with
`GUEST=agscratch1`, `VMID=199`, `CONTROL_NODE=aghub`, following it exactly
end to end (dry/apply retirement batch, dry destroy plan, checkpoint,
approved destructive apply, `converged` + zero-action repeat plan, prune).
Per the plan and prohibition 8, no skill edits may happen in that session.
