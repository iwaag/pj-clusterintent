# Phase 2 Sidefix2 Step 7 (items 9-13) Report: Persistent Apply, Refetch, Repeat

Status: applied. The reviewed/tested `nauto` fix now has a real, persistent, correct
Cluster/VirtualMachine/VMInterface/IPAddress graph committed to the live local Nautobot instance
from the exact fresh `aghub` report. User explicitly approved proceeding to persistent apply after
reviewing [`report7.md`](report7.md)'s preview.

This report covers [`plan.md`](plan.md) Step 7 items 9-13. Raw evidence continues in
`.local/vm-p2/sidefix2-step7/` (mode `0700`/`0600`, gitignored) alongside report7.md's preview
evidence.

## 1. Persistent apply (plan Step 7 item 9)

Ran the same deployed `Ingest Nodeutils Inventory` Job with `dry_run=false` against the identical
fresh `aghub` report used in the preview. Job result `560b6b6f-f4aa-44ea-a586-daa7b92ccd1e`
completed `SUCCESS` with **identical counts to the preview**:

```json
"object_counts": {
  "cluster": {"created": 1, "updated": 0, "unchanged": 0, "skipped": 0},
  "vm":      {"created": 9, "updated": 0, "unchanged": 0, "skipped": 0},
  "vminterface": {"created": 7, "updated": 0, "unchanged": 0, "skipped": 0},
  "ip":      {"created": 5, "updated": 1, "unchanged": 0, "skipped": 2}
},
"guest_errors": [
  {"scope_kind": "interface", "scope_id": "net0", "section": "ip", "code": "ip_parent_prefix_missing"},
  {"scope_kind": "interface", "scope_id": "net0", "section": "ip", "code": "foreign_ip_relation"}
]
```

This is preview/apply parity, proven directly (same counts, same errors — the only new field is a
real, non-`null` `cluster_id` now that `sanitize_created_ids` no longer applies).

## 2. Refetch the full graph (plan Step 7 item 10)

Real REST API refetch confirmed:

| Object | Refetched state |
|---|---|
| Cluster (`aghub-proxmox`) | 1 row, `id 0ef3f747-b905-42f7-82d8-7e8572e9b63d` (matches the summary's `cluster_id`) |
| VirtualMachine | 9 rows: `agansible, agdnsmasq, aggrafana, aghaos, agk3s, agkeadhcp, agnomad, agprome, infra` |
| VMInterface | 7 rows |
| `192.168.0.2` IPAddress | **still exactly 1 row**, same `id 579213a3-491c-454e-9f32-f6c2d4b64dbd`, same `last_updated 2026-07-23T15:18:07.975924Z` as before this Job ever ran — the native row is byte-for-byte untouched |
| `192.168.0.30` IPAddress | 1 row (the real Proxmox duplicate-IP situation; one guest attached, the other correctly `foreign_ip_relation`) |
| `agdnsmasq`/`net0` `proxmox_managed_ip_evidence` | `{"managed": {"192.168.0.2/24": {"ip_id": "579213a3-491c-454e-9f32-f6c2d4b64dbd", ...}}}` — the exact observed `/24` key, pointing at the reused `/32` row's real ID |

This is the concrete proof this whole sidefix2 blocker fix exists for: a real Nautobot instance's
pre-existing, differently-masked `IPAddress` row was correctly identified, reused, and left
natively unchanged, with the fresh observation recorded as managed evidence rather than either
duplicating the row or silently discarding the fresh `/24` observation.

## 3. `nctl actual --json` (plan Step 7 item 10, continued)

First attempt failed with an unrelated pre-existing `nctl` bug: `ACTUAL_QUERY` queried
`status { value }`, but this Nautobot version's GraphQL `StatusType` only exposes `name`/`vlans`
(confirmed by a direct GraphQL query returning the same `Cannot query field 'value'` error before
any nauto-side change). Traced and fixed as a one-line, isolated correction (`nctl` commit
`fd9cb87`, user confirmed before fixing): `status { value }` → `status { name }` in
`ACTUAL_QUERY`, and the corresponding `status["value"]` → `status["name"]` read in
`_build_virtual_machine()`, with the one affected test fixture (`_AGDNSMASQ_VM_ROW`) updated from
`{"value": "active"}` to `{"name": "Active"}` to match the real schema's casing (confirmed live:
`{"virtual_machines": [{"status": {"name": "Active"}}, ...]}`). Full `nctl` suite: **1000 passed**.

`nctl actual --json` then succeeded (`"ok": true`), reporting all 9 guests under the
`aghub-proxmox` cluster with correct per-interface `managed_ip_count`/`unrelated_ip_ids`
(`agdnsmasq`/`net0`: `managed_ip_count=1`; `agkeadhcp`/`net0`: `managed_ip_count=0`, the guest that
lost the real `192.168.0.30` conflict — consistent with `foreign_ip_relation`).

## 4. Identical repeat (plan Step 7 item 12)

Re-ran the identical Job call (`dry_run=false`, same `report_batch`). Job result
`3426b6ae-0f3b-46c8-8df8-daccd35caf99` completed `SUCCESS`:

```json
"object_counts": {
  "cluster": {"created": 0, "updated": 0, "unchanged": 1, "skipped": 0},
  "vm":      {"created": 0, "updated": 0, "unchanged": 9, "skipped": 0},
  "vminterface": {"created": 0, "updated": 0, "unchanged": 7, "skipped": 0},
  "ip":      {"created": 0, "updated": 0, "unchanged": 0, "skipped": 2}
},
"changed_fields": {}
```

Zero creates/updates across every kind, `changed_fields` for the Proxmox virtualization graph is
empty, and the same two bounded conflicts remain reported (correctly not re-created or
re-detached). A direct refetch confirmed:

- The Cluster's `id` and `last_updated` are unchanged.
- The full 9-VM `id` set is identical, and every VM's `last_updated` is unchanged.
- The reused `192.168.0.2` row's `id` and `last_updated` are unchanged.

No relation churn, no repeated attach/detach — a true no-op.

## 5. Continuing the original process (plan Step 7 item 13)

Phase 2 Step 9's persistent apply is now complete and verified. The original
`../report2.9.md`/Step 10 process (documented separately in `plan.md`'s parent phase document,
[`../plan.md`](../plan.md)) is the next step outside this blocker-fix document's own scope —
recorded here as a pointer, not executed by this report.

## What this step does not cover

- No further Proxmox/`aghub` host mutation and no SSH/Ansible actuation — only the Nautobot Job's
  own persistence ran.
- The `../report2.9.md`/Step 10 continuation itself (Section 5) is out of scope for this report.

## Gate

- The approved apply committed the preview-equivalent graph and conflicts: proven (Section 1).
- Refetch matches managed evidence and native relations: proven (Section 2).
- `nctl actual --json` succeeds and reports the correct graph: proven (Section 3).
- Identical repeat is a true no-op (zero creates/updates, no relation churn, unchanged IDs and
  timestamps): proven (Section 4).

This blocker fix (`plan.md`'s full Definition of Done, Section 8) is now complete: every item is
proven across `report0.md`-`report8.md`. Phase 2 itself remains gated on the separate
`report2.9.md`/Step 10 process (Section 5).
