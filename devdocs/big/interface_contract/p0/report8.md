# Phase 0 Step 8 — Amend the active VM Phase 3 plan

Parent: [plan.md](plan.md), Step 8.

Made one narrow, additive amendment to `devdocs/big/vm/p3/plan.md`. No other tracked file besides
this plan, `devdocs/big/vm/p3/plan.md`, and this report changed in Step 8, per plan §2's allowed-file
list.

## Amendment content

1. Updated the existing "Supersession/coordinated-rollout note" (lines 16–31): the sentence claiming
   migration `0016` and the matching nctl/root revisions were "prepared but live deployment is still
   pending a coordinated maintenance window" was stale — Step 0 of this phase
   (`interface_contract/p0/report0.md`) independently reconfirmed migrations applied through `0016`
   and nintent `c343c5a5...` installed identically on web/worker/scheduler on 2026-07-25. Replaced
   with a dated status update stating the rollout is complete, not pending, and changed the
   paragraph's tense from "applies"/"activates"/"resume" to "applied"/"activated"/"resumed"
   accordingly.
2. Added a new "Interface-contract supersession note" immediately after, dated 2026-07-25, stating:
   - the `interface_contract` roadmap supersedes this plan's broad UI/REST/Source YAML mutation
     assumptions;
   - Steps 9–12 (canonical live seed / apply / repeat-import proof) now depend on: (a) this phase's
     live-vs-YAML disposition ledger (explicitly citing `report4.md`–`report6.md`, and noting that
     Phase 0 independently reconfirmed the exact `aghub`/`agdnsmasq` scope VM Phase 3's own Step 9
     already named, plus 3 additional live-only `DesiredIPRange` rows and an endpoint-addressing
     correction for `agbach`/`agpc`/`agstudio` this VM plan did not previously know about); (b)
     Phase 1's strict canonical YAML and dry-by-default Import implementation; and (c) the final
     matched live interface from Phase 4;
   - seeding through the compute REST collections, editable UI, or Source YAML diagnostic page is
     prohibited — YAML through the Import Job is the only supported seed path;
   - the compute seed must be part of the one reviewed `intent_sources.yaml` proposal, not a
     separate nauto-seed or REST-driven write;
   - VM Phase 3 keeps ownership of compute values, desired MAC, dnsmasq safety, target isolation,
     and the no-Proxmox-actuation proof;
   - `interface_contract` keeps ownership of Import Job behavior, source identity/digest, the exact
     preview/apply artifact, the coordinated desired-data transition, and route contraction;
   - one approved Import apply plus its repeat-import proof may satisfy both initiatives' apply
     requirements when the evidence carries both sets of required fields — no duplicate apply for
     the same YAML revision.

## What was preserved unchanged

Historical compute-schema, desired-MAC, migration (`0014`/`0015`), and safety evidence in Sections
1–7 and the plan-creation-time baseline in §4.1 were **not** rewritten — the amendment is additive
(two paragraphs inserted/edited near the top of the file) and does not touch the Exit Criteria
(§2), Implementation Contracts (§5), Deliverables (§6), Procedure (§7, including the unmodified
Steps 9–12 text itself — the new dependency is stated in the supersession note, not by editing
Step 9–12's own numbered instructions), or Verification Plan (§8). No earlier VM report was
rewritten.

## Consistency check with Phase 0 findings

VM Phase 3's own existing Step 9 text (unmodified) already said: "Compare `nauto/seed/
intent_sources.yaml` against live `aghub`/`agdnsmasq` rows field by field" and its Exit Criteria
(§2, unmodified) already said the seed must cover "only the confirmed `aghub-pve -> agdnsmasq`
relationship and endpoint MAC. No desired record is generated for the other eight observed guests."
Phase 0 Step 6's Decision 2 (`interface_contract/p0/report6.md`) independently reached the same
`aghub`/`agdnsmasq` scope from live-evidence-and-Braindump-attestation grounds — the two initiatives
agree without either having copied the other's conclusion, which is a positive cross-check rather
than a conflict requiring resolution.

## Gate

The VM plan cannot proceed through a route this initiative removes: seeding is explicitly restricted
to the YAML/Import path, and Steps 9–12's dependency on Phase 0/1/4 deliverables is now stated in
the plan itself rather than left implicit. Proceeding to Step 9.
