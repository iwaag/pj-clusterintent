# Service Placement and Production Inventory Implementation Plan

## Status

Planned breaking redesign. Database migrations must be preserved and applied in
order. Outside the migration history, do not retain compatibility readers,
legacy exporters, duplicate fields, deprecated seed shapes, or transitional
inventory artifacts.

Only the new bootstrap schema and production schema `1.0` are executable
contracts after cutover. Do not add readers, converters, negotiation, or
fallback execution for pre-redesign inventory, intent, placement, operational
config, or deployment-profile formats. Operational rollback may retain the
last valid artifact only when it already conforms to the current schema; it is
not a legacy-format fallback.

## Objective

Replace `DesiredNode.expected_spec.ansible_groups` with an explicit service
placement model and generate the production Ansible inventory as a deterministic
projection of:

1. desired service declarations,
2. operator-controlled desired service placements,
3. desired nodes and endpoints,
4. typed desired node operational settings,
5. realized Nautobot Devices populated from nodeutils, and
6. an Ansible-owned deployment-profile mapping.

The bootstrap inventory remains a separate, minimal artifact used only to reach
name-reserved nodes and run nodeutils. The production inventory is generated
only after nodeutils data has been ingested into Nautobot.

## Design Decisions

### Source-of-truth ownership

- `DesiredService` describes a logical service. Git repository analysis remains
  its normal owner and may update service metadata, requirements, and placement
  policy without modifying placements.
- `DesiredServicePlacement` describes the desired binding of one service
  instance to one `DesiredNode`. Operators normally create and edit placements
  through Nautobot UI or environment intent YAML.
- `DesiredEndpoint` describes a network-facing endpoint. A placement may select
  an endpoint, but the node remains the execution target.
- `DesiredNodeOperationalConfig` owns explicit non-service execution policy,
  including connection selection, power control, laptop classification, Ansible
  port, and the policy for nodes that cannot run nodeutils.
- nodeutils and nauto own observed host facts. Observations never decide whether
  a host belongs to a desired service group.
- `ansible_agdev` owns the mapping from a neutral deployment profile to an
  Ansible group and the allowed projection of service configuration into role
  variables.
- The Ansible export playbook serializes the audited deployment-profile map as
  canonical JSON and supplies it in the production export Job input. The Job
  does not read files from the `ansible_agdev` checkout or keep a second profile
  copy in nintent.
- Secrets remain in Ansible Vault or another secret store. They must not be
  stored in placement configuration or exported from Nautobot.

### Desired versus actual behavior

- Desired placement determines which service must be configured on which node.
- Actual facts supplement the execution substrate: operating system, current
  addresses, architecture, primary interface, and similar directly observed
  values.
- A missing or stopped observed service must not remove a host from its desired
  service group.
- Desired/actual disagreement is reported as drift. The exporter must not hide
  disagreement by silently treating an observed value as desired intent.
- Stale actual data must be identified from `collected_at`/`last_seen`; it must
  not be silently presented as current.

### No speculative derivation

The production inventory exporter must use an explicit allowlist of facts and
must not infer additional operational choices. In particular, it must not:

- derive `package_manager` from `host_os`, `system`, distribution, or any other
  fact;
- infer service placement from installed packages, processes, containers,
  `service_roles`, or `observed_services`;
- infer power-management policy from OS or hardware;
- infer Tailscale addressing from ordinary interface data;
- copy the complete `inventory_raw_json` object into Ansible host variables;
- flatten arbitrary custom fields or placement JSON into the inventory.

Package selection remains inside the relevant Ansible role using explicit role
logic and, where appropriate, live Ansible facts.

## Target Data Model

Add `DesiredServicePlacement` to `nintent` as a `PrimaryModel` with these fields:

- `desired_service`: required foreign key to `DesiredService`;
- `desired_node`: required foreign key to `DesiredNode`;
- `desired_endpoint`: optional foreign key to `DesiredEndpoint`;
- `instance_name`: required slug identifying the instance within the service;
- `desired_state`: typed choice, initially `active` or `disabled`;
- `instance_role`: optional typed/string role such as `primary`, `replica`, or
  `worker` without Ansible semantics;
- `deployment_profile`: required slug consumed by the Ansible-side profile map;
- `config_schema_version`: required non-empty string;
- `config`: JSON object containing environment-specific, non-secret desired
  service configuration;
- `assignment_source`: typed choice such as `manual`, `yaml`, `policy`, or
  `generated`;
- `reason`: optional operator-readable placement rationale.

Add database constraints for:

- uniqueness of `(desired_service, instance_name)`;
- non-empty `deployment_profile` and `config_schema_version`;
- an endpoint belonging to the same node as the placement, enforced in model
  validation and importer validation;
- `config` being a JSON object rather than a list or scalar.

Intent YAML references must use identities that are unique in the current data
model rather than assuming that display names or slugs are globally unique:

- `desired_node` uses the globally unique `DesiredNode.slug`;
- `desired_service` uses the existing unique tuple `intent_source`,
  `catalog_namespace`, `catalog_metadata_name`, and `service_type`, with
  `intent_source` represented by its globally unique slug;
- an endpoint reference is scoped to its already selected node and uses both
  `name` and `endpoint_type`.

Loaders and importers reject incomplete, missing, or ambiguous references. They
must not select the first row returned by a query. UI forms may present human
readable labels, but persist the same unambiguous foreign keys.

Do not add an Ansible group field to nintent. Do not add a direct
`DesiredService.desired_node` foreign key; the placement is the relation and
supports multiple instances.

Keep `DesiredService.requirements` and `placement_policy` for requirements and
candidate/proposal evaluation. They do not constitute an active placement.

Add `DesiredNodeOperationalConfig` as a one-to-one typed model for
`DesiredNode` with these fields:

- `desired_node`: required one-to-one relation;
- `actual_state_policy`: `required` or `declared`; `required` means nodeutils
  data must satisfy freshness and field requirements, while `declared` is for
  intentionally non-collectable targets such as Home Assistant OS;
- `expected_host_os`: typed optional value, required when
  `actual_state_policy=required`; initial supported values are `linux` and
  `macos`; it is used only for drift and operational-policy validation and is
  never exported as `host_os` or used to build OS selector groups;
- `declared_host_os`: typed optional value, required when
  `actual_state_policy=declared`; the initial and only supported value is
  `haos`; declared Linux/macOS support requires a later explicit contract
  extension;
- `connection_path`: typed choice, initially `local` or `tailscale`;
- `local_endpoint`: optional relation to a `DesiredEndpoint` on the same node;
- `tailscale_endpoint`: optional relation to a `DesiredEndpoint` on the same
  node;
- `ansible_port`: optional positive integer;
- `power_control`: typed choice, initially `none`, `wol`, or `macos_sleep`;
- `is_laptop`: explicit boolean operational classification.

Derive `power_managed` membership from an explicit non-`none` `power_control`
value. Resolve desired local and Tailscale addresses through the selected
DesiredEndpoint rows instead of duplicating addresses in the operational model.
Validate that selected endpoints belong to the configured node.

Model and importer validation enforce the policy-dependent fields:

- `actual_state_policy=required` requires `expected_host_os` and forbids
  `declared_host_os`;
- `actual_state_policy=declared` requires `declared_host_os` and forbids
  `expected_host_os`;
- `connection_path=tailscale` requires a usable `tailscale_endpoint`;
- a declared node using `connection_path=local` requires a usable
  `local_endpoint` because it has no actual `local_ip` fallback.

The production composer also validates platform and power policy together.
Schema `1.0` permits `none` or `wol` for expected Linux, `none` or
`macos_sleep` for expected macOS, and only `none` for declared HAOS. An
unsupported desired combination is a global operational contract error; it is
not corrected from actual data. For an actual-backed node, a normalized
observed OS that differs from `expected_host_os` is recorded as drift. The OS
selector and exported `host_os` still use the observed value. If the observed
OS makes the configured power policy unsafe for current playbooks, the Job
fails with an explicit platform/power mismatch instead of emitting an invalid
`power_managed` member.

Define production eligibility as a `DesiredNode` in `approved` or `active`
lifecycle with an exportable node type. Every production-eligible node must
have exactly one `DesiredNodeOperationalConfig`; absence is a global contract
error. `planned` nodes remain eligible for bootstrap discovery but do not enter
the production inventory.

## Configuration Contracts

### Placement configuration

Common searchable identity and lifecycle values must be typed model fields.
Service-specific desired settings may remain in `config`, but each deployment
profile must declare and validate its accepted schema. Unknown keys fail
validation instead of being passed through to Ansible.

Example placement intent:

```yaml
desired_service_placements:
  - desired_service:
      intent_source: infrastructure
      catalog_namespace: default
      catalog_metadata_name: dnsmasq
      service_type: service
    instance_name: primary
    desired_node: agdns01
    desired_endpoint:
      name: primary
      endpoint_type: primary
    desired_state: active
    instance_role: primary
    deployment_profile: dnsmasq
    config_schema_version: "1"
    assignment_source: yaml
    config:
      dhcp_authoritative: true
      listen_addresses:
        - 192.168.0.1
```

### Ansible deployment profiles

Add one version-controlled mapping in `ansible_agdev`, for example
`vars/deployment_profiles.yml`:

```yaml
deployment_profiles:
  dnsmasq:
    group: dnsmasq_server
    config_schema_version: "1"
    variables:
      dhcp_authoritative:
        ansible_variable: dnsmasq_dhcp_authoritative
        type: boolean
        required: false
      listen_addresses:
        ansible_variable: dnsmasq_listen_addresses
        type: list
        items: string
        required: false
```

The profile map is an explicit contract. The production exporter fails on an
unknown profile, unsupported schema version, unknown config key, duplicate
variable assignment, invalid value type, missing required key, or conflicting
values from multiple placements on the same host. Each variable declaration
contains the exact Ansible variable name, its accepted JSON type, requiredness,
and an item type for lists. Schema `1.0` supports only the audited scalar and
collection shapes required by current roles; unsupported or unconstrained
objects are not passed through.

The export playbook loads `vars/deployment_profiles.yml`, serializes only the
`deployment_profiles` mapping to canonical JSON, calculates its SHA-256 digest,
and sends both values as Job input. The Job parses and validates that payload,
uses it for composition, and records the digest in `production.yml` metadata and
the companion JSON report. Profile data must contain no secrets. Manual Job
execution requires the same JSON input and is subject to the same validation.

For this contract, canonical JSON is the UTF-8 encoding of Python
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
allow_nan=False)` with no BOM and no trailing newline. All mapping keys must be
strings. The Job parses the input, reserializes it with those exact settings,
requires byte-for-byte equality with the supplied input, and calculates the
SHA-256 over those UTF-8 bytes before comparing the supplied digest. Contract
fixtures prove that Ansible and Python produce identical bytes and digests.

### Production connection variables

Keep connection resolution in `inventories/generated/group_vars/all/main.yml`
with this contract:

1. For `connection_path=local`, resolve `local_ip`, then
   `local_dns_hostname`, then `mdns_hostname`, then `inventory_hostname`.
2. For `connection_path=tailscale`, require and use `tailscale_ip`.
3. For actual-backed Devices, export `local_ip` from nodeutils actual data.
4. From `local_endpoint`, export `local_dns_hostname` from `dns_name` and
   `mdns_hostname` from `mdns_name`; for a declared HAOS node, also export
   `local_ip` from the endpoint `ip_address`.
5. From `tailscale_endpoint`, export `tailscale_ip` from `ip_address`.

The exporter validates that the selected connection path resolves to a
non-empty address/name. Missing selected endpoints or unusable endpoint fields
are operational contract errors.

All current hosts use the same SSH user. Add
`ansible_user: "{{ default_user }}"` to generated production
`group_vars/all/main.yml`; do not duplicate it per host. A future per-host user
requirement must add an explicit typed operational field and contract.

### Actual-state allowlist

Initially export only actual host variables that are directly available from
current nodeutils reports and consumed by current playbooks:

- normalized `host_os` from nodeutils `facts.system`, with only the explicitly
  supported `Linux -> linux` and `Darwin -> macos` mapping;
- `local_ip` from `facts.network.primary_ip_address`;
- `mac_address` from `facts.network.primary_mac_address`;
- `network_interface` from `facts.network.primary_interface.name`.

The mapping above is closed: adding a fact requires a concrete current
playbook consumer, a documented source path, and tests. Do not initially export
CPU, memory, GPU, package inventories, Docker summaries, arbitrary interface
lists, or observed-service payloads as Ansible host variables.

Use the report collection timestamp internally for freshness validation and in
the companion JSON report as provenance. Do not emit it as an Ansible host
variable until a playbook has a concrete consumer.

Export `power_control`, `connection_path`, `tailscale_ip`, `ansible_port`, and
`is_laptop` from `DesiredNodeOperationalConfig` and its selected endpoints.
These values are desired operational configuration rather than actual facts.
For a declared HAOS node, also export `host_os: haos` from
`declared_host_os`. This is an explicit declared value, not a desired fallback
for an actual-backed host.

## Inventory Artifacts

Use two explicit generated files:

- `inventories/generated/hosts_intent.yml`: minimal bootstrap inventory;
- `inventories/generated/production.yml`: joined desired/actual production
  inventory.

Production JSON reports are immutable, generation-addressed files under
`inventories/generated/production.reports/<generation_id>.json`. The generated
inventory metadata records the generation ID, report path, schema version, and
deployment-profile digest. Generated inventories and reports are ignored by
Git. The Job creates `generation_id` as a UUID and clients treat it only as a
validated filename component; Job input cannot choose a report path.

Both files are generated, validated, ignored by Git, and replaced atomically.
Neither is a compatibility copy of the other.

For a production refresh, download and validate both artifacts in a staging
directory, including matching generation ID and profile digest. Install the
immutable generation-addressed report first, then atomically replace
`production.yml`. Consequently the active inventory always refers either to
its already installed report or to the previous generation of the same current
schema. Cleanup may remove unreferenced old reports only after a successful
replacement and must retain the report referenced by the active inventory. No
reader for reports from an obsolete schema is retained.

The bootstrap artifact contains only eligible nodes, the `ssh_hosts` group,
stable desired-node identifiers, and the selected mDNS endpoint required to run
nodeutils. It must not contain service groups or `host_os` copied from desired
intent.

The production artifact contains:

- every production-eligible DesiredNode that passes host-level actual checks in
  the flat `ssh_hosts` group,
  independently of whether it has an active service placement;
- actual-backed nodes whose realized Device has sufficient fresh required
  facts;
- explicitly declared nodes such as HAOS, using typed operational settings and
  DesiredEndpoints without requiring nodeutils data;
- service groups generated from deployment profiles;
- factual `linux`/`macos` execution groups generated from the allowlisted
  observed `host_os` value because current playbooks target these groups; these
  groups are derived selector indexes and not the primary host containers;
- a declared `haos` selector group generated from the typed declared platform
  for nodes with `actual_state_policy=declared`;
- explicit desired operational groups only where a current playbook requires
  them and where their source is not a service placement;
- allowlisted actual host variables;
- mapped desired service variables;
- stable nintent and Nautobot object IDs for traceability;
- schema version, generation timestamp, source observation timestamp, and a
  skipped/error summary in the companion JSON export.

Inventory generation follows the explicit global-failure and host-skip policy
below and never fills missing values heuristically.

### Export failure policy

Fail the complete Job and preserve the previous local production inventory for
global contract errors:

- malformed profile JSON or digest mismatch;
- unknown deployment profile, unsupported config schema, or unknown config key;
- duplicate inventory hostname or conflicting host-variable assignment;
- placement/endpoint/node reference inconsistency;
- a production-eligible node without `DesiredNodeOperationalConfig`;
- an invalid declared-node contract or unresolved configured connection path;
- an unsupported platform/power-control combination;

Skip only the affected host and record a structured reason in the companion
JSON report for host-specific actual-state availability problems:

- missing or stale nodeutils data for `actual_state_policy=required`;
- missing consumer-specific actual facts such as WOL MAC address;
- no realized Device or an unsupported realized actual type;
- a realized Virtual Machine, because production schema `1.0` supports
  nodeutils-backed Devices only.

Placements targeting a skipped host are reported as inactive export members and
do not create dangling group entries. A successful Job may contain skipped
hosts, but its summary must include included/skipped counts and reason codes.

## Breaking Removals

Remove these paths rather than deprecating them:

- `expected_spec.ansible_groups` parsing, validation, tests, seed values, and
  export behavior;
- desired `host_os`/`os` fallback in the production inventory path;
- `preferred_services` as a placement declaration in nodeutils, nauto custom
  fields, placement review, seeds, and documentation;
- `service_roles` as a source of desired Ansible group membership;
- checked-in hand-maintained `inventories/production/hosts.yml` and the old
  broad `inventories/hosts.example.yml` once the generated production inventory
  is operational;
- the `networktocode.nautobot.inventory` setup and source configuration if it
  has no remaining consumer after the dedicated production export is added;
- old schema examples and README instructions describing direct Ansible groups
  in node intent;
- readers, renderers, validators, fixtures, and Job inputs for pre-redesign
  bootstrap or production inventory schemas;
- support for loading multiple deployment-profile schema versions or
  negotiating an older profile contract.

Keep `observed_services` only as actual-state evidence for evaluation. It is not
an inventory-group input.

Database migration files remain in history. A data migration must remove retired
`ansible_groups`, desired `host_os`, and `os` keys from existing
`DesiredNode.expected_spec` JSON. Do not implement runtime fallback for rows
that were not migrated. Do not attempt an ambiguous automatic conversion from
old group names to services; replace those declarations explicitly in seed
data with DesiredService and DesiredServicePlacement records. Replace necessary
non-service host settings with explicit `DesiredNodeOperationalConfig` seed
records, including the HAOS collection exemption.

## Implementation Steps

### 1. Freeze and test the new contracts

1. Inventory all current static groups and classify each as service placement,
   observed OS classification, desired operational policy, or obsolete.
2. Inventory every host variable consumed by current playbooks and record its
   authoritative source and whether it is desired or actual.
3. Audit every role default and template referenced by a deployment profile.
   Record exact existing variable names and types before defining profile
   mappings; examples in this plan are not contracts.
4. Define the typed deployment-profile shape and the exact canonical JSON byte
   and SHA-256 Job-input contract used to transfer the Ansible-owned deployment
   profiles to nintent.
5. Define and test the connection-variable resolution contract and the shared
   `ansible_user` group variable.
6. Define and test the qualified DesiredService and node-scoped DesiredEndpoint
   reference formats used by intent YAML.
7. Define production inventory schema `1.0`, placement config schemas, and the
   initial deployment-profile map from that audit.
8. Add contract fixtures for at least Linux, macOS, HAOS declared state,
   missing actual data, stale actual data, endpoint mismatch, unknown profile,
   invalid profile value type, ambiguous reference, desired/actual OS mismatch,
   invalid platform/power combination, and conflicting placement variables.

Exit criterion: every generated group and host variable has one documented
source and no field depends on heuristic inference.

### 2. Add placement and node operational models in nintent

1. Add `DesiredServicePlacement`, constraints, validation, migration, admin/UI
   form, table, list/detail/edit/delete views, filters, and navigation.
2. Add `DesiredNodeOperationalConfig`, constraints, endpoint validation,
   migration, admin/UI form, table, views, filters, and navigation.
3. Add YAML loader/importer support for `desired_service_placements` and
   `desired_node_operational_configs` with
   deterministic identity and strict qualified-reference validation.
4. Ensure Git-based DesiredService synchronization never deletes or overwrites
   independently owned placements.
5. Add unit tests for model validation, CRUD, importer idempotency, ownership,
   endpoint/node consistency, expected/declared OS exclusivity, actual-state
   policy validation, and service re-analysis with existing placements.
6. Update nintent concept and operator documentation.

Exit criterion: operators can create placements and operational settings
manually or from environment YAML, HAOS can be declared as non-collectable, and
re-analyzing a service repository preserves independently owned records.

### 3. Replace legacy placement declarations

1. Add explicit DesiredService declarations for every currently deployed
   infrastructure service that is not generated from a Git repository.
2. Add one placement per intended service instance for current production
   nodes.
3. Move production nodes to `approved` or `active` lifecycle and add operational
   configuration for every such node, including `expected_host_os` for
   actual-backed Linux/macOS nodes. Add HAOS with
   `actual_state_policy=declared`, `declared_host_os=haos`, its connection
   endpoint, and its Ansible port.
4. Remove every `ansible_groups` key and desired `host_os`/`os` bootstrap value
   from `nauto/seed/intent_sources.yaml` and other source documents.
5. Remove `preferred_services` collection and ingest support. Remove its custom
   field seed and all placement-review dependence on it.
6. Remove tests and documentation for the retired shapes instead of keeping
   dual-format parsing.

Exit criterion: all intended service membership is represented by placement
rows, every production-eligible node has operational configuration, and no
runtime code reads `ansible_groups` or `preferred_services`.

### 4. Simplify the bootstrap inventory

1. Change `nintent` bootstrap export to ignore service placement and emit only
   `ssh_hosts` plus mDNS reachability and stable identity metadata.
2. Remove desired `host_os` from bootstrap host variables.
3. Increment the bootstrap schema version because this is a breaking contract.
4. Update the export Job, Ansible download playbook, fixtures, and tests to the
   new schema, deleting old-schema fixtures and code instead of accepting both
   versions.
5. Preserve atomic local replacement: download to a temporary file, validate
   with `ansible-inventory --list`, then replace `hosts_intent.yml`.

Exit criterion: bootstrap collection succeeds without carrying production
service groups or pretending desired facts are observed facts.

### 5. Make actual facts exportable without inference

1. Ensure nauto persists each allowlisted nodeutils fact with its collection
   timestamp and source provenance. Add a dedicated custom field only when the
   value cannot be read reliably from the existing normalized/custom-field
   representation.
2. Persist the primary interface name explicitly instead of making the
   production exporter inspect unrestricted raw JSON.
3. Keep source values intact; normalization to the production `host_os` enum
   occurs in one tested exporter function.
4. Add freshness validation for nodes with `actual_state_policy=required` and
   bypass nodeutils freshness only for explicitly declared nodes.
5. Define required actual fields per current consumer: `host_os` for observed OS
   selectors, `mac_address` for WOL, and `network_interface` for playbooks or
   profiles that consume it. Do not require every allowlisted field on every
   host.
6. Add tests proving that no package manager, power policy, service placement,
   or other derived operational value is emitted from actual data.
7. Limit production schema `1.0` actual-backed composition to realized Devices.
   Emit `unsupported_actual_type` for realized Virtual Machines and defer VM
   ingest/export support to a later schema.

Exit criterion: the exporter can obtain every allowlisted fact through stable,
documented fields without parsing arbitrary raw inventory blobs.

### 6. Implement deterministic production inventory composition

1. Add a pure composition module with no Nautobot Job dependencies. It accepts
   placements, desired nodes/endpoints, operational configs, realized objects,
   actual facts, and the deployment-profile map, then returns inventory plus a
   structured summary.
2. Select `approved` and `active` production nodes and fail if any lacks exactly
   one operational config.
3. Join actual-backed nodes to realized Device objects and validate their
   freshness and consumer-specific required facts.
4. Compose declared nodes such as HAOS from typed operational settings and
   DesiredEndpoints without requiring a realized object or nodeutils report.
5. Build service groups from deployment profiles, never from observed services.
6. Build `linux` and `macos` selector groups from normalized observed system and
   the `haos` selector from an explicit declared platform.
7. Compare observed OS with `expected_host_os` for drift without using the
   expected value for exported `host_os` or OS selectors.
8. Export `host_os: haos` only for the explicit declared HAOS path and validate
   every desired and observed platform/power-control combination.
9. Resolve local and Tailscale connection variables from actual data and the
   selected operational endpoints according to the connection contract.
10. Map only declared, type-valid placement config keys to exact audited Ansible
   variables.
11. Apply the documented global-failure/host-skip taxonomy and prevent dangling
   placement group membership for skipped hosts.
12. Detect conflicting host variable assignments and fail deterministically.
13. Produce deterministic ordering and schema-versioned YAML and JSON renderers.
14. Add unit tests covering all joins, HAOS, Device-only actual support, skips,
   global validation failures,
   deterministic output, multiple services on one node, and multiple instances
   of one service.

Exit criterion: identical Nautobot state and profile input produce byte-stable
inventory output, and unsupported or ambiguous state fails closed.

### 7. Add the production export workflow

1. Add a Nautobot Job that accepts canonical deployment-profile JSON and its
   SHA-256 digest, validates them, calls the pure composer, and publishes
   `production.yml` plus a detailed JSON report containing the digest.
2. Add an Ansible localhost playbook that loads and serializes
   `vars/deployment_profiles.yml`, computes the digest, runs the Job with both
   inputs, waits for completion,
   downloads both artifacts, verifies their matching generation ID, profile
   digest, and schema, validates the YAML with `ansible-inventory --list`,
   installs the immutable report, and atomically replaces
   `inventories/generated/production.yml`.
3. Factor shared JobResult/FileProxy polling and download behavior out of the
   bootstrap and production export playbooks to avoid duplicate transport code.
4. Never delete or truncate the previous valid production inventory when a Job,
   download, schema check, or inventory validation fails. This protection
   applies only to an existing artifact that validates against the current
   production schema; do not fall back to a legacy inventory.
5. Add a concise command or Make target for the complete pipeline:
   bootstrap export, nodeutils collection, Nautobot ingest, and production
   export.

Exit criterion: production playbooks use a validated local snapshot and make no
implicit inventory-time Nautobot API calls.

### 8. Switch current playbooks to the generated contract

1. Point production execution explicitly at
   `inventories/generated/production.yml`; do not rely on an ambiguous global
   default inventory for both stages.
2. Add `ansible_user: "{{ default_user }}"` and the documented local/Tailscale
   connection resolution to generated production `group_vars/all/main.yml`.
3. Update playbooks and roles to consume only the documented production
   variables and groups.
4. Keep package selection in roles. Do not introduce a generated
   `package_manager` inventory variable.
5. Export power-management policy, connection path, selected desired endpoint
   addresses, Ansible port, and laptop classification from
   `DesiredNodeOperationalConfig`.
6. Generate `power_managed` from explicit non-`none` power control and generate
   all production hosts under the flat `ssh_hosts` base group. Keep OS groups as
   derived selectors while current playbooks use them.
7. Verify the HAOS deployment play through the declared-node path without a
   nodeutils report.
8. Remove the hand-maintained production inventory and obsolete examples after
   the generated inventory passes an end-to-end run.

Exit criterion: all current operational playbooks resolve their hosts and
required variables from the new production artifact.

### 9. Update service evaluation and placement review

1. Make deterministic evaluation compare DesiredService plus active placements
   against `observed_services` and actual host facts.
2. Treat placement review output as a proposal only. It must not mutate active
   placements without an explicit operator action.
3. Remove file-based desired-service loading where persisted nintent models are
   authoritative.
4. Report missing service, wrong node, stale observation, insufficient actual
   facts, and desired/actual OS mismatch separately.
5. Add tests proving that absent observations do not remove desired inventory
   membership.

Exit criterion: evaluation explains drift while inventory continues to express
the desired convergence target.

### 10. Remove obsolete code and verify the whole pipeline

1. Search all three repositories for `ansible_groups`, `preferred_services`,
   legacy production inventory paths, and old schema versions; remove remaining
   runtime, fixture, and documentation references rather than retaining
   compatibility paths.
2. Run nintent model/import/export/evaluation tests, nauto ingest/review tests,
   nodeutils report tests, and Ansible syntax/inventory validation.
3. Perform an end-to-end dry run with one Linux node, one macOS node, and the
   declared HAOS node.
4. Verify that a deliberately missing observed service remains in its desired
   service group.
5. Verify that an OS mismatch is reported, no `package_manager` is generated,
   and the previous valid inventory survives a failed refresh.
6. Apply formatting, migration consistency checks, and final documentation
   updates.

Exit criterion: the repository contains only the new contracts and artifacts,
with database migrations as the sole retained transition mechanism.

## Acceptance Criteria

- Database migrations are the only retained transition mechanism; runtime code,
  Jobs, fixtures, seeds, documentation, and generated artifacts support only
  the new contracts and contain no legacy reader, converter, dual-format path,
  or profile-version negotiation.
- No source, exporter, test, or documentation reads
  `DesiredNode.expected_spec.ansible_groups`.
- DesiredService synchronization preserves placements.
- DesiredNode operational settings have a typed source and are exported without
  reading legacy hand-maintained inventory files.
- Every `approved` or `active` production node has exactly one operational
  config; missing configuration is a global contract failure.
- Actual-backed operational configs carry typed `expected_host_os` for drift
  and policy validation, but expected OS never controls exported `host_os` or
  OS selector membership.
- Service group membership is derived exclusively from active placements and
  the Ansible deployment-profile map.
- Observed services never control desired group membership.
- The actual-state exporter emits only the documented allowlist.
- Actual-backed nodes use freshness validation, while only explicitly declared
  nodes such as HAOS can enter production inventory without nodeutils data.
- Production schema `1.0` supports realized Devices for actual-backed nodes;
  realized Virtual Machines are skipped with `unsupported_actual_type`.
- No `package_manager` variable is generated or inferred.
- Every deployment-profile variable name and type matches an audited current
  role input; the dnsmasq profile uses `dnsmasq_dhcp_authoritative` rather than
  a non-existent alias.
- Bootstrap and production inventories are distinct, explicit, validated local
  artifacts.
- The Ansible-owned profile map reaches the Job only through validated canonical
  JSON plus a recorded SHA-256 digest.
- Intent YAML resolves DesiredService through its unique composite identity and
  DesiredEndpoint through a node-scoped name/type identity; ambiguous
  references fail validation.
- Deployment profiles carry machine-validated value types and requiredness;
  config values are never accepted as untyped pass-through data.
- Local and Tailscale connection variables follow the documented endpoint and
  actual-data precedence, and all current hosts receive `ansible_user` from
  production `group_vars/all`.
- `actual_state_policy=declared` supports only `declared_host_os=haos` in schema
  `1.0`.
- Declared HAOS emits `host_os: haos`, while actual-backed Linux/macOS never use
  a desired OS fallback.
- Platform and power-control combinations are explicitly validated and invalid
  combinations fail the complete Job.
- Production hosts are stored in flat `ssh_hosts`; service, OS, power, and HAOS
  groups are membership indexes over those hosts.
- Production inventory refresh is atomic and preserves the last valid file on
  failure.
- The active production inventory references an already installed immutable
  JSON report with the same generation ID and deployment-profile digest.
- Profile/schema/reference/config/connection contract violations fail the whole
  Job; stale or missing host actual data and unsupported actual types skip only
  the affected host with structured reason codes.
- Current Linux/macOS and service-specific playbooks can run from the generated
  production inventory without querying Nautobot during inventory parsing.
