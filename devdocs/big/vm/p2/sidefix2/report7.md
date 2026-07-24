# Phase 2 Sidefix2 Step 7 Report: Resume sidefix1 Step 7 / Phase 2 Step 9 (Live Dry-Run Preview)

Status: dry-run preview executed against the deployed, fixed Job; gate met. Stopped before
requesting apply approval, per `plan.md` Section 7 ("A deployed preview with unexpected output
stops before persistent apply" — here the preview *matched* expectations, but the plan still
requires separate approval before any persistent apply regardless). No live Nautobot write
occurred (Job-owned rollback confirmed by refetch); no Proxmox host was mutated.

This report covers [`plan.md`](plan.md) Step 7 items 1-8 only (the dry-run-preview-and-review
portion). Raw evidence lives in `.local/vm-p2/sidefix2-step7/` (mode `0700`/`0600`, gitignored).

## 1. Freshness (plan Step 7.1)

The fresh `aghub` report already captured at `.local/vm-p2/20260725-step7/`
(`collected_at: 2026-07-24T16:42:33Z`) was about one hour old at the time of this run (system
clock ~2026-07-24T17:48Z) — well inside the Job's `max_report_age_hours=72` default and the same
report Step 5 already replayed locally. No new collection was needed.

## 2. Sanitized before-image (plan Step 7.2)

Confirmed via the live API before running anything:

| Object | Before state |
|---|---|
| `aghub` Device | exists, `id fcebe565-6aeb-40b1-ba51-4bde1e1065bc`, `last_updated 2026-07-24T16:29:24.283108Z` |
| Cluster (`aghub-proxmox`) | 0 rows |
| VirtualMachine | 0 rows |
| VMInterface | 0 rows |
| `192.168.0.2` IPAddress | 1 row (`579213a3-491c-454e-9f32-f6c2d4b64dbd`, `last_updated
  2026-07-23T15:18:07.975924Z`) |

Matches the required starting state exactly (existing observer Device, no matching Proxmox
Cluster/VM/VMInterface relations, the one pre-existing `192.168.0.2` row untouched).

## 3. Deployed Job run with `dry_run=true` (plan Step 7.3)

Ran the real, deployed `Ingest Nodeutils Inventory` Job (`id
e009d25c-a57f-40d5-adaf-5bde29c9e23d`, confirmed `installed: true, enabled: true` at `nauto`
`c62e707` per [`report6.md`](report6.md)) via `POST /api/extras/jobs/<id>/run/` with the same
`report_batch` payload Step 5 used locally. Job result `1d6e5614-e175-4bb9-b580-f588272a8707`
completed `SUCCESS`.

## 4. Result: gate met (plan Step 7.4-7.6)

```json
"proxmox": {
  "cluster_name": "aghub-proxmox",
  "identity_source": "standalone_node_fallback",
  "scope_key": "standalone-device:fcebe565-6aeb-40b1-ba51-4bde1e1065bc",
  "cluster_id": null,
  "observation_state": "complete",
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
}
```

- **All 9 guest scopes accounted for**: `sum(object_counts["vm"].values()) == 9`, matching the
  real report's 3 qemu + 6 lxc guests; `changed_fields` lists `vm:lxc:101`, `vm:lxc:103`,
  `vm:lxc:104`, `vm:lxc:106`, `vm:lxc:107`, `vm:lxc:108`, `vm:qemu:100`, `vm:qemu:102`,
  `vm:qemu:105` — all nine.
- **`lxc:108` (`agdnsmasq`) and `net0` succeed**: no `guest_upsert_failed` anywhere in
  `guest_errors`; `vm.created == 9` with `vm.skipped == 0` proves `lxc:108`'s VM committed
  alongside every other guest.
- **The existing `192.168.0.2/32` row is reused, not duplicated**: `ip.updated == 1` (exactly one
  `resolve_host()` "found" reuse across the whole report) and the post-run refetch (Section 5)
  confirms the row's `pk`/`last_updated` are unchanged.
- **`qemu:102` (`aghaos`) retains its VM/eligible interface and reports `ip_parent_prefix_missing`,
  not `guest_upsert_failed`**: confirmed — `ip_parent_prefix_missing` is the only new-conflict code
  besides the known real `foreign_ip_relation` duplicate, and `vm.created == 9` (not 8 +
  `vm.skipped`) proves `qemu:102`'s VM committed.
- **The real `192.168.0.30` duplicate-use conflict remains truthfully reported**:
  `foreign_ip_relation` is present in `guest_errors`, unchanged from sidefix1's original finding —
  real Proxmox configuration data (`problem.md` Section 1), correctly surfaced, not suppressed.
- **Errors are bounded**: both entries are the fixed four-field shape with no message string,
  payload, or traceback.

This is the identical result Step 5's local rolled-back replay already produced against the
reviewed-but-not-yet-deployed code — the deployed Job now behaves identically to what was reviewed
and tested.

## 5. Refetch equals the before image (plan Step 7.7)

| Object | Before | After |
|---|---|---|
| `aghub` Device `last_updated` | `2026-07-24T16:29:24.283108Z` | `2026-07-24T16:29:24.283108Z` (unchanged — the Job-owned transaction rolled back the Device update too) |
| Cluster count | 0 | 0 |
| VirtualMachine count | 0 | 0 |
| VMInterface count | 0 | 0 |
| `192.168.0.2` IPAddress count / `last_updated` | 1 / `2026-07-23T15:18:07.975924Z` | 1 / `2026-07-23T15:18:07.975924Z` (unchanged — no duplicate, no write) |

Byte-for-byte equal on every checked field. The preview left the live database exactly as it was.

## 6. Review and stop (plan Step 7.8)

The sanitized preview (Sections 4-5) is reviewed and satisfies every positive assertion the plan's
Step 5/Step 7 gates require: the named `agdnsmasq` positive case, the isolated `aghaos` conflict,
the truthful real `192.168.0.30` conflict, and an unchanged before/after image. Per `plan.md`
Section 6 Step 7 item 8 and Section 7, this step stops here — persistent apply (items 9-13) needs
a separate, explicit approval, requested in a follow-up turn of this conversation.

## What this step does not cover

- No persistent apply, no refetch-after-apply, no `nctl actual --json` run, and no identical-repeat
  proof — plan Step 7 items 9-13, gated on separate approval.
- No Proxmox or `aghub` host mutation; no SSH/Ansible actuation.

## Gate (items 1-8 only)

- The exact guest set, counts, errors, stable provider identities, and managed relations match
  expectations: proven (Section 4).
- `lxc:108/net0`, reuse of the existing host row, and truthful `aghaos` isolation are positively
  confirmed: proven (Section 4).
- Refetch equals the before image: proven (Section 5).
- The sanitized preview is reviewed and this step stops for the required separate apply approval:
  this report.
