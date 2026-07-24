# Phase 2 Sidefix1 Step 0 Report: Freeze the Contract and Reproduce the Failure

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 0 ("Freeze the contract and
reproduce the failure"). This step is static/test-only: no Nautobot, `aghub`, or Proxmox state was
touched.

## 1. Frozen revisions and worktree state (fixplan Step 0.1)

Matches the plan's own baseline table exactly; no submodule had moved since `problem_fixplan.md`
was written:

| Repository | Revision |
|---|---|
| superproject (`HEAD`) | `6801f0a2012b5064335c398457d8f5ffbb93a91b` |
| `nauto` | `4cea3b68b1bc766aedf75d8ea166b0e68d735bc2` |
| `nctl` | `d7b0e21c1bc9f459ecc0e3ce9bbe4c72ade99de3` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |

`git status -sb` in the superproject showed only the two untracked `sidefix1/problem.md` /
`problem_fixplan.md` files (already noted as intentionally untracked in `problem_fixplan.md`);
`nauto`'s tree was clean before this step's test-only addition.

## 2. Existing nauto tests (fixplan Step 0.2)

```
cd nauto
python3 -m unittest tests.test_proxmox_cluster_vm_upsert tests.test_proxmox_interface_ip_upsert \
  tests.test_nodeutils_ingest_summary
# Ran 60 tests in 0.004s, OK
python3 -m unittest discover -s tests
# Ran 89 tests in 0.006s, OK
python3 -m py_compile jobs/*.py
# no output (success)
```

All pre-existing tests pass at this baseline.

## 3. New failing Job-level test (fixplan Step 0.3)

Added `nauto/tests/test_ingest_nodeutils_inventory_job.py`. It loads the real
`jobs/ingest_nodeutils_inventory.py` by file path as a submodule of a stub `jobs` package
(stubbing only `nautobot.apps.jobs`, `django.apps`, `django.core.exceptions`, and `django.db`,
mirroring the existing `test_generate_desired_services.py` pattern), and calls the real
`ingest_report()` directly with `ingest_proxmox()` mocked out — isolating the orchestration
decision per the plan's Section 6.1 note, without covering the real ORM persistence core (already
covered by `test_proxmox_cluster_vm_upsert.py` / `test_proxmox_interface_ip_upsert.py`).

Two cases, one existing observer Device with `facts.proxmox` present:

- `test_apply_reaches_proxmox_ingest_for_an_existing_device` (`dry_run=False`) — **passes today**:
  `ingest_proxmox()` is called once, `result["proxmox"]` is present.
- `test_preview_reaches_proxmox_ingest_for_an_existing_device` (`dry_run=True`) — **fails today**:

  ```
  AssertionError: Expected 'mock' to have been called once. Called 0 times.
  ```

  `job.ingest_proxmox` is never called and `result["proxmox"]` is absent, reproducing the exact
  Step 9 blocker from `problem.md`/`problem_fixplan.md` Section 4.1: `ingest_report()` returns at
  `dry_run=true` (`ingest_nodeutils_inventory.py:250-251`) before it reaches `facts.get("proxmox")`
  at line 263.

Full-suite confirmation: `python3 -m unittest discover -s tests` now reports **90 passed, 1
failed** (the new red test) out of 91 total — no other test regressed.

## 4. Current hybrid save-suppression/IP-mutation behavior (fixplan Step 0.4)

Recorded directly from the current `nauto/jobs/proxmox_upsert.py` and
`nauto/jobs/proxmox_interfaces.py`, matching the plan's Section 4.2 description exactly:

- `proxmox_upsert.upsert_with_freshness()` (used for Cluster and VM rows) gates every `save_fn()`
  call behind `if not dry_run:` — create branch (`proxmox_upsert.py:291`) and update branch
  (`proxmox_upsert.py:324`).
- `proxmox_upsert.ingest_proxmox_platform()` gates two more `save_fn()` calls the same way: the
  per-guest interface-evidence merge onto the VM row (`proxmox_upsert.py:566`) and the final
  Cluster `observation_state`/`observation_detail` write (`proxmox_upsert.py:582`).
- `proxmox_interfaces.sync_guest_interfaces()` gates its own three `save_fn()` calls behind
  `if not dry_run:` the same way — new-interface create (`proxmox_interfaces.py:418`),
  existing-interface update (`proxmox_interfaces.py:428` for the immediate IP-evidence save,
  `proxmox_interfaces.py:471` for the field-diff save) and presence-absence convergence
  (`proxmox_interfaces.py:505`).
- `proxmox_interfaces.sync_interface_ips()` — the function actually called by
  `sync_guest_interfaces()` to converge IP relations — **takes no `dry_run` parameter at all** and
  unconditionally calls `create_ip()` (`proxmox_interfaces.py:320`), `attach_ip()`
  (`proxmox_interfaces.py:324`), and `detach_ip()` (`proxmox_interfaces.py:334`) regardless of
  mode. The presence-absence convergence loop in `sync_guest_interfaces()` likewise calls
  `detach_ip()` unconditionally (`proxmox_interfaces.py:501`) before its own gated `save_fn()`.

This confirms the plan's diagnosis precisely: Cluster/VM/VMInterface row saves are suppressed by a
lower-level Boolean, while IPAddress create/attach/detach run the same in both modes — two
different, independently-toggled behaviors glued together under one Job-level `dry_run` name, not
one transaction-backed preview.

## 5. Audit of every `dry_run` branch and persistence callback reached by Proxmox ingest (fixplan
   Step 0.5)

Complete enumeration of every place `dry_run` changes behavior, and every callback that performs a
Nautobot write, reached from `ingest_report()` → `ingest_proxmox()` →
`proxmox_upsert.ingest_proxmox_platform()`:

| Location | Behavior under `dry_run=True` today |
|---|---|
| `ingest_nodeutils_inventory.py:250-251` (`ingest_report`) | Returns before reading `facts.proxmox`; `ingest_proxmox()` is never called (**the Step 9 blocker**, Section 4.1). |
| `ingest_nodeutils_inventory.py:142` (`run`) | Sets `self.dry_run` on the Job instance; this is the value threaded down as the `dry_run` kwarg. |
| `ingest_nodeutils_inventory.py:172-174` (`run`) | Marks the owning transaction rollback-only and logs; this part of the contract already matches the target design and needs no change. |
| `proxmox_upsert.upsert_with_freshness()` (Cluster/VM) | `save_fn()` suppressed; in-memory object is still mutated/returned either way. |
| `proxmox_upsert.ingest_proxmox_platform()` interface-evidence merge | `save_fn()` suppressed. |
| `proxmox_upsert.ingest_proxmox_platform()` Cluster observation finalize | `save_fn()` suppressed. |
| `proxmox_interfaces.sync_guest_interfaces()` (create/update/absence) | `save_fn()` suppressed in all three spots; in-memory `iface`/`existing` object is still mutated either way. |
| `proxmox_interfaces.sync_interface_ips()` (`create_ip`/`attach_ip`/`detach_ip`) | **Not suppressed** — runs identically in both modes. |
| `ingest_nodeutils_inventory.py` `find_ip`/`create_ip`/`attach_ip`/`detach_ip`/`ip_related_elsewhere` closures (passed into `ingest_proxmox_platform`) | No `dry_run` awareness of their own; they always hit `IPAddress.objects`/`IPAddressToInterface.objects` when called, regardless of mode — confirms the previous row's finding at the real-ORM wiring layer, not just the pure-module layer. |

Side-effect-audit scope for a later step (fixplan Section 4.3/6.4), not run here: Django/Nautobot
`pre_save`/`post_save`/`m2m_changed`/delete signals, Job Hooks, Event Rules, webhooks, or plugins
on `Cluster`/`VirtualMachine`/`VMInterface`/`IPAddress`/their through model, and any
`transaction.on_commit()` handler. This step only enumerates the code-level `dry_run` branches and
callbacks the fix must reach; it does not yet inspect the live Nautobot instance's configured
hooks.

## Gate

- The early-return defect and every divergent preview/apply branch are enumerated: proven (Section
  4 and Section 5 tables above).
- No live state changed: proven — this step ran only local `python3 -m unittest`/`py_compile`
  against the existing `nauto` worktree; no Nautobot, `aghub`, or Proxmox call was made.

Step 0 is satisfied. Proceeding to Step 1 (centralize preview ownership) remains gated behind this
step's own review.
