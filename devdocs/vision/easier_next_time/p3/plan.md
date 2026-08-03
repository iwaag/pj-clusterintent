# Easier Next Time — Phase 3 Plan: First Runbook Skill

Date: 2026-08-03. Phase 3 of [`../roadmap.md`](../roadmap.md), executed under
[`../policy.md`](../policy.md). Input: the Phase 2 verdict
(`p2/report.md`, `.local/evidence/workflow-episodes/20260803_retire-aghaos/review.md`).

## Goal

Convert the Phase 2 verdict — **promote LXC guest retirement to Level 3** —
into one runbook skill in Git, then use it on a real retirement in a later
session and record whether it actually reduced improvisation.

## Exit criteria (fixed by the roadmap)

1. One skill at `.claude/skills/<workflow-id>/SKILL.md` with valid policy §5
   frontmatter, committed.
2. One recorded real use in a later session (self-report per policy §4 states
   whether the skill helped).
3. `last_verified` and `verified_against` set from that use, not from authoring.
4. `p3/report.md` with completion language per README_DEV.

## Facts found during planning (use these, don't re-derive)

- **`.claude/skills/` does not exist yet.** This skill is the first; whatever
  you create becomes the de-facto layout precedent. A `SKILL.md` with `name:`
  and `description:` frontmatter is picked up automatically; the description is
  the only part always in context — one specific sentence.
- **The workflow is already written down twice**, and the skill should
  supersede neither — it wraps them for an executor:
  - `README.md` §"Retiring one Proxmox LXC" (line ~109) — the contract-level
    description;
  - `nctl/README.md` §"Retiring one Proxmox LXC" (line ~749) — the operational
    detail, including the **minimal canonical retirement batch** (two partial
    upserts: `desired_node.lifecycle=retired` +
    `desired_compute_instance.desired_presence=absent`) and the exact review
    fields for the destroy action (`reconciler_id: destroy_compute_instance`,
    `evidence.vmid`, `evidence.control_desired_node_slug`).
- **What the skill must add** (the three Level 2 reasoning points from the
  audit, `audit.md` §"What a Level 3 runbook would need to encode"):
  1. Typed input: the guest slug (plus the expected VMID and control node for
     the checkpoint). Everything else derives from it.
  2. Fixed step order: declare batch (dry, then `--yes`) → dry
     `reconcile GUEST --allow-destroy --json` → **if `manual_review` errors,
     stop and consult the enumerated table** → checkpoint: confirm the single
     planned `destroy_compute_instance` targets the expected vmid/host →
     `reconcile GUEST --allow-destroy --yes` → confirm converged and a repeat
     dry reconcile plans zero actions → dry `prune GUEST` → eligibility
     `eligible` → `prune GUEST --yes`.
  3. Enumerated `manual_review` branch table. The episode produced two codes
     (`no_realized_object`, `actual_node_not_linked` — root cause: desired
     state not yet in realizable shape). Error codes live in
     `nctl/src/nctl_core/reconcile/classify.py` — skim it and enumerate the
     codes plausible for a retirement; for everything else the branch is
     "stop, return to a capable model/human" (`manual_intervention_required`,
     policy §5). Do not try to enumerate all of nctl.
- **Machine-checkable success evidence** (from audit.md): final reconcile
  state `converged`, repeat dry-reconcile action count `0`, prune state
  `pruned`. All three are visible in `--json` output / `nctl ops show`.
- **The 3-second-gap finding** (review.md calibration notes): in the audited
  episode the destructive dry plan and the `--yes` run were 3 seconds apart,
  so the written "review the unchanged plan" step was not a real fresh read.
  Encode the review as an explicit checkpoint with named fields to compare
  (vmid, slug, control node), not as a prose admonition — that is the whole
  point of promoting this to Level 3.
- Frontmatter fields per policy §5: `name`, `description`, `version`,
  `execution_level: 3`, `triggers`, `risk`, `prerequisites`, `last_verified`,
  `verified_against`. Get the nctl SHA at use time with
  `git -C nctl rev-parse HEAD`. On first commit, `last_verified` is unset (or
  explicitly marked unverified) — it is set from the first real use, and
  claiming otherwise violates policy §8.3.
- Commands run from repo root as `uv run --project nctl nctl …`.
- **A real use needs a real guest to retire.** None is currently requested. Two
  legitimate paths, implementer's choice at Step 2: wait for a natural
  retirement request, or deliberately create a scratch LXC (the documented
  creation workflow in `nctl/README.md` §"Canonical desired-state batch") and
  retire it with the skill. The cluster is experimental; a scratch
  create-then-retire is a *real* use, not a simulation — the skill neither
  knows nor cares why the guest is being retired.

## Steps

Step-by-step in the established style: progress notes appended to
`p3/report.md`, one commit per step where sensible. Steps 0–1 are pure Git
work. Step 2 touches the live cluster — pause for user approval before any
apply, per the phase-execution convention.

### Step 0 — Author the skill

Create `.claude/skills/<workflow-id>/SKILL.md` (suggested id:
`retire-proxmox-lxc`, your call). Body content per policy §5: typed inputs,
exact permitted commands, fixed step order, enumerated branches (the
`manual_review` table), prohibitions, stop conditions, success evidence — all
concrete material is in the facts above. Keep it executable-by-a-weaker-model
terse: numbered steps with exact commands and expected outputs beat prose.
Embed the two-upsert retirement YAML with the slug as the only placeholder.
Commit.

### Step 1 — Static verification

Verify the skill is picked up: a fresh session (or `/skills`-equivalent
listing) shows the name + description. Read the body once as if you were the
executor and fix anything that requires outside knowledge that isn't either in
the body or an explicit stop condition. No live commands. Commit fixes if any.

### Step 2 — Real use in a later session (live, needs approval)

Time separation (§7): this must be a **different session** from Steps 0–1. In
that session, invoke the skill against a real retirement target (natural
request or scratch guest, see facts). Follow the skill as written — where it
is wrong or incomplete, prefer stopping and noting the gap over silently
improvising past it; the gaps are the measurement. Write the policy §4
self-report to `.local/evidence/workflow-episodes/<date>_<slug>/`, explicitly
answering: did the skill reduce improvisation relative to the audited episode?

### Step 3 — Verify, refresh, report

Back in an improvement session: check the use's operation evidence shows the
success criteria, set `last_verified` + `verified_against` from the use, apply
any body fixes the self-report identified (this is the skill's first
use-driven revision — bump `version` if the fix changes executor behavior).
Finalize `p3/report.md`; update the memory index.

## Prohibitions (complete list — everything else is your call)

1. No secrets/tokens/private keys in the skill or any Git-tracked file;
   cluster-private values stay parameterized or in `.local`.
2. Self-report references operation IDs; no copied evidence bodies.
3. No `last_verified`, level, or completion claim the evidence doesn't show —
   in particular, authoring alone never sets `last_verified`.
4. Steps 0–1 and Step 2 happen in different sessions (§7); the Step 2 executor
   does not edit the skill mid-use.
5. Step 2's applies (`desired apply --yes`, `--allow-destroy --yes`,
   `prune --yes`, and any scratch-guest creation) pause for user approval
   first.

## Advice

- Resist scope growth. One workflow, one skill. The creation workflow, SSH
  enrollment recovery, etc. are future skills — mention them nowhere.
- The skill body may link to `nctl/README.md` sections for background, but the
  executor-critical material (commands, order, checkpoint fields, branch
  table) must be *in* the body — a Level 3 executor should not need to read
  and interpret a 800-line README; that reading is the Level 2 burden being
  eliminated.
- Write the checkpoint as a fill-in: "planned vmid = ___, expected vmid = ___,
  equal? proceed / stop" — this makes the review a recorded act rather than a
  3-second rubber stamp, directly addressing the audit's near-miss #2.
- For `risk`, this is destructive but scoped to one declared guest on an
  experimental cluster; something like `destructive_scoped` is fine — the
  vocabulary in policy §5 is an example list, not closed.
- If Step 2 ends in a safe stop (e.g. an unenumerated `manual_review` code),
  that is still a recorded real use per policy §2 — report it honestly and
  decide in Step 3 whether the fix is a body edit or a "stays as documented
  stop" note. It does not fail the phase.
- The Phase 2 finding that nctl's event log has no actor/session field stays
  parked for Phase 5 — do not fix it here.
