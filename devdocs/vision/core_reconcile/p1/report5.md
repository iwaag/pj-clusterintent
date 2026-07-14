# Phase 1 Report — Step 5 (deploy-only dnsmasq playbook)

Date: 2026-07-15. Implements [p1/plan.md](plan.md) Step 5. Continues from
[report4.md](report4.md), which removed the old nintent export Job.

## What changed

- Deleted `playbooks/nautobot/deploy_nintent_dnsmasq_records.yml`, including the entire
  localhost export play: Nautobot credentials, Job lookup/run/polling, File Proxy lookup and
  download, temporary staging, and the schema `3.0` assertion.
- Added `playbooks/dnsmasq/deploy_dnsmasq_records.yml` as a deploy-only playbook targeting
  `dnsmasq_server`.
  - Requires `dnsmasq_records_src` to be an absolute controller-side path.
  - Fails before gathering target facts if the variable is missing, relative, absent, or not a
    regular file.
  - Retains the Linux-only assertion, `/etc/dnsmasq.d` creation, destination
    `/etc/dnsmasq.d/nintent-records.conf`, mode/ownership, `dnsmasq --test --conf-file=%s`
    validation, and restart handler.
  - Does not read Nautobot or interpret an export schema; rendering is now nctl's responsibility.
- Updated `README.md` and `README_DEV.md` to show the new path and required variable and to remove
  the retired Job/token/File Proxy instructions.

## Verification

- `ansible-playbook -i inventories/generated/hosts_intent.yml
  playbooks/dnsmasq/deploy_dnsmasq_records.yml --syntax-check` — passed.
- `git diff --check` — passed.
- Repository search under `ansible_agdev` found no remaining old playbook path,
  `Export dnsmasq Records`, `nintent_dnsmasq_*`, or schema `3.0` documentation references.
- Executed the playbook in check mode against a temporary localhost-only `dnsmasq_server`
  inventory to exercise its controller-side guards:
  - missing `dnsmasq_records_src` — failed at the required-path assertion (exit 2);
  - relative `dnsmasq_records_src=relative.conf` — failed at the absolute-path assertion (exit 2);
  - absent `/tmp/does-not-exist.conf` — failed at the regular-file assertion (exit 2).
  In every case no target facts were gathered and no target mutation task ran.

## Inventory discrepancy discovered

The current `inventories/generated/hosts_intent.yml` contains only the `ssh_hosts` group; it does
not contain the `dnsmasq_server` group assumed by the Phase 1 plan. The production inventory file
is also currently absent. Therefore the syntax check reports a harmless "Could not match supplied
host pattern: dnsmasq_server" warning, and an end-to-end deploy cannot presently select a target.

This is important for Step 6: merely checking that `hosts_intent.yml` exists is insufficient.
`nctl apply dnsmasq` must either validate that its configured inventory resolves a non-empty
`dnsmasq_server` group and give a pointed error, or the inventory source must be corrected before
the end-to-end exit criterion can pass. This report does not expand Step 5 into the Phase 1.5
inventory migration.

## Commit boundary

This is the third suggested Phase 1 commit: **ansible_agdev: deploy-only dnsmasq playbook**. It is
intentionally stopped before Step 6, which changes the separate `nctl` submodule and introduces
operation events and subprocess orchestration.

Next: Step 6 — implement `nctl apply dnsmasq`, including explicit validation that the configured
inventory actually provides at least one `dnsmasq_server` target.

