# Easier Next Time — Phase 3 Report

## Step 0 — Author the skill

Created `.claude/skills/retire-proxmox-lxc/SKILL.md` per the plan's facts:
typed inputs (`GUEST`, `VMID`, `CONTROL_NODE`), the exact two-upsert
retirement YAML, the fixed step order (declare batch → dry apply → **user
approval** → apply → dry destructive reconcile → manual_review branch table →
checkpoint (fill-in fields, not prose) → **user approval** → destructive
apply → repeat dry reconcile (zero actions) → dry prune → **user approval** →
prune apply), the `manual_review` branch table (`no_realized_object`,
`actual_node_not_linked`, both from the audited episode — re-derived their
exact severities and messages from
`~/.local/state/nctl/events/01KZ2ZE44M3G766FN298HXCRJ8/plan.json` rather than
trusting `audit.md`'s prose summary alone), machine-checkable success
evidence, and prohibitions/stop conditions.

Frontmatter follows policy §5's fields. `last_verified` and
`verified_against` are `null` — explicitly unverified, per the plan and
policy §8.3 ("authoring alone never sets `last_verified`"); a note at the top
of the body states this and points at Step 2/3 as where it gets filled in.

One discrepancy found and resolved while authoring: `audit.md` reported
`actual_node_not_linked` as a "manual_review error" from the episode, but
`nctl/src/nctl_core/reconcile/classify.py`'s current table classifies that
code `AUTOMATIC` (`link_actual_node` reconciler) — it has been classified
that way since `dea9832` (2026-07-17), before the episode ran. Reading the
actual `plan.json` for that operation resolved the discrepancy: the code
appeared at `severity: warning`, not `error`, and only `no_realized_object`
(`severity: error`) was the blocking manual_review finding;
`actual_node_not_linked` was contextual explanation for why the one strong
actual-VM candidate couldn't be auto-linked at the *node* level (VM
realization belongs to `DesiredComputeInstance.realized_vm`, not
`DesiredNode`). The branch table encodes this precisely — treating
`actual_node_not_linked` as blocking only when it appears without
`no_realized_object` — rather than repeating the audit's flatter "two error
codes" framing into the skill.

Commit: this step is committed with this report.

## Step 1 — Static verification

Re-read `SKILL.md` end to end as the executor, with no outside knowledge
beyond the body and the two README sections it points to for background
(neither of which is required to *execute* — commands, order, checkpoint
fields, and the branch table are all inline, per the plan's advice).

Checks performed:

- Frontmatter parses as valid YAML (`python3 -c 'yaml.safe_load(...)'`
  confirmed) and lazy-loading works the same way as any other Claude Code
  skill — `name`/`description` are the only fields guaranteed always in
  context, and `description` is one specific sentence naming the exact
  workflow, per the plan's fact about `.claude/skills/` pickup.
- Every command in "Permitted commands" matches the exact flags used in
  `nctl/README.md`'s two retirement sections (`--allow-destroy --json` dry,
  `--allow-destroy --yes --json` apply, `--yes` alone refuses destruction —
  not relied on or mentioned as a trap here since the skill never emits that
  form).
- The step-6 checkpoint asks for three fill-in fields (slug, vmid, control
  node) sourced from the *immediately preceding* dry-plan output, addressing
  the audit's 3-second-gap near-miss directly (prohibition 5 in the body
  reinforces "re-read the fresh plan, don't reuse an earlier one").
- `.local/retire-GUEST.yaml` is confirmed git-ignored (`.gitignore` line 2:
  `.local`), satisfying prohibition 1 (no secrets/cluster-private paths
  committed).
- No step assumes information outside the guest slug, vmid, and control node
  the executor is told to obtain up front; every `--yes` step has its own
  explicit "STOP — user approval required" line rather than one blanket
  approval covering the whole run, matching Phase 3's prohibition 5.

No wording or command needed correction. No fix commit was necessary beyond
Step 0's.

Step 1 is complete: static verification found the body self-contained and
consistent with current `nctl`/README behavior. No live commands were run.

## Step 2 — attempted, blocked

Attempted later in this same session, at the user's explicit direction
(deviating from policy §7's time-separation rule — recorded as a deliberate
one-off exception, not a change to the rule). Full account in
[`failure1.md`](failure1.md): a scratch guest (`agscratch1`, vmid 199,
`aghub`) was created and declared retired, the skill correctly stopped at an
unenumerated `manual_review` code (`compute_instance_missing`) rather than
improvising past it, and two capable-model remediation attempts outside the
skill's declared scope both failed — the second on an external Nautobot
ingest-job timeout, not a skill or `nctl` defect. Work stopped there per the
user's instruction rather than continuing against a degraded Nautobot.

One real, confirmed skill-body defect was found and is **not yet fixed**
(prohibition 4 — the Step 2 executor does not edit the skill mid-use): the
embedded retirement YAML is missing the `dry_run: true` envelope field
`nctl desired apply` requires.

**Status: blocked**, per README_DEV.md §9. Phase 3's exit criteria (one
completed real use, `last_verified` set) are not met. `agscratch1`/vmid 199
is left live and undestroyed — see `failure1.md` for the exact state and
required follow-up. Step 3 cannot proceed until a clean Step 2 exists.

## Fix 1, Step 0 — Close the failed episode record

Recovery of this blocked state is tracked under
[`fix1/plan.md`](fix1/plan.md). Step 0 wrote the policy §4 self-report at
`.local/evidence/workflow-episodes/20260803_retire-agscratch1/selfreport.md`,
covering the `safe_stop` at `compute_instance_missing`, the
`partially_completed`/`interrupted` scratch-fixture recovery attempt, and the
two independent defects the episode surfaced (missing `dry_run: true`
envelope field, host-scope widening of `--refresh-observation`). See
[`fix1/report0.md`](fix1/report0.md) for the step report.

The blocked conclusion above still stood at that point: Phase 3 was not
complete, and `agscratch1`/vmid 199 remained live and unresolved pending
Fix 1's later steps.

## Fix 1, Step 1 — Fix the batch example and strengthen the skill precondition

Added `dry_run: true` as the first field of the canonical retirement
document in both `nctl/README.md` §"Retiring one Proxmox LXC" and
`.claude/skills/retire-proxmox-lxc/SKILL.md`; bumped the skill to
`version: 2`; replaced the `existing_desired_node` prerequisite with
`existing_realized_compute_instance` and added a prerequisite paragraph
requiring realization to already be observed/ingested/linked in a prior
session; added `compute_instance_missing` and any zero-destroy/link-only
plan to the `manual_review` branch table as explicit precondition failures
with no recovery commands. Static YAML/envelope checks confirmed both
retirement examples now parse with exactly `dry_run`/`operations` and
`dry_run: true`, and that the permitted-commands list and approval gates
were otherwise unchanged. See [`fix1/report1.md`](fix1/report1.md).

## Fix 1, Step 2 — Repair the host-scoped observation contract in nctl

Root cause: `select_scoped_diffs()` admitted placement-specific observation
diffs naming a different owning node merely because their service had any
placement on the requested host, and `_with_forced_observation()` then
merged the forced refresh into the resulting multi-target `observe_node`
action. Fixed `select_scoped_diffs()` to match placement-specific diffs
only to their exact owning node, and added defense in depth in
`_with_forced_observation()`: a still-multi-target action now raises
`ForcedObservationScopeError` (surfaced as
`forced_observation_scope_violation`) instead of silently contacting extra
hosts. Five focused tests added covering the exact failure shape, dedup,
cluster-scope preservation, and the defense-in-depth path. Full nctl suite
(1151 passed) and the Ansible conformance gate (3 passed) both green. nctl
commit `3329d93`; superproject pointer bumped alongside
[`fix1/report2.md`](fix1/report2.md).

## Fix 1, Step 3 — Re-establish local Nautobot Job health

Diagnosed a genuinely non-consuming local Celery worker (responsive to
`celery inspect ping`, not pulling from its own `default` queue) holding
two `run_job` tasks, including the exact stuck JobResult
(`c104e2eb-8963-4f28-a5ed-f417f2c71a45`) from `failure1.md`. Restarted only
`nautobot-nautobot-worker-1` via the documented compose project — no
PostgreSQL/Redis/full-stack recreation. Both queued tasks drained and
reached `SUCCESS` within seconds, proving the queue with terminal results
before any retirement retry. See [`fix1/report3.md`](fix1/report3.md).

## Fix 1, Step 4 — Recover `agscratch1` into an eligible pre-use fixture

A fresh dry `nctl reconcile agscratch1 --json` already showed an exact
`destroy_compute_instance` action (a byproduct of Step 3's drained ingest
Job), so no new `--refresh-observation` was needed. Restored
`agscratch1`'s desired lifecycle/presence to `active`/`present` (approved
apply), which flipped the plan to a non-destructive
`link_compute_realization` action; applied that (approved), after which a
fresh dry reconcile showed zero actions/manual_review — a uniquely
identified, realization-linked, pre-use fixture. No `pct`, direct REST
bypass, or duplicate guest. See [`fix1/report4.md`](fix1/report4.md).

## Fix 1, Step 5 — Real skill use in a new session

New session; no skill edits occurred in it (prohibition 8). Invoked the
revised skill with `GUEST=agscratch1`, `VMID=199`, `CONTROL_NODE=aghub`,
followed exactly with no deviation:

- dry/apply the two-upsert retirement batch (approval gate 1);
- dry destructive reconcile (`01KZ41W0SWZENJNKK5BJKVTCQX`): empty
  `manual_review`, exactly one `destroy_compute_instance` action;
- checkpoint: slug/vmid/control-node all matched;
- destructive apply (approval gate 2, `01KZ41WKMXS2DNC4M845XH1TJY`):
  `destroyed: true, absent: true`, state `converged`; post-actuation
  observation targeted only `["aghub"]`, a live confirmation of Step 2's
  fix beyond its unit tests;
- repeat dry reconcile (`01KZ41YG21KQNW731K3CVS0K35`): 0 actions;
- dry prune (`01KZ41ZP2BH2EX6BCM9BX5FJM4`): `eligible`;
- prune apply (approval gate 3, `01KZ420A7JRRESNPD3Z5WDJTQR`): state
  `pruned`.

All three machine-checkable success criteria held: `converged`, zero-action
repeat plan, `pruned`. Self-report at
`.local/evidence/workflow-episodes/20260803_retire-agscratch1-real-use/selfreport.md`
compares this run against the Phase 2 `aghaos` audit (real per-gate review
instead of a rubber stamp; `manual_review` interpretation stayed out of this
measured session by design) and against the failed use (no free-form
recovery remained inside the workflow; neither prior defect recurred). See
[`fix1/report5.md`](fix1/report5.md).

## Fix 1, Step 6 — Refresh metadata and finalize Phase 3

Set the skill's `last_verified: 2026-08-03` and
`verified_against.nctl: 3329d93bf3ebf38d284adedc6aa3653abd210cfc` (the SHA
used in Step 5's real use). No version bump: the use required no
behavioral edit. This report and the memory index were updated to close out
the roadmap step.

**Status: complete.** All of `fix1/plan.md`'s exit criteria are met: the
failed attempt has a policy-compliant self-report and remains visible as a
safe stop; both canonical retirement examples are valid batch envelopes; a
regression suite proves host-scoped forced observation cannot widen beyond
the requested host and both the nctl and Ansible-conformance gates pass;
the local queue completed bounded Jobs with terminal results before
retirement was retried; `agscratch1`/vmid 199 was safely retired and pruned
with no duplicate scratch guest; one later-session skill use recorded the
exact destroy action, scoped observation, `converged`, zero-action repeat
plan, eligible prune, and `pruned`; and the skill's
`last_verified`/`verified_against` values come from that use. Phase 3 of
the Easier Next Time roadmap is complete.
