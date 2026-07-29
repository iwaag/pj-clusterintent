# Braindump supersession — implementation plan

Date: 2026-07-29

## Goal

Provide the sole supported way to change current Braindump Ground Truth: create a new immutable
Braindump and atomically mark explicitly selected old Braindumps as reference-only.

This plan assumes the immutable-Braindump plan has been completed.

## Target contract

Add one field to `BrainDumpDocument`:

```text
status = active | superseded
```

- New Braindumps default to `active`.
- The only supported transition is `active -> superseded`.
- Normal Brainforge/list reads use active Braindumps.
- Superseded Braindumps remain available through direct show and an explicit
  `--include-superseded` list option.
- Body format remains unrestricted natural language.  No contradiction parser, subject schema, or
  positive/negative grammar is introduced.
- Supersession changes no Desired, Actual, drift, reconcile, or cluster state.

## Replacement operation

Add an nctl operation shaped approximately as:

```text
nctl braindump supersede
  --old OLD_ID [--old OLD_ID ...]
  --title TITLE
  --authorship user_direct|agent_transcribed
  (--body TEXT | --file PATH)
```

The server-side operation should run in one database transaction:

1. resolve the exact old IDs and require them to be active;
2. create the replacement as active;
3. mark the selected old rows superseded; and
4. return the new ID and superseded IDs.

If any step fails, keep the old rows active and do not retain the replacement.  Exact endpoint,
locking method, response envelope, and internal function layout are left to the implementer.
Generic status PATCH should not become a second transition path.

No persistent successor/predecessor relation is required.  The replacement prose may combine
unchanged wishes with changed, withdrawn, or negative wishes, subject to normal Brainforge user
confirmation.

## Implementation

### 1. Extend nintent

Add the status choices, default, migration, GraphQL/REST read projection, list filter, and table
display needed to inspect the state.  Add the transactional replacement operation to the narrow
REST boundary used by nctl.

Keep physical DELETE and content PATCH unsupported.

### 2. Extend nctl reads and writes

- Add status to typed Braindump records and output.
- Make ordinary list return active documents.
- Add `--include-superseded`.
- Add the supersede command, input validation, response confirmation, and readable/JSON output.
- Keep direct show valid for either status.

The active-list default, rather than agent memory, is the authoritative current-context filter.

### 3. Update Brainforge

The standard loop should:

1. read active Braindumps;
2. draft a replacement from the user's old and new statements;
3. show the replacement text and exact old IDs to the user;
4. run supersede only after confirmation; and
5. write a new Alignment Review for the replacement as needed.

Do not infer structured Desired changes from the status transition.

### 4. Verify

Cover the following distinct behavior:

- new rows default active;
- successful replacement creates one active row and supersedes exactly the selected old rows;
- invalid or already-superseded old IDs leave all rows unchanged;
- transaction failure leaves no partial replacement;
- ordinary list excludes superseded rows while explicit list/show can read them;
- content update and physical delete remain unavailable; and
- supersession produces no Desired/Actual mutation or drift/reconcile action.

Run affected nctl and nintent suites plus the reusable Nautobot runtime gate.  A live Proxmox or
Ansible test is unnecessary because this feature must not reach those boundaries.

## Out of scope

- deciding contradictions automatically;
- Desired retirement, unmanaged classification, resource destruction, and pruning;
- Braindump physical-deletion eligibility; and
- long-term archival, version history, or general workflow machinery.

