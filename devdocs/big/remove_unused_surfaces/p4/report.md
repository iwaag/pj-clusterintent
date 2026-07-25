# Phase 4 Final Report — Consolidate Current Documentation and Pre-deployment Evidence

Parent: [plan.md](plan.md) (all steps). Reports on root revision `50b20cd` (this phase's Step 7
commit; this report's own commit follows on top).

Status: **complete** (documentation Steps 0–5, retained verification/measurements Step 6, and final
commit/tuple preparation Step 7 are all implemented and committed. VM Phase 3 Steps 6–7 — initially
blocked at this phase's first pass — were completed and pushed by the user between this phase's
Step 5 and Step 6; independently re-verified rather than taken on trust, see §4 and
[report7.md](report7.md) §0. The live migration, coordinated deployment, and dashboard-directory
cleanup remain Phase 5 work, unchanged from the plan's own scope boundary.)

## 1. Execution timestamp and evidence

Executed 2026-07-25, across two passes (Steps 0–6 before the VM Phase 3 Step 6 block; Steps 6–7
resumed after the user completed and pushed VM Phase 3 Step 6/7). Private evidence directory:
`.local/remove-unused-surfaces/p4/20260725-172224/` (mode `0700`, files `0600`), containing
`revisions-start.txt`, `live-readonly-baseline.txt`, `deletion-search-before.tsv`,
`deletion-search-after.tsv`, `step6-command-surface.txt`, `step6-wheel-build.txt`,
`step6-plain-install.txt`, `step6-measurements.txt`, `step6-dependencies.txt`,
`step6-doc-linecounts.txt`, `step6-deletion-search-final.tsv`, `step7-live-reconfirm.txt`.

## 2. Starting and ending revisions

| Repository | Starting (Step 0) | Ending (Step 7) | Remote status |
|---|---|---|---|
| superproject | `a33687c821b7c26e65e145ac0966abc3a7ebcc7f` | `50b20cd` | 2 commits ahead of `origin/main` (`7831b8f`) — not yet pushed; see §14 |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | pushed (VM Phase 3 Step 7's fixup commit; this phase needed no separate nctl edit — §2.4/Step 1 confirmed its docs already current) |
| `nintent` | `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | `c343c5a56047b0df9ad901dd4459863ef1954053` | pushed (this phase's own Step 2 README commit) |
| `nauto`/`nodeutils`/`ansible_agdev` | unchanged | unchanged | pushed, untouched by this initiative |

## 3. Resolution of Phase 3's formerly-pending push

Phase 3's final report recorded nintent `0914ca496...` as `implemented, awaiting push`. Step 0
confirmed `origin/main` resolved to that exact commit before this phase's own edits — the push had
already happened. Phase 3's own historical report text was left unedited (plan §9 Step 0.3).

## 4. VM Phase 3 Step 6/7 coordination result

**Complete**, confirmed independently rather than taken on the user's word alone. At this phase's
first pass (through Step 5), `devdocs/big/vm/p3/` contained reports only through `report3.5.md`
("Proceeding to Step 6") and Steps 6–7 were correctly reported blocked (see [report6.md](report6.md)
for that gate check). The user then reported VM Phase 3 Steps 6–7 complete; before resuming, this
phase verified:

- `devdocs/big/vm/p3/report3.6.md` (Step 6, desired-MAC dnsmasq safety, `complete`) and
  `report3.7.md` (Step 7, pre-cutover review, `complete`) both exist.
- `git fetch` + `rev-parse origin/main` for `nctl` resolves to `ebe8a1d5...`, matching
  `report3.7.md`'s claimed final tuple exactly — the VM Step 7 fixup commit is pushed.
- `nctl`'s full test suite re-run by this phase independently: **954 passed**, matching the cited
  count.
- `nintent`'s diff since the Phase 3-proven commit (`0914ca4` → `c343c5a`) touches only
  `README.md`/`README_QUICK.md` — documentation alone, confirming the Phase 3 Nautobot-runtime proof
  remains valid.

Full detail in [report7.md](report7.md) §0.

## 5. Live installed revision/migration state, before and after

Unchanged throughout both passes of this phase (Step 0 and Step 7 re-confirmations, both read-only):
`nautobot-intent-catalog` `0.9.0`, Git commit `ad9d36397d23c269ad748e13acbccc532fa29f52`, migrations
applied through `0014_braindump_exchange_diary`. Local `0015`/`0016` remain unapplied live. No
process listens on port 8300. All three Nautobot containers healthy throughout.

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

Step 1 baseline vs. Step 5/Step 6 final searches, for the 6 `edit-current` files: root `README.md`
went from 5 stale command/prose lines to 0; `nintent/README.md` from 5 cache/link lines to 2 (both
inside the new removed-framing section); `nintent/README_QUICK.md` from 4 to 0 exact-token lines (2
bare-word "dashboard" mentions remain, both removal-framed, outside the 26-token exact set);
`core_reconcile/roadmap.md`, `braindump/roadmap.md`, and `vm/roadmap.md` each still contain
explanatory/historical mentions, all classified in [report5.md](report5.md) §3 and re-confirmed in
[report7.md](report7.md) §11 as supersession notices or history bracketed by an explicit superseded
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
touched. VM Phase 3 Step 6's actual desired-MAC dnsmasq implementation (landed independently in
`nctl` `cb655c6`, documented retroactively in `vm/p3/report3.6.md`) positively proves the same
properties in code: blocking findings suppress the whole render, `desired_mac_mismatch` is
manual-review-only, and blocked renders never reach SSH/Ansible.

## 10. Final deletion-search exceptions

See [report5.md](report5.md) §5 and [report7.md](report7.md) §11 for the complete classified tables
(Step 5 and the post-Step-6 re-run). Summary: 0 unexplained matches across both passes; all remaining
hits are `initiative-evidence` (this phase's own notices/reports, including this report itself),
`historical` (~105 files, header-bracketed), `migration` (3), `negative-test` (1), opaque-history
fixture (1), or `keep-unrelated` (~5 false positives, all substring hits on
`observed`/`reserved`/`published_ports` or the unrelated `ansible_agdev/api` FastAPI webhook
service named as plan §6.1's own example).

## 11. nctl/nintent tests and inherited-proof justification

Both suites re-run independently by this phase in [report7.md](report7.md) §2–5, after VM Phase 3
Step 6/7 completed: `nctl` full suite **954 passed**; `uv lock --check` clean; `nintent` local suite
**187 passed**. The Phase 3 252-test Nautobot-runtime proof is inherited (not rerun against
disposable state) because the nintent diff since that proof (`0914ca4` → `c343c5a`) is documentation
only — exactly the condition plan §7.2 item 4 requires for inheritance.

## 12. Source/test/template/doc line counts and collected tests

Measured with frozen path patterns in [report7.md](report7.md) §8: nctl `src/` 17,763 lines, nctl
`tests/` 19,380 lines, 954 collected pytest cases, nintent non-test Python (incl. migrations) 9,560
lines, nintent test lines 4,029, nintent template lines 1,327, 16 numbered migrations, current-
document set (16 files) 5,417 lines. All six nctl/nintent values match the plan §2.5 handoff baseline
exactly.

## 13. Dependency/plain-wheel results

[report7.md](report7.md) §6, §9: `nctl` direct dependencies `typer`/`httpx`/`pydantic`/`pyyaml`, dev
group `pytest`/`respx`, no `serve` extra; `uv.lock` resolves 26 packages, none of
`fastapi`/`starlette`/`uvicorn`/`websockets`/`httptools`/`uvloop`/`watchfiles`/`python-dotenv`. A
plain wheel built in a fresh `mktemp -d`, installed into a fresh venv with only its own dependencies,
shows the same 11-command `--help`, importable retained modules, `ModuleNotFoundError` on
`nctl_core.serve`/`dashboard`/`dashboard_render`, and no server-only package installed. Temporary
build/venv directories removed after use.

## 14. Matched and live rollback tuples

**Final matched tuple** (from [report8.md](report8.md) §5):

| Repository | Revision | Remote status |
|---|---|---|
| superproject | `50b20cd` (Step 7); this report's own commit follows | not yet pushed — see §18 |
| nctl | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | pushed |
| nintent | `c343c5a56047b0df9ad901dd4459863ef1954053` | pushed |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` | pushed, unchanged |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | pushed, unchanged |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | pushed, unchanged |

**Live rollback tuple** (confirmed live, read-only, unaffected by this initiative):

```text
nintent: ad9d36397d23c269ad748e13acbccc532fa29f52 (installed commit)
migration state: through 0014_braindump_exchange_diary
nctl/root pre-window tuple: the actual local-invocation revisions in place before the eventual
  maintenance window (nctl is not deployed into the Nautobot container)
database backup: not created here; Phase 5 owns creating it (plan §3.3/§9 Step 7.9)
```

## 15. Environment and temporary-state cleanup

The Step 6 wheel-build directory and venv directory (both under the OS `mktemp -d` area) were removed
after use, confirmed gone via `ls`. `git status --porcelain` clean in the superproject and `nctl`
after cleanup. The private evidence directory
`.local/remove-unused-surfaces/p4/20260725-172224/` is retained under `.local/` (git-ignored) as this
phase's own evidence, per plan §8 — not temporary state to remove.

## 16. Generated dashboard content

Not read or changed at any point in this phase. Step 0 recorded only the path, entry names
(`drift.json`, `index.html`), and byte sizes of `/Users/eiji/.local/state/nctl/dashboard/`; neither
file's content was opened.

## 17. Confirmation of no live mutation

No live Nautobot write, migration, Job run, desired/actual write, reconcile apply, Ansible
invocation, container rebuild/restart, or dashboard-directory cleanup occurred at any point in this
phase. All live-touching actions were read-only: container health, installed-package metadata,
`showmigrations`, a port-8300 listener check, and a job-results list query (Step 0 and Step 7, both
recorded).

## 18. Every omitted, substituted, inherited, failed, optional, or deferred check

- No plan-required check failed or was substituted with a weaker inherited proof; the one
  legitimate inheritance (nintent's Nautobot-runtime proof, §11) meets plan §7.2 item 4's own
  documentation-only condition exactly.
- **Open, not blocking**: the superproject (root) itself is not yet pushed to `origin/main` (2
  commits ahead: this phase's Step 7 commit `50b20cd` and this report's own commit). Plan §9's exit
  criteria require the *nintent* commit to be pushed and remotely verified (done, §14) but do not
  name a root-superproject push requirement; root push is left for the user, per this repository's
  general git-safety convention of never pushing without being asked.
- Everything else the plan's Step 8 report list requires is recorded in the sections above with a
  direct evidence pointer.

## 19. Exit-criteria table with evidence references

| Plan §11 criterion | Status | Evidence |
|---|---|---|
| Phase 3 push resolved without rewriting its historical report | ✅ | [report0.md](report0.md) §2 |
| VM Phase 3 Step 6 complete; Phase 4/VM Step 7 share one revision review | ✅ | §4 above, [report7.md](report7.md) §0 |
| Root README has no supported `dashboard`/`serve` instruction | ✅ | [report2.md](report2.md) §1 |
| nintent READMEs have no cache/dashboard/link/config contract | ✅ | [report2.md](report2.md) §2–3 |
| Current nctl docs describe only the retained surface | ✅ | [report1.md](report1.md) §2, [report7.md](report7.md) §7 |
| Current status documented as fresh `nctl drift`, not a cache | ✅ | [report2.md](report2.md) |
| Bounded operations/history documented via artifacts + `nctl ops` | ✅ | [report2.md](report2.md) |
| core-reconcile dashboard/realtime-API goals explicitly superseded | ✅ | [report3.md](report3.md) §1 |
| Braindump's optional server/dashboard integration superseded | ✅ | [report3.md](report3.md) §2 |
| Braindump models/UI/GraphQL/REST/CLI/authorship/prose-boundary retained | ✅ | [report3.md](report3.md) §2, §5 |
| Active VM roadmap has no dashboard/status-cache requirement | ✅ | [report3.md](report3.md) §3 |
| Active VM Phase 3 plan has no operative removed-surface dependency | ✅ | [report3.md](report3.md) §4 |
| VM safety/isolation/non-repetition properties unchanged | ✅ | [report3.md](report3.md) §5, §9 above |
| Historical plans/reports/fixtures preserved | ✅ | [report4.md](report4.md) |
| Migrations `0009`/`0010`/`0015`/`0016` unchanged | ✅ | [report4.md](report4.md) §4 |
| All required tokens searched across every repository/scope | ✅ | [report1.md](report1.md), [report5.md](report5.md), [report7.md](report7.md) §11 |
| Every remaining match has one allowed §6.3 classification | ✅ | [report5.md](report5.md) §5 |
| No unexplained current runtime/config/schema/dependency/instruction match | ✅ | [report5.md](report5.md) §2–3, [report7.md](report7.md) §11 |
| Final nctl suite and lock check pass after VM Step 6 | ✅ | [report7.md](report7.md) §2–3 |
| nintent local suite passes; runtime proof rerun/inherited with justification | ✅ | [report7.md](report7.md) §4–5 |
| Clean plain nctl install has no server/dashboard residue | ✅ | [report7.md](report7.md) §6 |
| Source/test/doc counts, command surface, dependency inventories repeatable | ✅ | [report7.md](report7.md) §8–9 |
| Exact final root/nintent/nctl/nauto/nodeutils/ansible_agdev revisions recorded | ✅ | §14 above |
| Exact live rollback commit/migration tuple recorded | ✅ | §14 above |
| Final nintent commit pushed and remotely verified | ✅ | §2, §4 above |
| Live Nautobot unchanged, migrations through `0014` | ✅ | §5, §17 above |
| No rebuild/restart/migration/Job/write/seed/apply/Ansible/host/dashboard mutation | ✅ | §17 above |
| Temporary state removed; generated dashboard content not read | ✅ | §15–16 above |
| Final report records all deviations/omissions/status | ✅ | this report |

## Gate

All 9 procedure steps ran to completion; every plan §11 exit criterion is met with a direct evidence
pointer. **Phase 4 status: complete.** The only open item is pushing the root superproject itself
(§18) — not a plan exit criterion, left for the user per this repository's push convention. Phase 5
(coordinated deployment: maintenance window, database backup, rebuild, `0015`+`0016` migration,
matching-nctl activation, live smoke checks, dashboard-directory cleanup) remains entirely separate,
unstarted, and requires its own explicit operator approval at each step.
