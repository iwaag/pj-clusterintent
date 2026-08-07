# QEMU creation path through nctl reconcile — implementation report

Date: 2026-08-07
Status: **implemented, not deployed** — code and local tests pass; no live Proxmox apply has been
run. Live QEMU creation still requires the usual dry plan plus a separately approved apply.

## Why

`nctl reconcile` could create Proxmox LXC guests (`create_lxc.yml` via the sole Phase 3 write
seam) and could destroy both LXC and QEMU guests, but had no QEMU creation path. Worse, the
create derivation never inspected `instance_kind`: a `virtual_machine` instance entered the same
create path as a container, and was only stopped by the incidental `vztmpl` template check — with
a `vztmpl` volid it would have created an LXC against declared VM intent. This closes that gap and
implements the minimum QEMU creation behavior of `devdocs/big/vm/roadmap.md` Phase 6.

## What changed

- `nctl/src/nctl_core/drift/compute_creation.py` — the create derivation is now kind-aware.
  `CREATABLE_GUEST_TYPES = {"container": "lxc", "virtual_machine": "qemu"}` mirrors the destroy
  side's `_DESTROYABLE_GUEST_TYPES`; an unmapped kind fails explicitly with
  `compute_instance_kind_not_creatable` instead of silently routing to LXC. The template gate is
  kind-aware (`vztmpl` for LXC, `iso` for QEMU). Parameters now pin `guest_type`;
  `unprivileged`/`ipv4_cidr`/`gateway_ipv4` are emitted for LXC only, and the static-network gate
  (`compute_endpoint_network_incomplete`) is container-only, because only `pct create` can inject
  the address — a QEMU guest receives its address inside the guest during manual initial access.
- `nctl/src/nctl_core/reconcile/actions/compute_create.py` — selects the playbook from the pinned
  `guest_type` (`CREATE_PLAYBOOKS`, mirroring `DESTROY_PLAYBOOKS`) and refuses an unmapped
  `guest_type` before any runner starts.
- `ansible_agdev/playbooks/proxmox/create_qemu.yml` — new bounded adapter, structurally identical
  to `create_lxc.yml`: refuse an occupied VMID, `qm create` with a fixed minimal argv
  (`--name`, `--cores`, `--memory`, `--scsihw virtio-scsi-pci`, `--scsi0 <storage>:<gb>`,
  `--net0 virtio=<mac>,bridge=<bridge>`, `--ide2 <iso>,media=cdrom`, `--boot order=scsi0;ide2`,
  `--onboot 1`), `qm start`, then controller-owned result transport. The empty root disk is not
  bootable, so first boot falls through to the installer ISO; installed guests boot the disk.
- `nctl/src/nctl_core/reconcile/classify.py` — registers `compute_instance_kind_not_creatable` as
  a manual-review diff code.
- `nctl/src/nctl_core/reconcile/reconcilers.py` — create-plan reason is now kind-neutral.

## Design decisions

- **ISO boot, no bootstrap mechanism.** Per Phase 6, no cloud-init, golden template, or OpenTofu
  was adopted merely to complete the path. The existing `template` config field carries the ISO
  volid, validated against fresh `iso` storage-content evidence — no new intent field and no
  generic Proxmox option bag was added.
- **The manual-initial-access gate is reused unchanged.** A created QEMU guest boots the
  installer; OS install, addressing, and SSH enrollment remain the operator-owned manual
  procedure, exactly as for LXC.
- **Explicit kind rejection over incidental rejection.** The historical gap is now a tested
  contract: `virtual_machine` intent with a `vztmpl` volid fails the `iso` template gate and can
  never reach `pct create`.

## Evidence

- `nctl` ordinary suite: `uv run pytest -q` — **1289 passed** (was 1280; new/updated coverage in
  `tests/test_compute_creation.py`, `tests/test_compute_create.py`).
  - New derivation tests prove: container → pinned `lxc` parameters; `virtual_machine` → pinned
    `qemu` parameters without LXC-only keys; `virtual_machine` + `vztmpl` volid fails
    `compute_template_unavailable` instead of creating an LXC; the static-network gate applies to
    containers only.
  - New handler tests prove: `qemu` parameters run `create_qemu.yml`; an unmapped `guest_type`
    stops before any playbook; the QEMU playbook contains only create/start plus local result
    transport and no `pct`/stop/destroy/set/resize/migrate/clone surface.
- Ansible conformance gate: `uv run --project nctl pytest -q
  devtests/test_strategy/test_ansible_conformance.py` — **4 passed**, including a new Tier A test
  running the real `create_qemu.yml` against a disposable `qm` stub and asserting the exact pinned
  argv and result transport.
- Compute conformance gate: `uv run --project nctl pytest -q
  devtests/test_strategy/test_compute_conformance.py` — **1 passed** (no contract change:
  `instance_kind = "virtual_machine"` and its config rules already existed in the shared
  contract).

## Not proven / deferred

- No live QEMU guest has been created. The Phase 6 exit criterion (one concrete approved VM
  reaching fresh compute realization, with repeat reconcile not recreating it) needs a live run:
  a disposable approved VM intent, `nctl reconcile` dry plan, and a separately approved apply
  against Proxmox — Proxmox writes stay behind the explicit approval boundary.
- Post-create observation/linking reuses the existing evaluation path (`qemu` →
  `virtual_machine` kind mapping and QEMU inventory observation already existed); its live
  round-trip for a created VM is part of the same pending live verification.
- Safe mutable differences (vCPU/memory/disk growth, power) for QEMU remain out of scope, one
  operation at a time per Phase 6.
- Automatic guest bootstrap remains out of scope (Phase 7 decides from Phase 5/6 evidence).
