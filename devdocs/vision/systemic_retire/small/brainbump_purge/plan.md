# Braindump purge — implementation plan

Date: 2026-07-30

## Goal

Allow an explicitly approved, already superseded Braindump to be physically
deleted immediately.  There is no soft-delete state, retention period,
scheduler, archive, or recovery path.  This is an experimental environment;
keep the implementation small.

## Contract

Add a narrow nctl operation:

```text
nctl braindump purge BRAINDUMP_ID          # show the exact deletion plan
nctl braindump purge BRAINDUMP_ID --yes    # delete it now
```

- Only an exact `status=superseded` Braindump is eligible.  `active` is
  rejected, so the current Brainforge context cannot be removed by this path.
- The dry run reads and shows the selected document and whether it has an
  Alignment Review; it writes nothing.
- Apply re-reads the exact ID and status, then deletes that document and its
  one-to-one Alignment Review in one database transaction.
- A missing target is a successful `already_purged` no-op.  A changed-to-active
  target is rejected.
- The operation affects only Braindump rows.  It must not change Desired,
  Actual, drift, reconcile, operation evidence, or cluster infrastructure.

`--yes` is the sole execution confirmation.  Do not add retention policies,
role workflows, deletion queues, cryptographic receipts, or database-level
tamper controls.

## Implementation

### 1. nintent

Keep ordinary Braindump REST `DELETE` unavailable.  Add one dedicated purge
endpoint that accepts an exact document UUID, checks that it is superseded,
and deletes it transactionally.  Return a small result distinguishing
`purged`, `already_purged`, and ineligible input.

### 2. nctl

Add `braindump purge` with normal text and JSON output.  The command first
obtains the server-side plan; `--yes` applies that exact target.  Reuse the
existing CLI confirmation convention.  Do not add a new persistent nctl
operation type unless the existing command boundary requires one.

### 3. Brainforge guidance

Before requesting purge, the agent must show the superseded document and ask
whether any part is still useful for current cluster operation.  Temporary
history such as a removed hostname may be transcribed into the current
operational-context Braindump, with a reason and removal condition.  Purge is
appropriate only after the user says the old document itself is no longer
useful.

## Verification

Cover these cases:

- dry run identifies one superseded row and does not mutate it;
- apply removes that row and its review;
- active rows are rejected and remain readable;
- a repeated purge returns `already_purged` without widening its scope; and
- Desired/Actual reads and drift are unchanged by a purge.

Run the affected nctl and nintent suites plus the reusable Nautobot runtime
gate.  No Proxmox, Ansible, retention timer, or external-service test is
needed.

## Out of scope

- scheduled deletion, grace periods, undo, archival, and version retention;
- purging an active Braindump;
- changing supersession semantics; and
- any Desired, Actual, or resource retirement behavior.
