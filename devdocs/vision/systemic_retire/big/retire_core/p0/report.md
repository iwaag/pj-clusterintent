# Retire core Phase 0 — contract report

Date: 2026-07-30

## Result

Phase 0 is complete. The narrow persistence, drift, reconcile, actuation, observation, and
acceptance contracts are fixed below. No application code, schema, Desired state, Actual state, or
Proxmox resource was changed.

Braindump remains outside the deterministic control loop. The implemented path will begin only
after an AI has confirmed the user's intent and written structured Desired state through nctl.

## Frozen contract

### Desired state

Add exactly one field to `DesiredComputeInstance`:

```text
desired_presence = present | absent
default = present
```

The field is current intent:

- `present` retains the existing compute contract;
- `absent` explicitly requests that the compute resource not exist; and
- omission, a missing Desired row, Braindump status, unmanaged classification, and observation
  failure never imply `absent`.

The supported removal declaration is an atomic desired-state batch which:

1. changes the owning `DesiredNode.lifecycle` to `retired`; and
2. changes its `DesiredComputeInstance.desired_presence` to `absent`.

The compute platform remains active because it is a shared control scope. The Phase 1 plan may
choose the simplest model/service validation which rejects an absent instance whose effective
lifecycle is not retired; it must not add a workflow or approval model.

Required projections:

- nintent model and migration;
- canonical batch `_FIELDS["desired_compute_instance"]`;
- GraphQL `desired_compute_instances.desired_presence`;
- nctl `DESIRED_QUERY`;
- nctl `DesiredComputeInstance`;
- compute conformance fixture; and
- ordinary JSON/text evidence where the current compute summary is rendered.

No timestamp, reason, schedule, approval, provenance, retention, protection, or case field is part
of this contract.

### Actual state

Reuse the existing CustomField key:

```text
proxmox_presence = present | absent
```

It is currently attached to `virtualization.vminterface`. Phase 2 will also attach the same key to
`virtualization.virtualmachine`; no second presence key is introduced.

Required projections:

- `nauto/seed/home_cluster.yaml` adds `virtualization.virtualmachine` to the existing field's
  content types and broadens its interface-only description to cover complete scoped presence
  enumeration;
- Proxmox guest upsert writes `present`;
- complete platform reconciliation writes `absent` to previously known, in-scope guests omitted
  from that complete observation;
- nctl adds `presence` to `ProxmoxVirtualMachineFacts` and `_VM_PROXMOX_FIELDS`; and
- compute drift ignores an `absent` VM as a present realization.

Partial, failed, stale, or conflicting platform evidence does not update a VM from present to
absent. The existing platform observation state supplies the unknown/untrustworthy condition; no
persistent third presence value is added.

VirtualMachine, VMInterface, IP, and Device rows remain retained. This initiative performs no
Actual-row deletion.

### Drift vocabulary

Use the existing compute codes wherever they already express the state:

- `compute_instance_missing` — desired presence is `present`, trustworthy Actual says absent;
- `compute_platform_observation_stale` — platform evidence cannot establish current presence;
- `compute_realization_summary` — retained realization and its disposition summary.

Add only two codes:

| code | severity | meaning | reconcile classification |
|---|---|---|---|
| `compute_instance_destroy_required` | warning | effective lifecycle is retired, desired presence is absent, and a trustworthy present LXC realization remains | automatic, `destroy_compute_instance` |
| `compute_instance_removal_complete` | info | effective lifecycle is retired, desired presence is absent, and trustworthy Actual presence is absent | no action; converged |

A retired instance with `desired_presence=present` produces no create, start, destroy, link, power,
or resource-correction action. Its retained realization may continue to appear in
`compute_realization_summary`.

### Reconcile action

Register:

```text
reconciler_id = destroy_compute_instance
action_kind   = compute_destroy
phase         = bootstrap
mutates       = true
requires_observation = true
```

The action target is the exact `compute_instance` target. Its execution parameters carry:

- DesiredComputeInstance ID;
- DesiredNode ID and slug;
- DesiredComputePlatform ID and slug;
- Actual Cluster ID;
- Actual VirtualMachine ID;
- guest type (`lxc`);
- VMID;
- observed Proxmox node;
- control DesiredNode ID and slug; and
- `host_slugs` containing only the control-node slug.

These values are sufficient to re-derive the same candidate from the action's round snapshot and
to invoke the existing Ansible boundary. Do not add a separate persisted target fingerprint,
approval record, or dispose case.

The planner produces this action only when all of the following are already true:

- effective lifecycle is retired;
- desired presence is absent;
- platform observation is trustworthy;
- the linked realization is present;
- provider is Proxmox;
- desired instance kind is container;
- Actual guest type is LXC; and
- desired/actual platform, VM, and VMID identity agree.

Other providers, QEMU, unlinked/ambiguous guests, and physical nodes do not get a destroy action.

### CLI and execution permission

The CLI option is fixed as:

```text
--allow-destroy
```

The command surface remains:

```text
nctl reconcile HOST
nctl reconcile HOST --allow-destroy
nctl reconcile HOST --allow-destroy --yes
```

Initial destroy execution is host-scoped. No `nctl dispose` command is added.

- Planning always reports `destroy_compute_instance` when Desired/Actual state requires it.
- Plan mode never mutates, with or without `--allow-destroy`.
- Apply without `--allow-destroy` does not execute the destroy action and reports that capability
  as not enabled.
- Apply with both `--allow-destroy` and `--yes` may execute it.

The option becomes one `allow_destroy: bool` input to `run_reconcile` and the round executor. The
existing action identity and dispatch entry identify which action it admits. Do not add another
prompt, token, delay, approval table, or new plan field solely for permission.

### Actuation and post-observation boundary

The current create seam is:

```text
compute drift
  -> create_compute_instance / compute_create
  -> reconcile bootstrap action
  -> nctl compute_create handler
  -> ansible-playbook playbooks/proxmox/create_lxc.yml
  -> pct
  -> controller-owned result artifact
  -> post-actuation observation
```

Destroy extends the same seam with one handler and one small playbook:

```text
destroy_compute_instance / compute_destroy
  -> nctl compute_destroy handler
  -> playbooks/proxmox/destroy_lxc.yml
  -> exact planned VMID
  -> controller-owned result artifact
```

The handler re-derives the current candidate from the round snapshot and requires its execution
parameters to match the plan, following the existing create handler pattern. Exact `pct` command
shape, stopped/running handling, and result JSON keys are Phase 4 implementation-plan choices.

`host_slugs=[control-node]` deliberately reuses `action_host_slugs()` for:

- SSH preflight;
- Ansible `--limit`; and
- post-actuation observation.

`destroy_compute_instance` must be added to the existing SSH-requiring reconciler set. Post-action
observation targets the Proxmox control node, not the destroyed guest. This lets the ordinary
nodeutils Proxmox collection and nauto ingest establish absence without a new observation command.

## Existing boundaries to extend

| concern | current owner | Phase extension |
|---|---|---|
| Desired persistence | nintent `DesiredComputeInstance`, batch service | one choice field and batch projection |
| Desired read | nctl GraphQL `DESIRED_QUERY` and typed compute model | read `desired_presence` |
| Effective lifecycle | shared compute contract fixture | combine lifecycle with desired presence |
| Compute comparison | `drift/compute_evaluation.py` and realization/creation derivation | presence-aware outcomes |
| Classification/planning | reconcile classify, planner, reconcilers | one automatic destroy code/action |
| Action dispatch | reconcile action registry/dispatch | one bootstrap handler |
| Proxmox write | nctl Ansible runner and `playbooks/proxmox/create_lxc.yml` pattern | bounded destroy playbook |
| Proxmox observation | nodeutils report and nauto `ingest_proxmox_platform()` | complete-set absence update |
| Actual read | nctl Actual GraphQL and strict Proxmox allowlist | VM presence projection |
| Durable evidence | existing reconcile event log and operation artifacts | destroy result and post-observation evidence |

No new subsystem is required.

## Acceptance fixture

The designated disposable acceptance fixture is `agfixture`.

Read-only inspection on 2026-07-30 confirmed:

- one DesiredNode named `agfixture`, currently approved;
- one linked DesiredComputeInstance of kind container;
- one active shared Proxmox platform and one linked Cluster;
- one linked Nautobot Device;
- one linked Nautobot VirtualMachine observed as a running LXC;
- matching desired and actual VMID, capacity, storage, and cluster identity;
- complete Proxmox guest and platform observation with no nctl Proxmox read errors; and
- current node and compute drift are converged.

Private UUIDs, MAC/IP values, template paths, and other cluster payload are intentionally not
copied into this tracked report. The acceptance run resolves and records exact IDs in its
operation-local evidence.

Expected starting state for the live acceptance:

```text
DesiredNode.lifecycle = approved or active
DesiredComputeInstance.desired_presence = present
Actual VM presence = present
Proxmox LXC exists
drift = converged
```

Expected ending state:

```text
DesiredNode.lifecycle = retired
DesiredComputeInstance.desired_presence = absent
same Nautobot VirtualMachine row has proxmox_presence = absent
same Nautobot Device row remains retained
Proxmox LXC no longer exists
shared platform remains active
fresh scoped drift = converged
repeated reconcile plans no destroy action
```

The acceptance path is:

1. preview and apply the atomic `retired + absent` Desired batch;
2. run ordinary reconcile and confirm the exact destroy action is reported but not executed;
3. run `--allow-destroy` without `--yes` and confirm no mutation;
4. run `--allow-destroy --yes`;
5. verify destroy evidence, control-node observation, nauto absence ingest, and fresh drift; and
6. repeat reconcile and confirm no destroy action.

No retention wait, scheduled work, Actual pruning, or fixture restoration is required by this
initiative. The retained negative Desired and absent Actual rows are the final expected state.

## Verification performed

- Inspected current nintent compute models, shared compute contract, batch field allowlist, and
  GraphQL-backed nctl Desired reader.
- Inspected current compute drift, creation gate, classifier, planner, action schema, action
  dispatch, executor, SSH target resolution, and post-actuation observation path.
- Inspected nodeutils/nauto Proxmox validation and VM/interface upsert boundaries.
- Confirmed that `proxmox_presence` already exists for VMInterface and can be reused for
  VirtualMachine.
- Inspected the bounded LXC create playbook used as the destroy adapter pattern.
- Read the live scratch Desired/Actual snapshot and current drift for `agfixture`; no writes were
  made.

No test suite was run because Phase 0 changed documentation only. Repository whitespace validation
is recorded with the final report change.

## Deferred by contract

The following remain outside retire core:

- Braindump parsing, triggers, or provenance relations;
- unmanaged as a deletion signal or an intentional-unmanaged model;
- delete scheduling, retention periods, grace timers, or garbage collection;
- Desired or Actual row pruning;
- Device absence inference;
- QEMU or non-Proxmox disposal;
- physical-machine destruction or a speculative protection field; and
- generic provider/disposition frameworks.

## Status

Complete. Phase 1 may proceed directly from this report with a concrete implementation plan.
