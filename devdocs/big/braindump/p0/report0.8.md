# Phase 0 Step 0.8 — Consistency review and handoff

Parent: [plan.md](plan.md), Step 0.8. Phase 0's final step — closes this documentation-only phase.

## Consistency review against the Step 0.8 invariants

Re-read `plan.md`'s "Authoritative minimal contract" section against each required invariant:

| Invariant | Verified in `plan.md` |
|---|---|
| Exactly two new domain models | `BrainDumpDocument`, `AlignmentReview` — no third model declared |
| Braindump has exactly three app-declared fields | `title`, `body`, `authorship` (§1) |
| Alignment Review has exactly two app-declared fields | `braindump`, `summary` (§2) |
| No persisted alignment/freshness status | §4's attention table is explicitly "computed... not persisted domain fields" |
| No JSON finding/score/confidence/fingerprint/grounding link/aggregate review/revision/archive model | None declared anywhere in §1–§3; §3 explicitly defers an aggregate view |
| Authorship cannot silently mislabel an agent transcription | §1: "no silent authorship default at the API/domain boundary... every programmatic writer must supply the choice explicitly" |
| An absent review is normal and visible | §2: "no review row means `unreviewed`... do not auto-create an empty review" |
| Review updates replace rather than append | §2: "re-evaluation replaces the existing summary in place... do not append revisions" |
| User text and AI text remain visually distinct | §2 closing paragraph + Step 0.5's escaped-rendering row |
| Arbitrary prose cannot trigger desired/actual-state writes | §5: "cannot itself mutate desired state" (stated for both Braindump and Review text) |
| Unmentioned actual services handled by conversation, not automatic judgment | §5: "unexplained... agent asks" |
| nctl reads with GraphQL, writes with REST | Step 0.3 table, confirmed live in report0.3.md |
| Braindump availability cannot affect drift/reconcile availability | Step 0.5: "No failure in this feature becomes a drift code or blocks reconciliation" |
| No compatibility artifacts or production-grade security work | Premises section + Step 0.6, confirmed live in report0.6.md |

All fourteen invariants hold with no contradiction found across the plan's own sections.

## Cross-check against prior steps

Reports 0.1–0.7 each independently verified their portion of this plan against the live nintent/nctl
source tree (not just internal plan self-consistency):

- 0.1: vocabulary/ownership matches `roadmap.md` exactly.
- 0.2: nintent's model/migration/forms/tables/views/urls/templates/navigation/filters/REST/GraphQL/
  docs/tests pattern matches the plan's stated current state, including the exact 3-viewset REST
  registration (`nodes`, `services`, `endpoints`).
- 0.3: nctl's GraphQL-read/REST-write split, thin-CLI pattern, and the forbidden integration points
  (`SourceSnapshot`, `drift/`, `reconcile/`, `production/`, `hosts_intent*`) hold as described.
- 0.4: every timestamp the freshness contract needs already exists in code with no new plumbing.
- 0.5: the failure/input table maps onto nctl's existing `NautobotError` hierarchy and exit-code
  pattern.
- 0.6: no real token or secret appears anywhere in `devdocs/big/braindump/`.
- 0.7: no runtime baseline changed this phase; the next migration is `0014_*`; the ten required
  Phase 1 test items don't duplicate an existing test module. One pre-existing, unrelated
  documentation staleness was found and flagged (`nintent/README_DEV.md:101`'s outdated "only two
  models have a REST API" claim) — not a Phase 0 blocker, and out of this phase's edit scope.

No step required an edit to `plan.md`'s domain contract; the plan is confirmed self-consistent and
consistent with the live repository as of 2026-07-21.

## Work assignment (per plan.md's own Step 0.8 list, restated only for handoff, not redefined)

- **Phase 1** (nintent): models, migration, UI, REST, GraphQL, documentation, tests, live schema
  verification — surfaces enumerated in Step 0.2.
- **Phase 2** (nctl): core/CLI CRUD, create-or-replace review operation, text rendering, timestamp
  attention hint, tests — surfaces enumerated in Step 0.3.
- **Phase 3**: live conversational scenarios and safety-boundary proof, per `roadmap.md`.
- **Phase 4**: optional `nctl serve`/presentation work, only after Phase 3 evidence.

## Exit criteria

Checked off in `plan.md` itself (matching this repository's established convention of marking plan
exit criteria `[x]` on completion, e.g. `devdocs/big/better_usability/p1/plan.md`):

- [x] Surface inventories checked against the current source tree.
- [x] Model fields, authorship semantics, cardinality, deletion behavior, validation settled.
- [x] Unreviewed/timestamp attention behavior settled without persisted status.
- [x] Drift/reconcile separation and conversation-first unmanaged-service policy explicit.
- [x] Phase 1 test and coordinated rollout obligations complete.
- [x] No schema-affecting open question remains.
- [x] `p0/report0.1.md`–`report0.8.md` record completion evidence without duplicating the contract.
- [ ] **The user approves this plan as the authoritative minimal contract.** Left unchecked — this
      is the one exit criterion that is the user's own judgment call, not something this audit can
      verify or grant on the user's behalf.

## Result

Every audit-able exit criterion is satisfied. Phase 0 is ready for the user's approval; once given,
Phase 1 (nintent implementation) may begin using this plan as the frozen, unexpanded minimal
contract.
