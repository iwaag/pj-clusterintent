# Immutable Braindump — implementation plan

Date: 2026-07-29

## Goal

Make a created Braindump an immutable user statement.  Preserve create and read operations, remove
supported content-update and physical-delete operations, and leave supersession for the next
initiative.

This applies to `BrainDumpDocument`, not to the separately owned Alignment Review.

## Current state

- The Nautobot UI already exposes only Braindump list and detail views.
- The REST ViewSet permits `GET`, `POST`, detail `PATCH`, and detail `DELETE`.
- The serializer permits writes to `title`, `body`, and `authorship`.
- nctl exposes `braindump update` and `braindump delete`.
- The model itself has no content-immutability rule.

## Target contract

- `POST` creates one Braindump with fixed `title`, `body`, and `authorship`.
- Reads continue through GraphQL, REST GET, Nautobot list/detail UI, and nctl list/show.
- REST PATCH/PUT/DELETE and bulk mutations are unsupported for Braindumps.
- `nctl braindump update` and `nctl braindump delete` are removed, including their dedicated
  client/core/render/schema/error paths when no longer used.
- Direct database administration is outside the public contract; do not add database triggers or
  elaborate tamper controls for this experimental environment.
- Alignment Review create/replace/delete behavior remains unchanged in this initiative.
- Braindump changes continue to have zero effect on drift, reconcile, Desired state, or Actual
  state.

## Implementation

### 1. Narrow the nintent write surface

Change `BrainDumpDocumentViewSet` to allow GET and POST only.  Remove partial-update and destroy
handling.  Keep serializer validation for creation, but expose no update fields for an existing
instance.

No migration is required in this initiative.

### 2. Remove nctl mutation paths

Remove the `braindump update` and `braindump delete` commands and the code used only by them.
Update command help, frozen output contracts, and documentation in the same coordinated change;
do not retain deprecated aliases or compatibility shims.

Keep `list`, `show`, `create`, `review`, and `review-delete`.

### 3. Update Brainforge guidance

State that a mistaken, incomplete, or changed Braindump is corrected by creating another
Braindump.  Until supersession is implemented, both remain visible; agents must ask the user when
their relationship is ambiguous.

### 4. Verify

Add focused tests proving:

- creation and all read surfaces still work;
- REST PATCH, PUT, and DELETE are rejected;
- removed nctl commands are ordinary unknown commands;
- the UI remains read-only; and
- creating another Braindump changes no drift or reconcile input.

Run the affected nctl tests, nintent fast tests, and the reusable Nautobot runtime gate.  Exact test
placement and helper boundaries are left to the implementer.

## Out of scope

- active/superseded state and replacement transactions;
- deletion eligibility or garbage collection;
- Desired retirement and Actual resource deletion; and
- enforcing immutability against unsupported direct ORM or database writes.

