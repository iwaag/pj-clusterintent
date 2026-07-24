# Phase 2 Step 4 Report: Idempotent Cluster and Guest Upsert

Status: implemented, not deployed (local code + local unit tests only; no live Nautobot run).

This report covers [`plan.md`](plan.md) Step 4 ("Implement idempotent Cluster and guest
upsert"), grounded in Section 5.4 (ledger mapping), Section 5.5 (matching/transaction/idempotence
rules), and Section 5.3 (completeness and freshness).

## 1. What changed

`nauto`:

- `jobs/proxmox_upsert.py` (new) — pure Cluster/VirtualMachine matching, freshness/diff, and
  per-guest savepoint orchestration. No Django import, so it is unit-testable without a live
  environment, mirroring the Step 3 `proxmox_ingest.py` pattern. Exposes
  `ingest_proxmox_platform()` as the single entry point; the real Job supplies real Nautobot
  managers/lookups/`save`/`transaction.atomic` and calls it unchanged, so tests exercise the same
  code path as production via a duck-typed fake-ORM double.
- `jobs/ingest_nodeutils_inventory.py` — after the existing Device upsert, a report's
  `facts.proxmox` subtree (if present) is validated with Step 3's `validate_proxmox_facts()` and,
  if valid, passed to `proxmox_upsert.ingest_proxmox_platform()` inside `Job.ingest_proxmox()`.
  Missing `Proxmox VE` `ClusterType` (unseeded prerequisite) or an invalid report produces zero
  virtualization writes and a `partial` result section, never an exception that aborts the batch.
- `jobs/nodeutils_ingest_summary.py` — unchanged in shape (the `proxmox` result section is built
  directly by `proxmox_upsert._section()` and threaded through `result["proxmox"]`, so no separate
  summary-builder duplication was added — a `build_proxmox_summary_section()` helper the
  implementing agent added was removed as dead code before commit; nothing referenced it).
- `tests/test_proxmox_cluster_vm_upsert.py` (new, 26 tests).

## 2. Design

### Cluster matching (Section 5.5 rules 1-7)

- Scope key: `cluster-name:<provider name>` for `proxmox_cluster_name`, or
  `standalone-device:<observer Device UUID>` for `standalone_node_fallback`
  (`derive_cluster_scope_key`).
- `match_cluster()` looks up candidates within `ClusterType=Proxmox VE`, matches by exact
  `proxmox_scope_key` first (zero/one/many → create/update/`duplicate_scope_key`), then checks
  same-name-but-disjoint-scope conflicts (rule 5) and, for fallback identity, an observer-Device
  change under what looks like the same name (rule 4, `fallback_scope_migration_required`). None
  of these paths auto-create a second same-named Cluster or silently rewrite scope identity.

### Guest matching (Section 5.5 Guest matching rules 1-4)

- `match_guest()` looks up `(proxmox_guest_type, proxmox_vmid)` globally first to detect
  cross-Cluster conflicts, then narrows to the target Cluster: zero → create (after a same-name
  conflict check), one → update, more than one → `duplicate_vmid_kind`. A same-name-only row
  (different VMID) is a `same_name_conflict`, never an implicit match.

### Freshness and no-op diffing (Section 5.3, Section 5.5 "No save is called when the diff is empty")

- `upsert_with_freshness()` is a single shared routine used for both Cluster and VirtualMachine
  rows. Rules implemented: older incoming `observed_at` → `stale_evidence` (object untouched);
  equal timestamp + identical allowlisted values → `noop` (no save); equal timestamp + any
  differing value → `conflicting_same_generation` (rejected, object untouched); newer timestamp →
  diff-and-save only changed native/custom fields, or plain `create` for a new object.

### Capacity/status/role mapping (Section 5.4 VirtualMachine table)

- `map_status`: running→Active, stopped/paused→Offline, other→Unknown.
- `map_role`: qemu→`virtual-machine`, lxc→`lxc-container`.
- `guest_disk_gb()`: native `disk` is populated only from parsed LXC `rootfs.size_gb`; QEMU guests
  and LXC guests without parsed rootfs get no `disk` value, never the aggregate `disk_gb`.
- `vcpus`/`memory` (MiB) are copied only when the validated guest provides them.

**Caveat**: `VirtualMachine.memory`/`disk` field units were mapped per documented Nautobot
semantics (memory in MB, disk in GB), not verified through a live GraphQL/REST introspection or an
installed Nautobot package, because neither was available in this sandbox. Plan.md Section 4.4
calls for this to be a "live model/unit assertion" — Step 0's environment already had no live
Nautobot reachable for this kind of check, so this remains an open item. **This must be confirmed
against the actually deployed Nautobot version before Step 8/9 live apply**; if the live unit
differs, the mapping in `proxmox_upsert.py` (`native_fields["memory"]`, `native_fields["disk"]`)
is the sole place to fix.

### Transactions (Section 5.5 "Transaction boundaries")

- Invalid report or missing `Proxmox VE` prerequisite: `ingest_proxmox()` returns before touching
  any Cluster/VM object.
- Each guest runs inside `guest_atomic()` (real `transaction.atomic()` from the Job; `nullcontext`
  in pure unit tests). Any exception inside that block — including a raised
  `stale_evidence`/`conflicting_same_generation` outcome, which is converted to an exception to
  force rollback — rolls back only that guest's writes, appends a bounded guest error, and flips
  `platform_partial = True`. Other guests in the same report continue to be processed.
- Cluster `proxmox_observation_state`/`proxmox_observation_detail` are finalized (and saved, if
  changed) only after the full guest loop completes, so the platform-level completeness reflects
  every guest's outcome, not just the Cluster row's own diff.

**Scope limitation carried into Step 5**: "finalize Cluster completeness only after all local
outcomes are known" is guest-outcome-only in Step 4, because storage-content ingest is not wired
into any ledger writer yet (Step 2 built only the read-only helper path; no storage-content ORM
consumer exists before Step 5+). Step 5 (or later storage-content ledger work) must fold
storage-scope outcomes into the same finalization before Cluster completeness can be considered
fully accurate per Section 2 exit criteria.

### Summary extension (Section 5.5 tail, item 11)

- `result["proxmox"]` on each Job result row is the same bounded shape
  `proxmox_upsert._section()` returns: `identity_source`, `scope_key`, `cluster_name`,
  `cluster_id`, `observation_state`, `object_counts` (per-kind created/updated/unchanged/skipped,
  with `vminterface`/`ip` staying at zero until Step 5), `changed_fields`, and bounded
  `guest_errors`. `nodeutils_ingest_summary.build_ingest_summary()` itself is untouched — existing
  Device-only result rows remain valid since Pydantic/consumers ignore the additional optional
  `proxmox` key, satisfying the "no summary version bump needed" requirement without introducing a
  second, unused summary-section builder.

## 3. Explicit non-goals held (per plan.md Section 3.2 and Step 5 boundary)

- No VMInterface/IPAddress creation, matching, or `vminterface`/`ip` counts beyond zero — Step 5.
- No storage-content ORM writer — not yet in scope for any step through Step 4.
- No `DesiredComputePlatform`/`DesiredComputeInstance` or other desired-side changes.
- No live Nautobot, live seed apply, or live ingest was run. No network call to `aghub` or any
  Proxmox host was made.
- `nodeutils`, `ansible_agdev`, and `nctl` were not touched in this step.

## 4. Tests

```
$ cd nauto && python3 -m unittest discover -s tests
Ran 58 tests — OK
```

58 = 32 pre-existing (Steps 0-3) + 26 new in `tests/test_proxmox_cluster_vm_upsert.py`, covering:

- cluster provenance: provider-name scope key, standalone-fallback scope key, unknown
  `name_source` rejection, zero-candidate create (both provenance kinds), single-node
  null-provider-ID fallback, one-candidate update-changed-fields-only, identical-repeat no-op with
  no save, same-name-disjoint-scope conflict, duplicate-scope-key conflict;
- guest identity: QEMU+LXC both created, capacity unit mapping, status/role mapping,
  duplicate-name/different-VMID conflict (not an implicit match), duplicate-VMID/kind rollback,
  cross-Cluster conflict rollback;
- freshness: older-is-stale, equal-identical no-op, equal-conflicting rejection, newer-updates,
  partial-generation updates only the observed guest without touching an unobserved one;
- transaction/idempotence: invalid report → zero writes, one-bad-guest isolated while others
  commit, guest-savepoint exception rolls back only that guest, batch continues after one report
  fails, dry-run plans without writing.

All matching/diff logic above was exercised against a duck-typed fake ORM double (fake
manager/model objects implementing `.filter()`, `.cf`/`.custom_field_data`, and a fake `save_fn`),
the same pattern Step 3 used for the pure-parser tests, because no Django/Nautobot package or live
test-database environment is available in this sandbox. The real ORM wiring added to
`ingest_nodeutils_inventory.py` (`get_model`, `Cluster.objects`, `VirtualMachine.objects`,
`transaction.atomic`, `validated_save`) was verified only by `py_compile`, not executed against a
live or in-memory Django environment — this is the same limitation Step 3 recorded for its own ORM
touchpoints, and it carries the same requirement forward: Step 8/9's live/dry-run steps are the
first point this wiring runs for real.

## 5. What Step 4 does not yet cover

- VMInterface/IPAddress matching, creation, and convergence (Step 5).
- Storage-content ledger writes and folding storage-scope state into Cluster completeness
  finalization (Step 5 or later, per the scope-limitation note above).
- Live verification of `VirtualMachine.memory`/`disk` field units against the actually deployed
  Nautobot version (must happen no later than Step 8's live prerequisite check).
- Live execution of the new ORM wiring in `ingest_nodeutils_inventory.py` (Step 8/9).

## Gate

Pure/unit tests prove clustered/fallback matching, create, rename-safe update, stale/future
reject, equal-conflicting reject, per-guest rollback, multi-generation partial merge (guest-level),
and no `save()` for an identical object — entirely without any live Nautobot dependency, per
Step 4's stated gate. VMInterface/IP relation proof and live-environment execution remain for
Step 5 and Step 8/9 respectively.

Proceeding to Step 5 (reliable VMInterface and IP relations).
