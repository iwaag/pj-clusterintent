# Phase 2 Step 9 Blocker Fix Plan (sidefix2): Namespace-Aware IP Reuse and Truthful Guest Results

Status: planned. No code change, deployment, persistent Nautobot ingest, Proxmox mutation, or
desired-state mutation is authorized by this document.

This plan resolves the two real-Nautobot-ORM defects and the result-accounting gap recorded in
[`problem.md`](problem.md). It restores the live-preview gate in
[`../sidefix1/problem_fixplan.md`](../sidefix1/problem_fixplan.md) Step 7 and the Phase 2 first
ingest contract in [`../plan.md`](../plan.md) Step 9.

The central correction is that a Nautobot `IPAddress` and an observed interface address do not
have the same identity key:

```text
Nautobot IPAddress identity/uniqueness
  = (parent Namespace, host)

fresh Proxmox interface evidence
  = (host, observed prefix)
```

The Job must resolve or create the one Nautobot host object in the intended Namespace, while
retaining the exact observed prefix in `proxmox_managed_ip_evidence`. It must not create a second
row merely because the existing row has another mask length, and it must not rewrite an unrelated
row's native mask, DNS name, status, role, tenant, tags, or relations.

Source revisions at plan-writing time:

| Repository | Revision |
|---|---|
| superproject | `30300b8280eb2037124bfa3e279379664194a087` |
| `nauto` | `1d2052ce469fe0ee03d554ed069c7a03fa198053` |
| `nctl` | `d7b0e21c1bc9f459ecc0e3ce9bbe4c72ade99de3` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |
| `nintent` | `ad9d36397d23c269ad748e13acbccc532fa29f52` |

The superproject was one commit ahead of `origin/main`; all inspected worktrees were otherwise
clean. Preserve [`problem.md`](problem.md) unchanged as the original defect record.

## 1. Required State Transitions

### 1.1 Existing host, different native mask

The concrete positive case is `agdnsmasq`:

```text
Global Namespace
  + existing IPAddress 192.168.0.2/32
      dns_name=agdnsmasq.home.arpa
      no VMInterface relation
  + fresh lxc:108 net0 evidence 192.168.0.2/24
  -> resolve the existing row by (Global, 192.168.0.2)
  -> do not create another IPAddress
  -> do not change /32, dns_name, status, or other unrelated fields
  -> attach that row to lxc:108/net0
  -> record managed evidence key 192.168.0.2/24 with the existing IPAddress ID
  -> retain the guest, VMInterface, and relation
  -> report no guest_upsert_failed for lxc:108
```

The native `/32` and observed `/24` are not competing duplicate objects. `/32` is the existing
shared Nautobot row's current native mask; `/24` is the exact prefix reported for this interface
generation. The latter remains visible in the closed, provenance-bearing managed-evidence map.

### 1.2 Missing parent Prefix for a new host

The concrete conflict case is `aghaos`:

```text
fresh qemu:102 IPv6 candidate
  + no IPAddress with the same host in Global
  + no containing IPv6 Prefix in Global
  -> do not call IPAddress.validated_save()
  -> create no Prefix and no IPAddress
  -> record one bounded interface/IP error: ip_parent_prefix_missing
  -> count the candidate as ip.skipped
  -> retain the successfully upserted qemu:102 VM and eligible VMInterface evidence
  -> continue with unrelated guests
  -> report no guest_upsert_failed for qemu:102
```

The absence of a parent Prefix is real ledger data, not permission for nauto to invent IPAM
structure. It is a target-local IP candidate conflict. It must not roll back the entire guest.

### 1.3 Unexpected failure after a guest write

Known IP conflicts are handled before a failing ORM save. Truly unexpected failures still use the
existing per-guest savepoint:

```text
guest VM temporarily created/updated
  -> later unexpected exception
  -> guest savepoint rolls back all VM/VMInterface/IP writes
  -> discard that guest's temporary created/updated counts and changed_fields
  -> report vm.skipped += 1 and one bounded terminal guest error
  -> continue with unrelated guests
```

The public summary must describe committed state in apply mode and state that would commit absent
the outer rollback in preview mode. It must never count a row whose guest savepoint rolled back.

### 1.4 Preview, apply, and repeat

After the repair:

```text
same fresh aghub report + dry_run=true
  -> all nine guests reach their intended per-guest result
  -> aghaos has a local missing-parent-Prefix IP conflict, not a guest failure
  -> agdnsmasq reuses 192.168.0.2 and succeeds
  -> the real duplicate 192.168.0.30 ownership remains foreign_ip_relation
  -> exact truthful counts and bounded errors are returned
  -> Job-owned transaction rolls back
  -> refetch equals the before image

same report + dry_run=false, only after separate approval
  -> preview-equivalent graph and conflicts commit
  -> refetch matches managed evidence and native relations

identical repeat apply
  -> zero creates/updates
  -> no repeated attach/detach
  -> unchanged IDs, relations, managed evidence, and last_updated
```

## 2. Scope and Non-goals

### 2.1 In scope

- `nauto/jobs/ingest_nodeutils_inventory.py`
  - explicit resolution of the one intended Nautobot Namespace;
  - Namespace-and-host IP lookup without `.first()` ambiguity;
  - containing-Prefix lookup before IP creation;
  - typed callbacks needed to resolve an IP by stable ID for managed-relation convergence.
- `nauto/jobs/proxmox_interfaces.py`
  - separation of Nautobot host identity from the observed address/prefix evidence key;
  - graceful per-candidate errors for missing parent Prefix and resolution ambiguity;
  - attach/detach ordering that remains correct when the observed prefix changes for the same
    host object;
  - preservation of foreign relations and unrelated native IP fields.
- `nauto/jobs/proxmox_upsert.py`
  - per-guest transactional result accumulation;
  - merging counts and `changed_fields` only after the guest savepoint exits successfully;
  - truthful failure counts after rollback.
- `nauto/tests/`
  - focused pure tests for identity, evidence, conflict, convergence, and count behavior;
  - real Nautobot ORM tests for the two live failures;
  - Job-level preview/apply/repeat and rollback proof.
- `devdocs/big/vm/p2/plan.md`
  - refine the Phase 2 IP mapping and matching text to distinguish native IP identity from exact
    observed-prefix evidence.
- `nctl` fixture tests if needed to prove that an observed `/24` evidence key pointing to a native
  `/32` row is still classified as managed by IP ID, not as an unrelated relation.
- deployment of the reviewed nauto revision and resumption of sidefix1 Step 7 items 1-6.

### 2.2 Explicit non-goals

This fix does not:

- create an IPv6 Prefix, Namespace, desired endpoint, or any other IPAM prerequisite;
- infer a parent Prefix from Proxmox, routing tables, another Namespace, or an arbitrary broad
  default;
- change `nodeutils.proxmox.v1` or discard the `aghaos` IPv6 observation;
- rewrite an existing `IPAddress.mask_length` to match one observer;
- rewrite an existing IP's parent, Namespace, DNS name, type, status, role, tenant, description,
  tags, NAT relation, Device relation, desired-endpoint relation, or foreign VMInterface relation;
- treat a row from another Namespace as the Global row;
- detach or steal a foreign relation;
- hide the real `192.168.0.30` duplicate-use conflict between `lxc:101` and `lxc:107`;
- weaken per-guest savepoints or the sidefix1 transaction-rolled-back preview;
- change Proxmox, nintent desired state, nctl drift, inventories, SSH trust, or Phase 3+ compute
  models;
- authorize the Phase 2 Step 9 persistent apply; or
- declare Phase 2 complete before the original Step 9 and Step 10 gates pass.

## 3. Contract Corrections

### 3.1 One explicit Namespace owner

Phase 2 currently creates IPs in Nautobot's default `Global` Namespace implicitly. Make that
existing contract explicit:

1. The real Job resolves exactly one Namespace named `Global` before Proxmox IP handling.
2. Zero or multiple matches is a shared IPAM prerequisite failure, not permission to select an
   arbitrary Namespace.
3. `find_ip` queries `host=<canonical host>, parent__namespace=<resolved Global Namespace>`.
4. A same-host row in another Namespace is a different object and is neither adopted nor changed.
5. `create_ip` receives the exact containing Prefix from the same Namespace and sets it explicitly;
   `validated_save()` remains the final ORM validation boundary.

Do not add a configurable Namespace to nintent or the report in this sidefix. There is no current
consumer requiring per-platform Namespace intent, and the deployed environment has exactly one
`Global` Namespace.

### 3.2 Match existing IPAddress rows by the real uniqueness key

Replace the current exact `(host, mask_length)` lookup with a bounded resolution:

| Matches for `(Global, canonical host)` | Result |
|---:|---|
| 0 | Search for the closest containing Prefix in Global, then create only if it exists |
| 1 | Reuse that IPAddress, regardless of its native `mask_length` |
| >1 | `ip_address_ambiguous`; create/attach/detach nothing for that candidate |

Do not use `.first()`. Although the database constraint should prevent duplicates inside one
Namespace, fail closed if corrupt or transitional data violates that assumption.

When one existing row has a different native mask:

- keep the native row unchanged;
- apply the existing foreign-VMInterface relation check;
- permit an existing Device-interface relation, as Phase 2 already requires for the dual
  guest-OS/compute observation layers;
- attach the VMInterface relation only when ownership checks pass; and
- store the exact observed `address/prefix` key and the reused row's `ip_id` in
  `proxmox_managed_ip_evidence`.

This refines `plan.md` Section 5.4. For a newly created IPAddress, native host/mask come from the
observation. For an adopted shared host row, native mask is not nauto-owned; the exact observed
prefix lives in the managed evidence key.

### 3.3 Check parent Prefix before create

For a host with no existing Global IPAddress:

1. Query the `Global` Prefix queryset for the closest containing Prefix using the deployed
   Nautobot manager's containment semantics.
2. Use `include_self=True`, matching Nautobot's own `IPAddress._get_closest_parent()` behavior.
3. If no Prefix exists, return the typed candidate result `ip_parent_prefix_missing`.
4. If one exists, create the IPAddress with the exact observed address/prefix, the existing fixed
   `Active` status, and that explicit parent.
5. Let `validated_save()` enforce all remaining model constraints.

Do not parse generic exception strings to discover this expected state. A narrow fallback may
translate a real `ValidationError` on the Namespace/parent boundary if a race or version-specific
validation path still reaches it, but unknown validation errors must escape to the per-guest
savepoint and remain truthful unexpected failures.

### 3.4 Keep evidence keys exact while converging relations by IP identity

Changing `find_ip` to host identity exposes an additional ordering hazard in the current
algorithm:

```text
prior managed key 192.168.0.2/24 -> IP id X
new observed key   192.168.0.2/32 -> same IP id X
```

The current attach-new-then-detach-old loop could attach `X` and then detach `X`, leaving a managed
key that claims a relation no longer present. Repair the algorithm as one desired-set operation:

1. Canonicalize and group candidates by host within the target Namespace.
2. If one generation reports the same host with multiple different prefixes, return
   `ip_observed_prefix_ambiguous` for that host and do not choose by order.
3. Resolve each accepted host to one existing or newly created IPAddress.
4. Run foreign-relation checks before changing the relation.
5. Build the new managed map using exact observed `address/prefix` keys and resolved `ip_id`s.
6. Attach each desired IP object at most once.
7. Resolve prior managed entries by their stored `ip_id`, not by their old prefix.
8. Detach a prior managed relation only when that IP ID is absent from every successfully resolved
   new managed entry.
9. If a legacy prior entry lacks a usable `ip_id`, use a bounded Namespace+host fallback. On
   missing or ambiguous resolution, retain the relation and report
   `managed_ip_reference_unresolved`; never guess.
10. Save managed evidence only after native relation changes succeed inside the same guest
    savepoint.

This preserves exact observation provenance without confusing a prefix-only evidence change with a
different Nautobot IP object.

### 3.5 Structured error and count semantics

Use bounded public errors with the existing shape:

| Code | Scope | Classification | Mutation behavior |
|---|---|---|---|
| `ip_parent_prefix_missing` | interface slot / `ip` | target-local candidate conflict | no Prefix/IP/relation creation; guest retained |
| `ip_address_ambiguous` | interface slot / `ip` | target-local ledger conflict | no create/attach/detach for host |
| `ip_observed_prefix_ambiguous` | interface slot / `ip` | target-local observation conflict | no create/attach/detach for host |
| `managed_ip_reference_unresolved` | interface slot / `ip` | target-local convergence conflict | retain relation/evidence; no guessed detach |
| `foreign_ip_relation` | interface slot / `ip` | existing behavior, target-local ownership conflict | foreign relation untouched |
| `guest_upsert_failed` or a typed unexpected code | guest / terminal section | unexpected guest failure | entire guest savepoint rolled back |

Known candidate conflicts increment `ip.skipped` once per rejected canonical host and remain in
`guest_errors`; they do not add `vm.skipped` and do not erase the VM/VMInterface.

Do not silently recategorize the whole platform's collection completeness. Preserve the existing
Phase 2 distinction between complete source observation and local ledger conflicts, and document
the exact final `observation_state` produced by the real multi-guest preview. Any change to that
existing classification requires an explicit contract update rather than an incidental side
effect of this fix.

### 3.6 Merge guest results only after savepoint success

For each guest, allocate local result state:

- `guest_counts`;
- `guest_changed_fields`;
- non-terminal interface/IP errors; and
- any interface evidence changes.

Perform the VM and interface/IP path inside `guest_atomic()`. Only after the context manager exits
successfully:

- merge the guest counts into the platform counts;
- merge the guest `changed_fields`;
- append its non-terminal errors; and
- retain its successful evidence.

If the savepoint exits with an exception:

- discard all local created/updated/unchanged/skipped counts from the rolled-back attempt;
- discard its changed-field claims;
- increment only `vm.skipped` once for the failed guest;
- append one bounded terminal guest error, preferring a known typed code over
  `guest_upsert_failed`; and
- continue with the next guest.

Cluster counts remain outside guest accumulators because the Cluster transaction is intentionally
platform-scoped. The summary must not claim `vm.created=9` when only seven guest savepoints
succeeded.

## 4. Implementation Surfaces

### 4.1 `nauto/jobs/ingest_nodeutils_inventory.py`

- Resolve `Global` through the real Namespace model with exact cardinality.
- Replace `find_ip(address, prefix)` with a Namespace-aware host resolver that returns zero, one,
  or ambiguity explicitly.
- Add closest-parent lookup and explicit-parent create wiring.
- Add lookup by stable IP ID for safe detachment of prior managed relations.
- Keep all callbacks inside the Job-owned transaction from sidefix1.
- Keep `validated_save()` as the final create validation.

Prefer a small typed resolution object or typed exception/result codes over sentinel combinations.
Do not make the Django-free pure module inspect Django `QuerySet` or `ValidationError` internals.

### 4.2 `nauto/jobs/proxmox_interfaces.py`

- Change callback contracts and docstrings from `(address, prefix)` identity to target-Namespace
  host resolution plus exact evidence keys.
- Implement host-group validation and desired-set convergence.
- Return known candidate conflicts through `IpSyncOutcome.conflicts`.
- Preserve the current maximum managed-IP bound and deterministic ordering.
- Never place raw validation messages or provider payloads in the summary/custom fields.

### 4.3 `nauto/jobs/proxmox_upsert.py`

- Add guest-local counts and changed-field accumulation.
- Ensure every merge occurs after successful savepoint release.
- Ensure exceptions from context-manager exit are included in the rollback path.
- Preserve successful interface conflict errors for guests that commit.
- Discard action claims belonging to a rolled-back guest.

### 4.4 Documentation and downstream readers

- Update `plan.md` Sections 5.4, 5.5, 8.2, and Step 9 wording where it currently implies that
  native `(host, prefix)` is the reusable IPAddress identity.
- State that exact observed prefix is carried by the managed-evidence key when an existing shared
  row has another native mask.
- Confirm nctl's managed/unrelated classification remains ID-based. Add a regression fixture for
  native `/32` plus manageいたSF怪奇冒険漫画『アルトゥリ・モンディ[注 3]（ALTRI MONDI）』を原作としd `/24` evidence if the existing tests do not already prove it.
- No output-schema version bump is expected: all proposed error codes use the existing bounded
  error envelope, and `proxmox_managed_ip_evidence` already maps exact keys to `ip_id`.

## 5. Verification Plan

### 5.1 Pure and fake-ORM tests

Extend the fake store so it no longer preserves the faulty shared assumption:

- uniqueness is enforced by Namespace+host, not host+mask;
- Prefix availability is explicit;
- IP lookup can return zero, one, or multiple candidates;
- relation attachment is distinguishable from IPAddress creation;
- prior managed entries are resolvable by `ip_id`; and
- guest savepoint rollback can restore stores while the result accumulator is inspected.

Required focused cases:

1. Exact existing host/prefix is reused and attached.
2. Existing host with another mask is reused; native fields remain byte-for-byte unchanged.
3. A Device-interface relation does not block the compute VMInterface relation.
4. A foreign VMInterface relation remains `foreign_ip_relation` and is never stolen.
5. Same host in another Namespace is not adopted.
6. Missing parent Prefix produces `ip_parent_prefix_missing`, no create call, and no guest
   rollback.
7. A new host under a valid parent Prefix creates exactly one IPAddress.
8. Multiple same-host rows in the target Namespace fail closed as `ip_address_ambiguous`.
9. One observation generation containing the same host with different prefixes fails closed as
   `ip_observed_prefix_ambiguous`.
10. Prior `/24` and new `/32` evidence resolving to the same IP ID changes the evidence key without
    detaching the relation.
11. A complete IP removal detaches only the relation named by prior managed `ip_id`.
12. Missing/ambiguous legacy managed references are retained, not guessed.
13. An unexpected failure after VM creation yields `vm.created=0`, `vm.skipped=1`, and no rolled-
    back guest `changed_fields`.
14. One failed guest does not alter counts or rows for successful siblings.
15. Identical repeat has zero creates/updates and no relation churn.

### 5.2 Real Nautobot ORM tests

Fake ORM remains insufficient for the two defects. Use the running local Nautobot container and
the established `/tmp/nauto_review` scratch-module method, neutralizing Job registration and
wrapping every fixture in an outer rollback-capable transaction.

Round A — native-mask reuse:

1. Use the existing `Global` Namespace and a test Prefix.
2. Create or select one test-owned IPAddress with native `/32`, a nonempty DNS name, and no
   VMInterface relation.
3. Ingest a synthetic LXC report for the same host with observed `/24`.
4. Prove the same IP ID is attached, no second row exists, native `/32` and all unrelated fields
   remain unchanged, and managed evidence contains `/24 -> same ID`.
5. Repeat identically and prove no writes/last-updated changes.

Round B — missing parent Prefix:

1. Select a test-only IPv6 host for which `Global` has no containing Prefix.
2. Ingest one QEMU guest with that candidate alongside one valid sibling.
3. Prove the QEMU VM and eligible VMInterface survive, no IPv6 Prefix/IP row is created,
   `ip_parent_prefix_missing` is reported, and `guest_upsert_failed` is absent.
4. Prove the sibling succeeds independently.

Round C — rolled-back count truth:

1. Inject an unexpected failure after a test guest's VM upsert but before guest completion.
2. Prove the savepoint restores every row/relation.
3. Prove no created/updated count or changed-field claim from that guest remains.
4. Prove `vm.skipped=1` and successful sibling counts are exact.

Round D — prefix-only evidence transition:

1. Attach one test-owned IPAddress through managed `/24` evidence.
2. Ingest a newer complete observation for the same host with `/32`.
3. Prove the relation remains present throughout the final state, the managed key becomes `/32`,
   and no unrelated relation or native IP field changes.
4. Repeat identically and prove no-op behavior.

All rounds must roll back their outer fixture transaction and refetch the pre-test database state.
Real model validation, real through-model relations, and real `last_updated` values are mandatory;
an in-memory imitation is not a substitute.

### 5.3 Fresh real-report preview

Before deployment, replay the exact fresh `aghub` report from
`.local/vm-p2/20260725-step7/` through the reviewed code inside a rolled-back real ORM run.

Assert positively:

- all 9 guest scopes are accounted for exactly once;
- `lxc:108` (`agdnsmasq`) and `net0` succeed;
- the existing `192.168.0.2/32` row is reused and remains unchanged;
- managed evidence records `192.168.0.2/24` with that row's ID;
- `qemu:102` (`aghaos`) retains its VM/eligible interface and reports
  `ip_parent_prefix_missing`, not `guest_upsert_failed`;
- the real `192.168.0.30` duplicate use remains `foreign_ip_relation`;
- no rolled-back guest is counted as created/updated;
- errors are bounded and contain no raw report or traceback; and
- post-run target state equals the before image.

Do not require every real guest to be conflict-free. The gate is truthful isolation and the named
positive case, not suppression of genuine Proxmox/IPAM conflicts.

### 5.4 Repository commands

Run from documented working directories and record exact versions/output:

```bash
cd nauto
python3 -m unittest \
  tests.test_proxmox_cluster_vm_upsert \
  tests.test_proxmox_interface_ip_upsert \
  tests.test_ingest_nodeutils_inventory_job \
  tests.test_nodeutils_ingest_summary
python3 -m unittest discover -s tests
python3 -m py_compile jobs/*.py
```

Record the exact `nautobot-server shell` command or test module used for the real-ORM rounds.

If nctl fixtures are added or its behavior changes, run at least:

```bash
uv run --project nctl pytest \
  nctl/tests/test_sources_actual.py \
  nctl/tests/test_actual_render.py
```

Finish with:

```bash
git diff --check
git status --short
git -C nauto diff --check
git -C nauto status --short
```

Review all affected submodule diffs and confirm unrelated worktrees remain untouched.

## 6. Implementation Sequence and Gates

### Step 0 — Freeze the live ORM contract and reproduce all three gaps

1. Record revisions and clean/dirty state.
2. Preserve the original sidefix2 evidence.
3. Record real model fields, `unique_together`, Namespace cardinality, parent-Prefix lookup
   behavior, and the existing `192.168.0.2/32` row without private payloads.
4. Add failing tests for both ORM defects and rolled-back count leakage.
5. Record current behavior for a prefix-only evidence-key transition before changing lookup
   semantics.

Gate: the matching key, parent requirement, count leak, and detach-order hazard are each
reproducible; no persistent change.

### Step 1 — Implement explicit Namespace/host resolution

1. Resolve the exact `Global` Namespace once.
2. Add bounded host lookup and stable-ID lookup callbacks.
3. Add closest-parent preflight and explicit-parent creation.
4. Remove `.first()` and exact-mask identity assumptions.

Gate: `/32` existing plus `/24` observed resolves to one unchanged IP object, and a missing parent
returns a typed result before create.

### Step 2 — Repair IP relation convergence

1. Group by host and reject multiple observed prefixes deterministically.
2. Resolve the complete desired IP object set before detach decisions.
3. Build exact observed-prefix evidence keys.
4. Attach each desired IP once and detach only prior managed IDs absent from the desired set.
5. Preserve foreign and unresolved relations.

Gate: prefix-only evidence changes cannot remove the final relation, and complete disappearance
still detaches only the ingestor-managed relation.

### Step 3 — Make guest summaries transaction-truthful

1. Introduce guest-local accumulators.
2. Merge them only after savepoint success.
3. Discard all rolled-back action claims and merge one terminal skip/error.
4. Verify successful non-terminal interface/IP conflicts remain visible.

Gate: object counts and `changed_fields` reproduce the state that would commit; no failed guest is
double-counted.

### Step 4 — Prove focused and real-ORM behavior

Run Sections 5.1 and 5.2, then the full nauto suite.

Gate: both original tracebacks are replaced by their intended successful/local-conflict paths,
real ORM constraints are exercised, every fixture rolls back, and all tests pass.

### Step 5 — Replay the exact live report without persistence

Run Section 5.3 against the exact fresh report and capture a sanitized summary/before-after proof
under `.local/vm-p2/` with restrictive permissions.

Gate: `agdnsmasq` is the required positive IP relation, `aghaos` is isolated at the candidate
level, the real foreign-IP conflict remains truthful, counts match surviving guest savepoints, and
the before image is unchanged.

### Step 6 — Review, commit, and deploy

1. Review the nauto and documentation diffs.
2. Commit the nauto fix as one reviewable sidefix2 commit.
3. Commit the superproject documentation/submodule-pin update separately as appropriate.
4. Ask the user to push; do not push on their behalf.
5. Sync the Nautobot Git Repository after the commit is available remotely.
6. Confirm the installed `Ingest Nodeutils Inventory` revision equals the reviewed/tested nauto
   revision.

Gate: the deployed Job is byte-for-byte the reviewed revision; no persistent virtualization
ingest has run.

### Step 7 — Resume sidefix1 Step 7 and Phase 2 Step 9

Before any persistent apply:

1. Take a new fresh `aghub` collection if the prior report no longer satisfies the freshness
   contract.
2. Save a new sanitized Nautobot before image.
3. Run the deployed Job with `dry_run=true`.
4. Assert the exact guest set, counts, errors, stable provider identities, and managed relations.
5. Positively confirm `lxc:108/net0`, reuse of the existing host row, and exact `/24` managed
   evidence.
6. Positively confirm `qemu:102` is not rolled back by the missing IPv6 parent.
7. Refetch and prove equality with the before image.
8. Review the sanitized preview and stop for the existing separate apply approval.

Only after explicit approval:

9. Apply the identical fresh report once.
10. Refetch the full Cluster/VM/VMInterface/IP graph and run `nctl actual --json`.
11. Prove native `192.168.0.2/32` remains unchanged while `/24` is managed evidence.
12. Repeat the identical ingest and prove no creates/updates, no relation churn, and unchanged
    timestamps.
13. Continue the original `report2.9.md` and Step 10 process.

Gate: any named guest-level failure, duplicate IP creation attempt, rolled-back count leakage,
preview rollback leak, unexpected error suppression, preview/apply mismatch, or non-empty
identical repeat fails the step.

## 7. Rollback and Failure Handling

- Any unit, real-ORM, or exact-report replay failure stops before deployment.
- Any deployed preview with unexpected output stops before persistent apply.
- If Namespace resolution is not exactly `Global`, stop the report; do not fall back to another
  Namespace.
- If the closest-parent lookup and `validated_save()` disagree, preserve the bounded error and
  traceback only in restricted local evidence, then stop implementation review. Do not convert an
  unknown validation failure into `ip_parent_prefix_missing`.
- If refetch differs after `dry_run=true`, preserve before/after evidence and write a separate
  repair plan. Do not delete or rewrite rows automatically.
- If the approved apply partially succeeds, preserve per-guest evidence and refetch actual state
  before retrying. Do not infer state from summary counts alone.
- Do not remove the existing `/32` row, create an IPv6 Prefix, or edit the real duplicate
  `192.168.0.30` configuration merely to make the preview green.
- No Nautobot rollback or repair authorizes a Proxmox resource mutation.
- Reports contain only bounded identifiers, counts, timestamps, field names, and error codes. Raw
  reports remain gitignored with restrictive permissions; tokens, credentials, and unrestricted
  provider payloads are never committed.

## 8. Definition of Done

This blocker is complete only when every applicable item is proven:

- [ ] IPAddress resolution uses exact target Namespace plus canonical host and never `.first()`.
- [ ] The target Namespace is explicitly and uniquely resolved as `Global`.
- [ ] A same-host row in another Namespace is not adopted.
- [ ] Existing same-host/different-mask rows are reused without changing native IP fields.
- [ ] `agdnsmasq` reuses the existing `192.168.0.2/32` row and records exact `/24` managed
      evidence pointing to the same ID.
- [ ] No duplicate `192.168.0.2` creation is attempted.
- [ ] Missing parent Prefix is detected before create and reported as
      `ip_parent_prefix_missing`.
- [ ] The `aghaos` VM and eligible interface are retained; no IPv6 Prefix/IP is invented.
- [ ] Foreign VMInterface ownership remains `foreign_ip_relation` and is untouched.
- [ ] Device-interface dual-layer relations remain allowed.
- [ ] Same-host/multiple-prefix observation is deterministic and fail-closed.
- [ ] Prefix-only evidence changes cannot detach the still-desired IP relation.
- [ ] Detach uses recorded managed IP identity and never guesses an unresolved legacy reference.
- [ ] Guest counts and `changed_fields` merge only after savepoint success.
- [ ] A rolled-back guest contributes no created/updated/unchanged action claim and exactly one
      terminal VM skip/error.
- [ ] Successful siblings retain exact counts when another guest fails.
- [ ] Pure/fake-ORM tests and real Nautobot ORM rounds cover both original failures.
- [ ] Identical repeat is a no-op with unchanged IDs, relations, evidence, native fields, and
      `last_updated`.
- [ ] Full nauto tests, syntax checks, affected nctl tests, and `git diff --check` pass.
- [ ] The exact fresh real report passes a rolled-back local replay with a before/after equality
      proof.
- [ ] The deployed Job revision equals the reviewed/tested nauto commit.
- [ ] The resumed live `dry_run=true` preview leaves the persistent before image unchanged.
- [ ] Separate user approval is obtained before Phase 2 Step 9's persistent apply.
- [ ] No Prefix, Namespace, Proxmox resource, desired-state row, unrelated Nautobot field/relation,
      generated inventory, or SSH trust entry is changed by this blocker fix.

Passing local tests alone supports at most `implemented, not deployed`. The blocker remains open
until the deployed fresh-report preview proves the named `agdnsmasq` positive path, the isolated
`aghaos` conflict, truthful counts, and transaction rollback. Phase 2 remains incomplete until the
separately approved persistent apply, refetch, identical repeat, and original Step 10 audit also
pass.
