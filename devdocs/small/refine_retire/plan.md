# Retired LXC Workflow Refinement — Implementation Plan

## Goal

Make the documented retirement workflow match what an operator and agent see
from `nctl`: a reviewable delete plan, a clearly successful removal result,
and an unambiguous ledger-prune outcome.

This is for the scratch environment. Keep the existing exact-host targeting,
dry-run, and explicit `--yes` boundaries, but do not add new approval systems,
credentials, or infrastructure safety machinery.

## Work

### 1. Add a retirement batch example

In `nctl/README.md`, add the smallest canonical batch that updates an existing
guest only:

```yaml
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

State that omitted fields are preserved by this update. Keep the creation
example separate; do not turn retirement into a generic VM lifecycle API.

### 2. Make the delete dry plan directly reviewable

Ensure `nctl reconcile GUEST --allow-destroy --json` exposes the planned
actions in its JSON result, or document one exact supported command for reading
the returned `plan_path`. The reviewer must be able to see the target slug,
VMID, control node, and action kind without reconstructing the operation from
logs.

Align the README with the chosen output shape. Tests should cover the JSON
contract used by agents, not just the persisted file.

### 3. Give successful removal a successful terminal state

After `destroy_compute_instance` succeeds and fresh observation reports
`compute_instance_removal_complete`, reconcile should finish as `converged`
(or another documented success state), rather than surface that informational
completion finding as `manual_intervention_required` / `ok: false`.

Keep manual review for ambiguous or unresolved removal evidence. A completion
record can remain visible in drift and operation artifacts; it should not make
the operation look failed.

Update the general reconcile-state documentation, which currently says manual
findings stop before mutation, and add an end-to-end retirement test for the
terminal envelope and exit status.

### 4. Make prune's Actual-record behavior precise

Clarify and tighten the `actual_already_pruned` path. Today it is selected
when either the realized VM or realized Device is missing, while the message
claims that all Actual roots are gone.

Choose one clear contract:

- require both Actual roots to be absent before skipping Actual cleanup; or
- retain the permissive retry path, but report exactly which roots are absent,
  which remain, and what was deliberately not deleted.

The second option is reasonable for this experimental environment if it keeps
recovery simple. In either case, never report an Actual deletion that was not
requested. Update the prune README wording to cover a guest that never obtained
a Device-level observation.

### 5. Keep brainforge guidance executable

Update `agentdocs/brainforge/README.md` only where command/output behavior
changed: retirement batch preview, delete-plan inspection, success criterion,
and the separate prune preview. Mention that session scratch may contain a
desired-state batch draft; it is not a source of truth.

## Verification

Add focused tests for:

- preview and apply of the two-field retirement batch, preserving other fields;
- JSON dry-plan inspection showing exactly one pinned destroy action;
- successful destroy plus re-observation ending in a success state with
  `compute_instance_removal_complete` evidence; and
- prune with both Actual roots, neither root, only VM, and only Device present.

Run the relevant `nctl` and `nintent` tests, then replay one disposable LXC in
the scratch Nautobot/Proxmox setup: retire → dry plan → destroy → fresh drift →
prune dry plan → prune. Record the observed operation IDs and final drift in a
short report.

## Minimal Constraints

- Do not broaden this work into a generic Proxmox deletion interface.
- Do not hide a non-successful observation or an ambiguous target behind a
  success result.
- Otherwise, helper structure, output fields, and test placement are left to
  the implementer.
