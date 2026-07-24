# Phase 2 Sidefix2 Step 4 Report: Prove Focused and Real-ORM Behavior

Status: implemented and environment-backed. Not deployed to the tracked `nauto` Git Repository and
no live `aghub`/Proxmox action was taken. No persisted Nautobot state changed — proven directly by
this step's own before/after checks. The user confirmed running real-ORM writes (rollback-wrapped)
against the local Nautobot container before this step proceeded.

This report covers [`plan.md`](plan.md) Step 4 ("Prove focused and real-ORM behavior") — Section
5.1 (already exercised across Steps 0-3's own reports), Section 5.2 (Rounds A-D, this step's main
content), and Section 5.4 (repository commands).

## 1. Pure and fake-ORM tests (plan Section 5.1)

Already added incrementally in [`report0.md`](report0.md)-[`report3.md`](report3.md). Full-suite
confirmation as of this step:

```
cd nauto
python3 -m unittest tests.test_proxmox_cluster_vm_upsert tests.test_proxmox_interface_ip_upsert \
  tests.test_ingest_nodeutils_inventory_job tests.test_nodeutils_ingest_summary
# Ran 69 tests in 0.006s, OK
python3 -m unittest discover -s tests
# Ran 101 tests in 0.009s, OK
python3 -m py_compile jobs/*.py
# no output (success)
```

All 15 required focused cases from Section 5.1 are covered across the four fake-ORM test files
touched in Steps 0-3 (`test_ip_namespace_host_identity.py`,
`test_proxmox_interface_ip_upsert.py`).

## 2. Real Nautobot ORM Rounds A-D (plan Section 5.2)

### Method

Followed sidefix1 `report4.md`'s established technique: copied the current `nauto` worktree
(commit at the head of Step 3) into the running `nautobot-nautobot-1` container at
`/tmp/nauto_review` with a neutralized `jobs/__init__.py` (no `register_jobs()` call — no Job
database record created or altered), then called `proxmox_upsert.ingest_proxmox_platform()`
directly from `nautobot-server shell` with real `Cluster`/`VirtualMachine`/`VMInterface`/
`IPAddress`/`Namespace`/`Prefix`/`IPAddressToInterface` managers and the exact same
`resolve_host`/`find_parent_prefix`/`create_ip`/`find_ip_by_id`/`ip_related_elsewhere`/
`attach_ip`/`detach_ip` closures `jobs/ingest_nodeutils_inventory.py` wires in production. Calling
the pure orchestration function directly (rather than the full `Job.run()`) is a faithful
substitute here because Steps 1-3's changes are entirely inside that function and the modules it
calls — no report-parsing/policy/identity-matching code changed in this sidefix — and it let every
round run inside one shared outer `transaction.savepoint()`, with a `finally:
transaction.savepoint_rollback(sid); transaction.set_rollback(True)` as defense-in-depth beyond
the savepoint itself, exactly mirroring sidefix1's Round A method.

Real, already-seeded fixtures reused: `Global` Namespace, the existing `192.168.0.0/24` Prefix, the
`Proxmox VE` ClusterType, the `virtual-machine`/`lxc-container` Roles, the `Active` Status, and one
real, unrelated, pre-existing Device (`agbach.local`, read-only reference, matching sidefix1's use
of a real Device for `observer_device_id`) — the real `aghub` Device was deliberately not touched.
All test data used addresses/vmids/cluster names distinct from any real Proxmox host, and the sole
existing `192.168.0.2/32` `agdnsmasq` row was never referenced (a synthetic `192.168.0.199/32`
test-owned row was created and rolled back instead, matching the plan's "Create or select one
test-owned IPAddress" wording).

Full script and output preserved at `.local/vm-p2/sidefix2-step4/round_abcd_script.py` /
`round_abcd_output.txt` (mode `0700`/`0600`, gitignored).

### Round A — native-mask reuse

1. Created a test-owned IPAddress `192.168.0.199/32` (`dns_name=sidefix2-test-owned.example`) under
   the real `192.168.0.0/24` Prefix.
2. Ingested a synthetic LXC guest (vmid 9001) observing `192.168.0.199/24` on the same host.
3. Proved: same IP ID attached (`reused.first().pk == before_pk`), no second row
   (`IPAddress.objects.filter(host="192.168.0.199").count() == 1`), native `dns_name` unchanged,
   managed evidence `192.168.0.199/24 -> <same ID>`.
4. Repeated identically: zero new IPs, `ip.created == 0`.

### Round B — missing parent Prefix

1. Confirmed via the real `Prefix.objects.filter(namespace=...).get_closest_parent(...,
   include_self=True)` call that no Prefix covers a synthetic test-only IPv6 address
   (`2401:aaaa:bbbb:cccc::1`).
2. Ingested one QEMU guest (vmid 9002) with that candidate alongside one valid sibling QEMU guest
   (vmid 9003, `192.168.0.198/24`).
3. Proved: `qemu:9002`'s VM committed, `guest_errors` contains `{"scope_kind": "interface",
   "scope_id": "net0", "section": "ip", "code": "ip_parent_prefix_missing"}` (never
   `guest_upsert_failed`), no IPv6 Prefix/IPAddress row created for that candidate.
4. Proved the sibling `qemu:9003` committed and got its IP attached, independent of 9002's
   conflict.

### Round C — rolled-back count truth

1. Wired a `resolve_host` that raises `RuntimeError` (simulating an unexpected interface-stage
   failure) for one guest (vmid 9004, after its VM upsert already ran inside the same guest
   savepoint).
2. Proved: `vm.created == 0`, `vm.skipped == 1`, no `VirtualMachine` row exists for vmid 9004 (the
   real `transaction.atomic()` guest savepoint actually rolled back the DB write, not just the
   in-memory counters), exactly one terminal guest error.

### Round D — prefix-only evidence transition

1. Ingested one LXC guest (vmid 9005) observing `192.168.0.196/24` — created and attached one
   `IPAddress`.
2. Re-ingested the identical guest with the same host now observed at `/32`.
3. Proved: zero new `IPAddress` rows (`ip.created == 0`), the `IPAddressToInterface` relation to
   the *same* object remains present throughout, the managed map's only key becomes
   `192.168.0.196/32` pointing at that same object's `ip_id`.
4. Repeated identically: zero further creates/updates.

### Result

```
Using observer Device: agbach.local da27c9b3-5613-412f-a71e-1a95167fda6f
=== Round A: native-mask reuse ===          7/7 PASS
=== Round B: missing parent Prefix ===      6/6 PASS
=== Round C: rolled-back count truth ===    4/4 PASS
=== Round D: prefix-only evidence ===       6/6 PASS
=== 24/24 checks passed ===
OVERALL: PASS
```

A post-run query in a fresh, separate `nautobot-server shell` invocation confirmed zero trace:
`IPAddress.objects.filter(host__in=["192.168.0.199", "192.168.0.196", "192.168.0.198"])` and
`VirtualMachine.objects.filter(name__icontains="sidefix2-round")` both returned empty — the outer
savepoint rollback left the database exactly as it was before this step.

Two test-authoring bugs were caught and fixed during this round (not code defects): the guest-error
assertions initially filtered on the wrong `scope_id` (interface conflicts are scoped to the
interface's `config_slot`, e.g. `"net0"`, not the guest's `"qemu:9002"` — only terminal guest
failures use the guest scope), and Round D's synthetic LXC guests initially shared one hardcoded
MAC address across different vmids in the same synthetic cluster, tripping the real
`mac_conflict_in_cluster()` check — each guest now gets a MAC derived from its own vmid.

## 3. `nctl` regression fixture (plan Section 4.4)

Read `nctl/src/nctl_core/actual_render.py`: IP relation classification (`managed` vs.
`unrelated_ip_ids`) is already purely `ip_id`-based (`managed_ip_ids = {entry.ip_id for entry in
...}`), never comparing native `mask_length` to the managed key's prefix — no code change needed.
Added one regression fixture proving it, since none of the existing fixtures had a native/managed
mask mismatch:

`test_render_actual_data_classifies_native_mask_mismatch_as_managed_by_id` in
`nctl/tests/test_actual_render.py` — reuses `_aghub_snapshot()` with `ip-108`'s native
`mask_length` changed from `24` to `32` (its managed evidence key stays `192.168.0.108/24`, same
`ip_id`), and asserts `managed_ip_count == 1` / `unrelated_ip_ids == ["ip-foreign"]` unchanged.

```
cd nctl
uv run --project . pytest tests/test_sources_actual.py tests/test_actual_render.py -q
# 19 passed in 0.11s (18 pre-existing + 1 new)
```

## 4. Repository commands (plan Section 5.4)

```
cd nauto
git diff --check          # no output
git status --short        # M jobs/ingest_nodeutils_inventory.py, jobs/proxmox_interfaces.py,
                           #   jobs/proxmox_upsert.py, tests/test_ip_namespace_host_identity.py,
                           #   tests/test_proxmox_interface_ip_upsert.py (all already committed
                           #   in Steps 0-3; clean at HEAD as of this step)
cd ../nctl
git diff --check          # no output
git status --short        # M tests/test_actual_render.py (this step's addition)
cd ..
git diff --check          # no output
git status --short        # clean except this report and the nctl submodule bump
```

All affected submodule diffs reviewed; no unrelated worktree was touched (`ansible_agdev`,
`nodeutils`, `nintent` untouched, matching plan Section 2.2's non-goals).

## Gate

- Both original tracebacks are replaced by their intended successful/local-conflict paths: proven
  (Round A, Round B).
- Real ORM constraints are exercised: proven (`validated_save()` ran against the real `Namespace`/
  `Prefix`/`IPAddress` uniqueness and parent-Prefix constraints throughout all four rounds).
- Every fixture rolls back: proven (Section 2 post-run check).
- All tests pass: proven (Section 1, Section 3).

Step 4 is satisfied. Proceeding to Step 5 (replay the exact live report without persistence)
remains gated behind this step's own review — it also touches the local Nautobot environment.
