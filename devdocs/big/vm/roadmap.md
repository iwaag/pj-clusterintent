# VM Platforms and Proxmox Guest Reconciliation — Development Roadmap

## Purpose

Make a virtualization platform an explicit part of cluster intent so a desired node can state
where and how it should be realized, and so `nctl reconcile` can eventually create and verify that
realization.

The first concrete platform is the Proxmox VE installation on `aghub`. The existing
`agdnsmasq` LXC is the initial read-only relationship to model and prove. A new disposable LXC,
followed later by a QEMU VM, provides the first creation paths.

This initiative does not attempt to design AWS or Azure support. It establishes only the small
platform/instance boundary justified by the current Proxmox use case. Guidance for adding another
provider later belongs in `README_DEV.md`, not in speculative fields, enum values, schemas, or
adapters in this initiative.

Phases in this roadmap begin at Phase 1 intentionally. Concrete implementation plans and reports
should live under `devdocs/big/vm/pN/` when each phase is started.

## Current state and the gap

Several pieces already exist, but they do not yet form a desired-versus-actual control loop:

- `DesiredNode` can classify a node as `device`, `virtual_machine`, `container`, or
  `service_host`, and can link to either a Nautobot Device or VirtualMachine.
- `nintent/CONCEPT.md` illustrates a Proxmox host and VM as separate desired nodes and places
  `hypervisor`, `vcpu`, and `memory_gb` in `DesiredNode.expected_spec`.
- The current node evaluator consumes only the identity-oriented `expected_spec` keys for
  hostname, serial, UUID, and platform. The illustrated hypervisor and capacity keys have no
  deterministic drift or reconcile effect.
- A DesiredNode linked to both a Device and a VirtualMachine is currently a
  `multiple_realized_links` conflict.
- nodeutils already collects Proxmox cluster, node, QEMU, LXC, VMID, resource, state, interface,
  storage, and network information through the read-only `pvesh` boundary.
- LXC guests are represented as Nautobot VirtualMachines because Nautobot has no dedicated LXC
  model; `proxmox_guest_type=lxc` distinguishes them.
- The normal nauto nodeutils ingest path does not yet materialize `facts.proxmox` into Nautobot
  Cluster, VirtualMachine, or VMInterface objects.
- nctl's actual-state query currently reads only VirtualMachine identity (`id` and `name`), and
  production composition still treats a realized VirtualMachine as unsupported.

`agdnsmasq` exposes the central modeling problem. It has two legitimate actual identities:

1. the guest operating system observed by nodeutils and represented as a Nautobot Device; and
2. the LXC compute resource observed from `aghub` and represented as a Nautobot VirtualMachine.

These are different layers, not competing candidates for one realization slot. The desired model
must preserve that distinction.

## Governing decisions

### 1. Separate managed-node identity from compute realization

`DesiredNode` remains the logical managed node and guest-OS identity. Its existing
`realized_device` relationship continues to answer:

> Which observed operating-system host realizes this managed node?

A new desired compute-instance record answers:

> Which observed Proxmox guest resource realizes the compute needed by this managed node?

The compute-instance record owns its own `realized_vm` link. Therefore one desired node may
correctly have both a Device-level observation and a VirtualMachine-level compute realization
without producing `multiple_realized_links`.

Do not add a generic `parent_node` field to `DesiredNode`. Hosting is a typed compute-placement
relationship with platform, lifecycle, resource, power, and provider-specific semantics. A bare
parent edge would be ambiguous for Proxmox clusters and would conflate hosting with other future
node relationships.

### 2. Add only fields with a demonstrated intent consumer

New models are not inventories of every value Proxmox can report or configure. A field is admitted
only when the implementation plan names at least one current consumer in one of these categories:

- it changes deterministic candidate matching or drift;
- it changes a reconcile plan or actuation payload;
- it is required to safely create or address the intended resource; or
- it is a stable actual link or provenance value required to prove convergence.

Every proposed persisted field must be classified as one of:

- **Intent** — a user choice that changes the desired result;
- **Derived** — computed from other authoritative inputs and shown with provenance; or
- **Actual link/cache** — a stable link or freshness marker derived from observation, never
  presented as user intent.

Do not store a value merely because the Proxmox API exposes it. In particular, raw provider
responses, uptime, utilization, storage lists, network lists, migration history, task history,
replication data, HA state, NUMA details, arbitrary QEMU arguments, and every available device
option remain outside the desired models until a real intent/reconcile need appears.

JSON configuration is a strict, versioned object with a closed key set. Unknown keys fail
validation; it is not an escape hatch around model design.

### 3. Model only Proxmox now

The only provider kind introduced by this initiative is `proxmox`. Do not add unused `aws`,
`azure`, `generic`, or `custom` choices, provider schemas, placeholder fields, or no-op adapters.

The model names may use the compute-platform vocabulary because that accurately describes the
current domain boundary. This naming does not require pretending that different providers share
configuration semantics that have not been tested.

### 4. Keep network identity under DesiredEndpoint

`DesiredEndpoint` remains the sole owner of desired IP address, DNS name, mDNS name, and IP policy.
The Proxmox instance config may select a bridge, but it must not duplicate desired IP/DNS values.

Add an optional desired MAC address to `DesiredEndpoint` only because it has two concrete
consumers:

- dnsmasq must be able to render a DHCP reservation before a new guest is observable; and
- the Proxmox creator must configure the guest NIC with that same stable MAC.

When the MAC is omitted, the existing observed/derived behavior remains. Do not invent or persist a
MAC during a read-only render. If creation requires a MAC, allocation must be an explicit,
deterministic planning/write step with collision checking and recorded evidence.

The first Proxmox creation contract supports exactly one guest NIC. A DesiredComputeInstance must
resolve exactly one NIC-bearing primary DesiredEndpoint with a desired MAC and mDNS name. The
effective bridge comes from the instance override or platform default, and the provider adapter
derives the single Proxmox NIC slot (`net0`/the corresponding guest interface) as execution
mechanism rather than storing it as another intent field.

Other logical service endpoints may still exist on the node, but a second primary/NIC-bearing
endpoint is an ambiguity and blocks guest creation. The implementation must not reuse the current
bootstrap selector's sorted-first fallback for this decision. Multi-NIC support is outside the
first contract; when a real case requires it, design an explicit endpoint-to-compute-interface
mapping rather than adding implicit list ordering or duplicating endpoint data in provider config.

### 5. Use Nautobot native virtualization objects as the actual ledger

Normal nodeutils collection from the Proxmox control node remains the observation source. The
normal nauto ingest path materializes supported observations into:

- one Nautobot Cluster for the observed Proxmox scope;
- one Nautobot VirtualMachine for each observed QEMU or LXC guest; and
- VMInterface/IP relations only when the source is reliable enough to avoid guessing.

Provider identity and freshness use a minimal allowlist of dedicated fields, such as Proxmox VMID,
guest kind, owning Proxmox node, raw power status, and observation time. Do not make nctl consume
the unrestricted `inventory_raw_json` blob.

The current QEMU normalizer cannot be used unchanged for interface ingest: when any guest-agent
interfaces are returned it replaces the configured NIC list, losing configuration-side bridge and
NIC-slot evidence. Phase 2 must revise the nodeutils observation schema so configured interfaces
and guest-agent interfaces retain separate provenance. They may be joined only by a unique,
normalized MAC match. Missing or duplicate MACs and unmatched/partial agent results remain
explicitly unmatched; they are never paired by list order or interface name guesswork.

Capacity evidence needs the same precision. The current aggregate `maxdisk` value must not be
called `root_disk_gb` or used to authorize disk growth. LXC root-disk observation must come from
the parsed `rootfs` volume/config evidence. QEMU root/boot-disk comparison remains unsupported
until Phase 6 selects and proves an exact source. Likewise, Phase 5 template validation must use
fresh Proxmox storage-content observation for the selected node/storage (the narrowly allowlisted
`/nodes/{node}/storage/{storage}/content` read path), not merely the existence of a storage name or
an unchecked desired string.

An observed guest missing from desired state is **unexplained**, not automatically unwanted.
Observation and ingest never delete it. Automatic guest deletion is outside this roadmap.

### 6. Keep credentials and execution mechanism outside nintent

nintent records non-secret intent. It must not store Proxmox passwords, API tokens, ticket
material, private keys, vault references that reveal a secret, or executable command fragments.

The platform slug is the stable non-secret key used by nctl/Ansible configuration to resolve the
approved actuator and credential. A concrete phase plan must choose and verify the least-privilege
write boundary. The current `pvesh` helper is intentionally read-only and must not be broadened
casually into a general root command path.

### 7. Preserve the Braindump authority boundary

Braindump and Alignment Review prose remains non-executable. A wish such as “create a small Debian
LXC on aghub” may produce an exact structured proposal, but only a confirmed proposal creates or
updates nintent records. A separate reconcile apply confirmation authorizes actuation.

The assisted path should be convenient for the single operator, but convenience must come from
one clear proposal/accept operation rather than treating arbitrary prose as an actuator input.

### 8. Start non-destructively

The first actuator supports ensure-present and start. Resource differences are visible before they
become mutable. Shrink, move, replace, stop, and delete operations remain manual/unsupported until
each receives its own safety and evidence design.

Retiring a desired record does not imply deleting its Proxmox guest. Absence from desired state
never authorizes deletion.

### 9. Make manual initial guest access an explicit resumable contract

A created and powered-on guest is not yet observable at the guest-OS layer through the current
nodeutils path. Before guest-OS observation can run, the guest must have:

- the shared Ansible user selected by the existing inventory/vault configuration;
- that user's approved SSH public key and the required privilege path;
- a running SSH service;
- a running mDNS service advertising the selected primary endpoint's `mdns_name`; and
- an SSH host key verified and enrolled under the stable DesiredNode alias.

These are operational bootstrap requirements, not additional per-instance intent fields. The
first LXC and QEMU creation slices do not automate them. After create/start and fresh Proxmox
observation, reconcile returns `waiting_for_manual_initial_access`; an operator uses an
authenticated Proxmox console or another approved out-of-band route to configure and check the
guest. No user, key, privilege, SSH, mDNS, hostname, or host-key property is inferred from an OS
template.

This manual gate keeps the first implementation focused on the Proxmox management loop. Selection
of a golden template, cloud-init profile, OpenTofu workflow, bounded Proxmox provisioning action,
or other automatic bootstrap mechanism is deferred until the LXC and QEMU compute-management
paths have been proven. A later decision may keep the manual procedure if its operational cost
does not justify another actuator.

Network scanning alone never verifies a new SSH key. After creation, reconcile may report the
offered public fingerprints, but trust requires an existing supported source: a previously trusted
ordinary known_hosts entry or an out-of-band verified fingerprint. The expected state transition
is:

```text
created and started
  -> freshly observed and linked at the compute layer
  -> waiting_for_manual_initial_access (safe, resumable stop)
  -> operator establishes and checks user/key/privilege/SSH/mDNS/hostname/unique host keys
  -> bootstrap route reachable and offered fingerprints visible
  -> waiting_for_ssh_enrollment (safe, resumable stop)
  -> explicit fingerprint verification and `nctl ssh enroll`
  -> guest observation resumes in a later reconcile
```

Both safe stops preserve successful create/start and compute-observation evidence. Neither is a
failed create, and reconcile must not recreate the guest merely because manual initial access is
incomplete. It must never bypass SSH enrollment with `accept-new`, disabled strict checking, or an
unverified keyscan result.

### 10. Inherit compute lifecycle from the owning DesiredNode

`DesiredComputeInstance` has no separate lifecycle because no independent lifecycle consumer is
currently justified. Its effective lifecycle is `desired_node.lifecycle`, further gated by the
platform lifecycle. This keeps one owner for whether the logical node should enter production.

The initial behavior is:

| Effective state | Observe/evaluate existing guest | Explicit ledger link | Create | Start |
|---|---:|---:|---:|---:|
| node and platform `approved`/`active` | yes | yes | yes | only when `desired_power_state=running` |
| either side `planned` | yes | only after explicit review | no | no |
| either side `deprecated` | yes | only after explicit review | no | no |
| either side `retired` | yes, to explain retained actual state | no automatic link | no | no |

`desired_power_state=stopped` suppresses start; automatic stop remains unsupported. Removing the
instance record, retiring its node/platform, or changing lifecycle never authorizes stopping or
deleting an actual guest.

## Minimal desired data contract

Field names may be refined by the Phase 1 contract review, but the semantic set must stay within
this boundary unless a concrete consumer justifies an addition.

### `DesiredComputePlatform`

Represents the Proxmox scope capable of realizing desired compute instances.

| Field | Class | Reason it exists |
|---|---|---|
| `name` | Intent | Human-readable platform identity |
| `slug` | Intent | Stable reference from desired instances and actuator configuration |
| `provider_type` | Contract | Selects the strict Proxmox schema/adapter; only `proxmox` exists now |
| `lifecycle` | Intent | Controls whether the platform may realize active instances |
| `control_node` | Intent | References the DesiredNode through which this local Proxmox scope is observed/operated |
| `config_schema_version` | Derived/contract | Pins validation and interpretation of the closed Proxmox config |
| `config` | Intent | Contains only the allowed Proxmox defaults below |
| `realized_cluster` | Actual link | Links the desired platform to its observed Nautobot Cluster |
| `realized_cluster_source` | Actual cache | Records derived versus explicit override provenance if both paths remain supported |

The Phase 1 Proxmox platform config admits only:

- `cluster_name` — an expected stable Proxmox cluster name when the operator needs to disambiguate
  or guard against observing the wrong scope;
- `default_storage` — the storage target used when an instance does not override it; and
- `default_bridge` — the network bridge used when an instance does not override it.

Each key is optional only when it can be derived unambiguously from fresh Proxmox observation.
Effective values and their provenance must appear in drift/plan evidence.

Do not add API URL, username, token identifier, TLS behavior, cluster utilization, default CPU
type, arbitrary extra arguments, or speculative multi-provider settings to this model.

### `DesiredComputeInstance`

Represents the compute realization required by exactly one DesiredNode.

It inherits effective lifecycle from `desired_node.lifecycle`; there is intentionally no lifecycle
field on this model.

| Field | Class | Reason it exists |
|---|---|---|
| `desired_node` | Intent | One-to-one owner of the logical guest identity |
| `platform` | Intent | Selects the Proxmox platform that must realize the node |
| `instance_kind` | Intent | Distinguishes `container` from `virtual_machine` |
| `desired_power_state` | Intent | Initially `running` or `stopped`; only `running` is automatically enforced at first |
| `vcpus` | Intent | Small, comparable capacity request used for create and drift |
| `memory_mb` | Intent | Small, comparable capacity request used for create and drift |
| `root_disk_gb` | Intent | Root capacity request used for create; compared only when exact typed root-disk evidence exists; shrinking is never automatic |
| `config_schema_version` | Derived/contract | Pins the closed Proxmox instance config |
| `config` | Intent | Contains only the allowed Proxmox-specific keys below |
| `realized_vm` | Actual link | Links to the Nautobot VirtualMachine representing the QEMU/LXC resource |
| `realized_vm_source` | Actual cache | Records derived versus explicit override provenance if both paths remain supported |

The Phase 1 Proxmox instance config admits only:

- `vmid` — optional requested stable Proxmox ID when the operator needs one; otherwise allocation
  is derived safely and the realized link becomes authoritative;
- `template` — the creation source required to build a new LXC or QEMU guest;
- `storage` — optional per-instance override of the platform default;
- `bridge` — optional per-instance override of the platform default; and
- `unprivileged` — LXC security intent, invalid for a QEMU instance.

`template` is creation intent. Until reliable source-template observation is explicitly added, it
must not create permanent post-creation drift merely because the running guest no longer exposes
its origin in a comparable form.

Do not initially add sockets, CPU model, NUMA, ballooning, BIOS/UEFI, machine type, cloud-init
contents, mount points, bind mounts, USB/PCI passthrough, tags, start order, HA group, replication,
snapshots, backup policy, migration policy, firewall rules, arbitrary features, or arbitrary
provider arguments. Any later addition needs a named real use case, a safe actuator mapping, and
fresh actual evidence when convergence is claimed.

### `DesiredEndpoint.mac_address`

Add one nullable, normalized MAC address intent field to the existing DesiredEndpoint model.

- It is optional for existing hosts and externally assigned cloud-style networking.
- When present, dnsmasq rendering, Proxmox NIC creation, endpoint drift, and collision checks must
  all consume the same canonical value.
- It is never copied into a second desired owner.
- An observed mismatch is a conflict or explicit remediation plan, never a silent rewrite of
  desired intent.
- For the first Proxmox creation slice, exactly one primary endpoint on the owning node must carry
  both this field and `mdns_name`; that endpoint is the single guest NIC/bootstrap endpoint.

## Effective example

The intended YAML shape is:

```yaml
desired_nodes:
  - name: aghub
    slug: aghub
    node_type: device
    lifecycle: active
    role: hypervisor

  - name: agdnsmasq
    slug: agdnsmasq
    node_type: service_host
    lifecycle: active
    role: dnsmasq
    accepted_actual_types:
      - device

desired_endpoints:
  - name: primary
    desired_node: agdnsmasq
    endpoint_type: primary
    ip_address: 192.168.0.2/32
    ip_policy: dhcp_reserved
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
    config:
      vmid: 102
      template: local:vztmpl/debian-13-standard.tar.zst
      unprivileged: true
```

The exact live cluster name, VMID, template, and resource values must be verified rather than
copied from this illustrative example.

## Reconciliation shape

The scope of a reconcile operation is an intent scope, not necessarily its SSH/API execution
target. For example:

```text
nctl reconcile new-guest
  -> desired target: new-guest
  -> related desired platform: aghub-pve
  -> observation/actuation target: aghub or the configured Proxmox API
  -> later guest observation target: new-guest
```

nctl must compute this dependency closure explicitly. It may include the selected platform and
control node, but it must not broaden a host-scoped operation to unrelated guests on the same
platform.

For a DHCP-reserved guest, the intended multi-round control loop is:

```text
structured desired node + endpoint + compute instance
  -> validate platform, instance, single-NIC endpoint, MAC, and manual-access gate contract
  -> reconcile/link desired IPAM ledger state
  -> render and deploy the dnsmasq reservation for the fixed MAC
  -> ensure the Proxmox guest exists with that MAC
  -> ensure the guest is running
  -> observe Proxmox again and ingest Cluster/VM/VMInterface state
  -> link DesiredComputeInstance.realized_vm
  -> safe stop at waiting_for_manual_initial_access
  -> operator prepares and checks the guest through the approved out-of-band route
  -> verify the bootstrap route and offered SSH fingerprints
  -> safe stop at waiting_for_ssh_enrollment until explicitly verified/enrolled
  -> resume reconcile and observe the guest OS
  -> ingest Device-level guest facts
  -> link DesiredNode.realized_device
  -> compute fresh drift
  -> converge without repeating create/deploy actions
```

Every action must record positive evidence that it actually ran. A successful command with an
empty guest action, empty Proxmox observation, or unchanged stale evidence does not prove this
path.

## Drift and safety vocabulary

Concrete phase plans may refine names, but all of these cases need structured treatment:

- desired platform has no observed Cluster candidate;
- platform observation is missing or stale;
- multiple Cluster candidates match;
- desired instance has no observed Proxmox guest;
- a unique guest candidate exists but is not linked;
- the realized guest disappeared from fresh Proxmox observation;
- provider scope, Proxmox node, VMID, or instance kind conflicts;
- vCPU, memory, or disk differs;
- desired and actual power state differs;
- desired endpoint MAC conflicts with another desired or actual resource;
- no unique NIC-bearing primary endpoint can be selected;
- the guest was created but awaits manual initial-access configuration;
- the manual initial-access completion checks fail;
- the guest was created but awaits explicit SSH key enrollment;
- a creation-only value cannot be compared after creation;
- configured and guest-agent interface evidence cannot be joined unambiguously;
- aggregate disk evidence cannot identify the desired root disk;
- the platform is healthy but the guest OS is not yet observable;
- the guest OS is healthy but its compute-platform observation is stale; and
- an observed guest has no matching desired compute instance.

Each code must define target kind, severity, human evidence, dashboard/status effect, and reconcile
classification. Bad data for one guest is target-local unless a shared platform contract or
credential makes every action on that platform unsafe.

## Phase 1 — Freeze the minimal contract and live baseline

**Goal: turn the decisions above into an implementation-ready contract without mutating the live
cluster.**

- Verify the live `aghub` Proxmox observation shape through the supported read-only nodeutils path.
- Record the actual cluster name, QEMU/LXC identities, VMIDs, resource units, statuses, interfaces,
  and observation timestamps needed for the `agdnsmasq` case without committing raw private
  inventory.
- Confirm how the current live Nautobot instance represents `aghub` and `agdnsmasq`, including
  Device, Cluster, VirtualMachine, interface, IP, and custom-field availability.
- Audit the old Proxmox self-registration path versus the normal nodeutils/nauto ingest path.
  Select one owner for normal virtualization-ledger writes; the normal ingest path is favored so
  `nctl reconcile` does not depend on a second registration workflow.
- Finalize exact model names, field types, constraints, config schemas, lifecycle behavior,
  GraphQL shape, REST write requirements, and YAML roots.
- Freeze an explicit operator-owned LXC manual-initial-access gate. Record its entry state,
  procedure location, required checks for the shared user, approved public key, privilege path,
  SSH service, mDNS service, hostname, and unique host keys, plus the trusted out-of-band source
  used for first SSH host-key enrollment. Do not select an automatic LXC or QEMU bootstrap
  mechanism in this phase.
- Verify that the `agdnsmasq` case and disposable LXC case each have exactly one intended
  NIC-bearing primary endpoint. Freeze the single-NIC endpoint/bridge/NIC-slot derivation and its
  ambiguity errors; do not silently inherit the current sorted-first mDNS selection.
- Freeze the revised nodeutils Proxmox observation schema: configured interfaces and guest-agent
  interfaces remain separate and may join only by a unique normalized MAC. Pin exact LXC rootfs
  evidence and the narrowly allowlisted storage-content source used to verify template
  availability.
- Produce a field classification table proving the consumer for every retained field and listing
  rejected candidate fields with reasons.
- Define data transition for existing DesiredNodes and clarify the future meaning or removal of
  `DesiredNode.realized_vm`. Do not leave two fields claiming ownership of the same compute link.
- Define output schema changes and the coordinated nintent/nctl/nauto rollout and rollback point.
- Capture a read-only baseline of `nctl drift`, production render, Braindumps, and generated
  inventories before schema changes.

**Exit criteria:** a Phase 1 plan and report pin the live data shape, every new field has a named
consumer and tier, `agdnsmasq` has one unambiguous proposed platform/instance/NIC mapping, the LXC
manual-initial-access and SSH-enrollment gates are explicit and dry-walked, automatic bootstrap is
recorded as deferred rather than assumed, and no live state has been changed.

## Phase 2 — Materialize Proxmox actual state through normal ingest

**Goal: make fresh Proxmox platform and guest observations first-class actual ledger state before
adding desired compute drift.**

- Extend the nauto nodeutils ingest Job to validate the strict `facts.proxmox` input shape.
- Upsert the observed Proxmox Cluster and QEMU/LXC guests into Nautobot native virtualization
  objects using stable provider identities.
- Store only the allowlisted Proxmox fields that have current matching, freshness, display, or
  reconcile consumers.
- Revise the nodeutils Proxmox observation schema before VMInterface ingest. Preserve configured
  interfaces and QEMU guest-agent interfaces as separate provenance-bearing collections, and emit
  a joined interface only for a unique normalized-MAC match.
- Upsert VMInterface and IP relations only from a reliable joined QEMU interface or explicit LXC
  config data. Preserve unmatched config-only/agent-only evidence diagnostically without
  inventing a relation. Never infer one from names, ordering, ARP, or incomplete strings.
- Normalize LXC `rootfs` capacity separately from aggregate guest disk data. Do not expose QEMU
  aggregate `maxdisk` as comparable root-disk evidence.
- Collect and validate the minimum storage-content inventory needed to prove that the requested
  Phase 5 LXC template currently exists on the selected storage. Extend the privileged helper only
  with the exact read-only path grammar required for this observation.
- Record per-platform/per-guest observation freshness so an old Nautobot VM row cannot masquerade
  as a current Proxmox observation.
- Make repeat ingest idempotent. A second ingest of identical evidence changes nothing.
- Do not delete or stop guests absent from one observation. Define truthful handling for complete
  versus partial collection before marking anything offline.
- Extend nctl's typed actual snapshot to read the new allowlisted Cluster/VM facts. Keep
  unrestricted raw JSON outside the snapshot.
- Show read-only Proxmox actual relationships in diagnostic output so `aghub -> aghub-pve ->
  agdnsmasq` can be inspected before any desired relation exists.

Tests must cover QEMU and LXC normalization, stable VMID matching, duplicate names, multi-NIC
guests, unique/duplicate/missing MACs, config-only and agent-only interfaces, partial guest-agent
results, LXC rootfs versus aggregate disk, template present/missing, partial collection, stale
evidence, repeat ingest, one bad guest isolated from others, and a live read-only ingest against
the local Nautobot environment.

**Exit criteria:** a fresh supported collection from `aghub` produces one inspectable Nautobot
Cluster and stable QEMU/LXC VirtualMachines, including `agdnsmasq`; interface evidence retains its
configuration/agent provenance; LXC rootfs and template availability have typed sources; and
repeating the operation is idempotent and non-destructive.

## Phase 3 — Add the minimal nintent compute models

**Goal: store a Proxmox platform and desired compute realization without yet creating or changing
a guest.**

- Add `DesiredComputePlatform` and `DesiredComputeInstance` with the minimal fields and strict
  Proxmox config keys defined above.
- Add the optional desired MAC field to `DesiredEndpoint`.
- Add model validation and database constraints:
  - one compute instance per DesiredNode;
  - a platform control node must reference a suitable, non-retired DesiredNode;
  - an instance kind/config combination must be valid;
  - effective lifecycle is inherited from DesiredNode and gated by platform lifecycle, with no
    independently writable instance lifecycle;
  - positive bounded CPU, memory, and disk values;
  - unique normalized desired MAC addresses;
  - an actionable compute instance resolves exactly one primary endpoint carrying both desired MAC
    and mDNS name; multiple candidates are rejected rather than sorted;
  - a realized VM must belong to the realized platform Cluster;
  - no credentials or arbitrary config keys; and
  - planned/deprecated/retired node or platform combinations remain observable but cannot create or
    start a guest.
- Cover normal Nautobot UI, filters, tables, detail relationships, REST as needed for confirmed
  structured writes, GraphQL reads, strict YAML load/import, and transactional rollback.
- Make effective platform defaults and per-instance overrides visible with provenance.
- Resolve the existing `DesiredNode.realized_vm` semantic overlap through the coordinated
  breaking-change decision from Phase 1.
- Seed only the confirmed `aghub-pve` and `agdnsmasq` relationships after a dry import and explicit
  review. Do not invent desired records for every observed guest.

The nintent deployment constraint applies: batch the schema/API work, commit it, ask the user to
push, rebuild the Nautobot image, migrate, and then deploy the matching nctl revision. Do not add a
mixed-version compatibility reader.

**Exit criteria:** supported UI/YAML/API paths can express the confirmed `aghub-pve ->
agdnsmasq` relationship, invalid or unknown Proxmox fields are rejected, and creating the desired
records alone performs no host or guest actuation.

## Phase 4 — Add compute drift, explicit ledger linking, and dashboard explanation

**Goal: deterministically compare desired platforms/instances with the actual Proxmox ledger and
produce truthful plans without actuating Proxmox guests. This phase may perform separately
approved Nautobot/nintent link writes; it is not globally read-only.**

- Add compute platform and instance targets to the typed desired snapshot and drift evaluator.
- Match platforms by explicit realized Cluster first, then by stable Proxmox scope identity.
- Match guests by explicit realized VM first, then by platform + guest kind + requested VMID or a
  single strong normalized-name candidate.
- Never match a guest from another platform merely because its name is equal.
- Compare only fields with reliable actual evidence. Report creation-only or unobservable values
  as such instead of permanent false drift.
- Add deterministic linking actions for single unambiguous candidates, with derived-link
  provenance. Applying a link is an explicit ledger mutation: require a dry plan, separate
  approval, exact-scope write, refetch confirmation, and fresh drift proving the action is not
  repeated.
- Add all compute findings to status, human drift rendering, JSON envelopes, dashboard tiles, and
  reconcile classification.
- Display both realization layers for a guest: compute resource and guest OS.
- Build plan-only reconcilers for missing guest, power mismatch, and resource mismatch. In this
  phase they remain unsupported/manual actions except safe ledger linking.
- Prove host-scope dependency closure: reconciling `agdnsmasq` may read/observe `aghub-pve` but
  cannot plan actions for an unrelated guest.

Tests must cover matching, ambiguity, stale observation, LXC-as-VirtualMachine representation,
dual Device/VM realization without conflict, inherited planned/approved/active/deprecated/retired
lifecycle behavior, stopped-intent behavior without automatic stop, mixed healthy/bad guests,
scoped planning, unknown codes, and output-contract validation.

**Exit criteria:** an `agdnsmasq` dry plan names the exact Cluster/VirtualMachine links; a
separately approved apply writes only those links; refetch proves the intended relations; and fresh
drift converges without repeating the link action or changing Proxmox. A hypothetical missing guest
still produces a precise non-actuating dry plan.

## Phase 5 — Reconcile one new LXC through compute realization

**Goal: prove the smallest useful Proxmox creation path with a disposable LXC.**

- Define a reversible, non-sensitive live LXC fixture with an approved name, VMID/allocation rule,
  template, resource values, storage, bridge, single primary endpoint, MAC, manual-initial-access
  owner/procedure, trusted host-key verification source, and cleanup decision.
- Add a least-privilege Proxmox ensure-present/start actuator through the established nctl →
  Ansible boundary. Keep credentials outside desired state and operation evidence.
- Validate the exact effective config before mutation, including storage/bridge existence, template
  availability from fresh storage-content observation, VMID/name/MAC/IP collisions, unique
  endpoint/NIC selection, the manual-access gate contract, and platform freshness.
- Add explicit action dependencies so DHCP/IPAM/dnsmasq preparation occurs before a guest that
  depends on it.
- Create only when no actual candidate exists. Refetch immediately after creation and fail
  truthfully if the result cannot be identified.
- Start only the exact created/linked guest. Do not stop, replace, migrate, resize, or delete.
- Re-observe Proxmox through nodeutils, ingest, and link the VirtualMachine, then preserve those
  completed compute actions and return structured `waiting_for_manual_initial_access`.
- Do not install packages, create users, inject keys, or alter guest services automatically.
  The operator may complete the Phase 1 manual procedure separately. Once the guest offers SSH
  keys, require out-of-band fingerprint verification and the existing explicit
  `nctl ssh enroll` path before a later reconcile resumes guest observation.
- Preserve complete evidence if any post-create step fails. A created guest that still lacks
  manual initial access or SSH observation is partially progressed, not “no action.”
- Run a bounded multi-round test proving:
  `missing -> planned create -> create actually executed -> fresh Proxmox ingest -> linked guest ->
  waiting_for_manual_initial_access -> repeated reconcile does not recreate`.
- Exercise a dry plan first and obtain separate approval for the live apply.

Automated tests must include a fake/disposable Proxmox boundary that positively proves the create
call ran, plus missing/ambiguous endpoint, template missing, missing manual-gate definition,
manual-access and unenrolled-key safe stops, collision, stale platform, malformed result, partial
success, repeat run, and unrelated-guest isolation cases.

**Exit criteria:** one approved disposable LXC can be described entirely through structured intent,
created by scoped reconcile, freshly observed and linked at the compute layer, and shown by repeat
reconcile not to recreate it. Reaching `waiting_for_manual_initial_access` is a successful,
resumable Phase 5 terminal state; guest-OS access and observation do not gate this phase.

## Phase 6 — Extend the proven path to QEMU and safe mutable differences

**Goal: support a real VM without turning the adapter into an unrestricted Proxmox configuration
surface.**

- Add the minimum QEMU creation behavior required by one concrete approved VM case.
- Reuse the same platform, instance, endpoint, scope, evidence, and observation contracts.
- Reuse the operator-owned manual-initial-access gate after fresh QEMU observation and linking.
  Do not select cloud-init, a golden template, OpenTofu, or another automatic bootstrap mechanism
  merely to complete this phase.
- If QEMU needs an additional field, document its exact consumer and decide whether it belongs in
  the strict Proxmox config. Do not bulk-import the Proxmox QEMU option set.
- Define safe behavior for vCPU, memory, root disk, and power differences one operation at a time.
- Before planning QEMU disk growth, identify the intended root/boot disk from typed configuration,
  observe its exact current capacity, and prove the mapping through ingest and nctl. Aggregate
  `maxdisk` is not sufficient evidence.
- Initially allow only changes proven non-destructive in the target state. Disk growth may be
  distinct from disk shrink; memory/CPU changes may require stopped guests; each condition must be
  visible in the plan.
- Keep guest move, replacement, delete, disk shrink, passthrough, arbitrary cloud-init, snapshots,
  backups, and HA outside the automatic path unless separately planned.
- Add real multi-round verification for the QEMU case and for every newly automatic mutation.

**Exit criteria:** one concrete QEMU VM reaches fresh compute realization through the same model
without adding a generic option bag, repeat reconcile does not recreate it, and every automatic
mutable difference has explicit preconditions and post-observation proof.

## Phase 7 — Evaluate and, if justified, automate initial guest access

**Goal: decide from proven operational evidence whether manual bootstrap should remain supported
or be replaced by narrowly bounded automation.**

- Measure the actual manual work and failure modes from the Phase 5 LXC and Phase 6 QEMU cases
  before selecting another tool or actuator.
- Compare only concrete mechanisms appropriate to each guest kind, such as a reproducible golden
  template, a bounded Proxmox-side action, or a fixed QEMU cloud-init profile. OpenTofu is adopted
  only if it is deliberately selected as the lifecycle owner rather than added solely for SSH
  setup.
- If automation is justified, define a versioned fixed profile with an owner, exact inputs,
  validation, idempotence, least privilege, secret handling, partial-failure evidence, and rollback
  behavior. Do not accept arbitrary commands, packages, paths, cloud-init, or key material from
  nintent.
- Prove every claimed result—shared user, approved key fingerprint, privilege, SSH, mDNS,
  hostname, and unique host keys—on a disposable guest. Keep explicit out-of-band host-key
  enrollment even if bootstrap becomes automatic.
- If automation is not justified, retain and document the manual safe stop without treating it as
  a product failure or an incomplete compute-management workflow.

**Exit criteria:** the decision record is based on Phase 5/6 evidence. If automation is selected,
one disposable case proves the bounded profile and retry behavior end to end; otherwise the manual
procedure remains the explicit supported contract and automatic bootstrap remains out of scope.

## Phase 8 — Connect confirmed Braindump wishes to structured proposals

**Goal: make casual requests convenient while keeping prose outside deterministic actuation.**

- Let an agent read a Braindump together with fresh desired, actual, platform-capacity, and drift
  context and compose an exact proposed nintent diff.
- The proposal must name the DesiredNode, DesiredEndpoint, DesiredComputePlatform,
  DesiredComputeInstance, selected single-NIC endpoint, effective defaults, applicable
  manual-access state or approved automatic profile, missing required choices, expected reconcile
  scope, and unsupported wishes.
- Do not write a proposal containing guessed security, storage, network, template, or destructive
  choices. Ask a concise question instead.
- Provide one explicit accept operation that writes the confirmed structured records
  transactionally through their canonical owner.
- Keep reconcile plan and reconcile apply as separate subsequent gates. Accepting a proposal does
  not authorize `--yes`.
- Replace the Alignment Review after structured write and again after apply/observation so it
  describes the current state rather than claiming success early.
- Prove that editing review prose alone changes no desired object, drift code, operation plan, or
  host state.

**Exit criteria:** a user can casually state a Proxmox LXC/VM wish, review and accept a small exact
structured proposal, separately approve a dry reconcile plan, and receive a fresh review after
deterministic convergence.

## Phase 9 — Consolidate operation, documentation, and live evidence

**Goal: make the Proxmox path a routine supported workflow rather than a one-off demo.**

- Document the ordinary “request/add/reconcile a Proxmox guest” workflow with the minimum genuine
  intent inputs.
- Make dashboard and CLI views explain platform, compute realization, guest-OS realization,
  effective defaults, provenance, freshness, and blockers without exposing raw provider payloads.
- Add failure recovery guidance for guest-created-but-not-observed, waiting for manual initial
  access, waiting for SSH enrollment, manual completion-check failure, platform unreachable,
  credential denied, template missing, IP/MAC collision, stale ledger, and ambiguous
  actual/interface links.
- Audit every new reader and writer across nintent, nctl, nauto, nodeutils, Ansible, generated
  inventories, docs, and tests.
- Run one whole-cluster dry plan showing an unhealthy guest remains target-local and unrelated
  nodes continue independently.
- Run repeated live scoped operations proving idempotence after convergence.
- Record unsupported/destructive boundaries honestly. Do not label the feature complete based only
  on unit tests or an action path that was not positively exercised.

**Exit criteria:** the existing `agdnsmasq` relationship and at least one created LXC plus one QEMU
case are inspectable, scoped, repeatably convergent at the compute layer, and documented; their
manual or approved automatic access state is visible; no prose, missing desired record, or
unexplained actual guest can trigger deletion.

## Definition of done for each phase

Every concrete phase plan must:

- state the desired transition and the exact fresh actual evidence that proves it;
- identify one owner for every identity, route, endpoint, resource, credential reference, and
  execution target;
- state the manual-initial-access and SSH trust transitions for every newly created guest kind,
  including both expected safe stops and any later approved automatic profile;
- inventory model, UI, loader, REST, GraphQL, snapshot, drift, planner, executor, dashboard,
  Ansible, observation, ingest, documentation, and test impacts as applicable;
- classify all new findings and distinguish shared-platform failures from target-local failures;
- define migration, coordinated rollout, rollback, and treatment of existing rows;
- reject unknown provider config rather than ignoring it;
- preserve evidence after side effects;
- include focused unit/error tests and the highest practical multi-round planner/executor test;
- positively assert that intended Proxmox actions ran and, when guest observation is in the
  phase's scope, that it ran;
- use a reviewed dry plan and separate approval before live mutation; and
- call a phase complete only when its stated live or environment-backed path was exercised.

## Sequencing rationale

Phase 1 freezes the narrow contract before schema work. Phase 2 makes the already-collected
Proxmox facts usable as actual state, preventing a desired model from being built against guessed
evidence. Phase 3 adds only the desired records required by that observed shape. Phase 4 proves
non-actuating compute convergence on the existing `agdnsmasq` LXC, including separately approved
ledger-link writes, before any guest creation is authorized.
Phase 5 adds the smallest LXC creation slice, and Phase 6 generalizes only as far as one concrete
QEMU case and individually safe mutations justify. Phase 7 uses evidence from those workflows to
decide whether initial-access automation is worth its additional actuator and security surface.
Phase 8 then connects the proven deterministic path to convenient, confirmed Braindump proposals.
Phase 9 consolidates routine operation and evidence.

AWS or Azure work is deliberately absent from this sequence. A future provider begins with its own
concrete use case and actual-state adapter, following the guidance in `README_DEV.md`; it does not
retroactively justify speculative fields in the Proxmox implementation.
