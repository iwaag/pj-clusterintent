# Phase 0 Step 7 — Amend the active VM Phase 3 plan

Parent: [plan.md](plan.md), Step 7.

Edited `devdocs/big/vm/p3/plan.md` in place, applying all ten exact semantic changes named by
plan §7 Step 7. Full diff saved to the private evidence file `vm-plan-diff.txt`.

## Changes applied

1. **Supersession/coordinated-rollout note** — added immediately after the plan's opening
   breaking-change paragraph, pointing at `devdocs/big/remove_unused_surfaces/roadmap.md` and this
   Phase 0 plan, naming the exact rollout sequence (`0015` then `0016` from one nintent revision,
   then one matching nctl revision, before operations resume) and stating explicitly that it does
   not change any compute/MAC/migration-`0015`/seed/safety/no-actuation requirement elsewhere in
   the plan.
2. **`desired_mac_mismatch` contract** — the exit-criteria bullet (§2) and the contract table (§5.9)
   both had their `dashboard/status effect` row/phrase replaced with "structured JSON drift and
   human-readable CLI drift presentation."
3. **Deliverables** (§6.1) — the `nctl` row now reads "drift/CLI output updates... no dashboard or
   serve output" instead of "drift/status/dashboard/CLI/serve output."
4. **Step 5** (§7) — "Keep valid compute collections out of compute drift/planner/dashboard/
   reconcile dispatch" lost `dashboard`; drift/planner/reconcile inertness is retained.
5. **Step 6** (§7) — "Wire structured mismatch finding, dashboard/status behavior, ..." became
   "Wire the structured mismatch finding into JSON drift and human-readable CLI drift output,"
   keeping manual-review classification, digest suppression, planner suppression,
   direct-apply/executor rechecks, and now explicitly naming zero SSH/zero Ansible calls.
6. **Step 8** (§7) — "...dnsmasq read path, dashboard read path, and dry reconcile" became
   "...dnsmasq read path, `nctl ops list`/`nctl ops show` evidence for an existing operation, and
   dry reconcile."
7. **Step 11** (§7) — "Assert the structured finding reaches JSON, human drift, dashboard/status
   derivation, ..." became "...reaches JSON drift, human-readable CLI drift output, ..."; the
   following zero-actuation assertion item now explicitly names "no dnsmasq action" as part of the
   zero-actuation proof for that fixture.
8. **Verification tables** (§8) — checked `## 8. Verification Plan` (repository commands, §8.2
   scenario matrix, §8.3 positive-evidence list) for `dashboard` before and after editing: zero
   occurrences in that section either way, so no additional edit was needed there — it was already
   phrased in terms of drift/render/reconcile/dnsmasq outcomes, not dashboard presentation.
9. **Phase Handoff** (§10) — "Phase 4 may then implement actual matching, compute findings,
   dashboard explanation, ..." became "...compute findings, structured CLI/drift/reconcile
   evidence, ..."
10. **Live window sequence** — covered by the new supersession note (item 1 above), which states
    the exact `0015` → `0016` → matching-nctl-revision sequence; the existing Step 8 procedure
    (§7, item 6, "Activate the matching nctl revision before routine operations resume") already
    matched this and needed no separate edit.

## Post-edit search

`grep -n "dashboard\|serve\|reconciliation_status\|reconciliation_checked_at"` against the edited
file found one remaining bare `dashboard` mention beyond the ones explained above: the §3.2
non-goals list's "dashboard compute tiles" phrase (an item Phase 3 explicitly does *not* add). Added
an inline parenthetical noting that surface no longer exists as a target at all per the new
supersession note, so there is nothing left to avoid adding to it — an explicit
historical/supersession explanation rather than a silent stale reference, per plan §7's closing
instruction. Every other remaining match is an unrelated use of "observed"/"reserved" substrings
(`dhcp_reserved`, "observed MAC/digest/behavior") caught by the loose grep pattern, not an actual
`serve`/`dashboard` token.

## Verification

```text
$ git diff --check -- devdocs/big/vm/p3/plan.md
(no output, exit 0)
```

No trailing-whitespace or conflict-marker problems. Focused diff saved to
`vm-plan-diff.txt` (123 lines).

## Gate

VM Step 6/8/11 acceptance, as now written, can pass using only retained CLI/evidence surfaces
(`nctl drift`, `nctl reconcile`, `nctl ops list/show`); no remaining acceptance bullet requires a
dashboard read path, dashboard/status derivation, or serve output. The plan's rollout sequence
(§7 Step 8 plus the new supersession note) cannot produce a mixed `0015`/`0016`/nctl tuple — it
still requires the matching nctl revision to activate before operations resume, exactly as before
this edit.
