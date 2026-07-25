# Phase 4 Final Report — Consolidate Current Documentation and Pre-deployment Evidence

Parent: [plan.md](plan.md) (all steps). Reports on root revision `1308074`.

Status: **partially complete** (documentation Steps 0–5 implemented and committed per plan §1/§9;
Steps 6–7 — final measurements, matched/rollback tuple, and final commits — did not run because VM
Phase 3 Step 6 has not started, per plan §2.3/§9 Step 0.5's own explicit instruction for this
scenario. This is not an unexpected failure; the plan anticipated it at planning time and defines
exactly this outcome.)

## 1. Execution timestamp and evidence

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p4/20260725-172224/` (mode `0700`, files `0600`), containing
`revisions-start.txt`, `live-readonly-baseline.txt`, `deletion-search-before.tsv`,
`deletion-search-after.tsv`.

## 2. Starting and ending revisions

| Repository | Starting (Step 0) | Ending (this report) | Dirty state |
|---|---|---|---|
| superproject | `a33687c821b7c26e65e145ac0966abc3a7ebcc7f` | `1308074` (Step 6 report) | clean |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean, **unchanged** (no `nctl` edit was needed — plan §2.4 confirmed its current docs already clean) |
| `nintent` | `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean locally; **not yet pushed** — `origin/main` still resolves to `0914ca496...` |
| `nauto`/`nodeutils`/`ansible_agdev` | unchanged | unchanged | clean, untouched |

## 3. Resolution of Phase 3's formerly-pending push

Phase 3's final report recorded nintent `0914ca496...` as `implemented, awaiting push`. Step 0
confirmed `origin/main` now resolves to that exact commit — the push happened before this phase
began. Phase 3's own historical report text was left unedited (plan §9 Step 0.3); this fact is
recorded here as the Phase 4 starting state.

This phase's own two nintent commits (`c343c5a`, README-only) are **not yet pushed**. Per plan §9
Step 7.3 ("ask the user to push the final nintent commit; do not push it") and this repository's own
push convention, the push request belongs to Step 7 once VM Phase 3 Step 6 is complete and the
documentation is folded into one final reviewable nctl/nintent/root revision set — not requested
piecemeal mid-phase. **User action needed eventually, not now:** push `nintent` `c343c5a` (or its
Step-7 successor commit) to `origin/main` when Step 7 runs.

## 4. VM Phase 3 Step 6/7 coordination result

Not complete. `devdocs/big/vm/p3/` contains reports only through `report3.5.md` ("Proceeding to Step
6"); VM Phase 3 Step 6 (desired-MAC/dnsmasq deployability gate) has not started. No nctl/nintent
compute/MAC/dnsmasq code was touched by this phase (all edits were Markdown). See
[report6.md](report6.md) for the full gate re-check.

## 5. Live installed revision/migration state, before and after

Unchanged throughout, confirmed at Step 0 and re-confirmed now (no live check was repeated since no
live-affecting action occurred): `nautobot-intent-catalog` `0.9.0`, Git commit
`ad9d36397d23c269ad748e13acbccc532fa29f52`, migrations applied through
`0014_braindump_exchange_diary`. Local `0015`/`0016` remain unapplied live. No process listens on
port 8300. All three Nautobot containers healthy throughout.

## 6. Exact edited/verified-current/historical/migration/negative-test/keep-unrelated inventory

See [report1.md](report1.md) §4 for the full classification table (131 matched files: 6
`edit-current` + 1 narrow-wording `edit-current`, 9 `verified-current`, 3 `migration`, 1
`negative-test`, 1 opaque-history fixture, ~5 `keep-unrelated`, ~105 `historical`). Files actually
edited this phase (see [report2.md](report2.md), [report3.md](report3.md)):

1. root `README.md` — removed `nctl dashboard`/`nctl serve` commands and prose; fixed two
   pre-existing broken `devdocs/vision/core_reconcile` links.
2. `nintent/README.md` — removed the cache-writer REST sentence and the reconciliation-status/
   dashboard-link section; added a "Current status and operation evidence" section.
3. `nintent/README_QUICK.md` — removed the dashboard command/PATCH/`dashboard_url` instructions.
4. `devdocs/big/core_reconcile/roadmap.md` — rewrote Vision/design-conventions to the retained
   contract; marked Phase 3/5 `superseded and removed` with historical text preserved underneath.
5. `devdocs/big/braindump/roadmap.md` — marked optional Phase 4 serve/dashboard integration
   superseded; positively reaffirmed models/UI/GraphQL/REST/CLI/authorship/prose-boundary intact.
6. `devdocs/big/vm/roadmap.md` — added a removed-surfaces note; replaced 4 operative
   dashboard/status mentions (general finding contract, Phase 4 title+bullet, Phase 9 bullet,
   definition-of-done bullet) with the retained JSON/CLI/ops-evidence contract.
7. `devdocs/big/vm/p3/plan.md` — updated only the top supersession note's tense (removal implemented
   locally, live deployment pending).

`nctl/README.md`, `nctl/docs/*.md` (4 files), `nctl/example.nctl.toml`, `nintent/README_DEV.md`,
root `README_DEV.md`, and `devenv/nautobot/nautobot_config.py` were reviewed and found already
correct — `verified-current`, no edit.

## 7. Before/after current-document token counts

Step 1 baseline (`deletion-search-before.tsv`) vs. Step 5 final (`deletion-search-after.tsv`), for
the 6 `edit-current` files: root `README.md` went from 5 stale command/prose lines to 0; `nintent/
README.md` from 5 cache/link lines to 2 (both inside the new removed-framing section); `nintent/
README_QUICK.md` from 4 to 0 exact-token lines (2 bare-word "dashboard" mentions remain, both
removal-framed, outside the 26-token exact set); `core_reconcile/roadmap.md`, `braindump/roadmap.md`,
and `vm/roadmap.md` each still contain explanatory/historical mentions, all classified in
[report5.md](report5.md) §3 as supersession notices or history bracketed by an explicit superseded
header — zero operative instructions remain in any of the 6 files.

## 8. Supersession treatment for core-reconcile, Braindump, and VM

- **core-reconcile**: Phase 3 ("Visualization dashboard") and Phase 5 ("Realtime API layer") each
  carry a `(superseded and removed)` title and an explanatory paragraph linking
  `remove_unused_surfaces/roadmap.md`, with their original goal/body text preserved underneath and
  their historical `p3/`/`p5/` reports left unedited and reachable one hop away.
- **Braindump**: Phase 4 carries a `(superseded)` title; its two now-impossible options are
  struck through, not deleted; models/UI/GraphQL/REST/CLI/authorship/prose-boundary are unchanged
  and explicitly reaffirmed in the same paragraph.
- **VM**: a new removed-surfaces note under Purpose reframes every "dashboard"/"status effect"
  mention below it; 4 operative mentions (general contract, Phase 4, Phase 9, definition-of-done)
  were rewritten to the retained JSON/CLI/ops-evidence contract; `vm/p3/plan.md`'s existing
  supersession note (added at Phase 0 of this initiative) had only its tense updated.

## 9. Proof that VM desired-MAC and Braindump boundaries remain

Per-file `git diff` review (recorded in [report3.md](report3.md) §5): every edit to
`core_reconcile/roadmap.md`, `braindump/roadmap.md`, `vm/roadmap.md`, and `vm/p3/plan.md` is a
header addition, a vocabulary substitution ("dashboard tiles" → "JSON envelopes"), a strikethrough,
or a tense change. No line defining desired-MAC mismatch/ambiguity blocking, digest suppression,
planner/direct-apply suppression, zero-SSH/zero-Ansible proof, recovery, scope isolation,
non-repetition, or Braindump's models/UI/API/CLI/authorship/non-executable-prose boundary was
touched.

## 10. Final deletion-search exceptions

See [report5.md](report5.md) §5 for the complete classified table. Summary: 0 unexplained matches;
all remaining hits are `initiative-evidence` (this phase's own notices/reports), `historical`
(~105 files, header-bracketed), `migration` (3), `negative-test` (1), opaque-history fixture (1), or
`keep-unrelated` (~5 false positives, all substring hits on `observed`/`reserved`/`published_ports`
or the unrelated `ansible_agdev/api` FastAPI webhook service named as plan §6.1's own example).

## 11. nctl/nintent tests and inherited-proof justification — deferred to Step 6

**Not run in this phase.** Plan §7.2 item 1–5 requires the final nctl suite, `uv lock --check`, and
the local nintent suite to be run *after* VM Phase 3 Step 6, against the actual final code tree —
running them now against documentation-only changes would produce a snapshot Step 6's later code
changes could invalidate, and plan §7.4 explicitly warns against treating a premature count as
evidence. No nctl or nintent source, test, or migration file was touched this phase (only Markdown +
2 README files), so no regression risk exists from the edits actually made; this was not
independently re-verified by a live test run in this phase.

## 12. Source/test/template/doc line counts and collected tests — deferred to Step 6

Not measured in this phase, for the same reason as §11. Plan §7.1 requires these under frozen path
patterns as final Phase 4 evidence, which depends on VM Step 6's completed code tree.

## 13. Dependency/plain-wheel results — deferred to Step 6

Not run in this phase; §7.3's wheel-build/install proof is Step 6 scope and depends on the final
nctl revision, which does not exist until VM Step 6 lands.

## 14. Matched and live rollback tuples

**Live rollback tuple** (confirmed live, unaffected by this phase, read-only):

```text
nintent: ad9d36397d23c269ad748e13acbccc532fa29f52
migration state: through 0014_braindump_exchange_diary
nctl: no live-deployed nctl revision tracked outside this repo's own submodule pointer
      (nctl is invoked locally, not deployed into the Nautobot container)
root/other components: unaffected by this phase
database backup: not created (Phase 5 owns this, per plan §3.3/§9 Step 7.9)
```

**Final matched tuple: not recorded.** Plan §4.7 explicitly forbids inventing a provisional
deployment tuple before VM Phase 3 Step 6 and Step 7's single coordinated revision review. No matched
tuple is declared by this report.

## 15. Environment and temporary-state cleanup

No temporary build/test/wheel state was created this phase (Steps 6/7's build steps did not run), so
none required cleanup. The private evidence directory
`.local/remove-unused-surfaces/p4/20260725-172224/` is retained under `.local/` (git-ignored) as this
phase's own evidence, per plan §8 — not temporary state to remove.

## 16. Generated dashboard content

Not read or changed. Step 0 recorded only the path, entry names (`drift.json`, `index.html`), and
byte sizes of `/Users/eiji/.local/state/nctl/dashboard/`; neither file's content was opened at any
point in this phase.

## 17. Confirmation of no live mutation

No live Nautobot write, migration, Job run, desired/actual write, reconcile apply, Ansible
invocation, container rebuild/restart, or dashboard-directory cleanup occurred. All live checks
(Step 0, this report §5) were read-only: container health, installed-package metadata,
`showmigrations`, a port-8300 listener check, and a job-results list query.

## 18. Every omitted, substituted, inherited, failed, optional, or deferred check

- Step 6 (retained verification, measurements, wheel proof): **deferred**, blocked on VM Phase 3
  Step 6 (§11–§13 above).
- Step 7 (final commits, matched/rollback tuple, push request, remote-availability confirmation):
  **deferred**, same blocker.
- No check failed. No check was substituted with a weaker inherited proof — the ones not run were
  simply not attempted, per plan §2.3's explicit instruction, rather than run early and risk being
  invalidated by VM Step 6's later code.
- This phase's own nintent documentation commit (`c343c5a`) is prepared but intentionally not
  pushed, pending Step 7's single coordinated push request (§3 above).

## 19. Exit-criteria table with evidence references

| Plan §11 criterion | Status | Evidence |
|---|---|---|
| Phase 3 push resolved without rewriting its historical report | ✅ | [report0.md](report0.md) §2 |
| VM Phase 3 Step 6 complete; Phase 4/VM Step 7 share one revision review | ❌ not met | [report6.md](report6.md) |
| Root README has no supported `dashboard`/`serve` instruction | ✅ | [report2.md](report2.md) §1 |
| nintent READMEs have no cache/dashboard/link/config contract | ✅ | [report2.md](report2.md) §2–3 |
| Current nctl docs describe only the retained surface | ✅ (already true) | [report1.md](report1.md) §2 |
| Current status documented as fresh `nctl drift`, not a cache | ✅ | [report2.md](report2.md) |
| Bounded operations/history documented via artifacts + `nctl ops` | ✅ | [report2.md](report2.md) |
| core-reconcile dashboard/realtime-API goals explicitly superseded | ✅ | [report3.md](report3.md) §1 |
| Braindump's optional server/dashboard integration superseded | ✅ | [report3.md](report3.md) §2 |
| Braindump models/UI/GraphQL/REST/CLI/authorship/prose-boundary retained | ✅ | [report3.md](report3.md) §2, §5 |
| Active VM roadmap has no dashboard/status-cache requirement | ✅ | [report3.md](report3.md) §3 |
| Active VM Phase 3 plan has no operative removed-surface dependency | ✅ | [report3.md](report3.md) §4 |
| VM safety/isolation/non-repetition properties unchanged | ✅ | [report3.md](report3.md) §5 |
| Historical plans/reports/fixtures preserved | ✅ | [report4.md](report4.md) |
| Migrations `0009`/`0010`/`0015`/`0016` unchanged | ✅ | [report4.md](report4.md) §4 |
| All required tokens searched across every repository/scope | ✅ | [report1.md](report1.md), [report5.md](report5.md) |
| Every remaining match has one allowed §6.3 classification | ✅ | [report5.md](report5.md) §5 |
| No unexplained current runtime/config/schema/dependency/instruction match | ✅ | [report5.md](report5.md) §2–3 |
| Final nctl suite and lock check pass after VM Step 6 | ❌ not run | [report6.md](report6.md) |
| nintent local suite passes; runtime proof rerun/inherited with justification | ❌ not run | [report6.md](report6.md) |
| Clean plain nctl install has no server/dashboard residue | ❌ not run (Step 1/2 already proved this historically; not re-proven as final Phase 4 evidence) | [report6.md](report6.md) |
| Source/test/doc counts, command surface, dependency inventories repeatable | ❌ not measured as final evidence | [report6.md](report6.md) |
| Exact final root/nintent/nctl/nauto/nodeutils/ansible_agdev revisions recorded | ❌ no final tuple | §14 above |
| Exact live rollback commit/migration tuple recorded | ✅ | §14 above |
| Final nintent commit pushed and remotely verified | ❌ pending Step 7 | §3 above |
| Live Nautobot unchanged, migrations through `0014` | ✅ | §5, §17 above |
| No rebuild/restart/migration/Job/write/seed/apply/Ansible/host/dashboard mutation | ✅ | §17 above |
| Temporary state removed; generated dashboard content not read | ✅ | §15–16 above |
| Final report records all deviations/omissions/status | ✅ | this report |

## Gate

Steps 0–5 are complete and independently reviewable. Steps 6–7 are blocked on VM Phase 3 Step 6,
which has not started — this is the plan's own documented outcome for this exact situation (plan
§2.3, §9 Step 0.5), not a defect in this phase's execution. **Phase 4 status: partially complete.**
Do not treat this report as authorizing a deployment tuple, a push, or any live action; those remain
gated on VM Phase 3 Step 6 completing and a subsequent Phase 4 Steps 6–7 pass.
