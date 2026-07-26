# Test Strategy Phase 2 — Step 1 Report: Domain-Owned Tier B Table

Parent: [plan.md](plan.md), Step 1.

Status: **`complete`**.

## Consolidation

Converted the `ansible_agdev` root-owned `nodeutils-pvesh-read` helper's `validate_path` rules
into one Tier B `domain_contract` table. The table has stable lowercase-kebab-case subtest IDs
for all allowlisted paths, rejected path forms, wrong argument cardinalities, and the empty-path
case. Each row asserts either the normalized path or its stable `SystemExit` diagnostic.

The nearby contract comment identifies `validate_path` as the authority and explicitly excludes
the separate exec construction and real privileged-helper boundary proofs. The latter tests remain
standalone and unchanged. No Tier A case from the Phase 0 manifest is adjacent to this file.

This is a selected family, not a deletion quota: other Tier B candidate families remain unchanged
until their authority boundaries and distinct outcomes have their own ledger-backed review.

## Verification

- Pre-change focused helper suite: 8 passed.
- Post-change focused helper suite: 4 passed; all table rows ran as named `subTest` cases.
- Ordinary `ansible_agdev` helper suite: 4 passed.

The private ledger and contract-table map record the five former test IDs, retained assertions,
row IDs, input classes, diagnostics, and commands under
`.local/test-strategy/p2/20260726T144434Z/`.

No production behavior, Ansible execution, helper deployment, external target, or secret-bearing
data was touched.
