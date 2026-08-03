# discuss_idea2 — Proposals for the Easier Next Time policy

A summary of opinions and proposals on idea.txt. (Written without having read
discuss_idea1.md.)

## Overall: agree with the policy

This project itself has already walked this path once. The README's "instead of
re-improvising the steps every time, we built a unified CLI, nctl" is exactly
the first lap of Easier Next Time. idea.txt promotes that from a one-off event
into a repeatable policy, which is consistent with how the project came to be.

Points especially worth supporting:

- **Separating operation time from improvement time.** Beyond avoiding
  interruption handling, this prevents the accident of half-building unverified
  automation mid-task (scattered, untested scripts).
- **The restraint of "manual improvement by human + agent is fine for now."**
  Same philosophy as README_DEV's "don't generalize until there is a concrete
  use case" — healthy.

## Proposal 1: split the level hierarchy into two axes and record a "target level"

### Problem

The difference between Level1 and Level2 is *where judgment lives* (human vs.
agent), while the difference between Level3 and Level4 is *determinism of
execution* (following a manual vs. a single command). These are different axes.
Example: "a human makes the judgment, and the agent just runs one existing nctl
command" is simultaneously Level1 and Level4.

### Proposal

Record the two axes separately in the audit:

| Axis | Example values |
|---|---|
| Where judgment lives | human instructed multiple times / agent judged autonomously / almost no judgment needed |
| Determinism of execution | improvised (SSH trial and error, etc.) / followed a manual / single command or script |

Why judgment remains with the human and why execution remains improvised call
for entirely different improvements, so recording them separately produces
better improvement proposals. Keeping the one-dimensional Level1–4 as an
approximate label for everyday conversation is fine.

### State explicitly that Level4 is not always the goal

Turn the opening concern of idea.txt (what to tolerate as non-deterministic)
into an explicit deliverable. The criterion is **frequency × risk**:

- Recurring work that involves mutation → promote to Level4
  (into nctl with a plan/apply boundary, per the existing dry-run policy)
- One-off, exploratory, or diagnostic work → staying at Level1–2 is
  **legitimate**. Do not force it into a manual.
- Make **"automate on the second occurrence"** the rule, and prohibit
  speculative automation on the first.

Audit results must record not only the "current level" but the **"target level
and its reason."** A record like "this task should stay at Level2 because ..."
is precisely the written statement of what is tolerated as non-deterministic.

## Proposal 2: build no new session log; start from existing records + self-report

### What already exists

- The deterministic side: `nctl ops` operation evidence (durable records)
- The improvised side (SSH trial and error, judgment process): Claude Code
  session transcripts

If the audit agent's input is **transcript + ops evidence**, the policy can
start with no new logging mechanism. Add recording formats only after the
missing information has been concretely identified.

### Cheap complement: an end-of-session self-report

At session end, have the agent leave a short structured self-report:

- What was improvised
- Which manuals (skills) were used, and whether they helped
- Where it got stuck, and what felt like a second occurrence

Far cheaper to audit than after-the-fact log archaeology; a strong candidate
for the first implementation.

### Narrowing the audit targets

Auditing every session is heavy. Restrict audits to sessions the operator
(human or agent) tagged as "this was painful / this felt like a second
occurrence."

## Proposal 3: manuals live in Git, formatted as Claude Code skills

### Location: Git only; database storage is not recommended

The README already draws the line: "Git holds framework and policy, never the
private cluster payload" — and workflow manuals are squarely on the
framework/policy side. Git provides review, diff, and rollback. Parameterize
cluster-specific secrets and values out into `.local` references.

### Format and delivery: the skill mechanism is nearly the exact answer

The final concern in idea.txt (context selection over a growing manual
collection — "for this kind of request, read only this manual") is precisely
what the Claude Code skill mechanism does:

- Each skill keeps only its "name + one-line trigger description" in context
  at all times
- The body is loaded only when a matching request arrives (lazy load)

Before designing a custom manual-delivery mechanism, start with
`.claude/skills/` (or index references from CLAUDE.md).

## Proposal 4: build decay countermeasures in from the start

The real enemy of a growing manual collection is not bloat but **staleness**.

- Require metadata on every manual: creation date + the versions it was
  verified against (e.g. the nctl commit)
- Position Level3 manuals as **stepping stones** toward Level4 (an nctl
  subcommand with tests). Once scripted, delete the manual body and leave only
  a pointer — apply README_DEV's breaking-change policy (leave no
  compatibility-only artifacts) to manuals as well
- Periodically inventory the collection; merge or delete duplicated or
  contradictory manuals

## Summary: three things to decide before designing

1. Two-axis split of the levels (where judgment lives × determinism of
   execution) plus mandatory recording of "target level + reason" — make this
   the mechanism that puts "what stays non-deterministic" in writing
2. Start logging with no new mechanism — transcript + ops evidence +
   end-of-session self-report. Restrict audits to tagged sessions
3. Manuals in Git + skill format — lazy load solves the context-selection
   problem; version metadata and "delete once scripted" counter staleness
