# Systemic retirement — big plot

Date: 2026-07-29

## Goal

Reach an auditable but practical path from a changed user wish to eventual removal of the real
resource and related data.  Each stage should solve one ownership problem without requiring the
later deletion policy to be designed in advance.

## Broad sequence

### 1. Make Braindump content immutable

Keep create and read operations.  Remove public Braindump update and delete paths.  Corrections are
new statements rather than edits to old statements.

### 2. Add supersession as the only change path

Add `active` and `superseded` usage states.  Atomically create a replacement and move explicitly
selected old Braindumps from `active` to `superseded`.  Brainforge reads active documents by
default and can still show superseded documents by ID or an explicit history option.

### 3. Turn current prose into an explicit retirement proposal

When an active Braindump says that an existing object is no longer wanted, the agent identifies
the corresponding structured Desired and Actual objects and presents a read-only proposal.
Free-form prose alone makes no state change.

### 4. Retire structured Desired state

After user confirmation, retire the exact Desired objects in dependency-aware order.  Define drift
so a retired intent with a still-present actual realization is visible but does not request create,
start, or ordinary convergence work.

### 5. Decide and perform resource disposition

Separately choose whether the actual resource is retained, intentionally unmanaged, stopped, or
destroyed.  Add bounded Proxmox LXC stop/destroy support first, with a dry plan and explicit target
identity.

### 6. Re-observe and retain absence evidence

Run normal observation after resource action.  Represent disappearance and any grace period
without immediately deleting the Actual ledger record.

### 7. Prune structured records

Once dependency, observation, and retention conditions are satisfied, add narrowly scoped pruning
for eligible Desired tombstones and Actual ledger rows.

### 8. Define final Braindump deletion

Only after the downstream lifecycle is proven, decide when superseded Braindumps can be physically
deleted.  The policy may retain minimal operation evidence even when resource-specific Desired,
Actual, and prose records are removed.

## Ordering principle

Later stages may refine earlier interfaces, but they must not make superseded prose current again
or allow prose to actuate the cluster directly.

