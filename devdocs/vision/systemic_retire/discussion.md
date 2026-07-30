# Systemic retirement — discussion summary

Date: 2026-07-30

## Starting point

The disposable Proxmox LXC `agfixture` was successfully moved from a Braindump wish through
structured Desired state into observed Actual state. The resulting work now provides a complete
narrow path to retire its Desired intent, destroy one explicitly absent Proxmox LXC, and retain
fresh Actual absence evidence. Pruning records and deleting related prose remain outside that path.

The first idea was to design that complete retirement path immediately, including provenance from
Braindumps to Desired records and a separate retirement case.  The discussion then narrowed to an
earlier problem: old prose must stop participating in the user's current Brainforge context before
resource retirement and deletion are designed.

## Current authority boundary

Braindump is free-form user Ground Truth, and Alignment Review is the agent's current free-form
understanding.  Neither is an execution input.  Today `nctl drift` and `nctl reconcile` do not read
Braindumps at all; they use only explicitly confirmed structured Desired state and observed Actual
state.

Therefore, saying that an old Braindump is "not used for reconcile" means:

- Brainforge must not treat it as a current user wish when proposing later Desired changes; and
- changing its status must itself cause no Desired mutation, drift change, reconcile action, or
  cluster actuation.

## Conclusion: immutable statements with supersession

A Braindump becomes immutable after creation:

- `title`, `body`, and `authorship` cannot be changed;
- a Braindump cannot be physically deleted yet; and
- corrections and changed wishes are recorded in a new Braindump.

A later small change adds one usage state:

```text
active -> superseded
```

`active` Braindumps are the current Brainforge context.  `superseded` Braindumps remain directly
readable as reference material but are excluded from the normal current-context read.

When a user changes a wish, the agent may transcribe a replacement Braindump and supersede the old
one after showing the text and scope to the user.  For example:

```text
old: agfixture and agcoolvm should exist
new: agfixture should be removed after its test; agcoolvm is still wanted
```

The prose remains unconstrained.  A replacement may restate unchanged wishes and express changed
or negative wishes in ordinary language.  The system does not parse positive and negative
sentences or require one subject per document.

Creating the replacement and superseding the explicitly selected old Braindump(s) should be one
transaction.  The initial design needs no successor relation, prose schema, Desired provenance
link, or retirement-case model.

Alignment Review remains a separate agent-owned current response.  Its detailed lifecycle does not
need to be redesigned to establish Braindump content immutability and supersession.

## Deferred work

This decision deliberately still does not define:

- automatic interpretation of contradictory prose;
- general Desired lifecycle retirement or dependency ordering beyond the completed one-LXC path;
- intentional unmanaged classification for Actual resources;
- Proxmox stop actions, QEMU destruction, or a general provider-disposal abstraction;
- retention periods or Actual tombstone pruning;
- pruning Desired or Actual database records; or
- when a superseded Braindump becomes eligible for physical deletion.

Those capabilities can be designed in order after the current Braindump set becomes deterministic.
