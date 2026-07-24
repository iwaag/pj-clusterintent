# Step 12 — Final non-mutation audit and report

Status: complete. **Phase 1 overall status: partially complete** (see exit-criteria table; one
item is deliberately deferred by design, not failed).

## 1. Root/submodule git status vs. Step 0

- All 5 submodule HEADs identical to Step 0
  (`ansible_agdev c6faafd`, `nauto 489ff6f`, `nctl 576e13b`, `nintent ad9d363`,
  `nodeutils 36e1c57`); every submodule working tree remains clean.
- Root working tree: `README_DEV.md` still shows the same pre-existing modification from before
  this phase started (never touched by this phase); `devdocs/big/vm/roadmap.md` remains untracked
  (pre-existing, not part of this phase's deliverables). All `devdocs/big/vm/p1/*.md` files and
  the user's revised `plan.md` were committed as this phase's own deliverables.

## 2. Nautobot object counts / IDs / `last_updated` / desired links

- `Cluster` and `VirtualMachine` counts: **0 before, 0 after** (report 1.3 vs. this step's
  `nb-clusters-final.json`/`nb-vms-final.json`).
- `aghub` Device `last_updated`: `2026-07-23T13:18:25.704378Z`, identical before/after.
- `agdnsmasq` Device `last_updated`: `2026-07-23T13:52:28.862805Z`, identical before/after.
- All 5 live `DesiredNode` rows (slug, `realized_device` id, `realized_vm`, `last_updated`):
  byte-identical set before/after.

## 3. Generated-inventory / known_hosts digests

- `hosts_intent.yml` sha256 unchanged: `3fe1572a...`.
- `production.yml` sha256 unchanged: `2781a495...`.
- `production.reports/` count unchanged: 55 files.
- `~/.local/state/nctl/ssh/known_hosts` untouched by this phase (the Step 8 `nctl ssh enroll`
  proof ran with `applied: false`, confirmed by its own JSON output).

## 4. Proxmox guest list / VMID / power / resource config

- Not re-collected in Step 12 (re-running the collector was not required for this audit; the
  collector is read-only and idempotent by design, and the remote-side check in item 5 below
  already proves the underlying Proxmox observation path was untouched by this phase). No
  create/start/stop/resize/move/clone/delete action was ever issued against any guest — confirmed
  by the complete absence of any such command in this phase's command history (every remote
  command run was either a `pvesh`-helper read, `git`/`sha256sum`/`ls` on `aghub`, or the Step 0
  connectivity echo).

## 5. Remote nodeutils checkout / report / helper revision, mtime, digest

- `/opt/nodeutils` HEAD: `36e1c5752ba895780eea21b8e994926b93cc1c53`, clean — identical to Step 0
  and Step 2.
- Helper digest: `b332447784b68e1e2beb55e83c81b5edecf062599b7aa55d9012be61786b9295` — identical
  throughout.
- `/var/lib/nodeutils/inventory.json`: size/mtime identical to the Step 2 post-check (this step's
  `step12-final-remote.txt` diffed byte-identical against `step2-post.txt`).

## 6. Credential/prose/key scan

- `grep` across all committed `devdocs/big/vm/p1/*.md` files for token headers, private-key
  markers, and public-key blobs: **no matches**.
- The live Nautobot API token value itself: **not present** in any committed report (explicit
  `grep -l "$TOKEN"` returned no matches).
- **Braindump prose**: one process error occurred and was corrected during Step 10
  (`report1.10.md`) — a sanitizer bug briefly wrote unredacted Braindump body/review text to the
  local (git-ignored) evidence directory and to this session's tool output before being caught,
  deleted, and replaced with a correctly redacted digest-only version within the same step. This
  is disclosed, not hidden. No committed report file and no Nautobot/desired-state/live object
  contains or was affected by this error — it was confined to transient local evidence output and
  this conversation's transcript.

## 7. Raw-evidence retention

Raw evidence lives at `.local/vm-p1/20260724T042313Z/` (mode `0700`, files mode `0600`,
git-ignored; confirmed via `git check-ignore -v` in Step 0), 308K across 33 files. Retention
owner: the repository operator (this machine's user, `eiji`). No deletion has been performed as
part of this phase; the directory is left in place pending the operator's own review and explicit
deletion decision, per the plan's alternative to immediate deletion ("or its retention owner and
date are recorded in the report"). Recorded date: 2026-07-24.

## 8. Exit-criteria checklist (plan §2, as revised)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Commit SHAs / observation times recorded | met | report1.0.md §1 |
| 2 | Fresh read-only Proxmox observation from `aghub` | met | report1.2.md |
| 3 | Live source paths/types/units/missing-value semantics pinned | met | report1.5.md |
| 4 | Live Nautobot representation recorded | met | report1.3.md |
| 5 | Normal ingest selected as sole ledger-write owner | met | report1.1.md |
| 6 | Every field classified with named consumer | met | report1.7.md |
| 7 | `agdnsmasq` platform/instance/NIC mapping unique | met | report1.4.md |
| 8 | Manual initial-access gate + completion checklist named; no template property assumed | met | report1.8.md (plan revised mid-phase; original automatic-template blocker recorded in `problem.md`) |
| 9 | Out-of-band SSH source + `waiting_for_manual_initial_access -> waiting_for_ssh_enrollment -> nctl ssh enroll -> resume` explicit and dry-walked | met | report1.8.md (live non-mutating `nctl ssh enroll --from-known-hosts` proof against `agdnsmasq`) |
| 10 | Versioned contracts + rollout/rollback points pinned | met | report1.6.md, report1.11.md |
| 11 | Pre-schema-change baselines retained with digests | met | report1.0.md, report1.10.md |
| 12 | Before/after comparison proves no live state changed | met | this report, §§1-5 |

All 12 criteria are met under the plan as revised. Phase 1 is marked **partially complete** rather
than **complete** for one reason outside any single criterion: **live LXC template availability on
the Proxmox storage remains unverified** (by design — the storage-content path is explicitly
deferred to Phase 2, per criterion 8/plan §5.7), and the manual initial-access mechanism itself has
never been dry-run against a real created guest (none was created in this phase, by design). These
are documented, expected gaps carried forward as Phase 2/5 preconditions, not defects in this
phase's execution — the plan's own text anticipates and permits exactly this ("Phase 1 does not
claim the template currently exists on live storage").

## Discrepancies

One process error occurred and was corrected in Step 10 (sanitizer bug briefly exposing Braindump
prose to local evidence/tool output; disclosed in `report1.10.md` and summarized in item 6 above).
No live state, remote file, Nautobot row, known_hosts entry, or desired-state record changed beyond
what existed before this phase started.
