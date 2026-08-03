# Easier Next Time — Phase 2 Report

## Step 0 — Pick the episode

Confirmed via `nctl ops show` on all six candidate operation IDs from
`plan.md`. They form one coherent task: retiring LXC guest `aghaos` (vmid 102,
host `aghub`).

- `01KZ2ZE44M3G766FN298HXCRJ8` — reconcile plan, `manual_review` errors
  (`no_realized_object`, `actual_node_not_linked`)
- `01KZ2ZEBM0NX40QBP7232D75EQ` — reconcile plan, clean, zero actions
- `01KZ304NKDWG8N6W3XYM70D15Y` — reconcile plan, one `destroy_compute_instance`
  action targeting vmid 102
- `01KZ304R6VX1FGJZCXQ37M6X3W` — reconcile **converged**; `plan.json` shows the
  same action, `result.json`/round artifacts show the destroy actuated and a
  fresh drift confirming completion
- `01KZ30EQY8HZT5K3TSDPZ5XD2B` — prune plan, `eligibility.json` → `eligible`
- `01KZ30FRTGF808QSK8SC2M8QCE` — prune **pruned**; Actual + Desired ledger
  records for `aghaos` deleted

No fallback needed — Step 0's live-action fallback did not apply.

## Step 1 — Retroactive self-report

Written to
`.local/evidence/workflow-episodes/20260803_retire-aghaos/selfreport.md`
(git-ignored, per policy §4/§8).

Notable finding while writing it: the session transcript for this episode
could not be conclusively located. Grepping `~/.claude/projects/.../*.jsonl`
for `aghaos` matches dozens of unrelated files (it's a recurring scratch guest
name across this project's history), and grepping for the six operation IDs
only turned up the *planning* session for this very Phase 2 plan (which
quoted them as reference text) — not an execution session. The one session
whose timestamp window overlaps the operations exactly
(`8ac022b6-ec47-4838-a182-9df8e8e018bb`, `devdocs/small/vm_retire` — the
implementation session that added VM-destroy support to `nctl`) only reads
code and runs `pytest`; it never calls `nctl reconcile`/`prune` on real data.
`nctl`'s operation event log records no actor/invoker field either. Per the
plan's explicit fallback ("if the transcript can't be located, say so and
audit from ops evidence alone"), the audit proceeds on ops evidence plus the
documented runbook in `README.md`, not transcript archaeology.

## Step 2 — Audit

Written to `.local/evidence/workflow-episodes/20260803_retire-aghaos/audit.md`
(git-ignored). Cross-referenced every operation's `plan.json`/`result.json`/
`eligibility.json`/`desired-operations.json`/`actual-plan.json` against
`README.md`'s "Retiring one Proxmox LXC" procedure. Findings, classified per
policy §1 component-by-component (full table in `audit.md`):

- Declaring the desired-state batch (`lifecycle=retired` +
  `desired_presence=absent`) and interpreting the first reconcile's
  `manual_review` errors are genuine Level 2 reasoning — no runbook currently
  enumerates what those error codes mean or how to resolve them.
- The destroy actuation and prune are already Level 4 — `nctl` owns the
  validation, the two-flag destroy gate, actuation, fresh observation, and the
  prune eligibility check.
- Two failure/near-miss points: the first reconcile plan errored before the
  desired-state was in a realizable shape (fixed within 7 seconds, but the fix
  itself isn't visible in any evidence), and there was only a 3-second gap
  between the destructive dry plan and the actual `--allow-destroy --yes` run
  — too short for the "review the unchanged plan" step README describes to
  have been a fresh read, suggesting the written safety step and the observed
  practice diverge.
- A systemic (not task) gap: `nctl`'s event log carries no actor/session
  field, which is exactly what made this audit's transcript search hard.
  Flagged as a Phase 5 input, not fixed here (roadmap decision 6 defers
  `.local`/episode-schema work).

## Step 3 — review.md and verdict

Written to
`.local/evidence/workflow-episodes/20260803_retire-aghaos/review.md`.

**Verdict: promote.** Wrap the retirement workflow (desired-state declaration
→ dry reconcile → manual_review handling → `--allow-destroy --yes` → converged
check → dry prune → `prune --yes`) in one Level 3 skill. Reasoning
(frequency × failure impact × reasoning burden): the workflow is already
recognized as recurring (README documents it by name, self-report tagged
second-occurrence), the destructive core is already safely bounded at Level 4
by nctl, and the remaining reasoning burden (field declaration, error-code
interpretation, step sequencing) is concrete and enumerable — exactly what a
Level 3 skill captures, and exactly what policy §3's target-level rule
("automate on the second occurrence") licenses here. This hands Phase 3 its
runbook directly, per the plan's first suggested shape.

`target_level = 3` for the orchestration; the destroy/prune core needs no
promotion (already 4). `human_guidance` was recorded as `unknown` rather than
guessed, since the transcript that would show whether a human explicitly
approved the destructive step could not be located.

## Step 4 — Phase report / policy adjustment

One policy format needed a small fix, made in this commit: §2's
`human_guidance` vocabulary (`none`/`approval_only`/`judgment_required`) had
no value for "the transcript needed to know this is unrecoverable" — a real
case for a retroactive audit like this one. Added `unknown` with a note not to
guess. Everything else in the policy (level definitions, self-report
template, attribute table shape) worked as written; no other adjustment was
needed.

**Phase 2 exit criteria met:**

1. One episode directory:
   `.local/evidence/workflow-episodes/20260803_retire-aghaos/` containing
   `selfreport.md`, `audit.md`, and `review.md`.
2. `review.md` records the §2 attributes and an explicit verdict (promote to
   Level 3, reason given).
3. This report states what was decided and why.

Phase 2 is complete. Next is Phase 3: convert this verdict into one Level 3
skill wrapping the `nctl reconcile`/`nctl prune` commands for LXC retirement,
then use it on a real later occurrence.
