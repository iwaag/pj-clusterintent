# Phase 2 Step 5 Report: Reliable VMInterface and IP Relations

Status: implemented, not deployed (local code + local unit tests only; no live Nautobot run).

This report covers [`plan.md`](plan.md) Step 5 ("Implement reliable VMInterface and IP
relations"), grounded in Section 5.4 (VMInterface/IPAddress ledger mapping) and Section 5.5
("Interface matching" and "Interface/IP convergence" rules).

## 1. What changed

`nauto`:

- `jobs/proxmox_interfaces.py` (new) — pure VMInterface/IPAddress candidate extraction,
  matching, and convergence logic. No Django import, following the `proxmox_ingest.py` /
  `proxmox_upsert.py` pattern.
- `jobs/proxmox_upsert.py` — `ingest_proxmox_platform()` gained optional interface-related
  parameters (`vminterface_manager`, `make_interface`, `find_ip`, `create_ip`,
  `ip_related_elsewhere`, `attach_ip`, `detach_ip`). When supplied, it calls
  `proxmox_interfaces.sync_guest_interfaces()` immediately after each guest's VM upsert succeeds,
  inside the same per-guest savepoint Step 4 established, so an interface-layer exception rolls
  back with the rest of that guest's writes.
- `jobs/ingest_nodeutils_inventory.py` — resolves `virtualization.VMInterface`, `ipam.IPAddress`,
  and the `ipam.IPAddressToInterface`/`IPAddressAssignment` through-model, and wires real
  `find_ip`/`create_ip`/`ip_related_elsewhere`/`attach_ip`/`detach_ip` closures into
  `ingest_proxmox_platform()`.
- `tests/test_proxmox_interface_ip_upsert.py` (new, 31 tests).

## 2. Design

### Interface candidate eligibility (Section 3.2 non-goal, Section 5.5 rule 1)

Only `guest["interfaces"]["joined_interfaces"]` entries are eligible for VMInterface
materialization:

- QEMU `joined_interfaces` are nodeutils' already-computed deterministic 1:1 config/agent MAC
  join; config-only and agent-only evidence never appears in this list, so it structurally cannot
  reach VMInterface creation.
- LXC `joined_interfaces` is the same list as `config_interfaces` (LXC has no guest-agent join).

`interface_candidates_for_guest()` additionally rejects (as bounded diagnostic evidence, never a
VMInterface): missing/invalid MAC, a config slot that appears more than once in one guest's own
joined list, and a MAC reused across two slots in the same guest. Every `unmatched` entry is
recorded as diagnostic evidence too. None of these paths create a VMInterface or IP relation.

### Matching (Section 5.5 "Interface matching" rules 2-4)

- `match_vm_interface()`: `(VirtualMachine, proxmox_config_slot)` via `name=config_slot`, not
  agent interface name.
- `mac_conflict_in_cluster()`: a MAC already used by another VMInterface whose VM is in the same
  Cluster is a conflict. Device-level guest-interface MAC reuse is explicitly exempt (Section 5.4:
  "the same MAC on the Device-level guest interface and compute-level VMInterface is legitimate
  dual-layer evidence") — the check is scoped to `VMInterface.filter(mac_address=...)` only.
- An existing interface whose stored MAC no longer matches the newly observed MAC for that slot
  is `interface_mac_changed` — an unsupported target-local conflict; the MAC is never rewritten
  and its relations are never touched (rule 4).

### IP candidate validation (Section 5.4)

`qemu_ip_candidates()`/`lxc_ip_candidates()` use `ipaddress.ip_interface()` and exclude loopback,
link-local, multicast, and unspecified addresses, plus malformed input. QEMU agent addresses
without an explicit `prefix` are excluded. LXC `ip=dhcp`/`auto`/`manual` tokens and any value
without an explicit `/prefix` are excluded. Only address+prefix pairs that survive this filter are
"exact reliable IP evidence."

### Convergence (Section 5.5 "Interface/IP convergence" rules 1-7)

`sync_interface_ips()` operates per already-matched, MAC-compatible interface against its stored
`proxmox_managed_ip_evidence = {"managed": {"<address>/<prefix>": {"ip_id", "evidence_observed_at"}}}`:

- **Not complete** (partial/truncated relevant section): the managed dict and its evidence time
  are returned unchanged — no attach/detach, and it is never presented as fresh (rules 3, 7).
- **Complete**: still-observed keys keep their existing IP relation and refresh evidence time;
  newly observed keys attach — find-or-create the IPAddress, unless it is already related to a
  *different* VMInterface (`ip_related_elsewhere`), in which case the candidate is recorded as a
  `foreign_ip_relation` conflict and left untouched (rule 6, never steals a foreign relation);
  previously-managed keys no longer observed detach — the relation only, never the IPAddress
  object itself (rule 2). An authoritative empty complete set therefore detaches everything
  previously managed (rule 3's other half).
- **Presence** (rule 5): once per guest, after all candidate interfaces are processed, any
  existing VMInterface for that VM+source (QEMU/LXC) whose slot is absent from this generation's
  *complete* candidate set is marked `proxmox_presence=absent`; its managed IPs detach; the row
  itself is retained. Partial enumeration never marks absence. "Complete" for this purpose is
  taken from the guest's own `observation.sections.agent_interfaces` (QEMU) or `.config` (LXC)
  section state, falling back to the guest's overall `observation.state` when the specific section
  is absent from the validated shape.

### Per-slot evidence time (deviation note)

`proxmox_observed_at` on each VMInterface, and the evidence time recorded in
`proxmox_managed_ip_evidence`, is taken from the guest's `agent_interfaces`/`config` section
`evidence_observed_at` when present, falling back to the platform-level `validation.observed_at`.
This is a pragmatic reading of "does not inherit the parent VM time" (Section 5.4): nodeutils'
`nodeutils.proxmox.v1` schema (Step 1) has no dedicated per-interface-slot timestamp distinct from
the section-level one, so the section time is the finest-grained evidence available. If a future
nodeutils revision adds a genuinely per-slot time, this is the single place to switch to it.

### Composition with Step 4

`sync_guest_interfaces()` is invoked from inside the existing `guest_atomic()` block in
`proxmox_upsert.ingest_proxmox_platform()`, immediately after that guest's VM upsert succeeds. Any
exception it raises therefore rolls back with the rest of that guest's writes under Step 4's
per-guest savepoint contract, and unmatched/diagnostic evidence is merged into the VM's
`proxmox_interface_evidence` custom field, keyed by slot (or `"unmatched"`).

## 3. Explicit non-goals held

- No storage-content ledger writer (unchanged — still open, no step has implemented this yet).
- No `DesiredComputePlatform`/`DesiredComputeInstance` or desired-side changes.
- No live Nautobot, live seed apply, or live ingest was run; no network call to `aghub` or any
  Proxmox host.
- `nodeutils`, `ansible_agdev`, `nctl`, and `devenv/` were not touched.
- No IPAddress object is ever deleted; no relation outside the recorded managed set is ever
  detached.

## 4. Tests

```
$ cd nauto && python3 -m unittest discover -s tests
Ran 89 tests in 0.007s
OK
```

89 = 58 pre-existing (Steps 0-4) + 31 new in `tests/test_proxmox_interface_ip_upsert.py`, covering:

- IP-candidate extraction: IPv4/IPv6 with prefix, missing prefix, loopback/link-local/
  multicast/unspecified, malformed address, LXC static CIDR, `dhcp` token, missing prefix/key;
- QEMU interfaces: unique-MAC join, config-only creates nothing, agent-only creates nothing,
  multi-NIC no-cross-pair, duplicate config/agent MAC excluded, invalid/missing MAC never
  materializes, partial agent results retain relations and old evidence time;
- LXC interfaces: static CIDR, DHCP token creates interface but no IP, missing MAC creates no
  interface, duplicate MAC in one guest excluded, multiple net slots each get their own interface;
- convergence: an unrelated Device-level relation with the same MAC is left alone, a foreign
  VMInterface's existing relation is untouched, complete IP change converges only the managed set,
  authoritative empty detaches everything managed, partial retention keeps old evidence time, a
  MAC change is flagged as a conflict and not auto-fixed, complete disappearance sets
  `presence=absent` and detaches managed IPs while keeping the row, later recovery re-attaches
  without creating a duplicate interface row;
- a cross-VM MAC conflict within the same Cluster is rejected at interface creation time.

As with Steps 3 and 4, all matching/diff/convergence logic was proven against a duck-typed fake
ORM double (fake managers, fake model objects with `.cf`, fake `save_fn`/`find_ip`/`create_ip`/
`attach_ip`/`detach_ip`), because no Django/Nautobot package or live test-database environment is
available in this sandbox. The real ORM wiring added to `ingest_nodeutils_inventory.py`
(`VMInterface.objects`, `IPAddress.objects`, the `IPAddressToInterface`/`IPAddressAssignment`
through-model lookup) was verified only by `py_compile`, consistent with `report2.0.md`'s Step 0
live introspection finding (a through-endpoint with mutually exclusive `interface`/`vm_interface`
fields) but not executed against a live environment — this remains open until Step 8/9's live
dry-run/apply.

## 5. What Step 5 does not yet cover

- The `nctl` typed actual reader does not yet read `proxmox_config_slot`,
  `proxmox_guest_interface_name`, `proxmox_bridge`, `proxmox_interface_source`,
  `proxmox_presence`, or `proxmox_managed_ip_evidence` — Step 6.
- Storage-content ledger writes remain unimplemented (open since Step 4; no step has scheduled
  this yet within Phase 2's remaining steps besides the read-only helper from Step 2).
- Live verification of the exact `IPAddress`/`VMInterface`/through-model field names and the
  dual Device/VMInterface relation capability against the actually deployed Nautobot version
  (Step 8's live prerequisite check is the first point this runs for real).
- Live execution of the ORM wiring end-to-end (Step 8/9).

## Gate

Unit tests prove the positive QEMU join and LXC config cases create the expected interface/IP
relation; complete IP change/empty/disappearance converges only managed relations; partial input
retains old-time evidence; and unmatched/ambiguous/foreign cases do not mutate unowned relations —
entirely without any live Nautobot dependency, per Step 5's stated gate.

Proceeding to Step 6 (nctl typed actual state and read-only diagnostic).
