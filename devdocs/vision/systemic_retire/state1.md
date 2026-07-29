# Systemic retirement — state 1: current design and implementation

## Purpose

This note describes the current gap between the desired system behaviour and the
implemented system.  In particular, the system does not yet have a safe,
systemic way to notice that a Desired-state element is no longer supported by a
user's current Braindump, move it through retirement or unmanaged handling, and
eventually remove it under explicit approval.

`unmanaged` in this document means an **Actual-state classification**: something
that is observed but has no current Desired-state owner.  It is not a lifecycle
value for a Desired record.

## Current state

### Braindump is deliberately separate from Desired state

Braindumps are user-originated free text, and Alignment Reviews are agent-owned
free text.  The only persisted relation in this exchange is one Alignment Review
per Braindump.  Neither model has a relation to a DesiredNode, DesiredService,
DesiredComputeInstance, endpoint, or an Actual-state record.

Consequently, deleting a Braindump deletes its review but does not identify or
change any Desired-state element.  The `nctl braindump` surface has no import
path into drift, reconciliation, Jobs, nodeutils, or Ansible.  This separation
is intentional: natural-language text and an agent's interpretation must not
silently actuate the cluster.

### Retirement is a retained Desired-state lifecycle

Desired nodes and compute platforms support `planned`, `approved`, `active`,
`deprecated`, and `retired` lifecycles.  `nctl lifecycle NODE retired` is an
explicit, direct lifecycle setter for a DesiredNode.  It is not part of
`nctl reconcile`, and reconcile never changes a lifecycle automatically.

For compute intent, a retired effective lifecycle means no further create or
start actuation.  The desired record remains readable and its observed
realization remains explainable.  Retirement is therefore a safe operational
stop and an audit record, not a delete request or a garbage-collection marker.

There is no `unmanaged` lifecycle value for a Desired record, and no command to
turn a Desired record into one.

### Actual state is observation-owned and conservatively retained

Nautobot/nodeutils observation owns Actual state.  `nctl actual` is read-only,
and desired-vs-actual drift can describe observed objects that lack a matching
Desired owner as unexplained/unmanaged.  That description is intentionally
neutral: an observed object with no matching Braindump or Desired record must
not be assumed unwanted.

The Proxmox design is similarly conservative.  A guest which disappears from
Proxmox is not automatically removed from Nautobot; it is intended to remain
visible (eventually as offline/stale evidence) so that an operator can choose a
cleanup policy.  The currently supported LXC reconciler can create and start a
guest, but cannot stop, destroy, replace, resize, or migrate it.

### No complete deletion path exists

`nctl braindump delete` is the only relevant deletion command.  It deletes a
specific Braindump and its Alignment Review after confirmation.  It does not
delete Desired or Actual state.

The current public Desired-state paths do not expose deletion: the Nautobot UI
is read-only, retained REST endpoints reject Desired deletes, and the canonical
intent-source import path is create/update-oriented.  There is likewise no nctl
action for deleting a Proxmox guest or pruning a Nautobot Actual record.

## Why the absence is correct for now

An absent sentence in a current Braindump is ambiguous.  It can mean a change of
mind, an accidental omission, a refactoring of prose, or that the component is
still desired but described elsewhere.  A missing Desired entry is also
ambiguous: it may be intentionally unmanaged, stale observation evidence, or a
failed/import-incomplete declaration.

Automatically retiring, destroying, or pruning on either absence would turn
loss of context into destructive action.  The current separation therefore
protects the cluster, but it also leaves cleanup as a manual, unimplemented
workflow.

## Desired systemic flow

The intended future behaviour should be a staged and auditable process, not a
direct inference from prose to deletion:

1. **Record provenance.** A structured Desired element records the specific
   Braindump(s), source declaration(s), or explicit policy that justify it. A
   free-text match alone is never sufficient evidence.
2. **Detect candidates read-only.** After a Braindump change or deletion, an
   audit reports affected Desired elements as *candidates for review*. It makes
   no state change and shows why each association exists.
3. **Classify with an explicit user decision.** The operator chooses, one
   reviewed scope at a time, to retain, update provenance, retire, or mark the
   corresponding observed object as intentionally unmanaged. Ambiguity stops
   here for clarification.
4. **Retire Desired intent.** An approved operation moves the selected Desired
   item to `retired` and records the decision/evidence. It must be dependency
   aware: platforms, instances, endpoints, placements, allocations, and
   realized links need an explicit ordered plan.
5. **Handle the real resource separately.** A dry-run plan states whether a
   guest/service should be retained, stopped, destroyed, or merely observed as
   unmanaged. Any real actuation requires its own explicit approval and a
   deterministic nctl action.
6. **Re-observe and verify.** nodeutils/Nautobot observation establishes the
   new Actual state. A removed resource is first retained as evidence according
   to the configured grace/retention policy; it is not silently erased.
7. **Prune only after a second approval.** After the retention prerequisites
   are met, a narrowly scoped prune operation may delete the Desired tombstone
   and/or eligible Actual ledger record. It must confirm the exact identities,
   dependencies, and postconditions.

## Required capabilities not yet implemented

- Structured provenance links between Braindumps and Desired elements, including
  an explicit way to represent non-Braindump sources and intentional retention.
- A read-only orphan/candidate audit with deterministic evidence and no
  prose-based guessing.
- An explicit, dependency-aware retire operation for Desired nodes, compute
  instances, endpoints, services, and placements.
- A first-class Actual-state unmanaged classification with policy and audit
  evidence; this must remain distinct from Desired lifecycle.
- nctl dry-run/apply actions for supported resource stop/destroy operations,
  beginning with bounded Proxmox LXC removal.
- Observation and retention/grace handling for removed resources.
- A confirmed, scoped prune command for Desired and Actual ledger records,
  including tests for cancellation, dependency conflicts, retries, partial
  observation, and identity mismatches.

## Safety invariants for any implementation

- Braindump deletion alone never retires, unmanages, destroys, or prunes
  anything.
- Every state-changing phase is explicit, dry-runnable where applicable, and
  separately approved; approval to retire is not approval to destroy or prune.
- Actual state continues to be written only by observation/ingest, never by an
  agent directly editing a ledger record.
- Unknown or ambiguous objects are reported neutrally and retained for review.
- Every destructive action is limited to stable identifiers and verified by a
  fresh post-action observation.

## Status

This is a vision/state document, not an implemented interface contract.  Today,
the supported safe operation is an explicitly approved lifecycle change to
`retired`; systemic provenance, unmanaged classification, destruction, and
pruning remain future work.
