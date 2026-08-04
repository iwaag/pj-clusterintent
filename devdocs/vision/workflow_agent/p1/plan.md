# Workflow Agent — Phase 1 Plan

Status: planned 2026-08-04. Implements Phase 1 of [`../roadmap.md`](../roadmap.md):
freeze the plan artifact contract + storage convention, write the planner
manual in agentdocs, author one real example plan by following that manual,
and amend `discuss_idea1.md`. **Documentation-only phase — no code, no
deploy, no live or hard-to-reverse step, no test suite to run.** The only new
software in this roadmap (the executor harness) is Phase 2.

## Goal and exit criteria

1. The plan artifact contract (roadmap decision 3) and the storage convention
   (decision 6) exist as one frozen written document that Phase 2's harness
   and the planner manual can both consume without further negotiation.
2. A planner manual exists in `agentdocs/`, covering: input handling (short
   request summary; return "needs confirmation" instead of guessing through
   ambiguity), known-workflow selection via skills / `nctl` bounded commands,
   unknown-work planning, and the approval-mark rule.
3. One real example plan artifact exists, produced by *actually following the
   manual* on a real (benign) request — not written freehand to look like an
   example.
4. `discuss_idea1.md` carries its two amendments: §6.4's dedicated comparison
   evaluation replaced by continuous WorkflowEpisode evaluation, and the
   `--yes`/`--allow-destroy` rule added to §6.2.

Exit (fixed by the roadmap): contract and manual exist, one example plan
artifact produced by actually following the manual, discuss_idea1 amended.

## Fixed constraints (everything else is implementer's discretion)

The roadmap's three standing prohibitions, applied to what this phase writes:

1. No secrets, tokens, or private payloads in the contract, manual, example
   plan, or any Git-tracked file. Cluster hostnames and operation IDs are
   fine (they appear throughout devdocs already); token values and private
   prose are not.
2. The contract must state the one hard rule verbatim: **a step without
   `approval required` must not contain `--yes` or `--allow-destroy`**. The
   manual must teach it; the example plan must satisfy it.
3. Do not claim completion the evidence does not show (README_DEV completion
   language). In particular, the example plan counts only if the report shows
   it was produced by walking the manual's procedure.

Not constraints (explicitly free): file naming, section wording, marker
syntax details, manual structure, how much of the example to inline where.
No backward compatibility (decision 8) — there is no old contract to
preserve; nothing existing consumes any of these files yet.

## Verified facts (checked 2026-08-04 while planning)

- **`devdocs/vision/workflow_agent/p1/` exists and is empty** — this plan is
  its first file.
- **agentdocs layout**: `agentdocs/README.md` is a 5-line dispatcher ("when
  asked to perform specific task, read `agentdocs/[task_name]/README.md`");
  the two existing session types are `brainforge/README.md` and
  `workflow-improvement/README.md`. The workflow-improvement manual is the
  freshest structural precedent (rules table → prohibitions → scratch area →
  standard loop → key commands → when to stop and ask → known gotchas).
- **`nctl session new <task_name> --topic <slug>` accepts any task name**
  (regex-validated only, not checked against an enum or the agentdocs
  directory — verified during easier_next_time2 p3 planning, same nctl
  version). So `nctl session new workflow-planning --topic <slug>` works the
  moment the manual exists, if you want per-plan scratch space; nothing in
  nctl needs to change.
- **`.local` is Git-ignored** and `.local/evidence/` already holds the
  operation-evidence pattern the roadmap's suggested storage mirrors
  (`.local/evidence/workflow-plans/<plan-id>/`). No prior
  `workflow-plans/` directory exists; create it when the example plan is
  authored.
- **Deterministic outputs available for `success evidence` sections** (quote
  these in the manual as the preferred evidence vocabulary): `nctl drift
  --json`, `nctl relations --json`, `nctl ops list` / `nctl ops show
  OPERATION_ID`, `nctl workflow-episode show <id> --json`. All run from the
  repo root via `uv run --project nctl nctl ...`.
- **Known cluster state for picking the example target**: `agpc.local` and
  `agstudio.local` are reachable; `agbach.local` / `agdnsmasq.local` are
  known-unresponsive and that is accepted state (`.local/localenv_memo.md`).
  Read-only diagnostics (`drift`, `relations`, ops inspection) or the local
  scratch Nautobot stack are the safe example domains — the roadmap's "first
  targets" guidance.
- **WorkflowEpisode linkage** (decision 5): the episode `references`
  namespace is free-form JSON, so carrying a plan ID needs no schema change —
  just a documented convention key (e.g. `"workflow_plan_id":
  "2026-08-04_drift-check"`). Phase 1 only has to *state* the convention in
  the contract or manual; actually creating episodes with it is Phase 3.
- **discuss_idea1.md is a dated discussion record** (in Japanese). The
  roadmap explicitly orders the two amendments, so amending it is correct —
  but amend visibly (a dated amendment note in each affected section, or a
  short "Amendments (2026-08-XX)" block) rather than silently rewriting the
  2026-08-04 text, consistent with how this repo treats historical records.

## Design hints (advice, not requirements)

### The contract document

- **Make it one short standalone file, separate from the manual.** The
  contract is the shared surface (roadmap: "freeze its contract first");
  Phase 2's executor rule prompt will want to quote or embed it without
  dragging planner-side guidance along. A natural home is
  `agentdocs/workflow-plan-contract.md` (agent-consulted, next to the
  manuals) or `devdocs/vision/workflow_agent/plan_contract.md` — pick one and
  have the manual link it.
- **Required sections, exactly four** (decision 3): `goal`, `steps` (with
  enumerated branches and bounded retries inline), `stop conditions`,
  `success evidence`. Plus the `approval required` mark on policy-gated
  steps. Keep everything else — machine-checkable expected outputs, workflow
  ID mentions, risk notes — explicitly *recommended, not required*; the
  discussion (§4.2) rejected a fat schema for v1.
- **Fix the marker syntax now, machine-checkably.** Phase 2 will want to
  lint "no `--yes`/`--allow-destroy` outside an approval-marked step" with a
  grep, not a judgment call. A concrete literal like a line-leading
  `**approval required**` (or `[approval required]`) on the step is enough —
  choose one form, show it in the contract's example, forbid paraphrases.
- **Storage convention** (decision 6): `.local/evidence/workflow-plans/
  <plan-id>/` with `plan.md`, `transcript.*`, `report.md`;
  `<plan-id> = <date>_<slug>`. State that the plan ID (never a path) is what
  goes into WorkflowEpisode `references`, and that bodies are never copied
  into `raw_data`. Transcript and report files won't exist until Phase 2 —
  say the directory may legitimately hold only `plan.md` until a run happens.
- Include one complete minimal plan example inline in the contract (can be a
  trimmed version of the Step 3 real example). A contract without a
  known-good instance invites drift immediately.

### The planner manual (`agentdocs/workflow-planning/README.md`, name free)

- **Audience is the strong model, not the cheap executor** — the opposite of
  the workflow-improvement manual. It can assume repo literacy (README.md,
  README_DEV.md, skill catalog) and should say so, but keep the procedure
  itself short and imperative like the brainforge/workflow-improvement
  precedents. Register the new directory in no dispatcher — `agentdocs/
  README.md`'s generic "read `agentdocs/[task_name]/README.md`" already
  covers it.
- **Input handling** (§6.1): start from a short confirmed request summary
  (goal, target, user-stated constraints). The planner may investigate repo
  docs and current state freely — that is the whole point of putting wide
  context on this side. If a material ambiguity survives investigation,
  return "needs confirmation" with the specific question; never resolve
  ambiguity by picking a plausible reading inside the plan.
- **Known-workflow selection**: skill lazy loading is already the router
  (roadmap fact). The procedure is: does a `.claude/skills/` runbook or an
  `nctl` bounded command (`reconcile`, `prune`, `workflow-episode`, …) cover
  this? If yes, the plan step *names* it and fills in this occasion's
  parameters — the plan does not re-derive the runbook's internals. Carry
  the runbook's own prohibitions/approval boundaries into the plan only to
  the extent the executor needs to see them (approval marks, stop
  conditions).
- **Unknown-work planning**: allowed and normal (§5.2 — the agreement
  explicitly rejects "no precedent, no service"). The manual should tell the
  planner to keep unknown-work steps *small and observable* (prefer
  read-only probes between mutations, prefer `--json` outputs it can name in
  `success evidence`), and to route genuinely irreducible judgment to a stop
  condition rather than an open-ended step like "investigate and fix".
- **The approval-mark rule** gets its own short section: which operations
  existing policy gates (external/destructive targets — the
  production/external class in README_DEV §10; `reconcile --yes`,
  `--allow-destroy`, `prune --yes`, direct SSH mutations), the exact marker
  syntax from the contract, and the hard rule about `--yes`/
  `--allow-destroy` never appearing unmarked.
- **Scratch space**: reusing `nctl session new workflow-planning --topic
  <slug>` costs nothing and matches the two existing manuals; the final
  `plan.md` then moves/copies to `.local/evidence/workflow-plans/<plan-id>/`.
  Equally fine: write the plan straight into the evidence directory. Pick
  one and write it down.
- **What the manual is not**: not a session type with a human survey step
  (planning happens inside a normal user session when a request firms up),
  not a workflow catalog, not an executor document. One sentence each on the
  first and last avoids future confusion.

### The example plan (Step 3)

- Pick a real, benign request in the roadmap's first-target class. Good
  candidates: "produce a current cluster convergence assessment" (`drift` +
  `relations` + inspecting the latest ops evidence, pure read-only), or a
  scratch-stack task like a read-only workflow-episode audit. Read-only is
  ideal here because the example then contains zero approval marks — pair it
  with a *snippet* in the contract or manual showing what an
  approval-marked destructive step looks like (the retire-proxmox-lxc
  `--allow-destroy --yes` step is the canonical shape) so both cases have a
  written instance.
- Actually follow the manual: start from a one-line request summary, walk
  its procedure, save the artifact under
  `.local/evidence/workflow-plans/<date>_<slug>/plan.md`. The step report
  should show the walk (which manual sections fired, what was consulted) —
  that is the "produced by actually following the manual" evidence the exit
  criterion needs.
- `.local` is not in Git, so also inline the full example plan body in the
  step report (it will contain no secrets if the target is chosen as above).
  Expect this walk to expose contract/manual defects — fix them in the same
  step and say so in the report; that is the step's purpose, not a deviation.
- **Do not execute the plan.** There is no executor yet; running it by hand
  proves nothing Phase 2 needs and blurs the phase boundary. The example is
  a planning artifact.

### The discuss_idea1.md amendments (Step 4)

- §6.4: replace the "run both methods and compare" evaluation with the
  adopted mechanism — continuous evaluation through WorkflowEpisode
  (references carry the plan ID; report notes planning-defect vs
  faithful-execution-stop, per roadmap decision 5).
- §6.2: add the hard rule — a step without `approval required` must not
  contain `--yes` or `--allow-destroy` — matching the contract's wording.
- Keep both amendments visibly dated (see Verified facts). The rest of the
  file stays untouched.

## Steps

One report + one commit per step (`p1/report_stepN.md`), all in the root
superproject — no submodule is touched. Nothing here is live or
hard-to-reverse, so no pause points; keep steps small and honest per the
standing style.

### Step 1 — Plan artifact contract

The frozen contract file: four required sections, approval-mark syntax and
the `--yes`/`--allow-destroy` hard rule, recommended (not required) extras,
storage convention and plan-ID form, WorkflowEpisode reference convention,
one inline minimal example.

### Step 2 — Planner manual

`agentdocs/<name>/README.md` following the existing manual precedents:
input handling, known-workflow selection, unknown-work planning, approval
marks, scratch/storage flow, when to return "needs confirmation".

### Step 3 — Real example plan via the manual

Pick a benign real request, follow the manual end to end, store the artifact
under `.local/evidence/workflow-plans/<plan-id>/`, inline it in the report
with the walk evidence. Fold any contract/manual fixes the walk forced into
this step's commit.

### Step 4 — discuss_idea1 amendments + phase report

The two dated amendments, then the phase report: exit criteria against
evidence, README_DEV completion language, and a residual-work note for Phase
2 (the harness now has a frozen surface to build against).

## Out of scope for this phase

The executor harness, any local-model selection or invocation, executing the
example plan, nctl/nintent code changes, WorkflowEpisode creation (Phase 3),
task card schema / catalog / allowlists / replay gate (deferred, decision 8),
and any change to skills other than quoting them.
