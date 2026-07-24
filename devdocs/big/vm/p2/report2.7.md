# Phase 2 Step 7 Report: Full Automated and Fixture-Backed Verification

Status: implemented, environment-backed round trip proven locally (not deployed to `aghub`/live
Proxmox — that remains Steps 8-9).

This report covers [`plan.md`](plan.md) Step 7 ("Full automated and fixture-backed
verification"). Unlike Steps 4-6, this step required going beyond the duck-typed fake-ORM unit
tests those steps used, because Step 7's own gate explicitly calls for "apply in
rollback-capable test DB/environment ... identical ingest ... zero writes." That environment
exists locally as the `devenv/nautobot` Docker Compose stack (already running, per
`.local/localenv_memo.md`). The user confirmed running the round trip against that local instance
before this step proceeded.

## 1. Repository command matrix (Section 8.1)

```
$ cd nauto && python3 -m unittest discover -s tests
Ran 89 tests in 0.007s
OK

$ cd nctl && uv run pytest tests -q
999 passed, 1 warning in 6.14s
```

`ansible_agdev`'s helper unit tests and `nodeutils`'s pytest suite were exercised in Steps 1-2
(see `report2.1.md`, `report2.2.md`) and are unchanged by Steps 4-7; they were not re-run here
since no file in those repositories changed in this step.

## 2. Environment-backed round trip (the step's actual gate)

### Method

Nautobot Jobs in this project are normally deployed by pushing `nauto` to GitHub and letting
Nautobot's Git Repository sync pull the update (confirmed live: the local instance's `main` Git
Repository tracks `https://github.com/iwaag/nauto`, currently pinned at the pre-Phase-2 commit
`617036d`). That deployment/sync path is Step 8's explicit responsibility, gated behind pushing
commits and a live sync — not this step's. To prove the round trip without pushing or touching the
deployed Job registration, this step instead:

1. Copied the current local `nauto` working tree into the running `nautobot` container at a
   scratch path (`/tmp/nauto_review`), with a neutralized `jobs/__init__.py` (no
   `register_jobs()` call) so no Job database record was created or altered.
2. From inside the container (`nautobot-server shell`, which has Django/Nautobot fully
   initialized), imported `jobs.seed_home_cluster` and `jobs.ingest_nodeutils_inventory` directly
   from that scratch path and instantiated the Job classes as plain Python objects.
3. Ran the whole sequence — seed (`dry_run=false`) then two identical ingests — inside a single
   `transaction.atomic()` block with a manual savepoint, and rolled the savepoint back
   unconditionally at the end. A separate post-run query confirmed zero Cluster/VirtualMachine
   rows remained and the pre-existing `aghub` Device (from Phase 1) was untouched.

This is a genuine ORM-level proof — real Django model validation, real `full_clean()`/
`validated_save()`, real custom-field/status/content-type constraints — without deploying to the
tracked Git Repository, without pushing anything, and without leaving any persisted change in the
shared local Nautobot database.

### Fixture

A `nodeutils.inventory.v2` report for observer `aghub` (reusing the real, already-existing `aghub`
Device from Phase 1 rather than fabricating a new one) with:

- one QEMU guest (`aghaos`, vmid 102) with a joined config/agent interface and an agent IP;
- the `agdnsmasq` LXC guest (vmid 108) with an explicit config interface and IP — the concrete
  positive case named in plan.md Section 1;
- IP addresses inside the real, already-seeded `192.168.0.0/24` Prefix (the first attempt used a
  synthetic `10.0.0.0/24` range with no matching Prefix, which surfaced a Nautobot IPAM
  precondition rather than a code defect — see below).

### Round-trip result (first, successful run)

| Assertion | Result |
|---|---|
| Seed creates `ClusterType "Proxmox VE"`, `virtual-machine`/`lxc-container` roles, all 21 `proxmox_*` custom fields | proven |
| First ingest: Cluster `aghub-proxmox` created, `standalone_node_fallback` scope key `standalone-device:<aghub Device UUID>` | proven |
| Both guests created: `(lxc, 108, agdnsmasq, Active)`, `(qemu, 102, aghaos, Active)` | proven |
| Both VMInterfaces created with correct MAC and `proxmox_presence=present` | proven |
| Both IPAddresses created and attached | proven |
| Platform `observation_state` = `complete` | proven |
| Identical second ingest: `object_counts` all `unchanged` (cluster 1, vm 2, vminterface 2), zero `created`/`updated` | proven |
| Cluster and both VM `last_updated` timestamps unchanged across the repeat ingest | proven |
| Malformed guest isolation (separate run, third LXC guest with `vmid=None` added alongside the two good guests) | the bad guest was rejected at Step 3's pure-validator layer (`invalid_vmid`, `guest_errors`), the two good guests still created normally, platform `observation_state` = `partial` |
| Post-rollback state | `Cluster.objects.count() == 0`, `VirtualMachine.objects.count() == 0`, `aghub` Device's pre-existing custom-field data unchanged |

## 3. Two real defects found and fixed

The first round-trip attempt failed twice before succeeding, both times against *real* Nautobot
model constraints that the fake-ORM unit tests in Steps 4/5 could not have caught because they
never modeled these constraints:

1. **`VMInterface.status` is a required native field** (`null=False`, `blank=False` in this
   Nautobot version). Step 5's `make_interface=lambda: VMInterface()` in
   `jobs/ingest_nodeutils_inventory.py` never set it, and no `proxmox_*` mapping was ever intended
   to carry this value (plan.md Section 5.4's VMInterface table does not mention `status` at all —
   a genuine plan gap, not just an implementation oversight). **Fix**: `make_interface` now sets
   `status=self.lookup_status("Active")`, matching the fixed-constant pattern already used for
   `IPAddress.status` in `create_ip()`. This is a required native-field default, not a claim about
   observed Proxmox interface operational state.
2. **The seeded `Active` `Status` object was never associated with the
   `virtualization.vminterface` or `ipam.ipaddress` content types.** `seed/home_cluster.yaml`
   already listed `virtualization.virtualmachine` for `Active` (added correctly in Step 3), but
   Step 5 introduced VMInterface and IPAddress writes without extending that same status's
   applicable content types, so both `full_clean()` calls failed with `"status instance ... is not
   a valid choice"`. **Fix**: added `virtualization.vminterface` and `ipam.ipaddress` to `Active`'s
   `content_types` list in `seed/home_cluster.yaml`.

Both fixes are committed to `nauto` (commit message: "vm p2 step 7: fix VMInterface/IPAddress
status gaps found in live round trip"). The full local unit-test suite (89 tests) still passes
after both changes.

A third apparent failure — "No suitable parent Prefix for 10.0.0.50 exists in Namespace Global" —
was **not** a code defect: Nautobot requires an IPAddress's parent Prefix to already exist in its
namespace, and the first fixture used a synthetic `10.0.0.0/24` range with no matching Prefix in
this dev instance. Switching the fixture's IP addresses into the real, already-seeded
`192.168.0.0/24` Prefix (the same range `aghub`'s own primary IP already lives in) resolved this
immediately, confirming it was a test-fixture artifact, not an ingest defect. This is worth noting
for Step 8/9: on `aghub`'s real network, IPs the Proxmox guests actually use must fall within an
existing Nautobot Prefix, or the same "no suitable parent Prefix" rejection will occur live — this
is expected, correct behavior (nauto does not invent Prefix objects, per Section 3.2's scope
boundary), not something to work around.

## 4. What Step 7 does not cover

- No deployment to the tracked `nauto` Git Repository, no push to GitHub, and no live Job
  execution through Nautobot's actual Job-run UI/API — that remains Step 8.
- No test against the real `aghub` Proxmox host or its actual guest inventory — the fixture is
  synthetic, matching the plan's illustrative `agdnsmasq`/vmid 108 case and reusing the real
  `aghub` Device identity, but not real Proxmox-collected facts.
- `nctl actual`'s live GraphQL query was not exercised end-to-end in this step (it remains
  fixture-tested per `report2.6.md`); the round trip above proves the Cluster/VM/VMInterface rows
  nctl's query targets are shaped as expected, but does not itself run nctl against them.
- Storage-content ingest remains unimplemented (unchanged since Step 4/5).
- Multi-generation partial-merge and IP-convergence scenarios beyond the ones covered by Step 5's
  fake-ORM unit tests were not additionally re-proven against the live ORM in this step, given the
  cost of constructing each additional live fixture; Step 5's 31 fake-ORM tests already cover that
  matrix in detail, and this step's purpose was to prove the ORM wiring itself works, which it now
  does for the create/no-op-repeat/per-guest-isolation paths exercised above.

## Gate

All local/fixture-backed unit-test suites pass (89 nauto + 999 nctl). The environment-backed
round trip — fresh create, positive `agdnsmasq` vmid 108 match, identical-repeat no-op with
unchanged `last_updated`, and one-bad-guest isolation — ran successfully against the local
Nautobot environment, with zero persisted writes (proven by transaction rollback and a
post-rollback row-count check). No empty guest list, unused helper path, empty ingest action set,
or absent refetch target was used to satisfy this gate.

Proceeding to Step 8 (coordinated deployment and fresh read-only collection) — which requires
pushing `nauto`/`nodeutils`/`ansible_agdev`/`nctl` commits and deploying to `aghub`, both squarely
in the "separate approval" category this plan and this project's standing practice require before
proceeding.
