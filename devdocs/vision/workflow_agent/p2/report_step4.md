# Phase 2 — Step 4: phase report

Date: 2026-08-04. Closes Phase 2 of [`../roadmap.md`](../roadmap.md) per
[`plan.md`](plan.md) Step 4.

## Status: complete

All three roadmap exit criteria are met, each against recorded evidence:

1. **The harness is in Git.** Commit `229951d` (Step 1) added
   [`executor/executor.py`](../../../../executor/executor.py) (stdlib-only
   Python, ~330 lines: CLI, contract lint, ollama chat loop with the single
   `run_command` tool, turn/wall-clock/per-command caps, transcript+report
   collection) and [`executor/rule_prompt.md`](../../../../executor/rule_prompt.md)
   (the fixed executor rule prompt, quoting contract §2's hard rule
   verbatim); commit `7f72e41` (Step 2) carries the one rule-prompt
   tightening iteration. The contract-promised linter exists and was
   proven both ways: accepts the real convergence-check plan, rejects a
   synthetic unmarked-`--yes` plan ([report_step1.md](report_step1.md)).
2. **One completed run.**
   `.local/evidence/workflow-plans/2026-08-04_cluster-convergence-check/`
   holds `plan.md` + `transcript.json` + `report.md`; the transcript shows
   exactly the plan's two `nctl` commands and the report quotes the
   success-evidence summaries (`{"drifting": 4, "converged": 13,
   "unknown": 2}`, `{"satisfied": 3}`) with the correct
   known-accepted/unexplained classification — the success-evidence check
   visibly matched, so "completed" follows README_DEV §9's completion
   language ([report_step2.md](report_step2.md)).
3. **One deliberate stop-and-report run.**
   `.local/evidence/workflow-plans/2026-08-04_agscratch1-retirement-episode-lookup/`
   holds the same three files; the run executed only step 1, hit the
   planned "no episode referencing agscratch1" stop condition
   (`data.count: 0`), and the report names the stop point and quotes the
   matched condition ([report_step3.md](report_step3.md)).

Both runs pass the "usable report" bar: a reader who never saw the run can
tell which steps executed, where (if anywhere) it stopped, and the key
structured outputs (no `nctl` operation IDs appeared in either read-only
run, and both reports say so explicitly).

Commits: `229951d` (Step 1), `7f72e41` (Step 2), `2b6e814` (Step 3), plus
this report's commit. Everything is in the root superproject; no submodule
was touched; no state-mutating or approval-marked command ran.

## Decisions settled by use (were "implementer's discretion")

- **Model**: `qwen3.6:35b-a3b-coding-nvfp4` via ollama `/api/chat`
  (native tool calling, `temperature 0.1`, `num_ctx 32768`). One
  rule-prompt iteration sufficed; the `glm-4.7-flash` fallback was never
  needed.
- **Harness shape/invocation**: single stdlib-only script,
  `python3 executor/executor.py <plan-file-or-plan-id> [--lint-only]`;
  env overrides `EXECUTOR_OLLAMA_URL`, `EXECUTOR_MODEL`.
- **Caps**: 30 turns, 30 min wall clock, 180 s per command; cap hits are
  recorded outcomes (`turn-cap-hit`/`time-cap-hit`), never hidden. Neither
  proof run came near a cap (4 and 2 turns).
- **Formats**: `transcript.json` = `{meta, messages}` with the raw message
  array rewritten every turn (crash-safe); `report.md` = harness-stamped
  header (plan ID, model, UTC times, turns, commands, `harness_outcome`)
  + the model's final message verbatim. The harness judges only
  model-finished vs cap-hit vs chat-error; completed-vs-stopped is the
  model's `## status` line plus the human read — no judge was built.
- **Marked-plan policy v1**: plans containing `**approval required**` pass
  lint but are refused before any model call ("not supported yet");
  runtime mirror: a model-issued command carrying `--yes`/`--allow-destroy`
  under an unmarked plan is refused with a stop-condition tool result.
- **Rule prompt**: imperative decision-4 rules + verbatim contract §2
  quote + a mandatory report skeleton (`## status` / `## steps executed` /
  `## stop point` / `## key outputs` / `## assessment`). The one live
  lesson baked in: composing a written product is not a command — never
  `run_command` a file write (`cat >`/`tee`/editors).

## Residual work → Phase 3

- **Real use + WorkflowEpisode integration** is all of Phase 3: use the
  planner+executor for genuinely wanted work, record episodes via
  `nctl workflow-episode`, amend the rule prompt from real failures.
- **Ready first real request**: the still-open, still-unexplained
  `swarmui`/`comfyui` (`service_missing` on agpc) and `prometheus`
  (`service_observed_on_wrong_node`) drift — re-confirmed live by this
  phase's completed run.
- **Known-and-accepted v1 gaps** (fix only when a real run forces it):
  marked-plan execution is refused, not prompted; the model's final
  message can leak scratch reasoning above the skeleton (read from
  `## status` down); big command outputs (≳100 KB) would pressure the 32k
  context — plans should pre-filter; the WorkflowEpisode store is empty
  (count 0), so the Step 3 finding "agscratch1 retirement has no episode"
  is also a note for Phase 3's backfill-or-not decision.
- The root superproject push remains pending per the standing convention
  (user pushes).
