# Phase 4 Step 4 — Protect history and verify cross-links

Parent: [plan.md](plan.md) Step 4.

Executed 2026-07-25.

## 1. Reachability of historical core-reconcile Phase 3/5 reports

`devdocs/big/core_reconcile/p3/plan.md` and `p5/plan.md` both open with `Parent: [roadmap.md](../roadmap.md)`
— the same link a reader following either directory would see first. `roadmap.md`'s Phase 3 and
Phase 5 sections (edited in Step 3) now open with an explicit `(superseded and removed)` header and
a paragraph naming the removal roadmap, right where that parent link lands. No reader can reach
these historical plans through current-roadmap navigation without first passing the supersession
notice; no directory-level notice was added inside `p3/`/`p5/` themselves, since plan §4.6's "at
most a narrow directory-level notice ... if a direct entry point remains genuinely ambiguous" is not
triggered — the one-hop parent link already carries the notice.

## 2. No completed report was edited

`git diff --stat` against the pre-Phase-4 commit (`4f756f0`, "move folder", predating this phase's
own edits) for every historical directory named in plan §5.3 shows exactly one changed file in
total: `devdocs/big/braindump/roadmap.md` (the active roadmap itself, edited in Step 3 — not a
report). `core_reconcile/p3/`, `core_reconcile/p5/`, all of `braindump/p0/`–`p3/`, `vm/p1/`, `vm/p2/`,
and `better_usability/` are byte-for-byte unchanged. Completed Braindump and VM reports remain
unchanged, matching plan §9 Step 4.4.

## 3. Better Usability dashboard fixture

`devdocs/big/better_usability/p4/fixtures/dashboard_pre.json` (matched in the Step 1 token search)
has zero Python references anywhere in `nctl/` or `nintent/` (`grep -rln` for its filename found no
consumer). It is inert historical evidence, not a current test/runtime fixture.

## 4. Migration byte-identity

`git log -1` on each of `nintent/nautobot_intent_catalog/migrations/0009_reconciliation_status.py`,
`0010_operational_overrides_and_provenance.py`, `0015_compute_platform_instance_and_endpoint_mac.py`,
and `0016_remove_reconciliation_dashboard_surfaces.py` shows their last-touching commits all predate
this phase's first commit; this phase's own commits (`git status`/`git diff` throughout Steps 2–3)
never touched `nintent/nautobot_intent_catalog/migrations/`. All four remain byte-identical to the
Phase 3 handoff.

## 5. Operation artifacts

No operation log, JSONL file, or `result.json` under any tracked or `.local/` path was read, parsed,
modified, or archived by this phase. Only two evidence files were written, both new, under this
phase's own private `.local/remove-unused-surfaces/p4/<timestamp>/` directory.

## Gate

History is truthful (no historical plan/report/fixture edited), current guidance is unambiguous (the
one-hop roadmap link carries the supersession notice before any historical Phase 3/5 plan is
reached), and no evidence was deleted or altered for a cleaner grep result. Step 4 gate met.
