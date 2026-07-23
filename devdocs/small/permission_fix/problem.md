# Problem: nodeutils collection fails on Proxmox hosts due to non-root `pvesh` execution

## Symptom

`nctl reconcile aghub` never converges. `nctl drift --host aghub` reports (among others):

- `no_realized_object` (error) — "observed operation is required but no realized device or VM is linked"
- `no_realized_device` (error) — "a supported realized device is required" (field `host_os`)
- `missing_actual_node` (error)

`sources.observed_errors` in the drift output additionally shows:

```
/var/lib/nodeutils/agpc.json: unsupported schema_version 'nodeutils.inventory.v1' (expected 'nodeutils.inventory.v2')
/var/lib/nodeutils/inventory.json: unsupported schema_version 'nodeutils.inventory.v1' (expected 'nodeutils.inventory.v2')
```

This looked at first like a stale nodeutils checkout on `aghub`, but the checkout used by the
failing `aghub` run already implemented schema v2. Its collection fails before output is written.

The two paths in `sources.observed_errors` need separate interpretation: they are files in the
controller's configured `dumps_dir`, and `scan_dumps()` reports errors for every file in that
directory even when drift is filtered to `--host aghub`.

- `agpc.json` was a pre-v2 Ubuntu observation and is unrelated to Proxmox.
- The controller-local `inventory.json` currently identifies `agstudio.local` (macOS), not
  `aghub`; it is a legacy generic-name dump.

Their presence in an `aghub` drift payload is therefore global source-scan noise, not evidence
that those hosts share the `pvesh` failure.

## Root cause

Running `nctl reconcile aghub --yes` triggers the `observe_node` action, which runs
`ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml`. In that run
(`~/.local/state/nctl/events/01KY6X5A2VHBEFXT1T44H3RH0P/ansible/collect.stdout`):

- `Clone or update nodeutils repository` — succeeded (repo updated to HEAD, already v2 code)
- `Sync nodeutils dependencies with uv` — succeeded
- `Run nodeutils inventory collection` — **failed**, rc=2:
  ```
  stderr: "error: failed to run pvesh get /cluster/status"
  ```

`nodeutils` auto-detects Proxmox hosts (`proxmox_inventory.is_proxmox_host()`) and, when detected,
calls `pvesh get /cluster/status` etc. (`nodeutils/proxmox_inventory.py:99`, `run_pvesh`). `pvesh`
talks to Proxmox's cluster filesystem (`pmxcfs`) over a local IPC socket, which requires root
privileges. Reproduced directly on `aghub` via ad-hoc Ansible:

```
# as regular login user (eiji, in the sudo group but not elevated)
$ pvesh get /cluster/status --output-format json
ipcc_send_rec[1] failed: Unknown error -1
ipcc_send_rec[2] failed: Unknown error -1
ipcc_send_rec[3] failed: Unknown error -1
Unable to load access control list: Unknown error -1
RC=255

# as root (become: true, no become_user override)
$ pvesh get /cluster/status --output-format json
[{"id":"node/aghub","ip":"192.168.0.10","level":"","local":1,"name":"aghub","nodeid":0,"online":1,"type":"node"}]
RC=0
```

The playbook's collection task explicitly overrides the become user:

```yaml
- name: Run nodeutils inventory collection
  ansible.builtin.command:
    cmd: "{{ nodeutils_uv_path }} run nodeutils collect {{ nodeutils_collect_args }}"
    chdir: "{{ nodeutils_checkout_dir }}"
  become: true
  become_user: "{{ nodeutils_user }}"   # <- non-root login user, overrides play-level root become
  ...
```

`nodeutils_user` defaults to `ansible_user` (the regular login user), so `become_user` demotes the
task away from root before `pvesh` runs, causing the IPC failure above. Because `nodeutils collect`
exits non-zero before writing any output, `aghub` cannot produce a fresh remote report for nctl to
retrieve, validate, cache, and ingest.

## Why this matters beyond aghub

This is not aghub-specific — any host that nodeutils detects as a Proxmox node will hit the same
failure, since the collection task always runs as `nodeutils_user`, never root.

`agpc` is a regular Ubuntu host, does not satisfy the Proxmox detection checks, and does not call
`pvesh`. Its stale v1 report was produced before the coordinated v2 collector change and is a
separate update/onboarding issue, not evidence of this permission failure.

## Independent workflow gaps found while investigating agpc

The agpc investigation found two reproducibility/usability gaps that can recur independently of
the Proxmox permission defect:

1. `run_nodeutils_collect.yml` defaulted `nodeutils_version` to mutable upstream `HEAD`. A normal
   observation could therefore deploy a collector schema newer than the local nctl reader.
2. `nctl reconcile HOST` planned no observation when current drift was already converged. There
   was no supported way to explicitly refresh nodeutils, its report, and Nautobot actual state.

The current nctl worktree addresses these by:

- resolving the exact `nodeutils` gitlink recorded by the pj-clusterintent superproject and
  passing that full commit SHA to Ansible;
- failing before Ansible rather than falling back to `HEAD` if the pinned version cannot be
  resolved;
- recording the SHA in event/action evidence; and
- adding host-scoped `nctl reconcile HOST --refresh-observation [--yes]`, which forces one
  observation in the first round and then returns to normal convergence planning.

Live agpc verification is recorded in `report1.md`. This does not fix the root-only `pvesh`
execution problem on `aghub`.

## Open design decision for the Proxmox fix

- Running `nodeutils collect` as root writes into `nodeutils_checkout_dir`
  (`/opt/nodeutils`, owned by `nodeutils_user`) and `nodeutils_state_dir`
  (`/var/lib/nodeutils`, mode 0700, owned by `nodeutils_user`). Elevating only the collection task
  to root risks leaving root-owned files (`.venv`, `uv.lock` cache, `inventory.json`) that a later
  non-root `uv sync` or read step can no longer touch. This needs to be worked out before changing
  `become_user` on that task.

There is currently no `devdocs/small/permission_fix/plan.md`; the privilege/ownership design still
needs to be written before changing the Proxmox execution user.
