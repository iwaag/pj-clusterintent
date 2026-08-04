# Phase 1 — Step 4 report: discuss_idea1 amendments + phase report

Date: 2026-08-04.

## Step 4 work: the two amendments

Both added as visibly dated blocks (2026-08-04), consistent with how this
repo treats historical discussion records — the original 2026-08-04 text is
kept, not silently rewritten:

- **§6.2**: added a dated amendment block stating the hard rule verbatim (a
  step without `approval required` must not contain `--yes` or
  `--allow-destroy`) and pointing to `plan_contract.md` §2 as the frozen
  record of the rule plus its exact marker syntax.
- **§6.4**: replaced the "run both methods and compare" evaluation
  description with the adopted mechanism — continuous evaluation via
  `WorkflowEpisode` (`references` carries the plan ID, `report` notes
  planning-defect vs. faithful-execution-stop, no new logging), matching
  roadmap decision 5. The original comparison-plan prose is removed (not
  just appended over) since the roadmap explicitly settled this design
  question rather than leaving both options open; a pointer to `roadmap.md`
  decision 5 and `p1/plan.md` is left in its place for traceability.

## Phase 1 exit criteria vs. evidence

The roadmap fixes this exit: "contract and manual exist, one example plan
artifact produced by actually following the manual, discuss_idea1 amended."

1. **Plan artifact contract exists** —
   [`../plan_contract.md`](../plan_contract.md) (Step 1, commit `376f129`).
   Four required sections, exact `**approval required**` marker syntax, the
   hard rule verbatim, storage convention
   (`.local/evidence/workflow-plans/<plan-id>/`), WorkflowEpisode reference
   convention, one inline minimal example plus one approval-marked-step
   snippet.
2. **Planner manual exists** —
   [`../../../agentdocs/workflow-planning/README.md`](../../../agentdocs/workflow-planning/README.md)
   (Step 2, commit `6481f8e`). Covers input handling/"needs confirmation",
   known-workflow selection, unknown-work planning, the approval-mark
   checklist, scratch/storage flow.
3. **One real example plan artifact, produced by actually following the
   manual** —
   [`report_step3.md`](report_step3.md) (Step 3, commit `6bc6b63`) shows the
   walk: request summary chosen → scratch session opened via `nctl session
   new workflow-planning` → skill catalog checked (none applicable) → live
   `nctl drift --json` / `nctl relations --json` run to validate the plan's
   own steps and capture real `success evidence` numbers → no ambiguity
   found → plan written to
   `.local/evidence/workflow-plans/2026-08-04_cluster-convergence-check/plan.md`
   and inlined in the report (full body, since `.local` is Git-ignored). The
   plan itself was not executed by an executor — none exists until Phase 2 —
   consistent with the plan.md Step 3 design hint.
4. **discuss_idea1.md amended** — this step, both amendments applied and
   dated (above).

All four exit items are met.

## README_DEV completion-language check

This report claims only what the evidence in commits `376f129`, `6481f8e`,
`6bc6b63`, and this step's amendment commit shows: two frozen documents, one
plan artifact produced by a real walk-through with live command output
quoted, and two dated amendments. It does not claim the executor exists, the
example plan was executed, or the cluster is fully converged (Step 3's walk
found 3 unexplained drifting targets — `swarmui`, `comfyui`, `prometheus` —
still open, not resolved by this phase, correctly out of scope).

## Fixed-constraint check (whole phase)

1. No secrets/tokens/private payloads in any file this phase touched —
   `plan_contract.md`, `workflow-planning/README.md`, `report_step1-4.md`,
   the example `plan.md` (untracked, inlined in `report_step3.md`), and the
   `discuss_idea1.md` amendments contain only doc paths, command syntax,
   public hostnames/slugs already used elsewhere in devdocs, and JSON
   summary counts.
2. The hard rule appears verbatim in `plan_contract.md` §2 and now also in
   `discuss_idea1.md` §6.2's amendment.
3. No overclaimed completion — see above.

## Residual work for Phase 2

Phase 2 builds the executor harness against this now-frozen surface:

- Launch a local LLM with a fixed executor rule prompt (quoting
  `plan_contract.md` §2's marker rule) plus one plan artifact
  (`.local/evidence/workflow-plans/<plan-id>/plan.md`).
- Capture the transcript and execution report into the same plan-ID
  directory (`transcript.*`, `report.md` per contract §3).
- Prove it end to end on a benign plan, both a completed case and a
  deliberate stop-and-report case. The Step 3 example plan
  (`2026-08-04_cluster-convergence-check`) is a ready, real, read-only
  candidate for the completed case — no approval marks, so it's safe for a
  first harness run; its documented "unexplained drifting target" stop
  condition (step 3/4 of the plan, triggered by `swarmui`/`comfyui`/
  `prometheus` not matching the known-accepted list) is a ready candidate
  for proving the stop-and-report case, since that condition is already
  true against live state.
- Not yet resolved, deliberately out of scope until real use: whether
  `swarmui`/`comfyui`/`prometheus` drift is a real problem worth a Braindump
  or reconcile — flagged in Step 3's report for the user, not acted on here.

## Exit status

Phase 1 complete. Contract and manual are frozen and cross-linked; one real
example plan exists with full walk evidence; discuss_idea1.md carries both
amendments. Ready for Phase 2 planning when the user starts it.
