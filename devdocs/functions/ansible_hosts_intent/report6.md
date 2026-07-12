# hosts_intent.yml implementation report: step 6

## Scope Completed

Implemented Step 6 from `plan.md`.

Completed in `nauto`:

- Added the default nintent loader input file:
  - `seed/intent_sources.yaml`

No Nautobot import/export job was executed in this pass.

## Files Changed

`nauto`:

- `seed/intent_sources.yaml`

## Added Intent Data

The new file defines name-reserved DesiredNodes and primary mDNS endpoints for
SSH/bootstrap collection.

Included nodes:

- `agmbp2019`
- `agmbp2018`
- `agpc`
- `agstudio`
- `agbach`
- `agprometheus`
- `aggrafana`
- `agnomad`

Each node has:

- `node_type: device`
- `accepted_actual_types: [device]`
- `lifecycle: planned`
- explicit `expected_spec.host_os` when known
- optional `expected_spec.ansible_groups`

Each node has one primary endpoint:

- `endpoint_type: primary`
- `ip_policy: external`
- explicit `mdns_name: <node>.local`

## Group Mapping

Configured `expected_spec.ansible_groups`:

- `agmbp2019`: `prometheus_node_exporter_targets`
- `agmbp2018`: `prometheus_node_exporter_targets`
- `agpc`: `gpu_hosts`, `nomad_client`, `prometheus_node_exporter_targets`
- `agstudio`: `nomad_client`
- `agprometheus`: `prometheus_server`
- `aggrafana`: `grafana_server`
- `agnomad`: `nomad_server`

No `linux` or `macos` inventory groups were added. OS is represented only as
`expected_spec.host_os`.

## Deliberate Omissions

The file does not carry over detailed handwritten inventory facts:

- no IP addresses
- no MAC addresses
- no GPU facts
- no laptop/power management facts
- no Tailscale addresses
- no interface names

Those belong to nodeutils collection and nauto ingest, not to the mDNS bootstrap
intent.

`aghaos` was not included because the current step is for SSH/nodeutils bootstrap
targets. HAOS handling can be modeled separately if needed.

## Verification

No runtime verification was performed in this pass, per instruction. The next
environment-backed step should import this YAML through nintent's `Import Intent
Sources` Job, then export `hosts_intent.yml`.

## Next Steps

In a Nautobot-capable environment:

1. Run nintent `Import Intent Sources`.
2. Run nintent `Export Ansible Hosts Intent`.
3. Run `ansible_agdev/playbooks/export_nintent_hosts_intent.yml`.
4. Inspect generated `ansible_agdev/inventories/generated/hosts_intent.yml`.
