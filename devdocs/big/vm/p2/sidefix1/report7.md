# Phase 2 Sidefix1 Step 7 Report: Resume Phase 2 Step 9 (Live Dry-Run Preview)

Status: dry-run preview executed; gate not met. Stopped before requesting apply approval, per
`problem_fixplan.md` Section 8 ("A deployed preview with unexpected output stops before apply").
No live Nautobot write occurred (Job-owned rollback confirmed by refetch); no Proxmox host was
mutated.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 7 ("Resume Phase 2 Step 9"),
items 1-6 only (the dry-run-preview-and-review portion; the user approved proceeding only that far
for this session). Raw evidence lives in `.local/vm-p2/20260725-step7/` (mode `0700`/`0600`,
gitignored).

## 1. Fresh Step 8 report reconfirmed (fixplan Step 7.1)

The Step 8 fresh report (`report2.8.md`, collected 2026-07-24T15:09) was over a day old, so a new
collection was taken instead of reusing it: `ansible-playbook -i inventories/generated/
hosts_intent.yml playbooks/nautobot/run_nodeutils_collect.yml --limit aghub` (`ok=33 changed=3
unreachable=0 failed=0`), then fetched via `ssh eiji@aghub.local cat /var/lib/nodeutils/
inventory.json` (no `sudo` needed — the non-root collector path already owns the file, per
`.local/localenv_memo.md`).

The fresh report (`collected_at: 2026-07-24T16:42:33Z`) confirmed the plan's required positive
case: `schema_version: nodeutils.inventory.v2`, nested `facts.proxmox.schema_version:
nodeutils.proxmox.v1`, `cluster: {name: aghub-proxmox, name_source: standalone_node_fallback,
identity_value: aghub, node_count: 1}`, and `agdnsmasq` present with `vmid: 108, node: aghub,
proxmox_status: running`, one joined interface (`net0`, MAC `bc:24:11:23:dc:b7`, bridge `vmbr0`,
IP `192.168.0.2/24`).

## 2. Sanitized before-image (fixplan Step 7.2)

Confirmed via the live API before running anything:

| Object | Before state |
|---|---|
| `aghub` Device | exists, `id fcebe565-6aeb-40b1-ba51-4bde1e1065bc`, `last_updated 2026-07-24T16:29:24.283108Z` |
| Cluster | 0 rows |
| VirtualMachine | 0 rows |
| VMInterface | 0 rows |
| IPAddress | 5 rows (`192.168.0.2/32`, `.10/32`, `.100/32`, `.110/32`, `.120/32` — none attached to any VMInterface) |

This matches `problem_fixplan.md` Section 2's required starting state (existing observer Device,
no matching Proxmox Cluster/VM/VMInterface relations) exactly.

## 3. Deployed Job run with `dry_run=true` (fixplan Step 7.3)

Ran the real, deployed `Ingest Nodeutils Inventory` Job (id `e009d25c-a57f-40d5-adaf-5bde29c9e23d`,
confirmed `installed: true, enabled: true`, `dry_run` variable help text now reads "without
committing target changes to Nautobot" — the sidefix1 Step 1 wording, confirming the Step 6 deploy
is live) via `POST /api/extras/jobs/<id>/run/` with the fresh report wrapped in the
`report_batch` schema and `policy_file: seed/nodeutils_ingest.yaml`. Job result
`5f843b42-cd8c-4ea1-b0ac-f57a061f70f9` completed `SUCCESS`.

## 4. Result: gate not met — two new real-ORM defects found (fixplan Step 7.4)

The core sidefix1 fix works: the summary's `proxmox` section is present and non-empty (unlike the
pre-sidefix1 defect evidence already captured in `.local/vm-p2/20260725-step9/`, which has no
`proxmox` key at all). But the section reports `observation_state: "partial"` with:

```json
"guest_errors": [
  {"code": "guest_upsert_failed", "scope_id": "qemu:102", "scope_kind": "guest", "section": "identity"},
  {"code": "guest_upsert_failed", "scope_id": "lxc:108", "scope_kind": "guest", "section": "identity"},
  {"code": "foreign_ip_relation", "scope_id": "net0", "scope_kind": "interface", "section": "ip"}
]
```

`lxc:108` is `agdnsmasq` — the fixplan's own named positive case, required by Step 7 item 4 to
positively confirm `net0`/`192.168.0.2/24` evidence. It fails instead.

Root-caused both `guest_upsert_failed` entries by reproducing the run in a rolled-back real-ORM
repro (copied worktree to `/tmp/nauto_review` in the Nautobot container per the
`report2.7.md`/`report4.md` scratch-module technique, neutralized `jobs/__init__.py` so no Job
registration changed, instrumented the swallowed exception to print its traceback, ran the real Job
class inside a manual savepoint that was rolled back). Findings and the full symptom detail are
recorded in [`../sidefix2/problem.md`](../sidefix2/problem.md), per the user's direction to record
this as a new, separate problem document rather than extend sidefix1 or patch inline:

- `qemu:102` (`aghaos`) fails because it carries an IPv6 address with no matching Prefix seeded in
  Nautobot's `Global` Namespace, and `sync_interface_ips()` has no graceful conflict path for that
  case (unlike `foreign_ip_relation`) — the `ValidationError` propagates and fails the whole guest.
- `lxc:108` (`agdnsmasq`) fails because `find_ip()` matches by `(host, mask_length)` while
  Nautobot's own uniqueness constraint is `(Namespace, host)` regardless of mask length; an
  unrelated, pre-existing `192.168.0.2/32` row (`dns_name: agdnsmasq.home.arpa`) is missed by the
  `/24` lookup, so `create_ip()` tries to insert a second row for the same host and Nautobot's
  `full_clean()` rejects it.
- The unrelated `foreign_ip_relation` conflict (`lxc:101`/`lxc:107` both configured with
  `192.168.0.30/24`) is real Proxmox data, handled correctly — not a defect.
- The user separately confirmed this is unrelated to `devdocs/big/vm/p1/plan.md` Step 8's manual
  SSH/initial-access contract, which governs a different, not-yet-reached phase (Phase 5 guest
  creation), not this phase's read/ingest path.

## 5. Refetch and equality proof (fixplan Step 7.5)

Two independent confirmations that no Nautobot state changed:

- Live API refetch after the Job run: Cluster/VirtualMachine/VMInterface still `count: 0`;
  IPAddress still `count: 5` at the same 5 addresses; `aghub` Device unchanged.
- The `/tmp/nauto_review` repro additionally wrapped the identical call in its own manual
  `transaction.savepoint()`/`savepoint_rollback()` as defense-in-depth beyond the Job's own
  internal rollback, and reproduced byte-identical `guest_errors`/`object_counts` — confirming the
  failure is deterministic, not a live-environment race.

## 6. Review and stop (fixplan Step 7.6)

Per Section 8 ("A deployed preview with unexpected output stops before apply"), this step does not
proceed to requesting the separate persistent-apply approval. `problem_fixplan.md`'s own
`sidefix1` Definition of Done is unaffected (all its items concern the transaction-rollback
mechanism sidefix1 built, which is proven working here); the newly found defects are recorded in
`sidefix2/problem.md` for separate triage, per explicit user direction (document only, no fix plan
or code change authorized yet).

## What this step does not cover

- Steps 7.7-7.10 (separate apply approval, persistent apply, `nctl actual --json`, identical
  repeat) — blocked behind `sidefix2` resolution.
- Any fix to `find_ip`/`create_ip`/`sync_interface_ips`/the `vm.created`/`vm.skipped` double-count
  noted in `sidefix2/problem.md` Section 5 — no code change is authorized by this report.

## Gate

Not met. `problem_fixplan.md` Step 7's own gate ("an omitted Proxmox section, empty first action
set, rollback leak, preview/apply stable-target or count mismatch, or non-empty identical repeat
fails the step") is triggered by the `agdnsmasq`/`aghaos` guest failures. Phase 2 Step 9 remains
blocked; `sidefix2/problem.md` is the new open blocker.
