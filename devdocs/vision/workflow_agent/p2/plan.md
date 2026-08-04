# Workflow Agent — Phase 2 Plan

Status: planned 2026-08-04. Implements Phase 2 of [`../roadmap.md`](../roadmap.md):
build the thin executor harness — launch a local LLM with the fixed executor
rule prompt plus one plan artifact, capture the transcript, collect the
execution report into the plan-ID directory — and prove it end to end with
one completed run and one deliberate stop-and-report run. This is the only
new software in the roadmap. The shared surface it consumes,
[`../plan_contract.md`](../plan_contract.md), is frozen; this phase does not
renegotiate it.

Destructive-phase note: no backward compatibility applies (roadmap
decision 8). There is no prior harness, no prior rule prompt, no prior
transcript/report format — nothing existing consumes anything this phase
creates, so every choice here is greenfield and may be changed freely later
without a migration path.

## Goal and exit criteria

Fixed by the roadmap:

1. The harness is in Git.
2. One **completed** run: a benign plan executed to its `success evidence`
   match, leaving `plan.md` + `transcript.*` + `report.md` in its
   `.local/evidence/workflow-plans/<plan-id>/` directory.
3. One **deliberate stop-and-report** run: a run that hits a stop condition
   and stops, leaving the same three files, with the report naming the stop
   point.

"Usable report" is the bar for both: a reader who never saw the run can tell
which steps executed, where (if anywhere) it stopped, and what the key
structured outputs / `nctl` operation IDs were (roadmap "Execution report
shape").

## Fixed constraints (everything else is implementer's discretion)

The roadmap's three standing prohibitions, applied to this phase — this list
is deliberately short; the execution environment is experimental with no
production users:

1. **No secrets, tokens, or private payloads** in the harness code, rule
   prompt, transcripts, reports, or any Git-tracked file. Watch the
   transcript specifically: the executor runs shell commands and the harness
   records their output verbatim, so never point it at a command that prints
   `.local/secrets` or token values. Hostnames, slugs, and JSON summary
   counts are fine (they are all over devdocs already).
2. **The approval boundary**: the harness/executor never adds `--yes` or
   `--allow-destroy` to a command the plan did not carry, and the contract §2
   hard rule is enforced by static grep before a run starts (the contract
   explicitly promises "Phase 2's linter greps for this literal string" —
   deliver that grep). Note the real barrier remains `nctl`'s own
   confirmation flags, not executor obedience — the lint is a tripwire, not
   the safety system, so keep it simple.
3. **Do not claim completion the recorded evidence does not show**
   (README_DEV completion language). A run "completed" only if the transcript
   shows the `success evidence` check actually matching.

Explicitly free: harness language and location (outside `nctl` per roadmap
decision 7 — a standalone script or tiny uv project both qualify), CLI
shape, local-model choice, rule-prompt wording, transcript format, report
format, how approval-marked steps are handled in v1 (see hints), turn/time
limits. Fix them by use, record what you fixed in the step reports.

## Verified facts (checked 2026-08-04 while planning)

- **`devdocs/vision/workflow_agent/p2/` exists and was empty** — this plan
  is its first file.
- **Frozen inputs**: [`../plan_contract.md`](../plan_contract.md) (four
  sections, exact `**approval required**` marker, storage convention) and
  [`../../../agentdocs/workflow-planning/README.md`](../../../agentdocs/workflow-planning/README.md).
  The contract §5 already reserves the executor rule prompt as a Phase 2
  deliverable that "quotes this contract's marker rule."
- **Local LLM runtime is ready, nothing to install**: `ollama` 0.31.1 is
  installed (`/opt/homebrew/bin/ollama`) and its server is already running
  on `localhost:11434`. Available models:
  `qwen3.6:35b-a3b-coding-nvfp4` (35B MoE, 262k context, **`tools`
  capability** — the obvious first pick), `glm-4.7-flash` (fallback if
  qwen disobeys), plus `gemma3`, `qwen3-vl`, `llava` (small/vision — not
  candidates). LM Studio's `lms` CLI also exists but ollama's HTTP API is
  the simpler target.
- **Native tool calling works on the first-pick model**: `ollama show`
  confirms the `tools` capability, so the harness can use `/api/chat` with
  one declared tool (e.g. `run_command`) instead of parsing fenced code
  blocks out of free text. This is the single biggest simplifier available —
  use it.
- **A ready completed-case plan exists**:
  `.local/evidence/workflow-plans/2026-08-04_cluster-convergence-check/plan.md`
  (Phase 1 Step 3's real example — full body inlined in
  [`../p1/report_step3.md`](../p1/report_step3.md) if the local copy is
  ever lost). Read-only, zero approval marks, and its steps were live-tested
  during planning: `uv run --project nctl nctl drift --json` and
  `nctl relations --json` both exit 0 with valid JSON from the repo root.
  Note its goal is an *assessment*, so the `swarmui`/`comfyui`/`prometheus`
  drift (still unexplained, still open — see p1/report_step4 residual note)
  does **not** stop it: the plan classifies them as "unexplained findings,
  recorded, not resolved" and completes. That makes it valid for the
  completed case despite live drift.
- **The stop case needs its own small plan.** The convergence-check plan
  only stops on command failure / invalid JSON, which won't happen naturally.
  Author a second tiny plan via the workflow-planning manual whose stop
  condition is guaranteed true against live state — see hints below.
- **`cagent/` (OpenCode-based cluster-agent) exists in this repo but is the
  wrong tool here**: it is a full agent stack with mTLS listeners and
  session state. The roadmap explicitly says the harness only needs "start a
  session with a system prompt + one file, capture output — resist building
  more than that." Do not route through cagent.
- **Environment class**: everything both proof runs touch is read-only
  `nctl` output against the local scratch stack (README_DEV §10.2,
  `.local/localenv_memo.md`). No production/external class step exists in
  this phase, so no human-approval pause point is required by policy —
  though the first-ever LLM-driven command execution deserves the timeout
  and turn cap below regardless.

## Design hints (advice, not requirements)

### The harness

- **Shape**: a small Python uv project (matching the repo's habits) or even
  one script, at the repo root or under a new top-level `executor/`
  directory — anywhere outside `nctl/src`. CLI takes a plan file or plan ID:
  `uv run executor .local/evidence/workflow-plans/<plan-id>/plan.md` or
  similar. Roadmap decision 7 fixed the *name* (`executor`), not the
  invocation.
- **Core loop** (~100 lines is a reasonable target): read plan → static lint
  → POST `/api/chat` to ollama with the rule prompt (system) + plan body
  (user) and one declared tool `run_command(command: str)` → on each tool
  call, run the command (subprocess, repo root cwd, per-command timeout,
  capture stdout/stderr/exit code — a non-zero exit is *data returned to the
  model*, not a harness crash) → append result, repeat → when the model
  answers without a tool call, treat that final message as the execution
  report. Bound the loop: a max-turn cap (~30) and a wall-clock cap, so a
  confused small model cannot spin forever; hitting a cap is itself a
  recorded stop, not an error to hide.
- **The lint** (before any model call): parse steps, then the contract §2
  grep — any `--yes` or `--allow-destroy` in a step without a literal
  `**approval required**` line fails the plan, refuse to run. Also cheap and
  worth it: require exactly the four `##` sections in order. Keep it under
  ~30 lines; it's a tripwire.
- **Approval-marked steps in v1**: both proof runs use unmarked read-only
  plans, so you can defer this entirely — simplest v1 policy: if the plan
  contains any `**approval required**` step, the harness prompts the human
  (y/N on the terminal) before executing that step's commands, or just
  refuses marked plans with "not supported yet." Pick one, write it in the
  step report, move on. Real marked-plan handling can wait for a Phase 3
  need.
- **Command gating**: obedience is best-effort by design (roadmap
  decision 2); do not build an allowlist (explicitly deferred, decision 8).
  One cheap harness-level check is defensible: reject a `run_command` whose
  text contains `--yes`/`--allow-destroy` when the current plan has no
  marked step — it mirrors the lint and costs three lines. Anything beyond
  that is scope creep.

### The rule prompt

- Fixed text, stored as a file in Git next to the harness (it is part of
  the frozen behavior, and Phase 3 will want to amend it from real
  failures). Content = roadmap decision 4 in imperative form: follow step
  order; only the branches and retries written in the plan; no unplanned
  investigation, command substitution, recovery, or scope expansion; on any
  state not covered by the plan, stop and report; continuing after a stop is
  never yours to decide. Quote contract §2's marker rule verbatim.
- Tell the model exactly what its final message must contain (this becomes
  `report.md`): steps executed, stop point if any, key structured outputs
  quoted, `nctl` operation IDs if any appeared. Small models do markedly
  better with an explicit output skeleton — give it the section headings.
- Keep it short (a page). A cheap executor with a 262k context does not need
  the plan contract's philosophy, only its orders.

### Transcript and report

- **Transcript**: dump the full message array (system, user, every tool
  call and tool result) as `transcript.jsonl` or `transcript.json` in the
  plan-ID directory. This is the artifact later episode audits diff against
  `steps` to detect unplanned commands (roadmap: "do not rely on the
  executor's self-report") — so it must contain the *exact* commands
  executed and their raw output, not a summary.
- **Report**: write the model's final message to `report.md` verbatim, plus
  a small harness-stamped header (plan ID, model name/tag, start/end time,
  turn count, completed vs stopped vs cap-hit as the *harness* saw it). The
  header matters: it is the ground truth when the model's self-report and
  reality disagree, and it is the material a Phase 3 WorkflowEpisode
  self-report copies.
- The harness, not the model, decides what "completed" means for its own
  exit code: model said done *and* no cap was hit. Whether success evidence
  truly matched is in the report for the human to check — don't build a
  judge.

### The two proof runs

- **Completed case**: run `2026-08-04_cluster-convergence-check`. Expected
  shape: model runs the two `nctl` commands, classifies the four
  non-converged targets (2 known-accepted, 3 unexplained), writes the
  assessment, reports completion. If qwen3.6 wanders — substitutes commands,
  invents extra investigation — that is a real result too: record it, tighten
  the rule prompt, rerun, and say so in the step report. Iterating the
  prompt against a live model is this step's actual work.
- **Stop case**: author a second tiny plan (follow the workflow-planning
  manual — this doubles as a second real use of Phase 1's deliverable) whose
  stop condition is guaranteed to fire. Reliable options: a step that runs a
  read-only `nctl` command against a target slug that does not exist (clean
  non-zero exit → stop condition), or `success evidence` that expects
  drift summary `{"drifting": 0, ...}` when live state is known to have 4.
  Prefer the first — it's deterministic and doesn't depend on drift state
  staying put. The plan must be honest (a real, benign goal whose plan
  happens to hit reality's wall), not a fake artifact — the manual's gotcha
  about not fabricating applies.
- Both runs are read-only against local state; no pause-for-approval is
  policy-required. Run them, keep the artifacts, quote from transcripts in
  the step reports (checking first that no secret leaked into the output).

### Model handling

- Start with `qwen3.6:35b-a3b-coding-nvfp4` (tools + context + coding
  tuning). If it cannot hold to the rules after a couple of prompt
  iterations, `glm-4.7-flash` is the fallback; note whichever you settle on
  in the report header and the phase report. Do not benchmark models — one
  model that works is the exit bar (roadmap decision 5: long-term use judges
  this, not trials).
- `ollama` request options worth pinning in the harness: `temperature` low
  (0–0.2 — an executor should not be creative), and a generous but finite
  `num_ctx` if the default truncates the plan + transcript.

## Steps

One report + one commit per step (`p2/report_stepN.md`), all in the root
superproject — no submodule is touched. No step is live or hard-to-reverse
(both proof runs are read-only), so no pause points; keep steps small and
honest per the standing style.

### Step 1 — Harness + rule prompt + lint

The executor harness in Git: CLI entry, static lint (contract §2 grep + four
sections), ollama chat loop with the single `run_command` tool, timeout and
turn caps, transcript + report collection into the plan-ID directory. The
fixed rule prompt as a Git-tracked file. Prove the non-LLM parts cheaply
(lint accepts the convergence-check plan, rejects a synthetic
unmarked-`--yes` plan; a mocked or trivial chat run writes both files where
they belong).

### Step 2 — Completed run

Execute `2026-08-04_cluster-convergence-check` end to end. Iterate the rule
prompt against the live model as needed (record iterations). Exit when the
plan-ID directory holds plan + transcript + report and the transcript shows
the plan's own steps, not improvisation.

### Step 3 — Stop-and-report run

Author the small stop-case plan via the workflow-planning manual (its own
plan-ID directory), run it, verify the run stops at the planned condition
and the report names the stop point. Fold in any harness/prompt fixes this
second plan shape forces.

### Step 4 — Phase report

Exit criteria against evidence (commits + both plan-ID directories),
README_DEV completion language, settled-by-use decisions recorded (model,
invocation, formats, marked-plan policy), and the residual-work note for
Phase 3 (real use + WorkflowEpisode integration; the still-open
`swarmui`/`comfyui`/`prometheus` drift remains a ready first real request).

## Out of scope for this phase

Phase 3's real-use practice and WorkflowEpisode creation; investigating or
fixing the `swarmui`/`comfyui`/`prometheus` drift (a candidate *subject* for
Phase 3, not Phase 2 work); executing any approval-marked or state-mutating
plan; nctl/nintent code changes; the deferred mechanisms (task card schema,
catalog, allowlists, planner/executor API, replay gate — roadmap
decision 8); model benchmarking or fine-tuning; routing through `cagent`.
