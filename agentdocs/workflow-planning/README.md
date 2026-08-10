# workflow-planning — agent manual

**workflow-planning** = turning a confirmed user request into one plan
artifact conforming to
[`../../devdocs/vision/workflow_agent/plan_contract.md`](../../devdocs/vision/workflow_agent/plan_contract.md),
then handing that artifact off. It happens inside a normal user session, the
moment a request firms up — there is no human survey step, no workflow
catalog, and the executor document is written separately in Phase 2.

- [`plan_contract.md`](../../devdocs/vision/workflow_agent/plan_contract.md) —
  the four required sections and the marker syntax. This manual does not
  restate them.
- [`discuss_idea1.md`](../../devdocs/vision/workflow_agent/discuss_idea1.md)
  §5–§6 — the reasoning behind the procedure below.
- Repo literacy is assumed: `README.md`, `README_DEV.md`, the skill catalog,
  `nctl --help`.

## 1. Input

A short confirmed request summary: goal, target, and any constraint the user
actually stated. Repo docs and current cluster state are both open to
investigate as widely as useful — broad non-deterministic reasoning belongs on
the planning side rather than the executor side.

A material ambiguity that survives investigation (the target is unclear, the
goal admits two different end states, a constraint conflicts with observed
reality) can be returned as "needs confirmation" with the specific question.
The executor has no context left to notice a guess that turned out wrong.

## 2. Known-workflow selection

Skill lazy loading is already the workflow router. A `.claude/skills/` runbook
or an `nctl` bounded command (`reconcile`, `prune`, `desired apply`,
`workflow-episode`, `drift`, `relations`, …) may already cover a piece of the
work.

- Where one does, a plan step can just *name* it and fill in this occasion's
  parameters (target slug, VMID, flags). A restated runbook procedure goes
  stale the moment the runbook changes; what the executor needs in the plan
  itself is the runbook's approval boundaries (as `**approval required**`
  marks, contract §2) and stop conditions it cannot infer from the command's
  own dry-run behaviour.
- `execution_level: 3` on a skill (level vocabulary in
  `easier_next_time/policy.md`) means it has been verified end to end.

## 3. Unknown work

Not covered by an existing skill or bounded command is normal, not a rejection
condition (discuss_idea1 §5.2 rejects "no precedent, no service" explicitly).

- Small, observable steps carry further than large ones: a read-only probe
  between two mutating steps, and `--json` output nameable in
  `success evidence`, beat a step whose result needs interpretation.
- "Investigate and fix" is not enumerable as a bounded command with written
  branches; that shape of decision is what `stop conditions` is for.
- A plan built without precedent does not carry the reliability of a
  known-workflow plan, and its `success evidence` wording is the place that
  shows.

## 4. The approval mark

Full syntax and the hard rule are in contract §2. Planning-side:

- A step touching the production/external class (README_DEV "Environment
  classes" class 1 — physical nodes, Proxmox, external services, anything not
  disposable), or whose command includes `--yes`, `--allow-destroy`, or a
  direct SSH/Ansible mutation, carries the exact line `**approval required**`
  directly under its heading, before its command.
- The marker is a literal string match consumed by Phase 2's grep-based
  check. Prose saying a step needs approval does not satisfy it.
- The persistent local scratch environment (README_DEV "Environment classes"
  class 2, `.local/localenv_memo.md`) is outside the gated class for its own
  ordinary migrate/restart/rebuild/repopulate operations.

## 5. Scratch space and storage

- `nctl session new workflow-planning --topic <slug>` — working notes while
  investigating, same convention as `brainforge` and `workflow-improvement`.
- `.local/evidence/workflow-plans/<plan-id>/plan.md` (`<plan-id> =
  <date>_<slug>`, contract §3) — where the finished artifact lives. This is
  the path the future executor harness and any `WorkflowEpisode` `references`
  entry expect; the scratch folder is not.

## Standard loop for one planning turn

1. Confirm the request summary (goal, target, constraints).
2. `nctl session new workflow-planning --topic <slug>` for scratch space.
3. Investigate: devdocs/README sections, the `.claude/skills/` catalog, `nctl
   --help`, current state (`nctl drift --json`, `nctl relations --json`,
   `nctl workflow-episode list --json` for precedent).
4. Write the plan artifact: `goal`, `steps` (naming known workflows, marking
   approval-gated steps, inlining branches/retries), `stop conditions`,
   `success evidence`, per contract §1–§4.
5. Save to `.local/evidence/workflow-plans/<plan-id>/plan.md`.
6. Hand it off — to the executor once Phase 2 exists, to the user until then.
   Executing the plan in the same pass blurs the phase boundary this protocol
   exists to draw (roadmap decision 1).

## Known gotchas

- `.local/evidence/workflow-plans/<plan-id>/` legitimately holds only
  `plan.md` until an executor runs it (Phase 2); a `transcript.*` or
  `report.md` there means something actually ran.
