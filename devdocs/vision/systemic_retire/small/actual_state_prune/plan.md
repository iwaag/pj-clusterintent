# Retired LXC state pruning — implementation plan

Date: 2026-07-30

## Goal

Complete systemic-retirement sequence 7 for the already-removed `agfixture` LXC: delete its
retained Nautobot Actual records and then its spent structured Desired records, while keeping the
Braindump and durable operation evidence.

This is an explicit cleanup operation after convergence, not a consequence of a missing
Braindump sentence or an incomplete observation.

## Starting point

- `agfixture` is `retired` and its compute instance has `desired_presence=absent`.
- A complete Proxmox observation recorded its linked VMID 109 as `proxmox_presence=absent`.
- Host-scoped drift reports `compute_instance_removal_complete`.
- Nautobot still retains the `VirtualMachine`, its VM interface, the guest-OS `Device`, and the
  Desired node, endpoint, and compute-instance tombstones.

## Target contract

Add an nctl operation approximately shaped as:

```text
nctl prune agfixture
nctl prune agfixture --yes
```

The first command is a dry plan. The second applies that same exact-host cleanup. JSON output and
durable operation artifacts must identify the selected Desired and Actual object IDs, eligibility
facts, dependent records, deletions performed, and any partial progress.

A target is eligible only when a fresh snapshot shows all of the following:

- exactly one DesiredNode matches the requested slug and is `retired`;
- its DesiredComputeInstance is explicitly `absent`;
- the linked Proxmox LXC is confirmed absent by a complete observation; and
- existing drift classifies the removal as complete, with no destroy or ordinary correction
  action remaining.

Reuse the existing drift/observation semantics instead of adding another freshness formula.
Active, present, incompletely observed, ambiguous, or unrelated objects are ineligible.

## Prune set and order

Build the concrete dependency set before applying. For this first path it consists of:

1. Actual children owned by the selected Device or VirtualMachine, such as interfaces and their
   exclusively attached IP data;
2. the selected `Device` and `VirtualMachine`;
3. Desired children owned by the node, including its endpoint and compute instance; and
4. the selected retired `DesiredNode`.

Use Nautobot/Django deletion collection to discover the exact core-model dependents instead of
maintaining a broad handwritten cascade table. Shared objects and protected references may block
or remain outside the prune set; report them clearly. Do not widen from the selected Desired links
to other objects merely because names, addresses, or VMIDs look similar.

Desired deletion must continue through the canonical Desired batch-writer contract. The
implementation may orchestrate Actual and Desired deletion in separate transactions; if a later
step fails, retain truthful evidence and make retry converge on the remaining records.

After successful pruning, update the reviewed `.local/desired-state.yaml` operator input so a
future apply does not recreate the removed Desired records. The database remains authoritative;
the file is only the corresponding operator input.

## Implementation

### 1. Add eligibility and plan generation

Extend nctl with a typed prune result and a host-scoped planner that resolves the current
Desired/Actual snapshot, checks the eligibility contract, and obtains the deletion collector
summary. A dry run performs no database or infrastructure mutation.

Keep exact module layout, endpoint shape, and whether the collector logic lives in nintent or a
small server-side operation at the implementer's discretion.

### 2. Apply and record cleanup

On `--yes`, re-resolve the target IDs immediately before deletion, reject a changed target, delete
the planned Actual set, then submit the planned Desired deletes through the batch writer. Record
each completed step so an interrupted or partially successful run can be inspected and retried.

This operation must not contact Proxmox, run Ansible, collect nodeutils, or delete Braindumps.
No grace period, scheduler, approval token, generic garbage collector, or archival subsystem is
required for this experimental environment.

### 3. Verify the resulting state

Prove that:

- dry-run lists the exact `agfixture` records and deletes nothing;
- apply deletes the selected Actual and Desired records, including exclusively owned dependents;
- sibling Device/VM/Desired records remain;
- a second apply is a clear no-op rather than an error or wider search;
- partial progress is recorded and retry removes only what remains;
- `agfixture` disappears from normal Desired/Actual reads and cluster drift; and
- its Braindump and prior reconcile/prune operation artifacts remain readable.

Add focused nctl and Nautobot runtime tests. Run the affected ordinary nctl/nintent suites and the
reusable runtime gate from `README_DEV.md`. A live Proxmox or Ansible acceptance is unnecessary
because pruning begins only after their absence proof and must not reach infrastructure.

## Acceptance on the scratch environment

Use the current `agfixture` rows as the one live acceptance target:

1. capture host-scoped drift and a prune dry plan;
2. review the exact IDs and dependent-object summary;
3. apply once;
4. confirm the DesiredNode, DesiredComputeInstance, DesiredEndpoint, Device, VirtualMachine, and
   owned Actual children are gone;
5. confirm unrelated records, Braindumps, and prior operation evidence remain; and
6. repeat the command to prove no repetition.

The scratch PostgreSQL backup mechanism is available if useful, but a mandatory new backup or
rollback framework is not part of this initiative.

## Out of scope

- Braindump physical deletion or retention policy;
- automatic retirement inferred from prose, omission, or discovery;
- unmanaged-resource classification or general orphan garbage collection;
- pruning active resources, physical nodes, QEMU guests, services, or compute platforms; and
- long-term retention periods, scheduled cleanup, restore tooling, or compatibility paths.
