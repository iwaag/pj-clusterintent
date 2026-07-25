# Phase 4 Step 7 — Prepare final commits and deployment/rollback tuples

Parent: [plan.md](plan.md) Step 7.

Executed 2026-07-25.

## 1. Review against the Step 1 manifest

All 7 `edit-current` files from [report1.md](report1.md) §5 were edited exactly as scoped (Steps 2–3,
recorded in [report2.md](report2.md)/[report3.md](report3.md)); no other file changed. `nctl`
required zero documentation edits from this phase (already `verified-current` at Step 1) — VM Phase
3 Step 7's own fixup commit (`ebe8a1d`, correcting a stale `nctl.render.dnsmasq.v2` CLI help string)
is unrelated to this phase's manifest and was reviewed independently in [report7.md](report7.md) §0.

## 2. nintent commit — already pushed

This phase's nintent documentation commit (`c343c5a56047b0df9ad901dd4459863ef1954053`, on top of the
already-pushed Phase 3 implementation `0914ca4`) was committed in Step 2. `git fetch origin && git
rev-parse origin/main` now resolves to that exact commit — it has been pushed (by the user, between
this phase's Step 2 and Step 6). No push request is needed; plan §9 Step 7.3/7.4's "ask the user to
push" / "verify read-only that it's reachable" are both satisfied.

## 3. nctl — no Phase 4 documentation commit needed; VM Step 6/7 commit already pushed

Plan §9 Step 7.5 ("commit any nctl documentation changes together with or after the final VM Step 6
code") — this phase found zero nctl documentation gaps (Step 1), so there is no Phase-4-specific nctl
commit to make. The final nctl revision is VM Phase 3 Step 7's own commit
`ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9`, confirmed pushed (`origin/main` matches) in
[report7.md](report7.md) §0.

## 4. Root — submodule pointers and active-roadmap/README changes

Root's tracked submodule pointers already read `nctl@ebe8a1d5` and `nintent@c343c5a5` (`git
submodule status`, this step) — both set by prior commits in this session's/VM's history
(`7831b8f` for `nctl`, this phase's own Step 2 commit `c55d8da` for `nintent`), not requiring a new
bump commit. Root's active-roadmap/README edits (Steps 2–3, commits `c55d8da`, `0f91675`) are already
committed as reviewable units, one per edited file group.

Root superproject itself: local `HEAD` is 1 commit ahead of `origin/main` (this session's Step 6
report `756150e`, plus this step's own upcoming commit) — `origin/main` currently resolves to
`7831b8f` (the VM p3 Steps 6–7 record, pushed since this phase's Step 8-partial report). Root push is
not attempted by this step; per this repository's git safety convention, pushing is confirmed with
the user rather than done automatically — flagged in the final report's open items.

## 5. Exact matched tuple

| Repository | Revision | Remote status |
|---|---|---|
| superproject | `756150e2ca185fed451336df51e8064d53d98f1f` (root, pre-this-step; this report's own commit will follow) | 1 commit ahead of `origin/main` (`7831b8f`); not yet pushed |
| nctl | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | pushed; `origin/main` confirmed at the same commit |
| nintent | `c343c5a56047b0df9ad901dd4459863ef1954053` | pushed; `origin/main` confirmed at the same commit |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` | pushed, unchanged throughout this initiative |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | pushed, unchanged throughout this initiative |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | pushed, unchanged throughout this initiative |

This is the tuple the GitHub-based Phase 5 build will consume for `nintent`/`nctl`; `nauto`,
`nodeutils`, and `ansible_agdev` are unchanged by this initiative and need no coordinated revision
beyond what is already live-equivalent.

## 6. Live installed revision/migration state (re-recorded)

Re-confirmed read-only, unchanged since Step 0: `nautobot-intent-catalog` `0.9.0`, Git commit
`ad9d36397d23c269ad748e13acbccc532fa29f52`, migrations applied through
`0014_braindump_exchange_diary`. Local `0015`/`0016` remain unapplied live. All three Nautobot
containers healthy. No process on port 8300.

## 7. Live rollback tuple

```text
nintent: ad9d36397d23c269ad748e13acbccc532fa29f52 (installed commit, unchanged)
migration state: through 0014_braindump_exchange_diary
nctl/root pre-window tuple: the actual local-invocation revisions in place before the eventual
  maintenance window (nctl is not deployed into the Nautobot container; it runs locally against
  the live API) — no separate "live nctl commit" exists to roll back
database backup: not created here; Phase 5 owns creating it (plan §3.3/§9 Step 7.9)
```

## 8. What remains before Phase 5 can start

- **Root push**: this phase's own commits (culminating in this report) are not yet pushed to
  `origin/main`. Not required for the GitHub-based nintent/nctl image build (only `nintent`/`nctl`
  need to be reachable there, and both already are), but needed for anyone else reading this
  repository's `origin/main` to see the final documentation state.
- **Phase 5 itself**: the coordinated maintenance window (stop writes, back up the database, rebuild
  Nautobot from `nintent` `c343c5a`, apply `0015`+`0016`, activate `nctl` `ebe8a1d`, live smoke
  checks, dashboard-directory cleanup) is entirely separate, explicitly-approved, live work — not
  started, not scoped to this phase.

## 9. Confirmation of no live mutation

No rebuild, restart, migration, Job, desired/actual write, seed, reconcile apply, Ansible run,
dashboard-directory cleanup, or host mutation occurred in this step. All actions were git
commit/push-status checks and read-only live reconfirmation (§6).

## Gate

Final code/docs/migration revisions are committed; the nintent revision is remotely available for
the GitHub-based image build; rollback facts are exact; and no mixed-version deployment has begun.
Step 7 gate met (root push remains an open item, not a blocker to the tuple itself).
