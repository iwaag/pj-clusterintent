# Phase 2 Step 9 Blocker Fix Plan: Transaction-Rolled-Back Proxmox Preview

Status: planned, revised after review. No code or live-state change is authorized by this
document.

This plan resolves the blocker recorded in [`problem.md`](problem.md) and restores the Phase 2
contract in [`plan.md`](plan.md): the first live virtualization-ledger apply must be preceded by an
exact preview and a separate approval.

The review decision is to retain the operator-facing `dry_run` option but define it as a
**transaction-rolled-back preview**, not as a second, pure read-only implementation:

```text
dry_run=true
  -> run the normal persistence path inside one Job-owned transaction
  -> collect the same validation, matching, counts, conflicts, and evidence as apply
  -> mark the owning transaction rollback-only
  -> commit no target rows or relations
  -> persist only the intended Job log/summary artifact
```

This matches `plan.md` Section 5.5, which already states that dry run exercises the same
matching/diff/validation path inside a rollback-only transaction. It avoids maintaining an
in-memory imitation of Django/Nautobot persistence and removes the unsaved-parent complexity found
in the first version of this fix plan.

Source revisions at plan-writing time:

| Repository | Revision |
|---|---|
| superproject | `6801f0a2012b5064335c398457d8f5ffbb93a91b` |
| `nauto` | `4cea3b68b1bc766aedf75d8ea166b0e68d735bc2` |
| `nctl` | `d7b0e21c1bc9f459ecc0e3ce9bbe4c72ade99de3` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |

`problem.md` is untracked at this baseline. Preserve it unchanged as the original defect record.

## 1. Why the Preview Is Retained

The preview remains useful for the Phase 2 rollout because the first ingest can create and relate
many Cluster, VM, VMInterface, and IPAddress objects. It gives the operator one exact target/count
review before the persistent write.

Its scope is deliberately limited:

- It protects the first Nautobot actual-ledger rollout and remains useful for troubleshooting.
- It does not imply that routine observation ingest must always require human approval after the
  path is proven.
- It is not the design for future Proxmox create/start operations. External actuation cannot be
  undone by a database rollback and must retain a separate, non-actuating nctl dry plan.
- It guarantees **no committed target-model change**, not “no SQL statement was issued.”

The implementation must therefore optimize for one execution path with a reliable transaction
boundary, rather than preserving two subtly different planners.

## 2. Required State Transition

The repaired Step 9 path starts with an existing observer Device and no Proxmox actual-ledger rows:

```text
existing Device aghub
  + fresh nodeutils.proxmox.v1 report
  + no matching Cluster/VM/VMInterface/IP relations
  + dry_run=true
  -> validate the report
  -> temporarily create/update the exact target graph
  -> return a non-empty result["proxmox"] summary
  -> roll back the owning transaction
  -> refetch equal to the before image

same report
  + dry_run=false after separate approval
  -> run the same persistence core
  -> produce the same actions and stable target identities
  -> commit the graph
  -> refetch the exact result

identical repeat apply
  -> zero creates/updates
  -> unchanged IDs, relations, allowlisted values, and last_updated
```

Preview and apply parity is compared using stable target identities:

- Cluster identity source and scope key;
- guest kind and VMID within the Cluster;
- VMInterface config slot and MAC;
- IP address and prefix; and
- action kind and changed allowlisted fields.

Database IDs allocated to rows created inside the preview transaction are temporary and must not be
presented as apply-stable identifiers.

## 3. Scope and Non-goals

### 3.1 In scope

- `nauto/jobs/ingest_nodeutils_inventory.py`
  - transaction ownership in `run()`;
  - removal of the dry-run early return in `ingest_report()`;
  - one normal Device/Proxmox persistence path for existing observer Devices;
  - suppression of temporary created-object IDs in preview output.
- `nauto/jobs/proxmox_upsert.py`
  - removal or internalization of lower-level `dry_run` save suppression;
  - use of the same Cluster/VM persistence behavior in preview and apply.
- `nauto/jobs/proxmox_interfaces.py`
  - use of the same VMInterface/IP create/attach/detach behavior in preview and apply.
- nauto automated tests for transaction rollback, preview/apply parity, identical repeat, and
  failure rollback.
- an audit of Nautobot/Django persistence hooks for transaction-external side effects.
- one real Nautobot ORM preview/apply/repeat verification before resuming Step 9.
- deployment of the reviewed nauto revision and the existing Step 9 approval gate.

### 3.2 Non-goals

This fix does not:

- build a second pure planner for Nautobot ORM writes;
- require zero `INSERT`, `UPDATE`, `DELETE`, save, attach, or detach calls during preview;
- add special matching behavior for unsaved Cluster/VM/VMInterface objects;
- change `nodeutils.proxmox.v1`, the fresh Step 8 report, or the privileged helper;
- change Proxmox itself;
- change nintent desired state or Phase 3+ compute models;
- change nctl drift or external-actuation safety;
- invent stable IDs for rolled-back objects;
- weaken freshness, conflict, completeness, relation-ownership, or per-guest savepoint rules;
- authorize routine auto-approval of ingest; or
- perform the Step 9 persistent apply without its existing separate approval.

## 4. Revised Root-Cause Assessment

### 4.1 The Job-level early return is the actual Step 9 blocker

`ingest_report()` returns at `dry_run=true` before it reads `facts.proxmox`. Consequently the outer
transaction has nothing Proxmox-related to roll back or summarize.

The fix must remove that return and allow an existing observer Device to reach
`ingest_proxmox()` in both modes.

### 4.2 The current implementation mixes two incompatible dry-run models

Most Cluster/VM/VMInterface `save_fn()` calls are suppressed by lower-level `if not dry_run`
branches, while IP create/attach/detach callbacks run normally. The outer Job transaction then
rolls the whole preview back.

This hybrid has three problems:

1. it hides Proxmox entirely because of the Job-level early return;
2. if that return alone is removed, planned Cluster and VM objects remain unsaved and dependent
   real-ORM queries cannot reliably traverse them; and
3. preview and apply execute different persistence paths, making parity harder to prove.

The IP callbacks are not, by themselves, evidence that target rows survive the Job dry run: the
outer transaction is already marked rollback-only. They are evidence that the implementation is
half transaction-backed and half simulated. The repair is to make transaction ownership explicit
and use it consistently.

### 4.3 Transaction rollback is sufficient only after side-effect audit

Database rows, through-model relations, and Nautobot change-log rows created in the same
transaction are expected to roll back together. The following do not automatically share that
guarantee and must be audited:

- Django/Nautobot `pre_save`, `post_save`, `m2m_changed`, and delete signals;
- Job Hooks, Event Rules, webhooks, or plugins triggered synchronously by these model changes;
- direct network/file/message calls from persistence callbacks;
- `transaction.on_commit()` handlers, which must not run after rollback;
- database-generated identifiers or sequences whose allocation is not transactional; and
- Job logs and `nodeutils-ingest-summary.json`, which intentionally survive as preview evidence.

If any target-model persistence hook performs an irreversible external action before commit, stop
and either disable that hook for the preview transaction through a supported mechanism or return
to a pure planning design for the affected operation. Do not assume rollback covers an external
side effect.

### 4.4 New observer Devices remain a separate precondition

The current Step 9 observer Device `aghub` already exists. That is the supported positive path.

For a report whose observer Device would itself be created, standalone Proxmox identity depends on
that Device's UUID. A UUID allocated inside a rolled-back preview may differ from the later apply
UUID, so its derived scope key is not apply-stable.

In this case:

- preview the Device create;
- include a bounded Proxmox precondition such as `observer_device_not_persisted`;
- do not claim an exact Proxmox Cluster scope preview;
- apply/refetch the Device separately after approval; and
- run a second Proxmox preview using the now-stable Device UUID.

Do not expose a rolled-back Device UUID as a stable provider scope.

## 5. Implementation Design

### 5.1 Make the Job the sole preview transaction owner

Keep the existing top-level `transaction.atomic()` in `IngestNodeutilsInventory.run()` and make its
contract explicit:

1. Load and validate every report as today.
2. Execute the normal Device and Proxmox persistence core.
3. Build the summary while the temporary rows and relations are visible within the transaction.
4. When `dry_run=true`, sanitize temporary IDs from the public summary.
5. Mark the transaction rollback-only before leaving the atomic block.
6. After rollback completes, create the intended Job summary artifact.

Any exception escaping the batch also rolls back the transaction normally. Existing per-guest
savepoints remain nested within this owner.

Do not allow a lower-level caller to create a “preview” merely by passing a Boolean without the
owning rollback boundary. Prefer one of these shapes:

- remove lower-level `dry_run` arguments from the persistence core entirely; or
- rename them to an internal execution policy that cannot suppress writes independently of the
  transaction owner.

The preferred implementation is to remove save-suppression branching from the lower layers. The
only public mode switch remains the Job's `dry_run`, whose meaning is commit versus rollback.

Update the Job variable description from “without writing to Nautobot” to “without committing
target changes to Nautobot” so the operational contract is accurate.

### 5.2 Remove the early return and use one Device/Proxmox path

For an existing observer Device:

1. Compute the Device diff.
2. Run Device update/no-op through the normal persistence path.
3. Read `facts.proxmox`.
4. Run `ingest_proxmox()` once when the subtree is a mapping.
5. Return the combined Device and Proxmox result.

This ordering is identical in preview and apply. In preview, the outer transaction rolls back the
Device and virtualization changes together.

For a new observer Device with Proxmox facts, use the explicit two-stage precondition in Section
4.4 rather than generating a provisional Proxmox scope.

Device-only reports remain compatible and do not gain a `proxmox` section.

### 5.3 Run Cluster/VM/VMInterface/IP persistence normally

Inside the Job-owned transaction:

- `upsert_with_freshness()` calls `save_fn()` for creates/updates in both preview and apply;
- `ingest_proxmox_platform()` persists the temporary Cluster before guest matching;
- each temporary VM is persisted before VMInterface matching;
- `sync_guest_interfaces()` persists interface changes;
- `sync_interface_ips()` uses its current create/attach/detach behavior;
- authoritative empty-IP and interface-disappearance paths perform their normal detach behavior;
  and
- per-guest failures still roll back to their nested savepoint and make the platform partial.

This deliberately eliminates the need for:

- a `dry_run` parameter on `sync_interface_ips()`;
- placeholder IPAddress objects;
- Python-side matching around unsaved related objects; and
- separate would-create/would-attach/would-detach algorithms.

The persistence core must be independently describable as “apply these facts.” It must not claim
to be safe preview code when called outside the Job-owned transaction.

### 5.4 Sanitize rolled-back identifiers

Created rows receive real model IDs inside the preview transaction, but those IDs cease to identify
objects after rollback and may differ on apply.

Before emitting the dry-run summary:

- set IDs for preview-created Cluster/VM/VMInterface/IP objects to `null` or omit them according to
  the existing optional schema;
- retain IDs only for objects that existed in the before image;
- never serialize Python `None` as the string `"None"`;
- retain stable provider identities, config slots, address/prefix keys, action counts, and changed
  field names; and
- optionally mark an ID as provisional only if the existing summary schema can do so without
  ambiguity; omission/null is preferred.

The current summary exposes `cluster_id`; audit all nested/changed evidence for other IDs rather
than assuming it is the only one. The nctl managed-IP schema already accepts `ip_id: str | None`,
so no nctl change is expected.

### 5.5 Preserve summary and count semantics

The existing `nodeutils.ingest.summary.v1` envelope remains compatible. Preview and apply from the
same before image must agree on:

| Kind | Compared action |
|---|---|
| Cluster/VM/VMInterface `created` | row creation |
| Cluster/VM/VMInterface `updated` | allowlisted row update |
| Cluster/VM/VMInterface `unchanged` | no row update |
| IP `created` | IPAddress creation and intended relation |
| IP `updated` | existing IPAddress relation adoption |
| IP `skipped` | current detach/conflict count contract |

The `IP.skipped` name is imperfect but changing public count vocabulary is outside this blocker
fix. Lower-level outcome/error evidence continues to distinguish detach from conflict.

The Job summary artifact and logs are expected durable outputs of a preview. They must contain
bounded public identifiers and counts only, not raw reports or credentials.

## 6. Automated Verification

### 6.1 Fast orchestration tests

Add focused coverage for the mode boundary:

1. Existing Device with Proxmox facts in preview:
   - the Device persistence path is reached;
   - `ingest_proxmox()` is called exactly once;
   - `result["proxmox"]` is present.
2. Existing Device in apply:
   - the same core calls occur in the same order.
3. Device-only input:
   - existing behavior and summary compatibility remain unchanged.
4. New Device with Proxmox facts in preview:
   - Device creation is named;
   - the Proxmox stable-scope precondition is visible;
   - no rolled-back observer UUID is claimed as stable.
5. An exception before normal completion:
   - the outer atomic block exits without committing target changes.

If importing the Job requires Nautobot/Django, run these in the Nautobot environment or isolate
only the orchestration decision into a small helper. A test that calls
`ingest_proxmox_platform()` directly does not cover the original early-return defect.

### 6.2 Persistence-core tests

Existing fake-ORM tests continue to test the apply core:

- Cluster/VM create, update, no-op, stale evidence, and conflicts;
- VMInterface create/update/disappearance;
- IP create, adoption, replacement, authoritative empty, detach, and foreign conflicts;
- partial evidence retention; and
- per-guest failure isolation.

Remove or rewrite fake-ORM tests that expect `dry_run=true` to leave fake stores empty. A list-based
fake store has no real transaction semantics and must not be treated as proof of rollback.

Instead, assert that the persistence core produces the exact graph and counts once. Preview safety
is tested at the Job-owned real transaction boundary.

### 6.3 Real ORM preview/apply/repeat test

Use the local Nautobot environment described in `.local/localenv_memo.md`. Load the candidate
nauto code through the scratch-module technique used in `report2.7.md`, without replacing the
deployed Job registration.

Prepare a rollback-capable test using:

- an existing observer Device;
- no matching Proxmox Cluster/VM/VMInterface rows;
- one LXC with one static IP inside an existing Prefix; and
- captured before images for Cluster, VM, VMInterface, IPAddress, assignment, and applicable
  change-log rows.

Run three rounds:

#### Round A — Preview

Call the actual Job transaction owner with `dry_run=true` and assert:

- the expected Cluster/VM/VMInterface/IP persistence functions execute;
- the full non-empty Proxmox summary is produced;
- temporary parents have usable IDs inside the transaction;
- no unsaved-parent ORM exception occurs;
- the transaction is rollback-only before exit;
- after exit, every captured target set/relation/value equals the before image; and
- preview-created IDs are absent/null in the public summary.

#### Round B — Rollback-contained apply proof

From the same before image, call `dry_run=false` inside a separate test-owned outer transaction:

- compare stable targets, counts, changed fields, and conflicts with Round A;
- refetch the exact graph while still inside the test transaction; and
- roll the test-owned outer transaction back unconditionally.

#### Round C — Identical repeat

Within one test-owned transaction:

1. apply once;
2. capture IDs, relations, values, and `last_updated`;
3. apply the identical report again;
4. assert zero creates/updates and unchanged timestamps; and
5. roll the test-owned transaction back.

This proves the real ORM and model constraints without performing the Step 9 persistent apply.

### 6.4 Side-effect audit

Before accepting rollback as the safety mechanism:

1. Inspect configured signals, Job Hooks, Event Rules, webhooks, and relevant plugins for Cluster,
   VirtualMachine, VMInterface, IPAddress, and their through model.
2. Classify each effect:
   - same-transaction database write;
   - `transaction.on_commit()` effect;
   - synchronous external/non-transactional effect; or
   - no applicable handler.
3. Prove `on_commit()` handlers do not run after the preview rollback.
4. If synchronous external effects exist, stop and revise the design before live preview.
5. Record whether any non-transactional identifier sequence advances. Treat harmless unused-number
   gaps as metadata, not target-state mutation, but document them rather than claiming they do not
   exist.
6. Confirm the intended surviving effects are limited to Job logs and the sanitized summary
   artifact.

### 6.5 Repository commands

Run from the documented working directories:

```bash
cd nauto
python3 -m unittest \
  tests.test_proxmox_cluster_vm_upsert \
  tests.test_proxmox_interface_ip_upsert \
  tests.test_nodeutils_ingest_summary
python3 -m unittest discover -s tests
python3 -m py_compile jobs/*.py
```

Record the exact Nautobot-container command used for Job/transaction tests. Do not substitute
fake-store emptiness for the real rollback proof.

Because the expected implementation is nauto-only, other repository suites are required only if
their files or contracts change. If nctl fixtures or parsing change, run at least:

```bash
uv run --project nctl pytest \
  nctl/tests/test_sources_actual.py \
  nctl/tests/test_actual_render.py
```

Finish with `git diff --check`, review the nauto diff, and confirm unrelated worktrees were not
modified.

## 7. Implementation Sequence and Gates

### Step 0 — Freeze the contract and reproduce the failure

1. Record current revisions and worktree state.
2. Run the existing nauto tests.
3. Add a failing Job-level test proving the Proxmox section is omitted in preview.
4. Record the current hybrid save-suppression/IP-mutation behavior.
5. Audit all lower-level `dry_run` branches and all persistence callbacks reached by Proxmox
   ingest.

Gate: the early-return defect and every divergent preview/apply branch are enumerated; no live
state changes.

### Step 1 — Centralize preview ownership

Make `run()` the sole commit/rollback decision owner, update the Job variable description, and
remove lower-level save-suppression semantics.

Gate: lower-level Proxmox ingest has one apply behavior, and `dry_run=true` can only be safe through
the Job-owned rollback boundary.

### Step 2 — Repair Job orchestration

Remove the early return, run Device and Proxmox handling in the normal order for existing
observers, and implement the new-observer two-stage precondition.

Gate: the existing `aghub` preview reaches the complete Proxmox path exactly once; Device-only
behavior remains compatible.

### Step 3 — Sanitize preview evidence

Remove rolled-back created-object IDs from the public summary while retaining stable provider
identities, counts, changed fields, and errors.

Gate: no temporary ID is presented as apply-stable, and preview remains reviewable without raw
evidence.

### Step 4 — Prove real transaction safety

Complete the side-effect audit and run the real ORM Round A preview.

Gate:

- all intended persistence paths run;
- no transaction-external irreversible effect is registered;
- target rows, relations, values, and change logs equal the before image after rollback; and
- the summary is non-empty and sanitized.

### Step 5 — Prove preview/apply/repeat parity

Run real ORM Rounds B and C plus the full nauto suite.

Gate: preview and apply stable targets/counts agree, apply produces the exact graph, identical
repeat is a no-op, and the test-owned transaction leaves no persistent fixture.

### Step 6 — Review, commit, and deploy nauto

1. Review the exact nauto diff and transaction evidence.
2. Commit the nauto change in one reviewable blocker-fix commit.
3. Ask the user to push the commit; do not push on their behalf.
4. Sync the Nautobot Git Repository after the revision is available remotely.
5. Confirm the installed `Ingest Nodeutils Inventory` revision equals the tested local revision.

Gate: the deployed Job is the exact reviewed revision. No persistent virtualization ingest has yet
run.

### Step 7 — Resume Phase 2 Step 9

1. Reconfirm the exact fresh Step 8 report.
2. Save a new sanitized before image.
3. Run the deployed Job with `dry_run=true`.
4. Assert the exact Cluster, every guest, VMInterface, and IP action; positively confirm
   `agdnsmasq` LXC VMID 108 and its `net0`/`192.168.0.2/24` evidence.
5. Refetch target rows/relations and prove equality with the before image.
6. Review the sanitized preview and stop for the existing separate apply approval.

Only after approval:

7. Apply the identical report once.
8. Refetch and run `nctl actual --json`.
9. Repeat the identical ingest and prove no creates/updates and unchanged timestamps.
10. Continue with `report2.9.md`; Phase 2 remains incomplete until Step 10 also passes.

Gate: an omitted Proxmox section, empty first action set, rollback leak, preview/apply stable-target
or count mismatch, or non-empty identical repeat fails the step.

## 8. Rollback and Failure Handling

- A unit, side-effect-audit, or real-ORM failure stops before deployment.
- A synchronous irreversible persistence hook blocks transaction-backed preview; do not proceed
  until the hook is safely addressed or the affected operation receives a pure planner.
- A deployed preview with unexpected output stops before apply.
- If refetch differs from the preview before image, preserve before/after evidence and write an
  exact repair plan. Do not apply again or delete rows automatically.
- If the first approved apply fails, preserve transaction/per-guest evidence and refetch the actual
  ledger before planning any repair.
- Job log and summary-artifact creation are intentional preview outputs, not rollback leaks.
- No Nautobot rollback or repair authorizes a Proxmox guest mutation.
- Reports contain bounded IDs, counts, digests, and error codes only; do not commit tokens, raw
  provider bodies, or unrestricted inventory JSON.

## 9. Definition of Done

This blocker fix is complete only when all applicable items are proven:

- [ ] `dry_run` is documented and implemented as normal persistence followed by owner-controlled
      transaction rollback.
- [ ] Lower persistence layers no longer implement a competing partial no-save mode.
- [ ] `ingest_report()` reaches Proxmox handling for an existing observer during preview.
- [ ] The current empty-ledger `aghub` case produces non-empty Cluster/VM/VMInterface/IP actions.
- [ ] Temporary parent rows permit the real ORM path to execute without unsaved-parent failures.
- [ ] Preview-created database IDs are absent/null in public evidence.
- [ ] A new observer Device yields a truthful two-stage precondition rather than an unstable scope
      key.
- [ ] The side-effect audit finds no unhandled irreversible action before commit.
- [ ] `transaction.on_commit()` actions do not run after preview rollback.
- [ ] After real ORM preview, all target rows, relations, values, and change logs equal the before
      image.
- [ ] Preview and apply stable targets, counts, changed fields, and conflicts agree.
- [ ] Apply creates/updates only the exact intended Nautobot ledger graph.
- [ ] Identical repeat apply is a no-op with unchanged `last_updated`.
- [ ] Full nauto tests, syntax checks, and `git diff --check` pass.
- [ ] The deployed Job revision equals the reviewed/tested nauto commit.
- [ ] The resumed live Step 9 preview leaves the persistent before image unchanged.
- [ ] Separate user approval is obtained before the first persistent virtualization ingest.
- [ ] No Proxmox resource, desired-state row, unrelated Nautobot row, generated inventory, or SSH
      trust entry changes as part of this blocker fix.

Until the live Step 9 preview satisfies these criteria, `problem.md` remains `Status: open,
blocking Step 9`. Passing local tests alone supports at most `implemented, not deployed`; it does
not clear the blocker.
