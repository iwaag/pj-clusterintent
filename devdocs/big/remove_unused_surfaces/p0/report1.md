# Phase 0 Step 1 — Record repository and VM Phase 3 state

Parent: [plan.md](plan.md), Step 1.

## Root/submodule revision tuple

| Repository | HEAD | Upstream | Dirty | Last commit date |
|---|---|---|---|---|
| superproject | `f4fc3394ae27495fe4cdcd5b39e1c91a7dc61d27` | — | untracked-only (see below) | Step 0 commit, this session |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `origin/main` | clean | 2026-07-24 20:21:34 +0900 |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | `origin/main` | clean | 2026-07-25 03:16:47 +0900 |
| `nctl` | `cb655c698312d864c311277e904c457213ae8d89` | `origin/main` | clean | 2026-07-25 12:20:59 +0900 |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | `origin/main` | clean | 2026-07-25 11:29:34 +0900 |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `origin/main` | clean | 2026-07-24 20:21:42 +0900 |

`git diff --submodule=short` at root is empty — every gitlink matches the checked-out submodule
HEAD above. This matches the plan's planning-time snapshot (§2.1) exactly for `nctl` and
`nintent`; the superproject HEAD advanced by one commit (this initiative's own Step 0 report).

Root `git status --short` shows only pre-existing untracked user documentation, none owned by this
step's execution and none touched by it:

```text
?? devdocs/big/remove_unused_surfaces/p0/plan.md
?? devdocs/big/remove_unused_surfaces/roadmap.md
?? devdocs/vision/
```

These are the initiative's own roadmap/plan/vision documents, authored before this execution
began; they are not a Phase 1–3 implementation edit and are left as-is (dirty-state ownership:
pre-existing user documentation, not this step's write).

## VM Phase 3 handoff point

Read all six reports under `devdocs/big/vm/p3/`: `report3.0.md` through `report3.5.md`. The
highest completed step is **Step 5** (`report3.5.md`, status `complete` for local implementation;
the running nctl deployment is explicitly deferred to the coordinated Step 8 cutover). Step 5's
own text states "Proceeding to Step 6." No `report3.6.md` or later exists, so **VM Step 6 has not
begun** — no explicit or implicit pending/deferred proof beyond what `report3.5.md` itself already
names (Steps 6 through 12 remain future work).

## Migration `0015` state

`nintent/nautobot_intent_catalog/migrations/0015_compute_platform_instance_and_endpoint_mac.py`
exists locally and declares:

```python
dependencies = [
    ("extras", "0142_remove_scheduledjob_approval_required"),
    ("ipam", "0055_rename_..."),
    ("nautobot_intent_catalog", "0014_braindump_exchange_diary"),
]
```

i.e. it depends directly on `0014`, consistent with plan §4.7's requirement that the new removal
migration `0016` must depend directly on `0015` (not on `0009` or another intermediate).

## Overlap check

`git status --short` inside `nctl` and `nintent` is empty for both — no uncommitted edit in either
submodule overlaps a Phase 1–3 deletion/edit path. No stop-and-classify action was required.

## Gate

The exact root/submodule tuple is recorded above, and the real VM Phase 3 handoff point is Step 5
complete / Step 6 not started, matching the plan's own Step 5 report text without reinterpretation.
