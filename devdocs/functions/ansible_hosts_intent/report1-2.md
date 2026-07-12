# hosts_intent.yml implementation report: steps 1-2

## Scope Completed

Implemented Step 1 and Step 2 from `plan.md`.

Completed in `nintent`:

- Added pure export helper:
  - `nautobot_intent_catalog/ansible_inventory.py`
- Added unit tests:
  - `nautobot_intent_catalog/tests/test_ansible_inventory.py`
- Added Nautobot Job registration:
  - `Export Ansible Hosts Intent`
  - Emits `hosts_intent.yml`
  - Emits `hosts-intent-export.json`

No `ansible_agdev` or `nauto` files were changed in this pass.

## Implemented Behavior

The new export helper builds a minimal bootstrap inventory from DesiredNode-like
objects.

Current export rules:

- Exports only `planned`, `approved`, and `active` nodes.
- Exports only `device` and `virtual_machine` node types.
- Does not require `DesiredEndpoint.endpoint_type == "mdns"`.
- Selects an mDNS endpoint per node using:
  1. `expected_spec.ansible_mdns_endpoint`
  2. primary endpoint with `mdns_name`
  3. management endpoint with `mdns_name`
  4. deterministic fallback to any endpoint with `mdns_name`
- Emits a flat `ssh_hosts` group.
- Emits `expected_spec.ansible_groups` as additional groups.
- Copies `expected_spec.host_os` or `expected_spec.os` into host vars only when
  explicitly set.
- Skips nodes without mDNS and records deterministic skip reasons.
- Does not emit legacy `linux` or `macos` groups.
- Does not use handwritten `hosts.yml`.

Example generated inventory shape:

```yaml
all:
  children:
    ssh_hosts:
      hosts:
        agnomad:
          mdns_hostname: agnomad.local
          nintent_inventory_stage: reserved_name
          nintent_desired_node: ag Nomad
          nintent_desired_node_slug: agnomad
          nintent_desired_node_id: node-agnomad
          nintent_desired_endpoint: primary
          nintent_desired_endpoint_id: endpoint-primary
          name_reserved_only: true
          host_os: linux
    nomad_server:
      hosts:
        agnomad: {}
```

## Files Changed

`nintent`:

- `nautobot_intent_catalog/ansible_inventory.py`
- `nautobot_intent_catalog/tests/test_ansible_inventory.py`
- `nautobot_intent_catalog/jobs.py`

## Verification

`pytest` is not installed in the current `uv` environment, so verification used
the repository's existing `unittest` style.

Commands run:

```bash
cd /home/eiji/agdev/temp2/nintent
uv run python -m unittest nautobot_intent_catalog.tests.test_ansible_inventory
uv run python -m unittest nautobot_intent_catalog.tests.test_dnsmasq
uv run python -m unittest discover
```

Results:

- `test_ansible_inventory`: 11 tests passed.
- `test_dnsmasq`: 12 tests passed.
- Full unittest discovery: 116 tests passed.

## Notes

- Group names from `expected_spec.ansible_groups` are normalized by replacing
  non-alphanumeric/underscore characters with `_`. For example,
  `nomad-server` becomes `nomad_server`.
- Groups that cannot be normalized into a conservative Ansible-safe identifier
  are skipped and reported as `invalid_ansible_group`.
- Inventory hostnames are preserved from `expected_spec.ansible_host_name` or
  `DesiredNode.slug`, but hostnames containing whitespace or `:` are skipped as
  invalid.
- The new Nautobot Job has not been manually exercised against a running
  Nautobot instance in this pass.

## Next Steps

Recommended next implementation chunk:

1. Add `ansible_agdev/inventories/generated/` and generated inventory group vars.
2. Add `playbooks/export_nintent_hosts_intent.yml`.
3. Update bootstrap collection playbooks from `linux:macos` defaults to
   `ssh_hosts`.
4. Run `ansible-inventory` validation once a real `hosts_intent.yml` is
   downloaded or test-generated.
