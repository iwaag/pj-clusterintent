# Phase 2 Step 9 Blocker: `dry_run` Does Not Prevent Real IP Writes

Status: open, blocking Step 9. Found while attempting the Step 9 ingest dry-run against the live
local Nautobot instance and the fresh `aghub` report collected in Step 8. No live ingest write has
occurred; this document only records the defect and a proposed fix for review before any code
change is made.

## 1. Symptom

Running the `Ingest Nodeutils Inventory` Job with `dry_run=true` against the fresh `aghub` report
produced a summary containing only the Device-level diff (`description`,
`custom_fields.last_seen`, `custom_fields.service_inventory_updated_at`,
`custom_fields.inventory_raw_json`). The summary had no `proxmox` section at all, so no
Cluster/VM/VMInterface/IP action could be previewed before requesting apply approval, contradicting
plan.md Section 2's exit criterion ("First apply is preceded by a dry-run summary...") and Step 9's
explicit gate ("Run ingest `dry_run=true`. Assert exact expected Cluster/guest/interface/IP actions
and no unrelated target.").

## 2. Root cause 1 (shallow): `ingest_report` short-circuits before Proxmox is ever reached

In [`nauto/jobs/ingest_nodeutils_inventory.py`](../../../nauto/jobs/ingest_nodeutils_inventory.py),
`ingest_report()`:

```python
outcome = "created" if device is None else "updated" if changes else "unchanged"
result = {
    "source": source,
    "outcome": outcome,
    "device": getattr(device, "name", None) or identity.get("hostname") or identity.get("fqdn"),
    "changed_fields": changes,
    "report_hash": report_hash,
}
if self.dry_run:
    return result                      # <-- returns here

if device is None:
    device = self.create_device(payload)
    ...
elif changes:
    self.update_device(device, payload)
    ...
result["device"] = device.name

proxmox_facts = facts.get("proxmox")
if isinstance(proxmox_facts, dict):
    result["proxmox"] = self.ingest_proxmox(proxmox_facts, device, policy, source)
return result
```

When `self.dry_run` is true, the function returns immediately after computing the Device-level
diff, before ever reaching `facts.get("proxmox")`. `ingest_proxmox()` (and the underlying
`proxmox_upsert.ingest_proxmox_platform`, which is itself `dry_run`-aware — see Section 3) is
simply never invoked in dry-run mode. This alone would make the dry-run preview silently omit all
virtualization actions.

This part is a well-scoped, shallow fix: move the `proxmox_facts` handling above the `if
self.dry_run: return result` branch, passing the existing (possibly `None`, for a not-yet-created
Device) `device` reference, and only skip the Device `create_device`/`update_device` calls under
`dry_run`.

## 3. Root cause 2 (deep, the actual blocker): `sync_interface_ips` ignores `dry_run` entirely

While tracing whether a naive fix of Root Cause 1 would be safe to re-run against the live
instance, inspection of the write paths reached by `ingest_proxmox_platform` found that
[`nauto/jobs/proxmox_upsert.py`](../../../nauto/jobs/proxmox_upsert.py) *does* correctly gate all
of its own `save_fn(...)` calls behind `if not dry_run:` (`upsert_with_freshness` for
Cluster/VM, and both `save_fn(iface)` sites in
[`proxmox_interfaces.py`](../../../nauto/jobs/proxmox_interfaces.py) `sync_guest_interfaces`).

However, `sync_guest_interfaces` calls `sync_interface_ips(...)` at two call sites (new-interface
path and existing-interface path) **without passing `dry_run` at all**:

```python
ip_outcome = sync_interface_ips(
    interface=iface, candidates=candidate.ip_candidates, complete=config_complete,
    observed_at_str=observed_at_str, find_ip=find_ip, create_ip=create_ip,
    ip_related_elsewhere=ip_related_elsewhere, attach_ip=attach_ip, detach_ip=detach_ip,
)
```

And `sync_interface_ips()` itself (`proxmox_interfaces.py:278`) has no `dry_run` parameter in its
signature at all. Its body unconditionally calls the injected `find_ip` / `create_ip` /
`attach_ip` / `detach_ip` closures whenever the config-derived candidate set is `complete`:

```python
ip_obj = find_ip(candidate.address, candidate.prefix)
if ip_obj is not None and ip_related_elsewhere(ip_obj, interface):
    outcome.conflicts.append({"key": key, "reason": "foreign_ip_relation"})
    continue
if ip_obj is None:
    ip_obj = create_ip(candidate.address, candidate.prefix)   # unconditional real write
    outcome.created += 1
else:
    outcome.attached_existing += 1
attach_ip(interface, ip_obj)                                   # unconditional real write
...
for key, entry in prior_managed.items():
    if key not in new_keys:
        ip_obj = find_ip(*_split_key(key))
        if ip_obj is not None:
            detach_ip(interface, ip_obj)                        # unconditional real write
        outcome.detached += 1
```

The real closures passed in from `ingest_nodeutils_inventory.py`'s `ingest_proxmox()` are not
dry-run-aware either:

```python
def create_ip(address: str, prefix: int) -> Any:
    status = self.lookup_status("Active")
    ip = IPAddress(address=f"{address}/{prefix}", status=status)
    validated_save(ip)          # always saves, regardless of self.dry_run
    return ip
```

**Consequence**: if only the shallow Root Cause 1 fix were applied and the ingest Job were re-run
with `dry_run=true`, the Job would still create real `IPAddress` rows and real
VMInterface-IPAddress relations in the live Nautobot database — a genuine write occurring inside
what is supposed to be a safe, side-effect-free preview. This directly violates plan.md Section
3.3 ("No approval in this phase authorizes a Proxmox mutation" — and more broadly the entire
dry-run-then-approve contract that governs every live-write step in this plan) and Section 5.5's
convergence rules, which assume `dry_run` fully gates all attach/detach/create behavior the same
way it gates the Cluster/VM/VMInterface `save_fn` calls.

The presence check `if not complete: return IpSyncOutcome(managed=prior_managed)` at the top of
`sync_interface_ips` (partial-input retention, Section 5.5 rule 3) is unrelated to this bug and is
correct; the bug is specific to the `complete=True` branch's unconditional IP mutation closures.

## 4. Why this was not caught earlier

- Step 5's unit tests exercise `ingest_proxmox_platform` directly against a fake in-memory ORM.
  The fake `find_ip`/`create_ip`/`attach_ip`/`detach_ip` closures used in those tests do not touch
  a real database, so even if they were called under a nominal `dry_run=True` test case, the tests
  could not detect "this closure should not have been called at all" — they only assert on
  `counts`/`managed` output shape, not on call-count/no-write invariants.
- Step 7's environment-backed round trip (`report2.7.md`) exercised the real ORM only with
  `dry_run=false`, wrapped in a manually rolled-back `transaction.atomic()` savepoint. It never
  exercised `dry_run=true` against the real ORM, so this specific gap — `dry_run=true` still
  writing IP rows for real — was never observed live until Step 9 attempted the first genuine
  dry-run/apply/approve sequence against the persistent local Nautobot database.

## 5. Proposed fix (not yet applied — for review)

1. Add a `dry_run: bool` parameter to `sync_interface_ips()` in `proxmox_interfaces.py`.
2. Guard all three real-write call sites inside it:
   - `create_ip(...)` — still compute what *would* be created for count/evidence purposes, but
     only call the real closure when `not dry_run`. Since `create_ip`'s return value (the object,
     specifically its `pk`) is used to populate `outcome.managed[key]["ip_id"]`, a dry-run branch
     needs a placeholder (e.g. `None` or a synthetic marker) so the previewed managed-evidence
     shape stays representative without fabricating a fake persisted ID.
   - `attach_ip(...)` — skip under `dry_run`; counts (`created`/`attached_existing`) should still
     reflect what would happen.
   - `detach_ip(...)` — skip under `dry_run`; `outcome.detached` count should still reflect what
     would happen.
3. Thread `dry_run` through both `sync_guest_interfaces()` call sites of `sync_interface_ips(...)`
   (`dry_run=dry_run`, matching the parameter `sync_guest_interfaces` already receives and already
   uses to gate its own two `save_fn(iface)` calls).
4. Apply the shallow Root Cause 1 fix in `ingest_report()`: move the `proxmox_facts = facts.get
   ("proxmox")` / `ingest_proxmox(...)` call above the `if self.dry_run: return result` branch, so
   dry-run mode actually reaches and previews the Proxmox path (passing the existing, possibly
   `None`, `device` — matching how a real create would have `observer_device_id=None` in preview
   mode too, an already-handled case in `ingest_proxmox`).
5. Add regression tests (fake-ORM, following the Step 5 pattern) asserting that under
   `dry_run=True`:
   - `create_ip`, `attach_ip`, and `detach_ip` closures are never called (mock call-count
     assertions, not just output-shape assertions);
   - `counts["ip"]` still reports the correct `created`/`updated`/`skipped` numbers a real apply
     would produce;
   - a subsequent real `dry_run=False` apply against the same input produces the same counts and
     actually creates the rows.
6. Re-run Step 9's dry-run against the live instance only after this fix lands, is tested, and is
   committed in `nauto`.

## 6. Current state

- No live write has occurred as a result of this investigation. The Step 9 before-image (0
  Clusters, 0 VMs, 0 VMInterfaces, 5 pre-existing unrelated IPAddresses) remains accurate; nothing
  has changed in the live Nautobot database since Step 8.
- The one `dry_run=true` Job run performed (job result `f9b132ee-ecd3-4c5a-ba73-f6432276b5e5`) did
  **not** reach the Proxmox/IP code path at all, because it was blocked by Root Cause 1 before ever
  reaching Root Cause 2 — so that specific run did not create any IP rows. The risk described in
  Section 3 is about what would happen on the *next* dry-run attempt if only Root Cause 1 were
  fixed in isolation.
- Step 9 (first live ingest, refetch, repeat-ingest proof) is blocked until this fix is reviewed,
  implemented, tested, and committed.
