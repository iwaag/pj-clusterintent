# vm/ex1 — iso storage evidence + first live QEMU creation

Goal: make the already-implemented QEMU creation path (`devdocs/vision/vm/report.md`,
status "implemented, not deployed") actually usable live, by closing the one structural
gap — **iso storage-content evidence is never collected** — and then creating the first
real VM (`agautolab1` on aghub, the autodev episode's Step 5 job runner) through
`nctl reconcile`.

This is an experimental cluster in a breaking-change phase: no backward compatibility,
no dual readers/writers, rename freely. Implementer discretion applies everywhere not
explicitly pinned below. The only hard rules:

1. Proxmox writes go through the usual dry plan → separately approved apply.
2. Secrets never enter tracked files (`.local/` per devpolicy).

## Findings from planning (verified 2026-08-07, save yourself the re-derivation)

- The QEMU create gate requires a **complete `iso` storage-content scope containing the
  ISO volid** (`nctl/src/nctl_core/drift/compute_creation.py` —
  `TEMPLATE_CONTENT_TYPES = {"lxc": "vztmpl", "qemu": "iso"}`). Without iso evidence it
  always fails `compute_template_unavailable`.
- Exactly **two chokepoints hardcode vztmpl**; everything else is already
  content_type-generic:
  1. `nodeutils/proxmox_inventory.py` ~lines 700-760: the collection loop skips storages
     without `vztmpl` in their content types, fetches
     `/nodes/<node>/storage/<storage>/content` once, and keeps only
     `content == "vztmpl"` entries (`LIMIT_VZTMPL_ITEMS_PER_STORAGE = 2048`).
  2. `nauto/jobs/proxmox_ingest.py` `_validate_storage_scope`: rejects any scope with
     `content_type != "vztmpl"` as `invalid_content_type`.
- Already generic — **no change needed**: nauto's merge key
  (`proxmox_upsert.storage_content_key` = `node:storage:content_type`, so iso scopes
  coexist with vztmpl per Section 5.3/5.4), nctl's read model
  (`sources/actual.py` `ProxmoxStorageScope.content_type: str`), and the kind-aware
  create derivation/playbook dispatch (tested; `create_qemu.yml` exists).
- The scope row shape for iso is identical to vztmpl (same keys, different
  `content_type`/`content` values), so `PROXMOX_SCHEMA_VERSION` can stay as is.
- aghub current evidence: only `local / vztmpl / complete`. Observed VMIDs 100-108
  (free: 109+), bridge `vmbr0`, storage `local-lvm` for rootfs. The pvesh fixture in
  `nodeutils/tests/test_pvesh_helper_integration.py` already models
  `content: "iso,vztmpl,backup"` on `local`, matching real Proxmox defaults — `local`
  accepts iso uploads at `/var/lib/vz/template/iso/`.
- QEMU create params need a **unique primary desired_endpoint with a MAC**
  (`qm create --net0 virtio=<mac>,...`); the static-IP/gateway gate is container-only.
  IP/MAC conflict checks run against observed actuals, so pick unused values.
- agdnsmasq (LXC, vmid 108) is the working desired-state example to copy from:
  `nctl desired export` shows its node/endpoint/compute_instance triple.

## Step 1 — nodeutils: collect iso scopes alongside vztmpl

Generalize the storage-content loop to a closed set of content types
(`{"vztmpl", "iso"}`): for each storage advertising a wanted type, emit one scope per
(storage, content_type) pair. Hints:

- The content listing is already fetched once per storage — fetch once, partition by
  `entry["content"]`, don't call pvesh per type.
- Rename `LIMIT_VZTMPL_ITEMS_PER_STORAGE` to something type-neutral; keep the same
  bound and the same truncation → `partial` + sink-error behavior per scope.
- Keep failure isolation per scope (one failed storage listing must not erase the
  other scopes), mirroring the existing partial-scope handling.
- Tests: extend `nodeutils/tests/test_proxmox_inventory.py` with an iso scope case
  (items sorted by volid, truncation, and a mixed-content storage yielding two
  scopes). Gate: `cd nodeutils && uv run pytest -q`.

## Step 2 — nauto: accept iso scopes at ingest

Relax `_validate_storage_scope` from equality-with-vztmpl to the same closed set.
Everything downstream (merge, custom-field ledger, freshness) already keys on
content_type. Tests: one accepted-iso and one still-rejected-unknown-type case in
nauto's suite. Gate: `cd nauto && python3 -m unittest discover -s tests`.

Since this crosses nodeutils → nauto → Nautobot, run the runtime gate once at the end
per README_DEV's matrix: `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb`.

## Step 3 — live evidence: put an ISO on aghub and re-observe

- Upload an Ubuntu Server ISO (24.04 live-server amd64) to aghub's `local` storage.
  Simplest: download on this Mac, `scp` to `root@aghub.local` (ssh via
  `~/.ssh/ansible_key` is allowed with user confirmation) into
  `/var/lib/vz/template/iso/`, or `pvesh create /nodes/aghub/storage/local/upload ...`.
  Implementer's choice; ~3 GB, verify the sha256 from releases.ubuntu.com.
- Deploy the updated nodeutils and refresh:
  `uv run --project nctl nctl reconcile aghub --refresh-observation --yes`
  (observation deploys the nodeutils commit pinned by the superproject — commit the
  submodule bump first).
- Acceptance: aghub's cluster evidence now shows a complete
  `local / iso` scope listing the uploaded volid (visible in `/var/lib/nodeutils/…`
  dump and in `nctl drift --json`).

## Step 4 — desired state + reconcile create (the Phase 6 live exit criterion)

Add one batch to `.local/desired-state.yaml` (preview, then `--yes`), copying the
agdnsmasq triple with these deltas:

```yaml
# desired_node: slug agautolab1, node_type service_host, lifecycle active,
#   accepted_actual_types [virtual_machine]
# desired_endpoint (primary): mac_address bc:24:11:xx:xx:xx (unused), ip_policy
#   dhcp_reserved with a free pool IP (e.g. 192.168.0.130), mdns agautolab1.local
# desired_compute_instance: platform aghub-pve, instance_kind virtual_machine,
#   vmid 109, template local:iso/<uploaded>.iso, storage local-lvm, bridge vmbr0,
#   vcpus/memory_mb/root_disk_gb ~ 4 / 8192 / 64 (implementer's judgment; the job
#   runner runs claude CLI + node + uv, not containers) — no `unprivileged` key
```

Then `nctl reconcile agautolab1` dry → confirm the single pinned
`create_compute_instance` action with `guest_type: qemu` → approved
`nctl reconcile agautolab1 --yes`. Acceptance per the vm report: created+started
result, post-create observation links the VirtualMachine, and a repeat reconcile
plans **no second create**.

## Step 5 — handoff (autodev episode boundary)

The VM boots the installer ISO; OS install, SSH keys, and Claude login are the user's
manual work by design (autodev plan Step 5 decision). Stop after the repeat-reconcile
check and report.

Reporting: `ex1/report.md` here, plus — because this is clusterintent implementation
work for the autodev episode — `devdocs/vision/autolab/report.md` per that episode's
reporting requirement. If any workflow pain repeats, file it through Easier Next Time
as usual.

Out of scope: cloud-init/golden-template bootstrap (Phase 7 decides), QEMU mutable
diffs (vCPU/memory growth), autolab installation on the VM (autodev Step 5 resumes
after the user's manual handoff).
