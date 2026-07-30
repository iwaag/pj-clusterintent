# Retire core — development roadmap

## Purpose

Build the smallest complete path from confirmed structured deletion intent to removal of one
Proxmox LXC and fresh confirmation that it is absent.

```text
AI confirms the user's wish from the active Braindump
  -> AI writes explicit structured Desired state through nctl
  -> nctl reconcile plans the retired resource disposition
  -> an explicitly enabled reconcile destroys the LXC
  -> normal Proxmox observation records the guest as absent
  -> fresh drift reports convergence
```

Braindumps remain conversational Ground Truth for the user and AI. They are never parsed or
imported by drift, reconcile, Jobs, or an actuator. The deterministic path begins only after the
AI has confirmed the target and submitted structured Desired state through the canonical writer.

## Scope

This initiative covers:

- retirement of the DesiredNode that owns one compute instance;
- an explicit Desired state saying that the compute resource should be absent;
- lifecycle-aware compute drift and reconciliation;
- bounded destruction of an existing Proxmox LXC through `nctl reconcile`;
- fresh observation of guest absence; and
- retained Desired and Actual records which explain the completed removal.

It does not cover physical deletion of Braindumps, Desired rows, Nautobot Device or VirtualMachine
rows, scheduled deletion, retention periods, garbage collection, QEMU guests, physical-machine
destruction, or a general unmanaged workflow.

## Minimal contract

### Desired state

Add one current-intent field to `DesiredComputeInstance`:

```text
desired_presence = present | absent
```

Existing and new rows default to `present`.

- `present` means that the compute resource should exist.
- `absent` is the explicit deletion intent. It is not inferred from a missing Desired row,
  `unmanaged`, a superseded Braindump, an observation failure, or an absent sentence.
- An absent compute instance is expected to belong to a retired effective lifecycle. The exact
  validation boundary and error presentation are left to the phase implementation plan.

No deletion-request timestamp, reason, approval record, schedule, retention value, successor,
provenance relation, or protection flag is added without a current consumer in this initiative.

### Actual state

Retain the Nautobot VirtualMachine row and record whether a complete Proxmox observation found the
guest:

```text
proxmox_presence = present | absent
```

A guest is changed to `absent` only when a fresh, complete observation of the same Proxmox scope
does not contain it. Partial, failed, or stale observation does not prove absence and leaves the
last presence evidence unchanged while drift reports the observation problem.

The related Nautobot Device remains retained as its last guest-OS observation. This initiative
does not invent a second Device absence mechanism or delete either Actual row.

### Reconcile interface

Keep `nctl reconcile` as the operational plan/apply interface. Do not add a parallel dispose
command.

The intended command shape is:

```text
nctl reconcile agfixture
nctl reconcile agfixture --allow-destroy
nctl reconcile agfixture --allow-destroy --yes
```

- Ordinary reconcile shows the required destroy action but does not execute it.
- `--allow-destroy` admits the destroy action to the executable plan and remains a dry-run without
  `--yes`.
- Existing `--yes` remains the apply switch.
- The first implementation may support destroy only for an exact host scope.

`--allow-destroy` and `--yes` have separate meanings: action capability and apply mode. Do not add
another confirmation prompt, persisted approval workflow, expiring token, delay, or duplicate
safety gate.

## Reconciliation semantics

The implementation should preserve these outcomes:

| Effective lifecycle | Desired presence | Observation | Actual presence | Result |
|---|---|---|---|---|
| active/approved | present | complete | present | ordinary compute reconciliation |
| active/approved | present | complete | absent | missing resource; existing create path may apply |
| retired | present | complete | present | retained realization; no create, start, or destroy |
| retired | absent | complete | present | destroy action required |
| retired | absent | complete | absent | converged removal |
| any | any | incomplete/stale/failed | unknown | observation finding; do not claim presence or absence changed |

Retirement alone is not deletion intent. Actual absence alone is not deletion intent. Only the
combination of structured `desired_presence=absent` and trustworthy Actual observation drives and
verifies removal.

## Phases

### Phase 0 — Freeze the narrow contract

**Goal:** make later implementation mechanical without designing the eventual prune system.

- Confirm field names, GraphQL and batch projections, drift codes, action kind, and CLI option.
- Identify the current compute create/start, Proxmox observation, Nautobot upsert, and reconcile
  evidence boundaries that will be extended.
- Define the exact identity carried by a destroy action: DesiredComputeInstance, DesiredNode,
  platform/cluster, VirtualMachine, guest type, VMID, and control host.
- Select one disposable LXC acceptance fixture and its expected starting and ending states.

**Exit criteria:** one wire/state sketch and one acceptance scenario are ready for the Phase 1–4
implementation plans.

### Phase 1 — Persist explicit Desired absence

**Goal:** represent confirmed deletion intent without overloading retirement or unmanaged state.

- Add `DesiredComputeInstance.desired_presence` and migrate existing rows to `present`.
- Expose it through the canonical desired-state batch writer and GraphQL reader.
- Extend nctl's typed Desired snapshot and compute conformance fixture.
- Ensure an atomic batch can retire the owning node and set its compute instance to `absent`.
- Keep Braindump APIs and behavior unchanged.

**Exit criteria:** preview and apply can record `retired + absent`, invalid values fail normally,
and existing `present` compute workflows remain unchanged.

### Phase 2 — Observe guest absence

**Goal:** make a complete Proxmox inventory authoritative for whether a previously known guest is
present.

- Add the minimal VirtualMachine presence field used by ingest and drift.
- Mark every observed guest `present`.
- After a complete platform observation, mark previously known in-scope guests omitted from that
  observation `absent`.
- Do not infer absence from partial, failed, stale, or different-scope evidence.
- Preserve the VirtualMachine, interfaces, IP evidence, and Device rows; update only fields needed
  by the current absence consumer.

**Exit criteria:** tests prove present, absent, reappeared, and incomplete-observation behavior
without deleting Nautobot objects.

### Phase 3 — Make compute drift retirement-aware

**Goal:** express removal as an ordinary desired-vs-actual result without allowing retired intent
to recreate or restart resources.

- Apply effective lifecycle and desired presence before ordinary compute mismatch planning.
- Report retired/present, deletion-required, deletion-complete, and observation-unknown outcomes
  with concise structured evidence.
- Plan no create, start, link, or normal resource correction for a retired compute instance.
- Add a deterministic `destroy_compute_instance` action candidate only for a retired, explicitly
  absent, presently observed Proxmox LXC.
- Keep unrelated observed guests neutral; do not interpret unexplained or unmanaged as deletion.

**Exit criteria:** the semantics table above is covered by focused drift/planner tests, and a
retired instance cannot enter the create path.

### Phase 4 — Execute bounded LXC destruction

**Goal:** let the existing reconcile executor perform and verify the planned removal.

- Add `--allow-destroy` to reconcile and carry the permission into plan/execution.
- Implement and register the destroy action using the existing action DAG and operation evidence.
- Add the smallest Proxmox LXC adapter needed to remove the exact planned VMID on the planned
  control host.
- Re-resolve the current typed snapshot before mutation and reject a changed or mismatched target.
- After successful destruction, run the normal platform observation/ingest path and compute fresh
  drift.
- Preserve truthful partial-progress evidence when destruction succeeds but later observation
  fails.

**Exit criteria:** dry-run performs no mutation; ordinary `--yes` does not destroy; explicitly
enabled apply destroys exactly the planned disposable LXC; and a repeated reconcile does not
repeat the action after complete absence observation.

### Phase 5 — End-to-end verification and documentation

**Goal:** prove the full negative-intent control loop and leave one clear operator workflow.

- Exercise `present -> retired+absent -> destroy required -> destroyed -> observed absent ->
  converged`.
- Cover an incomplete post-destroy observation without falsely claiming convergence.
- Run the affected nintent, nctl, nauto, Ansible helper/conformance, and Nautobot runtime gates from
  `README_DEV.md`.
- Perform one explicitly designated disposable-LXC acceptance run.
- Update current-state and operator documentation, including removal of statements that
  Braindump supersession or canonical Desired delete is unimplemented.

**Exit criteria:** the automated control-loop test and disposable live acceptance both show the
intended action was planned, executed once, freshly observed, and not repeated.

## Minimal implementation constraints

Only the following initiative-wide constraints are fixed:

1. Braindump content or status never directly changes Desired, Actual, drift, or actuation.
2. Deletion requires explicit structured `desired_presence=absent`; omission and unmanaged
   classification never imply deletion.
3. The first actuator destroys only a planned Proxmox LXC target and never widens its target set.
4. Actual absence comes from complete observation/ingest, not a direct ledger edit by the destroy
   handler.
5. Ordinary reconcile without the destroy capability does not perform destruction.

Implementation plans may choose internal modules, error codes, playbook structure, and transaction
details freely as long as these contracts and exit criteria remain true.

## Explicit non-goals

Do not add the following as preparatory work:

- Braindump-to-Desired relations or natural-language parsing;
- delete scheduling, grace periods, retention policy, approval history, or automatic pruning;
- `locked`, `deletion_protection`, or similar fields without a destructive physical-machine
  consumer;
- a generic provider disposal abstraction before a second implemented provider exists;
- persistent workflow/case models;
- duplicate confirmation systems beyond reconcile's capability option and existing apply mode;
- deletion of Nautobot Device, VirtualMachine, Desired, or Braindump rows; or
- intentional-unmanaged state.

Warnings and retained records are sufficient for deferred cleanup in this experimental phase.

## Completion condition

This initiative is complete when an AI can confirm a user's wish, record `retired +
desired_presence=absent` through the ordinary nctl Desired writer, show and explicitly enable one
LXC destroy action through `nctl reconcile`, and obtain fresh converged drift from a complete
observation that records the guest as absent—without adding scheduling, pruning, speculative
metadata, or a direct Braindump execution path.
