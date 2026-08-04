# Workflow Agent — Plan Artifact Contract

Status: frozen 2026-08-04 (Phase 1, Step 1 of [`roadmap.md`](roadmap.md)). This
is the shared surface between the planner (a strong model following
[`../../agentdocs/workflow-planning/README.md`](../../agentdocs/workflow-planning/README.md))
and the executor harness (Phase 2, not yet built). Both consume this file
without further negotiation — do not fork or paraphrase this contract
elsewhere; link to it instead.

No backward compatibility applies (roadmap decision 8): there is no prior
contract, so nothing here needs to preserve an older shape.

## 1. Required sections — exactly four

A plan artifact is one Markdown file with exactly these four `##` sections,
in this order. All four are required; none may be empty.

1. `## goal` — the state this plan run is trying to reach, in a few sentences.
   Names the target (host/service/desired-state object) and the user-stated
   constraints from the confirmed request summary.
2. `## steps` — the ordered, numbered list of concrete actions. Each step:
   - is small enough to be one executor turn (one command or one short
     bounded sequence);
   - names the known workflow it uses (a skill, an `nctl` bounded command)
     when one applies, rather than re-deriving the workflow's internals;
   - inlines any enumerated branches and bounded retries for that step
     directly under it — the executor does not invent branches or retries
     that are not written here;
   - carries the `**approval required**` marker (see §2) when it is gated by
     existing policy.
3. `## stop conditions` — the conditions under which the executor stops and
   reports instead of continuing: any state not covered by an enumerated
   branch in `steps`, any command error not covered by a bounded retry, and
   explicitly "reaching the end of `steps` without a `success evidence` match"
   if that can happen. This section is where *unplanned* divergence goes;
   *planned* divergence (known branches/retries) belongs inline in `steps`.
4. `## success evidence` — what to check, and against what expected result,
   to call the run complete. Prefer deterministic, machine-checkable output
   the executor can quote in its report over a judgment call: `nctl drift
   --json`, `nctl relations --json`, `nctl ops list` / `nctl ops show
   OPERATION_ID`, `nctl workflow-episode show <id> --json`. Name the specific
   command and the specific field/value to check, not just "check drift
   looks fine."

Everything else is optional and does not gate acceptance of a plan artifact:
machine-checkable expected outputs beyond `success evidence`, explicit
workflow-ID cross-references, risk notes, a rationale section. Add these only
if they earn their place — v1 deliberately rejects a fat schema
(discuss_idea1 §4.2).

## 2. The approval-mark rule

Some steps touch policy-gated ground: the production/external class
(README_DEV §10), or an `nctl` flag that actually mutates state —
`reconcile --yes`, `reconcile --allow-destroy`, `prune --yes`, `desired apply
--yes`, or a direct SSH/Ansible mutation outside `nctl`. Mark exactly these
steps.

**Marker syntax (exact, machine-checkable):** a line reading exactly

```
**approval required**
```

placed as its own line directly under the step's heading/number, before the
step's command(s). No paraphrase (`approval needed`, `[approval]`, `NOTE:
approval`, etc.) satisfies this — Phase 2's linter greps for this literal
string.

**The one hard rule:** a step without `**approval required**` must not
contain `--yes` or `--allow-destroy` anywhere in its command text. This is
checked by static grep over the plan file, not by executor judgment. A step
needing either flag must carry the marker; a step carrying the marker still
only executes after the human approval that flag itself gates (the plan
marker does not substitute for that approval — see discuss_idea1 §6.3: the
executor never disables a safety rule the plan omitted, and the real barrier
is `nctl`'s own confirmation flags).

## 3. Storage convention

Plan artifact, executor transcript, and execution report for one run live
together under one directory in the Git-ignored `.local/`:

```
.local/evidence/workflow-plans/<plan-id>/
  plan.md          # this contract's artifact — exists once planning is done
  transcript.*      # executor's raw transcript — Phase 2 only, may not exist yet
  report.md         # execution report — Phase 2 only, may not exist yet
```

`<plan-id> = <date>_<slug>` (e.g. `2026-08-04_cluster-convergence-check`),
mirroring the existing `.local/evidence/` operation-evidence pattern. A
directory holding only `plan.md` is a legitimate state — planning without
having run the plan through an executor yet (true for every Phase 1 example,
since there is no executor until Phase 2).

**What goes to the database, what stays local:** the plan ID (e.g.
`2026-08-04_cluster-convergence-check`) is what a `WorkflowEpisode`
`references` entry carries — never a machine-local path. Plan/transcript/
report bodies are never copied into `raw_data`; if a WorkflowEpisode needs to
point at this run, it points at the plan ID (and the reader resolves it back
to `.local/evidence/workflow-plans/<plan-id>/` on whichever machine has it).
Suggested convention key: `"workflow_plan_id": "<plan-id>"` inside the
episode's `references` JSON.

## 4. Minimal complete example

A read-only plan with no approval-gated steps:

```markdown
## goal

Produce a current convergence assessment for the cluster: confirm desired
vs. actual state agree and no drift is outstanding, without changing
anything.

## steps

1. Run `uv run --project nctl nctl drift --json` from the repo root. No
   branches; if the command errors (non-zero exit), that is a stop
   condition, not a retry target.
2. Run `uv run --project nctl nctl relations --json` from the repo root.
   Same no-branch, no-retry handling as step 1.

## stop conditions

- Either command in `steps` exits non-zero or produces output that is not
  valid JSON.
- `drift --json` reports any host/service as un-converged that the goal did
  not anticipate — do not attempt to reconcile it; stop and report the
  drifted item for a new planning cycle.

## success evidence

- `nctl drift --json` output shows no outstanding drift entries (empty or
  all-`converged`).
- `nctl relations --json` output completes without error and shows no
  relation marked inconsistent.
```

And the shape of one **approval-marked** step (a destructive example,
trimmed from the `retire-proxmox-lxc` skill — shown here only as an instance
of the marker, not a full plan):

```markdown
6. Actuate the destructive reconcile for GUEST.

   **approval required**

   Run `uv run --project nctl nctl reconcile GUEST --allow-destroy --yes
   --json`. Confirm the result state is `converged`. If it is not, stop —
   this is not a bounded-retry situation.
```

## 5. What this contract is not

Not an executor rule prompt (Phase 2 writes that separately, quoting this
contract's marker rule). Not a workflow catalog or router — skill lazy
loading already routes known work; a plan step just names the skill/command
it uses. Not a task-card schema, allowlist, or replay gate — those stay
deferred (roadmap decision 8) until real failures justify them.
