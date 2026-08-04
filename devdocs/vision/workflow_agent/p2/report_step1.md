# Phase 2 — Step 1 report: harness + rule prompt + lint

Date: 2026-08-04. Implements [`plan.md`](plan.md) Step 1.

## What was built

New top-level [`executor/`](../../../../executor/) directory (outside
`nctl`, per roadmap decision 7), two Git-tracked files:

- **`executor/executor.py`** — the whole harness, one stdlib-only Python
  script (~330 lines, no dependencies, no uv project needed). Invocation:
  `python3 executor/executor.py <plan-file-or-plan-id> [--lint-only]`; a
  plan ID resolves to `.local/evidence/workflow-plans/<plan-id>/plan.md`,
  and all output goes to the directory containing the plan file.
- **`executor/rule_prompt.md`** — the fixed executor rule prompt (system
  message). Roadmap decision 4 in imperative form, quotes contract §2's
  hard rule verbatim, and gives the model an explicit report skeleton
  (`## status` / `## steps executed` / `## stop point` / `## key outputs`
  / `## assessment`).

## Decisions fixed by use (plan left these free)

- **Language/shape**: single stdlib-only Python script — no dependencies at
  all beat a uv project for a ~300-line harness.
- **Invocation**: `python3 executor/executor.py <plan>`; env overrides
  `EXECUTOR_OLLAMA_URL` (default `http://localhost:11434`) and
  `EXECUTOR_MODEL` (default `qwen3.6:35b-a3b-coding-nvfp4`).
- **Chat**: ollama `/api/chat`, `stream: false`, one declared tool
  `run_command(command)`, `temperature 0.1`, `num_ctx 32768`.
- **Caps**: 30 turns, 30 min wall clock, 180 s per command, 10 min per
  chat call. Hitting a cap is a recorded outcome (`turn-cap-hit` /
  `time-cap-hit`), not a hidden error.
- **Marked-plan policy v1**: a plan containing any `**approval required**`
  step passes lint but is **refused** with "not supported yet" before any
  model call. Real marked-plan handling waits for a Phase 3 need.
- **Command gating** (the three-line mirror of the lint): a `run_command`
  whose text contains `--yes`/`--allow-destroy` while the plan has no
  marked step is not executed; the model receives a
  `harness: REFUSED …` tool result telling it this is a stop condition.
- **Transcript format**: `transcript.json` — `{meta, messages}` where
  `messages` is the full raw array (system, user, every assistant
  tool-call message, every tool result with exact command, stdout, stderr,
  exit code, duration). Rewritten after every turn, so a crash mid-run
  still leaves the transcript up to that point.
- **Report format**: `report.md` = harness-stamped header (plan ID, model,
  start/end UTC, turn count, commands executed, `harness_outcome`) +
  `---` + the model's final message verbatim. `harness_outcome` is the
  harness's own ground truth: `model-finished` vs `turn-cap-hit` vs
  `time-cap-hit` vs `chat-error: …`. Exit code 0 only on
  `model-finished`; whether success evidence truly matched stays a human
  read of the report (no judge built).

## The lint (contract §2 grep + §1 sections)

Before any model call: exactly the four `##` sections
`goal/steps/stop conditions/success evidence` in order; the steps section
split into numbered step blocks; any block containing `--yes` or
`--allow-destroy` must contain a line that is literally
`**approval required**`; gated flags outside the steps section also fail.
Lint failure refuses the run (exit 1).

## Evidence (all run 2026-08-04)

1. **Lint accepts the real plan**:
   `python3 executor/executor.py 2026-08-04_cluster-convergence-check
   --lint-only` → `lint passed`, exit 0.
2. **Lint rejects a synthetic unmarked-`--yes` plan** (scratchpad fixture
   with `nctl reconcile something --yes` and no marker) → `lint FAILED …
   contract §2: step contains --yes/--allow-destroy without a literal
   '**approval required**' line`, exit 1.
3. **Marked plan: lint passes, v1 refuses** (scratchpad fixture copying
   the contract §4 marked-step example) → `lint passed` then
   `plan contains an '**approval required**' step; v1 does not support
   marked plans — refusing to run`, exit 1, no model call.
4. **Mocked chat run writes both files where they belong**: a scratchpad
   mock of `/api/chat` (first call returns one `run_command: echo
   mock-hello` tool call, second a final message) against a copy of the
   convergence-check plan → `outcome=model-finished turns=2 commands=1`,
   exit 0; `transcript.json` holds roles
   `[system, user, assistant, tool, assistant]` with the tool result
   `{"command": "echo mock-hello", "exit_code": 0, "stdout":
   "mock-hello\n", …}`; `report.md` holds the header + mock status.
   Fixtures stayed in the session scratchpad; nothing synthetic entered
   `.local/evidence/`.

No real-LLM run yet — that is Step 2's work.
