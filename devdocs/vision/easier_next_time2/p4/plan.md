# Easier Next Time 2 — Phase 4 Plan

Status: planned 2026-08-04. Implements Phase 4 of [`../roadmap.md`](../roadmap.md):
one real improvement cycle end to end, plus a short evaluation.

## What counts as "a real cluster-work session" here

Phases 1-3 built the WorkflowEpisode pipeline but never exercised it against a
real self-report — the two seed episodes referenced in the agentdocs manual
were created as read-only examples while writing the manual, not as genuine
end-of-session self-reports. This Phase 4 session itself is the first session
since the pipeline went live that does non-trivial, non-mechanical
cluster-project work (evaluating/operating the WorkflowEpisode/GUI/nctl/policy
surface it just finished building, making live writes against the scratch
Nautobot, judgment calls about phase scope). Per policy.md §4 ("at the end of
a session that did non-trivial cluster work"), the self-report subject is
**this session's own Phase 4 work**, created at its natural end — this is the
straightforward reading, not a special exemption.

## Steps

One report + one commit per step where a commit is produced (`p4/report_stepN.md`),
per the standing step-by-step style. Steps 2 and 4 touch the live scratch
Nautobot (episode create/select/write/resolve) — not destructive or
external-reaching (per roadmap "Useful facts"), so no extra pause beyond the
one built into the roadmap's own exit criteria (see Step 3).

### Step 1 — do the phase's real work, then self-report

Finish this plan, then whatever Phase 4 evaluation work follows from it
(surveying the live episode list, checking GUI presentation, etc. — folded
into later steps). At the natural end, create the self-report via
`nctl workflow-episode create` per policy.md §4's template, tagged
appropriately (`painful` / `second-occurrence` / `routine`), referencing this
phase's commits.

### Step 2 — survey + select (human step, roadmap-mandated)

The roadmap's exit criterion literally names this as a human action ("have
the human survey the GUI and select one"), distinct from general "ask when
needed" caution — pause here, show the created episode's GUI URL and ID, and
let the user either select it themselves via `nctl workflow-episode select`
or explicitly hand that action back to the agent. Do not skip this by
self-selecting silently — the point of Phase 4 is partly to exercise the GUI
survey step as a human would.

### Step 3 — workflow-improvement session end to end

Once selected, follow `agentdocs/workflow-improvement/README.md`'s standard
loop against the real episode: `nctl session new workflow-improvement --topic
<slug>`, `show --json`, decide whether an improvement is warranted, make the
minimal fix(es) found (GUI presentation / nctl command / protocol wording —
whatever the cycle surfaces), write `resolution`, `resolve`. If nothing
warrants a change, `dismiss` with reasoning recorded first — both are valid
per policy §3.

### Step 4 — evaluation report

`p4/report.md`: what the cycle found, what (if anything) was fixed, and
explicitly whether any column-promotion candidate appeared (raw_data field
that should become a real column) — the roadmap asks this be recorded either
way.

## Out of scope

Migrating the 3 old `.local/evidence/workflow-episodes/` directories (decision
8, unchanged). Building any new mechanism beyond what Phases 1-3 already
shipped — Phase 4 is evaluation-driven fixes only, not new features.
