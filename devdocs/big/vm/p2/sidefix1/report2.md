# Phase 2 Sidefix1 Step 2 Report: Repair Job Orchestration

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 2 ("Repair Job orchestration").

## 1. Early return removed; one Device/Proxmox path for existing observers (fixplan Section 5.2)

`ingest_nodeutils_inventory.py`'s `ingest_report()` no longer has `if self.dry_run: return result`.
It now always runs, in this order, for both preview and apply:

1. match/diff the Device;
2. run the Device create/update/no-op through the normal persistence path;
3. read `facts.proxmox`;
4. for an existing observer Device, call `ingest_proxmox()` once when the subtree is a mapping;
5. return the combined Device + Proxmox result.

This is the exact ordering the plan requires, and it is now identical in both modes — the Job-owned
`transaction.atomic()`/`set_rollback(True)` boundary from Step 1 is what makes `dry_run=true` safe,
not a branch inside `ingest_report()`.

## 2. New-observer two-stage precondition (fixplan Section 4.4 / 5.2)

Added `device_is_new = device is None`, tracked separately from the (now reassigned) `device`
local, and a new `build_new_device_proxmox_precondition()` method used only when
`device_is_new and isinstance(proxmox_facts, dict)`:

- the Device create still runs normally (so its diff/creation is fully previewed like any other
  Device);
- `ingest_proxmox()` — and therefore any Cluster/VM/VMInterface/IP matching — is **not** called;
- the returned `proxmox` section uses the same bounded shape as `ingest_proxmox()`'s own
  precondition-failure paths (`identity_source`, `scope_key=None`, `cluster_name`, `cluster_id=None`,
  `observation_state="partial"`, zeroed `object_counts`, empty `changed_fields`,
  `guest_errors=[{"scope_kind": "platform", "scope_id": "cluster", "section": "cluster_identity",
  "code": "observer_device_not_persisted"}]`);
- `cluster_name`/`identity_source` are read from the pure `validate_proxmox_facts()` parse only, for
  operator-readable context — never used to derive or claim a `scope_key`, matching the plan's "do
  not claim an exact Proxmox Cluster scope preview."

Device-only reports (`facts.proxmox` absent or not a mapping) are unaffected either way — no
`proxmox` key is added, matching current behavior exactly.

## 3. Fast orchestration tests (fixplan Section 6.1)

Extended `nauto/tests/test_ingest_nodeutils_inventory_job.py` (added in Step 0 as the red test) to
cover items 1-4 of the plan's mode-boundary checklist, all against the real `ingest_report()` with
`ingest_proxmox()`/`create_device()`/`update_device()` mocked:

| Test | Item | Result |
|---|---|---|
| `test_preview_reaches_proxmox_ingest_for_an_existing_device` | 1 | now passes (was Step 0's red test) |
| `test_apply_reaches_proxmox_ingest_for_an_existing_device` | 2 | passes (same core calls/order as preview) |
| `test_device_only_report_is_unchanged_and_has_no_proxmox_section` | 3 | passes (no `proxmox` key, `outcome="unchanged"`) |
| `test_new_device_reports_a_truthful_precondition_not_a_proxmox_scope` | 4 | passes (`ingest_proxmox` not called, precondition shape asserted field-by-field) |

Item 5 (exception before completion leaves the outer atomic block uncommitted) requires the real
`transaction.atomic()`/rollback semantics this Django-free harness stubs out as a no-op context
manager; it is deferred to the real-ORM verification in fixplan Step 4/Section 6.3, per the plan's
own note that a real transaction boundary — not a fake store — is what proves rollback.

## 4. Verification

```
cd nauto
python3 -m py_compile jobs/*.py
# no output (success)
python3 -m unittest discover -s tests
# Ran 92 tests in 0.011s
# OK
```

All 92 tests pass, including the four Job-level orchestration tests above and the full existing
`test_proxmox_cluster_vm_upsert.py`/`test_proxmox_interface_ip_upsert.py`/`test_nodeutils_ingest_summary.py`
suites untouched by this step. `git diff --check` reported nothing; only
`jobs/ingest_nodeutils_inventory.py` and `tests/test_ingest_nodeutils_inventory_job.py` changed.

## Gate

- The existing `aghub` preview reaches the complete Proxmox path exactly once: proven by
  `test_preview_reaches_proxmox_ingest_for_an_existing_device` (unit level; the real-ORM equivalent
  is fixplan Step 4).
- Device-only behavior remains compatible: proven by
  `test_device_only_report_is_unchanged_and_has_no_proxmox_section`.

Step 2 is satisfied. Proceeding to Step 3 (sanitize preview evidence: null out rolled-back created
IDs) remains gated behind this step's own review.
