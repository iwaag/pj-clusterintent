# Phase 2 Sidefix1 Step 5 Report: Prove Preview/Apply/Repeat Parity

Status: implemented and environment-backed (Rounds B and C). Not deployed to the tracked `nauto`
Git Repository and no live `aghub`/Proxmox action was taken.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 5 ("Prove preview/apply/repeat
parity"). Like Step 4, this step touches the local Nautobot environment. Raw evidence lives in
`.local/vm-p2/sidefix1-step5/` (mode `0700`/`0600`, gitignored).

## 1. A test-methodology incident, corrected before this evidence was recorded

The first attempt at Round B used `transaction.savepoint()`/`transaction.savepoint_rollback()`
**without** an enclosing `transaction.atomic()` block. Django's `savepoint()` is only meaningful
inside an active atomic block; outside one, it does not protect against a commit. Round B's
`dry_run=false` apply call therefore **committed for real**: a Cluster/VM/VMInterface/IPAddress
were actually created, and — more seriously — the same call's Device-update path overwrote 6 real
fields on the pre-existing `aghub` Device (`comments`, and custom fields `last_seen`, `os_name`,
`os_version`, `ai_resource_summary`, `inventory_raw_json`) with values derived from this step's
synthetic test fixture.

This was caught immediately (a follow-up query showed non-zero Cluster/VM/VMInterface/IP counts
that should have been zero after "rollback"). The test-created Cluster/VM/VMInterface/IP rows were
deleted. The real `aghub` Device's overwritten fields were recovered exactly from Nautobot's own
`ObjectChange` audit log (its last real update, `2026-07-23T13:18:25Z`, by user `iwaag`) and
restored field-by-field, then verified equal to the recovered values. The user approved this
restore and confirmed the local dev Nautobot is an experimental environment: data changes there are
acceptable as long as the root cause is fixed and reported, which this section does.

**Root cause and fix**: every round in the corrected script now runs inside `with
transaction.atomic():` and forces its own rollback by raising a sentinel `RuntimeError` at the end
of the block (caught immediately outside it) — the officially-supported Django pattern, matching
`report2.7.md`'s own technique, rather than a bare, unenclosed savepoint pair. A live sanity check
now also confirms the two most distinctive `aghub` fields those never leave the corrected script
without verifying (`last_seen`, `os_name`) still equal their known-good values before declaring the
round done.

## 2. Round B — rollback-contained apply proof (fixplan Section 6.3, Round B)

Same fixture as Step 4 (`report4.md`): real `aghub` Device, `agdnsmasq` LXC vmid 108, static IP
`192.168.0.99/24`. Called with `dry_run=false` inside the corrected `transaction.atomic()` block:

| Check | Result |
|---|---|
| `object_counts` | `cluster.created=1, vm.created=1, vminterface.created=1, ip.created=1` — identical to Round A's preview counts |
| `scope_key` | `standalone-device:fcebe565-6aeb-40b1-ba51-4bde1e1065bc` — identical to Round A |
| `changed_fields` keys | `{"cluster", "vm:lxc:108"}` — identical shape to Round A |
| `cluster_id` | a real, non-null UUID (`c2f170f4-...`) — as required, apply reports the real id (only preview sanitizes it, per Step 3) |
| refetch | `Cluster.name="aghub-proxmox"`, `VirtualMachine.name="agdnsmasq"`, `VMInterface.mac_address="bc:24:11:23:dc:b7"`, `IPAddress` at `192.168.0.99/24` — all confirmed by direct query while still inside the transaction |
| post-rollback counts | `0/0/0/0` — back to the before image |

Round A (Step 4, preview) and Round B (this step, apply) agree exactly on stable targets, counts,
and changed fields, differing only in the one field Step 3 designed to differ: `cluster_id`.

## 3. Round C — identical repeat (fixplan Section 6.3, Round C)

Within one further `transaction.atomic()` block: applied the fixture once, captured
`cluster`/`vm`/`vminterface` ids and `last_updated` timestamps, applied the byte-identical report a
second time, and compared:

| Check | Result |
|---|---|
| second apply's `object_counts` | `cluster.unchanged=1, vm.unchanged=1, vminterface.unchanged=1, ip` all `0` — a true no-op |
| ids | identical between the two snapshots (`cluster_id`, `vm_id`, `iface_id`) |
| `last_updated` | identical between the two snapshots for both Cluster and VM |

Rolled back cleanly afterward; post-rollback counts `0/0/0/0` again.

## 4. Full suite

```
cd nauto
python3 -m py_compile jobs/*.py
# no output (success)
python3 -m unittest discover -s tests
# Ran 95 tests in 0.009s
# OK
```

No `nctl`/`nodeutils`/`ansible_agdev` file changed in sidefix1, so per Section 6.5 their suites were
not re-run.

## 5. Post-run state confirmation

After both rounds' rollbacks, `Cluster.objects.count() == VirtualMachine.objects.count() ==
VMInterface.objects.count() == IPAddress.objects.filter(host="192.168.0.99").count() == 0`, and the
real `aghub` Device's `custom_field_data["last_seen"]`/`["os_name"]` were re-verified equal to the
exact pre-incident values (`"2026-07-23T13:18:03+00:00"` / `"Debian GNU/Linux 13 (trixie)"`) inside
the same corrected script run — both the test's own writes and the earlier incident's writes are
fully absent from the database at the end of this step.

## Gate

- Preview and apply stable targets/counts agree: proven (Section 2).
- Apply produces the exact intended graph: proven (Section 2 refetch).
- Identical repeat is a no-op: proven (Section 3).
- The test-owned transaction leaves no persistent fixture: proven (Section 5), and the one instance
  where it briefly did not (Section 1) has been corrected and fully repaired.

Step 5 is satisfied. Proceeding to Step 6 (review, commit, and deploy nauto) is a coordinated
deployment step per the fixplan (push approval, Nautobot Git Repository sync, installed-revision
confirmation) and remains gated behind its own separate review.
