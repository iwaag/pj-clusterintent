# Phase 1.5 Report — Step 5 (remove Ansible Job/file-proxy plumbing)

Date: 2026-07-16. Implements [p1ex1/plan.md](plan.md) Step 5. This is the third commit unit
in the plan's suggested order and touches only the `ansible_agdev` submodule.

## What changed

- Deleted `playbooks/nautobot/export_nintent_hosts_intent.yml`. nctl now fetches desired state,
  renders the bootstrap inventory, validates it, and writes it directly.
- Deleted `playbooks/tasks/nautobot_run_job.yml` and
  `playbooks/tasks/nautobot_download_file.yml`. A repository-wide pre-deletion reference check
  confirmed that the removed export playbook was their last consumer.
- Changed `Makefile`'s `bootstrap-inventory` target to:
  `$(NCTL) render hosts-intent --config ../nctl.toml --out inventories/generated`.
  The pipeline order remains bootstrap render → collect/ingest → production render.
- Updated `README.md`, `README_ADMIN.md`, `ansible.cfg`, and
  `docs/production_inventory_contract.md` to describe nctl ownership, schema 3.0, direct
  validated/atomic writes, and the absence of a Nautobot export Job/File Proxy path.

The inline ingest-Job orchestration in `collect_nodeutils_and_ingest_nautobot.yml` is unchanged;
it belongs to Phase 4 as specified by the plan.

## Verification

- A repository-wide search found no remaining references in ansible_agdev to
  `export_nintent_hosts_intent`, `nautobot_run_job`, `nautobot_download_file`, or
  `Export Ansible Hosts Intent`.
- `make -n pipeline` expands to exactly:
  1. `nctl render hosts-intent --config ../nctl.toml --out inventories/generated`
  2. the existing collect/ingest playbook with explicit `hosts_intent.yml` inventory
  3. `nctl render production --config ../nctl.toml --out inventories/generated`
- Ran `NAUTOBOT_TOKEN=... make bootstrap-inventory` against the rebuilt live Nautobot:
  successful summary `total_nodes: 5`, `exported_hosts: 5`, `skipped_nodes: 0`, group
  `ssh_hosts`.
- Independently ran
  `ansible-inventory -i inventories/generated/hosts_intent.yml --list` — passed.
- Parsed `hosts-intent-export.json`: schema `3.0`, 5 exported hosts, 0 skipped nodes.
- `git diff --check` — passed.

Generated inventory/export artifacts remain ignored operational output and were not added to
Git.

## Commit boundary / next step

Step 5 is complete as the intended standalone ansible_agdev commit unit. Step 6 remains: fix the
stale `apply dnsmasq` missing-inventory guidance, update nctl/parent command documentation, and
finish the Phase 1.5 report/exit-criteria verification.
