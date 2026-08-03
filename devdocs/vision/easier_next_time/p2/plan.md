# Easier Next Time — Phase 2 Plan: First Retrospective

Date: 2026-08-03. Phase 2 of [`../roadmap.md`](../roadmap.md), executed under
[`../policy.md`](../policy.md).

## Goal

Run the retrospective loop once on real material: take one real episode, write
its self-report (retroactively if needed), audit it against transcript +
`nctl ops` evidence, and produce the first `review.md` with an explicit
verdict — "promote to level N because …" or "stays at level N because …".
Both verdicts complete the phase.

## Exit criteria (fixed by the roadmap)

1. One episode directory under `.local/evidence/workflow-episodes/<date>_<task>/`
   containing `selfreport.md` and `review.md`.
2. `review.md` records the §2 attributes (`level`, `human_guidance`,
   `execution_mode`, `outcome`, `target_level` + reason) and an explicit
   promote/stay verdict.
3. A `p2/report.md` stating what was decided and why, with completion language
   per README_DEV.

## Facts found during planning (use these, don't re-derive)

- `.local/evidence/workflow-episodes/` is **empty** — no tagged episode exists,
  so Phase 2 uses the roadmap's second option: pick a real task that already
  happened and self-report it retroactively, or run one deliberately.
- **Strong candidate already exists.** On the morning of 2026-08-03 a real
  guest-retirement task ran with full operation evidence:
  - `01KZ2ZE44M3G766FN298HXCRJ8` / `01KZ2ZEBM0NX40QBP7232D75EQ` — reconcile, planned
  - `01KZ304NKDWG8N6W3XYM70D15Y` — reconcile, planned
  - `01KZ304R6VX1FGJZCXQ37M6X3W` — reconcile, **converged**
  - `01KZ30EQY8HZT5K3TSDPZ5XD2B` — prune, planned
  - `01KZ30FRTGF808QSK8SC2M8QCE` — prune, **pruned**

  This looks like the documented "LXC guest retirement + prune" workflow (a
  named first-runbook candidate in the roadmap) executed end to end the same
  day. Auditing it retroactively satisfies time separation (§7): the operation
  happened in an earlier session, the retrospective happens now.
- Alternative material if the above turns out thin: the three **failed**
  `apply dnsmasq` operations of 2026-07-14 (`01KXGQ...`) are a real
  pain/improvisation episode; or deliberately run
  `nctl reconcile agpc --refresh-observation` (agpc.local and agstudio.local
  are reachable; agbach/agdnsmasq are known-down — don't pick those).
- Evidence access: `uv run --project nctl nctl ops show <ID>`; raw artifacts
  under `~/.local/state/nctl/events/<operation_id>/` (406 operations exist).
- Session transcripts: 167 `*.jsonl` files in
  `~/.claude/projects/-Users-eiji-projects-pj-clusterintent/`. To find the
  session for an operation, grep the transcripts for the operation ID or the
  guest name; file mtimes near the operation timestamps narrow it fast.
  Transcripts are large — extract with `jq`/`grep`, don't read whole files.
- The retirement workflow's authoritative written form is README.md
  §"Retiring one Proxmox LXC". The audit's job includes comparing what the
  transcript shows the agent actually did against that text: deviations,
  re-derivations, and judgment calls are exactly the "reasoning burden" the
  level measures.

## Steps

Run step-by-step in the established style: one short progress note per step in
`p2/report.md` (append as you go), commit per step where a commit makes sense.
Everything here is documentation and `.local` artifacts — no cluster mutation
is required unless Step 1's fallback is taken.

### Step 0 — Pick the episode

Confirm via `nctl ops show` that the 2026-08-03 reconcile/prune chain is one
coherent task (same guest, plan→apply→prune). If yes, that's the episode. If
it's fragmentary, fall back to the dnsmasq-failure episode or run a fresh
single-node reconcile (that fallback is a live cluster action — pause and get
user approval first, per the phase-execution convention).

### Step 1 — Write the retroactive self-report

Create `.local/evidence/workflow-episodes/20260803_<task-slug>/selfreport.md`
using the policy §4 template. Because it is retroactive, fill it from the
transcript + ops evidence rather than memory, and say so in the report ("tags:
[second-occurrence]" is likely right — guest retirement has happened before in
this project's history). Reference operation IDs only; copy no evidence bodies.

### Step 2 — Audit

Read the located transcript segment and the operation evidence. Answer
concretely:

- What did the executor actually decide vs. mechanically execute? (level per
  policy §1 — the retirement itself may be Level 4 via `nctl reconcile
  --allow-destroy`, while the surrounding steps — confirming the wish, editing
  desired-state.yaml, choosing prune timing — may be Level 2. Classify per
  task component, not the whole conversation.)
- Which prohibitions/stop conditions did the executor have to remember
  unaided? (e.g. `--yes` refuses destroy without `--allow-destroy`; prune only
  after reviewing converged state)
- What failure points or near-misses appear in the evidence?
- What would a runbook have to encode for a weaker executor to do this safely?

Keep notes in the episode directory (any format — implementer's choice).

### Step 3 — Write review.md and the verdict

`review.md` beside the self-report, format free but it must contain the §2
attribute table and the verdict. Likely shapes of the verdict (decide from
evidence, not from this list):

- "Core destroy/prune is already Level 4 (nctl owns it); the surrounding
  orchestration stays Level 2; promote the **whole retirement workflow** to a
  Level 3 skill wrapping the nctl commands" — this would hand Phase 3 its
  runbook directly; or
- "Stays as-is because the nctl commands already carry the safety burden and
  the surrounding judgment is genuinely per-request" — equally valid; Phase 3
  then takes the best candidate from the roadmap list instead.

State the reason in terms of frequency × failure impact × reasoning burden.

### Step 4 — Phase report

Finalize `p2/report.md`: episode chosen and why, audit findings, verdict,
which policy formats worked and which needed adjustment (if the §4 template
was awkward, adjust `policy.md` in the same commit and note it — Phase 1
explicitly left the formats to be fixed by use). Update the memory index per
usual practice.

## Prohibitions (complete list — everything else is your call)

1. No secrets/tokens/private keys in Git-tracked files. The episode directory
   is under ignored `.local/` — review artifacts stay there; only `p2/plan.md`,
   `p2/report.md`, and any `policy.md` tweak are committed.
2. Reference operation IDs; do not copy evidence bodies into artifacts.
3. No level/outcome/completion claim the evidence doesn't show.
4. Do not create or edit any `.claude/skills/` runbook in this phase — that is
   Phase 3, and time separation (§7) applies.
5. If the Step 0 fallback requires a live cluster run, pause for user approval
   before executing it.

## Advice

- The first review's value is calibration, not throughput. Where policy §1's
  level definitions feel ambiguous against real evidence, write the ambiguity
  down in `review.md` — that observation is a Phase 5 input.
- Don't over-invest in transcript archaeology. The ops evidence is structured
  and cheap; use the transcript only for what ops evidence can't show
  (judgment calls, improvisation, near-misses). An hour of grep beats a day of
  reading.
- `nctl ops show` output plus the raw `<events.log_dir>/<operation_id>/`
  artifacts (plan, drift, events) are usually enough to reconstruct what was
  planned vs. executed without any transcript at all.
- If the transcript for the episode can't be located, say so in the
  self-report and audit from ops evidence alone — a thinner but honest review
  still completes the phase.
