# Phase 1.5 Report — Step 6 (guidance, documentation, final verification)

Date: 2026-07-16. Implements [p1ex1/plan.md](plan.md) Step 6 and closes the Phase 1.5
implementation plan. This is the fourth suggested commit unit: nctl behavior/tests and nctl/parent
documentation, plus the parent submodule-pointer/report updates when the preceding submodule
commits are recorded.

## What changed

- Replaced `nctl apply dnsmasq`'s stale missing-inventory instruction
  (`export_nintent_production.yml`, removed in Phase 2) with the deterministic command
  `nctl render production --out <inventory-directory>`.
- Added a focused regression test asserting both the new nctl command and the absence of the old
  playbook name in the `ansible_inventory_missing` error.
- Documented `nctl render hosts-intent` in `nctl/README.md`, including stdout behavior, validated
  atomic `--out` behavior, both artifact names, the JSON envelope schema, and its distinction from
  the production inventory.
- Added the root-relative `render hosts-intent --out ansible_agdev/inventories/generated` command
  to the parent `README.md` and clarified that both bootstrap and production inventory composition
  belong to nctl.

The roadmap originally called this command `nctl render inventory`. Phase 2 subsequently added
`render production`, also an inventory renderer, so this phase deliberately uses
`render hosts-intent`: it matches `hosts_intent.yml` and keeps bootstrap vs production explicit.

`apply dnsmasq` does not automatically regenerate its production inventory. The apply command
must use a detailed inventory containing the `dnsmasq_server` actuation group, while
`render hosts-intent` intentionally produces only the minimal `ssh_hosts` bootstrap group.
Keeping the missing prerequisite explicit as one deterministic nctl command avoids silently
recomposing a separate artifact during an apply operation and satisfies the roadmap requirement
that users are no longer pointed at an Ansible export playbook.

## Verification

- `cd nctl && uv run pytest -q` — **285 passed**.
- `nctl --help` lists `render`; `nctl render --help` lists `dnsmasq`, `production`, and
  `hosts-intent` with distinct descriptions.
- nctl source and documentation contain no `export_nintent_production.yml` reference. The only
  test occurrence is a negative assertion preventing its return.
- Rechecked deletion invariants:
  - no `ExportAnsibleHostsIntent` class/reference in active nintent package code;
  - no nintent `ansible_inventory.py` or original test file;
  - no Ansible hosts-intent export playbook;
  - no shared `nautobot_run_job.yml` / `nautobot_download_file.yml` tasks or references.
- `git diff --check` — passed.

Live/bootstrap and deployment verification is recorded in [report4.md](report4.md) and
[report5.md](report5.md): rebuilt nintent 0.8.0 is healthy, the retired Job is not installed,
`nctl status` is green, and live `make bootstrap-inventory` produced a schema 3.0 inventory with
5 hosts that passed `ansible-inventory --list`.

## Phase 1.5 exit criteria

- [x] Live parity with the final Job export: inventory body and JSON hosts/skipped/summary matched
  ([report1-3.md](report1-3.md)).
- [x] `render hosts-intent --out` validates a staged inventory and preserves the previous file on
  failure (unit tests plus live validation).
- [x] The nintent export Job, renderer, and old tests are deleted; nintent's 80 tests pass; rebuilt
  Nautobot reports the historical Job row as `installed=false` and offers no installed Job.
- [x] The Ansible export playbook and the last shared Job/File Proxy tasks are deleted; the
  Makefile pipeline uses nctl for bootstrap rendering.
- [x] `apply dnsmasq` points at `nctl render production --out`, not a deleted playbook.
- [x] The nctl suite passes, including ported renderer vocabulary, CLI/write behavior, atomic
  failure preservation, and the new missing-inventory guidance test.

Phase 1.5 is functionally complete. Generated operational artifacts remain ignored and no
generated inventory or parity artifact was added under `devdocs`.
