# Report: make a created-then-orphaned guest reconcilable again

Executed 2026-08-10 (JST) against [`plan.md`](plan.md), on `nctl` submodule
`7782d72` (changes left **uncommitted** in the working trees; file list at the
end). Executor: Omni Agent (Claude Code, backend `claude-fable-5`).

**Outcome: complete.** All four steps implemented, `uv run pytest -q` green
(1316 passed), all three required plan-level acceptance tests present, and the
strongly-recommended live reproduction performed on `aghub`: a real
created-then-orphaned guest (LXC 113 `agdoomed3`) was recovered to destroyed +
pruned **with a single `nctl reconcile agdoomed3 --allow-destroy --yes` from
the guest's own scope**, no `pct` command and no ledger hand-edit anywhere.

## 0. Plan §0 corrections — verified

All four hold against `7782d72` exactly as the plan states:

1. Proposal A already implemented: `compute_disposition.py:90` and
   `compute_creation.py:79` both set `"host_slugs": [control.slug]`;
   `reconcilers.py` passes `parameters=disposition.parameters` through.
2. `destroy_compute_instance` already in the observe-suppression set
   (`planner.py`, `compute_transition_target_slugs`).
3. The hypervisor-side linking path exists (nodeutils collection on the
   control node; `executor.py` post-actuation observation uses
   `action_host_slugs()` → `host_slugs=[control]`). Nothing re-requested it —
   confirmed as the whole bug.
4. A ledger link is not required to destroy (`_match_instance` matches by
   vmid, then name). **Also verified live**: the first `agdoomed2` destroy ran
   against an *unlinked* guest matched by vmid and succeeded (see §3).

## 1. What was changed

### Step 1 — hypervisor-routed evidence refresh (`planner.py`)

`build_plan` now derives compute realizations and, for every scoped compute
instance that (a) has a diff in scope, (b) has no `VirtualMachine` in its
realization (missing guest and stale/absent platform observation alike), and
(c) got no compute transition action this round (the plan's recommended
narrowing — create fell back to manual_review, or the node is retired), plans
one `observe_node:compute-evidence` action targeting the platform's **control
node(s)**, with `parameters["host_slugs"]` set to those controls.

- Recorded decision: this deliberately actuates a node outside
  `scope.host_slug`. It is a read-only nodeutils collection + ingest, and it
  is the point of the fix — the evidence lives on the hypervisor.
- The forced-observation trap the plan warned about: `_with_forced_observation`
  now **skips** observe actions that do not contain the scoped host (they keep
  their own purpose) and still raises `ForcedObservationScopeError` only when
  an action mixes the scoped host with others. Covered by
  `test_with_forced_observation_skips_control_node_evidence_action`.
- The `--refresh-observation` terminal-failure check in `_run_apply` was
  narrowed to the actually-forced action ids so a coexisting compute-evidence
  observation keeps its established non-terminal failure behavior.
- No "tried once" flag added — the existing fingerprint/no_progress guard is
  the loop bound, as the plan predicted.

### Step 2 — retired nodes never get an observe action (`planner.py`)

`_retired_effective_lifecycle_slugs()` computes each node's effective
lifecycle (`compute.contract.effective_lifecycle` with its platform where one
exists; own lifecycle otherwise) and the observe-target filter drops retired
slugs alongside the existing compute-transition suppression. Their evidence
gaps stay visible in drift as before.

### Step 3 — one machine-readable home for SSH contact (`registry.py`, `reconcilers.py`, `ssh_preflight.py`)

- `Reconciler` gained `connects_over_ssh: bool`. True for `observe_node`,
  `create_compute_instance`, `destroy_compute_instance`, `service_profile`,
  `dnsmasq_config`, `new_node_baseline` (declarative only — no handler).
- `SSH_REQUIRING_RECONCILER_IDS` is now **derived** from the registry, not
  hand-written. Deliberate behavior change: `create_compute_instance` is now
  in the gate (it always ran `ansible-playbook --limit control` over SSH but
  was never gated). Its gate host is the control node, so the bootstrap
  "absent guest can't be enrolled" flow is unaffected — verified live
  (`ssh_preflight: [('aghub','ready')]` on a create plan).
- Every SSH-connecting reconciler now sets `parameters["host_slugs"]`
  explicitly (`plan_observe_node`, the executor's `post_actuation_observation`
  and forced-refresh action included). For those reconcilers the silent
  `targets` fallback in `action_host_slugs()` raises
  `MissingSshHostSlugsError`; ledger-only actions keep the fallback.
- **The invariant test** (`tests/test_reconcile_ssh_invariant.py`): for each
  registered reconciler with a handler, a representative action is executed
  through the real handler with a recording `CommandRunner`; every host
  actually contacted (`--limit` values, dnsmasq `host_limit`) is asserted
  equal to `action_host_slugs(action)`, and `connects_over_ssh` is asserted
  true iff something was contacted. Stubbed seams and their justification are
  documented in the test module docstring (ledger/Job transport has no path to
  a CommandRunner; dnsmasq's `host_limit` contract is pinned by
  `test_dnsmasq_apply.py`). A registry sweep asserts every reconciler is
  either executable or explicitly plan-only (`new_node_baseline`).

### Step 4 — docs and skill

- `nctl/docs/add-and-retire-proxmox-lxc.md`: new §"Recovering a
  created-then-orphaned guest (incident F3)".
- `nctl/docs/reconcile.md`: SSH preflight section rewritten around the
  registry derivation + invariant test; new §"Compute evidence routing and
  retired nodes".
- `.claude/skills/retire-proxmox-lxc/SKILL.md` (version 3): the
  "realized compute instance in a prior session … stop before Step 1" clause
  is replaced by the in-skill "Unrealized guest recovery";
  `nctl reconcile GUEST --yes` and
  `nctl reconcile CONTROL_NODE --refresh-observation --yes` added to permitted
  commands; the `compute_instance_missing` / zero-destroy-plan branch rows now
  route into the recovery instead of "precondition failure — stop";
  `last_verified: 2026-08-10`, `verified_against: 7782d72 (+ no_guest_vm fix,
  working tree at verification)`.
- `pj-clusterintent/README.md` §"Retiring one Proxmox LXC": one sentence.

### Acceptance tests (plan §4, required)

- (a) `test_stale_platform_observation_also_routes_refresh_to_control_node`
- (b) `test_present_guest_plans_exactly_one_destroy_gated_on_control_node`
- (c) `tests/test_reconcile_ssh_invariant.py`
- plus `test_orphaned_guest_routes_evidence_refresh_to_control_node` (the F3
  shape itself) and retired-suppression tests.

`uv run pytest -q` in `nctl/`: **1316 passed**.

## 2. Environment incident during execution (worth its own record)

The first `nctl reconcile aghub --refresh-observation --yes` **failed with the
incident's own signature**: the `Ingest Nodeutils Inventory` job stayed
`pending` for 5 minutes and timed out. Diagnosis: the local Nautobot celery
worker was online (ping OK, kombu binding present) but had consumed nothing
for ~28 h while 2 messages sat in the `default` queue — a stuck consumer
connection. `docker restart nautobot-nautobot-worker-1` drained the queue
immediately (scratch-environment restart per `.local/localenv_memo.md`).

This is very likely what "events 9–16 all pending" in the original incident
actually were: not a slow job, a stalled worker. It also means F3-class
orphans are *expected* to recur in this environment — which is exactly what
the shipped fix is for.

## 3. Live reproduction and recovery

Baseline: no orphan existed (hypervisor held only VMID 108). The incident's
leftover `agdoomed1` desired rows were still present; `nctl prune agdoomed1
--yes` removed them cleanly (eligible; the in-system tail of the original
incident is now closed with supported commands only).

**Attempt 1 — `agdoomed2`, vmid 112 (exact mid-poll kill).** Declared,
created through `nctl reconcile agdoomed2 --yes`, and the process was
`kill -9`'d during `job_poll: pending` — the incident's exact death point.
But the worker was healthy, so the already-queued ingest landed *after* the
kill and the guest appeared in Actual State as `compute_instance_not_linked`
(not the orphan). Useful anyway:

- The retirement that followed live-validated §0.4 and acceptance (b): the
  destroy was planned for the **unlinked** guest (matched by vmid), gated on
  `aghub` only, executed, repeat plan empty, prune eligible → pruned.

**Attempt 2 — `agdoomed3`, vmid 113 (faithful orphan).** Deviation from the
plan's "agdoomed2": re-using slug/vmid was impossible without a ledger
hand-edit, because the first prune left an *unlinked* `VirtualMachine` row
(presence `absent`) in Actual State which re-bound to any re-declared
`agdoomed2` by vmid/name (see finding G2). With the worker stopped
(simulating the stall diagnosed in §2), `nctl reconcile agdoomed3 --yes`
created LXC 113, collected and retrieved the report, and the ingest job
submission failed (HTTP 503, no worker); the run ended `non_converged`.
Deviation: the ingest never landed because submission failed rather than
because the poller was killed — the terminal state is identical to the
incident's (guest on hypervisor, nothing in Actual State), and attempt 1
already exercised the literal mid-poll kill. Worker restarted; orphan
confirmed:

- hypervisor: `[(108, agdnsmasq), (113, agdoomed3 running)]`
- drift: `compute_instance_missing` — the exact F3 dead-end state.

**Recovery, entirely from the guest's own scope:**

1. Retirement batch applied (`lifecycle: retired`, `desired_presence: absent`).
2. `nctl reconcile agdoomed3 --allow-destroy` (dry): plan =
   **one `observe_node:compute-evidence` action targeting `aghub`**, none on
   the guest, `ssh_preflight: [('aghub','ready')]`. On the old code this plan
   was a guest-gated `observe_node` failing `ssh_host_key_unenrolled`.
3. `nctl reconcile agdoomed3 --allow-destroy --yes` — one command:
   round 0 ran the control-node observation + ingest; round 1 planned and ran
   `destroy_compute_instance:agdoomed3` plus post-actuation observation. All
   actions succeeded.
4. Repeat dry plan: zero actions (no second destroy). `nctl prune agdoomed3
   --yes` → `pruned`. Hypervisor back to `[(108, agdnsmasq)]`; no `agdoomed*`
   target remains in drift.

Prohibition compliance: no `pct destroy` or any direct hypervisor write was
used at any point (including cleanup); no Nautobot ledger row was hand-edited;
`--allow-destroy` was only ever used host-scoped to the one planned guest.
Infrastructure interventions outside `nctl`: the read-only
`nodeutils-pvesh-read` ground-truth checks (plan §6) and the scratch-env
worker stop/restart (§2, simulating and fixing the stall).

### Terminal-state nuance vs plan §4 "recover to `converged`"

Both retirements ended `manual_intervention_required` rather than `converged`,
with the destroy and observation fully succeeded and prune eligible. The
blocker is `no_realized_object` (error): a throwaway guest that never
completed manual initial access has no realized Device, and that policy diff
persists on the retired node until prune removes the rows. This is independent
of the F3 fix (the `agscratch1` precedent was presumably a realized guest).
The honest completion signal for a never-realized guest's retirement is
therefore: destroy action succeeded + `compute_instance_removal_complete` in
drift + repeat plan empty + prune `eligible` → `pruned` — which is what the
skill's success evidence effectively checks (zero-action repeat plan, pruned).

## 4. Findings for future episodes (not fixed here)

- **G1 — worker queue stall** (§2): the local Nautobot worker can silently
  stop consuming while healthy-by-healthcheck; every ingest then times out
  pending. This manufactured the original incident and recurred today. No
  in-system detector exists.
- **G2 — prune leaves unlinked Actual VM tombstones**: prune deletes only
  *linked* Actual roots (`realized_vm`). A guest destroyed while unlinked
  leaves a `VirtualMachine` row (presence `absent`) that later re-binds by
  vmid/name to a re-declared node of the same name/vmid, blocking re-creation.
  Hit twice today (`agdoomed2` vmid 112 row, and now an `agdoomed3` vmid 113
  row, both still in the scratch ledger).
- **G3 — active unrealized guest under stale platform observation still
  bootstrap-gated**: before creation, an *active* declared guest whose
  platform observation is stale gets both a guest-targeted `observe_node`
  (unenrolled → round fails) and the new control-node refresh. Retired guests
  are fixed (Step 2); the active-bootstrap variant remains and is worked
  around by refreshing the control node first. Pre-existing behavior, now
  narrower.
- Root cause 5 (orphaned `state: running` operations) remains tracked as F4
  in the turn2 report; today added more such records (the killed runs).

## 5. Uncommitted changes (for review/commit)

In `nctl/` (submodule, on `7782d72`):
`src/nctl_core/reconcile/{registry,reconcilers,ssh_preflight,planner,executor}.py`,
`tests/{test_reconcile_planner,test_reconcile_executor,test_ssh_preflight}.py`,
`tests/test_reconcile_ssh_invariant.py` (new),
`docs/{reconcile,add-and-retire-proxmox-lxc}.md`.

In the superproject: `README.md`,
`.claude/skills/retire-proxmox-lxc/SKILL.md`, `devdocs/vision/fix/no_guest_vm/`
(this report). Operation evidence: `01KZN5SB98…` (orphan-creating run),
`01KZN5EJRR…` (mid-poll kill), recovery/destroy/prune envelopes under
`~/.local/state/nctl/events/` and `.local/agdoomed3-*.json`.
