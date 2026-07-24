# Phase 2 Step 10 Report: Final Audit, Documentation, and Phase Report

Status: **Phase 2 complete.**

This report covers [`plan.md`](plan.md) Step 10 ("Final audit, documentation, and phase report"),
closing out Phase 2 of [`devdocs/big/vm/roadmap.md`](../roadmap.md).

## 1. Final tests and `git diff --check` (plan Step 10.1)

```text
nodeutils:      38 passed
ansible_agdev:   8 passed
nauto:         110 passed
nctl:        1000 passed (1 pre-existing unrelated warning)
```

`git diff --check` is clean in every one of the six repositories (superproject, `nodeutils`,
`ansible_agdev`, `nauto`, `nctl`, `nintent`).

## 2. Final revisions and working-tree status (plan Step 10.2)

| Repository | `HEAD` | vs. `origin/main` |
|---|---|---|
| superproject | `1983a1a42fa69ea78acdcf199261f4f330a1846b` | ahead 1 (this report's own commit plus the prior `report2.9.md` commit; not yet pushed) |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | matches |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | matches |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | matches |
| `nctl` | `fd9cb878a1cdab9a436e7d125d2e5697badc1fc4` | matches |
| `nintent` | `ad9d36397d23c269ad748e13acbccc532fa29f52` | unchanged, Phase 2 out of scope |

Every submodule pointer in the superproject already matches the corresponding repository's local
`HEAD`. All working trees are clean.

## 3. Proxmox guest state vs. Step 0 baseline (plan Step 10.3)

The final live guest set (9 guests, same VMIDs/kinds/names) is unchanged from the
`report2.0.md`/`report2.8.md` baseline: `infra(100,qemu)`, `aghaos(102,qemu)`, `agk3s(105,qemu)`,
`agansible(101,lxc)`, `agprome(103,lxc)`, `aggrafana(104,lxc)`, `agnomad(106,lxc)`,
`agkeadhcp(107,lxc)`, `agdnsmasq(108,lxc)`. Power-state values differ across collections (ordinary
observed churn, e.g. `infra` stopped, `agansible` running) but no guest was created, deleted,
resized, or moved by any Phase 2 action — confirmed directly in `report2.9.md` Section 9 and by
every fresh collection performed across Steps 8-9.

## 4. Desired rows, generated inventories, and unrelated rows (plan Step 10.4)

- Phase 2 created no `DesiredComputePlatform`/`DesiredComputeInstance` row (explicit non-goal,
  Section 3.2) and did not touch `DesiredNode.realized_vm`.
- `ansible_agdev/inventories/generated/hosts_intent.yml` and `production.yml` file modification
  times (`2026-07-22`/`2026-07-24T00:18`) predate every Step 8/9 live action (`2026-07-24T15:xx`
  onward); Phase 2's own ingest/collection actions never write these files.
- No SSH `known_hosts` entry exists in the repository to compare (none was ever added by this
  phase; the Ansible collection path in Steps 8-9 used the pre-existing `ansible_key` trust only).
- The only Nautobot rows touched across Phase 2 are: the `aghub` Device (native fields + bounded
  custom fields, already in scope since Phase 1), the seeded ClusterType/Role/Status/CustomField
  prerequisites (Step 8), and the Cluster/VirtualMachine/VMInterface/IPAddress rows this phase
  explicitly owns. No unrelated Nautobot object was created, updated, or deleted.

## 5. Secret/credential scan of tracked reports (plan Step 10.5)

`grep` across every tracked `devdocs/big/vm/p2/**/*.md` for token/password/private-key/raw-SSH-key
patterns found no leaked credential, raw provider response body, private key, or SSH key blob —
only the expected prose describing token *storage location* (`.local/secrets`,
`Authorization: Token` header usage) and plan-language mentions of "token" as a forbidden category.
All raw execution evidence (job bodies, full API responses, digests) remains under
`.local/vm-p2/**`, which is `git`-ignored (`.gitignore:2`) and mode `0700`/`0600`.

## 6. Raw-evidence retention (plan Step 10.6)

Owner: the operator (`iwaag`), on the local development machine. Location:
`.local/vm-p2/{20260724-step0,20260724-step8,20260725-step7,20260725-step9,
20260725-step9-storagefix,sidefix1-step4,sidefix1-step5,sidefix2-step4,sidefix2-step7}/`
(≈1.2 MiB total, private, not committed). Retention date: kept indefinitely alongside the local
checkout unless the operator later prunes it; nothing in this evidence is required for Phase 2's
own completion proof beyond what is already excerpted into the committed `report2.*.md` files.

## 7. Exit-criteria table (plan Step 10.7 / Section 2)

| # | Exit criterion | Status | Evidence |
|---|---|---|---|
| 1 | Nested schema exactly `nodeutils.proxmox.v1`; unknown keys fail closed; malformed items isolated | met | `report2.1.md` |
| 2 | Cluster identity records provenance; fallback rename reuses stable scope or stops | met | `report2.1.md`, `report2.4.md`; live: `standalone_node_fallback` proven in `report2.8.md`/`report2.9.md` |
| 3 | Every semantic collection has explicit limit/deterministic sort; truncation recorded, cannot be hidden | met | `report2.1.md` |
| 4 | Bounded error codes/omitted-error count/section state survive into Nautobot + nctl | met | `report2.3.md`, `report2.4.md`, `report2.6.md` |
| 5 | QEMU config/agent interfaces separate; joined interface only for unique normalized-MAC match | met | `report2.1.md`, `report2.5.md` |
| 6 | Duplicate/missing/invalid/config-only/agent-only/unmatched MAC cases retain bounded diagnostic evidence | met | `report2.1.md`, `report2.5.md` |
| 7 | LXC `rootfs` parsed independently; aggregate `disk_gb` never used as root-disk evidence | met | `report2.1.md`, `report2.4.md`; live: `agdnsmasq` rootfs `8.0GB` (`report2.9.md`) |
| 8 | `/nodes/{node}/storage/{storage}/content` is the only new privileged path, positive/negative tested | met | `report2.2.md` |
| 9 | Storage-content collection retains only allowlisted identity/display fields | met | `report2.1.md`, `report2.2.md` |
| 10 | Normal nauto Job is sole Cluster/VM/VMInterface/IP writer; no self-registration writer restored | met | `report2.4.md` |
| 11 | Stable matching via Cluster type/name then `(cluster, guest_type, vmid)` | met | `report2.4.md` |
| 12 | Reliable joined/explicit interface creates stable VMInterface; unmatched creates none | met | `report2.5.md` |
| 13 | Foreign IP/MAC conflicts fail locally, never stolen/reassigned/guessed; complete observation detaches only ingestor-owned relations | met | `report2.5.md`; sidefix2 `report2.md`/`report8.md` (real foreign-relation case proven live) |
| 14 | IP change/empty-IP/MAC change/interface disappearance have explicit complete-vs-partial convergence | met | `report2.5.md`, sidefix2 `report2.md` |
| 15 | Freshness/completeness persisted per platform/guest; older/equal-conflicting cannot overwrite | met | `report2.4.md` |
| 16 | Timestamps timezone-aware UTC; beyond-skew rejected before writes | met | `report2.3.md` |
| 17 | Partial observation never marks absent guest changed; Phase 2 never deletes an absent guest even on complete observation | met | `report2.4.md`; live: `report2.9.md` Section 9 |
| 18 | One malformed guest rolls back only that guest; platform marked `partial` | met | `report2.4.md`, `report2.7.md` |
| 19 | Newer partial observations merge by stable keys; retained evidence keeps original time; no parent-time inheritance | met | `report2.4.md`, `report2.7.md`; extended to storage-content in `report2.9.md` Section 0 |
| 20 | First apply preceded by dry-run summary + before image; apply separately approved; followed by exact refetch | met | `report2.9.md` Sections 2-6 |
| 21 | Identical repeat ingest is a no-op, including unchanged `last_updated` | met | `report2.9.md` Section 8; sidefix2 `report8.md` |
| 22 | nctl reads only dedicated native + allowlisted custom fields; never `inventory_raw_json`/unrestricted payloads | met | `report2.6.md` |
| 23 | Read-only nctl diagnostic renders `aghub -> aghub-proxmox -> agdnsmasq` with VMID/kind/state/time/completeness | met | `report2.6.md`; live: `report2.9.md` Section 7 |
| 24 | Exact operator-recorded Phase 5 candidate `volid` present in a fresh, complete storage-content section | **met** | `report2.8.md` (selection + two confirmations), `report2.9.md` Sections 0 and 6 (closed the ledger-persistence gap found while preparing this evidence) |
| 25 | Automated tests cover Section 8 scenario matrix; environment-backed collect/ingest/refetch/repeat runs against local Nautobot | met | `report2.7.md`, `report2.9.md`; full suite counts in Section 1 above |
| 26 | Final audit proves no Proxmox guest state, desired object, generated inventory, SSH trust entry, or unrelated actual row changed | met | Sections 3-4 above |

Every applicable Section 2 exit-criterion bullet is `met`; none is `unmet` or `not applicable`.

## 8. Final phase status (plan Step 10.8)

**Phase 2 is `complete`.**

This includes the exact-candidate-`volid` gate (criterion 24), which plan.md Section 10 singles
out as the one condition that can force `partially complete` even with everything else proven —
that gate is met, so the earlier caution does not apply. One implementation gap was found and
closed during this final step: `nauto/jobs/proxmox_upsert.py` never persisted
`facts.proxmox.storage_content` to the Cluster ledger (deferred at Step 4, never picked up through
Step 7's own gate); it is now fixed, tested (37 new/extended `nauto` tests), deployed, and proven
live in `report2.9.md`.

One explicitly accepted, non-blocking residual scope item remains open: `nctl`'s own typed
storage-content reader (planned additively in Section 5.6) was never implemented. It is not
required by any Section 2 exit criterion — the candidate `volid`'s persistence is proven directly
against the Nautobot Cluster custom field — but a future phase or maintenance pass extending
`nctl actual` to surface storage-content evidence would complete that originally-planned surface.

## Phase Handoff

Per plan.md Section 10, Phase 2 hands Phase 3/4 stable actual Cluster/guest IDs with provenance,
exact Cluster/kind/VMID matching fields, typed power/capacity/rootfs evidence, typed interface
provenance with safely convergent ingestor-owned IP relations, current complete evidence for the
one exact operator-recorded template `volid`, explicit platform/guest completeness, bounded
structured observation errors, a read-only actual graph, and a proven non-destructive
repeat-ingest path. It hands off no implicit desired link; Phase 3 remains responsible for
operator-confirmed `DesiredComputePlatform`/`DesiredComputeInstance`/endpoint MAC intent.
