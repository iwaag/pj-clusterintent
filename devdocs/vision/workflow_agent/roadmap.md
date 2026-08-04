# Workflow Agent — Development Roadmap

Status: adopted 2026-08-04. Detailed plans are written per phase (`pN/plan.md`)
when each phase starts; this document fixes only the goals, order, and settled
design decisions.

## Purpose

Implement the agreement in [`discuss_idea1.md`](discuss_idea1.md): separate
wide-context, non-deterministic **planning** from narrow, plan-following
**execution**, so that a cheap local LLM executor works with a small bounded
context. The workflow agent is not a determinization machine — unknown or
one-off requests are planned non-deterministically; only recurring work is
later promoted through the Easier Next Time practice.

## Governing decisions

Settled during discussion; phases do not re-litigate them.

1. **Role assignment for v1.** The planner is the strong model (a Claude
   session) following a written manual; no planner code is built. The executor
   is a local LLM launched by a thin harness — that harness is the only new
   software in this roadmap.
2. **Context isolation is the mechanism, obedience is best-effort.** The
   executor gets a fresh context containing only the plan artifact and a short
   fixed rule prompt. Empirically, not carrying planning context into
   execution already improves small-model reliability; the harness guarantees
   this by construction.
3. **Plan artifact contract** (discuss_idea1 §6.2): a short Markdown file with
   exactly four required sections — `goal`, `steps` (enumerated branches and
   bounded retries live here), `stop conditions`, `success evidence` — plus
   `approval required` marks on steps that existing policy gates. One hard
   rule: a step without `approval required` must not contain `--yes` or
   `--allow-destroy`. Machine-checkable expected outputs per step (prefer
   `nctl` JSON output and operation IDs) are recommended, not required.
4. **Executor rules** (discuss_idea1 §6.3): follow step order, listed branches,
   and bounded retries; no unplanned investigation, command substitution,
   recovery, or scope expansion; on an unexpected state, stop and report.
   Continuing after a stop is a new, explicit planning cycle — never a silent
   extension of the same execution.
5. **No dedicated validation phase.** One or two trials cannot settle whether
   the separation helps; long-term use and user judgment will. Evaluation is
   folded into the existing WorkflowEpisode practice (easier_next_time2): the
   episode `references` namespace records the plan ID, and the `report`
   namespace notes, in free text, whether a failure was a planning defect or a
   faithful-execution stop. No new logging or measurement machinery.
6. **Evidence stays local, IDs go to the DB.** Plan artifact, executor
   transcript, and execution report are stored under one plan-ID directory in
   `.local`; WorkflowEpisode references that stable plan ID, never a
   machine-local path, and bodies are never copied into `raw_data`.
7. **Placement outside nctl.** The planner is non-deterministic and therefore
   does not belong inside nctl's deterministic drift/actuation/evidence
   backend. The harness is a thin separate frontend; its name (`wfagent` or
   other) and exact invocation are fixed at implementation time.
8. **No backward compatibility.** Standing breaking-change policy applies; no
   dual paths, no feature flags. Deferred mechanisms from discuss_idea1 §7
   (task card schema, workflow catalog, strict allowlists, planner/executor
   API, small-model replay gate) stay deferred until real failures justify
   them.

## Execution environment and implementer discretion

Experimental cluster, no production users. Fixed prohibitions are minimal:

- no secrets, tokens, or private payloads in plan artifacts, transcripts,
  reports, or Git-tracked files;
- plans must respect existing external/destructive approval boundaries
  (decision 3); the executor never disables a safety rule the plan omitted —
  but note the real barrier is nctl's own confirmation flags, not executor
  obedience;
- do not claim completion the recorded evidence does not show (README_DEV
  completion language).

Everything else — file naming, report format, harness language, prompt
wording, local-model choice — is implementer's discretion, to be fixed by use.

## Useful facts for implementers

- **The shared surface is the plan artifact.** Freeze its contract first;
  planner manual and executor harness both consume it and can then evolve
  independently.
- **Suggested storage**: `.local/evidence/workflow-plans/<plan-id>/` with
  `plan.md`, `transcript.*`, `report.md`; `<plan-id>` = `<date>_<slug>`,
  mirroring the operation-evidence pattern. `.local` is already Git-ignored.
- **The planner manual precedent is agentdocs** (`brainforge`,
  `workflow-improvement`): add the planning procedure as a manual the strong
  model follows. Skill lazy loading is already the workflow router — a plan
  step that uses a known workflow names the skill or `nctl` bounded command;
  do not build a catalog or router.
- **Success evidence should prefer deterministic outputs**: `nctl drift
  --json`, `nctl ops show OPERATION_ID`, `nctl relations --json`. This makes
  the executor's final check a comparison, not a judgment.
- **Keep the transcript next to the plan.** Later episode audits diff the
  executed command sequence against `steps` to detect unplanned operations —
  do not rely on the executor's self-report for that.
- **Execution report shape** (discuss_idea1 §6.3): steps executed, stop point
  if any, key structured outputs, related `nctl` operation IDs. This is
  deliberately the same material a WorkflowEpisode self-report needs, so
  feeding one into `nctl workflow-episode create` is a copy-shape operation.
- **First targets**: pick requests that are safe to run under a new harness —
  read-only diagnostics (`drift`, `relations`, ops inspection) or tasks on the
  persistent local scratch stack (`.local/localenv_memo.md`) before
  cluster-mutating reconciles.
- **Local-model side**: whatever runtime is used, the harness only needs
  "start a session with a system prompt + one file, capture output" — resist
  building more than that.
- **discuss_idea1.md needs two small amendments** when Phase 1 lands: replace
  §6.4 (dedicated comparison evaluation) with continuous WorkflowEpisode
  evaluation, and add the `--yes`/`--allow-destroy` rule to §6.2.

## Phases

Each phase gets its own `pN/plan.md` when started and runs in the established
step-by-step style (one report + one commit per step, pause before live or
hard-to-reverse actions). Exit criteria below are the fixed part.

### Phase 1 — Plan artifact contract + planner manual

Freeze the plan artifact format (decision 3) and the storage convention
(decision 6 / suggested layout above). Write the planner manual in agentdocs:
input handling (short request summary; return "needs confirmation" instead of
guessing through ambiguity — discuss_idea1 §6.1), known-workflow selection via
skills/bounded commands, unknown-work planning, the approval-mark rule. Author
one real example plan by following the manual. Amend discuss_idea1.md (two
amendments above).

Exit: contract and manual exist, one example plan artifact produced by
actually following the manual, discuss_idea1 amended.

### Phase 2 — Executor harness

Build the thin harness: launch the local LLM with the fixed executor rule
prompt plus one plan artifact, capture the transcript, and collect the
execution report into the plan-ID directory. Prove it end to end on a benign
plan (read-only or scratch-stack task): completed and stopped cases both
produce a usable report.

Exit: harness in Git; one completed run and one deliberate stop-and-report
run, each leaving plan + transcript + report in the plan-ID directory.

### Phase 3 — Real use and episode integration

Use the protocol on real requests as standing practice. After each
non-trivial run, create a WorkflowEpisode whose `references` carries the plan
ID and whose `report` notes planning-defect vs execution-stop. Make minimal
fixes to the contract, manual, and harness from what actually fails; record
whether any deferred mechanism (decision 8) has earned promotion.

Exit: at least one real request executed through plan → executor → report →
episode, plus a short evaluation note. After that this continues as ongoing
practice, not a roadmap.
