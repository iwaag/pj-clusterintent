# Test Strategy Phase 3 — Step 4 Report: Exact-Local-Source Nautobot Runtime Gate

Parent: [plan.md](plan.md), Step 4.

Status: **`complete`**.

## Exact-source runtime and nintent gate

The persistent scratch image carries old installed `nintent` revision `e873…`; the checked-out
revision is `2c1…`. The runtime gate therefore copies only test-owned source to container `/tmp`
and sets `PYTHONPATH` explicitly. Module resolution confirmed the local path, and
`makemigrations --check --dry-run` found no changes. The full local-source nintent App suite ran
against the named `test_nautobot` database: **279 passed**. The ordinary test database is not
used.

## nauto real-ORM proof and correction

Added `nauto/tests_runtime/test_ingest_runtime.py`, run only through the Nautobot runtime. It
seeds only the test database and proves a real ORM path for:

- valid nodeutils report → Device create;
- byte-identical report → semantic no-op with unchanged `last_updated`;
- stale report → skipped with no extra Device;
- existing observer plus valid Proxmox platform → Cluster create;
- byte-identical Proxmox report → unchanged Cluster; and
- unsupported Proxmox schema → bounded error with no additional Cluster.
- valid sibling guest survives while a malformed guest is isolated as a target-local partial
  diagnostic; and
- a real Nautobot model constraint failure rolls back only its guest savepoint, retains
  `guest_upsert_failed`, and leaves the valid sibling persisted.

`nctl/tests/test_reconcile_planner.py` now also has the maintained missing-desired no-delete
proof: an actual-only Device passes the real node evaluator and planner twice with no diff,
action, manual-review, or unsupported record. There is no deletion, unlink, retirement, or
replacement reconciler available for an observation outside desired state.

This gate exposed a bounded production defect: `diff_device()` compared a `description` payload
key that Nautobot 3's `Device` model does not have. Create/update correctly omitted it, but every
identical repeat was falsely reported as an update. The correction now compares only actual model
fields; ordinary nauto tests (**110 passed**) and the real-ORM gate (**2 passed**) pass.

## Remaining Step 4 work

The Phase 0 manifest's former no-delete test ID was absent from this checkout. The maintained
replacement above is now its current primary owner; the private Phase 3 work queue records that
resolution rather than relying on historical one-off evidence.

## Isolation

All runtime source copies were under `/tmp/p3-nintent` and `/tmp/p3-nauto`; test rows were owned
by Django's `test_nautobot` transaction. No deployed package, ordinary database, external host,
real inventory, or secret was read or changed.
