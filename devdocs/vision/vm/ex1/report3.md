# ex1 Step 3 report — live evidence: ISO on aghub + re-observation

Status: complete

## Deployment of Steps 1–2

- Pushed `nodeutils` `ae26207` and `nauto` `60ce8a2` to GitHub `main` (user
  approved Claude pushing with local credentials).
- Re-synced Nautobot's `main` Git Repository (nauto Jobs) via the REST sync
  endpoint; job result `SUCCESS`, `current_head` now `60ce8a2` — the ingest
  Job accepting iso scopes is live.
- The superproject pins nodeutils `ae26207` (committed in Step 1), so
  `--refresh-observation` deploys the iso-aware collector.

## ISO upload

- Downloaded `ubuntu-24.04.4-live-server-amd64.iso` (3.2 GB) from
  releases.ubuntu.com (24.04.4 is the current 24.04 live-server point release
  per `SHA256SUMS`); local sha256 verified:
  `e907d92eeec9df64163a7e454cbc8d7755e8ddc7ed42f99dbc80c40f1a138433` — OK.
  Kept under `.local/iso/` (ignored).
- Direct `ssh root@aghub.local` with `ansible_key` was rejected
  (`Permission denied (publickey)`) — root login is not enabled for that key.
  Used the approved Ansible path instead (`ansible.cfg` supplies key + vault
  user, `-b` for privilege escalation): `ansible aghub -m copy` into
  `/var/lib/vz/template/iso/ubuntu-24.04.4-live-server-amd64.iso`
  (root:root 0644).
- Remote sha256 re-verified on aghub: matches the published checksum.
- Pre-existing on `local`: `ubuntu-22.04.5-live-server-amd64.iso` (left as is).

## Re-observation

```
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
operation_id: 01KZDCVGYSDDQPK4KWSSTKT668
state: converged
ssh_preflight: ready=[aghub]
round 0: [ok] observe_node, [ok] regenerate_production_inventory
ok: True
```

## Acceptance

Nautobot cluster `aghub-proxmox` `proxmox_storage_content` now holds **both**
scopes, each `state: complete`, `evidence_observed_at: 2026-08-07T05:59:27Z`:

- `aghub:local:iso` — items include
  `local:iso/ubuntu-24.04.4-live-server-amd64.iso` (3405469696 bytes) and the
  pre-existing 22.04.5 ISO.
- `aghub:local:vztmpl` — the two vztmpl templates as before (iso and vztmpl
  scopes coexist under the `node:storage:content_type` merge key, as planned).

The QEMU create gate's required evidence (complete iso scope containing the
ISO volid) is now present.
