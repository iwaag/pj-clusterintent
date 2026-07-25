# Phase 4 Step 0 — Reconfirm prerequisites, ownership, and non-mutation boundary

Parent: [plan.md](plan.md) Step 0.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p4/20260725-172224/` (mode `0700`, files `0600`), containing
`revisions-start.txt`, `live-readonly-baseline.txt`.

## 1. Revisions and dirty state

| Repository | Revision | Dirty state |
|---|---|---|
| superproject | `a33687c821b7c26e65e145ac0966abc3a7ebcc7f` | clean; up to date with `origin/main` |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean; matches `origin/main` |
| `nintent` | `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | clean; matches `origin/main` |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean; matches `origin/main` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean; matches `origin/main` |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean; matches `origin/main` |

The superproject's own `p4/plan.md` was untracked when this step began and was committed by the
user as `a33687c` ("plan") during this step's execution — that commit is the plan file only, is
owned by the user, and was not touched by this step. No other dirty state was found.

## 2. Phase 3 handoff: the formerly-pending nintent push

Phase 3's final report ([p3/report.md](../p3/report.md)) recorded nintent `0914ca496...` as
`implemented, awaiting push`. `nintent`'s `origin/main` now resolves to that exact commit
(confirmed via `git rev-parse origin/main` above), so the push has since happened. This is recorded
here as a Phase 4 starting fact per plan §2.1; the Phase 3 report's own then-accurate historical
text is left unedited.

## 3. VM Phase 3 dependency status

`devdocs/big/vm/p3/` contains reports through `report3.5.md` only. `report3.5.md` ends "Proceeding
to Step 6" — VM Phase 3 Step 6 (desired-MAC/dnsmasq deployability gate) has not started, and
`devdocs/big/vm/p3/plan.md` Step 6 is unimplemented. This matches plan §2.3's planning-time
observation exactly.

Per plan §2.3/§9 Step 0.5, this means: documentation-drafting Steps 1–5 may proceed now, but Steps
6–7 (final measurements, matched/rollback tuple, final commits) cannot run or complete until VM
Phase 3 Step 6 is done. If VM Step 6 is still incomplete when this phase reaches Step 6's gate, the
phase must stop there and report `partially complete` rather than invent a provisional tuple (plan
§2.3, §9 Step 8).

## 4. Live installed state (read-only)

- All three Nautobot containers healthy (`nautobot-nautobot-1`, `-worker-1`, `-scheduler-1`).
- Installed `nautobot-intent-catalog` `0.9.0`, Git commit `ad9d36397d23c269ad748e13acbccc532fa29f52`
  — matches plan §2.2 and the live rollback tuple named in plan §4.7.
- `nautobot-server showmigrations nautobot_intent_catalog`: applied through
  `0014_braindump_exchange_diary`; local `0015`/`0016` not applied live.
- No process listens on TCP port 8300.
- Most recent 5 of 330 job results are `SUCCESS`; no running/pending job observed in that page.

## 5. Local migration graph

`nintent/nautobot_intent_catalog/migrations/`: `0015_compute_platform_instance_and_endpoint_mac.py`
and `0016_remove_reconciliation_dashboard_surfaces.py` both exist, in order, and remain unapplied
live (§4 above).

## 6. Generated dashboard directory (path/entries/sizes only, contents not read)

`/Users/eiji/.local/state/nctl/dashboard/`: `drift.json` (1106 bytes), `index.html` (13905 bytes).
Neither file's content was opened. This directory remains Phase 5 cleanup scope.

## 7. Secrets and evidence-directory handling

`.local/secrets` confirmed ignored (`git check-ignore -v` → `.gitignore:2`); not read or copied.
Evidence directory created at mode `0700`; both files written at `0600`. No token, header, or row
content was written to tracked or private files.

## Gate

Dirty state is owned (one user-authored plan commit, untouched by this step); Phase 3's push is
confirmed available on `origin/main`; the VM Phase 3 dependency is explicit and unmet for Steps 6–7
while open for Steps 1–5; live remains at `0014` on the expected installed commit; no removed-surface
process is active; local `0015`/`0016` exist unapplied in order; `.local/secrets` is ignored; and no
mutation occurred. Step 0 gate met.
