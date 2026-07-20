# Phase 0 — Step 0.7 report: Assign work to phases and perform a consistency review

Parent: [plan.md](plan.md) Step 0.7.

## What was done

Added `field-classification.md` §7 (lifecycle ingress matrix for `DesiredNode.lifecycle` and
`DesiredService.lifecycle`, each source individually verified rather than assumed from `models.py`
alone), §8 (phase assignment and decision summary — every contradiction/transition item from §2–§7
assigned to exactly one of Phase 1–4, with concrete numbered work items per phase), §9 (open
issues — confirmed empty of anything schema/behavior-shaping), and §10 (the roadmap's required
8-point consistency review, checked explicitly against this audit's own findings rather than
asserted).

## Key outcomes

- **`DesiredNode.lifecycle` has exactly 4 independent code-level default sources today, and all 4
  already agree (`planned`)** — the model field, the Quick Add form, the
  `create_desired_node_with_primary_endpoint` function signature, and the YAML loader. Phase 3's
  batch change is a clean, non-conflicting update across those 4 sites; REST and the import Job
  inherit automatically since neither has an independent default.
- **`DesiredService.lifecycle` needs no default change** — confirmed by combining §2/§3's
  finding (it gates only a drift warning, never production composition) with §7's ingress trace
  (its 2 creation paths already behave correctly: analysis-derived rows always start `proposed`,
  manually-declared YAML already overrides to `active` when meant). This is recorded as a
  considered decision, not a gap, per the roadmap's own instruction to record what, if anything,
  consumes service lifecycle before deciding.
- **Phase assignment produced 6 Phase 1 items, 7 Phase 2 items, 4 Phase 3 items, and 10 Phase 4
  items** — every contradiction found across the whole audit (§2's per-field table, §5's transition
  map, §6's failure-scope matrix) has exactly one owner; none were left dangling or duplicated
  across phases.
- **Consistency review confirmed Phase 3's hard-block on Phase 1+2 is load-bearing, not
  procedural caution**: defaulting `DesiredNode.lifecycle` to `active` without Phase 1 would turn
  any newly-active, config-incomplete node into a cluster-wide abort (masked today only because all
  5 live nodes are `planned`); without Phase 2's derivation it produces the identical global failure
  by a different route (a newly-active node still has no operational config). Traced this rather
  than restating the roadmap's assertion.
- **Section 9 (open issues) is empty of anything that can change schema shape, tier, derivation,
  default, or phase ordering** — the two items that could have qualified
  (`DesiredIPRange.lifecycle`'s consumption, and the `UnclassifiedDiffCodeError` mechanism's exact
  scope) were both traced to definite answers in Steps 0.3 and 0.6 respectively, not deferred.
  What remains open (`IntentSource.ref`'s null-fetch resolution, `placement_policy`'s long-term
  fate, the placement-vs-node `Target.kind` choice) is explicitly implementation-shape detail the
  roadmap already reserves for a later phase's own plan, not a Phase 0 classification gap.

No blocking surprises requiring human judgment — this closes the last plan.md step (0.1–0.7). What
remains is assembling/polishing the deliverable as a whole, running the plan's full verification
checklist, and updating `roadmap.md` only where this audit replaced a provisional choice with an
authoritative one (per the plan's suggested commit order).

## Next step

Final assembly pass: re-read `field-classification.md` end-to-end for internal consistency, run the
full Verification section (doc/static checks + read-only live checks), and update `roadmap.md` only
where warranted (the `DesiredNodeOperationalConfig` dissolution decision and the
`actual_state_policy`-collapses-into-`declared_host_os` finding are candidates, since the roadmap
currently frames dissolution as "favored... unless the audit surfaces a reason" — Phase 0 now has
confirmed evidence, not just a favored default).
