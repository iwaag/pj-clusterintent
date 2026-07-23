# Permission Fix Step 0 Report: Freeze the Live Baseline

Date: 2026-07-23

## Status

**Complete. No mutation performed.**

This step only records the current state on `aghub` and in Nautobot before any code or
configuration change. Nothing was installed, modified, or deleted.

## Drift and dry-plan baseline

`nctl drift --host aghub --json` (operation not applicable; drift is read-only):

- `severity_summary`: `error=3, warning=1, info=1`
- target `aghub` status: `unknown`
- diffs include `no_realized_device` (field `host_os`), `missing_actual_node`, and
  `no_realized_object` (manual-review, "observed operation is required but no realized device or
  VM is linked")
- `manual_review` also flags `missing_interface_candidate` (warning)

`nctl reconcile aghub --refresh-observation` (dry plan, no `--yes`):

- `operation_id: 01KY7EVDGB1F3WQ8NJ0SQKPS84`
- `state: planned`, `ssh_preflight: ready=[aghub]`
- `plan.json` contains exactly one action:
  ```json
  {
    "action_kind": "observation",
    "id": "observe_node",
    "reconciler_id": "observe_node",
    "mutates": true,
    "evidence": {"forced_refresh": true},
    "claimed_diff_codes": ["missing_actual_node", "no_realized_device"]
  }
  ```
- No writes occurred (plan mode only).

This confirms `observe_node` is actually planned for `aghub`, as required before implementation.

## Aghub IPAM Job review (read-only, no mutation)

Per `report1.md`, two previously queued aghub "Reconcile Desired IPAM Intent" Jobs were drained by
the Nautobot worker restart during the agpc replay. Their logs were inspected via
`/api/extras/job-results/<id>/logs/`:

- `828c1f85-95dc-4aa6-8b3c-e7816a9e7192` (05:42:43Z, ran first): `create_ip_address_applied` —
  created and linked `192.168.0.10/32` (`dns_name=aghub.home.arpa`) to the `aghub` desired
  endpoint `primary`. `created_ip_addresses=1, conflicts=0`.
- `d41d4f2c-d898-4a1a-b345-823712fedd39` (07:13:56Z, ran second): `conflict` — attempted to create
  the same `192.168.0.10/32` again and hit
  `IntegrityError: duplicate key value violates unique constraint
  "ipam_ipaddress_parent_id_host_89330d7e_uniq"`. `conflicts=1, created_ip_addresses=0`.

Current IP state (`GET /api/ipam/ip-addresses/?address=192.168.0.10/32`) shows exactly one record
(`id=e27d9f9e-c7c0-4e8e-856f-89599ee76980`), `dns_name=aghub.home.arpa`, status active, no
duplicate. The two queued Jobs were sequential replays of the same desired-IPAM reconcile against
a state that had already converged between the two runs — the second Job's "conflict" is expected
idempotent behavior (the IP already existed with the same fields), not a live duplicate/ownership
problem. No IPAM mutation was needed or performed in this step.

## Aghub host facts (read-only ad-hoc, no `become` unless noted)

- `ansible_user` / `nodeutils_user`: `eiji` (`uid=1000`, groups `eiji,sudo,users`); confirmed via
  `getent passwd eiji` and inventory `ansible_user: "{{ default_user }}"`.
- Absolute paths: `pvesh=/usr/bin/pvesh`, `sudo=/usr/bin/sudo`,
  `python3 -> /usr/bin/python3.13`, `visudo=/usr/sbin/visudo`, `uv=/usr/local/bin/uv`.
- Ownership/mode:
  - `/usr/bin/pvesh`: `root:root 755`
  - `/usr/bin/python3.13`: `root:root 755`
  - `/usr/bin`, `/usr`, `/`: `root:root 755` (no group/world-writable ancestor)
  - `/usr/sbin/visudo`: `root:root 755`
  - `/usr/local/libexec` (target parent for the future helper): already exists, `root:root 755`
  - `/etc/sudoers.d`: contains only pre-existing `README` and `zfs` fragments (`root:root`,
    mode `0440`/`r--r-----`); no `nodeutils-pvesh` fragment yet.
  - `/opt/nodeutils`: `eiji:root 755`, checkout present at pinned commit
    `e7b91860397abddee07801b438914e59e734ce57` (matches the superproject gitlink recorded by
    `git ls-tree HEAD nodeutils`).
  - `/var/lib/nodeutils`: `eiji:root 700`; contains only `nctl-probe-config.yaml`
    (`eiji:root 0600`). **No `inventory.json` exists yet** — confirms collection has never
    completed successfully on `aghub`.
- `sudo -n -l` as `eiji`: `sudo: a password is required` (no passwordless grants of any kind
  exist yet).
- Proxmox version: `pve-manager/9.1.1/42db4a6cf33dac83` (`pveversion` succeeds as non-root).

## Positive/negative `pvesh` baseline (reconfirmed live)

```text
# as eiji (non-root, no become)
$ pvesh get /cluster/status --output-format json
ipcc_send_rec[1] failed: Unknown error -1
...
Unable to load access control list: Unknown error -1
RC=255

# as root (become: true, no become_user override)
$ pvesh get /cluster/status --output-format json
[{"id":"node/aghub","ip":"192.168.0.10","level":"","local":1,"name":"aghub","nodeid":0,"online":1,"type":"node"}]
RC=0
```

This matches `problem.md` exactly: the failure is reproduced, and root execution succeeds.

## Secrets handling

No SSH private key material, vault passwords, or raw Proxmox API responses beyond the single
`/cluster/status` sample already quoted in `problem.md` were recorded. The Nautobot token was read
only in-memory from `.local/secrets` to authenticate `curl` calls and is not reproduced above.

## Conclusion

The baseline matches the plan's assumptions with no surprises:

- `observe_node` is confirmed planned for `aghub`.
- The two previously replayed aghub IPAM Jobs are explained and require no remediation — current
  IP ownership is correct and singular.
- `/usr/local/libexec` already exists as `root:root 0755`, so Step 1 can install the helper there
  without first creating the directory tree.
- No root-owned files exist yet under `/opt/nodeutils` or `/var/lib/nodeutils`.
- `nodeutils_user` (`eiji`) has no passwordless sudo of any kind, confirming the sudoers fragment
  in Step 1 will be the first and only grant.

Proceeding to Step 1 (implement and test the privileged helper) is unblocked.
