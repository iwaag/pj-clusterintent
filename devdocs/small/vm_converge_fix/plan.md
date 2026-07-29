# VM Guest-OS Convergence Fix — Implementation Plan

Date: 2026-07-29

## Goal

Complete the already-designed two-layer convergence path for `agfixture` without changing the VM
roadmap's data model:

```text
DesiredNode agfixture
  -> realized_device
     -> Nautobot Device agfixture
        -> guest-OS identity and nodeutils observation

DesiredComputeInstance agfixture
  -> realized_vm
     -> Nautobot VirtualMachine agfixture
        -> Proxmox LXC identity and compute realization
```

The completed result must make the Device-level guest-OS realization and the
VirtualMachine-level compute realization independently inspectable and converged. The same
QEMU/LXC guest may correctly have both Nautobot objects because they describe different layers;
neither object replaces or duplicates the other object's responsibility.

This is a repair inside the frozen `devdocs/big/vm/roadmap.md` contract, not a new virtualization
model or a generic observation-model redesign.

## Authoritative Design

The complete two-layer decision is currently documented in
`devdocs/big/vm/roadmap.md`, not in one concise README section:

- lines 52–58 identify the guest OS Device and Proxmox VirtualMachine as two legitimate actual
  identities and explicitly say they are different layers;
- lines 62–75 assign guest-OS realization to `DesiredNode.realized_device` and compute
  realization to `DesiredComputeInstance.realized_vm`;
- lines 434–448 define the intended convergence sequence: compute link, manual-access gate,
  guest observation, Device-level ingest, `DesiredNode.realized_device` link, fresh drift, and
  non-repeating convergence; and
- the completed VM Phase 3 report `devdocs/big/vm/p3/report3.5.md` confirms that guest-OS
  realization is Device-only after removal of the legacy `DesiredNode.realized_vm` field.

README coverage is incomplete:

- `nctl/README.md` describes creation, manual initial access, and later observation, but does not
  give one explicit Device-versus-VirtualMachine ownership statement;
- `nintent/README.md` documents `realized_device`, compute `realized_vm`, and
  `accepted_actual_types`, but its examples can be read as though a compute-backed guest's
  VirtualMachine should directly realize its `DesiredNode`; and
- the workspace root README does not describe the two-layer virtualization contract.

This initiative must add a concise normative explanation to the relevant current README surface
so later agents do not need to reconstruct the contract from phase history. The VM roadmap remains
the detailed design authority.

## Verified Current State

### Desired and actual state

- `nauto/seed/intent_sources.yaml` declares `agfixture` as a `service_host` with
  `accepted_actual_types: [virtual_machine]`.
- The same source declares one `DesiredComputeInstance` for `agfixture`, on `aghub-pve`, as an LXC
  with VMID 109.
- Nautobot currently contains both:
  - a Device named `agfixture`, created/updated by the successful nodeutils ingest; and
  - a VirtualMachine named `agfixture`, representing the Proxmox LXC.
- The compute-instance target is converged and already resolves to the intended VirtualMachine.
- The node target is `unknown` with:
  - `actual_node_not_linked`;
  - `no_realized_device`;
  - `no_realized_object`;
  - `ipam_reconcile_observation_missing`; and
  - an `intent_effect_summary` whose production state is skipped for `no_realized_device`.

The Device-level observation exists, but the DesiredNode policy excludes Device candidates, so the
guest-OS ledger link cannot be formed.

### Observation prerequisite failure

Operation `01KYPS6XB0QWVYE1124CRK1HRE` reached the guest by the managed SSH route but failed before
nodeutils could run:

```text
apt attempted to fetch a stale Ubuntu package version and received HTTP 404
-> Git installation failed
-> /var/lib/nodeutils/inventory.json was not created
-> the later slurp reported a non-base64 failure envelope
```

The normal `git_client` role currently installs packages without refreshing the APT package
index. A local uncommitted repair adds an APT cache refresh for `ansible_pkg_mgr == "apt"` before
Git installation. That repair belongs to this initiative and must receive tests, documentation,
and final review rather than remaining an unexplained worktree change.

### Reconcile planning failure

After the APT repair, operation `01KYPSF0BTBAT6YF7TN1DW7B70` successfully:

- collected the pinned nodeutils revision from `agfixture`;
- retrieved a valid report;
- ran `Ingest Nodeutils Inventory`; and
- persisted fresh Device-level facts.

It then failed with:

```text
unsupported candidate object_type 'virtualization.virtualmachine'
```

The node evaluator selected a VirtualMachine because the desired
`accepted_actual_types` permits only `virtual_machine`. `plan_link_actual_node()` copied that
candidate into an automatic action even though `execute_link_actual_node()` can persist only
`dcim.device -> DesiredNode.realized_device`. This is a planner/executor contract violation: an
executor-known unsupported candidate must never become an automatic action.

The same operation then performed another forced nodeutils observation in the next reconcile
round before ending `non_converged`. An explicit refresh request should establish fresh evidence
once; it must not cause repeated collection merely because later ledger work remains.

The earlier failed collection operation also ended with a misleading operation-level
`converged` result because the pre-observation target carried only the informational
`waiting_for_manual_initial_access` finding. A requested observation that fails is not a
successful convergence result even when the pre-existing drift target was not classified as
drifting.

## Target Contract

### 1. Preserve the two realization layers

- `DesiredNode.realized_device` is the sole guest-OS realization link.
- `DesiredComputeInstance.realized_vm` is the sole compute-resource realization link.
- A compute-backed node may have both links simultaneously without conflict.
- Guest OS facts, observed services, operational derivation, production composition, and
  node-level IPAM evidence continue to consume the Device-level observation.
- Proxmox cluster membership, VMID, guest kind, capacity, power, interfaces, and compute drift
  continue to consume the VirtualMachine-level observation.
- Do not create a generic `HostObservation`, generic realized-object relation, or mirrored
  Device/VirtualMachine custom-field scheme in this initiative.

### 2. Make automatic node linking executable by construction

`link_actual_node` may be planned only for a unique `dcim.device` candidate that can be written to
`DesiredNode.realized_device`.

If evaluation produces a `virtualization.virtualmachine` candidate:

- do not create a `link_actual_node` action;
- preserve bounded candidate evidence;
- classify the result as manual review or a more specific non-automatic finding;
- explain that a VM compute link belongs to `DesiredComputeInstance.realized_vm`; and
- never allow the executor's `unsupported_candidate_type` error to be the first place this
  incompatibility is discovered.

The executor keeps its current fail-closed validation as defense in depth.

### 3. Align agfixture guest-OS intent with the frozen model

The proposed desired change is:

```yaml
desired_nodes:
  - slug: agfixture
    node_type: service_host
    accepted_actual_types:
      - device
```

This changes only which Nautobot object type may realize the guest-OS DesiredNode. It does not
change, remove, or overwrite the `DesiredComputeInstance.realized_vm` link.

Because this is a structured desired-state mutation, the plan document does not authorize it.
Before applying it, show the exact Import Intent Sources preview and obtain explicit user
confirmation for this one change.

### 4. Observation outcomes must be truthful and non-repeating

- A requested nodeutils observation that fails makes the action and operation non-successful,
  even if the old drift contains only informational findings.
- Preserve the exact collection/Ansible evidence and do not proceed as though fresh evidence was
  ingested.
- `--refresh-observation` forces one fresh observation for the scoped node per reconcile
  operation. Later rounds may observe only when newly computed drift independently requires it;
  the original force flag must not inject an unconditional observation into every round.
- Successful ingest followed by ledger work must reuse that fresh evidence.

## Implementation Sequence

### Step 1 — Document the existing two-layer contract

Update `nctl/README.md` with a short section that states:

```text
Device = managed guest OS / nodeutils realization
VirtualMachine = Proxmox compute realization
```

Show the two different desired links and state that both objects may legitimately describe one
guest. Point to `devdocs/big/vm/roadmap.md` for the detailed contract.

Update `nintent/README.md` only where necessary to prevent
`accepted_actual_types: [virtual_machine]` from being presented as the guest-OS realization choice
for a node that has a `DesiredComputeInstance`. Do not rewrite the general model guide or remove
supported vocabulary as an incidental change.

### Step 2 — Complete the APT observation prerequisite repair

Keep the package-manager-specific cache update in `ansible_agdev/roles/git_client`:

- run only when the discovered package manager is APT;
- refresh before package installation;
- use a bounded cache-validity interval so every observation does not perform an unnecessary
  update;
- retain generic `ansible.builtin.package` installation for the actual package set; and
- leave non-APT Linux behavior unchanged.

Add or extend the available role/playbook checks to prove:

- the APT refresh precedes Git installation;
- a non-APT host does not execute the APT task;
- syntax check for `playbooks/nautobot/run_nodeutils_collect.yml` passes; and
- a repeat run with a valid cache is idempotent.

Do not use direct SSH or an ad-hoc `apt-get update` as the permanent fix. The normal nctl
observation path must own its prerequisite.

### Step 3 — Close the planner/executor candidate-type gap

In nctl, make `plan_link_actual_node()` validate the candidate object type before returning an
automatic action.

Prefer one named helper/constant for the ledger-supported node-link types rather than duplicating
the literal independently across evaluator, planner, and executor. Preserve executor validation
as a separate safety boundary.

Tests must cover:

1. a unique Device candidate produces one `link_actual_node` action;
2. a unique VirtualMachine candidate produces no automatic node-link action and a bounded
   fallback explanation;
3. a compute-backed node with a linked VM and a matching Device still selects the Device when
   Device is the accepted guest-OS type;
4. the compute `realized_vm` link remains unchanged by node-link planning; and
5. no plan that passes normal validation can later fail with
   `unsupported candidate object_type 'virtualization.virtualmachine'`.

Do not teach `execute_link_actual_node()` to PATCH a removed legacy
`DesiredNode.realized_vm` field.

### Step 4 — Make forced observation single-shot and failure-aware

Audit the reconcile round loop and observation result handling.

- Consume the explicit `refresh_observation` request in the first applicable round.
- Do not automatically carry it into later rounds.
- If the forced observation fails, terminate with a truthful failed/non-converged result and
  retained artifacts.
- If observation succeeds, allow the next round to plan the Device ledger link and IPAM work from
  the new snapshot without a second unconditional collection.

Add executor tests for:

```text
forced observation fails
  -> operation not converged
  -> no ingest/link claim
  -> exact failure retained

forced observation succeeds
  -> one collection
  -> next-round Device link
  -> no second forced collection
  -> final converged result
```

Keep normal drift-driven post-actuation observation behavior intact; only the unconditional
reapplication of the original force request is removed.

### Step 5 — Preview the agfixture desired correction

Change the canonical proposal in `nauto/seed/intent_sources.yaml` from:

```yaml
accepted_actual_types:
  - virtual_machine
```

to:

```yaml
accepted_actual_types:
  - device
```

Run the supported Import Intent Sources Job in preview mode through the established interface and
capture its structured artifact. The preview must show exactly the reviewed agfixture field
change and no unrelated desired rows.

Stop and obtain explicit user confirmation before apply. Do not treat approval of this plan file
as approval of the desired-state mutation.

### Step 6 — Apply the desired correction and dry-plan convergence

After explicit confirmation:

1. apply the exact reviewed Import Intent Sources revision;
2. repeat the import and prove it is a no-op;
3. run `nctl drift --host agfixture --json`;
4. run `nctl reconcile agfixture` without `--yes`;
5. verify the dry plan names:
   - the exact DesiredNode ID;
   - the exact existing Device candidate ID;
   - no VirtualMachine candidate for `link_actual_node`;
   - no compute create/start/relink action; and
   - only the ledger/IPAM/observation work justified by current drift.

Show that dry plan to the user and obtain separate approval before `--yes`.

### Step 7 — Execute and verify exact-scope convergence

After approval of the Step 6 plan, run the supported host-scoped reconcile through nctl. Do not
substitute direct REST, Django ORM, Ansible, SSH, or Nautobot UI writes.

Positive evidence must prove:

- `DesiredNode.agfixture.realized_device` links to the existing nodeutils-managed Device;
- `DesiredComputeInstance.agfixture.realized_vm` remains linked to the existing VMID 109
  VirtualMachine;
- fresh Device facts supply operational values;
- the primary endpoint/IPAM result is either converged or produces a new, exact, independently
  reported finding;
- `waiting_for_manual_initial_access`, `actual_node_not_linked`, `no_realized_device`, and
  `no_realized_object` are absent;
- no guest create/start action ran;
- no repeated unconditional nodeutils collection ran; and
- a final `nctl drift --host agfixture --json` reports both the node and compute-instance targets
  converged.

If any new real error occurs, stop and report it. Do not weaken SSH verification, bypass nctl, or
overwrite an existing link to force convergence.

## Verification Gates

At minimum:

1. `git diff --check` passes in every changed repository.
2. Ansible syntax check passes from the documented `ansible_agdev` working directory.
3. Targeted git-client role/playbook tests pass.
4. Targeted nctl evaluator, planner, ledger, and executor tests pass.
5. The full nctl suite passes.
6. Applicable nauto/nintent import tests pass if the canonical source or documentation fixtures
   require them.
7. Import preview/apply/repeat evidence is exact and bounded.
8. Reconcile dry plan precedes apply and is separately approved.
9. Final host-scoped drift is freshly computed after the operation.
10. Operation evidence contains no failed action hidden behind a `converged` result.

Record real test counts and operation IDs in step reports; do not copy historical counts from
another initiative.

## Non-goals

- No generic `HostObservation` model.
- No replacement of Nautobot Device or VirtualMachine native models.
- No mirroring of all nodeutils fields onto VirtualMachine.
- No removal of the valid Device plus VirtualMachine two-layer representation.
- No new `DesiredNode.realized_vm` or generic realized-object field.
- No Proxmox guest creation, recreation, stop, resize, migration, or deletion.
- No automatic deletion or merging of either existing `agfixture` actual object.
- No broad change to every existing node's `accepted_actual_types`.
- No unrelated service-placement, lifecycle, DNS, or cluster-wide convergence work.
- No direct host mutation merely to make drift green.

## Rollback

- The APT prerequisite change is controller-side Ansible code; reverting it does not roll back
  packages already installed on a guest.
- The planner/executor and refresh-loop changes are local nctl code and can be reverted together
  without changing ledger links.
- If the desired `accepted_actual_types` apply must be reversed, preview and explicitly approve
  the inverse canonical YAML change through the same Import Job. Do not hand-edit Nautobot.
- Do not automatically clear a successfully confirmed `realized_device` link during rollback.
  Treat link removal as a separate ledger mutation requiring its own evidence and approval.
- Neither rollback nor implementation removes the VirtualMachine or changes VMID 109.

## Completion Criteria

- Current README documentation explains the Device/VirtualMachine two-layer design without
  requiring phase-history reconstruction.
- The normal nctl observation path refreshes stale APT metadata when needed and collects
  nodeutils successfully.
- nctl never plans a VM candidate for the Device-only `link_actual_node` executor.
- Failed observation cannot be reported as successful convergence.
- Explicit refresh does not repeat unconditionally across rounds.
- The reviewed agfixture desired correction is applied through the canonical import path and is
  idempotent.
- `DesiredNode.realized_device` and `DesiredComputeInstance.realized_vm` point to their respective
  exact actual objects.
- Fresh `nctl drift --host agfixture --json` reports the guest-OS node and compute-instance
  targets converged without recreating or otherwise changing the LXC.
