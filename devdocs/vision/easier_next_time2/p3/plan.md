# Easier Next Time 2 — Phase 3 Plan

Status: planned 2026-08-04. Implements Phase 3 of
[`../roadmap.md`](../roadmap.md): agentdocs `workflow-improvement` session type
+ policy.md / README_DEV.md rewrite. **Pure documentation phase — no code
change is expected** (verified below), no deploy, no live/hard-to-reverse
step, no test suite to run.

## Goal and exit criteria

1. Add `workflow-improvement` to `agentdocs/` as the second session type
   (after `brainforge`), covering the full procedure: human surveys the GUI →
   `nctl workflow-episode select` → start session → read from DB → improve →
   update `resolution` → `resolve`.
2. Rewrite policy.md §4: self-report destination becomes WorkflowEpisode
   creation, the audit unit becomes the episode ID, the later `review.md`
   becomes an `assessment` write. Update the matching README_DEV.md paragraph
   in the same change. Remove the old local-file workflow from the text.

Exit (fixed by the roadmap): **every document a new session consults points
only at the new scheme, with no remaining references to the old one.**

## Fixed constraints (everything else is implementer's discretion)

1. The roadmap's three standing prohibitions apply to the text you write:
   no secrets in Git/`raw_data`; `references` hold stable IDs, not local
   paths; no transcript/ops-evidence bodies copied into `raw_data`. The new
   documents must *teach* these rules, and must not violate them in their own
   examples.
2. No backward compatibility (governing decision 9): no "legacy fallback"
   paragraphs, no dual-destination instructions. The old local-file workflow
   is removed from normative text, not deprecated-but-described.
3. No import of the 3 existing `.local/evidence/workflow-episodes/`
   directories and no mechanism for them (decision 8). They may be deleted at
   any time — so no live document may depend on those paths resolving.
4. The time-separation rule stays intact (policy.md §7): cluster operation
   and workflow improvement remain separate sessions. Phase 3 restates it in
   the new session type; it does not weaken it.

Wording, document structure, section order, and how much of the JSON shape to
show in examples are free choices.

## Verified facts (checked 2026-08-04 while planning)

- **No nctl change is needed.** `nctl session new workflow-improvement
  --topic <word>` already works: `session.py` validates `task_name` against a
  regex only, not against an enum or the agentdocs directory. Once the manual
  exists, the argument's help text ("matches an agentdocs/<task_name>/
  manual") simply becomes true for it.
- **The live command surface (Phase 2, final names)** — quote these exactly
  in the manual:

  | command | notes |
  |---|---|
  | `nctl workflow-episode list [--status S ... \| --all] [--json]` | default filter is `candidate`+`selected`; `--status` repeatable |
  | `nctl workflow-episode show <id> [--json]` | `--json` returns full `raw_data` — this is the agent's fetch contract |
  | `nctl workflow-episode create --title T [--raw-data JSON \| --file PATH]` | status always starts `candidate` |
  | `nctl workflow-episode write <id> <namespace> [--data JSON \| --file PATH]` | namespace ∈ report/assessment/references/resolution; replaces that namespace wholesale, others untouched |
  | `nctl workflow-episode select <id>` | `candidate → selected` |
  | `nctl workflow-episode resolve <id>` | `selected → resolved` |
  | `nctl workflow-episode dismiss <id>` | `candidate\|selected → dismissed` |

  Transitions are forward-only; violations exit 2 with
  `workflow_episode_transition_ineligible`. There is **no DELETE** — a
  mis-created episode can only be `dismiss`ed; say so in the manual.
- **Two live seed episodes exist** for copy-paste-able examples that a reader
  can actually run: `6569864c-8914-4e2e-9368-b7e04c64ac74` and
  `3915b1e4-8285-431b-bd7a-23203900c08d` (both `resolved`, so visible only
  via `--status resolved` / `--all`). Using real IDs in examples is fine, but
  don't make any instruction *depend* on them existing.
- **Documents a new session consults that still reference the old scheme**
  (the complete list — root README.md, nctl README/docs, and agentdocs are
  already clean):
  - `devdocs/vision/easier_next_time/policy.md` §4 (the whole self-report
    template + `review.md` sentence + "episode directory is the audit unit"
    paragraph).
  - `README_DEV.md` §"Easier Next Time: end sessions with a self-report"
    (currently points at `.local/evidence/workflow-episodes/`).
  - `.claude/skills/retire-proxmox-lxc/SKILL.md` — two references to
    `.local/evidence/workflow-episodes/...` paths (its verification-evidence
    link and its manual_review table's audit citation). These are *historical
    citations*, but the files they point at may be deleted at any time per
    decision 8, so reword them to stand alone (e.g. "verified in the
    2026-08-03 agscratch1 retirement episode") without a load-bearing local
    path.
- **Historical devdocs are out of scope.** `devdocs/vision/easier_next_time/`
  roadmap/plans/reports and `easier_next_time2/discuss_idea1.md` describe
  what happened or what was discussed; they are records, not documents a new
  session consults. Leave them untouched — rewriting history would itself
  violate the evidence rules.
- **agentdocs precedent**: `agentdocs/brainforge/README.md` is the structural
  template — rules up top, an "allowed to touch" table, scratch-area layout
  under `.local/workspace/<task_name>/<slug>/`, a standard per-turn loop, key
  commands, "when to stop and ask", known gotchas. Note a small inconsistency:
  `agentdocs/README.md` says manuals live at `agentdocs/[task_name]/README.txt`
  but brainforge actually uses `README.md`. Follow brainforge (`README.md`)
  and fix the dispatcher text while you're there — it's one line.

## Design hints (advice, not requirements)

### The workflow-improvement manual (`agentdocs/workflow-improvement/README.md`)

- **Audience framing**: like brainforge, write it to an agent that may be a
  cheap/local model — short imperative rules, explicit stop conditions, no
  reliance on the reader inferring policy from other documents (but do link
  policy.md for the level vocabulary rather than duplicating §1–§3).
- **The full lifecycle** (discuss_idea1 §6 is the source): human surveys GUI
  → human (or agent on request) runs `select` → `nctl session new
  workflow-improvement --topic <short-slug>` for scratch space →
  `nctl workflow-episode show <id> --json` to fetch report / assessment /
  references → only if needed, open referenced transcripts / `nctl ops`
  evidence → improve policy / agentdocs / skills / nctl / submodules with the
  matching tests → `write <id> resolution --data ...` → `resolve <id>`.
  A "no improvement warranted" outcome ends in `dismiss` with the reasoning
  written first (a resolution or assessment note) — make that path explicit
  so dismissal isn't evidence-free.
- **Prohibitions worth stating in the manual** (all inherited, not new): do
  not edit the episode's `report` namespace (it is the original evidence —
  the per-namespace write API exists precisely so you don't); do not let an
  improvement decision write desired or actual state directly; do not
  improve a runbook for a task you are currently executing (that belongs to
  the *other* session type); skill edits follow policy.md §5–§6 conventions
  (`last_verified`, decay rules).
- **What "improve" produces**: typically a commit touching policy /
  agentdocs / a `.claude/skills/` runbook / nctl. Advise recording the
  resulting commit SHAs and skill names in `resolution` — that is exactly
  what the namespace is for (discuss_idea1's example shape:
  `{"summary": ..., "skill": ..., "commits": [...]}`).
- **Gotchas section candidates**: no DELETE route; forward-only transitions
  (a premature `resolve` cannot be undone — the episode would need a fresh
  episode to reopen the topic); default `list` filter hides
  resolved/dismissed; `write` replaces the namespace wholesale, so
  read-modify-write if you mean to extend rather than replace.

### The policy.md §4 rewrite

- Keep the *triggering rule* ("end of a session that did non-trivial cluster
  work — always when painful or second-occurrence") verbatim; only the medium
  changes.
- Replace the markdown template with the equivalent `raw_data` guidance: one
  `nctl workflow-episode create --title ... --raw-data '{...}'` example whose
  `report` carries the same fields the old template had (occurred_at, tags,
  outcome per §2, summary, improvised parts, skills used, second-occurrence
  feeling) and whose `references` carries the old "References" bullet list
  (operation IDs, Braindump/desired IDs, session ID). Sub-structure is
  free-form (decision 4) — present it as convention, not schema.
- "The episode directory is the audit unit" → "the WorkflowEpisode ID is the
  audit unit"; the multi-task-per-session / multi-session-per-task point
  still applies (one episode per task).
- The later `review.md` → a later `write <id> assessment` carrying the §2
  attributes and the promotion verdict. §2 and §3 themselves need no change.
- §8's "Retrospective artifacts reference operation IDs; they do not copy
  evidence" already matches the new scheme; check §5/§6 for any stray
  directory mentions but expect no change there.
- Failure handling is one sentence, per decision 6: if `create` fails, report
  it in the session and move on — no offline draft mechanism.

### The README_DEV.md paragraph

Same shape as today (a pointer, not a duplicate): keep pointing at policy.md
for the rules, but the destination sentence becomes "create a WorkflowEpisode
via `nctl workflow-episode create`", and add one sentence that improvement
sessions are the `workflow-improvement` agentdocs session type. Keep the
"don't build runbooks mid-task" sentence.

## Steps

One report + one commit per step (`p3/report_stepN.md`). All commits are in
the root superproject (no submodule involved). Nothing here is live or
hard-to-reverse, so no pause points — but per the standing style, keep steps
small and honest.

### Step 1 — `agentdocs/workflow-improvement/README.md`

The new session-type manual, plus the one-line `agentdocs/README.md`
dispatcher fix (README.txt → README.md). Optionally dry-check the examples
against the live scratch Nautobot (read-only `list`/`show` on the seed
episodes) so the quoted commands are known-good, and say in the report
whether you did.

### Step 2 — policy.md §4 + README_DEV.md + skill citation reword

The normative rewrite, all in one commit so no intermediate state points at
two schemes. Includes the two `retire-proxmox-lxc` SKILL.md citation rewords.

### Step 3 — Verification sweep + phase report

Repo-wide `grep -rn "evidence/workflow-episodes\|selfreport\.md"` (and
similar) excluding `.git`, `.local`, and historical `devdocs/vision/`
records; show in the report that every remaining hit is a historical record,
not a consulted document. Phase report states the exit criterion with the
grep evidence, README_DEV completion language. Remind the user that nctl has
unpushed Phase 2 commits (no new push need arises in this phase, but the
reminder was carried from p2).

## Out of scope for this phase

Running an actual improvement cycle (Phase 4), any nctl/nintent code or GUI
change, importing or deleting `.local/evidence/workflow-episodes/`
directories, rewriting historical devdocs reports, column promotion.
