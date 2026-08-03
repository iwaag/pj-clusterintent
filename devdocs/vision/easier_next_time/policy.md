# Easier Next Time — Policy

Status: adopted 2026-08-03 (Phase 1 of [`roadmap.md`](roadmap.md)).

Complete the current request with whatever means work today; make it easier
retrospectively. This document defines the vocabulary and the small set of
formats every later phase uses. It intentionally contains no enforcement
machinery.

## 1. Execution-difficulty levels

The level describes the reasoning burden a **workflow version** places on its
executor — not which model ran it, and not whether a human approved a plan. A
capable model running one bounded command is executing a Level 4 workflow; a
human approving a Level 4 dry plan does not lower its level.

- **Level 1 — Collaborative exploration.** Goal or acceptance condition still
  ambiguous; human and agent decide the approach while working; tools combined
  ad hoc; open-ended branches.
- **Level 2 — Agent-led orchestration.** Goal and tools known, but the agent
  composes the workflow: chooses commands and order, interprets output, must
  remember global prohibitions itself. Repeatable in principle, not yet
  encoded.
- **Level 3 — Selected runbook execution.** A specific runbook (skill) was
  selected before execution. Typed inputs, exact permitted commands, fixed
  step order, enumerated branches, prohibitions and stop conditions written in
  the runbook, machine-checkable success evidence. No free-form shell
  construction.
- **Level 4 — Single bounded task command.** One task-level command owns the
  multi-step workflow: validation, exact scope, dry plan, apply authority,
  actuation, fresh observation, bounded convergence or safe stop, durable
  evidence, no-repeat proof. `nctl reconcile HOST` is the model.

One request may contain subproblems at different levels (clarifying whether to
retire a guest may be Level 1 while the retirement itself is Level 4). Classify
the workflow actually used for each task, not the whole conversation.

## 2. Recorded attributes

A retrospective records, per task:

| field | values |
|---|---|
| `level` | 1–4, per §1 |
| `human_guidance` | `none` / `approval_only` / `judgment_required` / `unknown` (retroactive audit, transcript unrecoverable — do not guess) |
| `execution_mode` | e.g. `ssh`, `node_agent`, `runbook`, `nctl`, `ansible`, mixed |
| `outcome` | `completed` / `partially_completed` / `failed` / `interrupted` / `safe_stop` |
| `target_level` | 1–4 **+ reason** — mandatory, see §3 |

A safe stop can be the correct terminal result of a mature workflow; it is not
a failure and must not be improvised around.

## 3. Target level — what stays non-deterministic

Every retrospective states `target_level` with a reason. **"Stays at Level 2
because it is one-off diagnostics" is a valid, valuable conclusion** — this
record is the written answer to "what do we tolerate as non-deterministic".

Rules:

- Automate on the **second occurrence**. Speculative automation on the first
  occurrence is prohibited.
- Promotion priority ≈ frequency × failure impact × reasoning burden.
- Recurring work that mutates state → aim for Level 4 (an nctl command with the
  existing plan/apply boundary). One-off, exploratory, or diagnostic work →
  staying at Level 1–2 is legitimate.
- Until a small local-model executor exists, promotion evidence is "the runbook
  was used successfully on a real second occurrence", not replay measurement.

## 4. Self-report

At the end of a session that did non-trivial cluster work — always when
something felt painful or like a second occurrence — the agent writes a short
self-report to `.local/evidence/workflow-episodes/<YYYYMMDD>_<task-slug>/selfreport.md`:

```markdown
# Self-report: <task, one line>
date: 2026-08-03
tags: [painful | second-occurrence | routine]

## What was requested and what happened
<2-4 lines; outcome per §2 vocabulary>

## References
- nctl operation IDs: <...>
- Braindump / desired-state IDs touched: <...>
- session: <transcript filename if known>

## Improvised parts
<what required free-form judgment, trial and error, or SSH improvisation>

## Skills used
<which skills were loaded; did each actually help; what was missing>

## Second-occurrence feeling
<anything that felt like "we did this before"; candidate for a runbook>
```

Reference `nctl` operation IDs; do not copy evidence bodies. Only sessions
tagged `painful` or `second-occurrence` are expected to be audited. A later
review adds `review.md` beside the self-report with the §2 attributes and the
promotion verdict.

The episode directory — not the session — is the audit unit: one task may span
sessions and one session may hold several tasks; make one directory per task.

## 5. Runbook skills

Runbooks are Claude Code skills in Git: `.claude/skills/<workflow-id>/SKILL.md`.
Lazy loading (name + description always in context, body on demand) is the
context-selection mechanism; no custom router.

Frontmatter convention (beyond the standard `name`/`description`):

```yaml
name: recover-dnsmasq-mismatch
description: Recover a managed dnsmasq content mismatch via nctl reconcile.
version: 1
execution_level: 3
triggers: [dnsmasq_content_mismatch]
risk: production_external          # or: local_scratch, read_only
prerequisites: [ssh_enrollment]
last_verified: 2026-08-03         # date of last successful real use
verified_against: {nctl: <sha>}   # submodule SHAs the run used
```

Keep `description` one specific sentence — it is the only part always in
context. The body states: typed inputs, exact permitted commands, fixed step
order, enumerated branches, prohibitions, stop conditions
(`manual_intervention_required` returns the task to a human/capable model —
never improvise past it), and the success evidence to check.

## 6. Decay rules

- Refresh `last_verified` on every successful real use.
- A Level 3 skill is a stepping stone. Once its workflow is absorbed into an
  nctl command (Level 4), **delete the skill body and leave only a pointer** to
  the command — the breaking-change policy applies to manuals too.
- A skill whose `last_verified` is stale relative to breaking changes in its
  `verified_against` components is suspect: re-verify or delete on next
  inventory (roadmap Phase 5).
- Merge or delete duplicated or contradictory skills during inventory; never
  keep two runbooks for one workflow.

## 7. Time separation

Cluster operation and workflow improvement happen in different sessions. An
agent does not create or edit runbooks for the task it is currently executing;
it records the pain in the self-report and moves on.

## 8. Fixed prohibitions

Everything not listed here is implementer's discretion (experimental cluster,
no production users):

1. No secrets, tokens, or private keys in Git-tracked files, skills included —
   parameterize cluster-private values out into `.local` references.
2. Retrospective artifacts reference operation IDs; they do not copy evidence.
3. Do not record a level, outcome, or completion the evidence does not show
   (README_DEV completion language applies).
