# Retire core Phase 4 — implementation plan: execute bounded LXC destruction

Parent: [roadmap.md](../roadmap.md) — Phase 4. Predecessors: [p0/report.md](../p0/report.md),
[p1/report.md](../p1/report.md), [p2/report5.md](../p2/report5.md), [p3/report.md](../p3/report.md).

Status: proposed. nctl + ansible_agdev only. One CLI option, one permission input, one refusal gate,
one dispatch entry, one action handler, one small playbook, one live acceptance run. No nintent,
nauto, or nodeutils change, no migration, no drift or planner change.

## 1. Goal

Make the destroy action Phase 3 already plans executable — exactly once, only when explicitly
enabled, and only against the planned VMID on the planned control host.

```text
current
  destroy_compute_instance is planned with pinned parameters
  + no dispatch handler, so --yes fails it as unknown_reconciler and mutates nothing
  + no --allow-destroy, no playbook, no pct call anywhere

after Phase 4
  nctl reconcile HOST                        -> plan shows the destroy action, mutates nothing
  nctl reconcile HOST --allow-destroy        -> still a dry plan
  nctl reconcile HOST --yes                  -> destroy refused: capability not enabled
  nctl reconcile HOST --allow-destroy --yes  -> destroys the planned LXC, re-observes the control
                                                node, ingests absence, converges
  repeat                                     -> removal_complete, no action
```

## 2. Frozen inputs from Phase 0

| Input | Value |
|---|---|
| CLI option | `--allow-destroy` (no `nctl dispose`, no second prompt/token/delay/approval record) |
| permission seam | one `allow_destroy: bool` input to `run_reconcile` and the round executor; **no new plan field** |
| reconciler | `destroy_compute_instance` / `compute_destroy`, phase `bootstrap`, `mutates=true`, `requires_observation=true` |
| action parameters | already implemented and unchanged (Phase 3): instance/node/platform/cluster/VM ids, node + platform + control-node slugs, `guest_type=lxc`, `vmid`, observed Proxmox node, `host_slugs=[control-node]` |
| adapter seam | `nctl compute_destroy handler -> playbooks/proxmox/destroy_lxc.yml -> pct -> controller-owned result artifact` |
| re-resolution | the handler re-derives the candidate from the **round snapshot** and requires the pinned parameters to match, following the create handler |
| SSH set | `destroy_compute_instance` joins the SSH-requiring reconciler set |
| post-action observation | ordinary `requires_observation` path on `host_slugs` (the Proxmox control node), not the destroyed guest |
| Actual absence | written only by nodeutils observation + nauto ingest; never by the destroy handler |

Exact `pct` shape, stopped/running handling, and result JSON keys are this plan's choices.

## 3. Findings that shape the plan

Measured on the checked-out tree (superproject `1e4eba5`, nctl `a3a01ec`, nintent `7c88023`,
nauto `6462ebc`, nodeutils `775ed7f`) on 2026-07-30.

**F1 — plan mode needs no permission logic at all.** `_run_plan_only`
([executor.py:165-206](../../../../../../nctl/src/nctl_core/reconcile/executor.py#L165-L206)) never
calls `execute_action`. `--allow-destroy` therefore only has to reach `_run_apply` /
`_execute_round`; "plan mode never mutates, with or without the option" is already structurally
true and only needs a test.

**F2 — one dispatch entry is the entire difference between inert and live.** `_HANDLERS`
([dispatch.py:15-23](../../../../../../nctl/src/nctl_core/reconcile/actions/dispatch.py#L15-L23))
has no destroy entry and `execute_action` turns that into a failed, non-mutating
`unknown_reconciler` result. Adding the entry makes the action real; the refusal gate must therefore
land in the same change, not after it.

**F3 — a refused destroy must be terminal, or the run reports the wrong reason.** If refusal is only
a failed `ActionResult` and the destroy is the round's only action, the loop falls through to the
fingerprint check and ends as `non_converged` / `no_progress`
([executor.py:281-284](../../../../../../nctl/src/nctl_core/reconcile/executor.py#L281-L284)) —
technically true, actively misleading. §4.1 makes it a terminal round error with its own code.

**F4 — post-destroy observation already exists.** `_execute_round` builds one
`post_actuation_observation` over `action_host_slugs()` of every `requires_observation` action
([executor.py:577-604](../../../../../../nctl/src/nctl_core/reconcile/executor.py#L577-L604)).
Because Phase 3 pinned `host_slugs=[control-node]`, the destroyed guest is never a target and the
Proxmox control node always is. No new observation code, no new command.

**F5 — truthful partial progress already exists.** `had_side_effects` plus the failure-path drift
refresh and `final_drift_unknown`
([executor.py:381-394](../../../../../../nctl/src/nctl_core/reconcile/executor.py#L381-L394))
already cover "destroyed, then observation failed" — provided the handler reports `mutated=True`
whenever the `pct` boundary was reached. That is a handler obligation, not an executor change.

**F6 — `create_compute_instance` is missing from the SSH-requiring set.**
`SSH_REQUIRING_RECONCILER_IDS`
([ssh_preflight.py:49](../../../../../../nctl/src/nctl_core/reconcile/ssh_preflight.py#L49)) omits
it even though its handler runs `ansible-playbook` over SSH. Phase 0 requires destroy to be in the
set: add destroy, leave create alone, and record the asymmetry as a known pre-existing gap rather
than widening this phase.

**F7 — the create handler is the whole template.**
[compute_create.py](../../../../../../nctl/src/nctl_core/reconcile/actions/compute_create.py):
re-derive → compare pinned parameters → `mkdir` the result path *before* the irreversible command →
run the playbook → every post-command failure carries `mutated=True`. Copy this shape; do not invent
a second actuation idiom.

**F8 — the live destroy is single-shot.** Phase 3's F7 stands: after removal, the retained absent VM
row and `realized_vm_id` keep `derive_compute_creations` from ever recreating `agfixture`
([compute_creation.py:28](../../../../../../nctl/src/nctl_core/drift/compute_creation.py#L28)). One
fixture buys exactly one live destruction. §4.6 decides who spends it.

**F9 — the inert test must be inverted, not deleted.**
[test_compute_actuation_inert.py:95-101](../../../../../../nctl/tests/test_compute_actuation_inert.py#L95-L101)
asserts that no `--allow-destroy`, no `pct`, and no handler exist. Phase 4 replaces it with the
positive capability assertions (§4.7).

## 4. Design decisions

### 4.1 CLI option, permission plumbing, refusal

- `--allow-destroy` on `nctl reconcile`
  ([main.py:345](../../../../../../nctl/src/nctl_core/cli/main.py#L345)), passed as
  `allow_destroy=` to `run_reconcile`, threaded to `_run_apply` and `_execute_round`. Nothing else
  in the signature chain changes.
- Record `allow_destroy` on `ReconcileData` beside `mode`. It is operation evidence — what capability
  the run actually had — not a plan permission field.
- **Refusal**, in the bootstrap loop of `_execute_round`, before `execute_action`: if
  `action.reconciler_id == "destroy_compute_instance"` and not `allow_destroy`, append a failed
  `ActionResult` with `mutated=False` and error code `destroy_capability_not_enabled`, then return
  `RoundOutcome` with the same code as a terminal error (F3). Actions that already ran this round
  stay in `summary`.
- The gate keys on the reconciler id — not `mutates`, not `action_kind`. No other action changes
  meaning, and no plan is rebuilt or filtered.
- The refusal message names the remediation: rerun with `--allow-destroy --yes`.

### 4.2 The handler

New `reconcile/actions/compute_destroy.py`, registered as
`ActionHandler("destroy_compute_instance", compute_destroy.execute, "bootstrap", False)`
(no Nautobot client needed). Following F7:

1. `derive_compute_dispositions(context.snapshot, generated_at=context.generated_at)` for the action
   target; require `outcome == "destroy_required"` and `parameters == action.parameters`. Anything
   else is a failed, `mutated=False` result: *"destroy parameters no longer match the pinned
   disposition"*. This is the whole re-resolution contract — same round snapshot, same pure
   derivation the plan used.
2. Create the result-artifact parent, then run
   `ansible-playbook -i <inventory> playbooks/proxmox/destroy_lxc.yml --limit <control-node slug>
   --extra-vars <parameters + result_path>`.
3. Non-zero exit, missing result file, unparseable result, or a result that does not confirm absence
   → failed with `mutated=True`.
4. Success requires the result to confirm the guest is absent. `mutated` reflects whether a destroy
   actually ran: an already-absent guest is a truthful success with `mutated=False`.
5. `actuation_result(..., requires_observation=True)` so F4's observation follows.

Extra playbook variables (`result_path`, and optionally an expected guest name derived from the
round snapshot's realization) are handler-local. They are **not** additions to the frozen action
parameter set.

### 4.3 `playbooks/proxmox/destroy_lxc.yml`

Mirror the shape of `create_lxc.yml`: one host, `gather_facts: false`, `become` overridable via
`nctl_compute_become`, `pct_binary: /usr/sbin/pct` as the only indirection, explicit `argv` lists.

Tasks, in order:

1. probe `pct status <vmid>` — non-zero rc means already absent and skips the destroy;
2. optionally verify the guest's identity (e.g. `pct config <vmid>` hostname against the expected
   name) and fail before destroying on a mismatch — recommended, since VMID reuse is the one way
   this playbook could hit the wrong guest;
3. `pct stop <vmid>` when it is running, tolerating already-stopped;
4. `pct destroy <vmid>`;
5. re-probe `pct status <vmid>` and fail unless it now reports absent;
6. write the result JSON (e.g. `{"destroyed": true, "absent": true}`) with `delegate_to: localhost`,
   mode `0600`.

The VMID always comes from `--extra-vars`. No loop, no host pattern, no `--all`, no `qm`, no
snapshot/backup/migrate/clone task, no second guest reachable from this playbook.

### 4.4 SSH and observation

Add `"destroy_compute_instance"` to `SSH_REQUIRING_RECONCILER_IDS` so an unenrolled control node
stops the round before `pct` runs. Leave the mDNS scan set (`observe_node` only) alone. Record F6.

Observation and absence ingest are untouched: the control-node observation is already planned by
F4, and nauto's complete-observation absence path shipped in Phase 2. Phase 4 adds tests, not code,
here.

### 4.5 Partial progress

No executor change (F5). Cover it with a test: destroy succeeds, the post-actuation observation
fails, and the run reports failure with the mutation recorded and the final drift refreshed or
explicitly `final_drift_unknown` — never a converged claim.

### 4.6 Who spends the fixture — decide at the live step

The roadmap gives Phase 4 the exit criterion *"explicitly enabled apply destroys exactly the planned
disposable LXC"*, and Phase 0 gives Phase 5 *"one explicitly designated disposable-LXC acceptance
run"*. By F8 those cannot both be a first live destruction of `agfixture`.

**Decision: Phase 4 performs the one live destroy of `agfixture`** (Step 5), and hands Phase 5 the
choice of either treating this run's evidence as the acceptance run — focusing Phase 5 on the
automated control-loop test, the incomplete-observation case, and documentation — or declaring a
second disposable fixture. Raise this with the operator at the Step 5 approval gate; if they prefer
to reserve `agfixture` for Phase 5, Step 5 stops after the refusal proof and Phase 4 reports as
`implemented, not deployed`.

### 4.7 Test-surface inversion

Replace F9's negative assertions with positive ones: `handler_for("destroy_compute_instance")` is
not `None`; `--allow-destroy` exists on the CLI; `destroy_lxc.yml` exists and contains only the
§4.3 task set; and the create playbook still contains no destroy verb
([test_compute_create.py:146](../../../../../../nctl/tests/test_compute_create.py#L146) keeps its
`pct destroy` prohibition — the two playbooks stay separate).

### 4.8 Explicitly unchanged

Drift, the disposition derivation, classification, the planner, the action schema, the DAG, the
round loop, the create handler and playbook, `nctl lifecycle`, the canonical writer, and every
nintent / nauto / nodeutils surface.

## 5. Steps

Merge or split freely. The only hard ordering constraint is that §4.1's refusal gate lands in the
same commit as §4.2's dispatch entry, so no tree state exists where a bare `--yes` can destroy.

### Step 0 — Baseline

Record the revision tuple, the fixture's current Desired/Actual state and drift, and the current dry
`nctl reconcile agfixture` plan. Read-only.

*Exit:* the before-picture Step 5 compares against.

### Step 1 — Permission plumbing and refusal

Implement §4.1 and §4.4. Tests: plan mode mutates nothing with and without the option; `--yes`
without the option produces exactly one refused, non-mutating destroy result plus the
`destroy_capability_not_enabled` terminal error and no `ansible-playbook` invocation; unrelated
actions in the same round still execute and survive in the round summary; an unenrolled control node
blocks the destroy round before any command runs.

*Exit:* the capability exists and defaults to off; nctl ordinary suite passes.

### Step 2 — The playbook

Implement §4.3 in `ansible_agdev`. Add a Tier A case to
[test_ansible_conformance.py](../../../../../../devtests/test_strategy/test_ansible_conformance.py)
mirroring the create case: real playbook, disposable `pct` stub, assert the exact argv sequence for
a running guest, for an already-absent guest, and that the result artifact is written locally.

*Exit:* Ansible conformance passes; the playbook's reachable command set is exactly §4.3's.

### Step 3 — The handler

Implement §4.2. Tests: happy path (argv, `--limit`, result path, `mutated=True`,
`requires_observation=True`); parameter/disposition drift refuses before the runner starts;
non-zero exit, missing result, invalid JSON, and unconfirmed absence each fail with `mutated=True`;
already-absent succeeds with `mutated=False`; §4.5's destroy-then-observation-failure case.

*Exit:* the destroy path is executable only under the Step 1 capability; nctl ordinary suite passes.

### Step 4 — Invert the surface tests

Implement §4.7.

*Exit:* no test still asserts the absence of the destroy capability.

### Step 5 — Live acceptance on `agfixture`

**Operator approval required before this step, and again before the destroying command.** Confirm
§4.6 first. Read-only verification between every command.

1. Canonical-writer atomic batch: `agfixture` node → `retired`, its compute instance →
   `desired_presence=absent`.
2. `nctl reconcile agfixture` — one destroy action with the real pinned IDs, no mutation.
3. `nctl reconcile agfixture --allow-destroy` — same plan, still no mutation.
4. `nctl reconcile agfixture --yes` — destroy refused with `destroy_capability_not_enabled`; verify
   the LXC still exists.
5. `nctl reconcile agfixture --allow-destroy --yes` — the LXC is destroyed, the control node is
   re-observed, nauto records `proxmox_presence=absent` on the same VirtualMachine row, the Device
   row is retained, and the compute target converges.
6. Repeat step 5's command — `compute_instance_removal_complete`, no destroy action, no second
   `pct` call.
7. Record the node-target behaviour (Phase 3's F8) and the operation ids for every run above.

*Exit:* one planned destroy was executed exactly once and freshly proven absent — or, under the
§4.6 alternative, the refusal proof is complete and the destruction is deferred with that stated.

### Step 6 — Gates and report

Run and state case counts for: nctl ordinary, Ansible conformance, and compute conformance (or state
why it does not apply). State explicitly that nintent, nauto, nodeutils, and the Nautobot runtime
gates do not apply because no such surface changed — say it rather than omitting it. Write
`p4/report.md` with the revision tuple, F6 and F8 as recorded limitations, the §4.6 outcome, the
Step 5 evidence, gate results, the Phase 5 handoff, and one precise status.

*Exit:* one status of `complete`, `partially complete`, `implemented, not deployed`, or `blocked`,
with every omitted check visible.

## 6. Exit criteria

1. Plan mode performs no mutation, with or without `--allow-destroy`.
2. `--yes` without `--allow-destroy` never reaches `pct`, and reports the capability as not enabled
   with its own error code.
3. `--allow-destroy --yes` destroys exactly the planned VMID on the planned control host, via the
   pinned playbook, and nothing else.
4. The handler refuses when the round snapshot no longer re-derives the pinned destroy parameters.
5. A successful destroy is followed by the ordinary control-node observation, and Actual absence is
   written only by nauto ingest.
6. Destroy-then-observation-failure reports the mutation truthfully and never claims convergence.
7. After complete absence observation, a repeated reconcile plans and executes no destroy.
8. `destroy_compute_instance` requires SSH enrollment of the control node.

## 7. Boundaries

Prohibitions, minimal:

1. **Destruction is opt-in per run.** No config default, environment variable, or persisted setting
   may enable `--allow-destroy`.
2. **One guest per action.** The playbook and handler act on the single pinned VMID on the single
   pinned control host — never a pattern, list, wildcard, or cluster scope.
3. **The handler never writes Actual state.** Absence comes from observation + ingest only.
4. **No mutation outside the enabled apply path.** Plan mode, refused runs, and preflight failures
   touch nothing.
5. **No new safety machinery.** No prompt, token, delay, retention timer, approval record, or
   protection field beyond the option and the existing `--yes`.
6. **No push, no deploy.** Local commits in `nctl` and `ansible_agdev` are yours; pushing and the
   superproject pointer move are the operator's.
7. **Ask before Step 5**, and again before the destroying command.

Everything else is yours: module and function names, error message wording, result JSON keys, how
the identity guard is implemented, `pct` flag choices, test structure, commit granularity, and step
count. Scratch Nautobot reads, drift runs, dry reconcile runs, and stubbed `pct` runs need no
approval.
