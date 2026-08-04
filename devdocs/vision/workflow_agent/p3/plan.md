# Workflow Agent — Phase 3 Plan

Status: planned 2026-08-04. Implements Phase 3 of [`../roadmap.md`](../roadmap.md):
use the plan → executor → report protocol on real requests as standing
practice, record a WorkflowEpisode per non-trivial run, make minimal fixes to
the contract / manual / harness from what actually fails, and record whether
any deferred mechanism (roadmap decision 8) has earned promotion.

Destructive-phase note: no backward compatibility (roadmap decision 8). The
rule prompt, harness behavior, report format, and even contract wording may
all be changed freely if real use demands it — nothing outside this roadmap
consumes them yet. The only stable surface is the plan-ID ↔ WorkflowEpisode
reference (contract §3), because episodes outlive this phase.

## Goal and exit criteria

Fixed by the roadmap:

1. At least **one real request** — work someone genuinely wants done, not a
   proof artifact — executed through plan → executor → report.
2. A **WorkflowEpisode** for that run: `references` carries the plan ID
   (convention key `"workflow_plan_id"`, contract §3), `report` notes in free
   text whether any failure was a *planning defect* or a
   *faithful-execution stop*.
3. A **short evaluation note**: what broke, what was fixed (contract/manual/
   harness/prompt commits), and a verdict per deferred mechanism — promoted
   or still deferred, with one line of justification each.

After exit, this continues as ongoing practice (episodes per run), not a
roadmap. There is no "enough runs" bar — one honest end-to-end real cycle is
the exit; more runs during the phase are welcome but not required.

## Fixed constraints (everything else is implementer's discretion)

The roadmap's three standing prohibitions, nothing more:

1. **No secrets, tokens, or private payloads** in plans, transcripts,
   reports, episode namespaces, or Git-tracked files. Real requests may pass
   near `.local/secrets` territory (localenv memo §Secrets) — never plan a
   step whose output prints token values; the transcript records command
   output verbatim.
2. **The approval boundary holds**: the contract §2 marker rule and the
   harness's existing lint/runtime mirror stay in force. Real mutations still
   go through `nctl`'s own confirmation flags; an approval-marked step
   executes only after actual human approval, whatever v2 marked-plan
   handling looks like (see hints). Real-cluster SSH/Ansible, Proxmox
   operations, and external writes keep their explicit approval boundary
   (localenv memo); local scratch-stack mutations are routine and need no
   pause.
3. **Do not claim completion the evidence does not show** (README_DEV
   completion language). For episodes this extends naturally: never write an
   `assessment`/`resolution` the run's artifacts don't support
   (workflow-improvement manual prohibition 2 analog).

Explicitly free: which real requests to take, how many runs, marked-plan v2
policy, rule-prompt/harness/report changes, episode `report` prose shape,
whether to backfill old episodes (see hints), commit granularity for fixes.

## Verified facts (checked 2026-08-04 while planning)

- **`p3/` was empty** — this plan is its first file.
- **Executor state** (Phase 2, commits `229951d`/`7f72e41`): invocation
  `python3 executor/executor.py <plan-file-or-plan-id> [--lint-only]`, model
  `qwen3.6:35b-a3b-coding-nvfp4` via ollama (`glm-4.7-flash` unused
  fallback), caps 30 turns / 30 min / 180 s per command. Known v1 gaps,
  accepted until a real run forces a fix (p2/report_step4):
  - plans containing `**approval required**` pass lint but are **refused
    before any model call** ("not supported yet");
  - the model's final message can leak scratch reasoning above the report
    skeleton — read from `## status` down;
  - big command outputs (≳100 KB) would pressure `num_ctx 32768` — plans
    should pre-filter (e.g. `--json` + a bounded `python3 -c` summarizer as
    an explicit plan step, or a narrower nctl subcommand).
- **The ready first real request is still real**: live `nctl drift --json`
  today shows `{"drifting": 4, "converged": 13, "unknown": 2}` with the
  `swarmui`/`comfyui` (`service_missing` on agpc) and `prometheus`
  (`service_observed_on_wrong_node`) findings still unexplained — unchanged
  since the Phase 2 completed run. Diagnosing (and possibly fixing) these is
  genuinely wanted work, not a manufactured target.
- **`agpc.local` and `agstudio.local` are reachable** over SSH/Ansible;
  `agbach.local`/`agdnsmasq.local` unresponsive is known-and-fine (localenv
  memo). So an agpc service diagnosis has a live target. Direct SSH (via
  `~/.ssh/ansible_key`) requires asking the user first (localenv memo, human
  note) — in plan terms that is an `**approval required**` step or a
  planning-time investigation done in the main session, not by the executor.
- **The WorkflowEpisode store is live and empty**: `nctl workflow-episode`
  has the full 7-command group (`list/show/create/write/select/resolve/
  dismiss`); count was 0 at Phase 2 Step 3. This phase writes the first real
  rows. GUI verification needs a browser session (agent cannot verify
  headlessly — easier_next_time2 p4 finding); verify episodes via
  `nctl workflow-episode show <id> --json` instead.
- **Episode conventions already exist** — do not invent new ones:
  `agentdocs/workflow-improvement/README.md` + easier_next_time policy.md.
  Key points that bind this phase: episode `report` is written once at the
  end of the operating session and never edited later; improvement work
  (editing manuals/skills/nctl in response to an episode) belongs to a
  *separate* workflow-improvement session after human selection — **time
  separation**. See the wrinkle in hints below for how that interacts with
  this phase's "minimal fixes" mandate.
- **The planner manual and contract are in daily-usable state** (Phase 1);
  two real plans exist under `.local/evidence/workflow-plans/`. Nothing in
  either document blocks Phase 3; amendments happen only if a real run
  exposes a defect.

## Design hints (advice, not requirements)

### Choosing and running real requests

- **First run suggestion**: a read-only diagnostic plan for the
  swarmui/comfyui/prometheus drift — enumerate the bounded checks (drift
  detail for those targets, `nctl relations --json`, service-status reads on
  agpc) as steps, with "any finding outside the enumerated hypotheses" as a
  stop condition. This exercises the whole protocol on wanted work without
  touching the marked-plan gap. The *fix* that follows the diagnosis is a
  second planning cycle (per decision 4 — continuing after a stop/completion
  is a new cycle), and that one may need marked steps.
- **Planning-time investigation is unlimited; executor steps are not.** If
  diagnosis needs open-ended exploration, do it in the main session while
  planning, then hand the executor only the bounded confirmation/actuation
  steps. Don't force exploratory work through the executor — that is the
  division of labor the whole roadmap exists for.
- **Non-trivial bar for episodes**: use judgment. A run that taught nothing
  (clean completion of a routine read) doesn't need an episode; the roadmap
  asks for episodes after each *non-trivial* run. The exit-criterion run
  should be non-trivial almost by definition.

### Marked-plan handling v2 (only if a real run forces it)

- The v1 refusal is fine until a real request needs a mutating step. When
  one does, the cheapest honest upgrade is the Phase 2 plan's original
  option: on reaching a marked step, the harness prints the step's full
  command(s) and prompts y/N on the terminal; N is a stop with a recorded
  stop point. That keeps the human at the actual approval boundary with
  ~20 lines of code. Do not build queueing, notification, or partial-resume
  machinery — a refused approval ends the run; re-running after a fix is a
  fresh execution.
- Remember the runtime mirror already refuses `--yes`/`--allow-destroy`
  from the model under an unmarked plan — keep that check when adding
  approval prompting; it is the tripwire for prompt-injection-shaped
  improvisation.

### Episode creation

- Feed the execution report into `nctl workflow-episode create` as a
  copy-shape operation (roadmap: report shape was designed for this). A
  reasonable `references` JSON:
  `{"workflow_plan_id": "<plan-id>", "operations": ["<nctl-op-id>", ...]}` —
  plan ID always, operation IDs when the run produced any. Never a local
  path (policy §8.2).
- The `report` namespace free text should answer the one evaluation question
  the roadmap cares about: *planning defect or faithful-execution stop?*
  Plus the usual: what ran, where it stopped, key outputs. Keep it short;
  the transcript stays local as the detailed record.
- Status stays `candidate` after create — do not self-select or self-resolve
  in the same session; that is the human's survey step
  (workflow-improvement manual).

### The time-separation wrinkle

Policy says: don't improve a runbook/manual for the task you are currently
executing. The roadmap says: make minimal fixes to contract/manual/harness
from what fails. These reconcile cleanly if you split by *which workflow the
fix belongs to*:

- **Fixes to the workflow-agent protocol itself** (rule prompt wording,
  harness bug, contract/manual defect) are this roadmap's own Phase 3 work —
  make them directly, one commit each, noted in the step report. The
  protocol is the thing under development here, not a runbook for the
  cluster task being executed.
- **Fixes to cluster runbooks/skills/nctl** that a run's pain suggests (e.g.
  "the drift diagnosis should be an nctl subcommand") go through the episode
  → human selection → separate workflow-improvement session path. Record the
  observation in the episode `report` and leave it.

### Backfill decision (small, decide once)

The Phase 2 stop-run discovered the agscratch1 retirement has no episode.
Decide explicitly: backfill episodes for pre-scheme work, or declare the
scheme forward-only. Recommendation: forward-only — backfilled reports would
be reconstructions, and policy already warns against depending on the old
`.local/evidence/workflow-episodes/` directories. Write the decision (either
way) in a step report; don't leave it implicit.

### Evaluation note shape

One page in `p3/`. Contents: runs executed (plan IDs), what failed and which
commit fixed it, planning-defect vs execution-stop tally (will be tiny — fine),
and the deferred-mechanism table: task card schema, workflow catalog, strict
allowlists, planner/executor API, small-model replay gate — each with
promote / keep deferred and one line why. Expected outcome given current
evidence: all stay deferred; say so honestly rather than promoting something
to look thorough.

## Steps

One report + one commit per step (`p3/report_stepN.md`), root superproject
unless a fix lands in a submodule (then the standing submodule-commit +
user-push convention applies). Pause for user approval before any step that
mutates the real cluster (SSH/Ansible/Proxmox/external) or runs an
approval-marked plan — read-only diagnostics and scratch-stack work need no
pause.

### Step 1 — First real request: plan + executor run

Pick the real request (default: swarmui/comfyui/prometheus drift diagnosis).
Plan it via the workflow-planning manual, run it through the executor, keep
plan + transcript + report in the plan-ID directory. If the run exposes a
harness/prompt/contract defect, fix it minimally (protocol-side fixes only,
per the time-separation split), rerun if needed, and record the iteration.

### Step 2 — WorkflowEpisode for the run

Create the episode (`references.workflow_plan_id`, free-text `report` with
the planning-defect vs execution-stop call), verify via
`nctl workflow-episode show <id> --json`. Record the backfill decision
(forward-only or backfill list) in this step's report.

### Step 3 — Follow-on cycle if the diagnosis warrants one

If Step 1's diagnosis points to a concrete fix someone wants applied: a new
planning cycle for the fix, marked-plan v2 handling if the plan needs marked
steps, execution with the human at the approval prompt, and its own episode.
If the diagnosis instead ends the matter (finding recorded, no fix wanted),
say so and skip to Step 4 — this step is conditional, and skipping it
honestly does not fail the phase.

### Step 4 — Phase report + evaluation note

Exit criteria against evidence (plan-ID directories, episode IDs, commits),
the evaluation note (runs, fixes, deferred-mechanism verdicts), README_DEV
completion language, and the handoff sentence: this practice now continues
per-request without a roadmap, episodes accumulating for the
easier-next-time loop to consume.

## Out of scope for this phase

Building any deferred mechanism (decision 8) unless this phase's own runs
justify promotion — record the verdict instead; resolving/dismissing the
episodes this phase creates (separate workflow-improvement sessions, after
human selection); model benchmarking or swapping without a disobedience
reason; GUI work for episodes; routing through `cagent`; fixing the
agpc/agstudio observed-state staleness beyond what the chosen real request
itself requires.
