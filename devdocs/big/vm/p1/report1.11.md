# Step 11 — Coordinated rollout and rollback point

Status: complete.

The rollout/rollback sequence itself is already fully specified in `plan.md` §Step 11 (Phase 2 and
Phase 3 rollout, rollback points, post-write recovery rules). This step confirms that sequence
against this Phase's live findings and records where the live environment simplifies or
constrains it; it does not alter the plan's rollout text.

## Phase 2 rollout — grounding in live evidence

- Step 11.1 ("implement the nested Proxmox schema, normalizer, helper allowlist extension"):
  grounded directly in report 1.5's field-by-field contract and report 1.2 §5's live proof of the
  guest-agent interface-replacement defect (VMID 102).
- Step 11.6 ("deploy the pinned nodeutils/helper revision and collect fresh evidence"): the
  current pin (`36e1c5752ba895780eea21b8e994926b93cc1c53`) and helper digest
  (`b332447784b68e1e2beb55e83c81b5edecf062599b7aa55d9012be61786b9295`) are the exact rollback
  reference point recorded in reports 1.0/1.2 — Phase 2 diffs against these, not a guess.
- Step 11.3/11.4 (savepoint/partial-collection rules): directly motivated by the live 9-guest,
  1-node, 1-cluster inventory (report 1.2 §3) — a `partial` collection marker matters even in this
  small environment, since a transient failure on any one of the 9 guests must not affect the
  other 8 or mark them offline.
- Step 11.7-11.9 (dry-run/before-image/apply/refetch): the "before image" for the first live
  ingest is the live baseline from report 1.3 — **zero** Cluster, VirtualMachine, VMInterface rows,
  zero `proxmox_*` custom fields, zero `ClusterType` rows. The first live ingest is therefore a
  pure-create operation with no existing rows to conflict with; the rollback point (§11, "normal
  rollback point is immediately before the first live ingest") is unusually simple here — rollback
  is "delete the created rows," not "restore a prior version of existing rows."

## Phase 3 rollout — grounding in live evidence

- Step 11.P3.2 ("smoke-test that the current nctl query still works"): the exact smoke-test
  baseline is report 1.0's `nctl drift --json` result (6/6 `converged`) — the additive migration
  must reproduce this identically before proceeding.
- Step 11.P3.5 ("seed only the confirmed `aghub-pve` and `agdnsmasq` records... after dry import
  and exact diff review"): the exact values to seed are frozen in report 1.4 (platform
  `cluster_name=aghub-proxmox`, instance `vcpus=1, memory_mb=512, root_disk_gb=8,
  vmid=108, template=<unverified>, unprivileged=true`).
- Step 11.P3.6 ("for a non-null legacy link, require the new instance row..."): report 1.3 §5
  found **zero non-null `realized_vm` rows** across all 5 live DesiredNodes — this step's migration
  logic has nothing to migrate today, simplifying (not skipping) the Phase 3 rollout; Steps
  P3.1/P3.2/P3.7/P3.8/P3.9 remain mandatory regardless, per plan §5.5's explicit instruction.

## Rollback point summary (confirmed, not altered)

- Phase 2: immediately before the first live ingest; recovery for transaction failure, missing-
  field rows, wrong-identity/membership rows, and erroneous updates all follow the before-image
  rules already in plan.md verbatim.
- Phase 3: immediately before the first desired-compute-record write; add/remove releases stay
  un-collapsed (bounded compatibility window), matching plan.md verbatim.
- Manual-access/SSH-enrollment rollback (new in this phase's revision, report 1.8): the
  `waiting_for_manual_initial_access`/`waiting_for_ssh_enrollment` safe-stops are themselves the
  rollback point for guest bootstrap — a guest stuck at either state can be safely abandoned
  (compute-only) or resumed later without any destructive action, since neither state writes SSH
  trust or desired links.

## Gate evaluation

The plan's already-frozen Phase 2/Phase 3 rollout and rollback sequence is confirmed consistent
with every live fact gathered in Steps 0-10 of this phase; no contradiction was found, and several
steps (Phase 2's zero-existing-rows starting point, Phase 3's zero-legacy-rows starting point) are
simpler in practice than the general case the plan text covers. Step 11 gate passed.

## Discrepancies

None.
