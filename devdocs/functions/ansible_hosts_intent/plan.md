# hosts_intent.yml export implementation plan

## Goal

Generate a minimal Ansible bootstrap inventory from nintent DesiredNode and
DesiredEndpoint data.

This inventory is not the canonical infrastructure inventory. It is the
initiator inventory for name-reserved compute resources: enough information to
reach a node by mDNS and run nodeutils. After nodeutils collection, nauto should
ingest the observed facts into Nautobot Devices, and the regular Nautobot
inventory should become the richer post-discovery inventory.

## Design Decisions

- This is a breaking-change phase. Do not keep compatibility shims for the
  handwritten `hosts.yml` era. New automation should consume generated
  inventories directly.
- Do not restrict export to `DesiredEndpoint.endpoint_type == "mdns"`.
  Most nodes are expected to have one Device-like DesiredNode and one primary
  DesiredEndpoint. The exporter should select an mDNS-bearing endpoint per node,
  not require a special endpoint type.
- Keep `hosts_intent.yml` intentionally small. It should contain the inventory
  hostname, `mdns_hostname`, optional explicit `host_os`, intent identifiers,
  and explicit service/workload Ansible group membership. Detailed host facts
  belong to nodeutils/Nautobot, not this file.
- Use a flat SSH bootstrap group instead of OS groups as the primary inventory
  shape. OS should be a host variable (`host_os`) when known, not the top-level
  host organization. Service/workload categories such as `grafana_server` and
  `nomad_server` remain groups.
- Use `DesiredNode.expected_spec.ansible_groups` for Ansible group membership.
  This is more explicit than overloading `DesiredNode.role`, and it supports
  multiple groups such as `nomad_server` and `prometheus_node_exporter_targets`.
- Treat existing handwritten `ansible_agdev/inventories/production/hosts.yml`
  as obsolete, not as an input to preserve. The target workflow is:
  `nintent -> hosts_intent.yml -> nodeutils collection -> nauto ingest -> Nautobot Device -> networktocode.nautobot inventory`.
- Defer Nautobot regular inventory group reflection. This plan only guarantees
  reliable generation and consumption of `hosts_intent.yml`.

## Export Semantics

One Ansible host should be emitted per eligible DesiredNode.

Eligible DesiredNode:

- `lifecycle` is one of `planned`, `approved`, or `active`.
- `node_type` is suitable for nodeutils bootstrap, initially `device` or
  `virtual_machine`. `service_host` can be included later if it is clearly a
  reachable host abstraction.
- At least one attached DesiredEndpoint can provide an mDNS name.

mDNS endpoint selection order:

1. `expected_spec.ansible_mdns_endpoint` if present, matching endpoint `name`.
2. Primary endpoint with `mdns_name`.
3. Management endpoint with `mdns_name`.
4. Any endpoint with `mdns_name`, sorted by `endpoint_type`, then `name`.

If a node has no mDNS-bearing endpoint, skip it and report the reason in the
export summary/skipped list.

Inventory host name:

- Default to `DesiredNode.slug`.
- Allow future override via `expected_spec.ansible_host_name`, but do not require
  it for the first implementation.

Group membership:

- Always include exported hosts in `ssh_hosts`.
- Always include exported hosts in `nintent_reserved` only if a distinct
  lifecycle marker group is still useful during implementation; otherwise omit
  it. Do not keep both solely for compatibility.
- Add groups from `DesiredNode.expected_spec.ansible_groups` when it is a list of
  non-empty strings.
- Do not emit `linux` or `macos` groups by default. OS-specific behavior should
  use `host_os` before connection when explicitly set, or `ansible_system` after
  facts are gathered.
- Ignore `DesiredNode.role` for group generation in the first implementation.

Host variables:

```yaml
mdns_hostname: node1.local
host_os: linux
nintent_inventory_stage: reserved_name
nintent_desired_node: Node 1
nintent_desired_node_slug: node1
nintent_desired_node_id: "<uuid>"
nintent_desired_endpoint: primary
nintent_desired_endpoint_id: "<uuid>"
name_reserved_only: true
```

Only emit `host_os` when it is explicitly present in intent, for example
`expected_spec.host_os` or `expected_spec.os`. Avoid exporting guessed OS, IP
address, MAC address, power state, GPU, or service facts. Those come from
nodeutils/nauto.

## nintent Changes

Add a new helper module, for example:

- `nautobot_intent_catalog/ansible_inventory.py`

The module should expose pure functions similar to `dnsmasq.py`:

- `export_hosts_intent(nodes, *, include_skipped=True) -> HostsIntentExport`
- `hosts_intent_payload(export, *, generated_at, job_result_id=None) -> dict`
- `render_hosts_intent_yml(export, *, generated_at, job_result_id=None) -> str`
- `render_hosts_intent_json(export, *, generated_at, job_result_id=None) -> str`

Use deterministic sorting for hosts, groups, and skipped entries.

Add a Nautobot Job in `nautobot_intent_catalog/jobs.py`:

- Name: `Export Ansible Hosts Intent`
- Query `DesiredNode.objects.prefetch_related("desired_endpoints")`.
- Run the helper export.
- Attach files:
  - `hosts_intent.yml`
  - `hosts-intent-export.json`
- Log summary and skipped nodes when requested.

Add tests:

- Single primary endpoint with `mdns_name` exports one host.
- Does not require `endpoint_type == "mdns"`.
- `expected_spec.ansible_groups` creates child groups.
- Empty or malformed `expected_spec.ansible_groups` is ignored or reported
  deterministically.
- Node with no mDNS-bearing endpoint is skipped.
- Selection order prefers configured endpoint, then primary, then management,
  then deterministic fallback.

## ansible_agdev Changes

Add a playbook to run the new nintent job and download `hosts_intent.yml`, using
the existing dnsmasq export playbook as the pattern:

- `playbooks/export_nintent_hosts_intent.yml`

Suggested variables:

- `nintent_hosts_intent_job_name: "Export Ansible Hosts Intent"`
- `nintent_hosts_intent_local_dir: "{{ playbook_dir }}/../inventories/generated"`
- `nintent_hosts_intent_local_file: "{{ nintent_hosts_intent_local_dir }}/hosts_intent.yml"`
- `nintent_hosts_intent_expected_schema_version: "1.0"`

The playbook should:

1. Assert `nautobot_url` and `nautobot_token`.
2. Look up and run the Nautobot Job.
3. Poll the JobResult.
4. Find the `hosts_intent.yml` file proxy.
5. Download and validate schema marker/comment or JSON metadata.
6. Write `inventories/generated/hosts_intent.yml`.

For consuming the bootstrap inventory, use the generated inventory directly:

```bash
ansible-playbook \
  -i inventories/generated/hosts_intent.yml \
  -e nodeutils_target_hosts=ssh_hosts \
  playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

Update bootstrap-oriented playbooks so their defaults target `ssh_hosts` instead
of `linux:macos`. They should branch on `ansible_system` after fact gathering for
Linux/macOS differences. Keep `host_os` only as an optional pre-facts hint.

Move the minimal connection variables needed by generated inventory into the new
generated/bootstrap inventory path instead of relying on the old production
inventory layout. The generated inventory should not need to emit `ansible_host`
if shared group vars can derive it from `mdns_hostname`.

## Implementation Steps

### 1. Implement pure nintent export helper

Repository: `nintent`

Create:

- `nautobot_intent_catalog/ansible_inventory.py`
- `nautobot_intent_catalog/tests/test_ansible_inventory.py`

Implementation details:

- Define `ANSIBLE_HOSTS_INTENT_SCHEMA_VERSION = "1.0"`.
- Define a small dataclass, for example `HostsIntentExport`, with:
  - `summary`
  - `inventory`
  - `hosts`
  - `skipped`
- Keep the helper independent from Django. Tests should use `types.SimpleNamespace`
  or small local dataclasses, following the style of `test_dnsmasq.py`.
- Input to `export_hosts_intent()` should be an iterable of node-like objects.
  Each node is expected to expose `desired_endpoints.all()` in Nautobot, but the
  helper should also tolerate a plain list/tuple attribute named
  `desired_endpoints` for unit tests.
- Normalize all text with a local `_text()` helper.
- Normalize `expected_spec` only when it is a mapping. Non-mapping values should
  behave like `{}` and produce a skipped/warning detail only if it affects export.
- Determine `host_os` from:
  1. `expected_spec.host_os`
  2. `expected_spec.os`
  3. omitted
- Determine inventory hostname from:
  1. `expected_spec.ansible_host_name`, if non-empty
  2. `DesiredNode.slug`
- Validate inventory hostname and group names as conservative Ansible-safe names:
  `^[A-Za-z_][A-Za-z0-9_]*$` after replacing `-` with `_`, or decide to preserve
  hyphens if existing Ansible usage relies on them. Make the rule explicit in
  tests.
- Choose the endpoint using the mDNS endpoint selection order in this document.
- Build `inventory` in YAML inventory shape:
  - `all.children.ssh_hosts.hosts.<host>` contains host variables.
  - Each `expected_spec.ansible_groups[]` becomes
    `all.children.<group>.hosts.<host>: {}`.
- Do not emit `nintent_reserved` unless implementation finds a concrete
  immediate use for it. The default target group should be `ssh_hosts`.
- Include comments or top-level vars for schema metadata in rendered YAML.
  Prefer this header:

```yaml
# Generated by Nautobot Intent Catalog
# schema_version: 1.0
# generated_at: "..."
```

Test cases:

- Primary endpoint with `mdns_name` exports under `ssh_hosts`.
- Export does not require `endpoint_type: mdns`.
- `expected_spec.ansible_groups` creates groups such as `nomad_server`.
- `expected_spec.host_os` is copied; absent OS is omitted.
- `expected_spec.ansible_mdns_endpoint` selects a non-primary endpoint by name.
- Primary endpoint is preferred over management when no explicit endpoint is set.
- Node with no mDNS endpoint is skipped with `missing_mdns_name`.
- Deprecated/retired node is skipped.
- Malformed `ansible_groups` does not crash export.
- Rendered YAML is parseable by `yaml.safe_load()`.

Verification commands:

```bash
cd /home/eiji/agdev/temp2/nintent
uv run pytest nautobot_intent_catalog/tests/test_ansible_inventory.py
uv run pytest nautobot_intent_catalog/tests/test_dnsmasq.py
```

### 2. Add Nautobot Job for hosts intent export

Repository: `nintent`

Modify:

- `nautobot_intent_catalog/jobs.py`

Implementation details:

- Import the new render helpers.
- Add `ExportAnsibleHostsIntent(Job)` near `ExportDnsmasqRecords`.
- Job variables:
  - `include_skipped = BooleanVar(default=True, ...)`
- Query:

```python
nodes = DesiredNode.objects.prefetch_related("desired_endpoints").order_by("slug")
```

- Run:
  - `export = export_hosts_intent(list(nodes), include_skipped=include_skipped)`
  - `generated_at = timezone.now().isoformat()`
  - `job_result_id = str(getattr(self.job_result, "id", "")) or None`
  - `self.create_file("hosts_intent.yml", render_hosts_intent_yml(...))`
  - `self.create_file("hosts-intent-export.json", render_hosts_intent_json(...))`
- Log:
  - summary counts
  - output filenames
  - skipped details when requested
- Register the job in the `jobs = (...)` tuple.

Verification commands:

```bash
cd /home/eiji/agdev/temp2/nintent
uv run pytest nautobot_intent_catalog/tests/test_ansible_inventory.py
uv run pytest nautobot_intent_catalog/tests/test_dnsmasq.py nautobot_intent_catalog/tests/test_evaluations.py
```

Manual Nautobot verification after deployment:

1. Sync/reload the nintent plugin/jobs.
2. Confirm a Job named `Export Ansible Hosts Intent` exists.
3. Run it with `include_skipped=true`.
4. Confirm JobResult files include `hosts_intent.yml` and
   `hosts-intent-export.json`.

### 3. Add generated bootstrap inventory layout

Repository: `ansible_agdev`

Create:

- `inventories/generated/.gitkeep`
- `inventories/generated/group_vars/all/main.yml`

The new generated/bootstrap group vars should contain only the variables needed
to connect and run bootstrap collection:

```yaml
connection_path: local
local_connection_host: >-
  {{
    local_ip
    | default(local_dns_hostname | default(mdns_hostname | default(inventory_hostname, true), true), true)
  }}
ansible_host: >-
  {{
    tailscale_ip | default(local_connection_host, true)
    if connection_path == 'tailscale'
    else local_connection_host
  }}
default_user: "{{ vault_default_user }}"
ansible_become_password: "{{ vault_ansible_become_password }}"
nautobot_url: >-
  {{
    lookup('ansible.builtin.env', 'NAUTOBOT_URL')
    | default(vault_nautobot_url | default(''), true)
  }}
nautobot_token: >-
  {{
    lookup('ansible.builtin.env', 'NAUTOBOT_TOKEN')
    | default(vault_nautobot_token | default(''), true)
  }}
nautobot_validate_certs: true
```

Copying this from the old production group vars is acceptable because this is a
new generated inventory root, not compatibility with old `hosts.yml`.

Decision:

- Do not create or maintain a generated `linux`/`macos` group.
- Do not update `ansible.cfg` to point at generated inventory yet unless the
  current config hardcodes the old production inventory. Prefer explicit `-i`.

Verification commands:

```bash
cd /home/eiji/agdev/temp2/ansible_agdev
ansible-inventory -i inventories/generated/hosts_intent.yml --list
```

This command will only work after step 5 generates or a test fixture creates
`hosts_intent.yml`.

### 4. Add ansible playbook to download hosts_intent.yml

Repository: `ansible_agdev`

Create:

- `playbooks/export_nintent_hosts_intent.yml`

Use `playbooks/deploy_nintent_dnsmasq_records.yml` as the operational template,
but remove deployment-to-remote-host steps. This playbook should only run the
Nautobot job and write the local generated inventory.

Implementation outline:

1. `hosts: localhost`, `connection: local`, `gather_facts: false`.
2. Load `../vars/nautobot.yml`.
3. Define:
   - `nintent_hosts_intent_job_name`
   - `nintent_hosts_intent_local_dir`
   - `nintent_hosts_intent_local_file`
   - `nintent_hosts_intent_export_file_regex`
   - `nintent_hosts_intent_expected_schema_version`
   - poll retry/delay vars
4. Assert Nautobot API vars.
5. Reset/create `inventories/generated`.
6. Look up Job by name via `/api/extras/jobs/?q=...`.
7. Run Job via `/api/extras/jobs/<id>/run/`.
8. Extract JobResult ID from response body or Location header.
9. Poll `/api/extras/job-results/<id>/`.
10. Query file proxies.
11. Select the file proxy containing the JobResult ID and matching
    `hosts_intent.yml`.
12. Download file proxy.
13. Assert schema version header is present.
14. Write `inventories/generated/hosts_intent.yml`.
15. Run a local `ansible-inventory --list` validation against the generated file
    if `ansible-inventory` is available.

Verification command:

```bash
cd /home/eiji/agdev/temp2/ansible_agdev
ansible-playbook playbooks/export_nintent_hosts_intent.yml
ansible-inventory -i inventories/generated/hosts_intent.yml --graph
```

### 5. Update bootstrap collection playbooks

Repository: `ansible_agdev`

Modify:

- `playbooks/run_nodeutils_collect.yml`
- `playbooks/collect_nodeutils_and_ingest_nautobot.yml`

Changes:

- Change default target from `linux:macos` to `ssh_hosts`.
- Keep runtime OS branching based on `ansible_system`, since facts are gathered
  before the Linux package tasks and uv path decisions.
- Keep `host_os` available only as a pre-facts hint for future tasks; do not
  depend on it where `ansible_system` is available.

Concrete edits:

```yaml
# run_nodeutils_collect.yml
hosts: "{{ target_hosts | default('ssh_hosts') }}"

# collect_nodeutils_and_ingest_nautobot.yml
target_hosts: "{{ nodeutils_target_hosts | default('ssh_hosts') }}"
hosts: "{{ nodeutils_target_hosts | default('ssh_hosts') }}"
```

Validation:

```bash
cd /home/eiji/agdev/temp2/ansible_agdev
ansible-playbook -i inventories/generated/hosts_intent.yml --syntax-check playbooks/run_nodeutils_collect.yml
ansible-playbook -i inventories/generated/hosts_intent.yml --syntax-check playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

### 6. Add or update intent source data

Repository depends on where the active intent YAML lives. The loader defaults to
`nauto/seed/intent_sources.yaml` unless configured otherwise.

Add desired node records like:

```yaml
desired_nodes:
  - name: agnomad
    slug: agnomad
    node_type: device
    lifecycle: planned
    expected_spec:
      host_os: linux
      ansible_groups:
        - nomad_server

desired_endpoints:
  - name: primary
    desired_node: agnomad
    endpoint_type: primary
    ip_policy: external
    mdns_name: agnomad.local
```

Then run the nintent import job:

1. `Import Intent Sources`
2. `Export Ansible Hosts Intent`

No handwritten `ansible_agdev/inventories/production/hosts.yml` edits should be
part of this workflow.

### 7. End-to-end workflow

Expected operator flow after implementation:

```bash
cd /home/eiji/agdev/temp2/ansible_agdev

ansible-playbook playbooks/export_nintent_hosts_intent.yml

ansible-inventory \
  -i inventories/generated/hosts_intent.yml \
  --graph

ansible-playbook \
  -i inventories/generated/hosts_intent.yml \
  playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

After nauto ingest creates or updates Nautobot Devices, use the
`networktocode.nautobot` inventory as the regular detailed inventory. That is
outside this implementation step.

### 8. Cleanup after generated path works

Repository: `ansible_agdev`

Do this only after one successful end-to-end run:

- Stop using `inventories/production/hosts.yml` in documented commands.
- Remove stale references to `linux:macos` defaults in bootstrap playbooks.
- Decide whether old production inventory files should be deleted, archived
  under `.local`, or left unreferenced for a short manual rollback window.
  Because this is a breaking-change phase, do not add code paths that merge old
  and new inventories.

## Example Intent YAML

```yaml
desired_nodes:
  - name: agnomad
    slug: agnomad
    node_type: device
    lifecycle: planned
    expected_spec:
      host_os: linux
      ansible_groups:
        - nomad_server

desired_endpoints:
  - name: primary
    desired_node: agnomad
    endpoint_type: primary
    ip_policy: external
    mdns_name: agnomad.local
```

Expected inventory:

```yaml
all:
  children:
    ssh_hosts:
      hosts:
        agnomad:
          mdns_hostname: agnomad.local
          host_os: linux
          nintent_inventory_stage: reserved_name
          nintent_desired_node: agnomad
          nintent_desired_node_slug: agnomad
          nintent_desired_node_id: "<uuid>"
          nintent_desired_endpoint: primary
          nintent_desired_endpoint_id: "<uuid>"
          name_reserved_only: true
    nomad_server:
      hosts:
        agnomad: {}
```

## Open Follow-Ups

- Decide later how nauto should preserve intent-origin group hints after
  nodeutils ingest. Candidate destinations are Device custom fields or Tags,
  not necessarily Device Role.
- Decide later whether `service_host` DesiredNodes should be exported.
- Decide later whether stale generated bootstrap hosts should be pruned by
  lifecycle only or by an additional explicit `expected_spec.bootstrap_enabled`
  flag.
