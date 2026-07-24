# Phase 2 Sidefix2 Step 1 Report: Implement Explicit Namespace/Host Resolution

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`plan.md`](plan.md) Step 1 ("Implement explicit Namespace/host resolution").
Implemented together with Step 2 (see [`report2.md`](report2.md)) because both steps change the
same shared callback contract between `jobs/ingest_nodeutils_inventory.py` and
`jobs/proxmox_interfaces.py`; this report covers only the Step 1 portion of that combined change.

## 1. `Global` Namespace resolution (plan Section 3.1)

`jobs/ingest_nodeutils_inventory.py` resolves the `Global` Namespace exactly once per Proxmox
ingest call, before any IP handling:

```python
global_namespace_matches = list(Namespace.objects.filter(name="Global"))
if len(global_namespace_matches) != 1:
    ... return a platform-level "namespace_ambiguous" guest_errors entry, skip all writes ...
global_namespace = global_namespace_matches[0]
```

Zero or multiple matches produces a bounded `namespace_ambiguous` platform-level error (mirrors
the existing missing-`ClusterType`/missing-role early-return shape already in this Job) rather
than falling back to any other Namespace, per the plan's non-goal.

## 2. Namespace-and-host IP lookup without `.first()` (plan Section 3.2)

Replaced `find_ip(address, prefix)` with `resolve_host(host) -> IpLookupResult`:

```python
def resolve_host(host: str) -> IpLookupResult:
    matches = list(IPAddress.objects.filter(host=host, parent__namespace=global_namespace))
    if not matches:
        return IpLookupResult(status="not_found")
    if len(matches) > 1:
        return IpLookupResult(status="ambiguous")
    return IpLookupResult(status="found", ip=matches[0])
```

`IpLookupResult` (`status` in `{"found", "not_found", "ambiguous"}`) is defined locally in
`ingest_nodeutils_inventory.py` as a small typed dataclass rather than imported from
`proxmox_interfaces.py`, since that module is loaded either as a real package-relative import or
via ad hoc `importlib` file loading in tests (`proxmox_upsert._load_proxmox_interfaces()`) — duck
typing avoids a class-identity mismatch between the two loading paths. `proxmox_interfaces.py`
defines its own structurally-identical `IpLookupResult` for the same reason (see
[`report2.md`](report2.md) Section 1).

## 3. Closest-parent lookup and explicit-parent create (plan Section 3.3)

```python
def find_parent_prefix(host: str) -> Any | None:
    try:
        return Prefix.objects.filter(namespace=global_namespace).get_closest_parent(host, include_self=True)
    except Prefix.DoesNotExist:
        return None

def create_ip(address: str, prefix: int, parent_prefix: Any) -> Any:
    status = self.lookup_status("Active")
    ip = IPAddress(address=f"{address}/{prefix}", status=status, parent=parent_prefix)
    validated_save(ip)
    return ip
```

`find_parent_prefix` calls the exact same manager method Nautobot's own
`IPAddress._get_closest_parent()` uses internally (`Prefix.objects.filter(namespace=...)
.get_closest_parent(host, include_self=True)`, confirmed by reading
`nautobot/ipam/models.py:1479-1487` in the live container — see [`report0.md`](report0.md)). No
generic exception-string parsing was added; `validated_save()` remains the final ORM validation
boundary, and any *other* `ValidationError` still propagates unchanged to the per-guest savepoint.

## 4. Stable-ID lookup for detachment (plan Section 3.2/3.4 wiring)

```python
def find_ip_by_id(ip_id: str | None) -> Any | None:
    if not ip_id:
        return None
    try:
        return IPAddress.objects.filter(pk=ip_id).first()
    except (ValueError, TypeError):
        return None
```

## 5. Removed the `.first()`/exact-mask assumption

The old `find_ip(address, prefix) = IPAddress.objects.filter(host=address,
mask_length=prefix).first()` is gone; every call site in `ingest_nodeutils_inventory.py` and
`jobs/proxmox_upsert.py`'s `ingest_proxmox_platform()` signature was updated to the new
`resolve_host`/`find_parent_prefix`/`create_ip(address, prefix, parent_prefix)`/`find_ip_by_id`
contract (`grep -rn "find_ip\b"` across `jobs/` now returns nothing).

## 6. Tests (plan Section 5.1 cases 1, 2, 6, 7 — Step 1 portion)

The two Step 0 regression tests in `nauto/tests/test_ip_namespace_host_identity.py` that model
these two defects now pass (updated to call the new contract instead of the old one, per
[`report0.md`](report0.md)'s intent — see [`report2.md`](report2.md) Section 3 for the full test
run):

- `test_existing_32_row_is_reused_for_observed_24_without_raising` — the existing `/32` row is
  reused for an observed `/24`; no second `IPAddress` is created; native `dns_name` untouched.
- `test_missing_parent_prefix_does_not_fail_the_whole_guest` — a missing parent Prefix no longer
  raises; the `qemu:102` VM is still committed.

## Gate

- `/32` existing plus `/24` observed resolves to one unchanged IP object: proven (Section 6,
  first test).
- A missing parent returns a typed result before create: proven (Section 6, second test;
  `find_parent_prefix()` is always called before `create_ip()` in the Step 2 convergence loop —
  see [`report2.md`](report2.md)).
- No live-state change: proven — this step is Python source changes plus local
  `python3 -m unittest`/`py_compile` only (see [`report2.md`](report2.md) Section 3 for exact
  output); no Nautobot write, `aghub` call, or Proxmox mutation occurred.

Step 1 is satisfied jointly with Step 2. Proceeding to Step 3 (transaction-truthful guest
summaries) remains gated behind both steps' review.
