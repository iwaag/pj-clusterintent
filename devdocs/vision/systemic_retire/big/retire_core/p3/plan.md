# Retire core Phase 3 — implementation plan: make compute drift retirement-aware

Parent: [roadmap.md](../roadmap.md) — Phase 3. Predecessors: [p0/report.md](../p0/report.md),
[p1/report.md](../p1/report.md), [p2/report5.md](../p2/report5.md).

Status: proposed. nctl only. One pure disposition derivation, one evaluator branch, three drift
codes, one reconciler registration, one planner group. No nintent change, no nauto change, no
migration, no deploy, no action handler, no CLI option, no Proxmox call.

## 1. Goal

Turn retirement plus explicit absence into an ordinary desired-vs-actual result, and produce the
destroy action candidate — without being able to execute it.

```text
current
  desired_presence is read and shown, but never interpreted
  + an absent VM row still matches as an ordinary present realization
  + ordinary comparisons run against a removed guest's retained fields
  + no destroy code, no destroy action, no retirement gate on link

after Phase 3
  one pure disposition per compute instance, shared by drift and the planner
  + compute_instance_destroy_required / compute_instance_removal_complete
  + a retired instance plans no create, start, link, or resource correction
  + destroy_compute_instance is registered and planned with pinned parameters
  + still zero executable destroy path: no handler, no --allow-destroy, no pct
```

Phase 4 owns execution. Phase 3 must not anticipate it.

## 2. Frozen inputs from Phase 0

| Input | Value |
|---|---|
| new codes | `compute_instance_destroy_required` (warning, automatic) and `compute_instance_removal_complete` (info, no action) |
| reused codes | `compute_instance_missing`, `compute_platform_observation_stale`, `compute_realization_summary` |
| reconciler | `destroy_compute_instance` / `compute_destroy`, phase `bootstrap`, `mutates=true`, `requires_observation=true` |
| action target | the exact `compute_instance` target; never widened |
| action parameters | DesiredComputeInstance id; DesiredNode id + slug; DesiredComputePlatform id + slug; Cluster id; VirtualMachine id; guest type `lxc`; VMID; observed Proxmox node; control DesiredNode id + slug; `host_slugs` = [control-node slug] only |
| planner gate | retired ∧ absent ∧ trustworthy platform observation ∧ present realization ∧ proxmox ∧ container ∧ lxc ∧ agreeing platform/VM/VMID identity |
| retired + present | retained realization; no create, start, destroy, link, power, or resource-correction action |
| out of Phase 3 | `--allow-destroy`, `run_reconcile` permission input, action handler, playbook, any Proxmox write |

## 3. Findings that shape the plan

Measured on the checked-out tree (superproject `3faa1f3`, nintent `7c88023`, nauto `6462ebc`,
nctl `13ae1cd`, nodeutils `775ed7f`) on 2026-07-30.

**F1 — the create path is already retirement-safe; pin it, do not build it.**
`derive_compute_creations` skips any instance whose `effective_lifecycle` is not `approved`/`active`
([compute_creation.py:35](../../../../../../nctl/src/nctl_core/drift/compute_creation.py#L35)), so a
retired instance can never become a create candidate. Phase 3's "plans no create" exit criterion is
a regression test, not new code.

**F2 — the link path is *not* retirement-aware.** `compute_instance_not_linked` is classified
`AUTOMATIC` → `link_compute_realization`
([classify.py:195](../../../../../../nctl/src/nctl_core/reconcile/classify.py#L195)), with no
lifecycle or presence condition in `plan_link_compute_realization`
([reconcilers.py:129-167](../../../../../../nctl/src/nctl_core/reconcile/reconcilers.py#L129-L167)).
A retired, explicitly absent instance whose guest is still observed but unlinked would today plan a
ledger link. Phase 3 must suppress this. The destroy action does not need the link first: it carries
`virtual_machine_id` from the same typed realization.

**F3 — presence is projected but not interpreted.** Phase 2 added
`ProxmoxVirtualMachineFacts.presence`
([actual.py:345](../../../../../../nctl/src/nctl_core/sources/actual.py#L345)) and put it on the
actual side of `compute_realization_summary`
([compute_evaluation.py:140](../../../../../../nctl/src/nctl_core/drift/compute_evaluation.py#L140)),
but `_match_instance` matches by link, VMID, then name regardless of presence
([compute_realization.py:90-109](../../../../../../nctl/src/nctl_core/drift/compute_realization.py#L90-L109)).
That matching is correct and must stay — the retained row is how a removed guest is still identified.
What changes is that a matched row is no longer automatically a *present* realization.

**F4 — every ordinary comparison of an absent guest is stale by construction.** Power state, vCPU,
memory, root disk, rootfs storage, bridge, and endpoint MAC in `_evaluate_instance`
([compute_evaluation.py:96-123](../../../../../../nctl/src/nctl_core/drift/compute_evaluation.py#L96-L123))
all read retained last-known evidence. Left unguarded, a successfully removed guest reports permanent
`compute_power_state_mismatch` and never converges.

**F5 — planning a destroy with no handler is already safe and truthful.** `dispatch._HANDLERS`
([dispatch.py:15-23](../../../../../../nctl/src/nctl_core/reconcile/actions/dispatch.py#L15-L23))
has no `destroy_compute_instance` entry, and `execute_action` turns a missing handler into an
`unknown_reconciler` failed, non-mutating `ActionResult`
([dispatch.py:40-47](../../../../../../nctl/src/nctl_core/reconcile/actions/dispatch.py#L40-L47)).
So a Phase 3 `reconcile --yes` on a retired+absent target fails that one action and touches nothing.
State this in the report as the deliberate Phase 3 end state; do not add a handler to smooth it over.

**F6 — the absent + non-retired combination has a helper and no consumer.**
`desired_presence_requires_retired`
([contract.py:305](../../../../../../nctl/src/nctl_core/compute/contract.py#L305)) exists but nothing
in nctl calls it. nintent rejects the combination at write time; Phase 1's F5 records that a later
node lifecycle change does not re-run instance validation. Phase 3 owns surfacing that state.

**F7 — a removed guest cannot re-enter the create path, and that is out of scope.**
`derive_compute_creations` skips any instance with a `realized_vm_id` or a matched VM
([compute_creation.py:28](../../../../../../nctl/src/nctl_core/drift/compute_creation.py#L28)), so
flipping `desired_presence` back to `present` after removal will report `compute_instance_missing`
but plan no create while the stale link and retained row remain. Record it as a known limitation;
re-creation is not part of retire core.

**F8 — node-target drift is not lifecycle-aware, and the fixture will show it.**
`service_evaluation` skips `deprecated`/`retired`
([service_evaluation.py:25](../../../../../../nctl/src/nctl_core/drift/service_evaluation.py#L25));
`node_evaluation` has no equivalent. After the fixture's guest is destroyed, its retired DesiredNode
keeps comparing against the retained Device row and will produce guest-OS findings on the `node`
target. Step 0 must measure this; §4.6 decides it.

## 4. Design decisions

### 4.1 One pure disposition, shared by drift and the planner

Add a pure module beside `compute_realization.py` / `compute_creation.py` (suggested
`drift/compute_disposition.py`; the name is yours) exposing
`derive_compute_dispositions(snapshot, *, generated_at) -> dict[instance_id, ComputeDisposition]`.
It consumes `derive_compute_realizations` and returns, per instance, exactly one outcome plus the
pinned destroy parameters when applicable:

| outcome | condition |
|---|---|
| `ordinary` | effective lifecycle not retired, desired presence `present` |
| `presence_conflict` | desired presence `absent`, effective lifecycle not retired (F6) |
| `retained` | retired, desired presence `present` |
| `destroy_required` | retired, absent, realization present, every Phase 0 gate satisfied |
| `removal_complete` | retired, absent, realization absent |
| `unknown` | platform evidence untrustworthy — already short-circuited by `platform_failures` |

This is the only place the combination is decided. Drift renders it; the planner re-derives the same
decision from the typed snapshot rather than reading a diff message, matching the create/link pattern.

**Presence reading rule.** `presence == "absent"` is the sole absent signal. `presence is None` is a
pre-Phase-2 row — treated as present for ordinary comparison, but it does **not** satisfy the destroy
gate: `destroy_required` requires an explicit `"present"`. A `None` under a fresh, complete platform
observation is contradictory evidence, and Phase 3 prefers reporting nothing over guessing.

### 4.2 Evaluator branching

In `_evaluate_instance`, branch on the disposition **before** the existing identity/resource
comparisons:

- `ordinary` — unchanged behaviour.
- `retained` — emit `compute_realization_summary` only. Suppress `compute_instance_not_linked`,
  `compute_power_state_mismatch`, and `compute_resource_mismatch`. Keep
  `compute_identity_conflict`: a retained realization pointing at the wrong guest is still a fact
  worth reporting, and it is manual-review either way.
- `destroy_required` — emit `compute_instance_destroy_required` (warning) plus the summary; suppress
  the same set as `retained` (F4).
- `removal_complete` — emit `compute_instance_removal_complete` (info) plus the summary; suppress
  every comparison against the retained row and suppress `compute_instance_missing`.
- `presence_conflict` — emit `compute_presence_lifecycle_conflict` (warning) **and** continue with
  ordinary comparison. Absence is not authorized, so the instance is still compared as present.

Add `presence` and the disposition outcome to the summary's actual side so one JSON record explains
the decision.

### 4.3 Vocabulary — three codes, not two

Phase 0 froze two. `compute_presence_lifecycle_conflict` is a deliberate third, added because Phase
1's F5 handoff requires the invalid combination to be an ordinary drift finding rather than a crash
or a deletion authorization, and no existing code carries that meaning. It is `warning` /
`MANUAL_REVIEW` / no reconciler. Record it as a named extension of the frozen vocabulary in the
report. If a reviewer prefers zero new codes, the fallback is to fold it into a
`compute_realization_summary` field — but then it never reaches `manual_review`, which is worse.

Severities follow Phase 0. Note in the report that `derive_status` reads error diffs only
([status.py](../../../../../../nctl/src/nctl_core/drift/status.py)), so a target with a pending
destroy stays `converged` while the plan shows the action — the same already-shipped behaviour as
`compute_instance_not_linked`. This is consistency, not a defect, and Phase 3 does not change the
status vocabulary to chase it.

### 4.4 Classification, reconciler, planner

- `classify.py`: `compute_instance_destroy_required` → `AUTOMATIC`, reconciler
  `destroy_compute_instance`. `compute_instance_removal_complete` → info, no error path;
  register it so the planner never treats it as unreviewed.
  `compute_presence_lifecycle_conflict` → `MANUAL_REVIEW`.
- `reconcilers.py`: register `Reconciler(id="destroy_compute_instance",
  action_kind="compute_destroy", mutates=True, requires_observation=True)` and add
  `plan_destroy_compute_instance(target, snapshot, *, generated_at)`. It re-derives the disposition;
  anything short of `destroy_required` is a `Fallback(MANUAL_REVIEW, ...)` naming the failed gate.
  Parameters are exactly Phase 0's frozen set, `host_slugs` = the control node only.
- `planner.py`: one new group loop next to the create group
  ([planner.py:198-203](../../../../../../nctl/src/nctl_core/reconcile/planner.py#L198-L203)).
  The destroy target's slug joins `compute_transition_target_slugs` so no `observe_node` action is
  planned for a node whose guest is about to disappear.
- No `run_reconcile` signature change, no executor change, no dispatch entry.

### 4.5 Link suppression

Gate `plan_link_compute_realization` on the disposition: decline with a `Fallback` for `retired`,
`destroy_required`, and `removal_complete`. Prefer suppressing the diff in the evaluator (§4.2) so
the code never reaches the planner at all, and keep the planner gate as the second line — a plan
built from a stale diff list must still refuse.

### 4.6 F8 — retired node guest-OS drift

**Decision: out of scope, measured and recorded.** Making `node_evaluation` lifecycle-aware is a
guest-OS-realization change that touches every retired node in the cluster, not a compute change.
Step 0 records exactly what the fixture's `node` target reports today and Step 4 records what it
reports after the desired flip; the report states that the `compute_instance` target converges while
the `node` target may remain `unknown`/`drifting` against its retained Device. If that turns out to
block Phase 5's "fresh drift = converged", it becomes a scoped Phase 5 decision with real evidence
behind it, not a speculative Phase 3 change.

### 4.7 Explicitly unchanged

Matching, linking semantics for non-retired instances, `compute_instance_missing` for an ordinary
present instance, the create preflight, the DAG, the action schema, the executor, the CLI, every
render path, and every nintent/nauto surface.

## 5. Steps

Merge or split freely. The only real ordering constraint is that the pure derivation lands before
the planner consumes it.

### Step 0 — Baseline

Record the revision tuple, `nctl drift --json`, the fixture's current compute and node target diffs
and statuses, and the current dry `nctl reconcile agfixture` plan. Read-only; this is the
before-picture Step 4 compares against.

*Exit:* baseline recorded, including the F8 measurement.

### Step 1 — The pure disposition

Implement §4.1 with unit tests over the six outcomes, the `presence=None` rule, and each Phase 0
gate rejected individually (non-proxmox provider, QEMU guest type, `virtual_machine` instance kind,
VMID disagreement, cluster disagreement, untrustworthy platform observation).

*Exit:* the derivation is total — every desired compute instance maps to exactly one outcome; nctl
ordinary suite passes.

### Step 2 — Evaluator

Implement §4.2 and §4.3. Cover every row of the roadmap's reconciliation-semantics table, plus:
suppression of stale comparisons for `retained`/`destroy_required`/`removal_complete`; the
`presence_conflict` path still comparing as present; an unrelated observed guest in the same cluster
staying neutral; and unchanged codes/severities for every existing present-path case.

*Exit:* the semantics table is covered by drift tests; no existing compute drift expectation moved
except by the deliberate suppressions.

### Step 3 — Classification, reconciler, planner

Implement §4.4 and §4.5. Tests: a retired+absent+present target plans exactly one
`destroy_compute_instance` action with the frozen parameters and nothing else; each gate failure
falls back to `manual_review` with a named reason; a retired instance plans no create, no start, no
link, and no observe; `removal_complete` plans nothing; `presence_conflict` reaches `manual_review`;
an unrelated node's plan is byte-identical to before; and the destroy action targets exactly one
`compute_instance`.

Assert positively that `destroy_compute_instance` has **no** dispatch handler and that the tree
contains no `--allow-destroy`, no destroy playbook, and no `pct` invocation — the Phase 3 equivalent
of the inert test.

*Exit:* nctl ordinary suite passes; the destroy path exists only in plans.

### Step 4 — Live dry proof on the fixture

Operator approval required for both desired writes; no Proxmox mutation at any point.

1. Preview and apply an atomic `retired + absent` batch for `agfixture` through the canonical writer.
2. Run `nctl drift --json` and confirm `compute_instance_destroy_required` with the expected
   evidence, no create/link/observe action for the node, and no unrelated drift movement.
3. Run `nctl reconcile agfixture` (plan only) and confirm exactly one `destroy_compute_instance`
   action carrying the frozen parameters and the real IDs.
4. Record the node target's behaviour for F8.
5. Revert `agfixture` to `approved + present` through the same writer and confirm drift returns to
   the Step 0 baseline.

Phase 5 owns the acceptance run; this step only proves the plan is truthful and reversible.

*Exit:* one real destroy plan was produced and withdrawn, with the fixture back at its Phase 5
starting state.

### Step 5 — Gates and report

Run and state case counts for: nctl ordinary pytest and compute conformance. State that no nintent,
nauto, nodeutils, Ansible, or Nautobot-runtime gate applies because no component outside nctl
changed — and say so explicitly rather than omitting them. Write `p3/report.md` with the revision
tuple, the §4.3 third-code extension, F5 (a Phase 3 `--yes` fails the destroy action truthfully), F7
and F8 as recorded limitations, the Phase 4 handoff, gate results, and one precise status.

*Exit:* one status of `complete`, `partially complete`, `implemented, not deployed`, or `blocked`,
with every omitted check visible.

## 6. Exit criteria

1. Every row of the roadmap's reconciliation-semantics table is produced by drift and covered by a
   test.
2. A retired compute instance plans no create, start, link, observe, power, or resource-correction
   action, whatever its desired presence.
3. `compute_instance_destroy_required` appears exactly under the full Phase 0 gate, and each gate
   failure is a named `manual_review` fallback.
4. The planned destroy action carries the frozen parameter set, targets exactly one
   `compute_instance`, and limits `host_slugs` to the control node.
5. `compute_instance_removal_complete` is info-severity and plans nothing.
6. `desired_presence=absent` under a non-retired lifecycle is a visible finding that authorizes
   nothing.
7. No destroy handler, `--allow-destroy`, playbook, or Proxmox call exists anywhere in the tree, and
   a test asserts it.
8. A live retired+absent declaration produced one truthful destroy plan and was reverted, leaving
   the fixture at its Phase 5 starting state.

## 7. Boundaries

Prohibitions, minimal:

1. **No execution path.** No dispatch entry, no handler, no playbook, no `run_reconcile` permission
   input, no CLI option. Phase 4 owns all of it.
2. **No Proxmox mutation and no Actual-row write.** Phase 3 is drift and planning only.
3. **Absence is never inferred.** Only explicit `desired_presence=absent` plus an explicit
   `presence="absent"` may produce a removal outcome; `None`, stale, partial, and missing evidence
   never do.
4. **No widening.** A destroy candidate covers one compute instance and one control host; it never
   groups, batches, or falls back to a cluster scope.
5. **No push, no deploy.** Local commits are yours; pushing nctl is the operator's step.
6. **Ask before writing `agfixture`** — both the retire flip and the revert.

Everything else is yours: module and function names, how the disposition dataclass is shaped, where
the suppression is implemented, code spellings beyond the three named here, test structure and
fixtures, commit granularity, and step count. Scratch Nautobot reads, drift runs, dry reconcile
runs, and test rows need no approval.
