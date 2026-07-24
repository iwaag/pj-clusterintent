# Phase 2 Sidefix2 Step 0 Report: Freeze the Live ORM Contract and Reproduce All Three Gaps

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`plan.md`](plan.md) Step 0 ("Freeze the live ORM contract and reproduce all
three gaps"). This step is read-only against the live Nautobot container (introspection only, no
writes) plus test-only against the `nauto` worktree.

## 1. Frozen revisions and worktree state (plan Step 0.1)

| Repository | Revision |
|---|---|
| superproject (`HEAD`) | `a9ac264f84ffec60faf1f294afec200de336a041` (`plan.md`'s own authoring commit, one ahead of the plan's recorded baseline `30300b8`) |
| `nauto` | `1d2052ce469fe0ee03d554ed069c7a03fa198053` (unchanged from the plan's baseline table) |

`git status --short` in the superproject shows only the untracked `sidefix2/plan.md` (already
noted as untracked in the plan itself, now joined by this report) before this step's addition;
`nauto`'s tree was clean before this step's test-only addition.

## 2. Real model fields, uniqueness, and Namespace cardinality (plan Step 0.3)

Queried directly against the running `nautobot-nautobot-1` container via
`nautobot-server shell` (read-only; user confirmed before running):

```
unique_together: (('parent', 'host'),)
constraints: []
Namespace count: 1
 ns: dad3d8f7-495a-4874-a592-9d12abb1013f Global
existing 192.168.0.2: 579213a3-491c-454e-9f32-f6c2d4b64dbd 192.168.0.2/32 32 Global agdnsmasq.home.arpa 2026-07-23 15:18:07.975924+00:00
v6 global prefixes: 0
```

Confirms `problem.md`/`plan.md`'s stated facts exactly:

- `IPAddress`'s only uniqueness constraint is `(parent, host)` — `parent` is the containing
  Prefix, whose own `namespace` is the effective Namespace scope; mask length plays no role in
  uniqueness.
- Exactly one Namespace exists (`Global`), matching plan Section 3.1's assumption that resolving
  it is unambiguous today.
- The pre-existing `192.168.0.2/32` row (`agdnsmasq.home.arpa`, `last_updated` predating this
  Phase 2 work) is exactly as `problem.md` Section 3 describes.
- Zero IPv6 Prefixes exist in `Global`, confirming `aghaos`'s candidate has no containing Prefix
  (`problem.md` Section 2).

## 3. Existing nauto tests (baseline)

```
cd nauto
python3 -m unittest discover -s tests
# Ran 95 tests in 0.011s, OK
python3 -m py_compile jobs/*.py
# no output (success)
```

## 4. New failing tests for all three gaps (plan Step 0.4)

Added `nauto/tests/test_ip_namespace_host_identity.py`. Its fake ORM enforces the *real* Nautobot
constraint (`create_ip` raises when a row with the same `host` already exists, regardless of mask,
and raises a distinct "no suitable parent Prefix" error when the observed address has none),
mirroring the two live tracebacks recorded in `problem.md` exactly rather than the old fake-ORM
assumption of `(host, mask_length)` uniqueness.

Three cases, all failing against current `jobs/ingest_nodeutils_inventory.py` /
`jobs/proxmox_upsert.py`:

- `test_existing_32_row_is_reused_for_observed_24_without_raising` — reproduces the `agdnsmasq`
  defect: today's `find_ip(host, mask)` misses the existing `/32` row for an observed `/24`,
  `create_ip` is attempted, the fake store's uniqueness check raises, and the guest ends up with
  `guest_upsert_failed` instead of reusing the row.

  ```
  AssertionError: {'scope_kind': 'guest', 'scope_id': 'lxc:108', 'section': 'identity',
  'code': 'guest_upsert_failed'} unexpectedly found in [...]
  ```

- `test_missing_parent_prefix_does_not_fail_the_whole_guest` — reproduces the `aghaos` defect:
  today's `create_ip` has no graceful path for a missing parent Prefix, so the guest is rolled back
  and reported as `guest_upsert_failed` instead of a bounded `ip.skipped` conflict.

  ```
  AssertionError: ('qemu:102', 'guest_upsert_failed') unexpectedly found in {...}
  ```

- `test_failure_after_vm_upsert_does_not_leave_a_created_count` — reproduces the count-leak gap
  (plan Section 3.6): `counts["vm"]` is mutated directly inside the guest's try-block
  (`proxmox_upsert.py:531`) before the guest finishes, so an unexpected exception later in the same
  guest (simulated here via a raising `find_ip`) leaves `vm.created=1` *in addition to*
  `vm.skipped=1` for the one rolled-back guest.

  ```
  AssertionError: 1 != 0 : rolled-back guest must not count as created
  ```

Full-suite confirmation: `python3 -m unittest discover -s tests` now reports **95 passed, 3
failed** (all three new tests) out of 98 total — no other test regressed. `python3 -m py_compile
jobs/*.py tests/*.py` succeeds.

## 5. Prefix-only evidence-key transition (current behavior, for later comparison)

Not yet exercised by a dedicated test at this step: the plan's Section 3.4 detach-order hazard
(prior managed key at one prefix, new observed key at the same host but a different prefix,
resolving to the same IP ID) requires the Step 2 convergence rewrite to even construct a
resolvable-by-ID managed-entry shape. Recording current behavior here would require prescribing
the shape of `proxmox_managed_ip_evidence` entries the fix itself is meant to introduce; deferred
to Step 1/2's own tests (plan Section 5.1 cases 10-12) rather than fabricated ahead of the
resolution-by-ID mechanism existing.

## Gate

- The matching key defect (`agdnsmasq`), the missing-parent-Prefix defect (`aghaos`), and the
  count-leak are each reproduced by a dedicated failing test grounded in real model constraints:
  proven (Section 4).
- No persistent change: proven — this step ran only read-only `nautobot-server shell` queries
  against the existing live container and local `python3 -m unittest`/`py_compile` against the
  `nauto` worktree; no Nautobot write, `aghub` call, or Proxmox mutation occurred.

Step 0 is satisfied. Proceeding to Step 1 (explicit Namespace/host resolution) remains gated behind
this step's own review.
