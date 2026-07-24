# Phase 2 Step 9 Blocker (sidefix2): IP Matching/Creation Fails for Real Guest Data

Status: open, blocking Step 9. Found while resuming `problem_fixplan.md` (sidefix1) Step 7 — the
first live `dry_run=true` preview of the deployed, sidefix1-fixed `Ingest Nodeutils Inventory` Job
against a fresh `aghub` report. The sidefix1 fix itself works: the Proxmox section is no longer
omitted from the preview. Two new, previously undiscovered defects appeared instead, both inside
real Nautobot ORM validation that the existing fake-ORM tests never modeled. No live write
occurred; the run was a transaction-rolled-back preview (Job-owned `dry_run=true`, confirmed
before/after equal) and a separate rolled-back real-ORM repro under `/tmp/nauto_review` in the
Nautobot container.

Evidence lives under `.local/vm-p2/20260725-step7/` (mode `0700`/`0600`, gitignored): the fresh
`aghub` report, before-image of Nautobot target rows, the job run payload, job log, and the full
`nodeutils-ingest-summary.json`.

## 1. Symptom

Running the deployed Job with `dry_run=true` against a fresh, real `nodeutils.proxmox.v1` report
from `aghub` (9 guests: 3 qemu, 6 lxc) produced `observation_state: "partial"` with three
`guest_errors`:

```json
"guest_errors": [
  {"code": "guest_upsert_failed", "scope_id": "qemu:102", "scope_kind": "guest", "section": "identity"},
  {"code": "guest_upsert_failed", "scope_id": "lxc:108", "scope_kind": "guest", "section": "identity"},
  {"code": "foreign_ip_relation", "scope_id": "net0", "scope_kind": "interface", "section": "ip"}
]
```

`lxc:108` is `agdnsmasq` — the exact positive case `problem_fixplan.md` Step 7 names as required to
positively succeed ("`agdnsmasq` LXC VMID 108 and its `net0`/`192.168.0.2/24` evidence"). Its guest
upsert instead fails.

The third error (`foreign_ip_relation` for `net0`) is not a defect: `lxc:101` (agansible) and
`lxc:107` (agkeadhcp) both really are configured in Proxmox with the identical static IP
`192.168.0.30/24` on `net0`. `sync_interface_ips()` in
[`nauto/jobs/proxmox_interfaces.py`](../../../nauto/jobs/proxmox_interfaces.py) correctly detects
and reports this as a conflict rather than crashing. This is included here only for completeness;
it is real-world Proxmox configuration data, not a code defect.

## 2. Root cause 1: `qemu:102` (`aghaos`) — no-parent-prefix IPv6 address is not treated as a conflict

Reproduced traceback (rolled-back real ORM run):

```
File "jobs/proxmox_upsert.py", line 548, in ingest_proxmox_platform
  iface_result = proxmox_interfaces.sync_guest_interfaces(...)
File "jobs/proxmox_interfaces.py", line 420, in sync_guest_interfaces
  ip_outcome = sync_interface_ips(...)
File "jobs/proxmox_interfaces.py", line 320, in sync_interface_ips
  ip_obj = create_ip(candidate.address, candidate.prefix)
File "jobs/ingest_nodeutils_inventory.py", line 385, in create_ip
  validated_save(ip)
File "jobs/ingest_nodeutils_inventory.py", line 60, in validated_save
  obj.validated_save()
django.core.exceptions.ValidationError: {'namespace': ['No suitable parent Prefix for
2400:2410:1f84:800:da09:7be7:e0bd:58cd exists in Namespace Global']}
```

`aghaos` reports an IPv6 address for which no matching Prefix is seeded in Nautobot's `Global`
Namespace. `sync_interface_ips()` in
[`nauto/jobs/proxmox_interfaces.py`](../../../nauto/jobs/proxmox_interfaces.py) has an explicit,
graceful path for one kind of `create_ip` failure (`ip_related_elsewhere` →
`foreign_ip_relation` conflict, no exception), but no equivalent graceful path for "the target
Namespace has no parent Prefix for this address." `create_ip()`'s `validated_save()` raises a
Django `ValidationError` instead, which propagates out of `sync_interface_ips()` uncaught, is
caught only by the *guest-level* `except Exception` in `ingest_proxmox_platform()`
([`nauto/jobs/proxmox_upsert.py`](../../../nauto/jobs/proxmox_upsert.py) line ~578), and fails the
entire guest (its per-guest savepoint rolls back, including the Cluster/VM fields that were about
to be recorded), not just the one IP.

## 3. Root cause 2: `lxc:108` (`agdnsmasq`) — `find_ip` matches by `(host, mask_length)`, but Nautobot's uniqueness constraint is `(Namespace, host)` only

Reproduced traceback (rolled-back real ORM run), same call path as above, different guest:

```
django.core.exceptions.ValidationError: {'__all__': ['IP address with this Parent and Host already exists.']}
```

`find_ip()` in
[`nauto/jobs/ingest_nodeutils_inventory.py`](../../../nauto/jobs/ingest_nodeutils_inventory.py)
(line ~379) is:

```python
def find_ip(address: str, prefix: int) -> Any | None:
    return IPAddress.objects.filter(host=address, mask_length=prefix).first()
```

It requires an exact `(host, mask_length)` match. The live Nautobot instance already has an
unrelated, pre-existing `192.168.0.2/32` IPAddress row (`dns_name: agdnsmasq.home.arpa`, not
attached to any VMInterface — apparently created by an earlier, unrelated DNS-facing seed/ingest,
confirmed by its `created`/`last_updated` timestamps predating this Phase 2 work). The real
`agdnsmasq` report carries `192.168.0.2/24` (mask length 24, not 32). `find_ip(host="192.168.0.2",
prefix=24)` does not match the existing `/32` row, so `create_ip()` attempts to create a *second*
IPAddress for host `192.168.0.2` — which Nautobot's own model-level uniqueness constraint
(`(Parent Namespace, Host)`, independent of mask length) rejects.

This is a matching-key mismatch between nauto's own lookup (`host` + `mask_length`) and the
uniqueness rule of the system it is upserting into (`host` alone, within a Namespace). Any host
address whose only existing Nautobot record has a different mask length than the freshly observed
one will hit this, not only `agdnsmasq`.

## 4. Why sidefix1's tests did not catch either defect

Both failures are real Nautobot ORM `full_clean()`/`validated_save()` rejections. `sidefix1`
Section 6.2's fake-ORM tests do not model Nautobot's per-Namespace host-uniqueness constraint or
Prefix-existence validation for IPv6, so a `create_ip` call that would fail in the real ORM
succeeds silently in the fake store. `sidefix1` Section 6.3's Round A (`report4.md`) used one
synthetic LXC/IP fixture chosen specifically to avoid any pre-existing conflicting row, so it never
exercised either code path. This is the first run against a real, previously-populated Nautobot
instance and a real, multi-guest Proxmox report, and is exactly the scenario `problem_fixplan.md`
Section 6.3/6.4 anticipated real-ORM testing would need to cover before the live Step 9 resume — it
surfaced defects the plan's own fake-ORM suite structurally could not.

## 5. Current blocking status

- `problem_fixplan.md` (sidefix1) Steps 0-6 remain complete/deployed; its own Definition of Done
  items are unaffected by this document.
- `problem_fixplan.md` Step 7 (resume Phase 2 Step 9) cannot pass its gate as the code stands: the
  named `agdnsmasq`/vmid 108 positive case fails instead of positively confirming its `net0`/
  `192.168.0.2/24` evidence, and `aghaos`/qemu:102 fails on an unhandled IPv6 validation error.
  `object_counts` also currently over-counts (`vm.created=9` while 2 of those 9 guests' per-guest
  savepoints were rolled back on failure — the count is not adjusted when a guest fails after its
  VM upsert succeeds), which is a separate accuracy gap worth fixing alongside the two failures
  above if a fix plan is written for this document.
- No code change, fix plan, or live apply is authorized by this document. It only records the
  defects found while resuming sidefix1 Step 7.
