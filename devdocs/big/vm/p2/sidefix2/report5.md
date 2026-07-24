# Phase 2 Sidefix2 Step 5 Report: Replay the Exact Live Report Without Persistence

Status: implemented and environment-backed. Not deployed to the tracked `nauto` Git Repository and
no live `aghub`/Proxmox action was taken. No persisted Nautobot state changed — proven directly by
this step's own before/after checks. The user confirmed running real-ORM writes (rollback-wrapped)
against the local Nautobot container before Step 4 proceeded; this step continues under the same
confirmation (same risk class: transient write, then rollback, no persistence).

This report covers [`plan.md`](plan.md) Step 5 ("Replay the exact live report without
persistence") / Section 5.3.

## 1. Method

Reused the exact fresh `aghub` report already captured at `.local/vm-p2/20260725-step7/` during
sidefix1's original (blocked) Step 7 attempt — `run_payload_dryrun.json`, the real
`{"reports": [{"source": "aghub", "text": "<the full nodeutils.inventory.v2 YAML>"}]}` payload,
unchanged. Copied the reviewed `nauto` worktree (head of Step 4) into the running
`nautobot-nautobot-1` container at `/tmp/nauto_review` with the same neutralized `jobs/__init__.py`
used in Step 4, then instantiated the real `IngestNodeutilsInventory` Job class directly (no Job
database record touched) and called `job.run(report_batch=..., dry_run=True, ...)` exactly as
sidefix1 `report4.md`'s Round A did, with `create_file` monkeypatched to capture the summary in
memory. The whole call ran inside an outer `transaction.savepoint()` with a
`finally: transaction.savepoint_rollback(sid); transaction.set_rollback(True)` as defense-in-depth
beyond `run()`'s own internal `transaction.set_rollback(True)`.

Full script and output preserved at `.local/vm-p2/sidefix2-step4/step5_replay_script.py` /
`step5_replay_output.txt` (mode `0700`/`0600`, gitignored).

## 2. Before/after equality (the step's central gate)

A full snapshot (the real `aghub` Device's custom field data and `last_updated`, the
`aghub-proxmox` Cluster count, total VM/VMInterface counts, and the exact `192.168.0.2` and
`192.168.0.30` `IPAddress` rows) was taken before `job.run()` and again after it returned. Both
snapshots are byte-for-byte equal (`before == after`, proven by direct dict comparison in the
script) — the fix's preview leaves the real, previously-populated Nautobot instance completely
unchanged, exactly as the original sidefix1 `dry_run=true` contract requires.

## 3. Assertions from the produced summary (plan Section 5.3)

```
Proxmox object_counts: {
  "cluster": {"created": 1, "skipped": 0, "unchanged": 0, "updated": 0},
  "vm":      {"created": 9, "skipped": 0, "unchanged": 0, "updated": 0},
  "vminterface": {"created": 7, "skipped": 0, "unchanged": 0, "updated": 0},
  "ip":      {"created": 5, "skipped": 2, "unchanged": 0, "updated": 1}
}
Proxmox guest_errors: [
  {"code": "ip_parent_prefix_missing", "scope_id": "net0", "scope_kind": "interface", "section": "ip"},
  {"code": "foreign_ip_relation", "scope_id": "net0", "scope_kind": "interface", "section": "ip"}
]
```

- **All 9 guest scopes accounted for exactly once**: `sum(object_counts["vm"].values()) == 9 ==
  len(qemu_vms) + len(lxc_containers)` from the real report's own `facts.proxmox`.
- **`lxc:108` (`agdnsmasq`) and `net0` succeed**: no `guest_upsert_failed` anywhere in
  `guest_errors` (the list contains only the two known bounded local-conflict codes above,
  correctly scoped to the `net0` interface, not to any guest).
- **The existing `192.168.0.2/32` row is reused and remains unchanged**: confirmed via a real ORM
  query for `host="192.168.0.2"` immediately after `run()` returns — same `pk`
  (`579213a3-491c-454e-9f32-f6c2d4b64dbd`), same native `mask_length=32`, same
  `dns_name="agdnsmasq.home.arpa"` as the pre-run snapshot (this row is a real, previously
  persisted row, unaffected by this preview's own internal rollback since it was only read and
  reused, never written).
- **`ip.updated == 1`**: exactly one candidate across all 9 real guests resolved to a pre-existing
  `IPAddress` (`sync_interface_ips()` counts a `resolve_host()` "found" result as
  `attached_existing`, mapped to `counts["ip"]["updated"]`) — the only value consistent with
  `agdnsmasq`'s `192.168.0.2` being reused rather than a second row being attempted. (The dict
  entry pointing `192.168.0.2/24 -> that row's ID` inside the new `VMInterface`'s
  `proxmox_managed_ip_evidence` could not be inspected directly: `dry_run=True`'s own
  `transaction.set_rollback(True)` fires inside `run()`'s *own* `with transaction.atomic():`
  block, so every newly-created row — including the new `VMInterface` — is already gone by the
  time `run()` returns control to this script. This matches sidefix1 `report4.md`'s own evidence
  bar, which likewise relied on `object_counts` rather than mid-transaction row inspection for its
  preview round.)
- **`qemu:102` (`aghaos`) retains its VM/eligible interface and reports `ip_parent_prefix_missing`,
  not `guest_upsert_failed`**: confirmed — the only two `guest_errors` entries are the bounded
  `net0`-scoped conflicts above, and `vm.created == 9` (not `8` + one `vm.skipped`) proves
  `qemu:102`'s VM row was among the 9 successfully-processed guests.
- **The real `192.168.0.30` duplicate use remains `foreign_ip_relation`**: confirmed — present in
  `guest_errors` exactly as before the fix (this is real-world Proxmox configuration data per
  `problem.md` Section 1, not a code defect, and the fix does not and must not suppress it).
- **No rolled-back guest is counted as created/updated**: `sum(vm counts) == 9` with zero
  `vm.skipped` — no guest failed at all in this replay, so there is nothing to leak; Step 3's fix
  is exercised structurally (guest-local accumulators merge on success) but this particular replay
  has no guest whose savepoint actually rolled back.
- **Errors are bounded and contain no raw report or traceback**: both `guest_errors` entries are
  the fixed four-field shape (`scope_kind`, `scope_id`, `section`, `code`) with no message string,
  payload, or traceback.
- **Post-run target state equals the before image**: proven in Section 2.

## 4. Result

```
PASS: before == after (full refetch equality)
PASS: no guest_upsert_failed anywhere
PASS: lxc:108 (agdnsmasq) has no terminal guest error
PASS: qemu:102 (aghaos) has no terminal guest error
PASS: net0 foreign_ip_relation (real 192.168.0.30 duplicate) still reported
PASS: all 9 guest scopes accounted for exactly once in vm counts
PASS: 192.168.0.2/32 row existed before with native mask 32
PASS: in-transaction: same 192.168.0.2 ID reused (no duplicate)
PASS: in-transaction: native mask stayed /32
PASS: in-transaction: native dns_name unchanged
PASS: ip.updated == 1 (exactly one pre-existing IP reused, not duplicated)
=== 11/11 checks passed ===
OVERALL: PASS
```

A follow-up query in a fresh, separate `nautobot-server shell` invocation confirmed: `VM count: 0`,
`Cluster aghub-proxmox count: 0`, `192.168.0.2 rows: 1` (the one real pre-existing row, unchanged)
— the container's Nautobot database carries zero trace of this replay.

## 5. What this step does not cover

- No separate apply-then-rollback round (plan Section 5.3 asks only for the `dry_run=true`
  preview replay here; the real persistent apply, its own refetch, and the identical-repeat proof
  are Step 7's scope, gated on separate user approval).
- No deployment to the tracked `nauto` Git Repository, no push, and no touch of the real `aghub`
  Proxmox host.

## Gate

- `agdnsmasq` is the required positive IP relation: proven (Section 3).
- `aghaos` is isolated at the candidate level: proven (Section 3).
- The real foreign-IP conflict remains truthful: proven (Section 3).
- Counts match surviving guest savepoints: proven (Section 3 — all 9 guests surviving, `vm.created
  == 9`, `vm.skipped == 0`).
- The before image is unchanged: proven (Section 2, Section 4).

Step 5 is satisfied. Proceeding to Step 6 (review, commit, deploy) remains gated behind this
step's own review.
