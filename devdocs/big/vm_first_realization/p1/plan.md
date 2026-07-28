# First Proxmox Guest Realization — Phase 1 Implementation Plan: Seed the Compute Roots and Make Compute Drift Real

Parent: [roadmap.md](../roadmap.md) — Phase 1. Predecessor: [p0/report.md](../p0/report.md).

Status: proposed. One desired-state write to the local scratch Nautobot, one image rebuild carrying
the amended seed, and one nctl source change. No Proxmox mutation, no Ansible run, no push.

## 1. Goal

Phase 1 turns compute from "typed but inert" into "explained but still inert".

After this phase, `nctl drift` must be able to say — from real data, not a fixture — that the
running LXC container `agdnsmasq` on `aghub` *is* the realization of a desired compute instance,
that its platform `aghub-pve` *is* the observed Proxmox cluster `aghub-proxmox`, and that the one
thing still wrong is that the ledger link has never been written. It must say this without planning
a single compute action.

The phase must answer, and prove:

1. Which exact desired rows describe the existing `agdnsmasq` guest, and which of their required
   values cannot be verified from any observation we have?
2. How does a desired platform find its actual Cluster, and a desired instance find its actual
   VirtualMachine, without ever adopting a guest that belongs elsewhere?
3. Which desired fields have reliable actual evidence, which are creation-only, and which are
   simply unobservable — and how does drift say so without manufacturing permanent drift?
4. Where do compute targets appear in the four surfaces that already exist (JSON drift, CLI drift,
   host scoping, reconcile classification), and what breaks if they are added to only some of them?
5. Does every frozen failure code actually fire against constructed state, and does the *fixture's*
   real state produce exactly the codes we predicted?
6. Is a plan still free of compute actions after all of the above?

The observable result is:

```text
current
  zero DesiredComputePlatform rows and zero DesiredComputeInstance rows
  + drift/registry.py registers node, endpoint, and service only
  + `nctl drift` says 5 unknown / 5 converged / 1 drifting and never mentions compute
  + agdnsmasq appears once, as a node whose guest-OS observation is stale
  + test_compute_actuation_inert.py asserts compute produces no drift at all

to
  one aghub-pve platform row and one agdnsmasq compute-instance row, imported through the
    canonical Import Job and provably idempotent
  + one desired endpoint MAC on agdnsmasq, agreeing with observed evidence
  + a registered `compute_instance` evaluator plus a `compute_platform` target
  + agdnsmasq appearing twice and distinctly: as a node (guest-OS realization, still stale) and
    as a compute instance (guest realization, matched to VMID 108, not yet linked)
  + every frozen failure code reachable and tested
  + a replacement inert test that asserts the new contract: compute drifts, compute never acts
```

Phase 1 does **not** write any link, does not add a reconciler, and does not add an action handler.
Deriving a candidate and *recording* it are separate acts; recording is Phase 2.

## 2. Required outputs

1. two seed rows plus one endpoint MAC in `nauto/seed/intent_sources.yaml`, applied through the
   canonical Import Job;
2. the compute evaluation module and its registered comparator;
3. compute-aware target seeding, status derivation, classification, scoping, and rendering;
4. the replacement for `tests/test_compute_actuation_inert.py` and its `MANIFEST.md` row;
5. live evidence: drift before and after, plus one dry plan; and
6. `devdocs/big/vm_first_realization/p1/report.md` with a final state of `complete`,
   `partially complete`, `implemented, not deployed`, or `blocked`. Intermediate `report<N>.md`
   files are optional — write one per step, per group of steps, or not at all.

`nintent` needs no change, so there is no contract change, no fixture regeneration, and no push.

## 3. Authority and safety boundary

The Nautobot/Postgres/Redis stack is scratch and the cluster is experimental. Rebuild it, migrate
it, restart it, write test rows into it, and revert desired rows through the canonical writer
without asking. Everything not listed below is the implementer's call, including module layout,
file names, test structure, commit granularity, how many steps this plan actually runs as, and
whether a check lives in the evaluator or the comparator.

**The only prohibitions:**

1. **No Proxmox mutation.** No `pct`/`qm`, no pvesh write, no playbook against a cluster node.
   Creating the first guest is Phase 4's approved gate; a guest created by accident here cannot be
   rolled back.
2. **No compute action in a plan.** No compute reconciler, action handler, or `AUTOMATIC`
   classification — that is this phase's deliverable boundary, not a safety rule, and Phase 2/3 add
   them deliberately.
3. **No `realized_cluster`/`realized_vm` write.** Deriving a candidate is Phase 1; recording it is
   Phase 2's single approved write.
4. **No push.** Local commits are fine; pushing `nintent`/`nauto`/`nctl` stays the operator's step.

**One approval gate — the seed apply.** Before `apply=true`, show the YAML diff and the two values
in Section 5.2 that are declared but unverifiable (`template`, `unprivileged`), and let the operator
confirm them. This is about not fabricating intent, not about write safety: the rows are reversible
through the same Import Job.

**One thing worth stopping for:** if the endpoint MAC we intend to seed disagrees with the Device-side
evidence (F3), that is a real identity conflict — report it instead of seeding the MAC anyway.
Everything else that surprises you is a finding to record and work through.

## 4. Governing inputs and planning-time findings

### 4.1 Required reading before Step 0

[`roadmap.md`](../roadmap.md) governing decisions 1–7 and hard rules 1–7; [`p0/report.md`](../p0/report.md)
in full; [`README_DEV.md`](../../../../README_DEV.md) §"Test strategy command matrix" and lessons 1,
5, 8, 9; [`.local/localenv_memo.md`](../../../../.local/localenv_memo.md); and
`nctl/README.md` §"Module admission" and §"Adding a comparator".

### 4.2 Frozen inputs carried from Phase 0

| Input | Value |
|---|---|
| Proxmox cluster | `aghub-proxmox`, one node `aghub`, bridge `vmbr0` |
| LXC rootfs storage | `local-lvm` |
| Available `vztmpl` | only the two Ubuntu 22.04 / 24.04 strings recorded in p0 |
| DHCP decision | the future fixture is non-reservation/static; **no consequence for Phase 1** |
| Actuator | a future `ansible_agdev` playbook; **not built in Phase 1** |
| Drift vocabulary | the fourteen-row table in p0 §"Frozen compute vocabulary" |

**Phase 0's one unmet exit condition — the frozen fixture record — is not an input to Phase 1.**
Phase 1 seeds only `aghub-pve` and the *already existing* `agdnsmasq` guest; it declares no new
guest, no new VMID, no new IP, and no new MAC. Phase 3 is the first phase that cannot start without
the fixture record. This plan therefore proceeds with Phase 0 still `blocked` on that single item,
and the Phase 1 report must repeat that statement rather than implying Phase 0 completed.

### 4.3 Planning-time findings

Measured on the live scratch stack and the checked-out tree on 2026-07-28.

**F1 — the actual ledger already carries the evidence Phase 1 needs.** `nctl actual` returns Cluster
`aghub-proxmox` (`observation_state: complete`, `observed_at 2026-07-27T22:20:28Z`,
`observer_device_id` = `aghub`'s Device) with nine guests, including `agdnsmasq`: `lxc`, VMID 108,
node `aghub`, `running`, 1 vCPU / 512 MB / 8 GB, rootfs on `local-lvm`, one `net0` interface
`BC:24:11:23:DC:B7` on `vmbr0`. No re-ingest is required unless that observation ages past 72 hours
(see F9).

**F2 — three required values are not observable.** `nodeutils/proxmox_inventory.py` parses `rootfs`
but never collects the LXC `ostemplate` or the `unprivileged` flag. The compute contract
(`validate_instance_config`) nevertheless *requires* `template` for every instance and
`unprivileged` for every container. Seeding `agdnsmasq` therefore forces us to declare two values we
cannot verify. These two are the seed-apply gate's confirmation items, and the evaluator must treat
them as creation-only rather than as drift.

**F3 — the seed MAC is derivable but must be cross-checked.** The MAC comes from the observed
VMInterface, so it is not invented. But `drift/endpoint_evaluation.py` independently compares a
desired endpoint MAC against the node's realized *Device* interface evidence and emits
`desired_mac_mismatch` (severity `conflict`, `MANUAL_REVIEW`, and a member of
`dnsmasq.DHCP_BLOCKING_SKIP_CODES`). Seeding a MAC that disagrees with the Device-side evidence
would flip node `agdnsmasq` from `unknown` to `drifting` and change reconcile behavior. Step 1
must compare the two sources *before* applying; disagreement is the one stop condition in §3.

**F4 — most of the compute semantics already exist and must be reused, not re-derived.**
`nctl_core/compute/contract.py` already owns `effective_lifecycle`, `is_actionable_lifecycle`,
`select_compute_primary_endpoint`, `effective_compute_defaults` (with `instance_override` /
`platform_default` / `unresolved` provenance), and `normalize_mac_address`. The evaluator consumes
these. Adding a second spelling of any of them violates roadmap decision 2 and the
`compute-contract-single-owner` manifest row.

**F5 — `DesiredSnapshot.source_issues` has zero consumers today.** `build_compute_collections` and
`validate_endpoint_macs` already produce structured row-scoped issues, including
`compute_primary_endpoint_missing`/`_ambiguous` — codes p0 froze as drift codes — and nothing
surfaces them. A compute row that fails source validation is silently dropped from the snapshot and
disappears from drift entirely. Phase 1 must surface these as diffs, or the frozen vocabulary is
only half-implemented and a malformed row reads as "no compute intent".

**F6 — four surfaces assume `kind == "node"`.** A new target kind is invisible or wrong in each
until changed: `drift_render.py:158` (`--host` filter), `reconcile/planner.py:64`
(`select_scoped_diffs`), `reconcile/executor.py:745` (final host-scoped drift summary), and
`drift/engine.py:108` (`_observed_at_for`, which correctly returns `None` for non-node kinds but
must be re-read once compute targets exist). Adding the evaluator without these makes
`nctl drift --host agdnsmasq` and `nctl reconcile agdnsmasq` silently drop every compute finding —
exactly the "empty evidence read as a pass" failure `README_DEV.md` lesson 1 warns about.

**F7 — the seed YAML is baked into the image, not mounted.** `devenv/nautobot/Dockerfile` does
`COPY nauto/seed/intent_sources.yaml /opt/nautobot/intent_sources.yaml` from the superproject build
context and records its `sha256`. Editing the working tree changes nothing the Import Job can see;
the apply path is edit → `docker compose build` → restart → Import. The build context is the local
checkout, so **no `nauto` push is required**. `NINTENT_COMMIT` stays pinned at `84ac0b1…`, so the
rebuild must not change the installed plugin — verify the resolved commit from `build_info.json` and
the image label rather than assuming it (use `--no-cache`; a cached layer has silently carried a
stale plugin commit before).

**F8 — the classification table is fail-closed for error diffs only.** `planner.build_plan` skips a
non-error diff whose code is absent from `CODE_CLASSIFICATION`, but `classify()` raises
`UnclassifiedDiffCodeError` for any error diff. `tests/test_reconcile_classify.py` re-derives the
vocabulary by scanning `_SCANNED_FILES`, which currently lists `drift/evaluation.py`,
`drift/service_placement.py`, `drift/evaluation_snapshot.py`, and `sources/actual.py` — not
`comparators.py`. The new evaluator module must be added to that list, and the one informational
code Section 5.6 introduces needs an explicit, reviewed exemption rather than a silent one.

**F9 — `ACTUAL_MAX_AGE_HOURS = 72` in `production/contract.py` already owns staleness**, through
`actual_state_problem(collected_at, generated_at)` which distinguishes missing / invalid / stale.
Platform observation freshness reuses that function. Introducing a second threshold would give
`stale_actual_data` and `compute_platform_observation_stale` independent definitions of "stale".

### 4.4 Deviations from Phase 0's frozen table

Two rows of p0's vocabulary table are implemented with a different *classification* than frozen.
The codes, severities, and target semantics are unchanged. Both deviations must appear in the Phase
1 report and in the code comment that implements them.

| Code | p0 classification | Phase 1 classification | Reason and reversal |
|---|---|---|---|
| `compute_instance_not_linked` | `ledger_link` | `manual_review` | The linking reconciler is Phase 2's deliverable. Classifying it `AUTOMATIC` now would either name an unregistered reconciler id (a crash) or plan a compute action (a Phase 1 exit violation). **Phase 2 flips this row.** |
| `compute_platform_observation_stale` | `observe`, then manual_review | `manual_review` | The `OBSERVATION` branch of `build_plan` resolves a target to a node and has a special case only for `kind == "service"`; a `compute_instance` target would be handed to `observe_node` unresolved. Routing it to the platform's control node is real work with no Phase 1 consumer. **Phase 2 promotes this row** when the linking reconciler needs fresh evidence. |

One refinement, not a deviation: p0 says every code targets `compute_instance` because "platform
evidence is attached to the affected instance". That holds for platform failures that block an
instance. It cannot hold for `unexplained_compute_guest`, which by definition has no affected
instance, nor for a platform with zero declared instances. Phase 1 therefore uses **two** target
kinds — see Section 5.6.

## 5. The design made concrete

### 5.1 The platform row

```yaml
desired_compute_platforms:
  - name: aghub-pve
    slug: aghub-pve
    control_node: aghub
    provider_type: proxmox
    lifecycle: active
    config_schema_version: v1
    config:
      cluster_name: aghub-proxmox
      default_storage: local-lvm
      default_bridge: vmbr0
```

`cluster_name` is `aghub-proxmox`, the observed Cluster name — not the platform slug. The slug is
intent's name for the platform; `cluster_name` is the assertion about actual state, and the
evaluator cross-checks them (Section 5.4).

### 5.2 The instance row and the endpoint MAC

```yaml
desired_compute_instances:
  - desired_node: agdnsmasq
    platform: aghub-pve
    instance_kind: container
    desired_power_state: running
    vcpus: 1
    memory_mb: 512
    root_disk_gb: 8
    config_schema_version: v1
    config:
      vmid: 108
      template: <one of p0's two observed vztmpl strings>   # declared, not verified
      storage: local-lvm
      bridge: vmbr0
      unprivileged: <true|false>                            # declared, not verified
```

and, on the existing `agdnsmasq` primary endpoint, one added key:

```yaml
    mac_address: bc:24:11:23:dc:b7                          # derived from observation, cross-checked
```

`vcpus`/`memory_mb`/`root_disk_gb`/`vmid`/`storage`/`bridge` are transcribed from F1's observation,
so the seed converges by construction rather than by luck. `template` and `unprivileged` are the two
values F2 makes unverifiable; both are the **seed-apply gate's confirmation items**, and the report
must record them as declared-not-verified rather than as observed facts.

`agdnsmasq`'s node lifecycle is `active` and the platform's is `active`, so `effective_lifecycle` is
`active` and `is_actionable_lifecycle` is true. That is precisely why the MAC is mandatory:
`build_compute_collections` drops any actionable instance whose node has no primary endpoint
satisfying the compute NIC contract (`mac_address` + `mdns_name` + a usable address policy).
Without the MAC edit, the instance never reaches the snapshot at all.

### 5.3 Applying the seed

1. Cross-check the MAC (F3 — the one stop condition).
2. Edit the YAML; commit in `nauto`.
3. `docker compose build --no-cache`; restart web, worker, scheduler.
4. Check `sha256sum /opt/nautobot/intent_sources.yaml` against the working-tree file, and that
   `build_info.json` still names `nintent` `84ac0b1…` (a cached layer has carried a stale plugin
   commit before). A mismatch means rebuild, not proceed.
5. Run `Import Intent Sources` with `apply=false`. The artifact should plan one
   `DesiredComputePlatform` create, one `DesiredComputeInstance` create, one `DesiredEndpoint`
   update, and `unchanged` for everything else.
6. **Gate.** Then `apply=true`; read the post-commit confirmation.
7. Run `apply=true` again. Every object must report unchanged; zero writes.

### 5.4 Matching rules

**Platform → Cluster.** In order:

1. If `realized_cluster_id` is set, that Cluster must exist. A dangling link is
   `compute_platform_missing` with evidence `reason=realized_cluster_missing` — never a silent
   fall-through to fuzzy matching.
2. Otherwise match by stable Proxmox scope identity: Clusters whose `proxmox.observer_device_id`
   equals the control node's `realized_device_id`. Zero → `compute_platform_missing`; more than one
   → `compute_platform_ambiguous`; exactly one → matched.
3. A matched Cluster whose `name` disagrees with a declared `config.cluster_name` is
   `compute_identity_conflict` with `dimension=scope`. The match still stands for evidence purposes;
   the conflict is what gets reported.
4. Freshness, via `actual_state_problem` (F9): missing, unparsable, or older than
   `ACTUAL_MAX_AGE_HOURS` → `compute_platform_observation_stale`, with the distinguishing reason in
   evidence. `observation_state != "complete"` emits the same code with
   `reason=platform_observation_incomplete`.

Every platform-scoped failure is reported on **both** the platform target and each instance it
blocks, because an operator reading one instance must not have to know that the reason lives
elsewhere. Instance evaluation stops after platform failure — a guest is never matched against an
unmatched, ambiguous, or stale platform.

**Instance → VirtualMachine.** In order:

1. If `realized_vm_id` is set, that VirtualMachine must exist → otherwise
   `compute_realized_instance_missing`. If it exists but sits in a different Cluster than the
   matched platform → `compute_identity_conflict`, `dimension=scope`. **A vanished link never
   re-enters candidate matching and never authorizes a create.**
2. Otherwise, candidates are restricted to VirtualMachines whose `cluster_id` is the matched
   platform's Cluster. A guest belonging to another platform is never a candidate, at any tier.
3. Tier A — declared VMID: candidates with `proxmox.vmid == config["vmid"]`. Exactly one → matched
   with `match_basis=vmid`.
4. Tier B — single strong normalized name: casefolded, domain-stripped VM name equal to the desired
   node's slug. Exactly one → matched with `match_basis=name`. More than one →
   `compute_instance_candidate_ambiguous`. Zero → `compute_instance_missing`.
5. On a match, verify the other identity dimensions and emit `compute_identity_conflict` with
   `dimension` set to `kind` (`lxc`↔`container`, `qemu`↔`virtual_machine`), `vmid` (matched by name
   but the observed VMID disagrees with a declared one), or `node` (the guest's `proxmox.node` is
   not among the Cluster's `observed_node_names`).
6. A derived (not explicitly linked) match is `compute_instance_not_linked`, warning.

`agdnsmasq` is expected to match at Tier A with `match_basis=vmid`, no identity conflict, and
`compute_instance_not_linked` as its only non-informational finding.

### 5.5 Field comparison policy

Each desired field gets exactly one disposition, carried in the informational summary (Section 5.6)
so a reader never has to guess why something was not compared:

| Field | Disposition | Evidence | Code on disagreement |
|---|---|---|---|
| power state | compared | `proxmox.status` | `compute_power_state_mismatch` (warning) |
| vcpus | compared | VM `vcpus` | `compute_resource_mismatch` (warning) |
| memory_mb | compared | VM `memory` | `compute_resource_mismatch` |
| root_disk_gb | compared | `lxc_rootfs.size_gb`, else VM `disk` | `compute_resource_mismatch` |
| endpoint MAC | compared *only* when the guest has exactly one NIC-bearing VMInterface | `ActualVMInterface.mac_address`, normalized through `normalize_mac_address` | `compute_endpoint_mac_conflict` (error) |
| instance_kind | compared | `proxmox.guest_type` | `compute_identity_conflict` (`dimension=kind`) |
| vmid | compared | `proxmox.vmid` | `compute_identity_conflict` (`dimension=vmid`) |
| storage | compared for LXC only | `lxc_rootfs.storage` | `compute_resource_mismatch` |
| bridge | compared | VMInterface `proxmox.bridge` | `compute_resource_mismatch` |
| template | **creation-only** | none exists (F2) | never |
| unprivileged | **unobservable** | none exists (F2) | never |

Multi-NIC guests are out of scope (roadmap "Deferred"): more than one NIC-bearing interface
suppresses the MAC and bridge comparisons and records `mac_comparison=skipped_multi_nic` in
evidence. It does not emit a code and does not silently pass.

`compute_resource_mismatch` is classified `UNSUPPORTED`, matching p0: nctl has no resize capability,
so the honest statement is "we see this and we cannot act on it", not "a human must fix this".

### 5.6 Targets, codes, and where they surface

Two target kinds:

- `Target(kind="compute_instance", slug=<node slug>, name=<node name>, id=<instance id>)` — one per
  desired compute instance. `slug` is the owning node's slug so that host scoping works; the kind
  keeps it distinct from the node's own target, which satisfies the roadmap's "names the compute
  realization separately from its guest-OS realization".
- `Target(kind="compute_platform", slug=<platform slug>, id=<platform id>)` — one per desired
  platform, carrying platform-scoped findings and `unexplained_compute_guest` (info, one per
  observed guest with no desired instance; classified `UNSUPPORTED` — nctl cannot and must not
  adopt, stop, or delete an unmanaged guest, mirroring the existing `unmanaged-no-delete` posture).

Both kinds are **seeded with zero diffs** in `engine._group_by_target`, exactly as nodes and
services are, so a healthy platform or instance still appears in `nctl.drift.v1`.

One informational code, `compute_realization_summary` (info), is emitted per compute target. It
carries the matched Cluster/VirtualMachine refs, the match basis, the `effective_compute_defaults`
values with their provenance, and the per-field disposition table from Section 5.5. This is the
compute analogue of `intent_effect_summary` and is what makes drift *explain* rather than merely
flag. Like `intent_effect_summary` it stays out of `CODE_CLASSIFICATION`; `test_reconcile_classify`
gains an explicit `_INFORMATIONAL_UNCLASSIFIED_CODES` set naming both codes, so the exemption is
reviewed rather than accidental (F8).

Source issues (F5) surface as diffs on the same two kinds, using the issue's own code and severity,
with `scope=global` issues additionally reported once on a `kind="global"` target. This makes
`compute_primary_endpoint_missing`/`_ambiguous`, `duplicate_platform_slug`,
`compute_instance_platform_missing`, and the rest visible instead of silently dropped.

Status derivation: `drift/status.py::UNKNOWN_CODES` gains `compute_platform_missing`,
`compute_platform_observation_stale`, and `compute_realized_instance_missing` — all three mean "we
do not have trustworthy actual data", not "the data disagrees". `compute_instance_missing`,
`compute_instance_candidate_ambiguous`, and `compute_identity_conflict` stay `drifting`: we have the
data and it disagrees.

Scoping (F6): `select_scoped_diffs`, `drift_render`'s `--host` filter, and `executor`'s final
summary each gain a compute clause selecting targets whose `slug` is the scoped host's slug.
`compute_platform` targets carry a platform slug, not a node slug, so they appear in cluster scope
only — correct, since a platform is not owned by the guest node.

### 5.7 Module layout

- `nctl_core/drift/compute_evaluation.py` — pure domain: matching, comparison, code emission. No
  registry, transport, or CLI import. Added to `test_module_boundaries.py`'s purity list and to
  `test_reconcile_classify.py`'s `_SCANNED_FILES`.
- One thin `@register("compute_instance")` wrapper in `drift/comparators.py`, matching how
  `node_intent_matching` / `endpoint_intent_matching` / `service_intent_matching` already attach.
  Registration lives with the other registrations; logic does not.

This satisfies `nctl/README.md` §"Module admission": the module owns one decision (does desired
compute state match observed compute state), changes for reasons independent of `comparators.py`,
names its consumers (the comparator wrapper, the classification table, and Phase 2's reconciler),
and sits in the domain layer.

### 5.8 Behavior that must not change

- Node, endpoint, and service diff codes, messages, and severities — byte-identical.
- The three deterministic renders — identical to p0's recorded digests **except** for any change the
  three seed edits explain, which must be stated exactly.
- Envelope schemas: `nctl.drift.v1` gains targets, not fields with new meanings.
- `nctl reconcile` plans: zero compute actions, and every pre-existing action unchanged.

## 6. Evidence

Raw output goes under `.local/vm-first-realization/p1/`; tracked reports carry summaries and digests
only, and no tokens or keys. What actually has to survive is small: the baseline drift + render
digests, the import preview/apply/repeat artifacts, the post-evaluator drift, and the dry plan.
Organize it however is convenient.

## 7. Implementation procedure

Seven steps as written, or fewer if merging them is cleaner — the ordering constraint is only that
the seed lands before live verification, and that the evaluator is registered (Step 4) before the
inert test is replaced (Step 5). Pause once, at the seed-apply gate.

### Step 0 — Re-verify the baseline

Record the revision tuple, the deployed image's `nintent`/`nauto` commits, and `nctl drift --json`,
`nctl actual --json`, and the three render digests; state any difference from p0. If the Cluster
observation in the ledger is older than 72 hours, run one read-only nodeutils collection and ingest
it first.

*Exit:* the baseline is current, or its drift from p0 is explained.

### Step 1 — Seed the compute roots (gate)

Execute Section 5.3 in order. The MAC cross-check comes first and can stop the step. Record the
preview artifact's full object plan, the operator's confirmation of `template` and `unprivileged`,
the apply confirmation, and the repeat-apply no-op. Immediately afterwards, re-run drift and the
three renders and prove that nothing changed except what the three edits explain — in particular
that node `agdnsmasq` did not acquire `desired_mac_mismatch` and the dnsmasq digest is unchanged.

*Exit:* two compute rows and one endpoint MAC exist in the live scratch database, the identical
import is a proven no-op, and drift is unchanged apart from explained effects.

### Step 2 — Platform matching and freshness

Implement Section 5.4's platform half in `compute_evaluation.py`. Cover at least: explicit link
resolved; explicit link dangling; scope-identity match; zero candidates; two candidates; declared
`cluster_name` disagreeing with the matched Cluster; and each of missing / unparsable / stale /
incomplete observation.

*Exit:* every platform-scoped frozen code is produced by a focused test; `nctl drift` is unchanged.

### Step 3 — Guest matching and field comparison

Implement Section 5.4's instance half and Section 5.5's comparison policy. Cover at least: Tier A
match; Tier B match; ambiguous name; no candidate; a same-name guest on another platform proving
non-adoption; a dangling `realized_vm`; each `dimension` of `compute_identity_conflict`; power-state
mismatch; resource mismatch; MAC conflict; MAC comparison suppressed by multi-NIC; and positive
assertions that `template` and `unprivileged` never produce a code.

*Exit:* every instance-scoped frozen code is produced by a focused test; `nctl drift` is unchanged.

### Step 4 — Register, seed targets, classify, scope

Add the `@register("compute_instance")` wrapper; seed both compute target kinds in
`engine._group_by_target`; surface source issues (F5); extend `UNKNOWN_CODES`; add every compute
code to `CODE_CLASSIFICATION` with the Section 5.6 classifications and the Section 4.4 deviation
comments; extend the three scope projections (F6); add `compute_evaluation.py` to `_SCANNED_FILES`
and the informational exemption set; add the module to `test_module_boundaries.py`. Add an
engine-level test asserting a healthy compute instance appears as a seeded, zero-diff target, and a
planner test asserting no compute code resolves to an `AUTOMATIC` classification.

*Exit:* compute appears in JSON drift, CLI drift, host-scoped drift, and reconcile classification —
and in no plan action.

### Step 5 — Replace the inert test and update the documented surface

Delete `tests/test_compute_actuation_inert.py` and add its successor asserting the contract that now
holds: over a real snapshot, the real comparator and planner produce compute diffs and compute
targets, and **zero** compute actions — including the negative case that no compute code maps to a
registered reconciler. Update the `compute-inert` row in `devtests/test_strategy/MANIFEST.md` to
name the new test and the new asserted evidence. Update `nctl/README.md`'s responsibility map and
the "Compute remains deliberately inert" paragraph in §"Adding a comparator", which is now false as
written. The replacement is a reportable act (roadmap Phase 1 item 5): the report states what the
old test guaranteed, what the new one guarantees, and why the guarantee moved.

*Exit:* no tracked file still claims compute produces no drift.

### Step 6 — Live verification and gates

Run the `nctl` ordinary suite and the compute conformance gate, with stated case counts. The
Nautobot runtime gate is only needed if something under `nauto`/`nintent` behavior actually changed
— the seed edit alone does not require it; say which you ran and why. Then against the live scratch
stack: `nctl drift` (JSON and human), `nctl drift --host agdnsmasq`, `nctl reconcile` dry, and
`nctl reconcile agdnsmasq` dry. Assert positively that `agdnsmasq` appears as two distinct
targets with distinct findings, that the compute instance matched VMID 108 at `match_basis=vmid`,
that its only non-informational finding is `compute_instance_not_linked`, and that both plans
contain zero compute actions and zero Proxmox calls. Diff the three render digests against Step 0.

*Exit:* the verification matrix in Section 8 is fully populated with real output.

### Step 7 — Report

Write `p1/report.md`: revision tuple, the state transition with evidence, the two Section 4.4
deviations, the declared-not-verified values, gate results with case counts, what is proven and what
is explicitly not, Phase 0's still-unmet fixture record, and the handoff to Phase 2. Bump the
`nauto` and `nctl` submodule pointers in the superproject.

*Exit:* one precise status, no unqualified `complete` if any check was omitted.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| canonical write | the two compute rows and the endpoint MAC entered the database through the Import Job's `apply=true` path, with its post-commit confirmation |
| idempotence | an identical second import reports every object unchanged and writes nothing |
| baked-seed integrity | the container's seed checksum equals the working-tree file's; the resolved `nintent` commit is unchanged |
| platform realization | drift names Cluster `aghub-proxmox` as `aghub-pve`'s realization, with its observation age |
| guest realization | drift names VirtualMachine `agdnsmasq` (VMID 108) as the instance's realization, with `match_basis=vmid` |
| separation | `agdnsmasq` appears as both a `node` target and a `compute_instance` target, with different statuses and different findings |
| non-adoption | a guest in another Cluster with the same name is never matched, proven by test |
| frozen vocabulary | every code in p0's table that Phase 1 implements is produced by at least one test; every deferred code is named as deferred and has no stub |
| unobservable fields | `template` and `unprivileged` produce no code under any tested input |
| no actuation | cluster and host-scoped dry plans contain zero compute actions; no compute code resolves to an `AUTOMATIC` classification |
| scoping | `nctl drift --host agdnsmasq` includes the compute instance; a plan for `aghub` does not plan anything for `agdnsmasq`'s guest |
| fail-closed | an unclassified compute error code still raises `UnclassifiedDiffCodeError` |
| contract ownership | the compute conformance gate passes unchanged; no compute rule is re-implemented in the evaluator |
| artifacts | the three render digests differ from Step 0 only where the seed edits explain it |
| gates | the gates actually run pass with stated case counts, and the report says which were skipped |

## 9. Reporting and completion states

Per `README_DEV.md` lesson 9: `complete` requires every Section 8 row exercised and passed, and a
skipped row must be visible and prevent an unqualified `complete`. A green test run is never
reported as live proof, and an absent finding is never reported as a converged one.

## 10. Exit criteria

Phase 1 is `complete` when:

1. `aghub-pve` and the `agdnsmasq` compute instance exist as desired rows written through the
   canonical Import path, and the identical import is a proven no-op;
2. `nctl drift` names the `agdnsmasq` compute realization separately from its guest-OS realization,
   with the matched Cluster, the matched VirtualMachine, and the match basis;
3. a stale, ambiguous, or missing platform, and a missing, ambiguous, conflicting, or unlinked
   guest, each produce their frozen code, each proven by a test;
4. compute source issues are visible in drift instead of silently dropped;
5. compute targets appear correctly in JSON drift, CLI drift, host-scoped drift, and reconcile
   classification;
6. no plan — cluster or host-scoped — contains a compute action, and no compute code names a
   reconciler;
7. `test_compute_actuation_inert.py` has been replaced by a test of the contract that now holds, and
   `MANIFEST.md` and `nctl/README.md` no longer claim compute produces no drift;
8. the three deterministic artifacts differ from the Step 0 baseline only as the seed explains; and
9. the report records the two classification deviations, the declared-not-verified values, and
   Phase 0's still-unmet fixture record.
