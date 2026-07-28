# First Proxmox Guest Realization — Phase 3 Plan: The Wish, the Records, and a Dry Create Plan

Parent: [roadmap.md](../roadmap.md) — Phase 3. Predecessors: [p0/report.md](../p0/report.md),
[p1/report.md](../p1/report.md), [p2/report.md](../p2/report.md).

## 1. Goal

Phase 1 made compute realization visible; Phase 2 made it recorded. Phase 3 makes it *requested*:
one confirmed wish becomes structured desired state, and the whole create path — preflight,
reconciler, handler, playbook — exists and is proven against fakes, while making zero Proxmox calls.

```text
current
  one desired compute instance (agdnsmasq, VMID 108), linked, converged
  + compute_instance_missing is manual_review with no reconciler
  + no create preflight, no create action, no Proxmox write path anywhere
  + Phase 0's fixture record is still unfrozen (its sole unmet exit condition)

to
  the fixture exists as a confirmed Braindump wish and as desired node + endpoint + compute instance
  + compute_instance_missing is AUTOMATIC -> create_compute_instance
  + every preflight failure mode has a named code and a test
  + one dry plan names exactly one guest, its control host, and the exact pct grammar
  + zero Proxmox calls have been made
```

Not in this phase: running the create (Phase 4), any `pct`/`qm`/pvesh write, any nintent change.

## 2. Boundary

The cluster is experimental and the Nautobot stack is scratch. Rebuild the image, restart, migrate,
re-run the Import Job, write and delete test rows freely. Module layout, file and code names, code
spellings beyond the frozen Phase 0 vocabulary, test structure, commit granularity, and step count
are yours.

**One prohibition: no Proxmox mutation.** No `pct`, `qm`, pvesh write, or playbook run against a
cluster node. Phase 4 owns the first one and a created guest cannot be rolled back. Reaching the
real Ansible/Proxmox boundary in this phase is only ever through a fake command runner.

Two mechanical facts, not ceremonies: the seed YAML is baked into the image by `COPY` from the
**local** `nauto` checkout (Dockerfile line 24), so a desired write needs a local nauto commit plus
`docker compose build` — no GitHub push and no nintent change; and show the Import preview and the
dry plan to the operator before the apply.

## 3. Findings that shape the design

Measured on the live scratch stack and the checked-out tree, 2026-07-28.

1. **Starting revisions.** superproject `6204330`, nctl `70002cc`, nintent `0eae8a0`, nauto
   `6f2fbeb`, nodeutils `775ed7f`, ansible_agdev `66b31c8`, all clean. `nctl drift --json` returns
   13 targets; `compute_instance agdnsmasq` is `converged` with only its summary, and
   `compute_platform aghub-pve` carries the summary plus 8 `unexplained_compute_guest` infos.

2. **The template evidence exists in the ledger but nctl cannot read it.** Cluster
   `aghub-proxmox` carries `proxmox_storage_content` with key `aghub:local:vztmpl`, state
   `complete`, `evidence_observed_at=2026-07-27T22:20:28Z`, items exactly the two Ubuntu volids from
   p0. `_CLUSTER_PROXMOX_FIELDS` in `sources/actual.py` has no `storage_content` entry, so the
   template preflight is blocked on one small reader addition — the residual gap VM p2 recorded.

3. **`compute_instance_missing` is exactly the create trigger.** `_match_instance` emits it only
   when the platform matched (so it is fresh, complete, and identity-consistent — `_match_platform`
   already gates that) and no VMID or name candidate exists in that Cluster. Nothing else needs to
   be invented to know that a guest is wanted and absent.

4. **`parameters["host_slugs"]` is the seam for a control-node action.** `action_host_slugs`
   prefers it over the action's targets, and both the SSH preflight and the executor's
   post-actuation observation read it. So a create action targeted at the `compute_instance`
   (guest) but carrying `host_slugs=["aghub"]` gets SSH-gated on `aghub` and, with
   `requires_observation=True`, is followed automatically by a fresh nodeutils collection and
   ingest of `aghub` — which is precisely what turns the created guest into a linkable candidate
   for the Phase 2 `link_compute_realization` action in the next round. No new observation
   machinery is needed.

5. **The new node's own target cannot converge before manual access.** A desired node with no
   realized device yields `no_realized_object` (ERROR, manual_review) from `node_existence`, and
   an `approved`/`active` lifecycle also makes it production-composable, which will add its own
   `PRODUCTION_BLOCKING_NODE_CODES` finding. Both are target-local. This is what
   `waiting_for_manual_initial_access` has to explain (§4.4), otherwise Phase 4's "successful
   terminal" is indistinguishable from an error.

6. **A static endpoint plans no IPAM job.** `endpoint_evaluation` resolves a non-`dhcp_reserved`
   endpoint with no self-observation to `ipam_reconcile_observation_missing` (manual_review), so
   the fixture will not trigger `reconcile_ipam`. Combined with the Phase 0 DHCP decision
   (`generate_dnsmasq: false`, §4.6), the create action has **no** action dependencies.

7. **Lifecycle gates the whole thing.** hosts-intent and dnsmasq export `planned|approved|active`;
   production requires `approved|active`; `effective_lifecycle(node, platform)` must be
   `active|approved` for `select_compute_primary_endpoint` to be enforced at all. The fixture node
   must therefore be `approved` — a `planned` draft is deliberately not creatable.

8. **The instance config key set is closed.** `_INSTANCE_CONFIG_KEYS` is
   `{vmid, template, storage, bridge, unprivileged}`, owned by nintent's `compute_contract.py`.
   Anything the create grammar needs beyond those (a gateway, a DNS server, an SSH key) would be a
   contract change, a conformance regeneration, and a nintent push. §4.5 stays inside the closed
   set instead.

## 4. Design

### 4.1 Storage-content reader (nctl)

Add `storage_content` to `_CLUSTER_PROXMOX_FIELDS`/`ProxmoxClusterFacts` as
`dict[str, ProxmoxStorageScope]`, mirroring `nauto/jobs/proxmox_upsert.py:build_storage_content_entry`
(`node`, `storage`, `content_type`, `state`, `last_attempted_at`, `evidence_observed_at`,
`omitted_error_count`, `errors`, `items[{volid, content, format, size_bytes}]`).

One trap: `_read_proxmox_facts` nulls the **entire** `ProxmoxClusterFacts` on any validation error,
which would silently downgrade a healthy platform to `compute_platform_missing` because of one odd
storage row. Drop and count unparsable scopes inside the field validator instead of failing the
whole model. Existing drift output must stay byte-identical after this step.

### 4.2 Creation preflight

One pure module beside `compute_realization.py`, with the same single-owner rule — the evaluator,
the planner, and the handler all read it and none of them re-derives anything from a diff message:

```python
derive_compute_creations(snapshot, *, generated_at) -> dict[str, ComputeCreation]
```

Per desired instance whose realization is "platform matched, no guest candidate": the resolved
control node, the effective create parameters (vmid, template, storage, bridge, unprivileged,
vcpus, memory_mb, root_disk_gb, hostname, MAC), and an ordered tuple of failure
`(code, message, desired, actual)` — empty means create-ready.

Checks, all against the same fresh snapshot:

| Check | Code |
|---|---|
| effective lifecycle is `active`/`approved` (finding 7) | (no code: not create-ready, no diff) |
| exactly one NIC-bearing primary endpoint | `compute_primary_endpoint_missing` / `_ambiguous` (exist) |
| template volid present in a `complete`, fresh `vztmpl` scope for a platform node | `compute_template_unavailable` |
| rootfs storage evidenced on the platform (storage-content scope or an observed LXC rootfs) | `compute_storage_unavailable` |
| bridge evidenced on the platform (any observed VMInterface bridge) | `compute_bridge_unavailable` |
| VMID unused by any observed guest in the Cluster and unrequested by another desired instance | `compute_vmid_conflict` |
| endpoint MAC not on any observed VMInterface/Interface | `compute_endpoint_mac_conflict` (exists) |
| endpoint IP not held by another desired endpoint or an observed IPAddress | `compute_endpoint_ip_conflict` |
| control node resolves into the composed production inventory (the Ansible target exists) | `compute_control_node_not_actionable` |

New codes are ERROR on the `compute_instance` target and MANUAL_REVIEW in `classify.py`. Desired-side
MAC/VMID duplication is already covered by `compute/collection.py` and is not re-implemented.

`compute_platform_observation_stale` moves from MANUAL_REVIEW to OBSERVATION routed at the
**control node** — a stale platform is the one compute failure a fresh observation actually fixes,
and creation cannot proceed without it. This needs the diff to carry the control node's slug and
`planner.build_plan`'s OBSERVATION branch to retarget a compute diff the way it already retargets a
service diff. If that retargeting turns out to be more than a few lines, leave the code
MANUAL_REVIEW and report the p1/p2 deviation as still open — it is not worth a redesign here.

### 4.3 Reconciler and action

```python
Reconciler(id="create_compute_instance", action_kind="compute_create",
           mutates=True, requires_observation=True)
```

`requires_observation=True` per finding 4: the control node must be re-observed and re-ingested
immediately after a create, in the same operation.

One action per create-ready instance, anchored on the `compute_instance` target: id
`create_compute_instance:<guest node slug>`, `claimed_diff_codes=["compute_instance_missing"]`,
`dependencies=[]` (finding 6), `parameters` = `host_slugs=[<control node slug>]` plus the entire
pinned create grammar, `evidence` = the platform, Cluster, control node, and the observation
timestamps the derivation read. `classify.py`: `compute_instance_missing` becomes AUTOMATIC ->
`create_compute_instance`.

`plan_create_compute_instance` returns `Fallback(MANUAL_REVIEW, …)` — never an action — when the
instance is not create-ready for any reason in §4.2, when a guest candidate exists (that is
Phase 2's link, not a create), or when the instance already carries a `realized_vm` link.

### 4.4 `waiting_for_manual_initial_access`

One narrow predicate in the same pure module: a desired node is *awaiting initial access* when its
compute instance is linked to an observed guest, that guest is running, the node has no realized
device, and no nodeutils observation for it exists. When true:

1. `node_existence` emits `waiting_for_manual_initial_access` (INFO) **instead of**
   `no_realized_object`;
2. the production composer excludes the node with that reason rather than a blocking code; and
3. the create planner refuses to plan anything for it.

Every one of the four conditions gets a test showing that dropping it restores `no_realized_object`.
This is the whole of the terminal — no other code, status, or gate is suppressed, and the guest-OS
node target simply resumes ordinary evaluation once the operator finishes the console bootstrap and
the node is observed.

### 4.5 Handler and playbook

`reconcile/actions/compute_create.py`, registered in `dispatch.py` as
`ActionHandler("create_compute_instance", …, "bootstrap", False)`:

1. Re-derive from `context.snapshot`; any difference from `action.parameters` fails **before** the
   runner is touched.
2. Run, through the existing `AnsibleRunner` and operation inventory:
   `ansible-playbook -i <inventory> playbooks/proxmox/create_lxc.yml --limit <control host>
   --extra-vars <pinned JSON incl. result_path under the operation artifacts>`.
3. Require the playbook's result file to exist and to record `created`/`started` with the exact
   argv used. Exit code 0 with no result file is a failed action, not a success.
4. `mutated=True` from the moment the runner is launched — a failure after `pct create` must
   preserve partial progress; the next round's fresh observation, not an assumption, decides what
   exists.

The playbook is new, `become: true`, `gather_facts: false`, argv-form `ansible.builtin.command`
only, absolute `/usr/sbin/pct`:

- `pct status <vmid>` as an execution-time absence gate — a guest already at that VMID fails the
  play with no further command;
- `pct create <vmid> <template> --hostname … --cores … --memory … --rootfs <storage>:<gb>
  --net0 name=eth0,bridge=<bridge>,hwaddr=<mac> --unprivileged <0|1> --onboot 1`;
- `pct start <vmid>`;
- write the result JSON.

**The NIC gets no address configuration.** Per finding 8 the closed config key set has no gateway,
and per Phase 0 the initial network, user, key, and SSH setup are the manual console step. The
desired static IP stays intent that the manual bootstrap satisfies and a later observation
verifies. No `pct stop`, `destroy`, `set`, `resize`, or `migrate` exists anywhere in the playbook,
the role, or the handler.

### 4.6 The fixture record

Candidate values, to be confirmed by the operator in Step 1 and re-checked for collision in Step 0.
`agdnsmasq` is the model row; VMIDs 100-108 and the static pool `192.168.0.2-9` are in use as of
p0/today.

| Field | Candidate |
|---|---|
| node slug / name | `agfixture` |
| node_type / accepted_actual_types / lifecycle | `service_host` / `[virtual_machine]` / `approved` |
| VMID | `109` |
| template | `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst` |
| storage / bridge / unprivileged | `local-lvm` / `vmbr0` / `true` |
| vCPU / memory / root disk | `1` / `512` MiB / `8` GiB |
| endpoint | `primary`, `ip_policy: static`, `192.168.0.9`, `generate_dnsmasq: false` |
| MAC / dns / mdns | `bc:24:11:00:01:09` / `agfixture.home.arpa` / `agfixture.local` |
| disposition after Phase 5 | operator's call (kept or destroyed by hand) |

`generate_dnsmasq: false` is what keeps the dnsmasq render digest unchanged and the create action
free of a dnsmasq dependency, implementing the Phase 0 DHCP decision.

### 4.7 Unchanged

Every other diff code, message, and severity; the dnsmasq render digest; `nctl.drift.v1` and
`nctl.reconcile.v2` field sets; every pre-existing action; the compute contract, its conformance
fixture, and all of nintent.

## 5. Steps

Merge or split as convenient. Only real ordering constraints: the storage reader proves
byte-identical drift before any behavior change; the code lands before the rows, so the fixture's
first appearance in live drift is already understood; the dry plan is the last thing.

0. **Baseline.** Revision tuple, deployed nintent/nauto commits and seed checksum,
   `nctl drift --json`, the three render digests, the current guest/VMID set, and the desired and
   observed MAC/IP inventory the fixture must not collide with. Refresh the Proxmox observation if
   it is outside 72h.
1. **Wish and freeze.** Record the operator's wish through `nctl braindump create`, present the
   §4.6 proposal, and get explicit confirmation. This closes Phase 0's sole open item; record the
   confirmed values in the phase report. The wish is not the write.
2. **Storage-content reader** (§4.1). Exit: drift byte-identical, live and in tests; the two Ubuntu
   volids are visible through the typed read.
3. **Preflight module, codes, classification** (§4.2), plus the evaluator emission. One test per
   failure code, each proving that only that code fires and the instance is not create-ready.
4. **Reconciler, planner wiring, terminal** (§4.3, §4.4). Tests: the action is planned exactly once
   with the exact parameters; each Fallback branch declines; the target set is one
   `compute_instance` and the host set is one control node; a plan for another node plans nothing
   for the fixture; the four terminal conditions.
5. **Handler and playbook** (§4.5) against a fake command runner. Cover: the exact argv and
   extra-vars issued; parameters changed between plan and execution -> refused before the runner;
   missing result file -> failure; non-zero exit -> failure with `mutated=True`; an unrelated guest
   never named in any command. Static assertion: no stop/delete/resize/migrate string exists in the
   repository's create path.
6. **Replace `tests/test_compute_actuation_inert.py` again** — it currently asserts exactly one
   `ledger_patch` and no Proxmox-capable action, and the second half is now deliberately false.
   Successor: a create-ready instance produces exactly one `compute_create` action that names one
   guest, and a dry plan executes nothing. Update the `compute-inert` MANIFEST row, `nctl/README.md`
   (comparator/reconciler/handler sections), and `ansible_agdev/README.md` for the new playbook.
7. **Write the fixture rows.** Extend `nauto/seed/intent_sources.yaml` with the node, endpoint, and
   compute instance; commit nauto; `docker compose build` (the seed is `COPY`d, so verify the baked
   checksum equals the checkout) and restart. Import Job preview first — it must show exactly three
   creates and nothing else — then the operator-approved `apply=true`, then an identical repeat run
   proving a no-op.
8. **Dry plan, artifacts, gates, report.** `nctl reconcile agfixture` and a whole-cluster dry plan:
   one `create_compute_instance` action naming VMID 109, `aghub` as its host, and the exact create
   grammar; zero Proxmox calls; unrelated nodes and guests unaffected. Diff the three render digests
   against Step 0 and explain every difference by the fixture (dnsmasq: unchanged; hosts-intent:
   the fixture added; production: unchanged until manual access). Gates with stated case counts:
   nctl ordinary, Ansible conformance, nauto ordinary, Nautobot runtime. Write `p3/report.md` and
   bump the `nctl` and `nauto` pointers.

## 6. What must be proven

| Area | Proof |
|---|---|
| the wish is traceable | a Braindump record exists and the confirmed proposal's values equal the written rows |
| prose never actuates | the create action derives only from structured rows; the wish text is never read by the planner |
| single owner | one preflight derivation feeds evaluator, planner, and handler; drift byte-identical across the storage-reader step |
| every failure has a code | each §4.2 row has a named code, a test, and a `Fallback` that refuses to plan |
| template truth | the create is refused when the volid is absent, the scope is stale, or the scope state is not `complete` |
| exact scope | one `compute_instance` target, one control host, one VMID through plan and (faked) actuation |
| the create would be issued | positive assertion on the exact `pct create` and `pct start` argv, not merely absence of error |
| plan/apply separation | the dry plan runs zero commands and makes zero Proxmox calls |
| no repeat create | an instance with a candidate, or with a `realized_vm` link, or awaiting manual access plans no create |
| the terminal is explicit | `waiting_for_manual_initial_access` replaces `no_realized_object` only under all four conditions |
| partial progress | a post-launch handler failure reports `mutated=true` and preserves the evidence |
| target isolation | the fixture's findings block only the fixture; `agdnsmasq`, `aghub`, and the other nodes are unchanged |
| no deletion path | no stop/delete/resize/migrate exists in the handler, the playbook, or any role it uses |
| durability | the repeat Import run is a no-op and the Phase 2 links still resolve |
| artifacts | the three digests differ from Step 0 only where the fixture explains it |
| gates | the four gates pass with stated case counts |

## 7. Reporting

`p3/report.md`: revision tuple, the confirmed fixture record (closing Phase 0), the state transition
with evidence, the `compute_instance_missing` classification flip, the
`compute_platform_observation_stale` deviation resolved or still open, the third replacement of the
inert test, the Import preview/apply/repeat JobResult ids, the dry-plan artifact path, gate results,
what is proven (one confirmed wish is structured desired state and produces one truthful create
plan) and what is not (nothing created, no Proxmox call made, no QEMU path), and the handoff to
Phase 4 — which must re-run this exact dry plan unchanged before applying.

Per `README_DEV.md` lesson 9, any omitted row above is visible and prevents an unqualified
`complete`. If the operator does not confirm the fixture values, the status is `blocked` on that
one input and the code steps still land as `implemented, not deployed`.
