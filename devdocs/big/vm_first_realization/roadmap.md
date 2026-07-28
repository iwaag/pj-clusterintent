# First Proxmox Guest Realization — Development Roadmap

## Purpose

Prove that one confirmed user wish can become one newly created Proxmox guest through the standard
control loop, and that a repeat run does not create it again.

This roadmap implements item 5 of [`devdocs/vision/refactor/vision.md`](../../vision/refactor/vision.md).
The vision and [`README_DEV.md`](../../../README_DEV.md) remain authoritative for evidence and
completion language. [`nctl_modularization/roadmap.md`](../nctl_modularization/roadmap.md) is a
completed prerequisite, and its [`p5/report.md`](../nctl_modularization/p5/report.md) §7 states the
exact seams this roadmap extends.

The observable outcome is:

```text
current
  compute models, ingest, and typed reads exist on every side
  + zero desired compute rows, zero compute drift codes, zero compute actions
  + no write path to Proxmox anywhere in the repository
  + `test_compute_actuation_inert.py` asserts that compute does nothing

to
  one confirmed Braindump wish recorded as structured desired compute state
  + a compute evaluator that explains platform and guest realization in drift
  + one dry plan that names exactly one guest and its dependencies
  + one LXC container created and started once on `aghub`, freshly observed and linked
  + a safe stop at `waiting_for_manual_initial_access` that survives a repeat run
  + an Alignment Review that states what converged, what is manual, and what is unsupported
```

The consumer is the operator who wants to add a guest to the cluster by describing it, and the
agent that has to do that deterministically instead of improvising `pct create` over SSH.

## What this roadmap supersedes

[`devdocs/big/vm/roadmap.md`](../vm/roadmap.md) Phases 4 through 9 are **superseded** by this
document. Their goals were correct but unbounded: they mixed the first creation proof with QEMU
support, mutable resource differences, bootstrap automation, Braindump proposal engineering, and
whole-workflow consolidation.

- VM Phases 1 and 2 are `complete` and remain the contract for observation and ingest.
- VM Phase 3 is `complete` through Step 8 (models, endpoint MAC, destructive cutover, deployment).
  Its Steps 9-12 never ran. This roadmap absorbs the Step 9-10 seed work into its Phase 1 and
  replaces Steps 11-12 with its own verification.
- VM Phases 6-9 remain valid future work. Each needs its own roadmap when a concrete case appears.

Read the VM roadmap's governing decisions 1-10 and its drift vocabulary as still-current design
input. Do not re-derive them here.

## The realization contract

**The fixture is one new, disposable Proxmox LXC container on `aghub`.** It is chosen because the
LXC path already has typed evidence end to end — `rootfs` capacity, `vztmpl` template availability
through the allowlisted storage-content read, and `agdnsmasq` as a live LXC to validate matching
against before anything is created.

This roadmap therefore proves **Proxmox guest/container creation**. It does not prove QEMU virtual
machine creation, and no report may claim it does.

The required state transition:

```text
confirmed Braindump wish
  -> exact structured desired proposal (node + endpoint + compute instance)
  -> user confirmation and desired write through the canonical writer
  -> dry plan naming one guest scope and its dependencies
  -> separate apply authority
  -> create and start execute exactly once
  -> fresh Proxmox observation and ingest
  -> stable compute link on the desired instance
  -> waiting_for_manual_initial_access (successful, resumable terminal)
  -> repeat reconcile plans no create action
  -> refreshed Alignment Review explains the resulting state
```

`waiting_for_manual_initial_access` is a success, not a failure. The operator configures the guest's
user, key, privilege, SSH, and mDNS through the Proxmox console; guest-OS observation and SSH
enrollment resume in a later ordinary reconcile and are **not** gates for this roadmap.

## Governing decisions

1. **One guest, one kind, one direction.** Ensure-present and start only. Nothing in this roadmap
   stops, deletes, resizes, migrates, or replaces a guest — including the disposable fixture, whose
   cleanup is an out-of-band operator action.
2. **nintent owns the compute contract.** nctl replays nintent's generated
   `tests/fixtures/compute_conformance.json`. If a contract rule changes, regenerate the fixture and
   run the compute conformance gate. Do not add a second validator in nctl.
3. **The guest is created through the existing actuation boundary.** The recommended actuator is a
   new `ansible_agdev` playbook, run against `aghub` through the existing playbook action handler,
   which already owns inventory scope, `--limit`, and strict SSH trust. Extending the pvesh helper
   with a narrow write grammar is an acceptable alternative if the Ansible path proves more
   expensive. A Proxmox API client inside nctl is the last resort and needs its reason recorded.
4. **Deterministic identity comes from intent, not allocation.** The fixture declares its `vmid`
   and its endpoint MAC explicitly. VMID allocation, MAC generation, and collision-resolution
   strategies are deferred; collision *detection* is not.
5. **Create only against fresh evidence.** A create action requires a fresh Proxmox observation
   showing no matching candidate. After creation, re-observe and link before reporting anything;
   if the created guest cannot be identified, say so instead of assuming success.
6. **Compute stays target-local.** A bad platform, an ambiguous candidate, or a failed create for
   one guest never blocks planning or actuation for unrelated nodes.
7. **Registration, not restructuring.** The evaluator, the reconciler, and the actuator each attach
   at the seam `nctl_modularization` left for them. If a seam turns out to be wrong, fix the seam
   and say so — do not route around it by extending an existing evaluator or handler.

## Current-state inventory

Measured 2026-07-28 on a clean tree. **Phase 0 must recheck all of it**, especially the deployed
image, since three initiatives have deployed to the scratch stack since VM Phase 3 was written.

### Revisions

| Component | Revision | State |
|---|---|---|
| superproject | `cc20614` | clean |
| nctl | `1ca0e74` | clean, pointer current |
| nintent | `4f46bc8` | clean |
| nauto | `6dab422` | clean |
| nodeutils | `775ed7f` | clean |
| ansible_agdev | `66b31c8` | clean |

The installed Nautobot image was last reported carrying nintent `84ac0b1` and nauto `1c78af8`.
nintent HEAD is ahead of that. Phase 0 must confirm the delta contains no model, API, or contract
change — and rebuild if it does.

### What already exists

- **nintent**: `DesiredComputePlatform`, `DesiredComputeInstance`, `DesiredEndpoint.mac_address`,
  migration `0015`, strict `v1` config with closed key sets, UI/REST/GraphQL/YAML import, and
  `compute_contract.py` as the single semantic owner with a generated conformance fixture.
  Migrations are applied through `0016`.
- **nodeutils**: `proxmox_inventory.py` collects cluster/node/QEMU/LXC/VMID/resource/state/interface/
  storage evidence through the read-only `nodeutils-pvesh-read` helper, with configured and
  guest-agent interfaces kept separately.
- **nauto**: `proxmox_ingest.py`, `proxmox_upsert.py`, and `proxmox_interfaces.py` materialize
  Cluster, VirtualMachine, VMInterface, and IP relations under the closed `proxmox_*` allowlist with
  per-object freshness.
- **nctl**: `nctl_core/compute/{contract,collection,model}.py` types desired compute;
  `sources/actual.py` reads clusters and virtual machines plus the `proxmox_*` allowlist with
  structured per-field read errors; the desired MAC is a live dnsmasq consumer.
- **Seeded desired state**: `aghub` is a desired node with a primary endpoint and appears in the
  generated inventory as `aghub.local`. `agdnsmasq` is a live LXC on that Proxmox host.

### What does not exist

- Zero `DesiredComputePlatform` rows and zero `DesiredComputeInstance` rows.
- No compute comparator: `drift/registry.py` has `node`, `endpoint`, and `service` only.
- No compute reconciler and no compute action handler: `reconcile/actions/dispatch.py` holds five
  handlers, none of them compute.
- No Proxmox write path in any component. The pvesh helper is read-only by design.
- `tests/test_compute_actuation_inert.py` runs the real comparator and planner pipeline over a valid
  platform and instance and asserts zero diffs and zero actions. **This is the first test the
  roadmap must deliberately replace**, and replacing it is a reportable act.

### Environment facts that shape the plan

- `aghub.local` is the actuation target and must be reachable and SSH-enrolled. Phase 0 confirms it.
- `agdnsmasq.local` and `agbach.local` have been unreachable as a known, accepted condition. Phase 0
  must decide what that means for the fixture's DHCP reservation — see Phase 0 decision 4.
- The local Nautobot/PostgreSQL/Redis stack is scratch. `aghub` and its guests are real hardware,
  but this is an experimental cluster, not production.

## Ownership and dependency map

| Value or decision | Owner |
|---|---|
| compute contract semantics | nintent `compute_contract.py`; nctl conforms via the generated fixture |
| desired compute rows | nintent, written through the canonical Import/REST path only |
| Proxmox actual ledger | nauto ingest into native Cluster/VirtualMachine/VMInterface objects |
| typed compute reads | `nctl_core/compute/` and `sources/actual.py` |
| compute drift and target status | a new evaluator registered at `drift/registry.py` as `compute_instance` |
| compute action identity, phase, DAG order | `reconcile/registry.py` and `reconcile/reconcilers.py` |
| create/start execution | one new handler in `reconcile/actions/`, in the `_HANDLERS` table |
| the exact target set | `planner.build_plan`; a handler never widens it |
| guest bootstrap after creation | the operator, out of band, through the Proxmox console |
| the fixture's identity values | the frozen Phase 0 record, confirmed by the operator |

Prerequisites `remove_unused_surfaces`, `interface_contract`, `test_strategy`, and
`nctl_modularization` are all `complete`. No other roadmap is in flight; this one owns
`sources/desired.py`, `drift/`, and `reconcile/` for its duration.

## Scope

### In scope

- one compute evaluator, one linking reconciler, one create/start reconciler and handler;
- the seed of `aghub-pve` plus the existing `agdnsmasq` compute instance, and the new fixture's
  node/endpoint/instance records;
- preflight validation for template availability, storage/bridge existence, VMID/MAC/IP collision,
  single NIC-bearing endpoint, and platform observation freshness;
- one least-privilege ensure-present/start actuator;
- post-create observation, ingest, and link;
- the `waiting_for_manual_initial_access` terminal and its non-repetition proof;
- Braindump wish, confirmed proposal, and refreshed Alignment Review for the fixture; and
- documentation of the resulting ordinary workflow.

### Deferred (each may get its own roadmap)

QEMU creation; a second guest kind; vCPU/memory/disk mutation; stop, delete, replace, migrate,
shrink, move; automatic guest bootstrap (cloud-init, golden templates, OpenTofu); multi-NIC
support; VMID or MAC allocation; other providers; capacity scheduling; a proposal engine inside
nctl; and whole-cluster compute lifecycle management.

## Phases

Plans and one report per phase live under `devdocs/big/vm_first_realization/pN/`.

| Phase | Goal | Live mutation |
|---|---|---|
| 0 | Recheck state, freeze the fixture and the vocabulary | none |
| 1 | Seed compute roots; compute drift becomes real and explains `agdnsmasq` | desired write |
| 2 | Deterministic ledger link for an existing guest | Nautobot link write |
| 3 | The wish, the records, and a dry create plan | desired write |
| 4 | Create and start the guest once | Proxmox create/start |
| 5 | Review, document, remeasure, report | none |

### Phase 0 — Recheck, freeze the fixture, freeze the vocabulary

**Goal:** know the real current state and make every ambiguous choice before code exists. Read-only.

1. Record revisions, dirty state, the installed nintent/nauto commits inside the running containers,
   and the migration state. Rebuild if the installed image is behind a contract change.
2. Run a fresh read-only nodeutils Proxmox collection from `aghub`. Record the cluster name, the
   existing guest set with VMIDs and kinds, available storages, available `vztmpl` templates, and
   the bridge. Confirm `aghub.local` is reachable and enrolled.
3. Freeze the fixture record with the operator's confirmation: guest name and slug, VMID, template
   string, storage, bridge, vCPU, memory, root disk, endpoint IP and MAC, mDNS/DNS names, and
   whether the guest is kept or destroyed at the end.
4. **Decide the DHCP question.** If `agdnsmasq` cannot receive a deployed reservation, choose: give
   the fixture an IP policy that does not depend on a dnsmasq deploy action, or accept that the
   rendered reservation stays undeployed and an unreachable dnsmasq host is a target-local blocker
   that does not block guest creation. Record the choice and its consequence for the plan's action
   dependencies.
5. Freeze the compute drift vocabulary: which of the VM roadmap's listed cases get codes now, their
   target kind, severity, and reconcile classification. Anything not needed by the fixture is
   deferred, not stubbed.
6. Choose the actuator mechanism per governing decision 3 and name the exact commands or modules,
   the credential source, and the privilege boundary it needs on `aghub`.
7. Capture the behavior baseline: `nctl drift --json`, the generated inventories, the dnsmasq
   render digest, and the current guest set.

**Exit:** a frozen fixture record, a decided DHCP behavior, a frozen drift vocabulary, a chosen
actuator with its privilege boundary, a captured baseline, and no changed file outside `devdocs/`.

### Phase 1 — Seed the compute roots and make compute drift real

**Goal:** desired compute state exists and drift explains the *existing* `agdnsmasq` guest, with no
actuation anywhere.

1. Extend `nauto/seed/intent_sources.yaml` with the `aghub-pve` platform and the `agdnsmasq` compute
   instance, plus the endpoint MAC. Preview first; apply only after the preview shows exactly the
   intended rows. Run the identical import again and prove it is a no-op. (This is VM Phase 3
   Steps 9-10, finished here.)
2. Implement the compute evaluator and register it as `compute_instance`. Match a platform by
   explicit realized Cluster first, then by stable Proxmox scope identity; match a guest by explicit
   realized VM first, then by platform plus kind plus requested VMID, then by a single strong
   normalized-name candidate. Never match a guest belonging to another platform.
3. Compare only fields with reliable actual evidence. Report creation-only and unobservable values
   as such rather than as permanent drift.
4. Emit compute findings into structured JSON drift, human-readable CLI drift, and reconcile
   classification.
5. Replace `test_compute_actuation_inert.py` with the contract that now holds: compute produces
   drift, and still produces no actuation. State the replacement in the report and update the
   `MANIFEST.md` row.

**Exit:** `nctl drift` names the `agdnsmasq` compute realization separately from its guest-OS
realization; a stale, ambiguous, or missing candidate produces its frozen code; repeat import is a
no-op; and no plan contains a compute action.

### Phase 2 — Link one existing guest through an approved ledger write

**Goal:** prove the link path against real data before anything is created.

1. Add the linking reconciler and its action handler for a single unambiguous candidate, recording
   derived provenance.
2. Dry plan first: it must name the exact Cluster and VirtualMachine and nothing else.
3. Apply with separate approval, refetch, and prove the link is exactly what the plan named.
4. Fresh drift converges and a repeat run plans no link action.
5. Prove dependency closure: reconciling `agdnsmasq` may read `aghub-pve` and `aghub`, but plans
   nothing for an unrelated guest.

**Exit:** one link written once, confirmed by refetch, non-repeating, scoped, with zero Proxmox
mutation.

### Phase 3 — The wish, the records, and a dry create plan

**Goal:** the fixture exists as confirmed structured intent and produces a truthful create plan that
does not run.

1. Record the Braindump wish for the new guest and let the agent produce an exact structured
   proposal — node, endpoint with MAC and mDNS name, compute instance with the frozen values. The
   proposal is not the write; the operator confirms it, and the write goes through the canonical
   desired writer.
2. Add the create/start reconciler with its DAG dependencies, following the Phase 0 DHCP decision.
3. Implement preflight validation: template present in fresh storage-content observation, storage
   and bridge exist, no VMID/MAC/IP collision against desired or actual state, exactly one
   NIC-bearing primary endpoint, and platform observation fresh enough to trust.
4. Build a fake or disposable Proxmox boundary in tests that positively proves the create call would
   be issued, plus the negative cases: template missing, ambiguous or missing endpoint, collision,
   stale platform, malformed result, partial success, and an unrelated guest left alone.
5. Run the real dry plan against the live scratch state. It names one guest, its dependencies, and
   the actions it would take — and takes none.

**Exit:** one confirmed wish is structured desired state; one dry plan names one exact guest scope;
every preflight failure mode has a named code and a test; zero Proxmox calls have been made.

### Phase 4 — Create and start the guest once

**Goal:** the one live proof. Requires explicit operator approval at the apply gate.

1. Re-run the dry plan immediately before applying and confirm it is unchanged.
2. Apply. Create only when fresh observation shows no candidate; start only the guest just created.
3. Refetch from Proxmox immediately. If the result cannot be identified, fail truthfully and stop
   with the created guest recorded as partial progress.
4. Run nodeutils observation and nauto ingest, then link `realized_vm` to the observed
   VirtualMachine.
5. Reach `waiting_for_manual_initial_access` as a successful terminal, with create, start,
   observation, and link all preserved in the operation evidence.
6. Run reconcile again. It must plan no create and no start, and must not touch the guest.
7. Run a whole-cluster dry plan and confirm unrelated nodes and guests are unaffected.

**Exit:** the guest exists, was created exactly once through the approved boundary, is freshly
observed and linked, terminates at the manual-access safe stop, and survives a repeat run unchanged.

### Phase 5 — Review, document, remeasure, report

**Goal:** make the path repeatable by someone who was not here.

1. Refresh the Alignment Review so it states what converged, what waits on manual access, and what
   is unsupported.
2. Document the ordinary "add a Proxmox guest" workflow: the minimum intent inputs, the dry plan,
   the apply, the manual gate, and the recovery guidance for created-but-not-observed, template
   missing, collision, platform unreachable, and stale ledger.
3. Update `nctl/README.md` with the compute evaluator, reconciler, and handler as worked examples of
   the three seams.
4. Execute the fixture's cleanup decision from Phase 0. If the guest is destroyed, the operator does
   it by hand; record it as an out-of-band action, not as an nctl capability.
5. Run the root command matrix, verify every `MANIFEST.md` row resolves, and diff the deterministic
   artifacts against the Phase 0 baseline.
6. Write the final report: revision tuple, the state transition with its evidence, every deviation,
   what is proven (LXC creation) and what is explicitly not (QEMU, mutation, deletion, automatic
   bootstrap), and the handoff for whichever roadmap comes next.

**Exit:** the workflow is documented, the review is current, the matrix passes, the cleanup decision
is executed and recorded, and the report states precisely what was proven.

## Verification matrix

| Area | Required proof |
|---|---|
| structured intent | one confirmed wish exists as desired node, endpoint, and compute instance |
| drift truth | compute targets appear in JSON and CLI drift with the frozen codes |
| plan/apply separation | the dry plan makes zero Proxmox calls; apply requires its own authority |
| exact scope | one guest through plan, preflight, actuation, observation, and link; siblings untouched |
| the create ran | positive evidence that create and start were issued, not merely absence of error |
| identification | the created guest is refetched and linked, or the failure is reported truthfully |
| non-repetition | a second reconcile plans no create, no start, and no link |
| partial progress | a post-create failure preserves create/start/observation evidence and `mutated=true` |
| target isolation | a bad platform or guest blocks only its own target |
| SSH boundary | the actuation path uses the existing strict trust; no `accept-new`, no disabled checking |
| contract ownership | the compute conformance gate passes; nctl has no second validator |
| no deletion path | no code in the repository can stop, delete, or replace a guest |
| artifacts | dnsmasq, hosts-intent, and production bytes differ from baseline only where the fixture explains it |
| gates | the root command matrix in `README_DEV.md` passes with stated case counts |

## Hard rules

These are the only prohibitions. Everything else is the implementer's call.

1. Prose never actuates. Only a confirmed structured record produces a plan; only explicit apply
   authority produces a mutation.
2. Create and start only. No stop, delete, resize, migrate, or replace — in code, in tests, or by
   hand through nctl.
3. Missing desired state never authorizes touching an observed guest.
4. Never weaken SSH strictness to reach the new guest.
5. One exact target set from plan to observation; a compute action never widens it.
6. Create only after fresh observation shows no candidate; re-observe before claiming success.
7. No credentials or tokens in nintent, in operation evidence, or in tracked files.

## Implementer discretion

Explicitly yours to decide, without asking: module layout and file names; drift code spellings
beyond the frozen set; how the evaluator is decomposed; test structure and fixture design; commit
granularity; how many phase steps a plan has; whether a preflight check lives in the evaluator, the
planner, or the handler; and when to rebuild the image.

Local scratch Nautobot, its database, test rows, container restarts, and migrations need no
approval and no backup ceremony. Read-only Proxmox observation needs no approval.

Ask the operator only at: the Phase 0 fixture values, the Phase 1 seed apply, the Phase 2 link
apply, the Phase 4 create/start apply, the Phase 5 cleanup, and any nintent push.

## Evidence, rollback, and cleanup

Each phase produces one report under `pN/`, carrying the revision tuple, decisions, gate results
with case counts, deviations, and a precise status: `complete`, `partially complete`,
`implemented, not deployed`, `blocked`, or `superseded`. Raw output stays in operation artifacts or
under `.local/`, not in tracked prose.

Rollback for source changes is the prior submodule revision. Rollback for desired rows is the
canonical writer. There is no rollback for a created guest: it is deleted by hand or kept. That
asymmetry is the reason Phase 4 is a separate gate — record the guest's identity before creating it
so it can always be found again.

A created guest that never reaches manual access is partial progress, not a failed create, and not
a reason to create a second one.

## Definition of done

This initiative is `complete` only when:

- one confirmed Braindump wish is represented in structured desired state and traceable to it;
- compute drift explains both the existing `agdnsmasq` guest and the new one, with frozen codes;
- one dry plan named one exact guest scope and its dependencies before any mutation;
- create and start are positively shown to have executed exactly once through the approved boundary;
- the created guest was freshly observed, ingested, and linked;
- reconcile terminates at `waiting_for_manual_initial_access` with all prior evidence intact;
- a repeat run plans no create, no start, and no link;
- unrelated guests and nodes were neither acted on nor blocked;
- the compute conformance gate and the full root command matrix pass;
- no stop, delete, resize, or replace capability was added;
- the workflow, the recovery guidance, and the three seam examples are documented;
- the cleanup decision was executed and recorded; and
- the report says "one Proxmox LXC container was created", not "a VM was created", and lists every
  omitted or substituted proof.

The outcome is not a compute feature set. It is one guest that exists because someone asked for it,
with a traceable line from the wish to the running container and back.
