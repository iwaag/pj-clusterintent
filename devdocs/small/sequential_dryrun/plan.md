# Sequential Desired-State Planning — Implementation Plan

## Goal

Make `nctl desired apply` correctly preview atomic batches whose operations
depend on records created earlier in the same logical batch.

Keep the preview small: report resolvable identities and planned
create/update/delete actions. Do not build a second execution engine or
simulate external actuation.

## Current Problem

`nintent` plans each operation against the current database. It has a partial
fallback for references created by the same batch, but the fallback requires
every reference on an operation to be batch-created.

This rejects a valid mixed case:

```text
create DesiredNode agdummy in this batch
use existing DesiredComputePlatform aghub-pve
create DesiredComputeInstance for agdummy
```

The compute instance is incorrectly reported as
`unresolved desired_node reference: 'agdummy'`.

## Target Contract

For every model reference in a batch operation, the planner accepts the
reference when either:

1. the target already exists in the database; or
2. the target has an `upsert` identity in the same batch and its kind can be
   created before the dependent kind.

A reference that satisfies neither condition is a conflict. Mixed existing
and batch-created references are normal.

The preview remains advisory. Final model validation, transaction behavior,
concurrent-state checks, and external effects belong to apply.

## Implementation

### 1. Add one generic planned-reference resolver

Replace the all-or-nothing `_references_are_planned()` fallback with a resolver
that evaluates each reference independently against:

- the current database;
- the batch's upsert identity index; and
- the existing `KIND_ORDER`.

A small symbol table, resolver object, or equivalent implementation is fine.
Reuse `_REFERENCE_KIND` and the canonical identity format where useful.

The resolver should return enough information for `plan_batch()` to distinguish
an existing row, a valid future row, and a missing reference. It does not need
to construct or save temporary Django objects.

### 2. Keep planning and application responsibilities separate

Use the resolver only to compute plan actions and conflicts. Preserve the
current atomic apply flow: ordered upserts, reverse-ordered deletes,
`full_clean()`, and transaction rollback on failure.

Do not reproduce model validation in the resolver. If cheap validation can be
shared cleanly, use it; otherwise apply remains the authoritative final check.

### 3. Cover mixed dependency chains

Add focused runtime tests for:

- a new node plus endpoint in one batch;
- a new node plus compute instance referencing an existing platform;
- a new node, endpoint, and compute instance in one batch;
- a genuinely missing node or platform reference;
- dry-run producing the expected actions without database writes; and
- apply committing the valid chain atomically or rolling it all back on final
  validation failure.

Prefer representative dependency shapes over one test for every model kind.
Add another case only when it exposes a different resolver rule.

### 4. Replay the reported case

After deploying the `nintent` change to the scratch Nautobot environment, run
the existing `agdummy` batch:

```bash
uv run --project nctl nctl desired apply \
  -f .local/workspace/brainforge/2026-07-30_974e/sources/agdummy-desired-state.yaml \
  --json
```

The plan should report three creates and no conflicts. Committing the desired
state and reconciling Proxmox remain separate operator decisions.

## Minimal Constraints

- Do not add per-resource exceptions for `agdummy` or compute instances.
- Do not make preview write transient database rows.
- Do not extend this work into SSH, Ansible, or Proxmox dry-run simulation.

Implementation structure, helper names, test placement, and refactoring scope
are left to the implementer.

## Verification

Run the focused nintent batch tests and the documented Nautobot runtime gate.
Confirm the exact `agdummy` dry-run against scratch Nautobot.

Completion requires:

- mixed existing and batch-created references plan successfully;
- missing references remain clear conflicts;
- dry-run performs no desired-state writes;
- valid apply remains atomic; and
- the implementation uses one general dependency rule rather than accumulating
  special-case dry-run paths.
