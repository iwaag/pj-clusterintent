# Phase 1 — Step 2 report: Planner manual

Date: 2026-08-04.

## What was done

Wrote [`../../../agentdocs/workflow-planning/README.md`](../../../agentdocs/workflow-planning/README.md)
following the `brainforge`/`workflow-improvement` structural precedent (rule
→ procedure sections → scratch/storage → standard loop → when to stop and
ask → known gotchas). No dispatcher registration needed —
`agentdocs/README.md`'s generic "read `agentdocs/[task_name]/README.md`"
already covers the new directory (verified by re-reading it; unchanged).

Sections, matching plan.md's design hints:

- Audience note up front: strong model, not the cheap executor — opposite of
  `workflow-improvement`; assumes repo literacy.
- §1 input handling: confirmed request summary, free investigation, "needs
  confirmation" instead of guessing through ambiguity (discuss_idea1 §6.1).
- §2 known-workflow selection: skill/`nctl`-bounded-command check first,
  name-don't-restate rule, `execution_level: 3` as the strong-signal case.
- §3 unknown-work planning: allowed and normal (discuss_idea1 §5.2 quoted),
  small/observable steps, irreducible judgment routed to stop conditions
  instead of an open-ended "investigate and fix" step.
- §4 approval-mark rule: planning-side checklist referencing README_DEV
  §10.1 (production/external class) and §10.2 (scratch environment
  exemption), pointing back to the contract for exact syntax rather than
  duplicating it.
- §5 scratch space: `nctl session new workflow-planning --topic <slug>` for
  notes, final artifact goes straight to
  `.local/evidence/workflow-plans/<plan-id>/plan.md`.
- Standard loop (7 steps), when-to-stop-and-ask, known gotchas (marker is a
  literal-string match, not a concept; don't fabricate transcript/report
  files before an executor exists).

## Fixed-constraint check

1. No secrets/tokens/private payloads — file contains only doc paths,
   command syntax, and generic examples; confirmed by re-reading.
2. The manual teaches the exact hard rule and marker syntax by reference to
   the contract (§2/§4 here), rather than repeating it — avoids the two
   documents drifting out of sync on wording.
3. No completion claims beyond what this step did.

## Verification

Re-read the written file in full for structural completeness against the
plan's four required manual topics (input handling, known-workflow
selection, unknown-work planning, approval-mark rule) — all four present as
their own sections. Confirmed `agentdocs/README.md` needs no edit (its
routing rule is already generic). No test suite applies.

## Exit status

Step 2 done. Step 3 (real example plan, produced by actually following this
manual) is next.
