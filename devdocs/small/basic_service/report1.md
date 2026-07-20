# Step 1 report — hosts-intent: connect via mDNS

## Change

- `nctl/src/nctl_core/hosts_intent.py::_host_vars`: added `ansible_host: <endpoint.mdns_name>`
  alongside the existing `mdns_hostname` var. `mdns_hostname` is kept unchanged (production's
  `resolve_connection_variables` and humans still read it).

## Why this is enough

`_host_vars` is only ever attached to `ssh_hosts` members (`_inventory` in the same file
special-cases `ssh_hosts` to carry host_vars; every other group gets empty host objects), so the
new `ansible_host` var lands exactly where scenario 1 step 3 needs it — Ansible resolves
`inventory_hostname` (`node.slug`) to `ansible_host` (`endpoint.mdns_name`) for the bootstrap
connection, without touching the `HOSTS_INTENT_SCHEMA_VERSION` (no shape change — one more key in
an existing dict).

## Tests

- Extended `test_primary_endpoint_with_mdns_exports_ssh_host` in
  `nctl/tests/test_hosts_intent.py` to assert `ansible_host == "agnomad.local"`.
- No new skip reason needed: a node whose selected endpoint has no `mdns_name` was already
  skipped via `missing_mdns_name` before `_host_vars` is ever called.

## Verification

```
uv run pytest tests/test_hosts_intent.py tests/test_hosts_intent_render.py -q
```
16 passed.
