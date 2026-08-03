# Easier Next Time — Phase 5 Report: Steady State and Review

Date: 2026-08-04. Phase 5 of [`../roadmap.md`](../roadmap.md), executed under
[`../policy.md`](../policy.md). This phase is read-only evaluation over
existing artifacts (no cluster mutation, no skill edits) — no live/hard-to-
reverse action was needed, so it ran in one pass rather than a multi-step
plan, matching the precedent set by Phase 4 (also plan-less).

## 1. Skill catalog inventory

`.claude/skills/` contains exactly **one** skill: `retire-proxmox-lxc`
(`version: 2`).

| check | result |
|---|---|
| staleness | **not stale.** `verified_against.nctl` = `3329d93bf3ebf38d284adedc6aa3653abd210cfc`. `git -C nctl log --oneline 3329d93b..HEAD` returns 0 commits — the submodule has not moved since the last real verified use (Phase 3 Fix 1 Step 5, 2026-08-03). `last_verified: 2026-08-03` is current. |
| duplicates | none — one skill, one workflow. |
| contradictions | none — nothing else documents Proxmox LXC retirement as a skill; `README.md`/`nctl/README.md` are the wrapped source material the skill itself points back to, not a competing procedure. |

With a catalog of one, "inventory" is necessarily thin. Nothing here requires
action; recorded so the next inventory has a baseline to diff against.

## 2. Self-report / tagging convention — tuned from actual use

Three episode directories exist under
`.local/evidence/workflow-episodes/`, all from 2026-08-03:
`20260803_retire-aghaos` (Phase 2 audit source), `20260803_retire-agscratch1`
(Phase 3 blocked attempt), `20260803_retire-agscratch1-real-use` (Phase 3
Fix 1 real use). Comparing what they actually used against the policy §4
template:

- **Tags used:** `[second-occurrence, retroactive]`, `[painful,
  second-occurrence]`, `[second-occurrence]`. `retroactive` is not in the
  policy's documented tag set (`painful | second-occurrence | routine`), but
  it earned its keep — it's the tag that explains *why* a report reads from
  ops evidence instead of a live session, which the audit-selection rule
  ("only sessions tagged painful/second-occurrence get audited") depends on
  being able to tell apart from a live self-report. **Change made:** added
  `retroactive` to policy §4's documented tag set (below), since three-for-
  three real reports needed it and none needed a tag outside these four.
- **Fields actually used every time:** "What was requested and what
  happened", "References" (operation IDs — all three respected prohibition 2,
  none copied evidence bodies), "Skills used", "Second-occurrence feeling".
  All pulled their weight; no change needed.
- **Field used inconsistently:** "Braindump / desired-state IDs touched" —
  the `aghaos` report filled it with raw UUIDs (`desired_node_id=...`,
  `compute_instance_id=...`) since no human-readable slug path existed in the
  evidence at hand; the two `agscratch1` reports used the guest slug and VMID
  instead, which is both more readable and consistent with how the skill
  itself names inputs (`GUEST`, `VMID`, `CONTROL_NODE`). Not a defect — the
  template already says "format free" for this — but worth a one-line
  steer since the slug form proved easier to cross-reference. **Change
  made:** added a one-line note to policy §4 preferring slug/name references
  over raw UUIDs when both are available.
- **Field never exercised:** the `routine` tag — no self-report to date
  described uninteresting, non-recurring work (unsurprising: policy §4 only
  asks for a report when something felt painful or like a second
  occurrence). No change — this is the tag doing its job by absence, not a
  gap.
- **`human_guidance: unknown`** (added during Phase 2 for exactly this
  reason) was exercised once (`aghaos`, transcript unrecoverable) and not
  needed again in the two Phase 3 episodes, where the executing session was
  known. Vocabulary is now confirmed sufficient across all three real uses;
  no further change.

Policy §4's tag line changed from:

```
tags: [painful | second-occurrence | routine]
```

to:

```
tags: [painful | second-occurrence | routine | retroactive]
```

with a one-line addition after the template noting the UUID-vs-slug
preference. See the diff in `policy.md` committed alongside this report.

## 3. Deferred mechanisms — does anything now earn its own roadmap?

Checked each item in roadmap governing decision 6 against what actually
happened since Phase 1:

- **Task cards / `allowed_commands` contracts / workflow routing** — frozen
  "until a small local-model executor actually exists." No such executor
  exists; nothing in Phases 2-4 changed that precondition. **Stays
  deferred.**
- **Small-model replay measurement** — becomes the promotion gate only once
  that executor exists. Same precondition, unmet. **Stays deferred.**
- **`.local` reorganization and storage policy** — explicitly "a separate
  future initiative with its own roadmap." Total footprint to date is three
  episode directories under `.local/evidence/workflow-episodes/`, no
  filename collisions, no storage-scale pain reported in any self-report or
  review. **Stays deferred** — no evidence has accumulated that would justify
  designing it now.
- **Episode schema — the actor/session field gap.** This is the one item
  with a real, recorded pain point: Phase 2's audit (`review.md` calibration
  notes, `audit.md` #3) found that `nctl`'s event log carries no
  actor/session field, making transcript-to-operation correlation
  unexpectedly hard for the one retroactive audit performed. Weighing
  whether this has earned its own roadmap: it has caused friction in exactly
  one of three episodes (the two Phase 3 episodes both had a known executing
  session, since they were self-reported live rather than reconstructed).
  Frequency is low so far, and per policy §3's promotion rule ("automate on
  the second occurrence, never speculatively on the first"), one occurrence
  of this specific pain is not yet enough to justify new logging machinery
  (governing decision 3 also sets a real bar here: "New capture machinery is
  added only after a concrete missing field is identified twice"). **Stays
  deferred, but flagged concretely for Phase 5's successor inventory**: if
  the next retrospective also needs transcript correlation and also can't
  find it cheaply, that is the second occurrence and an operation-id-to-
  session pointer should be designed then.

No deferred mechanism crosses its promotion bar yet. This matches Phase 4's
finding for the nctl-command promotion (no second real occurrence) —
consistent with the roadmap's overall discipline of not building ahead of
evidence.

## Exit criteria check

Per roadmap Phase 5: "a short evaluation report; Easier Next Time continues
as an ongoing practice rather than a roadmap."

- Skill catalog inventoried (staleness/duplicates/contradictions): done, §1.
- Self-report/tagging convention tuned from actual use: done, §2 (one policy
  edit: `retroactive` tag added, UUID-vs-slug note added).
- Deferred-mechanism promotion decided: done, §3 — none promoted; one
  (actor/session field) given a concrete, evidence-based re-check condition
  for next time rather than left as a vague "someday."

**Phase 5 is complete. This closes the Easier Next Time roadmap as written.**
Guidance for what comes next is no longer phase-numbered: keep writing
self-reports per policy §4 (now including `retroactive` where applicable),
keep the `retire-proxmox-lxc` skill's `last_verified` fresh on every real
use, and re-open a scoped piece of this roadmap (not a new phase number) only
when a deferred mechanism's promotion bar is actually crossed — most likely
the actor/session field, next time transcript correlation is needed and
still isn't cheap.
