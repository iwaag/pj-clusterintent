# workflow-planning — agent manual

**workflow-planning** = the process where you (a strong model, this is not
written for a cheap executor) turn a confirmed user request into one plan
artifact conforming to
[`../../devdocs/vision/workflow_agent/plan_contract.md`](../../devdocs/vision/workflow_agent/plan_contract.md),
by investigating repo docs and current cluster state as needed, then hand
that plan artifact off. You may assume repo literacy (`README.md`,
`README_DEV.md`, the skill catalog, `nctl --help`) — this manual does not
repeat that material, only the planning-specific procedure on top of it.

This is not a session type with a human survey step (planning happens inside
a normal user session, the moment a request firms up), not a workflow
catalog, and not the executor document (Phase 2 writes that separately,
quoting the contract's approval-mark rule).

## Rule

- Read
  [`../../devdocs/vision/workflow_agent/plan_contract.md`](../../devdocs/vision/workflow_agent/plan_contract.md)
  in full before writing a plan artifact — this manual assumes it, it does
  not restate the four required sections or the marker syntax.
- Read [`../../devdocs/vision/workflow_agent/discuss_idea1.md`](../../devdocs/vision/workflow_agent/discuss_idea1.md)
  §5–§6 if you want the reasoning behind the procedure below; not required
  for routine planning once you've read it once.

## 1. Input handling

Start from a short confirmed request summary: goal, target, and any
constraint the user actually stated. You may investigate repo docs and
current cluster state as widely as you need — that is the entire point of
putting broad, non-deterministic reasoning on the planning side rather than
the executor side.

If a material ambiguity survives that investigation — the target is
unclear, the goal admits two different end states, a constraint conflicts
with observed reality — **do not resolve it by picking a plausible
reading.** Return "needs confirmation" with the specific question. Guessing
through ambiguity here is exactly the failure mode this protocol exists to
avoid: the executor has no context left to notice you guessed wrong.

## 2. Known-workflow selection

Skill lazy loading is already the workflow router. Before writing any step
from scratch, check: does a `.claude/skills/` runbook, or an `nctl` bounded
command (`reconcile`, `prune`, `desired apply`, `workflow-episode`, `drift`,
`relations`, …), already cover this piece of work?

- **If yes:** the plan step *names* that skill or command and fills in
  *this occasion's* parameters (target slug, VMID, flags). Do not re-derive
  or restate the runbook's internal procedure in the plan — that duplication
  is exactly what a bounded command exists to avoid, and it goes stale the
  moment the runbook changes. Carry forward only what the executor needs to
  see directly in the plan: the runbook's own approval boundaries (as
  `**approval required**` marks, per contract §2) and any stop conditions
  the executor can't infer from the command's own dry-run behavior.
- A skill with `execution_level: 3` (see `easier_next_time/policy.md` if you
  need the level vocabulary) is the strongest signal that a step can just
  name it — that skill has already been verified end to end.

## 3. Unknown-work planning

Not covered by an existing skill or bounded command is normal, not a
rejection condition (discuss_idea1 §5.2 explicitly rejects "no precedent, no
service"). Plan it anyway, following these constraints:

- Keep each step **small and observable**: prefer a read-only probe between
  any two mutating steps, and prefer commands with `--json` output you can
  name concretely in `success evidence` over a step whose result requires
  judgment to interpret.
- Route genuinely irreducible judgment calls to a **stop condition**, not to
  an open-ended step. "Investigate and fix" is not a valid step — if you
  cannot enumerate what "fix" means as a bounded command with its branches
  written out, that decision belongs in `stop conditions` (the executor
  stops and a human or a new planning cycle decides), not inside `steps`.
- A plan built this way does not claim the same reliability as a
  known-workflow plan — do not write `success evidence` or step wording that
  implies more certainty than an unprecedented procedure actually has.

## 4. The approval-mark rule

Full syntax and the hard rule live in the contract (§2) — this section is
the planning-side checklist for applying it:

1. For every step, ask: does this touch the production/external class
   (README_DEV §10.1 — physical nodes, Proxmox, external services, anything
   not disposable), or does its command include `--yes`, `--allow-destroy`,
   or a direct SSH/Ansible mutation?
2. If yes to either, the step gets the exact marker line `**approval
   required**` directly under its heading, before its command.
3. If no, the step's command text must not contain `--yes` or
   `--allow-destroy` — if you find yourself about to write one of those
   flags on an unmarked step, that is a signal the step is misclassified,
   not that the rule has an exception. Add the marker instead.
4. The persistent local scratch environment (README_DEV §10.2,
   `.local/localenv_memo.md`) does not need the marker for its own ordinary
   migrate/restart/rebuild/repopulate operations — those are not the
   policy-gated class the marker exists for.

## 5. Scratch space and storage

Use `nctl session new workflow-planning --topic <slug>` for working notes
while you investigate — same convention as `brainforge` and
`workflow-improvement`. The final plan artifact itself does not live in that
scratch folder: write or move it to
`.local/evidence/workflow-plans/<plan-id>/plan.md` per contract §3
(`<plan-id> = <date>_<slug>`), since that is the path the (future) executor
harness and any WorkflowEpisode `references` entry will expect.

## Standard loop for one planning turn

1. Confirm the request summary (goal, target, constraints) — ask if it's
   thin.
2. `nctl session new workflow-planning --topic <slug>` for scratch space, if
   you expect to accumulate notes before the plan settles.
3. Investigate: relevant devdocs/README sections, `.claude/skills/` catalog,
   `nctl --help` subcommands, current state (`nctl drift --json`, `nctl
   relations --json`, `nctl workflow-episode list --json` for precedent).
4. If a material ambiguity remains after investigating, stop and return
   "needs confirmation" with the specific question — do not proceed to
   writing steps.
5. Write the plan artifact: `goal`, `steps` (naming known workflows where
   they apply, marking approval-gated steps, inlining branches/retries),
   `stop conditions`, `success evidence`. Follow contract §1–§4 exactly.
6. Save it to `.local/evidence/workflow-plans/<plan-id>/plan.md`.
7. Hand the plan artifact off (to the executor, once Phase 2 exists; until
   then, to the user for review). Planning is done — do not execute the plan
   yourself in this same pass; that blurs the phase boundary this protocol
   exists to enforce (roadmap decision 1).

## When to stop and ask instead of deciding

- A material ambiguity in the request survives investigation (§1) — always
  "needs confirmation," never a guessed interpretation.
- A step would need `--yes`/`--allow-destroy` but you're not sure it should
  be in this plan at all (e.g. the target's current state is unclear) —
  resolve the target's state first (a read-only step), don't write the
  destructive step speculatively.
- The request implies unknown-work planning (§3) but you cannot make the
  steps small/observable no matter how you decompose it — that is itself a
  signal to return "needs confirmation" describing what's missing (usually:
  what does success look like for this request, concretely), rather than
  writing a vague plan and hoping the executor improvises.

## Known gotchas

- Naming a skill/command in a step is not the same as inlining its
  internals — if you catch yourself copying a runbook's command sequence
  into the plan wholesale, stop and just name the runbook instead; the
  duplication will drift out of sync with the runbook the next time it
  changes.
- The marker is a literal string match (`**approval required**`), not a
  concept — a step that says "this needs approval" in prose without that
  exact line does not satisfy the hard rule and will not be caught by
  Phase 2's grep-based check.
- `.local/evidence/workflow-plans/<plan-id>/` legitimately holds only
  `plan.md` until an executor runs it (Phase 2) — do not fabricate a
  `transcript.*` or `report.md` to make a plan look executed.
