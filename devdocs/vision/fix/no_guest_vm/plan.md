# Plan: make a created-then-orphaned guest reconcilable again

Fixes [`problem.md`](problem.md) (incident F3, LXC 110 `agdoomed1` on `aghub`).

Planned 2026-08-10 against `nctl` `7782d72` (superproject submodule pointer, tree clean).
Destructive phase: no backward compatibility required. Plan schema, reconciler
registry shape, and `SSH_REQUIRING_RECONCILER_IDS` may all change freely.

## 0. Corrections to problem.md — read this first

Four of `problem.md`'s claims do not hold against `7782d72`. They change the
shape of the fix, so verify them yourself before starting.

1. **Proposal A is already implemented.**
   [`compute_disposition.py:90`](../../../../nctl/src/nctl_core/drift/compute_disposition.py#L90)
   already sets `"host_slugs": [control.slug]` in the destroy parameters, and
   [`reconcilers.py:211`](../../../../nctl/src/nctl_core/reconcile/reconcilers.py#L211)
   passes `parameters=disposition.parameters` straight through. So
   `action_host_slugs()` already returns the hypervisor for a destroy action.
   Same for create ([`compute_creation.py`](../../../../nctl/src/nctl_core/drift/compute_creation.py),
   `params = {... "host_slugs": [control.slug] ...}`). Both landed in `aa422a6`
   (2026-07-30), *before* the incident. Root cause 2 is not live. It is still
   untested — Step 3 pins it.

2. **`destroy_compute_instance` is already in the observe-suppression set**
   ([`planner.py:236`](../../../../nctl/src/nctl_core/reconcile/planner.py#L236)).

3. **Root cause 4's premise is wrong.** `snapshot.actual.virtual_machines` is
   populated by the nodeutils collection **on the hypervisor**, not on the
   guest — the same `facts_raw/proxmox/lxc_containers` view the incident read by
   hand. The create action's post-actuation observation already targets
   `host_slugs=[control]` ([`executor.py:618-625`](../../../../nctl/src/nctl_core/reconcile/executor.py#L618-L625)).
   The guest never had to answer SSH for its VM to be linkable. **A
   hypervisor-side linking path already exists; nothing re-requests it once the
   operation that owned it died.** That single sentence is the whole bug.

4. **A ledger link is not required to destroy.**
   `compute_instance_destroy_required` is emitted from the disposition
   ([`compute_evaluation.py:110`](../../../../nctl/src/nctl_core/drift/compute_evaluation.py#L110)),
   and `_match_instance` matches an unlinked guest by vmid, then by name
   ([`compute_realization.py:100-109`](../../../../nctl/src/nctl_core/drift/compute_realization.py#L100-L109)).
   A fresh hypervisor guest list is sufficient — link first, then destroy, is
   not needed.

## 1. Recovery that works today (no code change)

Confirm this by hand first; it is also the acceptance baseline.

```bash
uv run --project nctl nctl reconcile CONTROL_NODE --refresh-observation --yes
uv run --project nctl nctl reconcile GUEST --allow-destroy          # dry: expect one destroy action
uv run --project nctl nctl reconcile GUEST --allow-destroy --yes
uv run --project nctl nctl prune GUEST --yes
```

`--refresh-observation` forces an `observe_node` on `CONTROL_NODE` even when it
is converged ([`executor.py:776-821`](../../../../nctl/src/nctl_core/reconcile/executor.py#L776));
that re-collects the guest list, the ingest lands, the orphan appears in Actual
State, and the destroy plans normally. It requires host scope and an enrolled
`CONTROL_NODE` — both true for `aghub`.

The fix below is about making that recovery *reachable from the guest's own
scope*, so the operator does not have to know it.

## 2. Steps

### Step 1 — route a compute-backed node's evidence refresh to its hypervisor

Today `nctl reconcile GUEST` plans `observe_node` on the guest, which is
SSH-gated on a host that may never answer. The evidence that actually resolves a
missing/unlinked compute instance lives on the control node.

In [`planner.py`](../../../../nctl/src/nctl_core/reconcile/planner.py): when a
scoped compute instance has no `virtual_machine` in its realization, plan an
`observe_node` action targeting **the platform's control node**, with
`parameters["host_slugs"] = [control_node_slug]`.

- Recommended narrowing: plan it only when no `create_compute_instance` action
  was planned for that instance (i.e. the create fell back to manual_review, or
  the node is retired). That leaves the ordinary create path at its current
  round count.
- This deliberately actuates a node outside `scope.host_slug`. That is the
  point, and it is a read-only collection. Record the decision in the report.
- Loop guard already exists: an observation that changes nothing leaves the
  drift fingerprint unchanged and the run ends `non_converged` /`no_progress`
  ([`executor.py:296`](../../../../nctl/src/nctl_core/reconcile/executor.py#L296)) —
  a truthful outcome, not a hang. You do not need to invent a "tried once" flag.

**Trap:** `_with_forced_observation` raises `ForcedObservationScopeError` when an
`observe_node` action carries any slug other than the scoped host
([`executor.py:796-801`](../../../../nctl/src/nctl_core/reconcile/executor.py#L796-L801)).
A control-node observation action will trip it under
`reconcile GUEST --refresh-observation`. Either keep it as a separate action
whose targets never include the scoped host and make that function skip actions
not containing the scoped node, or fold the two. Your call; add a test either way.

### Step 2 — never plan `observe_node` for a node that cannot answer

Extend the suppression at
[`planner.py:233-245`](../../../../nctl/src/nctl_core/reconcile/planner.py#L233-L245):
in addition to `compute_transition_target_slugs`, drop any observe target whose
effective lifecycle is `retired` (`compute.contract.effective_lifecycle`, as used
by [`compute_disposition.py:35`](../../../../nctl/src/nctl_core/drift/compute_disposition.py#L35)).
A retired node's evidence gaps stay visible in drift; they just stop producing an
SSH-gated action that can only fail. Node evidence evaluation does not currently
filter on lifecycle at all — that is why the incident's plan contained
`observe_node` for an already-retired guest.

### Step 3 — one machine-readable home for "which hosts does this action SSH to"

This is `problem.md`'s proposal B, and the only step that stops the recurrence
rather than the instance. Three structures hand-encode the same fact today
(`problem.md` §Root cause 1).

- Derive `SSH_REQUIRING_RECONCILER_IDS`
  ([`ssh_preflight.py:49`](../../../../nctl/src/nctl_core/reconcile/ssh_preflight.py#L49))
  from the reconciler registry
  ([`reconcilers.py:47-76`](../../../../nctl/src/nctl_core/reconcile/reconcilers.py#L47-L76))
  instead of hand-writing it — e.g. a `connects_over_ssh: bool` field on
  `Reconciler`.
- Make every SSH-connecting reconciler set `parameters["host_slugs"]`
  explicitly, and make the silent `targets` fallback in `action_host_slugs()`
  ([`ssh_preflight.py:101-104`](../../../../nctl/src/nctl_core/reconcile/ssh_preflight.py#L101-L104))
  an error for those reconcilers. That fallback is what made the destroy gate
  *look* wrong to the incident reviewer even though the parameter was set.
- **The invariant test.** For each registered reconciler, build a representative
  action from fixtures, execute the handler with a fake `command_runner` and
  ssh probe, collect every host actually contacted (`ansible-playbook --limit`,
  keyscan/ssh targets), and assert it equals `action_host_slugs(action)`; assert
  `connects_over_ssh` is false iff nothing was contacted. This is where the
  already-correct destroy `host_slugs` finally becomes falsifiable.

Existing tests to extend rather than duplicate:
`tests/test_compute_destroy.py`, `tests/test_compute_create.py`,
`tests/test_reconcile_planner.py`, `tests/test_ssh_preflight.py`,
`tests/test_reconcile_ssh_preflight.py`.

### Step 4 — documentation and the retirement skill

- [`nctl/docs/add-and-retire-proxmox-lxc.md`](../../../../nctl/docs/add-and-retire-proxmox-lxc.md)
  and [`nctl/docs/reconcile.md`](../../../../nctl/docs/reconcile.md): record the
  orphan case and its recovery.
- [`.claude/skills/retire-proxmox-lxc/SKILL.md`](../../../../.claude/skills/retire-proxmox-lxc/SKILL.md):
  its "Prerequisite — realized compute instance … stop before Step 1 and return
  the task to a human" clause exists *because of* this bug. Replace it with the
  recovery, add `nctl reconcile CONTROL_NODE --refresh-observation --yes` to the
  permitted commands, bump `verified_against` / `last_verified`.
- `pj-clusterintent/README.md` §"Retiring one Proxmox LXC": one sentence.

## 3. Explicitly not doing

- **Proposal C as written** (a separate hypervisor-side linking path). The
  nodeutils/ingest collection on the control node already *is* that path — see
  §0.3. Step 1 makes it re-requestable, which is the actual missing piece.
- **Root cause 3 ("actuated but unlinked" state).** A durable "I created this and
  lost it" record would carry its own staleness and its own repair problem. Once
  the hypervisor observation is re-requestable from the guest's scope, the
  hypervisor *is* the record.
- **Root cause 5 (orphaned `state: running` operations).** Out of this episode;
  tracked as F4 in the turn2 report.

## 4. Acceptance

Required:

- `uv run pytest -q` green in `nctl/`.
- Plan-level tests: (a) with a stale hypervisor snapshot, a retired guest's plan
  contains an `observe_node` on the control node and none on the guest;
  (b) with the guest present in the hypervisor's guest list, the plan contains
  exactly one `destroy_compute_instance` and gates SSH on the control node only;
  (c) the Step 3 invariant test.

Strongly recommended — this is the real proof, and the environment is
experimental:

- Reproduce F3 live on `aghub` with a fresh throwaway (`agdoomed2`, an unused
  vmid): create it through `nctl reconcile`, kill the process while the ingest
  job is polling (that is exactly where it died — events 9–16), then recover to
  `converged` and `nctl prune` using only supported `nctl` commands from the
  guest's own scope. A successful real retirement through this path already
  exists as precedent (`agscratch1`, vmid 199, `aghub`, 2026-08-03).

## 5. Prohibitions (all of them)

1. Do not hand-edit Nautobot ledger rows to fake a realization link. The repair
   must go through observation and ingest, or it proves nothing.
2. Do not use `pct destroy` (or any direct hypervisor write) as part of
   acceptance — removing that necessity is the deliverable. If you need it to
   clean up after a failed attempt, that is fine; say so in the report.
3. Keep `--allow-destroy` scoped to the one guest you planned.

Everything else — module layout, registry shape, how you thread the control node
into the planner, whether you split or merge the forced-observation path — is
yours.

## 6. Environment notes

- `aghub.local` is the Proxmox VE host. `eiji` has no passwordless sudo and root
  SSH is denied; root-level `pct`/`qm` needs the user. Read-only ground truth
  works without a password and is the fastest way to check what the hypervisor
  actually holds:
  `ssh aghub.local sudo -n /usr/local/libexec/nodeutils-pvesh-read /nodes/aghub/lxc`
- The local Nautobot is a scratch environment
  (`.local/localenv_memo.md`); migrations, test rows, and restarts there are not
  live mutations. Real-cluster SSH/Ansible and Proxmox writes still are.
- `nctl ops list` / `nctl ops show OPERATION_ID` read the durable evidence under
  `<events.log_dir>/<operation_id>/`. Note that a killed run stays `state:
  running` forever (root cause 5) — do not read that as "still executing".
