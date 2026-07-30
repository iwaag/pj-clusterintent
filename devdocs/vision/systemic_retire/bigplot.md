# Systemic retirement — big plot

Date: 2026-07-30

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

### 4. Retire structured Desired state — complete for one LXC

After user confirmation, the canonical Desired writer can atomically retire the exact node and set
its compute instance's explicit `desired_presence=absent`. Drift keeps a retired/present
realization visible without requesting create, start, or ordinary correction.

### 5. Decide and perform resource disposition — complete for one Proxmox LXC

For a retired compute instance explicitly declared absent, `nctl reconcile` plans one bounded
Proxmox LXC destroy action. `--allow-destroy --yes` is required to execute the pinned VMID on the
pinned control host; ordinary apply refuses it. Retained and unmanaged resources still do not
imply deletion, and stop/unmanaged disposition remains future work.

### 6. Re-observe and retain absence evidence — complete for that LXC path

Normal complete Proxmox observation records the destroyed guest as absent while retaining the
VirtualMachine, Device, and their prior evidence. Incomplete or stale observation cannot claim
absence or convergence. Grace-period policy remains future work.

### 7. Prune structured records

Once dependency, observation, and retention conditions are satisfied, add narrowly scoped pruning
for eligible Desired tombstones and Actual ledger rows.

### 8. Purge explicitly approved superseded Braindumps — complete

An explicitly approved, already superseded Braindump may be physically deleted immediately through
the narrow `nctl braindump purge ID --yes` path. The API re-checks the exact UUID and status and
deletes only that document and its one-to-one Alignment Review transactionally. There is no
retention timer, soft delete, archive, recovery workflow, or impact on structured Desired/Actual
state, reconciliation evidence, or cluster resources.

## Ordering principle

Later stages may refine earlier interfaces, but they must not make superseded prose current again
or allow prose to actuate the cluster directly.
