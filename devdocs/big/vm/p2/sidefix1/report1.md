# Phase 2 Sidefix1 Step 1 Report: Centralize Preview Ownership

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 1 ("Centralize preview
ownership").

## 1. Lower-level `dry_run` save-suppression removed (fixplan Section 5.1, Step 1)

Removed the `dry_run: bool` parameter and every `if not dry_run: save_fn(...)` guard from the
persistence core, per the plan's preferred shape ("remove save-suppression branching from the
lower layers"):

- `proxmox_upsert.upsert_with_freshness()` — the create branch (was `proxmox_upsert.py:291`) and
  update branch (was `:324`) now call `save_fn()` unconditionally.
- `proxmox_upsert.ingest_proxmox_platform()` — no longer accepts `dry_run`; no longer forwards it
  to either `upsert_with_freshness()` call (Cluster, VM) or to `sync_guest_interfaces()`; the
  interface-evidence merge save (was `:566`) and the Cluster `observation_state`/
  `observation_detail` finalize save (was `:582`) now call `save_fn()` unconditionally.
- `proxmox_interfaces.sync_guest_interfaces()` — no longer accepts `dry_run`; its four guarded
  `save_fn()` calls (new-interface create, immediate IP-evidence save, existing-interface
  field-diff update, presence-absence convergence) now call `save_fn()` unconditionally.

`proxmox_interfaces.sync_interface_ips()` already had no `dry_run` parameter (Section 0 audit) and
is unchanged — it always ran `create_ip`/`attach_ip`/`detach_ip`. The lower layers now have exactly
one apply behavior, matching that function's existing shape instead of the mixed one.

## 2. Job wiring updated (fixplan Section 5.1 items 2, 6)

- `ingest_nodeutils_inventory.py`'s call into `ingest_proxmox_platform()` no longer passes
  `dry_run=self.dry_run` (the kwarg no longer exists on the callee).
- The `dry_run` `BooleanVar` description changed from *"Log planned changes without writing to
  Nautobot."* to *"Run the normal persistence path without committing target changes to
  Nautobot."*, matching the plan's required operational-contract wording.
- `run()`'s existing `transaction.atomic()` ownership, `transaction.set_rollback(True)` on
  `dry_run=True`, and the Job summary/log artifact creation after the atomic block are unchanged —
  this was already the target shape per Section 5.1 items 1/3/5/6 and needed no edit.
- The early return in `ingest_report()` (`if self.dry_run: return result`, still at line 253) is
  intentionally **not** touched in this step — removing it is Step 2's scope. Its practical effect
  right now: preview mode still never reaches the now-unconditional persistence core, so this
  step's edits do not change apply-mode behavior and do not yet fix the Step 9 blocker.

## 3. Fake-ORM tests updated (fixplan Section 6.2)

`upsert_with_freshness()`/`ingest_proxmox_platform()`/`sync_guest_interfaces()` are pure functions
with no notion of "preview" anymore, so their `dry_run` kwarg was removed from every call site in
`test_proxmox_cluster_vm_upsert.py` and `test_proxmox_interface_ip_upsert.py`.

`DryRunTests.test_dry_run_plans_without_writing` (asserted a list-based fake store stayed empty
under `dry_run=True`) was removed per the plan's explicit instruction: *"Remove or rewrite fake-ORM
tests that expect `dry_run=true` to leave fake stores empty. A list-based fake store has no real
transaction semantics and must not be treated as proof of rollback."* Preview safety is tested at
the Job-owned real transaction boundary in a later step (fixplan Section 6.3), not here.

## 4. Verification

```
cd nauto
python3 -m py_compile jobs/*.py
# no output (success)
python3 -m unittest discover -s tests
# Ran 90 tests in 0.009s
# FAILED (failures=1)
```

The single failure is the Step 0 red test
(`test_ingest_nodeutils_inventory_job.DryRunProxmoxSectionTest.test_preview_reaches_proxmox_ingest_for_an_existing_device`),
unchanged and still red as expected — Step 1 only removes lower-level save suppression, it does not
touch the Job-level early return that causes it. All 89 other tests (including the retargeted
`test_proxmox_cluster_vm_upsert.py`/`test_proxmox_interface_ip_upsert.py`) pass, confirming the
persistence core's create/update/no-op/stale/conflict/interface/IP behavior is unchanged for the
apply path.

`git diff --check` reported nothing; only the four files above changed in `nauto`.

## Gate

- Lower-level Proxmox ingest has one apply behavior: proven — no `dry_run` parameter or branch
  remains anywhere in `proxmox_upsert.py`/`proxmox_interfaces.py` (confirmed by `grep`).
- `dry_run=true` can only be safe through the Job-owned rollback boundary: proven by construction —
  the persistence core can no longer suppress a save on its own; the only place that can still stop
  a commit is `IngestNodeutilsInventory.run()`'s `transaction.atomic()`/`set_rollback(True)`.

Step 1 is satisfied. Proceeding to Step 2 (repair Job orchestration: remove the early return, run
Device/Proxmox handling in one order) remains gated behind this step's own review.
