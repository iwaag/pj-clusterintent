# Phase 0 Final Report — Freeze Consumers, Live Ownership, and the Final Matrix

Parent: [plan.md](plan.md). Per-step detail: [report0.md](report0.md)–[report8.md](report8.md).

## 1. Status and timestamp

**Status: complete.** Audit window: 2026-07-25T12:20:38Z (start, Step 0) through 2026-07-25T12:53Z
(this verification, Step 9). All 10 procedure steps (0–9) executed, evidence-backed, one commit per
step.

## 2. Evidence location and redaction statement

Private evidence: `.local/interface-contract/p0/20260725T122031Z/` (directory mode `0700`, files
mode `0600`), 22 files (`00_...` through the GraphQL/ObjectChange/route JSON/text dumps listed in
report0–report4). No Braindump body, Alignment Review summary, raw `ObjectChange.object_data`,
token, credential, or raw SSH key was written to any tracked file; Braindump titles appear only in
the private evidence file `19_live_provenance_graphql.json`, never in a tracked report (Step 3,
Step 9 §6 below).

## 3. Exact repository/live revision tuple and dirty state

| Repository | Revision | State |
|---|---|---|
| superproject | `d73ea3d0937407d3a0d1de8b3bd743ec6907c234` (pre-Phase-0) → 9 commits added during Phase 0 | clean except this phase's own additions |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean, unchanged throughout |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean, unchanged throughout |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean, unchanged throughout |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean, unchanged throughout |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean, unchanged throughout |

All 5 submodule pointers are identical at Step 0 and Step 9 (`report0.md` vs. this section's
re-check) — no submodule commit was made or checked out during Phase 0.

## 4. Installed package/container and migration parity

nintent `c343c5a5...` installed identically on `nautobot-nautobot-1`, `-worker-1`, `-scheduler-1`
(Step 0). Nautobot `3.1.3`/Django `5.2.14`/PostgreSQL `15.17`. `nautobot_intent_catalog` migrations
applied through `0016_remove_reconciliation_dashboard_surfaces` at both Step 0 and this
re-verification (Step 9) — unchanged.

## 5. Current interface and size measurements

12 GraphQL-registered models, 7 REST ModelViewSets, 60 static / 61 resolver-walked UI `path()`
entries, 8 `fields = "__all__"` serializers, 954 nctl tests / 17,763 source / 19,380 test lines, 252
nintent test methods (statically counted, corroborating `remove_unused_surfaces` Phase 5's later
in-container figure over the roadmap's older 187 baseline) — all detailed in `report1.md`/`report2.md`.
All measured values matched the roadmap's 2026-07-25 baseline exactly except the two explicitly
reconciled deviations (test-count baseline supersession, an "about" estimate vs. an exact count),
both explained in `report2.md`.

## 6. Classified consumer manifest summary

Every match from the plan's mandatory 19-term search plus follow-up REST/CLI/Makefile/GraphQL
searches was classified per §5.1 (`report1.md`). Retained interfaces (`nodes`/`braindumps`/
`alignment-reviews` REST, 4 installed Jobs minus `PreviewIntentSourceAnalysis`, 11 CLI commands,
GraphQL for all objects except `IntentSource`) each have a named current caller. Deletion candidates
(4 REST ViewSets, all UI mutation surfaces, `PreviewIntentSourceAnalysis`, nauto
`GenerateDesiredServices`) have zero callers within the audit boundary — confirmed positively (not
merely absence of evidence) via nctl source greps returning zero matches for the four REST paths and
zero GraphQL `intent_source` reads.

## 7. Final interface matrix with evidence references

Adopted in full in `report7.md` §1 — the roadmap's existing matrix, now cross-referenced to Steps
0–6 evidence for every checkmark and deletion.

## 8. Frozen GraphQL selection manifest

4 pinned queries with normalized SHA-256 digests (desired snapshot, actual snapshot, Braindump
list, Braindump show) — `report7.md` §2. `IntentSource` GraphQL registration is removed in Phase 2
(zero nctl reader, confirmed).

## 9. Frozen REST method/field manifest

3 collections retained (`nodes` PATCH-narrowed to 3 fields; `braindumps`/`alignment-reviews` full
CRUD with explicit field lists), 4 deleted — `report7.md` §3. Current live `OPTIONS` still shows
unnarrowed CRUD on all 7 (Step 2) — expected pre-Phase-2 state, not a defect Phase 0 needed to fix.

## 10. Frozen read-only UI route manifest

11 retained list/detail route pairs (+ Braindump's nested review panel); all `*_add`/`*_edit`/
`*_delete`, Quick Host Add, and Source YAML routes removed — `report7.md` §4, live-route-walk-backed
(`15_ui_routes.txt`).

## 11. Frozen YAML root/field/ownership manifest

9 canonical roots (already enforced by the current loader, plus the confirmed-live unknown-root
defect to fix in Phase 1) — `report7.md` §5, including the 5 concrete Phase 1 content edits Step 6
decided (move Infrastructure source/services; drop 6 stale checked-in nodes; add `agdnsmasq`/
`aghub`/Manual/dnsmasq; correct 3 nodes' endpoint addressing to match live; add a
`desired_ip_ranges` root).

## 12. Frozen Job variable and artifact schemas

Import/Analyze/IPAM Job contracts adopted from roadmap §6.5 unchanged, no contradicting evidence
found — `report7.md` §6.

## 13. Live ownership/provenance summary

All structural rows across 7 models have evidence-backed provenance or explicit `unknown`
(`report3.md`): `human_ui`/session origin for all `DesiredNode`/`DesiredEndpoint`/`BrainDumpDocument`/
`AlignmentReview` rows and 5 of 6 `DesiredService`s; `nauto_seed` origin for the `Infrastructure`
IntentSource + its 5 services (`report5.md`); the `Manual` IntentSource / `dnsmasq` service /
one `DesiredServicePlacement` cluster had zero `ObjectChange` history and was resolved by user
attestation in Step 6 as Braindump-sourced confirmed intent.

## 14. Node/endpoint/live-YAML disposition ledger

`report4.md` (comparison) + `report6.md` (final dispositions): 3 overlap nodes
(`agbach`/`agpc`/`agstudio`, endpoint fields corrected to match live), 2 live-only nodes
(`confirmed_live_intent`, to be added), 6 checked-in-only nodes (`stale_seed`, to be dropped), 3
live-only `DesiredIPRange`s (`confirmed_live_intent`, to be added), 6 checked-in-only
`DesiredServicePlacement`/override rows (`stale_seed`, tied to the dropped nodes), 1 live-only
`DesiredServicePlacement` (`confirmed_live_intent`, to be added).

## 15. IntentSource/service disposition ledger

`report5.md`: `Infrastructure` + its 5 services `confirmed_checked_in_intent` (move from
`home_cluster.yaml` to `intent_sources.yaml` in Phase 1); `Manual` + `dnsmasq`
`confirmed_live_intent` per Step 6 Decision 2.

## 16. User decisions and external-caller attestation

`report6.md`, 5 decisions recorded with date (2026-07-25) and authority (repository owner,
interactive session): stale-checked-in-node omission, live-only-node/source/service/placement
carry-forward, endpoint-addressing-scheme correction, IP-range carry-forward, and the
no-external-caller attestation closing plan §5.3's deletion-proof requirement for every REST/UI
surface Step 1 found with zero in-repository caller.

## 17. VM Phase 3 amendment summary

`report8.md`: one additive amendment to `devdocs/big/vm/p3/plan.md` — corrected stale
migration-`0016`-pending language to reflect the now-confirmed-live state, and added an
"Interface-contract supersession note" making VM Phase 3 Steps 9–12 explicitly depend on this
phase's disposition ledger plus Phases 1/4, prohibiting compute-REST/editable-UI/Source-YAML
seeding, and stating the ownership split and duplicate-apply-prevention rule. No historical section
of the VM plan was rewritten. Cross-check: VM Phase 3's own pre-existing, unmodified Step 9/Exit
Criteria text already targeted the exact `aghub`/`agdnsmasq` scope Phase 0 independently confirmed
— positive agreement, not a conflict.

## 18. Non-mutation proof

- No REST `POST`/`PUT`/`PATCH`/`DELETE` was issued (only `GET`/`OPTIONS`/GraphQL query documents).
- No Nautobot Job was run: `JobResult` most-recent-row timestamp is unchanged at
  `2026-07-24 18:31:33Z` before and after the audit window (Step 0 §Jobs, Step 9 above); 0
  pending/running `JobResult`s throughout.
- Migration state unchanged (`0016`, both Step 0 and Step 9).
- No container was rebuilt or restarted (`docker ps` uptimes span the whole audit window
  uninterrupted).
- No nctl operation/event log was created during the audit window: `find ~/.local/state/nctl/events
  -name '*.jsonl' -newermt '2026-07-25 21:20:38'` (JST, the audit start) returns zero files — all
  pre-existing `.jsonl` entries from the same calendar day predate Phase 0's start time.
- `git diff --check` passes with zero output in the superproject and all 5 submodules.
- Only 3 tracked paths changed across the whole phase: this plan, the 9 `p0/reportN.md` files, and
  `devdocs/big/vm/p3/plan.md` (`git diff --stat` against the pre-Phase-0 commit, Step 9 above) — no
  runtime, seed, migration, or dependency file in any submodule changed.

## 19. Deviations and explicitly deferred items

- Test-count baseline: roadmap's "187 tests" (nintent Django-free suite) is superseded by
  `remove_unused_surfaces` Phase 5's later in-container figure of 252, independently corroborated by
  a static `grep -c "def test_"` count (`report2.md`) rather than re-running Django's `test` command
  against the shared live Postgres instance.
- The current YAML loader's "unknown top-level root is silently ignored rather than rejected" defect
  is confirmed live and carried to Phase 1 as a fix target, not fixed here (`report2.md`).
- The `home.arpa` DNS-naming convention's exact Braindump provenance is explicitly out of this
  initiative's scope per the user's own Step 6 answer — noted, not resolved (`report6.md` Decision
  3).
- The live `AI Resource Auto Review` JobHook remains explicitly deferred and untouched
  (`report0.md`, `report7.md` §8) — no code change.

## 20. Exit-criteria table and Phase 1 handoff

| Exit criterion (plan §10) | Met? | Evidence |
|---|---|---|
| Exact revision/live tuple recorded and reproducible | yes | `report0.md`, this report §3–4 |
| Every retained matrix checkmark has a named caller and exact evidence | yes | `report1.md`, `report7.md` §1 |
| Every planned deletion has no real caller within the audit boundary | yes | `report1.md`, `report6.md` Decision 5 |
| User attested to off-repository caller status | yes | `report6.md` Decision 5 |
| REST/GraphQL/UI/YAML/Job contracts frozen | yes | `report7.md` |
| All current structural desired identities have an evidence-backed disposition | yes | `report4.md`, `report5.md`, `report6.md` |
| No live/YAML discrepancy remains unresolved | yes | `report6.md` (all 5 decisions recorded) |
| VM Phase 3 seed steps use only the final canonical Import path | yes | `report8.md` |
| No live/desired/actual/Job/migration/operational mutation occurred | yes | this report §18 |
| Final report contains no secret or private prose | yes | this report §2, verified §6 above |

**Phase 0 is `complete`.**

Phase 1 receives: the confirmed live-to-YAML disposition ledger (§14–15 above,
`report4.md`–`report6.md`) including the 5 concrete content edits to
`nauto/seed/intent_sources.yaml`; the strict nine-root contract (`report7.md` §5); and the frozen
Import/Analyze Job schemas (`report7.md` §6). Phase 2 receives the exact REST deletion/narrowing
manifest and GraphQL confirmation contract (`report7.md` §3). Phase 3 receives the exact read-only
UI route manifest (`report7.md` §4). Phase 4 receives the revision tuple, live baseline, and
user-approved desired proposal boundary (this report §3–4, §14–16). VM Phase 3 receives the same
canonical seed/import contract via the `report8.md` amendment.
