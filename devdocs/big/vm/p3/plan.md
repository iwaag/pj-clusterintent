# Phase 3 Implementation Plan: Add the Minimal nintent Compute Models

This plan implements Phase 3 of [`devdocs/big/vm/roadmap.md`](../roadmap.md). It is grounded in
the Phase 1 frozen contract and reports, the completed Phase 2 actual-ledger implementation, the
repository development rules in `README.md` and `README_DEV.md`, and the local deployment
constraints in `.local/localenv_memo.md`.

Phase 3 adds structured desired compute intent and proves every supported read/write surface. It
does **not** create, start, stop, resize, move, replace, or delete a Proxmox guest. It also does
not add compute drift or automatic Cluster/VirtualMachine linking; those are Phase 4 concerns.
This repository is currently in the coordinated breaking-change phase described in
`README_DEV.md`: Phase 3 deploys the final schema and updates all in-scope consumers together. It
does not add or retain dual readers, deprecated aliases, shadow fields, or other artifacts whose
only purpose is backward compatibility.

**Supersession/coordinated-rollout note (added by
[`devdocs/big/remove_unused_surfaces/roadmap.md`](../../remove_unused_surfaces/roadmap.md) and its
[Phase 0 plan](../../remove_unused_surfaces/p0/plan.md)):** the `nctl serve`/`nctl dashboard`
surfaces and the nintent `reconciliation_status`/`reconciliation_checked_at` cache fields referenced
below as presentation/status effects are being removed by that separate, coordinated initiative.
Every "dashboard"/"status" effect in this plan is superseded by structured JSON drift, human-readable
CLI drift output, and reconcile manual-review classification/evidence — the retained inspection
surfaces `nctl drift`, `nctl reconcile`, and `nctl ops list/show`. The live rollout window applies
local migration `0015_compute_platform_instance_and_endpoint_mac` and the removal migration
`0016_remove_reconciliation_dashboard_surfaces` from one exact nintent revision, then activates one
matching nctl revision, before routine operations resume (`remove_unused_surfaces/p0/plan.md` §3.2).
This note does not change any compute, endpoint-MAC, migration-`0015`, seed, safety, or
no-actuation requirement elsewhere in this plan.

## 1. Purpose and Required State Transition

### 1.1 Desired transition

The desired-state system must move from:

```text
DesiredNode
  ├─ guest-OS desired identity
  ├─ realized_device (guest-OS actual link)
  └─ legacy realized_vm (semantically overlaps compute realization)

DesiredEndpoint
  └─ desired IP/DNS/mDNS, but no desired MAC

nctl
  └─ no typed desired platform or compute-instance records
```

to:

```text
DesiredNode
  └─ guest-OS desired identity + realized_device

DesiredEndpoint
  └─ sole owner of desired IP/DNS/mDNS/MAC

DesiredComputePlatform
  ├─ Proxmox platform intent
  ├─ control-node dependency
  ├─ strict versioned platform config
  └─ nullable realized_cluster link/cache

DesiredComputeInstance
  ├─ one-to-one owner: DesiredNode
  ├─ selected DesiredComputePlatform
  ├─ strict versioned instance config and capacity intent
  ├─ inherited/gated effective lifecycle
  └─ nullable realized_vm link/cache

nctl desired snapshot
  └─ typed platform/instance/MAC records, without compute evaluation or actuation
```

The concrete Phase 3 data target is one operator-confirmed desired relationship:

```text
aghub (DesiredNode)
  -> aghub-pve (DesiredComputePlatform)
     -> agdnsmasq (DesiredComputeInstance)
        -> agdnsmasq primary endpoint with desired MAC
```

The Phase 2 actual graph remains separate:

```text
aghub Device
  -> aghub-proxmox Cluster
     -> agdnsmasq VirtualMachine (LXC, VMID 108)
```

Phase 3 may read the actual graph for validation and evidence, but it does not write
`realized_cluster` or `realized_vm` for the seed relationship. The separately approved link plan
and link write belong to Phase 4.

### 1.2 Fresh evidence that proves the transition

Completion requires all of the following positive evidence:

1. The final breaking nintent migration applies in the running Nautobot environment and
   `makemigrations --check --dry-run` reports no missing migration.
2. Nautobot UI list/detail/edit paths expose the two compute models and endpoint MAC without a
   template-resolution or changelog failure.
3. REST create/read/update and GraphQL reads return the exact closed schema and relationships.
4. A strict YAML preview identifies only the reviewed `aghub-pve`, `agdnsmasq` compute-instance,
   and endpoint-MAC changes; invalid later rows roll the entire import back.
5. The separately approved YAML apply creates/updates exactly those rows, and a repeat import is a
   no-op including stable `last_updated`.
6. A fresh nctl desired snapshot contains the platform, instance, effective defaults/provenance,
   and canonical endpoint MAC.
7. Existing `nctl drift --json`, production inventory render, hosts-intent render, and dnsmasq
   behavior remain correct after the coordinated breaking-schema cutover. Endpoints without
   desired MAC retain their current observed-MAC behavior, without a permanent compatibility
   branch.
8. A fixture with desired MAC but no actual Device/VM can render a deterministic DHCP reservation;
   a conflicting observed MAC is reported and never silently overwrites desired intent.
9. A deployed-reservation mismatch fixture produces a structured `desired_mac_mismatch` finding,
   no deployable dnsmasq artifact/digest, no `dnsmasq_config` action, no Ansible call, and no
   change to the previously deployed digest.
10. Immediately before the coordinated cutover, desired writes are closed and an all-row
    assertion proves no non-null legacy `DesiredNode.realized_vm(+_source)` remains. The final
    nintent migration removes those fields and the matching nctl revision never queries them.
11. Refetch proves that Phase 3 changed no Proxmox guest/resource state, no Phase 2 actual-ledger
    identity/freshness data, no SSH trust store, and no generated file except an explicitly
    invoked render output used as test evidence.

No successful command with an empty result substitutes for these assertions. The report must name
the rows, GraphQL roots, REST endpoints, import actions, nctl snapshot counts, and legacy-field
query result that actually exercised the intended path.

## 2. Phase 3 Exit Criteria

- [ ] `DesiredComputePlatform` exists with exactly the fields and ownership rules in Section 5.2.
- [ ] `DesiredComputeInstance` exists with exactly the fields and ownership rules in Section 5.3.
- [ ] `DesiredEndpoint.mac_address` is nullable, canonical, and unique when non-null.
- [ ] Only provider type `proxmox` and schema version `v1` are accepted.
- [ ] Platform and instance `config` values must be JSON objects; unknown keys and wrong scalar
      types fail on every supported write path.
- [ ] One compute instance per DesiredNode is enforced by both schema and database.
- [ ] A control node cannot be retired, and supported updates cannot retire a node that still
      controls a platform.
- [ ] CPU, memory, disk, and requested VMID bounds are enforced consistently by model, form, REST,
      YAML, and database where representable.
- [ ] An active/approved platform-instance combination resolves exactly one NIC-bearing primary
      endpoint with desired MAC, mDNS name, DNS name when DHCP-reserved, and a usable address
      policy, and resolves effective storage and bridge; zero/multiple candidates or unresolved
      static create inputs fail without list-order fallback.
- [ ] A non-null realized VM can be written only with matching provenance and membership in the
      realized platform Cluster; guest kind and requested VMID conflicts fail closed.
- [ ] Effective lifecycle is computed from the node and platform; the instance has no lifecycle
      column or writable lifecycle API/YAML field.
- [ ] Effective `cluster_name`, storage, and bridge values are visible with
      `instance_override|platform_default|unresolved` provenance without pretending that Phase 3
      has performed actual-state derivation.
- [ ] UI, navigation, forms, filters, tables, detail relationships, REST, GraphQL, YAML preview,
      YAML apply, and Source YAML display cover the new records.
- [ ] Actual-link/source fields are read-only in Phase 3 UI and REST and are rejected by YAML.
      Pure membership/kind/VMID validators are ready for the dedicated Phase 4 link action, but
      normal Phase 3 CRUD cannot write links.
- [ ] nctl reads the final compute schema, preserves all current non-compute behavior, and adds no
      compute drift, compute plan, or Proxmox action. Malformed compute rows are retained as
      scoped source issues rather than stopping unrelated targets.
- [ ] Desired MAC is a real current consumer: dnsmasq uses it before actual observation, falls
      back to existing observed behavior when omitted, and makes a desired/actual mismatch or
      ambiguity non-deployable.
- [ ] `desired_mac_mismatch` has target, severity, bounded evidence, structured JSON drift and
      human-readable CLI drift presentation, and manual-review reconcile classification. A blocked
      diagnostic preview has no authoritative
      artifact or desired digest and can never reach direct apply or reconcile actuation.
- [ ] The final migration asserts the closed-write legacy link count, adds the new schema, and
      removes `DesiredNode.realized_vm(+_source)` in one coordinated breaking rollout. No
      compatibility-only reader, field, alias, or version branch remains.
- [ ] A reviewed and separately approved import seeds only the confirmed `aghub-pve ->
      agdnsmasq` relationship and endpoint MAC. No desired record is generated for the other
      eight observed guests.
- [ ] Repeat import and repeat reads are idempotent and no Proxmox actuation occurs.
- [ ] All applicable tests and environment-backed checks in Section 8 pass.

If the implementation is deployed but the operator has not confirmed the seed MAC/template and
approved the seed write, the phase status is **implemented, not seeded**, not complete. If the seed
is applied but the destructive cutover or a required live UI/API/GraphQL/dnsmasq safety check is
omitted, the status is **partially complete**.

## 3. Scope, Non-goals, and Safety Boundary

### 3.1 In scope

- nintent model fields, migrations, constraints, validation helpers, and inverse-update guards;
- Nautobot forms, tables, filters, views, URLs, navigation, and detail templates;
- REST serializers/viewsets/routes and live API contract checks;
- GraphQL model registration and live query checks;
- strict YAML entries, normalization, reference resolution, preview, transactional import,
  summaries, and repeat-import proof;
- Source YAML display support for the new roots;
- nctl typed desired models/query/builders for compute platforms, compute instances, and endpoint
  MAC;
- nctl effective desired-value/provenance helpers that use desired data only;
- row-scoped desired-source issue diagnostics so malformed compute intent blocks only its target
  or platform dependency scope;
- desired-MAC consumption by dnsmasq with a deployable-versus-blocked result contract;
- the coordinated destructive removal of `DesiredNode.realized_vm(+_source)`;
- documentation and phase reports;
- one reviewed live desired-state seed for `aghub-pve -> agdnsmasq`.

### 3.2 Explicit non-goals

Phase 3 does not:

- create, start, stop, resize, move, clone, replace, migrate, or delete a guest;
- add a Proxmox write credential, API URL, token, vault reference, SSH key, command, or arbitrary
  provider argument to nintent;
- broaden the read-only `nodeutils-pvesh-read` helper;
- change nodeutils collection, nauto Proxmox ingest, Cluster/VM/VMInterface/IP matching, or
  freshness semantics completed in Phase 2;
- add compute-platform or compute-instance drift codes, matching candidates, link plans,
  dependency-closure plans, or reconcile actions (the "dashboard compute tiles" surface this
  non-goal originally also named no longer exists as a target at all, per the supersession note
  above — there is nothing left to avoid adding to it);
- write `realized_cluster` or `realized_vm` for the live seed;
- expose actual-link writes through ordinary UI, REST, or YAML CRUD;
- infer the existing `agdnsmasq` template origin from its running guest;
- copy the Phase 5 disposable-LXC template selection into `agdnsmasq` intent without explicit
  operator confirmation;
- allocate a VMID or MAC;
- infer endpoint selection by sorted order;
- add a second NIC, interface-slot intent, IP/DNS fields in provider config, or multi-NIC mapping;
- add AWS, Azure, generic, custom, or no-op provider choices;
- add cloud-init, a golden-template pipeline, or automatic initial guest access;
- remove `accepted_actual_types` or change the guest-OS observation contract;
- add dual readers/writers, deprecated aliases, shadow fields, old output schemas, fallback
  routes, or any other backward-compatibility-only artifact;
- modify actual-state rows merely to make validation pass; or
- seed desired compute instances for every observed Proxmox guest.

### 3.3 Mutation boundary and approvals

Local code, migrations, fixtures, and tests may be changed during implementation. Live operations
are divided into these gates:

1. **Read-only preflight:** versions, schema, current rows, GraphQL shape, API `OPTIONS`, object
   counts, and file digests. No approval beyond starting the phase is needed.
2. **Breaking-schema maintenance window:** commit the matching nintent/nctl changes, ask the user
   to push nintent, stop desired writes/imports and routine nctl operations, assert the legacy
   link/source count, rebuild/restart the Nautobot image, apply the final migration, and activate
   the matching nctl revision. The agent must not push.
3. **Seed preview:** sync the reviewed YAML revision and run a non-committing preview. This must
   emit exact create/update/unchanged field diffs, not only counts.
4. **Seed apply:** show the preview and before image, then obtain separate explicit approval
   before committing the desired platform, instance, and endpoint MAC.
5. **Resume operations:** only after the final GraphQL/REST/UI/nctl schema smoke tests pass.

No Phase 3 command may target a Proxmox mutation endpoint. No test may weaken SSH verification,
rewrite actual observations, or stop a service to manufacture a path.

## 4. Current Implementation Baseline

The implementation must recheck this baseline at Step 0 and record any change rather than blindly
copying these values.

### 4.1 Revisions and runtime

At plan creation on 2026-07-25:

| Component | Baseline |
|---|---|
| superproject | `f422657d5cb6987a3da61e616ab0ef83ff6a6c04` |
| nintent | `ad9d36397d23c269ad748e13acbccc532fa29f52` |
| nctl | `fd9cb878a1cdab9a436e7d125d2e5697badc1fc4` |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |
| Nautobot / Django | `3.1.3` / `5.2.14` |
| PostgreSQL | `15.17` |
| Proxmox VE | `pve-manager 9.1.1` |

All worktrees were clean before this plan file was added.

### 4.2 nintent

- `DesiredNode.realized_device` and `DesiredNode.realized_vm` are separate nullable actual links,
  each paired with `derived|override` source and XNOR model validation.
- `DesiredEndpoint` owns desired IP/DNS/mDNS but has no MAC field.
- The latest nintent migration is `0014_braindump_exchange_diary.py`.
- There are no desired compute models, forms, tables, filters, views, templates, REST routes, or
  YAML roots.
- The import Job uses one outer `transaction.atomic()` and `_validated_upsert()` calls
  `full_clean()` before save, but its current summary is count-oriented and needs an exact preview
  contract for the live seed gate.
- The fast local nintent test suite is deliberately Django/Nautobot-free. Migration, ORM
  constraint, GraphQL, API, and UI checks therefore require the running Nautobot environment.
- The running plugin is installed from a pushed Git revision during Docker image build. Local
  source edits are not hot-loaded.

### 4.3 Phase 2 actual ledger

Phase 2 is complete. The live actual graph includes:

- Cluster `aghub-proxmox`, id `0ef3f747-b905-42f7-82d8-7e8572e9b63d`;
- nine stable VirtualMachine rows;
- `agdnsmasq`, id `935f0b6f-5926-41e2-80db-bfa4b637cfce`, with
  `proxmox_guest_type=lxc`, `proxmox_vmid=108`, node `aghub`, one joined/configured `net0`,
  MAC `bc:24:11:23:dc:b7`, bridge `vmbr0`, and typed LXC rootfs
  `local-lvm/vm-108-disk-0/8 GiB`;
- complete storage-content evidence containing the operator-selected future disposable-LXC
  candidate `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst`.

That candidate proves template availability for the later Phase 5 fixture. It does not prove the
historical origin of `agdnsmasq` and must not be silently used as its desired template.

### 4.4 nctl

- The desired GraphQL query reads legacy `DesiredNode.realized_vm`.
- `DesiredSnapshot` has no compute platform/instance collections and `DesiredEndpoint` has no
  desired MAC.
- Current node evaluation treats simultaneous Device and legacy VM realization as
  `multiple_realized_links`.
- Production composition supports Device realization and truthfully skips VM-only realization as
  unsupported.
- dnsmasq currently derives DHCP MAC candidates from fresh actual Device/interface facts. It must
  retain that behavior when desired MAC is null.
- Phase 2 added typed actual Cluster/VM/VMInterface evidence and `nctl actual`, but nctl does not
  yet expose storage-content. That accepted Phase 2 residual gap does not block Phase 3 because
  Phase 3 performs no template availability evaluation or actuation.

## 5. Implementation Contracts

### 5.1 Ownership

| Value or operation | Sole owner in/after Phase 3 |
|---|---|
| logical node and guest-OS identity | `DesiredNode` |
| guest-OS Device link | `DesiredNode.realized_device` |
| desired IP/DNS/mDNS/MAC | `DesiredEndpoint` |
| compute-platform intent | `DesiredComputePlatform` |
| compute-instance intent | `DesiredComputeInstance` |
| compute Cluster link/cache | `DesiredComputePlatform.realized_cluster(+_source)` |
| compute VM link/cache | `DesiredComputeInstance.realized_vm(+_source)` |
| configured desired reads | nintent GraphQL |
| confirmed structured writes | nintent REST or transactional YAML import |
| actual Cluster/VM/VMInterface/IP writes | normal nauto nodeutils ingest |
| actual Proxmox collection | nodeutils on the platform control node |
| effective desired default resolution | nctl, from instance override then platform default |
| compute drift/matching/link planning | Phase 4 nctl, absent in Phase 3 |
| Proxmox actuation/credential resolution | Phase 5 nctl/Ansible local config, absent in Phase 3 |
| SSH trust | existing nctl managed known_hosts and explicit enrollment, unchanged |

No field may duplicate another owner's value. In particular, platform/instance config must not
contain endpoint IP, DNS, mDNS, or MAC values, and the instance must not store a NIC slot.

### 5.2 `DesiredComputePlatform`

Use `@extras_features("graphql")` and the existing Nautobot `PrimaryModel` conventions.

| Field | Type and rule | Write/display contract |
|---|---|---|
| `name` | `CharField(max_length=255)`, non-blank | UI/REST/YAML writable |
| `slug` | `SlugField(max_length=255, unique=True)` | stable YAML/config identity |
| `provider_type` | closed choice; only `proxmox`, default `proxmox` | single choice, never accepts future placeholders |
| `lifecycle` | same values/default as `DesiredNode.LIFECYCLE_CHOICES` | UI/REST/YAML writable |
| `control_node` | FK to `DesiredNode`, `PROTECT`, related name `controlled_compute_platforms` | required |
| `config_schema_version` | `CharField(max_length=16, default="v1")`, exact value `v1`, immutable | UI display-only; REST/YAML may omit it or explicitly supply `v1` |
| `config` | `JSONField(default=dict)` with strict platform-v1 validator | JSON edit, typed validation |
| `realized_cluster` | nullable FK to `virtualization.Cluster`, `SET_NULL` | Phase 3 UI/REST read-only |
| `realized_cluster_source` | nullable `derived|override`, not ordinarily editable | Phase 3 UI/REST read-only; present exactly with link |

Platform config v1 admits only:

| Key | Type | Meaning |
|---|---|---|
| `cluster_name` | non-empty string, max 255 | desired scope guard/matching hint |
| `default_storage` | non-empty Proxmox storage identifier, max 255 | instance storage fallback |
| `default_bridge` | non-empty Proxmox bridge identifier, max 255 | instance bridge fallback |

All three keys are optional in the generic model. Missing values remain `unresolved` in Phase 3;
Phase 3 must not claim they were derived from actual state. The live `aghub-pve` seed supplies all
three explicitly from reviewed Phase 1/2 evidence.

Validation and constraints:

- `provider_type == "proxmox"` and `config_schema_version == "v1"`; model default, DB check,
  UI create, REST create, and YAML create all converge to the same persisted `v1`;
- config is a plain JSON object, not null/list/string/number/boolean;
- unknown keys fail;
- values are stripped non-empty strings and are not command fragments;
- `control_node.lifecycle != retired`;
- `realized_cluster` and source satisfy XNOR;
- a change to `realized_cluster` is rejected if any linked instance VM belongs to a different
  Cluster;
- supported `DesiredNode` lifecycle updates cannot retire a node referenced as a control node;
- the database enforces provider/schema fixed values and link/source XNOR where supported, while
  model/service validation enforces cross-row rules.

There is no API URL, username, token ID, TLS option, arbitrary provider payload, or credential
reference.

### 5.3 `DesiredComputeInstance`

Use `@extras_features("graphql")` and `PrimaryModel`.

| Field | Type and rule | Write/display contract |
|---|---|---|
| `desired_node` | `OneToOneField(DesiredNode, CASCADE)`, related name `desired_compute_instance` | sole owner/identity |
| `platform` | FK to `DesiredComputePlatform`, `PROTECT`, related name `desired_compute_instances` | required |
| `instance_kind` | `container|virtual_machine` | required |
| `desired_power_state` | `running|stopped`, default `running` | required/defaulted |
| `vcpus` | positive integer, `1..8192` | MiB/GiB-independent CPU count |
| `memory_mb` | positive integer, `16..2147483647` | exact MiB |
| `root_disk_gb` | positive integer, `1..2147483647` | exact GiB |
| `config_schema_version` | `CharField(max_length=16, default="v1")`, exact `v1`, immutable | UI display-only; REST/YAML may omit or explicitly supply `v1` |
| `config` | `JSONField(default=dict)` with strict kind-aware instance-v1 validator | no arbitrary keys |
| `realized_vm` | nullable FK to `virtualization.VirtualMachine`, `SET_NULL` | Phase 3 UI/REST read-only |
| `realized_vm_source` | nullable `derived|override`, not ordinarily editable | Phase 3 UI/REST read-only; present exactly with link |

The vCPU maximum and VMID bounds follow the installed Proxmox 9 schema. The memory/disk maxima
are the explicit upper bound of the stored positive integer contract; Phase 5 still validates
fresh host/storage capacity before any create. A large but schema-valid request is never evidence
that the platform can satisfy it.

Instance config v1 admits only:

| Key | Type/rule | Consumer |
|---|---|---|
| `vmid` | optional integer `100..999999999`; booleans rejected | identity/collision/create |
| `template` | required non-empty string, max 512 | creation input only |
| `storage` | optional non-empty identifier, max 255 | per-instance override |
| `bridge` | optional non-empty identifier, max 255 | per-instance override |
| `unprivileged` | required boolean for `container`; forbidden for `virtual_machine` | LXC security intent |

For `container`, `template` must use the proven storage-content identity form
`<storage>:vztmpl/<filename>`. The storage prefix does not have to equal effective guest storage:
template storage and root-disk storage are different inputs. For `virtual_machine`, Phase 3
requires a non-empty stable template reference but does not invent a QEMU-specific origin grammar;
Phase 6 must narrow that grammar before QEMU creation becomes actionable.

Validation and constraints:

- one row per DesiredNode, structurally and in the database;
- platform and desired node references are exact and non-null;
- omitted schema version becomes `v1` identically through UI, REST, and YAML; any explicit other
  value fails before save;
- field bounds are enforced by validators and database checks;
- config is a plain object with only the five keys above;
- kind/config rules above are enforced by one shared pure validator;
- requested non-null VMID is unique per platform;
- the preferred database implementation on Django 5.2/PostgreSQL 15 is an expression
  `UniqueConstraint` over platform and the JSON `vmid` value; Step 1 must prove migration
  serialization and duplicate rejection in the real container. If the ORM cannot generate the
  exact constraint, use a reversible migration-owned PostgreSQL unique expression index rather
  than duplicating VMID into a second desired field;
- `realized_vm` and source satisfy XNOR;
- a non-null realized VM requires a non-null platform `realized_cluster` and exact VM Cluster
  membership;
- allowlisted Phase 2 actual identity must agree: container -> `lxc`, virtual_machine -> `qemu`,
  and a requested VMID must equal `proxmox_vmid`;
- no independently stored lifecycle exists.

The link validation is a safety check on a supplied link, not Phase 4 matching. Phase 3 neither
searches for nor writes the live `agdnsmasq` VM link.

### 5.4 Effective lifecycle

Implement one pure helper used by UI display, serializers, YAML validation, and nctl typed desired
state:

```text
if node or platform is retired:
    retired
else if node or platform is deprecated:
    deprecated
else if node or platform is planned:
    planned
else if node and platform are both active:
    active
else:
    approved
```

Actionability in Phase 3 means only whether the desired record is structurally ready for later
create/link/start planning:

| Effective state | Require complete NIC/template contract | Future create | Future start |
|---|---:|---:|---:|
| `active` / `approved` | yes | eligible in Phase 5 | only if desired power is `running` |
| `planned` | no actuation; config still strictly typed | no | no |
| `deprecated` | no actuation; existing rows remain readable | no | no |
| `retired` | no actuation; actual state remains explainable | no | no |

The model always requires capacity and template fields because they are core compute intent, not a
future actuator option. An effective active/approved instance must also resolve effective storage
and bridge from an instance override or platform default and must pass the endpoint actionability
check. A planned/deprecated/retired row may retain unresolved storage/bridge or an incomplete
endpoint as a non-actionable draft. Changing node/platform lifecycle into active/approved must run
the dependent instance validation and fail atomically if any static create input is incomplete.

`desired_power_state=stopped` does not make an active/approved instance structurally
non-actionable: a missing stopped guest may still be created in a later phase, but it must not be
started. Phase 3 plans neither action.

### 5.5 Endpoint MAC and single-NIC contract

Add `DesiredEndpoint.mac_address` as a nullable `CharField(max_length=17)`.

Use one Django-free helper, imported by loader/importer and model/API/form code:

```text
normalize_mac_address(value) -> lower-case colon-separated six-octet string or None
```

Rules:

- null/empty becomes null;
- six hexadecimal octets separated consistently by `:` or `-` are accepted;
- canonical persisted/output form is lower-case colon-separated;
- dotted, short, overlong, mixed-separator, non-hex, list, numeric, and boolean values fail;
- every non-null canonical desired MAC is globally unique;
- the database rejects non-canonical persisted values and duplicate non-null values;
- actual observation never rewrites this field.

For an effective active/approved compute instance, select endpoint candidates only from the owning
DesiredNode. Exactly one candidate must satisfy:

- `endpoint_type == primary`;
- canonical non-null desired MAC;
- non-empty `mdns_name`; and
- a usable address contract.

For the first Proxmox contract, a usable address contract is:

- `dhcp_reserved` with a parseable desired IP, non-empty `dns_name`, and
  `generate_dnsmasq=true`; or
- `static` with a parseable desired IP.

`external` may be stored for ordinary endpoints and planned compute records but does not make an
active/approved compute instance ready for the first create contract. Zero candidates is
`compute_primary_endpoint_missing`; more than one is
`compute_primary_endpoint_ambiguous`. These are structured validation codes/messages in Phase 3,
not Phase 4 drift findings. No sorted-first fallback is allowed.

Inverse supported writes must preserve the invariant:

- changing/removing the selected endpoint MAC, mDNS name, address, policy, type, or node;
- deleting the selected endpoint;
- changing node/platform lifecycle into active/approved; and
- moving the instance to another platform/node

must revalidate the affected compute topology in the same transaction. The same validator rejects
an active/approved instance whose effective storage or bridge is unresolved. Implement the shared
topology validator at the service/model boundary and call it from forms, REST, YAML import, and
supported delete/update views. Tests must not prove only the instance-create direction.

### 5.6 Effective defaults and provenance

Phase 3 resolves only desired-layer precedence:

| Effective value | Resolution |
|---|---|
| `cluster_name` | platform `config.cluster_name`, otherwise unresolved |
| storage | instance `config.storage`, else platform `config.default_storage`, else unresolved |
| bridge | instance `config.bridge`, else platform `config.default_bridge`, else unresolved |
| VMID | instance `config.vmid`, otherwise unresolved (no allocation in Phase 3) |
| MAC | selected DesiredEndpoint `mac_address` |

Each resolved value is represented with:

```json
{
  "value": "local-lvm",
  "provenance": "platform_default"
}
```

Allowed provenance is `instance_override`, `platform_default`, or `unresolved`; `intent` may be
used for the platform's own direct value in platform detail output. Phase 3 must not emit
`derived_actual`, an observation timestamp, or a Cluster/VM candidate because actual matching is
Phase 4.

`cluster_name` and VMID may remain unresolved because later matching/allocation phases have an
explicit safe derivation contract. Storage and bridge are different: an effective
active/approved instance is invalid while either is unresolved. Only a
planned/deprecated/retired non-actionable draft may show unresolved storage/bridge.

The UI instance detail and nctl typed desired diagnostic/test representation must show effective
storage/bridge plus provenance. Do not persist these derived values as additional columns.

### 5.7 UI, REST, and GraphQL

#### UI

Add:

- list/detail/add/edit/delete URLs and views for both compute models;
- forms that expose only intent fields;
- tables with stable identity, lifecycle/effective lifecycle, owner/platform, kind/power, and
  actual-link display;
- filters for slug/provider/lifecycle/control node/platform/desired node/kind/power/realized
  link;
- navigation entries under **Desired State**;
- detail templates `desiredcomputeplatform.html` and `desiredcomputeinstance.html`;
- related-object panels/links: platform -> instances, node -> compute instance/controlled
  platforms, endpoint -> selected compute relation where applicable;
- endpoint form/table/detail/filter support for MAC;
- Source YAML display sections/counts for platforms and instances.

Ordinary forms do not edit actual-link/source fields. Actual links are displayed with provenance.
Keep `tests/test_templates.py` synchronized so a successful create cannot end in a missing
template error. Use explicit edit/delete table buttons if the model lacks a changelog route.

#### REST

Register:

```text
/api/plugins/intent-catalog/compute-platforms/
/api/plugins/intent-catalog/compute-instances/
```

Use ID-based related fields where a hyperlink would require an unregistered viewset. Serializer
validation must:

- call the same config/MAC/topology helpers as the model/importer;
- treat partial update against the merged current+incoming object, not only incoming keys;
- keep schema version immutable;
- default an omitted schema version to `v1` exactly like UI/YAML and reject any explicit other
  value;
- expose actual link/source fields as read-only in the ordinary serializers;
- never accept a writable `lifecycle` on instances; and
- return bounded field-specific errors without raw provider payloads.

Pure link validators still cover Cluster membership, guest kind, requested VMID, and link/source
XNOR for reuse by Phase 4. They are not wired as a Phase 3 CRUD capability. The future Phase 4
dedicated link action owns dry plan, separate approval, exact-scope write, evidence, and refetch.
The live Phase 3 seed leaves both links null.

#### GraphQL

Prove the generated live roots and exact field spellings rather than guessing from Django class
names. The intended roots are:

```graphql
desired_compute_platforms { ... }
desired_compute_instances { ... }
```

The query must include IDs, intent fields, config/schema versions, owner/control/platform
relations, and actual links/sources. Choice values are expected to follow Nautobot's uppercase
GraphQL enum representation and are lowercased only at the nctl boundary.

GraphQL is read-only for this contract. No alternate mutation mechanism is added.

### 5.8 Strict YAML, preview, and transactional import

Add roots:

```yaml
desired_compute_platforms: []
desired_compute_instances: []
```

Identity and references:

| Root | Identity | References |
|---|---|---|
| `desired_compute_platforms` | unique `slug` | `control_node` by DesiredNode slug |
| `desired_compute_instances` | unique `desired_node` slug | platform by platform slug |

Import order is:

```text
intent sources
  -> desired nodes
  -> desired IP ranges
  -> desired endpoints (including MAC)
  -> desired compute platforms
  -> desired compute instances
  -> services/placements/overrides
```

The platform must exist before its instances; the endpoint must exist before an active/approved
instance topology is validated. New platform/instance entries and their nested config mappings
use exact allowed-key sets. Unknown fields, duplicate identities, unresolved references,
wrong types, invalid schema versions, and invalid cross-row topology are load/import errors.
Actual-link/source fields are not YAML keys.

`config_schema_version` is optional on YAML input and defaults to `v1`; an explicit value must be
exactly `v1`. Preview, apply, UI create, REST create, GraphQL output, and repeat import must all
produce the same persisted/output value. No legacy schema-version branch is retained.

Extend the import Job with an explicit preview mode that:

- performs the same parsing, reference resolution, normalization, full validation, and diff
  computation as apply;
- guarantees zero committed writes independent of a UI checkbox default;
- emits deterministic per-object create/update/unchanged records and changed field names/old/new
  bounded values;
- redacts no secret because the schema cannot contain one, but still never logs arbitrary raw
  JSON or credentials;
- includes platform/instance/endpoint-MAC counts and identities; and
- is tested for preview/apply parity.

Apply remains one outer transaction. A failure in the last compute instance must roll back an
earlier endpoint MAC and platform create. A repeat identical import must not call save and must
leave `last_updated` unchanged.

The normal seed owner is `nauto/seed/intent_sources.yaml`. Before adding the live seed, export and
compare the current `aghub`/`agdnsmasq` node and endpoint fields so adding their definitions to the
tracked YAML cannot erase live-only intent. If the canonical file cannot represent the current
rows without unrelated rewrites, stop and record the conflict; do not use an untracked one-off
REST script as a substitute for the transactional seed.

### 5.9 nctl desired snapshot and desired-MAC consumer

Add typed models:

- `DesiredComputePlatform`;
- `DesiredComputeInstance`;
- typed strict v1 config models or validators;
- effective value/provenance representation; and
- `DesiredEndpoint.mac_address`.

Extend the single desired GraphQL query and snapshot builder. Validate:

- unique platform slug;
- one instance per node;
- existing referenced node/platform IDs;
- closed provider/schema/kind/power/source vocabulary;
- strict config types and keys;
- endpoint MAC canonicality/uniqueness; and
- effective active/approved topology completeness.

Validate compute rows independently and retain failures in a typed desired-source issue envelope:

```text
code
target_kind
target_id / target_slug-or-name
severity
scope (target | platform | global)
message
bounded evidence
blocked_consumers
```

An invalid instance blocks that instance. An invalid platform blocks the platform and instances
that reference it. Invalid desired MAC blocks the owning endpoint's DHCP material. Unrelated
nodes/services/endpoints remain readable and renderable. A root/envelope/query failure, a missing
required GraphQL collection, or corruption that makes row identity/scope unknowable remains a
global fetch failure.

No invalid row is silently discarded: diagnostics and counts must distinguish valid, invalid, and
dependency-blocked rows. Phase 4 promotes these source issues into the compute finding vocabulary;
Phase 3 already exposes them to CLI/JSON diagnostics and consumers use them to prevent unsafe
target-local operations.

#### Desired MAC behavior

For DHCP-reserved dnsmasq rendering:

1. If desired MAC is present and the desired endpoint contract is complete, use desired MAC even
   when endpoint evaluation, actual node reference, Device, VM, or interface evidence is absent.
   This permits reservation rendering before a new guest is observable.
2. If desired and all reliable actual candidates agree, use desired MAC and record both
   provenances.
3. If desired and a reliable actual MAC disagree, emit structured
   `desired_mac_mismatch` and make the entire shared dnsmasq managed-file result non-deployable.
4. If desired MAC is absent, preserve the existing observed-candidate behavior byte-for-byte.
5. Multiple conflicting actual candidates remain `ambiguous_interface`, are not overridden
   without explanation, and also make the shared dnsmasq result non-deployable.

For the desired-MAC path, `resolve_dhcp_reservation()` no longer requires
`dhcp_reservation_ready` or exactly one actual reference merely to authorize the desired
reservation. It still requires the desired DHCP fields (`generate_dnsmasq`, eligible lifecycle and
endpoint type, IP, DNS name, DHCP policy, canonical desired MAC). Output evidence uses:

```text
mac_source: desired_endpoint
actual_ref: null                  # when no actual evidence exists
confidence: deterministic_desired
actual_mac_candidates: []        # or the bounded observed candidates
```

It never fabricates an actual reference or claims observed confidence. When desired MAC is absent,
the current evaluation/readiness/one-actual-reference contract remains the single implementation
path; do not retain the old behavior as a version branch.

`desired_mac_mismatch` contract:

| Property | Value |
|---|---|
| target | desired endpoint ID/name plus owning node slug |
| severity | `conflict` |
| scope | target-local diagnosis; shared dnsmasq file deployment is blocked |
| evidence | desired canonical MAC, bounded actual candidates/references, no raw provider payload |
| drift presentation | structured JSON drift finding plus human-readable CLI drift output for the owning node and affected dnsmasq service |
| reconcile classification | `manual_review` |
| remediation | operator corrects desired intent or actual NIC identity; no automatic rewrite |

#### Deployable artifact boundary

The pure renderer returns one of two mutually exclusive states:

```text
deployable
  -> complete authoritative conf bytes + content_sha256

blocked
  -> structured blocking findings + optional diagnostic preview
  -> no authoritative conf artifact and no desired content_sha256
```

Use a new final render/output schema rather than preserving the old success shape. A diagnostic
partial preview is clearly named and cannot be passed to artifact write/deploy code.

- `nctl render dnsmasq --out` must not create or overwrite the output file while blocked.
- `nctl apply dnsmasq`, in dry-run and apply modes, stops before deployable artifact write, SSH
  preflight, or Ansible when render state is blocked.
- drift does not compare a diagnostic partial digest with the deployed digest. It emits the
  blocking finding and cannot produce automatic `service_config_mismatch`/
  `dnsmasq_config` from that partial result.
- reconcile classification is manual review and suppresses the dnsmasq action before executor
  dispatch. The executor/apply boundary independently rechecks deployability as defense in depth.
- the previously deployed managed file and observed digest remain unchanged until the conflict is
  resolved.

This is the one current operational consumer needed to justify the Phase 3 MAC field. Do not
switch production inventory's actual `mac_address` fact to desired intent; production continues
to describe realized facts.

Phase 3 adds this endpoint/dnsmasq safety finding because it is required to prevent an existing
automatic action from deleting a reservation. It still adds no compute target, compute drift,
Cluster/VM matching, link action, or Proxmox plan.

### 5.10 Destructive `DesiredNode.realized_vm` cutover

The final compute-link owner is `DesiredComputeInstance.realized_vm`. Because the repository is in
a coordinated breaking-change phase, implement only the final contract:

- the final nintent migration adds compute models/endpoint MAC and removes
  `DesiredNode.realized_vm` and `realized_vm_source`;
- final nintent forms/tables/filters/serializers/GraphQL contain no legacy fields or aliases;
- the matching nctl revision queries compute models and never queries the removed fields;
- compute realization remains separate from Device guest-OS realization, so a future legitimate
  `realized_device + DesiredComputeInstance.realized_vm` pair cannot become
  `multiple_realized_links`;
- `accepted_actual_types` and its current candidate semantics remain; do not delete that field;
- no dual reader, deprecated model field, fallback query, compatibility serializer, or permanent
  version branch is added.

Before the maintenance window, and again after writes are closed but before migration:

1. assert every legacy link/source is null;
2. if any is non-null, stop the cutover;
3. obtain operator-confirmed compute intent and design an explicit migration that preserves the
   link only after platform membership, guest kind, and stable provider identity are verified;
4. do not invent CPU/memory/disk/template intent from actual facts; and
5. do not retain the legacy field as the workaround.

Close the race by stopping desired UI/API writes, import Jobs/workers, and routine nctl operations
for the maintenance window. The migration repeats the zero/non-null assertion inside its
transaction before dropping columns. Deploy the matching nctl revision before operations resume.
A mismatched old/new pair is unsupported and is never presented as a compatibility state.

Phase 3 still does not evaluate compute convergence. A compute-instance link is carried as typed
desired data for Phase 4, not treated as a second guest-OS actual link.

### 5.11 Seed contract

The reviewed seed proposal is:

```yaml
desired_endpoints:
  - name: primary
    desired_node: agdnsmasq
    endpoint_type: primary
    ip_policy: dhcp_reserved
    ip_address: 192.168.0.2
    mac_address: bc:24:11:23:dc:b7
    dns_name: agdnsmasq.home.arpa
    mdns_name: agdnsmasq.local
    generate_dnsmasq: true

desired_compute_platforms:
  - name: aghub Proxmox
    slug: aghub-pve
    provider_type: proxmox
    lifecycle: active
    control_node: aghub
    config_schema_version: v1
    config:
      cluster_name: aghub-proxmox
      default_storage: local-lvm
      default_bridge: vmbr0

desired_compute_instances:
  - desired_node: agdnsmasq
    platform: aghub-pve
    instance_kind: container
    desired_power_state: running
    vcpus: 1
    memory_mb: 512
    root_disk_gb: 8
    config_schema_version: v1
    config:
      vmid: 108
      template: <operator-confirmed creation intent; do not infer>
      unprivileged: true
```

Before apply, the operator must explicitly confirm:

- the observed MAC is being adopted as desired intent;
- VMID 108, 1 vCPU, 512 MiB, and 8 GiB are desired values, not merely copied actual facts;
- the exact template string is the desired future creation source for `agdnsmasq`; and
- the platform defaults are intentional.

The Phase 5 candidate template is offered as evidence of current availability, not preselected for
this row. If the operator does not choose an `agdnsmasq` template, do not weaken the model or insert
a placeholder; leave the seed unapplied and report the phase status accordingly.

Both actual links remain null in the Phase 3 seed.

### 5.12 Coordinated breaking rollout and rollback contract

The supported sequence is:

```text
nintent final-schema commit + nctl matching-query/consumer commit
  -> automated final-schema and migration tests
  -> ask user to push nintent
  -> open maintenance window and stop desired writes/import Jobs/routine nctl
  -> refetch + in-transaction legacy-link zero assertion
  -> rebuild/restart Nautobot and apply final migration
  -> activate the matching nctl revision
  -> final GraphQL/REST/UI/nctl smoke checks
  -> resume operations
  -> seed YAML preview
  -> explicit seed approval/apply/refetch/repeat
  -> fresh drift/render/dnsmasq safety proof
```

The old and new schema/query pairs are never supported concurrently. The maintenance window makes
the temporary mismatch unavailable to routine operation rather than encoding it as product
compatibility. Record the exact pre-cutover and final revision tuples.

Rollback points:

- before final migration: restore the old image/revision tuple and resume only after verifying the
  old schema is intact;
- after migration but before operations resume: reverse the migration and restore the complete old
  revision tuple, or fix forward to the complete final tuple; never run a mixed pair;
- immediately before seed apply: retain a before image of the endpoint and all relevant desired
  rows; reverse only through a reviewed transactional YAML/REST plan;
- after operations resume: rollback still means the whole matching revision/schema tuple, not a
  legacy field, dual reader, or alias.

No rollback step modifies Proxmox or actual Cluster/VM rows.

## 6. Deliverables

### 6.1 Expected code and documentation surfaces

| Repository | Expected surfaces |
|---|---|
| nintent | `models.py`, shared validators/topology helper, migrations, forms, tables, filters, views, URLs, navigation, templates |
| nintent | API serializers/viewsets/routes |
| nintent | loaders, importer projections, import Job preview/apply summaries, Source YAML display |
| nintent | Django-free tests plus environment-backed ORM/API/GraphQL/UI checks |
| nctl | desired GraphQL query/models/builders, schema validation, effective defaults/provenance |
| nctl | row-scoped desired-source issue envelope and target/platform isolation tests |
| nctl | dnsmasq desired-MAC selection, deployability gate, finding/classification, and multi-round safety tests |
| nctl | drift/CLI output updates for the final blocked/deployable schema (retained JSON/human drift and reconcile/ops evidence only; no dashboard or serve output) |
| nctl | final removal of legacy query/consumer code |
| nauto | reviewed `seed/intent_sources.yaml` additions only after exact live-row comparison |
| root docs | this plan and one report per procedure step, with final exit-criteria report |
| README docs | user/developer model, YAML/API examples, rollout/recovery boundaries |

No nodeutils, ansible_agdev, nauto Proxmox ingest, or Proxmox helper code change is expected. Any
need to change one of those surfaces stops the step and requires a scoped plan amendment.

### 6.2 Evidence handling

Store raw live/API/schema evidence under a git-ignored directory such as:

```text
.local/vm-p3/<timestamp>/
```

Use mode `0700` for directories and `0600` for files. Reports may contain stable public UUIDs,
counts, schema names, validation codes, digests, and selected non-secret desired values. They must
not contain:

- the Nautobot token or `.local/secrets` contents;
- raw authentication headers;
- private keys or raw SSH public-key blobs;
- Braindump bodies or private operator prose;
- unrestricted provider payloads; or
- full database dumps.

Record evidence retention owner/date in the final report.

## 7. Procedure

### Step 0 — Safety preflight and current contract snapshot

1. Record root/submodule HEADs, upstream status, and dirty files.
2. Confirm `.local/secrets` is ignored and never print its contents.
3. Record Nautobot/Django/PostgreSQL/Proxmox versions.
4. Capture migration list and `makemigrations --check --dry-run`.
5. Refetch current DesiredNode/DesiredEndpoint rows needed for `aghub` and `agdnsmasq`, including
   IDs, current values, actual links, sources, and `last_updated`.
6. Assert the live non-null legacy `DesiredNode.realized_vm` count and record every non-null row if
   it is no longer zero.
7. Refetch actual Cluster/VM identity and freshness for `aghub-proxmox`/`agdnsmasq`.
8. Capture current GraphQL schema/root results, REST `OPTIONS`, nctl desired/drift JSON schema,
   and deterministic render digests.
9. Capture generated inventory/dnsmasq/known_hosts digests and Proxmox guest identity/resource
   summary using read-only paths.
10. Confirm no active conflicting migration/import Job is running.

Gate: all baseline reads succeed, no secret is captured, and any discrepancy from Section 4 is
explained before schema work.

### Step 1 — Implement shared pure contracts and prove database mechanisms

1. Implement provider/schema/config/MAC/effective-lifecycle/effective-default helpers in a
   Django-free module.
2. Add focused pure tests for every valid/invalid key, type, bound, normalization, and provenance
   path.
3. In the Nautobot 3.1.3/Django 5.2.14/PostgreSQL 15 environment, spike the platform+JSON-VMID
   uniqueness constraint in a disposable test migration/table.
4. Prove VMID 100 and 999999999 pass, adjacent values fail, duplicate same-platform VMID fails,
   and the same VMID on a second platform passes.
5. Verify the Proxmox 9 provider bounds against the installed or official schema and record the
   source; do not derive a maximum from the current live VMIDs 100-108.

Gate: one reviewed constraint implementation is selected and reversible before the real model
migration is authored.

### Step 2 — Add the final models and destructive migration

1. Add `DesiredComputePlatform`, `DesiredComputeInstance`, and endpoint MAC.
2. Implement model validation, DB constraints, relation names, URLs, string representations, and
   `config_schema_version="v1"` model defaults/checks.
3. Add inverse-update/delete topology validation for supported paths, including DNS name and
   effective storage/bridge readiness.
4. Remove legacy DesiredNode VM fields from the final models and author migration `0015_...` to
   add the final schema, assert legacy rows, and drop the obsolete columns.
5. Add environment-backed ORM tests for constraints and cross-row validation.
6. Run migration forward/backward/forward against a disposable or backed-up local database state.
7. Prove the forward migration stops before dropping columns when a legacy link/source fixture is
   non-null.
8. Prove successful migration creates zero compute rows and synthesizes no desired intent.

Gate: the migration is reversible, refuses data loss, and leaves only the final ownership model.

### Step 3 — Add UI, REST, and GraphQL surfaces

1. Add forms/tables/filters/views/URLs/navigation/templates and endpoint MAC exposure.
2. Keep actual-link fields out of ordinary edit forms and make them read-only in REST.
3. Add REST serializers/viewsets/routes with merged partial-update validation.
4. Register both models for GraphQL.
5. Extend template-existence and Django-free surface tests.
6. Run live environment tests against a disposable transaction/rows.
7. Prove list/detail/edit validation errors and related-object panels.
8. Prove UI/REST/YAML omitted/explicit schema-version parity, REST create/get/patch/error behavior,
   REST link-write rejection, and GraphQL roots/enum values.

Gate: every supported UI/API/read path is positively exercised; a 200 response with empty roots is
not sufficient.

### Step 4 — Add strict YAML preview and transactional import

1. Add loader dataclasses, strict normalizers, duplicate checks, roots, and reference resolution.
2. Add importer identity/default projections and counts/details.
3. Extend the Import Intent Sources Job with explicit preview and exact diff output.
4. Add Source YAML display sections.
5. Test strict unknown fields, invalid types, references, bounds, lifecycle/topology, MAC
   normalization/collision, and actual-link-key rejection.
6. Test import order and last-row failure rollback.
7. Test preview/apply parity and repeat-import `last_updated` stability in a real transaction.

Gate: the same planned operations are produced by preview and apply, and a deliberately invalid
last instance leaves zero preceding writes.

### Step 5 — Add the final nctl desired schema and scoped source issues

1. Extend the desired GraphQL query.
2. Add typed platform/instance/config/effective-value models and endpoint MAC.
3. Remove every legacy field query/builder/evaluation/production consumer and test fixture.
4. Add row-scoped source-issue parsing and platform dependency blocking.
5. Keep valid compute collections out of compute drift/planner/reconcile dispatch.
6. Add invalid-instance, invalid-platform, invalid-MAC, duplicate/reference, and global-envelope
   fixtures.
7. Prove a malformed compute sibling blocks only its target/platform while an unrelated healthy
   node's read/render succeeds.
8. Prove only root/envelope/identity-unknowable corruption fails the whole snapshot.
9. Add a future dual Device+compute-VM fixture proving compute realization is not passed to the
   guest-OS `multiple_realized_links` path.

Gate: nctl reads only the final schema, reports every invalid row truthfully, and preserves
unrelated targets without adding a compute action.

### Step 6 — Make desired MAC a safe dnsmasq consumer

1. Pass endpoint desired MAC through the dnsmasq snapshot adapter.
2. Implement desired/no-actual, desired=actual, desired!=actual, desired-absent, and
   actual-ambiguous rules.
3. Implement the deployable-versus-blocked result and final render envelope.
4. Wire the structured mismatch finding into JSON drift and human-readable CLI drift output, with
   manual-review classification, drift digest suppression, planner suppression, and
   direct-apply/executor rechecks (zero SSH calls, zero Ansible calls).
5. Prove through the real `SourceSnapshot -> compute_dnsmasq_render()` path that a complete
   desired endpoint with no endpoint evaluation, actual reference, Device, VM, or interface emits
   the reservation with null actual provenance.
6. Prove desired-absent endpoints still use the current actual-evaluation path.
7. With a fixture containing an already deployed reservation/digest, introduce mismatch and
   ambiguity and run dry plan/apply/reconcile rounds. Assert no deployable artifact/digest,
   output overwrite, SSH preflight, Ansible call, or deployed digest change.
8. Resolve the fixture conflict and prove a subsequent round becomes deployable and does not
   repeat after observed digest convergence.

Gate: a blocked diagnostic preview can never become an authoritative artifact or automatic
dnsmasq action.

### Step 7 — Pre-cutover review and matched commits

1. Run all nintent and nctl suites plus configured lint/type/diff checks.
2. Review config-key closure, schema-version parity, target isolation, migration reversibility,
   dnsmasq safety, and secret handling.
3. Search active code/tests for legacy field names, dual-read branches, aliases, and old render
   output schemas; only migration history and historical reports may retain them.
4. Commit nintent final-schema work in a reviewable unit.
5. Commit nctl final-query/consumer/render work in a reviewable unit.
6. Ask the user to push nintent; do not push on the user's behalf.
7. Record the exact matched revision tuple and rollback tuple.

Gate: both final revisions are ready before the maintenance window begins; no compatibility-only
artifact remains.

### Step 8 — Coordinated breaking deployment

1. Start the maintenance window: stop desired UI/API writes, import workers/Jobs, and routine nctl
   operations.
2. Refetch and assert all legacy link/source rows are null. If not, stop and restore operation
   without migrating.
3. Back up the affected database schema/rows and record migration rollback commands.
4. Rebuild/restart Nautobot from the exact pushed nintent revision.
5. Run the migration; require its in-transaction legacy assertion and exact final schema.
6. Activate the matching nctl revision before routine operations resume.
7. Prove final GraphQL roots, REST/UI behavior, migration state, desired snapshot, drift,
   production, hosts-intent, dnsmasq read path, `nctl ops list`/`nctl ops show` evidence for an
   existing operation, and dry reconcile.
8. Confirm ordinary REST/YAML/UI paths cannot write actual links.
9. Resume operations only after every smoke test passes.

Gate: only the final matched schema/query pair is exposed; no desired compute row exists yet.

### Step 9 — Prepare and review the canonical live seed

1. Compare `nauto/seed/intent_sources.yaml` against live `aghub`/`agdnsmasq` rows field by field.
2. Add only definitions that reproduce the current node/endpoint intent plus the proposed MAC and
   compute roots.
3. Ask the operator to confirm MAC, capacity, VMID, platform defaults, and exact template string.
4. Commit the reviewed nauto seed change and ask the user to push.
5. Sync the Nautobot Git Repository to the exact pushed nauto revision.
6. Capture a before image of affected desired rows and actual-link fields.
7. Run explicit preview; assert exact create/update/unchanged identities and no unrelated diff.
8. Show the preview and stop for separate apply approval.

Gate: no placeholder remains, the canonical YAML would not erase live-only fields, and the
preview contains only the intended rows.

### Step 10 — Apply, refetch, and prove repeat import

After explicit approval:

1. Run the same import in apply mode against the same source revision/digest.
2. Assert the endpoint MAC update, platform create, and instance create actually occurred.
3. Refetch through ORM/REST/GraphQL and compare exact IDs/fields/relations.
4. Fetch nctl desired snapshot and assert one platform/instance plus effective value provenance.
5. Assert both new actual links are null and the legacy fields are absent.
6. Run the identical import again.
7. Assert zero creates/updates and stable `last_updated` for all affected rows.
8. Run dnsmasq render and assert the desired MAC source and expected reservation.
9. Run fresh drift/production/hosts-intent checks and separate unrelated drift from Phase 3
   regressions.

Gate: exact rows changed once, repeat is a no-op, and no compute/Proxmox action was planned.

### Step 11 — Environment-backed dnsmasq safety and target-isolation proof

1. Run a non-mutating environment-backed desired-only render from a complete disposable desired
   endpoint and assert no actual provenance is fabricated.
2. Run the deployed code against a disposable/simulated managed-file fixture containing an
   existing reservation, then introduce desired/actual mismatch.
3. Assert the structured finding reaches JSON drift, human-readable CLI drift output, and
   manual-review reconcile classification.
4. Run direct apply dry-run/apply and reconcile dry/apply with fake command boundaries; assert
   zero SSH/Ansible calls, no dnsmasq action, and stable deployed bytes/digest (this is the
   zero-actuation proof for this fixture).
5. Include a malformed planned compute instance beside a healthy unrelated live-like node and
   prove only the malformed target is blocked.
6. Re-run the ordinary live dnsmasq render without changing desired intent and verify no
   unexpected blocker/regression.

Gate: both the destructive-risk boundary and target-local source issue behavior are proven above
unit-helper level.

### Step 12 — Final verification, non-actuation audit, and report

1. Run every repository command and scenario in Section 8.
2. Compare root/submodule status and deployed revisions with Step 0.
3. Compare actual Cluster/VM/VMInterface/IP identities and freshness semantics; ordinary newer
   read-only observation times are distinguished from mutation.
4. Compare Proxmox guest set, VMID, kind, power, CPU, memory, rootfs, and interface/MAC evidence.
5. Compare generated artifact and SSH known_hosts digests.
6. Confirm no credentials/raw private prose/provider payload entered tracked files or reports.
7. Record raw-evidence retention owner/date.
8. Evaluate every Section 2 criterion as met/unmet/not applicable with evidence references.
9. State `complete`, `partially complete`, or `implemented, not seeded` precisely.

Gate: Phase 3 is complete only if the environment-backed path, approved seed, repeat proof,
destructive cutover, dnsmasq non-deployment proof, target isolation, and no-actuation audit all
passed.

## 8. Verification Plan

### 8.1 Repository commands

The implementation report must use the repositories' documented environments and record exact
commands/results. At minimum:

```bash
# repository root
git status --short
git submodule status
git diff --check

# nintent fast Django-free suite
cd nintent
python3 -m unittest discover -s nautobot_intent_catalog/tests

# nctl
cd ../nctl
uv run pytest

# running Nautobot environment after pushed image rebuild
nautobot-server makemigrations nautobot_intent_catalog --check --dry-run
nautobot-server showmigrations nautobot_intent_catalog
nautobot-server migrate nautobot_intent_catalog
```

Add the repository-standard formatter/linter/type checks discovered at implementation time; do
not invent a command that is not configured. Run migration/ORM/API/GraphQL/UI tests inside the
Nautobot environment because the local nintent suite does not import Django/Nautobot.

### 8.2 Required scenario matrix

| Area | Required cases |
|---|---|
| platform schema | valid empty/partial/full config; unknown key; non-object; wrong types; blank identifiers; omitted/explicit/wrong schema version; immutable persisted version |
| platform control | valid active node; retired control node; retire-after-reference inverse update; protected delete |
| platform link validator/authorization | pure null/link/source/membership cases; ordinary UI/REST/YAML write rejection |
| instance schema | container and VM; unknown key; wrong types; boolean-as-VMID; kind/unprivileged rules; missing template; omitted/explicit/wrong schema version |
| numeric bounds | each minimum/maximum and adjacent invalid value for CPU/memory/disk/VMID |
| uniqueness | one instance/node; duplicate platform slug; duplicate same-platform VMID; same VMID different platform |
| instance link validator/authorization | pure correct Cluster/kind/VMID and conflict cases; ordinary UI/REST/YAML write rejection |
| lifecycle | all planned/approved/active/deprecated/retired node/platform combinations; no instance lifecycle input; stopped power does not authorize stop |
| endpoint MAC | null; colon/hyphen input normalization; uppercase; invalid/mixed/dotted; duplicate; DB canonical check |
| topology | exactly one candidate; zero; multiple; foreign-node endpoint; no mDNS; DHCP without DNS name/IP/dnsmasq; external; static; effective storage/bridge missing; inverse update/delete; lifecycle activation |
| UI | list/add/edit/detail/delete; related links; filters; endpoint MAC; actual-link display-only; template presence |
| REST | list/create/get/patch; partial merged validation; FK IDs; schema-version default parity; link read-only; errors; repeat |
| GraphQL | non-empty roots; exact fields/relations/enums; null links; no legacy fields |
| YAML | strict roots/entries/config; schema-version default parity; duplicates/references/order; actual-link rejection; preview/apply parity; last-row rollback; repeat no-op |
| nctl desired | empty collections; full live-like row; malformed instance sibling isolation; malformed platform dependency scope; invalid MAC endpoint scope; duplicate/ref errors; root/global failure; effective provenance |
| dnsmasq desired-only | actual node/evaluation/Device/VM/interface absent; reservation emitted; `actual_ref=null`; desired provenance; real `SourceSnapshot -> compute_dnsmasq_render()` |
| dnsmasq safety | deployed reservation + desired/actual mismatch or ambiguity; structured conflict; diagnostic-only preview; no authoritative digest/output overwrite/apply/reconcile/SSH/Ansible; deployed digest unchanged; recovery round |
| breaking rollout | writes closed; pre-migration and in-transaction legacy assertions; non-null fixture stops; matched final schema/query; rollback as whole tuple; no compatibility artifacts |
| live seed | exact preview; approved apply; REST/GraphQL/nctl refetch; repeat no-op; null actual links; no unrelated guest desired rows |
| non-actuation | no Proxmox change; no helper widening; no SSH trust change; no actual-ledger rewrite |

### 8.3 Positive evidence requirements

The phase reports must positively assert:

- migrations and constraints actually ran;
- the intended UI/REST/GraphQL/YAML paths returned the expected non-empty objects;
- preview named the exact seed field changes;
- apply created/updated the exact intended objects;
- repeat import attempted the same source and made zero writes;
- nctl actually read the new roots and endpoint MAC;
- the desired-MAC no-actual renderer path actually emitted the expected line;
- the mismatch path produced no authoritative artifact/digest or dnsmasq action, invoked no
  SSH/Ansible boundary, and preserved existing deployed bytes/digest;
- malformed instance/platform/MAC rows remained visible as scoped issues while an unrelated
  healthy target continued;
- the legacy field was absent from the final live GraphQL schema/query and all legacy rows were
  proven null after writes closed and again inside migration;
- no compatibility-only field, alias, route, reader/writer, serializer, fixture, or output-schema
  branch remained;
- no compute/Proxmox action appeared in drift/reconcile; the endpoint MAC conflict was classified
  manual review;
- no Proxmox state changed.

An empty compute collection immediately after cutover is useful final-schema smoke evidence, not
proof of the seeded path. A null link is expected Phase 3 behavior, not a failed link test.

## 9. Sequence and Dependencies

```text
Phase 1 frozen desired contract
  + Phase 2 complete actual ledger
  -> Step 0 live baseline
  -> Step 1 pure validators + DB mechanism proof
  -> Step 2 final models + destructive migration
  -> Step 3 UI/REST/GraphQL
  -> Step 4 YAML preview/import
  -> Step 5 final nctl schema + scoped issues
  -> Step 6 desired-MAC + dnsmasq deployability gate
  -> Step 7 matched final commits
  -> Step 8 coordinated breaking deployment
  -> Step 9 reviewed seed preview
  -> Step 10 approved seed + repeat proof
  -> Step 11 environment-backed safety/isolation proof
  -> Step 12 final audit/report
```

Do not write seed data before the final matched deployment and preview path are proven. Do not
open the breaking migration window until both nintent and nctl final revisions are ready and
desired writes can be closed. Do not begin Phase 4 link planning until the final Phase 3 schema
and nctl desired snapshot are stable.

## 10. Phase Handoff

Phase 3 hands Phase 4:

- stable desired platform/instance IDs and strict v1 config;
- a canonical desired endpoint MAC and one explicit NIC-bearing endpoint;
- effective lifecycle and desired default provenance;
- a typed nctl desired snapshot with compute realization separate from guest-OS realization;
- Phase 2 stable actual Cluster/VM identities and freshness;
- no legacy `DesiredNode.realized_vm` owner;
- one seeded but deliberately unlinked `aghub-pve -> agdnsmasq` relationship;
- a proven transactional structured-write path and rollback point; and
- no Proxmox actuation capability.

Phase 4 may then implement actual matching, compute findings, structured CLI/drift/reconcile
evidence, scoped dependency closure, dry link plans, and separately approved Cluster/VM link
writes. It must not
reinterpret Phase 3's seed as permission to actuate a guest, infer a missing template, or create
desired rows for unexplained actual guests.

Phase 5 remains responsible for least-privilege ensure-present/start actuation, fresh template
availability checks through the Phase 2 ledger, collision checks, action dependency ordering,
post-create observation, and the manual-initial-access/SSH-enrollment safe stops.
