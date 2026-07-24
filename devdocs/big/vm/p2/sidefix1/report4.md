# Phase 2 Sidefix1 Step 4 Report: Prove Real Transaction Safety

Status: implemented and environment-backed (Round A only). Not deployed to the tracked `nauto` Git
Repository and no live `aghub`/Proxmox action was taken. No persisted Nautobot state changed —
proven directly by this step's own before/after snapshot.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 4 ("Prove real transaction
safety"). This is the first sidefix1 step to touch the local Nautobot environment (per
`.local/localenv_memo.md`); the user confirmed running against it before this step proceeded.
Raw evidence lives in `.local/vm-p2/sidefix1-step4/` (mode `0700`/`0600`, gitignored).

## 1. Side-effect audit (fixplan Section 6.4)

Inspected the running `nautobot-nautobot-1` container directly (`nautobot-server shell`) for every
registered signal handler, Job Hook, Event Rule (not a model in this Nautobot version — see
below), and Webhook on `Cluster`, `VirtualMachine`, `VMInterface`, `IPAddress`, and their through
model `IPAddressToInterface`:

| Effect | Classification | Detail |
|---|---|---|
| `pre_save`/`post_save`/`pre_delete`/`post_delete` on all five models | same-transaction database write | Nautobot's own built-in `ObjectChange` (change-log) signal handlers (`_handle_changed_object_pre_save`, `_handle_changed_object`, `_handle_deleted_object`) — ordinary `ObjectChange.objects.create()` calls inside the same DB connection/transaction. |
| `IPAddressToInterface.pre_save` → `ip_address_to_interface_assignment_created` | same-transaction validation | Calls `instance.full_clean()` only; no external effect. |
| `IPAddressToInterface.pre_delete` → `ip_address_to_interface_pre_delete` | same-transaction database write | Nulls `host.primary_ip4`/`primary_ip6` and calls `host.save()` when the deleted assignment was the primary IP; ordinary same-transaction ORM write. |
| Webhooks | no applicable handler | Zero `Webhook` rows exist in this environment. |
| Job Hooks | no applicable handler for our models | One enabled `JobHook` ("AI Resource Auto Review") exists, but its `content_types` is `['device']` only — it is never triggered by a Cluster/VirtualMachine/VMInterface/IPAddress save. |
| Event Rules | not applicable | This Nautobot version (3.1.3) has no `EventRule` model (`ImportError` confirmed); the plan's generic "Event Rules" category has no concrete implementation to audit here. |
| `nautobot_intent_catalog` (the only installed third-party plugin, i.e. nintent) | no applicable handler | `grep` for `receiver`/`post_save`/`pre_save`/`signals` across its installed package found zero matches — it registers no signal on any model. |
| `transaction.on_commit()` sites in Nautobot core | not reachable from this path | The only three call sites found (`extras/customfields.py` custom-field bulk-provisioning jobs, `extras/models/jobs.py` Celery job dispatch, `extras/utils.py` Kubernetes job pod creation) all fire only when a *Job* itself is being enqueued/dispatched — never as a side effect of saving a Cluster/VirtualMachine/VMInterface/IPAddress row. Since no JobHook/JobButton targets these models (previous row), none of these `on_commit()` sites are reachable from Proxmox ingest at all, so none can run after this Job's own rollback. |
| Non-transactional identifier sequences | not applicable | `Cluster._meta.pk` (and the other three models) is `UUIDField` — Nautobot generates primary keys client-side (`uuid.uuid4()`), not from a database sequence, so a rolled-back row leaves no advancing/gapped counter to document. |

Conclusion: no synchronous external/non-transactional effect exists on the path this Job's Proxmox
ingest can reach. Every registered handler is a same-transaction database write or validation call
that necessarily rolls back with the surrounding transaction. Rollback is sufficient as the preview
safety mechanism for this environment's actual configuration, satisfying the plan's precondition
for treating preview safety as transaction-backed (Section 4.3).

## 2. Real ORM Round A preview (fixplan Section 6.3, Round A)

### Method

Followed `report2.7.md`'s established technique: copied the current `nauto` worktree (sidefix1
Steps 0-3, commit `1d2052c`) into the running container at `/tmp/nauto_review` with a neutralized
`jobs/__init__.py` (no `register_jobs()` call — no Job database record created or altered), then
ran the real `IngestNodeutilsInventory` class directly from `nautobot-server shell` as a plain
Python object (`self.create_file` monkeypatched to capture the summary content in memory instead of
writing a `FileProxy` row, since no `JobResult` exists for a manually-instantiated Job). The whole
call was additionally wrapped in a manual `transaction.savepoint()`/`transaction.savepoint_rollback()`
pair as defense-in-depth beyond `run()`'s own internal `transaction.set_rollback(True)`.

### Fixture

A `nodeutils.inventory.v2` report for the **real, already-existing** `aghub` Device (Device UUID
`fcebe565-6aeb-40b1-ba51-4bde1e1065bc`, confirmed via a direct query — matches the plan's Section
2 required starting state: existing observer Device, no matching Proxmox Cluster/VM/VMInterface/IP
relations, confirmed by the same query showing zero Cluster/VM/VMInterface rows beforehand), with
one LXC guest (`agdnsmasq`, vmid 108 — the plan's own named positive case) and one static IP
`192.168.0.99/24` inside the real, already-seeded `192.168.0.0/24` Prefix (an address not already
in use by any of the five pre-existing IPAddress rows in that Prefix, confirmed by listing them
first).

### Before/after state (the step's actual gate)

| Snapshot | Cluster | VM | VMInterface | `192.168.0.99` IPAddress | `aghub` `proxmox_*` custom fields | `aghub` `last_updated` |
|---|---|---|---|---|---|---|
| Before | 0 | 0 | 0 | 0 | `{}` | `2026-07-23 13:18:25.704378+00:00` |
| Immediately after `run()` returns (dry_run=True) | 0 | 0 | 0 | 0 | `{}` | unchanged |
| After the additional outer savepoint rollback | 0 | 0 | 0 | 0 | `{}` | unchanged |

Identical at all three points — proven by an in-script `assert before == after`. A follow-up
`ObjectChange` query for `object_repr__icontains="aghub-proxmox"` returned `0` rows post-rollback
(the change-log entries these writes would have produced also rolled back).

### Produced summary (from the captured `nodeutils-ingest-summary.json`)

The Proxmox section was non-empty and fully populated, proving the fix reaches and completes the
whole persistence path in preview:

- `cluster_name: "aghub-proxmox"`, `identity_source: "standalone_node_fallback"`,
  `scope_key: "standalone-device:fcebe565-6aeb-40b1-ba51-4bde1e1065bc"` — derived from the real
  Device UUID, exactly as Section 2 requires;
- `object_counts`: `cluster.created=1`, `vm.created=1`, `vminterface.created=1`, `ip.created=1`,
  all other actions `0`;
- `observation_state: "complete"`, `guest_errors: []`;
- **`cluster_id: null`** — the Step 3 sanitization fired correctly: the Cluster row got a real,
  usable in-transaction `pk` (proven by the create succeeding — a `VirtualMachine.cluster` foreign
  key to an unsaved parent would have raised a Django `ValueError`, and it did not), but that
  temporary id was withheld from the public summary because this call's own match found no
  pre-existing Cluster;
- `changed_fields["cluster"]` and `changed_fields["vm:lxc:108"]` list only field names, no ids,
  matching the Step 3 audit's conclusion that `cluster_id` is the only id ever exposed.

## 3. What this step does not cover

- Round B (rollback-contained apply proof) and Round C (identical repeat) — fixplan Step 5's
  scope, not this step's.
- No deployment to the tracked `nauto` Git Repository, no push, no live Job execution through
  Nautobot's Job-run UI/API, and no touch of the real `aghub` Proxmox host — unchanged from
  `report2.7.md`'s equivalent boundary.
- The fixture is synthetic (matching the plan's own named `agdnsmasq`/vmid 108 case and reusing the
  real `aghub` Device), not the actual Step 8 fresh collection — reconfirming against the real
  fresh report is fixplan Step 7's job, not this step's.

## Gate

- All intended persistence paths run: proven (Cluster, VM, VMInterface, IP all created in one
  pass).
- No transaction-external irreversible effect is registered: proven by the Section 1 audit.
- Target rows, relations, values, and change logs equal the before image after rollback: proven by
  the Section 2 before/after table and the `ObjectChange` check.
- The summary is non-empty and sanitized: proven (Section 2 summary excerpt; `cluster_id: null`
  while all other stable identity/count/changed-field evidence is present).

Step 4 is satisfied. Proceeding to Step 5 (prove preview/apply/repeat parity: real ORM Rounds B and
C, plus the full nauto suite) remains gated behind this step's own review — it also touches the
local Nautobot environment.
