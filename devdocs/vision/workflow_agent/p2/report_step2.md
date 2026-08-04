# Phase 2 — Step 2 report: completed run

Date: 2026-08-04. Implements [`plan.md`](plan.md) Step 2: execute
`2026-08-04_cluster-convergence-check` end to end with the live model
(`qwen3.6:35b-a3b-coding-nvfp4` via ollama), iterating the rule prompt as
needed.

## Result

**Completed on iteration 2.**
`.local/evidence/workflow-plans/2026-08-04_cluster-convergence-check/` now
holds `plan.md` + `transcript.json` + `report.md`. Harness header of the
kept run: `turns: 3`, `commands_executed: 2`,
`harness_outcome: model-finished`, 2026-08-04T11:50:19→11:51:21 UTC (~1 min
wall clock), executor exit 0.

The transcript shows exactly the plan's own commands and nothing else:

1. `uv run --project nctl nctl drift --json` → exit 0 (44,679 bytes JSON)
2. `uv run --project nctl nctl relations --json` → exit 0 (3,221 bytes JSON)

The model's report follows the rule-prompt skeleton, states
`## status: completed`, quotes the exact summary objects — drift
`{"drifting": 4, "converged": 13, "unknown": 2}`, relations
`{"satisfied": 3}` — and classifies all six non-converged targets exactly
as the plan's step 3 demanded: `agbach` (unknown), `dnsmasq` (unknown),
and the agdnsmasq-tied compute_instance as **known-accepted**;
`swarmui`/`comfyui` (`service_missing` on agpc) and `prometheus`
(`service_observed_on_wrong_node`) as **unexplained findings, recorded,
not resolved**. That matches the success-evidence expectations frozen in
the plan itself, so "completed" is what the recorded evidence shows, not
just the model's claim.

## Rule-prompt iteration (the real work of this step)

- **Iteration 1** (rule prompt as committed in Step 1): the model ran the
  two planned commands correctly, classified everything correctly — then
  improvised a third command, `cat > /tmp/assessment.md << 'EOF' …`, to
  "write the assessment", although plan step 5 says no command runs beyond
  steps 1–2. Outcome was `model-finished, turns: 4, commands_executed: 3`
  with a good report, but the transcript showed improvisation, which fails
  this step's exit bar. Artifacts preserved in the session scratchpad for
  comparison; the plan-ID directory keeps the passing run.
- **Fix**: extended rule 2 of [`executor/rule_prompt.md`](../../../../executor/rule_prompt.md)
  — composing a written product is not a command; write it in the final
  message; never use `run_command` to create or edit files (`cat >`,
  `echo >`, `tee`, editors).
- **Iteration 2** (prompt as now committed): zero unplanned commands;
  the assessment was composed in the final message. Done.

One iteration was enough; `glm-4.7-flash` fallback not needed.

## Observations for later phases

- The model's final message leaks some of its scratch reasoning (a stray
  `</think>` tag and a draft of the assessment before the skeleton
  sections). Harmless — the skeleton sections are all present and correct,
  and `report.md` is defined as the final message verbatim — but a Phase 3
  episode audit should read from `## status` down.
- The 44 KB drift JSON fits comfortably in the 32k-token `num_ctx`; a plan
  whose commands print much more than this would need the context raised
  or the plan to pre-filter (worth remembering when authoring plans).
- Secret check: the transcript contains only `nctl` JSON (slugs, UUIDs,
  machine-local event-log paths) — no tokens or secret material.
