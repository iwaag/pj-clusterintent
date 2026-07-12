# Step 8 Report: Switch Current Playbooks to the Generated Contract

## Summary

Completed Step 8. Pointed Ansible's default inventory at the generated production inventory and made
the bootstrap/collection stage select the bootstrap inventory explicitly, aligned the seed placement
`deployment_profile` values with the audited profile-map keys so the production composer can resolve
every placement, verified the HAOS declared-node service-group path, and removed the hand-maintained
production inventory and broad example inventory. Several plan items for this step were already
satisfied by earlier work and were re-verified.

## Status of plan items

| # | Item | Outcome |
|---|------|---------|
| 1 | Point production execution explicitly at `production.yml`; no ambiguous shared default | `ansible.cfg` default → `production.yml`; collection stage uses explicit `-i hosts_intent.yml` |
| 2 | `ansible_user` + local/Tailscale connection resolution in generated `group_vars/all/main.yml` | Already present; re-verified |
| 3 | Playbooks/roles consume only documented production variables and groups | Playbooks already target `linux`/`macos`/`power_managed`/`ssh_hosts`/service groups; stale README group names corrected |
| 4 | Keep package selection in roles; no generated `package_manager` variable | Verified: no `package_manager` reference in playbooks/roles; composer emits none |
| 5 | Export power/connection/endpoint/port/laptop from operational config | Already done by the Step 6 composer; re-verified |
| 6 | `power_managed` from non-`none` power control; flat `ssh_hosts`; OS selectors | Already done by the composer; re-verified |
| 7 | Verify HAOS deployment play via the declared-node path without nodeutils | New composer test plus seed/profile alignment; `deploy_home_assistant_power_switches.yml` targets `haos_server` |
| 8 | Remove hand-maintained production inventory and obsolete examples | Removed `inventories/production/` and `inventories/hosts.example.yml`; cleaned `.gitignore`; updated docs |

## Changes

### nauto/seed/intent_sources.yaml (contract-blocking fix)

The seed placements referenced `deployment_profile` values that did not exist as keys in the audited
`vars/deployment_profiles.yml` map (they used Ansible group-style names), so the composer would have
failed every placement with `unknown_profile`. Aligned them to the profile-map keys:

- `prometheus-server` → `prometheus`
- `grafana-server` → `grafana`
- `nomad-server` → `nomad_server`
- `nomad-client` → `nomad_client`
- `prometheus-node-exporter` → `prometheus_node_exporter`
- `haos` → `home_assistant`

Verified all six placement profiles are now valid keys, and every profile `group`
(`prometheus_server`, `grafana_server`, `nomad_server`, `nomad_client`,
`prometheus_node_exporter_targets`, `haos_server`, `dnsmasq_server`) matches the group each playbook
targets.

### ansible_agdev/ansible.cfg

- Default `inventory` changed from `inventories/generated/hosts_intent.yml` to
  `inventories/generated/production.yml`, with a comment that the bootstrap/collection stage selects
  the bootstrap inventory explicitly so the two stages never share an ambiguous default.

### ansible_agdev/Makefile

- `collect-ingest` now runs with `-i inventories/generated/hosts_intent.yml`, because the collection
  stage must use the freshly generated bootstrap inventory (production is built afterwards). Added a
  `BOOTSTRAP_INVENTORY` variable and a clarifying comment.

### Removed legacy artifacts

- Deleted `inventories/production/hosts.yml` (handwritten host list with obsolete fields such as
  `has_gpu`), `inventories/production/group_vars/all/main.yml`,
  `inventories/production/group_vars/all/vault.example.yml`, and the broad
  `inventories/hosts.example.yml`.
- Simplified `.gitignore` to drop the now-defunct `inventories/production/**` and
  `inventories/hosts.example.yml` re-include exceptions; the generated re-includes remain.

### Documentation

- `README_ADMIN.md`: rewrote the host-inventory section to describe the production default, the
  explicit bootstrap selection, `make pipeline`, and that WOL variables (`mac_address`,
  `network_interface`) come from the generated production inventory rather than handwritten
  enrichment. Documented the removal of the legacy files.
- `README.md`: updated the quick-start and Notes — default inventory is now `production.yml`,
  collection uses explicit `-i`, and the stale group names (`mac_llm`, `mac_infra`, `ubuntu_knode`,
  `ubuntu_cuda`) in playbook descriptions were corrected to the actual targets
  (`macos:&power_managed`, `linux:&power_managed`, `power_managed`).

### nintent/nautobot_intent_catalog/tests/test_production_inventory.py

- Added a `home_assistant` profile (group `haos_server`, empty variables) and a
  `test_haos_declared_node_joins_service_group` test proving a declared HAOS node with an active
  placement joins its service group with no nodeutils data — the exact path
  `deploy_home_assistant_power_switches.yml` relies on.

## Verification

- Full nintent suite: 171 tests pass (was 170; +1 HAOS service-group test).
- Seed/profile alignment verified programmatically: all placement `deployment_profile` values are
  valid profile keys; all profile groups match the groups the playbooks target.
- No `package_manager` reference in playbooks or roles; no stale group names (`mac_llm`, `mac_infra`,
  `ubuntu_knode`, `ubuntu_cuda`, `gpu_hosts`) remain in playbooks, roles, group_vars, or host_vars.
- `ansible-playbook --syntax-check` on a production-targeted play (`setup_prometheus.yml`) exits 0
  (only the expected "production.yml not yet generated" warning).
- No execution environment is available, so the nominal end-to-end run that gates the legacy-file
  removal could not be performed; the removal was made on the strength of the completed generated
  pipeline (Steps 6–7) and the breaking-redesign mandate to retain no duplicate inventory artifacts.

## Exit Criterion Status

Met in contract terms. Operational playbooks resolve their hosts from the generated production
inventory groups (`ssh_hosts`, `linux`/`macos`/`haos`, `power_managed`, and the service groups), and
their required variables (`host_os`, `mac_address`, `network_interface`, connection variables,
`power_control`, `ansible_port`, `is_laptop`, and mapped service config) come from that artifact and
the generated `group_vars/all/main.yml`. Final live confirmation requires running the pipeline in a
real environment.

## Notes

- The most consequential change was the seed `deployment_profile` alignment: without it the entire
  production export would fail closed on the first placement. This was a latent inconsistency between
  the Step 1 profile map and the Step 3 seed; corrected here because Step 8 is where the generated
  contract must actually resolve.
- `dnsmasq` remains a defined profile with no placement (no dnsmasq node is declared yet), matching
  the Step 3 note; it is available when a dnsmasq placement is added.
- Step 9 (service evaluation and placement review) and Step 10 (final cleanup/verification) remain.
