# Phase 3 — Step 4: phase report + evaluation note

Date: 2026-08-04. Closes Phase 3 of [`../roadmap.md`](../roadmap.md) per
[`plan.md`](plan.md) Step 4. This also closes the workflow_agent roadmap:
after this phase the protocol continues as ongoing per-request practice,
not a roadmap.

## Status: complete

All three exit criteria are met, each against recorded evidence:

1. **At least one real request executed through plan → executor → report.**
   The swarmui/comfyui/prometheus drift diagnosis — genuinely wanted,
   still-unexplained findings carried since Phase 2, not a proof artifact.
   Plan ID `2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis`
   (plan + transcript + report in the plan-ID directory per contract §3);
   executor outcome `model-finished`, 4 turns, exactly the plan's 3
   read-only commands, all hypotheses confirmed, success evidence visibly
   matched ([report_step1.md](report_step1.md)).
2. **A WorkflowEpisode for that run.** Episode
   `2f2d3de6-039a-4a36-a6a6-152da8a92d51` (status `candidate`, the store's
   first row): `references.workflow_plan_id` carries the plan ID (contract
   §3 key); `report.planning_defect_or_execution_stop` answers the roadmap's
   evaluation question explicitly — neither: a clean completion
   ([report_step2.md](report_step2.md)).
3. **A short evaluation note** — below, in this report (the phase plan's
   "one page in `p3/`").

Commits: `ba106f5` (Step 1), `c99dd3d` (Step 2), `92cd4a6` (Step 3 skip
record), plus this report's commit. Root superproject only; no submodule
touched; no state-mutating or approval-marked command ran anywhere in the
phase. Root superproject push remains with the user, per convention.

## Evaluation note

### Runs executed

| Plan ID | Outcome | Episode |
|---|---|---|
| `2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis` | completed; H1–H3 all confirmed | `2f2d3de6-039a-4a36-a6a6-152da8a92d51` (candidate) |

One run — the phase's bar is one honest end-to-end real cycle, met.
Findings: all three drift entries are observation defects (swarmui/comfyui
run as StabilityMatrix user processes invisible to the observer; the
prometheus entry is a substring false positive on
`prometheus-node-exporter.service`). The cluster is correctly deployed;
the observer is what needs improving, and that is now recorded in the
episode for human selection.

### What broke, and what was fixed

**Nothing broke; nothing needed fixing.** Zero protocol-side commits
(contract/manual/prompt/harness all unchanged this phase). Tally:
planning defects 0, faithful-execution stops 0, clean completions 1.
Two imperfections observed, both recorded rather than fixed, deliberately:

- the known cosmetic v1 gap recurred (scratch narration above the report
  skeleton) — did not impair the report; "fix only when a real run forces
  it" was not triggered;
- the phase plan's hint mis-sketched the episode `report` namespace as
  free text; the API requires a JSON object — a hint inaccuracy, not a
  contract/manual defect (the actual conventions already say free-form
  JSON *object*), noted in report_step2 for the next author.

### Deferred-mechanism verdicts (roadmap decision 8)

All stay deferred — one clean run produced no failure that would justify
any of them:

| Mechanism | Verdict | Why (one line) |
|---|---|---|
| Task card schema | keep deferred | The four-section Markdown plan carried everything the run needed; no field was missed. |
| Workflow catalog | keep deferred | Known-workflow routing via skills/`nctl` commands sufficed; the plan just named commands. |
| Strict allowlists | keep deferred | The executor ran exactly the 3 planned commands; the lint + runtime `--yes`/`--allow-destroy` mirror was never even exercised. |
| Planner/executor API | keep deferred | File hand-off (`plan.md` in, `transcript.json`/`report.md` out) had zero friction at this volume. |
| Small-model replay gate | keep deferred | One-for-one obedience on the first attempt; no disobedience evidence to gate against. |

Also still deferred, from Phase 2's own list: marked-plan v2 handling
(interactive approval prompt) — no real run needed a marked step
([report_step3.md](report_step3.md)).

### Honest limits of this evaluation

One diagnostic run cannot show the separation "works"; per roadmap
decision 5 there is deliberately no validation phase — long-term use and
accumulating episodes are the evaluation. What this phase does show: the
full loop (real request → manual-guided plan → bounded executor run →
evidence-matched report → episode row) runs end to end with no manual
patching between stages.

## Handoff

This practice now continues per-request without a roadmap: plan real work
via `agentdocs/workflow-planning/`, execute via `executor/executor.py`,
record a WorkflowEpisode per non-trivial run, and let the easier-next-time
loop consume the episodes. The two observer improvement candidates await
human survey of episode `2f2d3de6-039a-4a36-a6a6-152da8a92d51`; marked-plan
v2 gets built the first time a real plan needs a marked step.
