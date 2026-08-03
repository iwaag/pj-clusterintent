# Easier Next Time — Development Roadmap

Status: adopted 2026-08-03. Detailed plans are written per phase (`p1/plan.md`, …)
when each phase starts; this document fixes only the goals, order, and governing
decisions.

## Purpose

Make cluster operations easier the second time they occur: complete each request
with whatever means work today, then retrospectively convert the painful parts
into reusable runbooks and, when justified, bounded deterministic commands.

Inputs, in order of authority:

- [`idea.txt`](idea.txt) — the original policy idea
- [`discuss_idea1.md`](discuss_idea1.md) — full design (levels, episodes, task
  cards, replay verification, storage policy)
- [`discuss_idea2.md`](discuss_idea2.md) — minimal first implementation (no new
  logging, skills as manuals, decay countermeasures)

The two discussion documents agree on the core and differ mainly in scope. This
roadmap takes **discuss_idea2 as the execution plan** and **discuss_idea1 as the
design reserve** for mechanisms that become justified later.

## Governing decisions

These were settled during discussion; phases do not re-litigate them.

1. **Levels.** Adopt discuss_idea1 §3–4: the level (1–4) measures the reasoning
   burden on the executor of a workflow version, not who happened to run it or
   whether a human approved a plan. Record alongside it the separate attributes
   `human_guidance`, `execution_mode`, `outcome` — this covers discuss_idea2's
   two-axis concern without a second hierarchy.
2. **Target level is mandatory.** Every retrospective records `target_level` and
   its reason. "Stays at Level 2 because it is one-off diagnostics" is a valid
   and valuable conclusion; this record *is* the written answer to "what remains
   non-deterministic". Rule of thumb: automate on the second occurrence, never
   speculatively on the first. Promotion priority ≈ frequency × failure impact ×
   reasoning burden.
3. **No new logging mechanism.** Retrospective input is the Claude Code session
   transcript + `nctl ops` operation evidence + a short end-of-session
   self-report. Only sessions tagged "painful / felt like a second occurrence"
   get audited. New capture machinery is added only after a concrete missing
   field is identified twice.
4. **Manuals are Claude Code skills in Git.** Runbooks live under
   `.claude/skills/<workflow-id>/SKILL.md`. The skill mechanism's lazy loading
   (name + one-line trigger always in context, body loaded on demand) is the
   answer to idea.txt's context-selection concern — do not build a custom
   router. Frontmatter carries discuss_idea1's manifest fields so a catalog can
   be generated mechanically later: `id`, `version`, `execution_level`,
   `triggers`, `risk`, `prerequisites`, `last_verified` (date + relevant
   submodule SHAs).
5. **Decay countermeasures from day one.** A Level 3 manual is a stepping stone.
   Once its workflow is scripted into nctl (Level 4), delete the manual body and
   leave a pointer to the command — the breaking-change policy applies to
   manuals too. `last_verified` is refreshed on every successful use.
6. **Deferred, not rejected** (design preserved in discuss_idea1):
   - task cards, `allowed_commands` contracts, and workflow routing — frozen
     until a small local-model executor actually exists (§7–8);
   - small-model replay measurement (§12) — becomes the promotion gate at that
     time; until then, "used successfully on a real second occurrence" is the
     promotion evidence;
   - the `.local` reorganization and storage policy (§10–11) — a separate
     future initiative with its own roadmap; do not couple it here. New
     artifacts from this roadmap may already use the proposed locations
     (e.g. `.local/evidence/workflow-episodes/`).
7. **Time separation.** Cluster operation and workflow improvement happen in
   different sessions. An agent does not edit its own runbook mid-task.

## Execution environment and implementer discretion

This is an experimental cluster with no production users. Phases should impose
the **minimum** rules that keep evidence trustworthy, and otherwise leave the
implementer free. The only fixed prohibitions:

- no secrets, tokens, or private keys in Git-tracked files (skills included);
- retrospective artifacts reference `nctl` operation IDs instead of copying
  evidence bodies;
- do not claim a level or completion that the recorded evidence does not show
  (README_DEV completion language applies).

Everything else — file formats beyond the frontmatter fields above, self-report
wording, tagging convention, directory layout details — is implementer's choice,
to be fixed by use rather than by upfront design.

## Useful facts for implementers

- Session transcripts already exist:
  `~/.claude/projects/-Users-eiji-projects-pj-clusterintent/*.jsonl`. No work is
  needed to "start" logging.
- Operation evidence: `nctl ops list` / `nctl ops show OPERATION_ID`; raw
  artifacts under `<events.log_dir>/<operation_id>/`.
- Skills: `.claude/skills/<name>/SKILL.md` with `name:` and `description:`
  frontmatter is picked up automatically; the description doubles as the
  trigger line. Keep it one sentence and specific ("Recover a managed dnsmasq
  content mismatch"), since it is the only part always in context.
- Good first runbook candidates (recurring, multi-step, already partly
  deterministic): single-node reconcile with fresh observation, LXC guest
  retirement + prune, SSH enrollment recovery, local Nautobot stack
  repair/rebuild (`.local/localenv_memo.md`), nintent rebuild with the
  `--no-cache` SHA check.
- An "episode" is the audit unit, not a session: one task may span sessions,
  one session may hold several tasks. The self-report should therefore name the
  task and its operation/Braindump IDs, which is enough correlation for now.

## Phases

Each phase gets its own `pN/plan.md` and `pN/report.md` when started, run in the
established step-by-step style. Exit criteria below are the fixed part.

### Phase 1 — Policy and formats

Write the small set of documents that everything else references:

- `policy.md` in this directory: level definitions (adapted from discuss_idea1
  §3–4), the recorded attributes, the target-level rule, promotion/demotion
  rules, decay rules;
- a self-report template (a few structured lines: what was improvised, which
  skills were used and whether they helped, what felt like a second occurrence,
  operation IDs touched) and where it is written
  (`.local/evidence/workflow-episodes/<date>_<task>/`);
- the skill frontmatter convention (fields from governing decision 4);
- a one-paragraph pointer from `README_DEV.md` so future sessions know the
  policy exists and end with a self-report.

Exit: documents exist, README_DEV points at them, no behavior change yet.

### Phase 2 — First retrospective

Run the loop once on real material. Pick one tagged episode (or deliberately
run one real cluster task and self-report it), audit transcript + ops evidence,
and produce the first review: current level, target level + reason, the
concrete decisions/prohibitions/failure points worth encoding.

Exit: one review artifact under `workflow-episodes/`, and an explicit verdict —
either "promote, and to what" or "stays at current level because …". Both
outcomes complete the phase.

### Phase 3 — First runbook skill

Convert the Phase 2 verdict (or the best candidate from the list above if
Phase 2 concluded "no promotion") into one Level 3 skill: typed inputs, exact
permitted commands, fixed step order, enumerated branches, embedded
prohibitions and stop conditions, machine-checkable success evidence.

Then use it on a real similar request in a later session and record in the
self-report whether it actually reduced improvisation.

Exit: one skill in Git with valid frontmatter, one recorded real use, its
`last_verified` set from that use.

### Phase 4 — First Level 4 promotion (conditional)

If — and only if — the Phase 3 workflow shows a second real occurrence and its
frequency × risk justifies it, absorb the runbook into a bounded nctl command
(plan/apply boundary per the existing dry-run policy, fresh observation,
operation evidence, no-repeat proof). Delete the manual body, leave the
pointer. If the justification is absent, record that decision as the phase
result; that is a legitimate completion, not a failure.

Exit: either a tested nctl command replacing the manual, or a recorded
"remains Level 3 because …" verdict.

### Phase 5 — Steady state and review

After the loop has run end to end: inventory the skill catalog (staleness,
duplicates, contradictions), tune the self-report/tagging convention based on
what the audits actually used and ignored, and decide whether any deferred
mechanism (task cards, replay gate, `.local` reorg, episode schema) has now
earned its own roadmap.

Exit: a short evaluation report; Easier Next Time continues as an ongoing
practice rather than a roadmap.
