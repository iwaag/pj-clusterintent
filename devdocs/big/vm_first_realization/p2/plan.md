# First Proxmox Guest Realization — Phase 2 Plan: Link One Existing Guest Through a Ledger Write

Parent: [roadmap.md](../roadmap.md) — Phase 2. Predecessors: [p0/report.md](../p0/report.md),
[p1/report.md](../p1/report.md).

## 1. Goal

Phase 1 made compute realization visible. Phase 2 makes it recorded: build the one path that can
write a realization link, use it on a guest that already exists, and prove it is exact and
non-repeating — before Phase 4 uses the same machinery on a guest that does not exist yet.

```text
current
  compute_instance agdnsmasq: compute_instance_not_linked (warning), match_basis=vmid
  + compute_platform aghub-pve: matched by scope identity, realized_cluster unset
  + no nintent surface can write either link
  + compute_instance_not_linked classified MANUAL_REVIEW, no reconciler, no handler

to
  aghub-pve.realized_cluster = the observed aghub-proxmox Cluster (source=derived)
  + agdnsmasq.realized_vm = the observed VMID-108 VirtualMachine (source=derived)
  + both written by one plan-named, GraphQL-confirmed action
  + compute_instance_not_linked gone, match_basis=linked, repeat plan has zero compute actions
```

Not in this phase: creating a guest, any Proxmox call, the new fixture record (Phase 0's remaining
open item — irrelevant here, this phase links a guest that has existed for months).

## 2. Boundary

The cluster is experimental and the Nautobot stack is scratch. Restart, rebuild, migrate, write test
rows, and revert the link (`PATCH {"realized_vm": null, "realized_vm_source": null}`) freely. Module
layout, file and code names, error spellings, test structure, commit granularity, and step count are
all yours.

**One prohibition: no Proxmox mutation.** No `pct`, `qm`, pvesh write, or playbook against a cluster
node. Phase 4 owns the first one, and a created guest cannot be rolled back.

Two mechanical facts, not ceremonies: the nintent change only reaches the container via GitHub, so
ask the operator to push before rebuilding; and show the dry plan before `--yes` so the approved
candidate is the one that gets written.

## 3. Findings that shape the design

Measured on the live scratch stack and the checked-out tree, 2026-07-28.

1. **The starting point.** `nctl drift --json` returns 13 targets. `compute_instance agdnsmasq` is
   already **`converged`** — its only finding is a *warning* — carrying
   `compute_instance_not_linked` plus `compute_realization_summary`. So the link landing does not
   flip a status; the proof is the diff disappearing and `match_basis` going `vmid` → `linked`.
   `compute_platform aghub-pve` carries the summary plus eight `unexplained_compute_guest` infos.

2. **No writer exists, and its absence was delegated here.** `nintent/…/api/urls.py` registers only
   `nodes`, `braindumps`, `alignment-reviews`; `interface_contract` Phase 2 deleted both compute
   serializers and ViewSets, and `tests/test_api_contract.py` now *asserts* their absence in four
   places. That roadmap wrote the hand-off: "VM compute-linking work may later introduce one narrow
   real writer … That later roadmap owns the REST addition, dry plan, exact scope, refetch, and
   non-repetition proof." Both compute FilterSets were retained.

3. **Two writes, in a forced order.** `models.py:842-861` rejects `realized_vm` unless the platform's
   `realized_cluster` is already set and the VM's cluster equals it; it also requires
   `proxmox_guest_type` to match `instance_kind` and `config.vmid` to equal `proxmox_vmid`. Platform
   link first, instance link second. nintent is thus an independent second gate on the same identity
   rules — worth proving with a real request rather than assuming.

4. **The evaluator derives the candidate and throws it away.** `evaluate_compute` yields only
   `DiffRecord`s. A reconciler reading the candidate back out of a diff message is what Decision 2
   forbids; `plan_link_actual_node` shows the alternative (re-derive from typed evidence). Phase 2
   extracts the derivation and gives it two consumers.

5. **Host scope can never reach a `compute_platform` target.** `select_scoped_diffs`,
   `drift_render`'s `--host` filter, and the executor summary all select compute targets by *owning
   node slug*; a platform target carries the platform slug. A platform-anchored action would be
   unplannable in exactly the scope this phase uses — so the platform link is a dependency write
   inside the instance-anchored action, not its own action.

6. **Freshness is already gated.** `_match_platform` returns no match for a missing/unparsable/
   >72h/incomplete observation, so `compute_instance_not_linked` only ever appears against a fresh
   platform. Re-derive at execution time anyway; the handler runs after the plan.

7. **The compute target and the node target share a slug.** `derive_status` resolves
   `latest_convergent_actuation_for_target` by slug alone, so the link's actuation event is visible
   to node `agdnsmasq`'s status derivation. It cannot produce a false `converging` only because that
   node's error (`stale_actual_data`) is not in the action's `claimed_diff_codes`. Assert it.

8. **The host-scoped apply will also contain a failing observation.** Node `agdnsmasq` carries
   `stale_actual_data` (an OBSERVATION code) and the host is unreachable, so `observe_node` is
   planned and fails. `observe.py` returns `success=False` without terminal errors, so the round
   continues and the link's evidence survives — but the operation will not report `converged`.
   Report the link's own success separately; do not read the roadmap's "fresh drift converges" as
   anything more than the compute finding disappearing.

9. **Two things routinely rewrite this data.** The Import Job never writes realized fields
   (`desired_compute_*_defaults`) but does re-run `full_clean()`, which after the link exercises
   finding 3's validations. nauto matches clusters by `proxmox_scope_key` and guests by
   `(guest_type, vmid)` and updates in place, so UUIDs are stable. Both are cheap to verify and a
   dangling link degrades to a code that by design never re-links.

## 4. Design

### 4.1 nintent writer

Two collections mirroring `DesiredNodeViewSet`/`DesiredNodeSerializer` exactly:

```text
GET, PATCH  /api/plugins/intent-catalog/compute-platforms/<uuid>/
GET, PATCH  /api/plugins/intent-catalog/compute-instances/<uuid>/
```

`http_method_names = ["get", "patch", "head", "options"]`; POST/PUT/DELETE/bulk → 405. Explicit
`fields`; writable set exactly `{realized_cluster, realized_cluster_source}` and
`{realized_vm, realized_vm_source}`. Reuse `_check_allowed_mutation_keys` and
`DesiredNodeSerializer.validate`'s pairing rule. Explicit `null` clears the link (that is the
rollback path; reverse order — instance first, then platform). No model change, no migration, no
compute-contract change, so no conformance fixture regeneration.

nintent tests: route/method/field matrix for both collections; unallowed key → 400 with zero write;
**`realized_vm` before the platform link → 400 with zero write, then the ordered pair → 200**; wrong
cluster / wrong guest type / mismatched VMID each → 400 with zero write. Shrink the four removal
lists in `test_api_contract.py` by exactly the two compute entries each. Update
`nintent/README.md` and `README_DEV.md` §"REST API" (5 retained collections now).

### 4.2 Derivation seam

Extract the matching decision out of `drift/compute_evaluation.py` into a pure module, e.g.:

```python
derive_compute_realizations(snapshot, *, generated_at) -> dict[str, ComputeRealization]
```

carrying, per desired instance: the platform row, matched Cluster or `None`, platform failure codes,
matched VirtualMachine or `None`, instance failure codes, `match_basis`
(`linked`/`vmid`/`name`), and each row's link state (`absent`/`linked_to_expected`/`linked_to_other`).
`evaluate_compute` becomes its renderer; the planner is the second consumer. Land this refactor
separately from the behavior change, with byte-identical drift as its exit. Keep both modules in
`test_module_boundaries.py`'s purity list and `test_reconcile_classify.py`'s `_SCANNED_FILES` /
`_COMPUTE_CODES`.

### 4.3 Reconciler and action

```python
Reconciler(id="link_compute_realization", action_kind="ledger_patch",
           mutates=True, requires_observation=False)
```

`requires_observation=False` — a link changes nothing observable, and `True` would enqueue a
post-actuation `observe_node` against an unreachable host (findings 5, 8).

One action per desired compute instance, anchored on the `compute_instance` target: id
`link_compute_realization:<node slug>`, `claimed_diff_codes=["compute_instance_not_linked"]`,
`dependencies=[]`. `parameters` pin both writes (instance/vm, platform/cluster, `platform_link_state`,
`match_basis`); `evidence` records the platform and control node the derivation *read*, so dependency
closure is checkable from the plan artifact alone.

`plan_link_compute_realization` returns `Fallback(MANUAL_REVIEW, …)` — never an action — when no
unique candidate is derivable, the platform did not match or is stale, or either row is
`linked_to_other`.

`classify.py`: move `compute_instance_not_linked` to `AUTOMATIC` → `link_compute_realization`. This
closes p1 §4.4 deviation 1. Leave `compute_platform_observation_stale` as `MANUAL_REVIEW` — p1
expected Phase 2 to promote it, but per finding 6 a stale platform produces no match and therefore no
action, so there is nothing to route. Record the deviation as still open rather than as resolved.

**No new drift code.** `compute_platform_not_linked` is deliberately not added: an unlinked platform
with instances is already explained by the instance's finding, one with zero instances has nothing to
link for, and per finding 5 it could never be selected in host scope. Surface platform link state in
the existing `compute_realization_summary` evidence instead. Link-time failures are
`LedgerActionError` codes at the action boundary, which need no classification entry.

### 4.4 Handler

`reconcile/actions/compute_link.py` registered in `dispatch.py` as
`ActionHandler("link_compute_realization", …, "bootstrap", True)`; the write itself in
`reconcile/ledger.py` (whose docstring currently says compute linking is out of scope — update it),
keeping that module the single place `nctl reconcile` writes to the ledger.

1. Re-derive from `context.snapshot`; a candidate differing from `action.parameters` fails without
   writing.
2. Pre-read both rows through the canonical GraphQL snapshot.
3. Platform: `absent` → PATCH `{realized_cluster, realized_cluster_source: "derived"}`;
   `linked_to_expected` → skip, recorded as `already_correct`; linked elsewhere → fail, no write.
4. Refetch and assert both fields landed exactly.
5. Instance: same three-way branch → PATCH `{realized_vm, realized_vm_source: "derived"}`.
6. Refetch and assert.
7. Return node slug, both object ids/names, VMID, `match_basis`, and which writes actually happened.

`mutated` is owned by the writer that crossed the boundary: a failure at step 6 after a successful
step 3 still reports `mutated=True`, so partial progress survives.

### 4.5 Unchanged

Every other diff code, message, and severity; the three render digests (a link is not an input to
production composition, dnsmasq, or hosts-intent — a change there is a defect until explained);
`nctl.drift.v1` and `nctl.reconcile.v2` field sets; every pre-existing action.

## 5. Steps

Merge or split as convenient. Only real ordering constraints: the derivation extraction proves
byte-identical drift before any behavior change; nintent is deployed before the apply.

0. **Baseline.** Revision tuple, deployed nintent/nauto commits, `nctl drift --json`, three render
   digests, both rows' current link state, and the exact Cluster/VirtualMachine UUIDs the derivation
   produces. Refresh the Proxmox observation first if it is outside 72h.
1. **Extract the derivation** (§4.2). Exit: drift output byte-identical, live and in tests.
2. **nintent writer** (§4.1) + its tests + docs; commit locally.
3. **Reconciler, classification, planner wiring** (§4.3). Tests: the action is planned; each Fallback
   branch declines; the target set is exactly one `compute_instance`; a plan for another node plans
   nothing for `agdnsmasq`; finding 7's guard holds.
4. **Handler** (§4.4) against a fake client. Cover: both writes; platform already correct → one
   write; either row linked elsewhere → refused with correct `mutated`; PATCH non-2xx; refetch
   mismatch / wrong source / refetch failure — each preserving `mutated=True`; candidate changed
   between plan and execution.
5. **Replace `tests/test_compute_actuation_inert.py`** — it currently asserts `instance-1` lands in
   `plan.manual_review` and that no action targets a compute kind, both now false. Successor: the
   real comparator and planner produce exactly one `ledger_patch` action for the compute instance and
   zero Proxmox-capable actions. Update the `compute-inert` MANIFEST row and `nctl/README.md`'s
   comparator section (still says compute "does not write a realization link or authorize an action").
6. **Deploy.** Operator pushes nintent; `docker compose build --no-cache`; restart web/worker/
   scheduler. Verify the resolved nintent commit in `build_info.json` and the image label equals the
   pushed SHA (a cached layer has carried a stale plugin commit before) and the seed checksum is
   unchanged. Confirm both collections respond and the API token's user may PATCH them. `nctl drift`
   unchanged.
7. **Dry plan → apply.** `nctl reconcile agdnsmasq` must name one link action with both UUIDs, VMID
   108, and the two fields; the accompanying `observe_node` is the pre-existing unrelated one
   (finding 8). Show it, then `nctl reconcile agdnsmasq --yes --max-rounds 1`.
8. **Durability + gates + report.** Re-run the Import Job with `apply=true` (still a full no-op, no
   validation failure); one read-only observation + ingest (links still resolve, drift unchanged).
   Gates with stated case counts: nctl ordinary, compute conformance, nintent fast (14 expected
   skips), Nautobot runtime. Write `p2/report.md`; bump the `nintent` and `nctl` pointers.

## 6. What must be proven

| Area | Proof |
|---|---|
| writer is narrow | GET + detail PATCH only, 405 elsewhere; unallowed key → 400 with a refetch showing zero write |
| model gates are real | `realized_vm` before the platform link → 400 zero write; wrong cluster / guest type / VMID likewise; the ordered pair succeeds |
| single owner | one derivation feeds evaluator and planner; drift byte-identical across the extraction |
| plan/apply separation | the dry plan writes nothing and names both objects by UUID |
| exact scope | one `compute_instance` target; exactly two fields on two rows |
| the write ran | `success=true`, `mutated=true`, both writes named, GraphQL refetch equals the approved candidate |
| confirmation is part of success | a refetch mismatch fails the action while preserving `mutated=true` |
| never replaces | a row linked elsewhere is refused with zero writes on it |
| non-repetition | fresh drift has no `compute_instance_not_linked`; a repeat dry plan has zero link actions |
| dependency closure | the plan records reading `aghub-pve` and `aghub`, and plans nothing for another guest or node |
| status isolation | the link's actuation event does not flip node `agdnsmasq` to `converging` |
| durability | post-link Import re-run is a no-op; post-ingest the links still resolve |
| no Proxmox path | zero Proxmox calls; no create/start/stop/delete/resize code anywhere |
| artifacts | the three render digests equal step 0 |
| gates | the four gates pass with stated case counts |

## 7. Reporting

`p2/report.md`: revision tuple, the state transition with evidence, the classification flip and the
still-open `compute_platform_observation_stale` deviation, the interface-manifest amendment (two REST
collections reinstated under `interface_contract`'s written hand-off), the second replacement of the
inert test, gate results, what is proven (one existing guest linked) and what is not (nothing
created, no Proxmox write path), and the handoff to Phase 3.

Per `README_DEV.md` lesson 9, any omitted row above is visible and prevents an unqualified
`complete`. The `observe_node` failure is unrelated pre-existing drift, reported as such. If the
push does not happen, the status is `implemented, not deployed` — not `blocked`.
