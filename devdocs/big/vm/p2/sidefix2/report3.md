# Phase 2 Sidefix2 Step 3 Report: Make Guest Summaries Transaction-Truthful

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`plan.md`](plan.md) Step 3 ("Make guest summaries transaction-truthful").

## 1. Guest-local accumulators (plan Section 3.6)

`jobs/proxmox_upsert.py`'s `ingest_proxmox_platform()` per-guest loop now allocates local state
before entering `guest_atomic()`:

```python
guest_counts = {kind: {a: 0 for a in (...)} for kind in ("vm", "vminterface", "ip")}
guest_changed_fields: dict[str, list[str]] = {}
guest_non_terminal_errors: list[dict[str, str]] = []
```

Every write that used to go straight into the platform-level `counts`/`changed_fields`/
`guest_errors` inside the `try: with guest_atomic():` block (the VM upsert count/changed-fields,
the interface/IP counts, the non-terminal interface/IP conflict errors, and the
`proxmox_interface_evidence` changed-field claim) now goes into these guest-local containers
instead — nothing platform-level is touched while the guest's own transaction is still open.

## 2. Merge only after savepoint success

```python
try:
    with guest_atomic():
        ...  # writes only guest_counts / guest_changed_fields / guest_non_terminal_errors
except Exception as exc:
    platform_partial = True
    counts["vm"]["skipped"] += 1
    ...  # one bounded terminal guest_errors entry; guest_counts/guest_changed_fields discarded
else:
    for kind in ("vm", "vminterface", "ip"):
        for action, value in guest_counts[kind].items():
            counts[kind][action] += value
    changed_fields.update(guest_changed_fields)
    guest_errors.extend(guest_non_terminal_errors)
```

The `else:` clause on the `try` runs only when the `with guest_atomic():` body completed without
raising, which is exactly "the savepoint exited successfully" — Python guarantees `else` never
runs if the `try` block (including everything inside the `with`) raised. If it raised, the local
`guest_counts`/`guest_changed_fields`/`guest_non_terminal_errors` for that guest simply go out of
scope at the end of the loop iteration and are never merged — this is the fix for the exact
count-leak `report0.md` Section 4 reproduced: an exception after `vm_outcome` was already counted
no longer leaves `vm.created` incremented in addition to `vm.skipped`.

Known candidate conflicts (`ip_parent_prefix_missing`, `ip_address_ambiguous`,
`ip_observed_prefix_ambiguous`, `managed_ip_reference_unresolved`, `foreign_ip_relation`) are
never exceptions — `sync_interface_ips()` returns them as `IpSyncOutcome.conflicts`/errors without
raising, so they still merge normally as part of a successful guest, matching plan Section 3.5:
"they do not add `vm.skipped` and do not erase the VM/VMInterface."

Cluster counts/changed-fields (set before the guest loop starts, at the platform scope) were left
untouched — the plan is explicit that "Cluster counts remain outside guest accumulators because
the Cluster transaction is intentionally platform-scoped."

## 3. Tests

No new test file was needed: the Step 0 regression test
(`test_failure_after_vm_upsert_does_not_leave_a_created_count` in
`tests/test_ip_namespace_host_identity.py`), which asserted `vm.created == 0` and
`vm.skipped == 1` after a simulated failure inside `resolve_host()` following a successful VM
upsert, now passes for the first time since it was added in Step 0.

```
cd nauto
python3 -m unittest discover -s tests
# Ran 101 tests in 0.010s, OK
python3 -m py_compile jobs/*.py
# no output (success)
git diff --check
# no output (success)
```

All 101 tests pass — the last remaining Step 0/1/2 red test is now green, and nothing else
regressed. This also matches the pre-existing `test_guest_savepoint_exception_rolls_back_only_that_guest`
/ `test_one_bad_guest_isolated_others_committed` tests in `tests/test_proxmox_cluster_vm_upsert.py`,
which cover the case where `guest_atomic()` itself raises before the guest body runs at all (no
`guest_counts` were ever populated in that case either way) — both styles of failure are now
covered.

## Gate

- Object counts and `changed_fields` reproduce the state that would commit; no failed guest is
  double-counted: proven (Section 2, Section 3).
- No live-state change: proven — Section 3's exact command output; no Nautobot write, `aghub`
  call, or Proxmox mutation occurred.

Step 3 is satisfied. Proceeding to Step 4 (focused and real-ORM test rounds) remains gated behind
this step's own review.
