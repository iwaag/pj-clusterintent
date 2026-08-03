# Easier Next Time — Phase 3 Fix 1 Plan: restore exact scope and complete the first real runbook use

Date: 2026-08-03. Recovery plan for [`../failure1.md`](../failure1.md). This
plan supersedes only the unfinished Steps 2–3 of [`../plan.md`](../plan.md);
the committed Step 0–1 work (`3441e28`) remains valid.

## Goal

Finish Phase 3 without hiding the failed attempt or weakening the retirement
safety boundary:

1. record the failed episode as the policy requires;
2. correct the invalid retirement document in both its authoritative example
   and the skill;
3. restore the documented invariant that a host-scoped forced observation
   targets exactly that host;
4. recover or clean up the existing `agscratch1` fixture without creating a
   second scratch guest or blindly retrying a destroy; and
5. run the revised Level 3 skill successfully in a later session, then set
   `last_verified` from that use and finish the Phase 3 report.

Phase 3 is complete only if the original roadmap exit criteria are met. A
safe cleanup of `agscratch1` without a successful skill use is useful partial
progress, not a substitute for verification.

## Evidence-backed diagnosis

The retry must start from current read-only state. The observations below are
historical evidence from 2026-08-03, not assumptions that the same live state
still holds.

### 1. The skill and README contain an invalid batch envelope

`nctl/src/nctl_core/desired_apply.py` requires the document keys to be exactly
`dry_run` and `operations`. The retirement YAML in both
`nctl/README.md` and `.claude/skills/retire-proxmox-lxc/SKILL.md` omits
`dry_run: true`. The failed use proved that following the Level 3 instructions
literally stops before the dry preview.

This is a runbook/document defect independent of Nautobot health. It is fixed
before another use, not worked around during the use.

### 2. The scratch guest was not a valid retirement fixture yet

Creation operation `01KZ3XHADPAMV7MHDB7KDP2J0Y` created and started VMID 199,
but ended before the corresponding Nautobot `VirtualMachine` was ingested and
linked to `DesiredComputeInstance.realized_vm`. The later retirement dry plan
`01KZ3XYBZXZ2V0ZR90W3PGTS7Z` therefore correctly produced
`compute_instance_missing` and no destroy action.

A newly created LXC is not automatically a valid input to the retirement
skill. For a deliberate scratch use, creation, control-node Proxmox
observation/ingest, and exact compute realization must be complete before the
retirement run begins. Guest-OS SSH enrollment is not required to identify or
destroy the LXC, but the control-node observation and realized VM identity are.

### 3. The failed control-node observation had enough source evidence but its Job never ran

Operation `01KZ3Y5KTQ54XNF6JS7YVNPE5R` collected a complete `aghub` Proxmox
report containing `agscratch1`, VMID 199, node `aghub`, status `running`, and
presence evidence. Its Nautobot JobResult
`c104e2eb-8963-4f28-a5ed-f417f2c71a45` remained `pending` for all 149 polls and
timed out at 300 seconds. This distinguishes a queue/worker problem from a
collector failure. The old report may now be stale, so it is evidence for the
diagnosis, not an input to be replayed without normal age validation.

The local Nautobot/PostgreSQL/Redis stack is a persistent scratch environment
per `.local/localenv_memo.md`. Inspecting and, when justified, restarting only
the local worker is ordinary repair. Collection from `aghub` still crosses the
external-cluster boundary and retains dry-plan review and explicit approval.

### 4. Host-scoped forced observation widened to three hosts

The same operation was invoked as:

```text
nctl reconcile aghub --refresh-observation --yes
```

but its durable `plan.json` gave `observe_node` the targets `aghub`, `agpc`,
and `agstudio`. This contradicts `nctl/README.md`'s promise that
`--refresh-observation` collects and ingests one scoped host.

The cause is deterministic:

- `select_scoped_diffs()` selects every node-agent service diff when that
  service has any active placement on the scoped host;
- placement-specific observation diffs for the same service can name another
  node in `desired.expected.node_slug`;
- the planner resolves those diffs to their named nodes; and
- `_with_forced_observation()` merges the forced refresh into the existing
  multi-target `observe_node` action merely because it contains `aghub`.

This is an nctl scope-contract defect exposed by the failure, not merely a
Nautobot outage. Retrying control-node observation is prohibited until it has
an automated regression test and the dry plan contains exactly `aghub` for
the forced observation.

### 5. The failed episode itself still needs a self-report

Policy §4 requires a self-report after non-trivial cluster work, always when
it was painful. `failure1.md` says none was written because the attempt did
not reach a completed retirement; that rationale conflicts with the policy.
Failed, interrupted, partially completed, and safe-stop episodes are exactly
the cases the self-report format can represent.

## Corrected contracts

### Retirement runbook contract

- The embedded document is a complete batch envelope with
  `dry_run: true` and exactly the two existing partial upserts.
- `existing_realized_compute_instance` is an explicit prerequisite. A target
  that produces `compute_instance_missing`, a link-only plan, no destroy
  action, or an ambiguous candidate is a precondition failure and safe stop;
  the skill does not turn into a creation, observation-recovery, or linking
  runbook.
- `compute_instance_missing` remains an unenumerated/manual stop. It must not
  be reclassified as a harmless wait or given a direct-`pct` bypass.
- A use is successful only after an exact destroy checkpoint, converged
  apply, zero-action repeat plan, eligible prune, and `pruned` apply.

### Host-scope contract

For `nctl reconcile HOST --refresh-observation`:

```text
requested HOST
  = observe_node action target set
  = SSH preflight host set
  = bootstrap inventory/Ansible --limit host set
  = report_batch source set
```

All sets contain exactly one slug. Placement-specific service observation
diffs for other hosts do not enter a host-scoped plan merely because the same
service also has a placement on `HOST`.

Service actions may still be selected for the requested host, but their
`parameters.host_slugs` remain limited to that host as today. Global contract
errors remain visible and blocking; they do not authorize observation of
additional hosts.

### Fixture contract

Do not create another guest for this retry. Prefer the already-created,
disposable `agscratch1` only if current evidence still proves all of these:

- VMID 199 exists exactly once as an LXC on `aghub`;
- no conflicting desired or actual identity exists;
- fresh control-node evidence has been successfully ingested;
- `DesiredComputeInstance.realized_vm` is linked to that exact VM; and
- before invoking the skill, the guest is restored to the ordinary
  `active`/`present` starting state so the skill itself performs the real
  `retired`/`absent` transition.

If these cannot be established safely, clean up the disposable resource under
separate explicit authority and wait for a naturally eligible retirement
target. Direct cleanup never counts as the Level 3 use.

## Execution plan

Use separate sessions at the boundaries below. In particular, no session that
edits the skill may also be the session measured as its real use.

### Step 0 — Close the failed episode record

In an improvement-only session, create
`.local/evidence/workflow-episodes/20260803_retire-agscratch1/selfreport.md`
using policy §4. Reference the four operation IDs from `failure1.md`; do not
copy their evidence bodies.

Record the outcome precisely:

- the skill use ended in a correct `safe_stop` at the unenumerated
  `compute_instance_missing` code;
- the surrounding scratch-create/recovery work was `partially_completed` and
  then interrupted by the pending ingest Job;
- the runbook reduced improvisation at the destructive boundary, but the
  missing `dry_run` field and an unprepared fixture forced Level 2 recovery;
  and
- host-scope expansion was discovered only by inspecting durable evidence.

Do not change `last_verified`. Append a short Step 0 note to `../report.md`
that points to the self-report and says the earlier blocked conclusion still
stands.

### Step 1 — Fix the batch example and strengthen the skill precondition

Update both:

- `nctl/README.md` §"Retiring one Proxmox LXC"; and
- `.claude/skills/retire-proxmox-lxc/SKILL.md`.

Add `dry_run: true` as the first field of the canonical retirement document.
Keep the existing two operations unchanged. In the skill:

- bump `version` because executor behavior changes;
- replace the broad `existing_desired_node` prerequisite with an explicit
  realized-compute prerequisite;
- state before Step 1 that a scratch guest must have completed platform
  observation/ingest and compute realization in a prior session;
- add `compute_instance_missing` and a link-only/no-destroy plan to the stop
  conditions as precondition failures, without adding recovery commands; and
- keep `last_verified` and `verified_against` null.

Static checks:

1. parse the frontmatter as YAML;
2. extract and parse both retirement YAML examples;
3. assert each has exactly `dry_run` and `operations`, with `dry_run: true`;
4. confirm the skill's permitted commands and every `--yes` approval boundary
   are unchanged; and
5. confirm a fresh skill listing exposes its name and description.

Commit this documentation/skill correction before any cluster work.

### Step 2 — Repair the host-scoped observation contract in nctl

Change host-scope selection so a service observation diff carrying
`desired.expected.node_slug` or `node_id` is selected only for that exact
owning node. Retain the existing service-membership behavior only for
genuinely service-wide diffs that have no placement-specific node identity.
Do not filter targets later in `run_observation`; the installed plan itself
must show the correct scope.

Add defense in depth around forced refresh: after building a host-scoped
forced plan, its `observe_node` action must contain exactly the requested
node. Do not merge a forced refresh into a multi-target observation action.
Treat such a plan as a planner invariant violation rather than silently
contacting the extra hosts.

Focused tests must cover the exact failure shape:

1. one multi-placement service with observation diffs for `aghub`, `agpc`,
   and `agstudio`, scoped to `aghub`, yields only the `aghub` observation
   target;
2. a node-local observation diff and service observation diff for `aghub`
   deduplicate to one target;
3. `--refresh-observation` on a plan that would otherwise contain service
   observations neither merges nor widens beyond `aghub`;
4. the executor passes only `aghub` through SSH preflight, bootstrap
   inventory, Ansible `--limit`, and the ingest `report_batch`; and
5. cluster-scoped observation retains its existing multi-host behavior.

Verification from documented working directories:

```bash
cd nctl
uv run pytest -q --durations=20

cd ..
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
```

Commit the nctl change in the submodule, then commit the superproject pointer.
Do not deploy or touch the cluster in this step.

### Step 3 — Re-establish local Nautobot Job health

Run this in a later infrastructure-recovery session, before any new
collection or apply.

1. Inspect the current status of JobResult
   `c104e2eb-8963-4f28-a5ed-f417f2c71a45`, the local worker/scheduler
   container status, and worker logs around the timeout. Do not assume the Job
   is still pending and do not expose tokens or report bodies.
2. Confirm the Nautobot HTTP health endpoint and a time-bounded
   `nctl status --json` complete. A container health label alone is
   insufficient.
3. If the old Job is terminal and the queue is draining, do not restart
   anything. If it is abandoned/pending with no worker consuming jobs,
   restart only `nautobot-nautobot-worker-1` using the documented local
   compose project. Do not recreate PostgreSQL, Redis, or the full stack for a
   worker-only fault.
4. Prove the queue with one bounded Job execution and a terminal JobResult;
   record its ID and runtime. Prefer a fixture-owned/synthetic runtime case
   with exact cleanup. If the runtime probe cannot exercise Celery, use the
   next intended single-source `aghub` ingest as the proof, but do not submit
   repeated Jobs while an earlier one remains pending.

If the worker or API still cannot complete one bounded Job after the targeted
repair, stop and report the current evidence. Do not increase the 300-second
timeout to disguise a non-consuming queue.

### Step 4 — Recover `agscratch1` into an eligible pre-use fixture

This is fixture preparation outside the retirement skill. It may use capable
model/human judgment, but every write and external contact remains scoped and
recorded.

1. Re-read current desired and actual state. Confirm whether VMID 199 still
   exists on `aghub`, whether it is already ingested/linked, and whether any
   delayed old Job changed the ledger. A current exact destroy dry plan means
   the realization recovered; do not perform redundant observation.
2. If fresh platform evidence is still needed, run
   `nctl reconcile aghub --refresh-observation --json` first. Its durable plan
   must show the `observe_node` target set exactly `['aghub']`; reject the
   plan if `agpc`, `agstudio`, or any other host appears. Review all other
   `aghub`-scoped actions separately.
3. After explicit approval, apply the unchanged scoped plan. Assert positive
   evidence: SSH preflight names only `aghub`, Ansible is limited to `aghub`,
   the ingest batch has only source `aghub`, the Job reaches `success`, and
   the summary includes the source. A timeout or pending result stops the
   step; do not immediately resubmit.
4. Restore only `agscratch1`'s desired lifecycle/presence to
   `active`/`present` with one canonical dry/apply batch (including
   `dry_run: true`) so the later skill performs a real retirement transition.
   This changes scratch Nautobot intent only; still obtain explicit approval
   for the apply because it changes the target being prepared.
5. Run a dry `nctl reconcile agscratch1 --json`. If it plans the exact
   `link_compute_realization` for the freshly observed VM, apply that
   non-destructive ledger action under approval and verify the link from a
   fresh snapshot. It must not create a second VM, destroy VMID 199, or
   require observation of the unenrolled guest merely to establish the
   Proxmox realization. If the current nctl loop cannot isolate the link from
   a create/destroy or guest-SSH action, stop; do not use an expected failure
   as the normal fixture-preparation interface.
6. Confirm a fresh snapshot uniquely maps `agscratch1` to VMID 199 on
   `aghub`. Do not start the skill until this holds.

Step 5 above is an audit point: if nctl has no safe bounded way to complete an
already-observed compute link, write a separate defect plan rather than adding
direct REST/PATCH or `pct` commands to the retirement skill.

If VMID 199 is absent or identity is ambiguous, do not recreate it. Follow the
cleanup branch below and wait for a naturally eligible target.

### Step 5 — Real skill use in a new session

Start a new session after Steps 1–4 are committed/complete. Invoke the revised
skill with:

```text
GUEST=agscratch1
VMID=199
CONTROL_NODE=aghub
```

Use these values only after the fresh checks in Step 4; they are not inferred
from this historical plan. Follow the skill exactly:

1. dry and apply the two-upsert retirement batch;
2. produce a fresh dry destroy plan;
3. fill in and retain the slug/VMID/control-node checkpoint;
4. obtain separate approval and run the destructive apply once;
5. verify `converged` and a repeat dry reconcile with zero actions; and
6. dry/apply prune under its separate approval and verify `pruned`.

Positive evidence must show that `destroy_compute_instance` actually ran,
that post-destroy observation used only `aghub`, and that no second destroy
was planned. An unenumerated code or missing exact action is a safe stop, not
permission to leave the skill and improvise in the same session.

Write a new self-report under a distinct episode directory. Explicitly compare
the revised run against both the Phase 2 audit and the failed use: which
decisions disappeared, whether the checkpoint was a real review, and whether
any free-form recovery remained inside the measured workflow.

### Step 6 — Refresh metadata and finalize Phase 3

In a later improvement session:

1. inspect the successful operation artifacts and self-report;
2. set the skill's `last_verified` to the real-use date and
   `verified_against.nctl` to `git -C nctl rev-parse HEAD` from that run;
3. bump the skill version again only if the use requires a behavioral edit;
4. append Steps 1–6 and all operation IDs/results to `../report.md`;
5. change the report from `blocked` to `complete` only when every original
   Phase 3 exit criterion is met; and
6. update the memory index required by the original plan.

Run final static checks and the ordinary nctl suite again if Step 6 changes
executable skill content or nctl code.

## Cleanup-only branch

If `agscratch1` cannot safely become an eligible fixture, it must not remain a
forgotten resource:

1. obtain explicit approval for cleanup of the exact disposable LXC, VMID 199
   on `aghub`;
2. prefer nctl-managed retirement if a unique realization and exact destroy
   plan can be established;
3. use direct Proxmox cleanup only as the separately approved last resort
   described in `failure1.md`, after re-resolving identity immediately before
   mutation;
4. observe/ingest the absence and clean only the fixture-owned desired/actual
   ledger state when the supported path permits it; and
5. record cleanup as partial progress. It does not set `last_verified` and
   does not complete Phase 3.

Do not delete historical operation evidence or the failed episode record.

## Prohibitions

1. No secret, token, private key, raw report body, or private cluster payload
   in Git-tracked files or retrospective artifacts.
2. No blind retry of a pending ingest Job and no timeout increase as a queue
   workaround.
3. No control-node refresh whose plan names hosts other than the requested
   control node.
4. No new scratch guest while VMID 199 is unresolved.
5. No direct `pct`, direct REST ledger link, fabricated actual state, or
   weakened SSH policy inside the retirement skill.
6. No second destroy after partial mutation; use retained evidence and fresh
   control-node observation.
7. No `last_verified` or Phase 3 completion claim from a safe stop, fixture
   cleanup, unit test, or dry plan.
8. No skill edit in the session measured as its real use.

## Exit criteria

- The failed attempt has a policy-compliant self-report and remains visible as
  a safe stop/partial outcome.
- Both canonical retirement examples are valid batch envelopes.
- A regression test proves host-scoped forced observation cannot widen beyond
  the requested host, and the nctl ordinary plus Ansible conformance gates
  pass.
- The local queue completes one bounded Job with a terminal result before
  retirement is retried.
- `agscratch1` is either safely removed or explicitly accounted for; no
  duplicate scratch guest exists.
- One later-session skill use records the exact destroy action, scoped
  observation, `converged`, zero-action repeat plan, eligible prune, and
  `pruned`.
- The successful use has its own self-report, and the skill's
  `last_verified`/`verified_against` values come from that use.
- `../report.md` uses `complete` only after all of the above; otherwise it
  names the remaining criterion and stays `partially complete` or `blocked`
  according to README_DEV.md §9.
