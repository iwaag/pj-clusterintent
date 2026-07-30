# Retire core Phase 2 — implementation plan: observe guest absence

Parent: [roadmap.md](../roadmap.md) — Phase 2. Predecessors: [p0/report.md](../p0/report.md),
[p1/report.md](../p1/report.md).

Status: proposed. One seed change, one nauto ingest rule, one nctl read projection, one scratch
deployment. No schema migration, no drift semantics, no destroy code, no Proxmox call.

## 1. Goal

Make a complete Proxmox observation authoritative about whether a previously known guest still
exists, and record that in the Actual ledger without deleting anything.

```text
current
  a guest that disappears from Proxmox leaves its VirtualMachine row untouched;
  nothing in Nautobot or nctl can state that the guest is gone

after Phase 2
  proxmox_presence also applies to virtualization.virtualmachine
  + every guest in a validated observation is written present
  + after a complete platform observation, previously known in-scope guests omitted
    from it are written absent
  + partial, failed, stale, or different-scope evidence never writes absent
  + nctl's typed VM facts carry presence and show it in ordinary compute evidence
  + zero new drift codes, zero classification changes, zero action changes
```

Phase 3 consumes presence. Phase 2 must not anticipate it: no `compute_instance_destroy_required`,
no `compute_instance_removal_complete`, no planner change, no `--allow-destroy`.

## 2. Frozen inputs from Phase 0

| Input | Value |
|---|---|
| field | reuse the existing CustomField key `proxmox_presence`, values `present` \| `absent` |
| attach | add `virtualization.virtualmachine` to that field's content types; no second presence key |
| present rule | every guest in a validated observation is `present` |
| absent rule | only a **complete** observation of the **same Proxmox scope** may write `absent`, and only to previously known in-scope guests it omitted |
| never absent | partial, failed, stale, or conflicting evidence leaves the last presence evidence unchanged |
| required projections | seed content types + description, guest upsert writes `present`, complete-observation absence sweep, nctl `ProxmoxVirtualMachineFacts.presence` + `_VM_PROXMOX_FIELDS` |
| retained | VirtualMachine, VMInterface, IP, and Device rows; this initiative deletes no Actual row |

## 3. Findings that shape the plan

Measured on the checked-out tree (superproject `22bde35`, nauto `3bd1820`, nctl `49f4355`,
nodeutils `775ed7f`) on 2026-07-30.

**F1 — completeness is already a trustworthy end-to-end signal; do not invent a second one.**
nodeutils enumerates guests per node over the observed node list, and a truncated node list or any
failed `/nodes/<node>/qemu|lxc` listing sets `collection.state = "partial"`
([proxmox_inventory.py:646-766](../../../../../../nodeutils/proxmox_inventory.py#L646-L766)).
`validate_proxmox_facts` folds `collection.state` and every rejected guest/storage item into
`ProxmoxValidationResult.state`
([proxmox_ingest.py:191-227](../../../../../../nauto/jobs/proxmox_ingest.py#L191-L227)).
`ingest_proxmox_platform` additionally raises `platform_partial` for any guest whose savepoint rolled
back and for any partial storage scope. Its `final_state == "complete"`
([proxmox_upsert.py:680](../../../../../../nauto/jobs/proxmox_upsert.py#L680)) therefore already means
"every guest on every node of this cluster was enumerated and written in this generation" — exactly
the condition under which omission proves absence.

**F2 — the identical rule already exists one level down.** `sync_guest_interfaces` marks
previously managed VMInterfaces missing from a *complete* config enumeration
`proxmox_presence=absent`, guarded by `config_complete`, keyed on this generation's candidate slots,
skipping rows already absent
([proxmox_interfaces.py:544-573](../../../../../../nauto/jobs/proxmox_interfaces.py#L544-L573)).
Phase 2 is the same rule at guest level, keyed on `(guest_type, vmid)`. Reuse its shape and its
`PRESENCE_PRESENT`/`PRESENCE_ABSENT` constants rather than defining a parallel vocabulary.

**F3 — presence must join the allowlisted diff, and that has one transitional hazard.**
`upsert_with_freshness` ([proxmox_upsert.py:331](../../../../../../nauto/jobs/proxmox_upsert.py#L331))
is the single freshness/no-op authority, so `proxmox_presence: "present"` belongs in `guest_cf`
([line 596](../../../../../../nauto/jobs/proxmox_upsert.py#L596)); reappearance then works for free.
But existing VM rows carry no `proxmox_presence`, so re-ingesting a report whose `observed_at` equals
the stored one compares unequal at an equal timestamp and returns `conflicting_same_generation` for
every guest. The first post-deploy ingest must be a fresh collection, not a replay. State this in
the report; do not add a compatibility branch for it.

**F4 — the sweep's scope is the matched Cluster, with two restrictions.** Guests are matched within
`cluster` ([match_guest:178](../../../../../../nauto/jobs/proxmox_upsert.py#L178)), so the sweep set
is `vm_manager.filter(cluster=cluster)`. It must skip (a) rows lacking `proxmox_guest_type` or
`proxmox_vmid` — a hand-made VirtualMachine row in the same Cluster is not this ingestor's to mark
absent — and (b) any row whose recorded `proxmox_observed_at` is newer than this generation's
`validation.observed_at`, mirroring the stale rule at
[lines 364-368](../../../../../../nauto/jobs/proxmox_upsert.py#L364-L368).

**F5 — ordering.** `final_state` is computed after guest processing and immediately before the
Cluster's observation fields are written
([lines 680-689](../../../../../../nauto/jobs/proxmox_upsert.py#L680-L689)). The sweep belongs in
that gap. Anything the sweep itself fails on must raise `platform_partial`, so recompute the state
after the sweep instead of writing one derived before it.

**F6 — nctl needs one allowlist entry and no semantics.** `_VM_PROXMOX_FIELDS`
([actual.py:395](../../../../../../nctl/src/nctl_core/sources/actual.py#L395)) and
`ProxmoxVirtualMachineFacts` ([line 333](../../../../../../nctl/src/nctl_core/sources/actual.py#L333))
are a closed allowlist; the VMInterface model already maps the same CF key
([line 413](../../../../../../nctl/src/nctl_core/sources/actual.py#L413)). `_select_allowlisted` drops
`None`, so a VM not yet touched by a presence-aware ingest reads `presence=None` — "not yet
observed", never "absent". `_match_instance`
([compute_realization.py:90](../../../../../../nctl/src/nctl_core/drift/compute_realization.py#L90))
deliberately keeps matching an `absent` VM as a realization in this phase; Phase 3 owns that.

**F7 — nauto deploys as a Nautobot Git Repository, and the seed change is the whole migration.**
`ensure_object` calls `.set()` on `content_types` on every sync when `update_existing=true`
([seed_home_cluster.py:138-145](../../../../../../nauto/jobs/seed_home_cluster.py#L138-L145)), so
re-running **Seed Home Cluster** with `dry_run=false` attaches the field. There is no Django
migration and no container rebuild requirement — but nauto must be pushed and the Git Repository
re-synced, and `NAUTO_COMMIT` in
[devenv/nautobot/Dockerfile:7](../../../../../../devenv/nautobot/Dockerfile#L7) should be bumped so
`build_info.json` keeps recording the truth.

## 4. Design decisions

### 4.1 Seed

In [nauto/seed/home_cluster.yaml:482](../../../../../../nauto/seed/home_cluster.yaml#L482) add
`virtualization.virtualmachine` to the existing `proxmox_presence` entry's `content_types` and
broaden its interface-only description to cover complete scoped enumeration of both guests and
interfaces. Nothing else in the seed changes.

### 4.2 nauto ingest

Write `proxmox_presence: PRESENCE_PRESENT` as part of `guest_cf` so it flows through
`upsert_with_freshness` (F3).

Add one absence sweep inside `ingest_proxmox_platform`, in the gap identified by F5, gated on the
final platform state being `complete`. For each managed VM in the matched Cluster whose
`(guest_type, vmid)` is absent from this generation's observed set, and which passes the F4
restrictions and is not already `absent`: set `proxmox_presence=absent` and advance
`proxmox_observed_at` to this generation, so downstream freshness checks can tell how recently
absence was established. Count it as a `vm` update and record it in `changed_fields`.

Do not touch that guest's VMInterfaces, IP relations, Device, status, node, or resource fields — the
row keeps its last-known realization evidence; only presence and its evidence time move.

Keeping the sweep in this pure module (no Django import) is deliberate: it stays unit-testable
against the existing fake-ORM doubles, exactly like the interface-level rule.

### 4.3 nctl read projection

- `ProxmoxVirtualMachineFacts`: `presence: str | None = None`.
- `_VM_PROXMOX_FIELDS`: `"presence": "proxmox_presence"`.
- `compute_evaluation._summary` ([line 126](../../../../../../nctl/src/nctl_core/drift/compute_evaluation.py#L126)):
  add the matched VM's presence to the **actual** side of `compute_realization_summary`, mirroring
  what Phase 1 did for `desired_presence` on the desired side. This is the whole of Phase 2's drift
  change: no new code, no severity change, no classification entry, no planner change, no matcher
  change.

### 4.4 Live proof target

`agfixture` stays `approved/present` — it is Phase 5's recorded acceptance start state, and this
phase performs no Proxmox mutation, so a real disappearance cannot be staged.

Prove the transition instead with a **disposable synthetic VirtualMachine row** in the scratch
Nautobot: create one inside the observed Cluster carrying `proxmox_guest_type`, a VMID that exists on
no Proxmox node, and a `proxmox_observed_at` older than the next collection. Run an ordinary
observation and ingest, confirm the synthetic row flips to `absent` while every real guest —
`agfixture` included — is written `present` and the platform stays `complete`, then delete the
synthetic row. This is a scratch-Nautobot write only; no cluster node is contacted beyond the normal
read-only observation.

### 4.5 Explicitly unchanged

No Actual row is deleted. Interfaces, IP evidence, and Device rows of an absent guest are retained
untouched. No drift code, severity, classification, action, CLI option, or render output changes.
No second presence key, and no persistent third presence value — an untrustworthy observation is
already expressed by the platform's own observation state.

## 5. Steps

Merge or split freely. The only real ordering constraints are that the pure rule lands before the
deployment, and that the seed is applied before the first presence-writing ingest.

### Step 0 — Baseline

Record the revision tuple, the deployed nauto commit, `nctl drift --json`, the current Cluster's
`proxmox_observation_state`, and the current VirtualMachine rows with their `proxmox_observed_at`
and (absent) presence values. This is the before-picture Step 4 must show as unchanged apart from
the new field.

*Exit:* baseline recorded.

### Step 1 — nauto rule and tests

Implement §4.2. Tests against the existing fake-ORM doubles in `nauto/tests/`: every observed guest
is written `present`; a complete observation omitting a previously known guest marks exactly that
guest `absent` and nothing else; a partial observation (failed guest list, rejected guest, partial
storage, guest savepoint rollback) writes no absence; a reappearing guest returns to `present`; an
older-than-recorded observation neither updates nor marks absent; an unmanaged VM row in the same
Cluster is never marked absent; a guest in a different Cluster is out of scope; interfaces, IPs, and
resource fields of an absent guest are untouched; and an already-`absent` row is a no-op.

*Exit:* the `nauto` ordinary suite passes with the listed cases; no Django import entered the pure
module.

### Step 2 — Seed

Implement §4.1.

*Exit:* the seed YAML lists both content types for `proxmox_presence`; `nauto/tests` still passes.

### Step 3 — nctl read and evidence

Implement §4.3. Tests: a VM row with `proxmox_presence` round-trips into the typed facts; a VM
without it reads `presence=None`; an unrelated custom field is still dropped by the allowlist; the
compute realization summary carries the actual presence; and existing compute drift codes,
severities, classifications, and plans are unchanged.

*Exit:* `nctl` ordinary suite passes; no new drift code and no action exists anywhere in the tree.

### Step 4 — Deploy and prove the transition live

Commit, ask the operator to push nauto, sync the Nautobot Git Repository, bump `NAUTO_COMMIT` in
`devenv/nautobot/Dockerfile`, and run **Seed Home Cluster** with `dry_run=false`,
`update_existing=true`. Verify the Job source actually moved (the synced commit, not just a green
run) before trusting the container.

Then, against the scratch stack:

1. run one ordinary observation + ingest with a **fresh** collection (F3) and confirm every real
   guest is written `present` and the platform state is `complete`;
2. create the disposable synthetic VM row (§4.4);
3. run a second fresh observation + ingest and confirm the synthetic row is the only row flipped to
   `absent`;
4. confirm `nctl drift --json` reads the field and is otherwise identical to Step 0; and
5. delete the synthetic row and re-run drift.

*Exit:* present, absent, and complete-only behavior are shown end to end through the real Job, and
no unrelated drift moved.

### Step 5 — Gates and report

Run and state case counts for: nauto ordinary unittest, nctl ordinary pytest, compute conformance,
and the Nautobot runtime gate covering the nauto real-ORM ingest tests (`--keepdb` is sufficient —
no Django migration is in scope). Write `p2/report.md` with the revision tuple, the decisions above,
F3 named as an accepted transitional limit, the Phase 3 handoff (drift still matches an `absent` VM
as a present realization), gate results, and one precise status.

*Exit:* one status of `complete`, `partially complete`, `implemented, not deployed`, or `blocked`,
with every omitted check visible.

## 6. Exit criteria

1. `proxmox_presence` is attached to `virtualization.virtualmachine` in the deployed scratch
   Nautobot, applied through the ordinary seed Job.
2. Every guest of a validated observation is recorded `present`.
3. A complete observation of one Proxmox scope marks its previously known, omitted, managed guests
   `absent` — and only those.
4. Partial, failed, stale, and different-scope evidence provably write no absence.
5. A reappearing guest returns to `present` through the ordinary upsert path.
6. No VirtualMachine, VMInterface, IP, or Device row is deleted, and an absent guest keeps its other
   fields.
7. nctl's typed VM facts carry presence and the ordinary compute summary shows it.
8. No drift code, classification, action, CLI option, or destroy path was added.

## 7. Boundaries

Prohibitions, minimal:

1. **No Proxmox mutation.** Observation is read-only; Phase 4 owns the first write.
2. **No row deletion.** Absence is a recorded field, never a removal.
3. **No absence from untrustworthy evidence.** Only the single completeness signal of F1 may
   authorize an absence write; do not add a parallel completeness heuristic.
4. **No push.** Local commits are yours; pushing nauto/nctl stays the operator's step.
5. **No Phase 3–4 surface.** No destroy code, handler, action, or `--allow-destroy`, and no change
   to how drift matches a realization.

Everything else is the implementer's call: module layout, function and constant spellings, sweep
placement within the identified gap, error/count reporting shape, test structure, commit
granularity, and step count. Scratch Nautobot writes, Job re-syncs, re-seeds, restarts, test rows,
and the disposable synthetic VM row need no approval. Ask the operator only for the nauto push and
for anything that would write `agfixture`.
