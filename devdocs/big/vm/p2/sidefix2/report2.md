# Phase 2 Sidefix2 Step 2 Report: Repair IP Relation Convergence

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`plan.md`](plan.md) Step 2 ("Repair IP relation convergence"). Implemented
together with [Step 1](report1.md) because both change the same shared callback contract; this
report covers the `jobs/proxmox_interfaces.py` rewrite and the combined test run for both steps.

## 1. `IpLookupResult` and the rewritten `sync_interface_ips()` (plan Section 3.4)

`jobs/proxmox_interfaces.py` gained its own `IpLookupResult` dataclass (structurally identical to
the one in `ingest_nodeutils_inventory.py`; duck-typed rather than shared — see
[`report1.md`](report1.md) Section 2) and `sync_interface_ips()` was rewritten as one desired-set
operation instead of the old attach-new-then-detach-old loop:

1. **Group by host, reject same-generation ambiguity** — candidates are grouped by
   `candidate.address`; a host observed with more than one distinct prefix in one generation
   produces `ip_observed_prefix_ambiguous` for that host and is excluded from resolution entirely
   (never picked by order).
2. **Resolve before detach** — for each non-ambiguous, not-already-managed key: `resolve_host()`
   is called once; `"ambiguous"` → `ip_address_ambiguous`; `"found"` → check
   `ip_related_elsewhere()` first (`foreign_ip_relation` if true, relation never stolen), else
   reuse; `"not_found"` → `find_parent_prefix()` first (`ip_parent_prefix_missing` if `None`),
   only then `create_ip(address, prefix, parent_prefix)`.
3. **Track resolved IP identity, not just keys** — every successfully resolved key's `ip_id` is
   added to a `resolved_ip_ids` set alongside the exact observed-key `managed` entry.
4. **Detach only what's truly absent** — a prior managed entry is only detached if its key is
   absent from the new `managed` map *and* its `ip_id` is absent from `resolved_ip_ids`. A
   prefix-only evidence-key change (prior `/24`, new `/32`, same IP identity) now updates the
   managed key without ever detaching the still-desired relation — the exact hazard `plan.md`
   Section 3.4 names.
5. **Bounded fallback for unresolvable legacy references** — if a prior entry's `ip_id` doesn't
   resolve via `find_ip_by_id()`, a bounded Namespace+host fallback (`resolve_host()` on the old
   key's address) is tried; if that also fails, the entry is retained as-is and
   `managed_ip_reference_unresolved` is reported — never guessed, never silently dropped.

The same detach-by-ID resolution (with the same bounded fallback) was applied to the presence
(complete-disappearance) convergence loop in `sync_guest_interfaces()`, which previously called
the same removed `find_ip(*_split_key(key))`.

## 2. Signature changes

`sync_interface_ips()` and `sync_guest_interfaces()` now take `resolve_host`, `find_parent_prefix`,
`create_ip` (3-arg), and `find_ip_by_id` instead of the old 2-arg `find_ip`/`create_ip`.
`proxmox_upsert.ingest_proxmox_platform()`'s own signature and its one call into
`sync_guest_interfaces()` were updated to match and simply forward the four new callables
unchanged (no logic added in `proxmox_upsert.py` itself at this step — that is Step 3's scope).

## 3. Tests (plan Section 5.1 cases 1-12 minus the count-leak cases, which are Step 3's)

Updated `nauto/tests/test_proxmox_interface_ip_upsert.py`'s fake ORM (`make_env`) to the new
contract, and added three new cases proving the Step 2 gate directly:

- `test_prefix_only_evidence_change_does_not_detach_the_same_ip` — ingest `10.0.0.5/24`, then
  re-ingest the same host at `/32`; asserts zero new `IPAddress` created, the relation stays
  attached to the *same* object throughout, and the managed map's only key becomes `10.0.0.5/32`
  pointing at that object's `ip_id`.
- `test_same_host_multiple_prefixes_one_generation_is_ambiguous` — one generation reporting
  `10.0.0.5/24` and `10.0.0.5/32` simultaneously creates nothing and reports
  `ip_observed_prefix_ambiguous`.
- `test_missing_parent_prefix_is_bounded_conflict_not_exception` — `find_parent_prefix` returning
  `None` produces `ip_parent_prefix_missing`, no `IPAddress` row.

Also updated `nauto/tests/test_ip_namespace_host_identity.py` (added in Step 0) to call the new
contract; its two IP-matching regression tests (Section 6 of [`report1.md`](report1.md)) now pass,
and its count-leak test correctly still fails (Step 3's scope, not this one).

```
cd nauto
python3 -m unittest tests.test_proxmox_interface_ip_upsert -v
# Ran 34 tests, OK (31 pre-existing + 3 new Step 2 cases)
python3 -m unittest discover -s tests
# Ran 101 tests in 0.010s, FAILED (failures=1)
#   -- the one expected-red test_failure_after_vm_upsert_does_not_leave_a_created_count,
#      unchanged from Step 0/1, gated on Step 3
python3 -m py_compile jobs/*.py tests/*.py
# no output (success)
```

100 of 101 tests pass; the sole failure is the pre-existing, intentionally-red Step 0 count-leak
test that Step 3 resolves. No other test regressed relative to the Step 1/2 baseline.

## 4. Preserved behavior (plan Section 2.2 non-goals)

- `192.168.0.30`'s real duplicate-use conflict (`foreign_ip_relation`) path is untouched —
  `ip_related_elsewhere()` is still checked first, before any attach, exactly as before.
- Device-interface dual-layer relations are unaffected — `ip_related_elsewhere()`'s own logic
  (only `vm_interface`-typed assignments count as foreign) was not touched.
- `MAX_MANAGED_IPS_PER_INTERFACE` truncation logic is unchanged.
- No Prefix, Namespace, or IPAM prerequisite is created anywhere in this step; `create_ip()` only
  ever runs after `find_parent_prefix()` returns non-`None`.

## Gate

- Prefix-only evidence changes cannot remove the final relation: proven (Section 3, first new
  test).
- Complete disappearance still detaches only the ingestor-managed relation: proven — the
  pre-existing `test_authoritative_empty_detaches_managed` /
  `test_complete_disappearance_sets_absent_and_detaches` tests still pass unchanged against the
  rewritten detach-by-ID path.
- No live-state change: proven — Section 3's exact command output; no Nautobot write, `aghub`
  call, or Proxmox mutation occurred.

Step 2 is satisfied jointly with Step 1. Proceeding to Step 3 (transaction-truthful guest
summaries) remains gated behind both steps' review.
