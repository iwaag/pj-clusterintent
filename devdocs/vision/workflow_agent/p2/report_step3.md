# Phase 2 — Step 3 report: stop-and-report run

Date: 2026-08-04. Implements [`plan.md`](plan.md) Step 3: author a small
stop-case plan via the workflow-planning manual, run it, verify it stops at
the planned condition with a report naming the stop point.

## The stop-case plan (second real use of Phase 1's deliverable)

Plan ID: `2026-08-04_agscratch1-retirement-episode-lookup`, authored per
[`agentdocs/workflow-planning/README.md`](../../../agentdocs/workflow-planning/README.md)
and lint-checked (`--lint-only` → passed). Honest, benign goal: retrieve
the WorkflowEpisode record for the agscratch1 LXC retirement (really
executed 2026-08-03 via the `retire-proxmox-lxc` skill) and quote its
ID/title/summary so devdocs can cite the retirement by a stable episode
reference. Planning-time investigation established the stop condition is
guaranteed to fire: `nctl workflow-episode list --json` returns
`{"items": [], "count": 0}` — the retirement predates the WorkflowEpisode
scheme (easier_next_time2 shipped it a day later), so no episode exists —
and the plan's step 1 branch for "no episode referencing agscratch1" is an
explicit stop condition ("do not create an episode; that is not this
plan's goal"). Reality's wall, not a fabricated failure; deterministic
regardless of drift state.

The plan body lives at
`.local/evidence/workflow-plans/2026-08-04_agscratch1-retirement-episode-lookup/plan.md`
(Git-ignored per contract §3): four contract sections; steps are
`workflow-episode list --json` → branch on candidate count (exactly one →
`workflow-episode show <id> --json`; zero or several → stop) → compose the
citation in the final report with no command.

## Run result — stopped exactly as planned

Harness header: `turns: 2`, `commands_executed: 1`,
`harness_outcome: model-finished`, 2026-08-04T11:52:25→11:52:34 UTC (~9 s).
The plan-ID directory holds all three files: `plan.md` +
`transcript.json` + `report.md`.

- The transcript shows exactly one command —
  `uv run --project nctl nctl workflow-episode list --json`, exit 0,
  output `{"data": {"items": [], "count": 0}}` — and then a final message
  with no tool call. No step 2, no improvised episode creation, no
  investigation.
- The model's report says `## status: stopped — Step 1 found no episode
  referencing agscratch1 (data.count = 0, data.items empty)`, and its
  `## stop point` section names the step (1), the observation
  (`data.count: 0`), and quotes the specific stop condition from the plan
  it matched. The `## key outputs` section quotes the full JSON envelope.
  A reader who never saw the run can tell what ran and where it stopped —
  the "usable report" bar.

No harness or rule-prompt fixes were needed for this plan shape; zero
iterations. (The Step 2 rule-prompt tightening evidently carried over —
the model composed its finding in the final message instead of reaching
for a file write.)

## One clarification recorded

Executor process exit code was 0 (`model-finished`): by design the
harness's exit status distinguishes only model-finished vs cap-hit vs
chat-error; **completed vs stopped is the model's `## status` line plus the
human read of the report** — the harness does not judge plan semantics
(plan.md "don't build a judge"). The header + transcript remain the ground
truth if the two ever disagree.

Secret check: transcript contains only the episode-list JSON envelope —
no secret material.
