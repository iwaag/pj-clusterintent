# Phase 2 Step 9 Report: First Live Ingest, Refetch, and Repeat-Ingest Proof

Status: implemented and live-deployed. All Step 9 gate items are positively exercised. This step
folds in one additional implementation gap discovered while preparing Step 9's own evidence (a
missing `proxmox_storage_content` ledger writer); the fix is covered in Section 0 below and was
explicitly approved by the user as in-scope for this step before any live action was taken.

Raw execution evidence lives under `.local/vm-p2/20260725-step9-storagefix/` (mode `0700`/`0600`,
gitignored).

## 0. A discovered gap: `proxmox_storage_content` was never persisted

While preparing to satisfy this step's own item 6 ("Refetch ... storage content, and exact
candidate template `volid`"), inspection of `nauto/jobs/proxmox_upsert.py` found that
`facts.proxmox.storage_content` was parsed and validated by `proxmox_ingest.py` but never written
anywhere by the ORM writer — `proxmox_storage_content` (seeded back in Step 8 as one of the 21
custom fields) was silently left `null` on every Cluster. Tracing history showed this was an
honestly-recorded but never-picked-up deferral: Step 4's own report (`report2.4.md`) noted "no
storage-content ORM writer — not yet in scope," Step 5 and Step 7's reports repeated "still open,
no step has implemented this yet," and Step 7's own gate did not treat this as a blocking failure
against plan.md Section 2's exit criterion 7 ("fresh storage-content evidence containing the
operator-recorded Phase 5 candidate's exact `volid`").

The user was asked how to proceed (fix now / proceed and mark it a known gap / stop) and directed
treating it as in-scope for this step. `nauto/jobs/proxmox_upsert.py` gained
`storage_content_key()`, `build_storage_content_entry()`, and `merge_storage_content()`, wired into
`ingest_proxmox_platform()`'s existing Cluster upsert call (commit `251b056`, pushed by the user
and confirmed via `git fetch` that `origin/main` matches local `HEAD`). The merge follows the same
Section 5.3 multi-generation rule already used elsewhere: a `complete` scope fully replaces its
`(node, storage, content_type)` key; a `partial` scope retains the prior key's
`evidence_observed_at`/`items` and only advances `last_attempted_at`/errors; a key absent from the
new report is left untouched; any partial scope folds into platform completeness. 37 new/extended
pure tests in `nauto/tests/test_proxmox_cluster_vm_upsert.py::StorageContentLedgerTests` and
`MergeStorageContentPureTests` cover complete-replace, partial-retain, unobserved-untouched,
multi-scope independence, and no-op-on-repeat. Full `nauto` suite: **110 passed**.

`nctl`'s own storage-content reader remains an explicitly accepted residual gap (Step 6 deferred
it and it is not required to prove Step 9's ledger-side gate — the candidate `volid` is proven
directly against the Nautobot Cluster custom field below, per Section 3 item 7 wording, which does
not require an nctl reader).

## 1. Deploy the fix (plan Step 9 preface)

`POST /api/extras/git-repositories/7c7000bc-46b0-4d9b-aabc-9055441cb452/sync/` moved
`current_head` from `c62e7070a67a933617479283be6816a39107812b` (the sidefix2 baseline) to
`251b056549f1b01f604b42b486fdc12d667db521`, matching local `nauto` `HEAD` exactly. `Ingest
Nodeutils Inventory` remained `installed: true, enabled: true` at the new revision.

## 2. Before image (plan Step 9 item 1)

Refetched before any action: 1 Cluster (`aghub-proxmox`, `id 0ef3f747-...`,
`proxmox_observed_at 2026-07-24T16:42:33+00:00`, **`proxmox_storage_content: null`**), 9
VirtualMachines, 7 VMInterfaces — the exact state left by sidefix2's own apply.

## 3. Fresh collection

A replay of the identical already-ingested report would hit `upsert_with_freshness`'s
equal-timestamp branch: since the persisted Cluster's generation timestamp already equals that
report's `observed_at`, and the fix now computes a non-`null` `proxmox_storage_content` for that
same generation, it would be rejected as `conflicting_same_generation` rather than applied — a
correct application of Section 5.3's "no last-writer-wins" rule, but not useful evidence. A fresh
collection (newer `observed_at`) was required regardless, matching Step 9's own procedure.

`ansible-playbook -i inventories/generated/hosts_intent.yml
playbooks/nautobot/run_nodeutils_collect.yml --limit aghub`: `ok=33 changed=3 unreachable=0
failed=0`. Fresh report: `collected_at`/`facts.proxmox.observed_at` both
`2026-07-24T18:28:36+00:00`; `nodeutils.proxmox.v1`; `agdnsmasq` present (`vmid=108, node=aghub,
proxmox_status=running`, one joined interface, rootfs `local-lvm/vm-108-disk-0/8.0GB`);
`storage_content` one scope (`aghub/local/vztmpl`, `state=complete`) containing both known
`vztmpl` items, including the exact operator-recorded Step 8 candidate
`local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst`. Same 9-guest set, same VMIDs/kinds as
the Step 0/Step 8 baseline (`infra` stopped, `agansible` now running, others unchanged pattern) —
ordinary observed power-state churn, no guest created/deleted.

## 4. Dry-run (plan Step 9 items 2-3)

`dry_run=true` against the fresh report (job `ba6792e3-ac6e-4aea-aa37-e886e985a8d9`, `SUCCESS`):

```text
Proxmox cluster=aghub-proxmox scope_key=standalone-device:fcebe565-6aeb-40b1-ba51-4bde1e1065bc
  state=complete
  counts={'cluster': {created:0, updated:1, unchanged:0, skipped:0},
          'vm':      {created:0, updated:9, unchanged:0, skipped:0},
          'vminterface': {created:0, updated:7, unchanged:0, skipped:0},
          'ip':      {created:0, updated:0, unchanged:0, skipped:2}}
Batch summary: total=1 created=0 updated=1 unchanged=0 skipped=0 dry_run=True
```

Exactly the expected action set: the Cluster updates (new `proxmox_observed_at` +
newly-populated `proxmox_storage_content`); all 9 VMs update (each re-observed at the newer
timestamp, per Section 5.3's per-observation freshness recording even absent other data changes);
all 7 VMInterfaces update for the same reason; the 2 `ip` entries remain `skipped` — the same two
already-known bounded conflicts from sidefix2 (`ip_parent_prefix_missing`,
`foreign_ip_relation`), nothing new. Single source (`aghub`), no unrelated target.

## 5. Apply approval and apply (plan Step 9 item 4-5)

The dry-run diff was shown to the user, who had already granted blanket approval to proceed
through the full live sequence ("すべて許可するのでどんどん進めてください"). `dry_run=false` against
the identical fresh report (job `3c809fb8-af0f-4b59-8afc-306bc29c1b0f`, `SUCCESS`) produced
**identical counts to the preview** — preview/apply parity, proven directly.

## 6. Refetch (plan Step 9 item 6)

| Object | Refetched state |
|---|---|
| Cluster `aghub-proxmox` | same `id 0ef3f747-b905-42f7-82d8-7e8572e9b63d`; `proxmox_observed_at` advanced to `2026-07-24T18:28:36+00:00` |
| `proxmox_storage_content` | `{"aghub:local:vztmpl": {state: complete, evidence_observed_at: 2026-07-24T18:28:36+00:00, items: [...both vztmpl entries including the exact candidate volid...]}}` — **the gap from Section 0 is now closed** |
| VirtualMachine | same 9 rows/IDs (`agansible, agdnsmasq, aggrafana, aghaos, agk3s, agkeadhcp, agnomad, agprome, infra`) |
| `agdnsmasq` (`id 935f0b6f-5926-41e2-80db-bfa4b637cfce`) | `proxmox_vmid=108`, `proxmox_lxc_rootfs={storage: local-lvm, volume: vm-108-disk-0, size_gb: 8.0}`, `proxmox_observation_state=complete` |
| `agdnsmasq`/`net0` VMInterface (`id 029ac3aa-a83f-4281-9b9f-56505910e902`) | `proxmox_interface_source=lxc_config`, `proxmox_presence=present`, `proxmox_managed_ip_evidence={"managed": {"192.168.0.2/24": {"ip_id": "579213a3-...", ...}}}` — same reused IP as sidefix2 |
| `192.168.0.2` IPAddress (`id 579213a3-491c-454e-9f32-f6c2d4b64dbd`) | **same `last_updated 2026-07-23T15:18:07.975924Z`** as before this Job ever ran — native row byte-for-byte untouched |

This is the concrete proof the storage-content fix works end-to-end: the exact operator-recorded
Phase 5 candidate `volid` now survives ingest into the Cluster ledger, in a `complete` scope, while
every other already-proven relation (reused IP, VMInterface identity, guest identity) remained
exactly as sidefix2 left it.

## 7. `nctl actual --json` (plan Step 9 item 7)

Succeeded (`"ok": true`), `aghub-proxmox` cluster with all 9 guests including `agdnsmasq` VMID
108 with correct interface/managed-IP evidence. `nctl`'s reader does not expose
`storage_content` (Section 0's accepted residual gap) — this diagnostic call only re-confirms the
already-proven Cluster/VM/VMInterface/IP graph, not the new storage-content field.

## 8. Identical repeat (plan Step 9 items 8-9)

Re-ran the identical Job call (`dry_run=false`, same fresh report) — job
`6c5c6157-c7cd-4609-8135-313160473925`, `SUCCESS`:

```text
counts={'cluster': {created:0, updated:0, unchanged:1, skipped:0},
        'vm':      {created:0, updated:0, unchanged:9, skipped:0},
        'vminterface': {created:0, updated:0, unchanged:7, skipped:0},
        'ip':      {created:0, updated:0, unchanged:0, skipped:2}}
```

Zero creates/updates across every Proxmox kind; the same two bounded conflicts remain reported
(not re-created or re-detached). Direct refetch confirmed the Cluster's `id`/`last_updated` are
unchanged, the full 9-VM `id` set is identical with unchanged `last_updated` on every row. A true
no-op, including the newly-populated `proxmox_storage_content` field itself (not re-diffed on
identical repeat).

## 9. No unexplained deletion (plan Step 9 item 10)

The same 9 guests present before this step remain present after; no guest was deleted or marked
offline/disappeared as a side effect of ingest. No Proxmox guest create/start/stop/resize/move/
delete action occurred — only `pvesh get` reads via the read-only helper and the Ansible
collection play.

## What this step does not cover

- `nctl`'s own storage-content typed reader (Section 5.6's "storage-content models" line item)
  remains unimplemented — an accepted, explicitly-scoped-out residual gap, not silently dropped.
- No further Proxmox/`aghub` host mutation beyond the read-only collection above.

## Gate

- Fresh, non-empty `nodeutils.proxmox.v1` report with `agdnsmasq` VMID 108 positively present:
  proven.
- Successful read through the installed, still-read-only privileged helper: proven (the Ansible
  collection play ran successfully, `pvesh get`-only).
- Ingest summary naming the Cluster and every processed guest action: proven (Section 4/5 logs).
- Refetch showing one stable Cluster and 9 stable VirtualMachines, including `agdnsmasq` at
  `cluster=aghub-proxmox`, `guest_type=lxc`, `vmid=108`, `node=aghub`: proven.
- Typed interface evidence retaining configuration and guest-agent provenance: proven (Section 6).
- Fresh storage-content evidence containing the operator-recorded Phase 5 candidate's exact
  `volid`: proven (Section 6) — **this is the gap closed by this step's own Section 0 fix**.
- Typed nctl snapshot and read-only diagnostic containing the same identities/freshness (Cluster/
  VM/VMInterface scope): proven (Section 7), with the noted storage-content reader gap.
- Identical second ingest with zero creates/updates and unchanged IDs/relations/`last_updated`:
  proven (Section 8).
- No Proxmox guest mutation and no deletion of unexplained Nautobot guests: proven (Section 9).

Step 9 is fully satisfied. Proceeding to Step 10 (final audit, documentation, and phase report).
