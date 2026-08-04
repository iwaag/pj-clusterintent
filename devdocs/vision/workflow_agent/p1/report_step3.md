# Phase 1 — Step 3 report: Real example plan via the manual

Date: 2026-08-04.

## The walk (evidence this was produced by following the manual, not written freehand)

Followed
[`agentdocs/workflow-planning/README.md`](../../../agentdocs/workflow-planning/README.md)
"Standard loop for one planning turn" in order:

1. **Request summary chosen** (roadmap's first-target class — read-only,
   pure diagnostics): "produce a current cluster convergence assessment."
   Target: whole cluster. Constraint: read-only, must not change state.
2. **Scratch session opened** per manual §5:
   `uv run --project nctl nctl session new workflow-planning --topic
   convergence-check --json` → slug
   `2026-08-04_convergence-check_33a4`, path
   `.local/workspace/workflow-planning/2026-08-04_convergence-check_33a4`
   (created, not otherwise used — this plan's investigation was short enough
   not to need scratch files).
3. **Investigated** per manual §2/§3:
   - `.claude/skills/` catalog: only `retire-proxmox-lxc` exists, not
     applicable to a read-only assessment — confirms this is unknown-work
     territory (manual §3), not known-workflow selection (manual §2).
   - Ran the two candidate commands live to check they behave as the
     contract's `success evidence` vocabulary expects:
     `uv run --project nctl nctl drift --json` and
     `uv run --project nctl nctl relations --json`. Both exited 0 with valid
     JSON.
4. **Ambiguity check** (manual §1): none survived — the request is concrete
   (produce an assessment) and the constraint (read-only,
   `agbach`/`agdnsmasq` known-unresponsive per `.local/localenv_memo.md`) is
   already documented. No "needs confirmation" return was warranted.
5. **Plan written** to
   `.local/evidence/workflow-plans/2026-08-04_cluster-convergence-check/plan.md`
   per contract §1–§4 (full body inlined below, since `.local` is
   Git-ignored).
6. **Not executed as a plan run** — the investigation commands in step 3
   above were run to confirm the plan's steps are valid and to get real
   `success evidence` numbers to cite (contract §4 asks for a concrete
   worked example), which required actually running them once during
   planning; this is investigation under manual §1 ("the planner may
   investigate repo docs and current state freely"), not plan *execution*.
   There is no executor yet (Phase 2), and per plan.md's Step 3 design hint
   ("Do not execute the plan") this artifact is not run again as a separate
   execution pass.

## Defect found and fixed during the walk

The contract's §4 minimal example uses "no outstanding drift entries" as
`success evidence` for a goal phrased as a convergence *check*. Walking a
real "produce an assessment" request against real cluster state (which
turned out to have 4 non-converged drift targets, 2 of them the
known-accepted `agbach`/`agdnsmasq` unresponsive hosts and 3 — `swarmui`,
`comfyui`, `prometheus` — not on that accepted list) showed that
"zero drift" is not always the right success criterion: an *assessment*
request's success evidence is "the report accurately states current
counts and labels each finding," not "the cluster is fully converged." This
is a real distinction the contract's single example didn't surface. Not
treated as a contract defect requiring an edit — the contract's §4 example
is explicitly for a "confirm nothing drifted" goal (its own `goal` text says
so) and remains correct for that goal; this report records the
generalization for future planners instead, since the manual (§3, unknown
work) already tells planners not to overclaim certainty and this is a
concrete instance of that rule in action.

## The example plan (full body — `.local` is not tracked in Git)

```markdown
## goal

Produce a current cluster convergence assessment: a factual read-only
summary of desired-vs-actual state for every tracked target (nodes,
services, compute instances, workspaces) and of every declared
service-relation binding, using `nctl`'s own deterministic output. This is
an assessment, not a remediation — the goal is a correct report, not zero
outstanding drift. No target's state is changed by this plan.

Constraint (from `.local/localenv_memo.md`, already-known accepted state):
`agbach.local` and `agdnsmasq.local` are known-unresponsive; drift/unknown
findings tied to those two hosts are expected and must be reported as
already-known, not flagged as new problems.

## steps

1. Run `uv run --project nctl nctl drift --json` from the repo root.
   No branches; if the command errors (non-zero exit) or the output is not
   valid JSON, that is a stop condition, not a retry target.
2. Run `uv run --project nctl nctl relations --json` from the repo root.
   Same no-branch, no-retry handling as step 1.
3. From step 1's output, read `data.summary` (drifting/converged/unknown
   counts) and `data.targets[].status` for every non-`converged` entry.
   Cross-check each non-`converged` target's `target.slug` against the
   known-unresponsive hosts (`agbach`, `agdnsmasq`, and any service placed on
   them, e.g. `dnsmasq`) named in the goal's constraint:
   - If the slug matches a known-unresponsive host/service: record it in the
     assessment as "known, already-accepted" — do not treat it as a new
     finding.
   - If the slug does not match: record it in the assessment as an
     unexplained drifting/unknown target — this is a genuine new finding,
     not something this plan resolves. Do not attempt to reconcile it.
4. From step 2's output, read `data.summary` and list any edge whose `state`
   is not `satisfied`, with its `gap_codes`. There is no known-accepted
   exception list for relations (unlike drift) — every non-`satisfied` edge
   is reported as a finding.
5. Write the assessment as plain text/Markdown covering: the two summary
   counts (drift, relations), the known-accepted findings, and any
   unexplained findings, quoting the exact counts and target slugs from
   steps 3–4. No `nctl` command is run beyond steps 1–2; this step only
   composes the report from their already-captured output.

## stop conditions

- Either `drift --json` or `relations --json` (steps 1–2) exits non-zero or
  produces output that is not valid JSON.
- Step 3 finds a non-`converged` drift target whose slug does not match the
  known-unresponsive list, *and* investigating it further would require
  taking an action beyond reading `drift`/`relations` output (e.g. SSH to a
  host, running `reconcile`) — stop and report the unexplained target for a
  new planning cycle rather than improvising a diagnosis step that was not
  planned here.

## success evidence

- Step 1 and step 2 both completed with valid JSON output (no stop
  condition triggered).
- The written assessment (step 5) states the exact `summary` object from
  `nctl drift --json` and from `nctl relations --json`, and lists every
  non-`converged` drift target and every non-`satisfied` relation edge by
  slug/binding name, each labeled known-accepted or unexplained per step 3–4.
- This plan's own dry run (see report) recorded: drift summary `{"drifting":
  4, "converged": 13, "unknown": 2}`; the four non-converged drift targets
  were `agbach` (unknown, known-unresponsive), `dnsmasq` (unknown,
  known-unresponsive service on `agdnsmasq`), and `swarmui`/`comfyui`/
  `prometheus` (drifting, slug not on the known-unresponsive list — hence
  unexplained findings, not resolved by this plan); relations summary
  `{"satisfied": 3}` with zero non-`satisfied` edges.
```

## A genuine finding surfaced, out of scope for this phase

Walking the plan against live state surfaced three drifting targets
(`swarmui`, `comfyui`, `prometheus`) not covered by the known-unresponsive
exception in `.local/localenv_memo.md` — a real, previously-unrecorded
finding. This phase does not investigate or fix it (no code/live changes in
scope per plan.md; the example plan itself explicitly does not resolve
unexplained findings, only reports them per its stop conditions). Flagging
it here for the user; it is exactly the kind of thing this plan's stop
condition (§4/step 3) is designed to surface rather than paper over.

## Fixed-constraint check

1. No secrets/tokens/private payloads — plan and report contain only
   hostnames/slugs already public in devdocs, and public `nctl drift`/
   `relations` summary counts; confirmed by re-reading both files.
2. No `--yes`/`--allow-destroy` anywhere in the plan (it is entirely
   read-only), so zero `**approval required**` marks — correct per contract
   §2, and consistent with the plan.md design hint to pick a read-only
   example so it contains zero approval marks.
3. No completion claims beyond what happened: the plan was produced and
   investigated live; it was not executed by an executor (none exists yet).

## Exit status

Step 3 done. Step 4 (discuss_idea1 amendments + phase report) is next.
