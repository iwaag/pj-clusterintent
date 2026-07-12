# Step 10 Report: Obsolete-Code Removal and Pipeline Verification

## Summary

Completed the repository-wide Step 10 cleanup and static verification. Removed the last
documentation instruction that declared bootstrap groups through
`DesiredNode.expected_spec.ansible_groups`, and removed the unused Nautobot dynamic-inventory
installer playbook, role, and documentation. The generated schema `1.0` production inventory is now
the sole production inventory contract; no compatibility reader, duplicate inventory source, or
legacy setup artifact remains. Added the required one-way data migration that removes retired
placement/platform keys from existing desired-node JSON; migrations remain the only transition
mechanism.

Because this workspace has no Nautobot or target-host execution environment, no live database
migration check, Nautobot Job run, node collection, or end-to-end deployment was attempted. The
equivalent database-free composition and contract checks were run, including a new mixed Linux,
macOS, and declared-HAOS pipeline test.

## Changes

### nauto

- Replaced the stale `README.md` instruction to configure
  `desired_nodes[].expected_spec.ansible_groups` with the current ownership contract: bootstrap uses
  eligible desired nodes and mDNS endpoints, service groups come from active placements plus the
  Ansible-owned deployment-profile map, and actual facts are restricted to the exporter allowlist.

### ansible_agdev

- Deleted `playbooks/setup_nautobot_ansible_inventory.yml` and the complete
  `roles/nautobot_ansible_inventory/` role. Nothing consumes the
  `networktocode.nautobot.inventory` plugin after the dedicated production export workflow.
- Removed the corresponding install/pinning instructions from `README.md`.
- Removed the obsolete `.local/plan_refactor.md`, which described editing the deleted handwritten
  inventory and carrying manually declared host capability fields.
- Removed backward-looking references to the deleted handwritten inventory files from
  `README_ADMIN.md`; the documentation now describes only the generated contracts.

### nintent

- Added migration `0005_remove_retired_expected_spec_keys.py`. It removes `ansible_groups`,
  `host_os`, and `os` from existing `DesiredNode.expected_spec` objects without adding a runtime
  reader or reverse converter.
- Added `MixedPlatformPipelineTests.test_linux_macos_and_declared_haos_compose_together`.
  One composition now verifies three included hosts, correct `linux`/`macos`/`haos` selectors,
  placement-derived `web_server` and `haos_server` membership, and absence of
  `package_manager` on every host.

## Legacy-reference audit

Repository-wide searches found no remaining `ansible_groups` outside the required data migration,
and no legacy production inventory path, old broad inventory example, Nautobot dynamic-inventory
plugin, or installer/role reference in runtime code, fixtures, seeds, or current documentation.

The only remaining `preferred_services` and `service_roles` strings are negative regression-test
inputs/assertions. They do not parse or preserve an old schema: they prove that nodeutils does not
self-report those retired declarations and that the production actual-fact allowlist discards such
input. Database migrations remain the only retained transition mechanism.

## Verification

- nintent: `python3 -m unittest discover -s nautobot_intent_catalog/tests` — 172 tests passed.
- nauto: `python3 -m unittest discover -s tests` — 24 tests passed.
- nodeutils: `python3 -m unittest discover -s tests` — 7 tests passed.
- nodeutils: `uv run ruff check .` — passed.
- Python compile checks passed for every tracked Python file in nintent, nauto, and nodeutils.
- `git diff HEAD --check` passed in nintent, nauto, nodeutils, and ansible_agdev.
- All 26 remaining Ansible playbooks passed `ansible-playbook --syntax-check` using a validation-only
  config that omits the unavailable local Vault password file. Expected unmatched-group warnings
  occurred with the localhost-only validation inventory.
- `playbooks/verify_deployment_profiles_contract.yml` ran successfully: exact canonical JSON bytes,
  SHA-256 digest, and deterministic non-empty audited profile serialization all passed.
- Existing tests re-verified that an absent observed service remains a desired member,
  desired/actual OS mismatch is reported separately, unknown host variables such as
  `package_manager` are rejected, skipped hosts do not leave dangling placement membership, and
  generated output is byte-stable.
- Static review reconfirmed that production installation stages and validates the candidate before
  the atomic `mv`; failures enter `rescue`, delete only the staging file, and leave the previous
  current-schema production inventory unchanged.

## Unavailable live checks

- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run` and application of the
  new data migration.
- Live bootstrap export, nodeutils collection, Nautobot ingest, production export Job, artifact
  download, and target-host Ansible execution.
- A real end-to-end failure injection against an already installed production artifact.

These require the external environment explicitly excluded from this task. No result above claims a
live operational verification.

## Exit Criterion

Met for repository contracts and static verification. Only the new bootstrap schema and production
schema `1.0` remain executable inventory contracts, with migrations as the sole historical
transition mechanism. Live operational confirmation remains an environment-side deployment step.
