# Phase 2 Implementation Plan: Materialize Proxmox Actual State Through Normal Ingest

Status: planned.

This plan implements Phase 2 of
[`devdocs/big/vm/roadmap.md`](../roadmap.md). It is grounded in the Phase 1 contract and live
baseline under [`devdocs/big/vm/p1/`](../p1/), especially `report1.1.md`, `report1.2.md`,
`report1.3.md`, `report1.5.md`, `report1.9.md`, `report1.11.md`, and `report1.12.md`.

The source revisions at plan-writing time are:

| Repository | Revision |
|---|---|
| `ansible_agdev` | `c6faafdaef4ed43fe3477ee0443437d4b9b58ea9` |
| `nauto` | `489ff6fc869b4df7748b862dd0b8efc75aea764f` |
| `nctl` | `576e13b856fc5a657cd0b6cce4382679ba60e6a6` |
| `nintent` | `ad9d36397d23c269ad748e13acbccc532fa29f52` |
| `nodeutils` | `36e1c5752ba895780eea21b8e994926b93cc1c53` |

Step 0 records the actual starting revisions again. If they differ, the report must audit the
change before implementation continues.

## 1. Purpose and Required State Transition

Phase 2 makes the Proxmox facts already collected from `aghub` into bounded, typed, fresh actual
ledger state:

```text
fresh nodeutils collection on aghub
  -> strict facts.proxmox schema validation
  -> normal nauto ingest
  -> Nautobot Cluster + VirtualMachine + reliable VMInterface/IP rows
  -> nctl typed actual snapshot
  -> read-only actual-compute diagnostic
  -> identical repeat ingest produces no write
```

The concrete positive case is:

```text
Device aghub
  -> observed Proxmox Cluster aghub-proxmox
  -> observed LXC VMID 108 agdnsmasq
```

This phase does not create `DesiredComputePlatform` or `DesiredComputeInstance`. The future desired
platform slug `aghub-pve` therefore must not be invented in actual state. Until Phase 3, diagnostic
output shows the observer Device, the actual Cluster name, and its actual guests.

The exact fresh evidence that proves completion is:

1. a supported `nodeutils.inventory.v2` report with nested
   `facts.proxmox.schema_version=nodeutils.proxmox.v1`;
2. a successful supported read through the installed, still-read-only privileged helper;
3. an ingest summary naming the Cluster and every processed guest action;
4. a refetch showing one stable Cluster and stable QEMU/LXC VirtualMachines, including
   `agdnsmasq` as `cluster=aghub-proxmox`, `guest_type=lxc`, `vmid=108`, and `node=aghub`;
5. typed interface evidence that retains configuration and guest-agent provenance;
6. parsed LXC rootfs evidence distinct from aggregate disk evidence;
7. fresh storage-content evidence containing the operator-recorded Phase 5 candidate's exact
   `volid` (recorded as acceptance evidence, not desired intent);
8. a typed nctl snapshot and read-only diagnostic containing the same identities and freshness;
9. an identical second ingest with zero creates/updates and unchanged IDs, relations, and
   `last_updated` values; and
10. no Proxmox guest create/start/stop/resize/move/delete action and no deletion of unexplained
    Nautobot guests.

## 2. Phase 2 Exit Criteria

Phase 2 is `complete` only when every applicable item below is positively exercised.

- [ ] The nested schema is exactly versioned as `nodeutils.proxmox.v1`; unknown top-level/shared
      keys fail closed, and malformed guest/storage items are isolated and make the platform
      observation `partial`.
- [ ] Cluster identity records whether its name came from a provider cluster record or the
      standalone-node fallback. A fallback rename reuses a stable observer-Device scope or stops
      for explicit migration; it never creates a second Cluster merely because the hostname
      changed.
- [ ] Every semantic collection has an explicit limit and deterministic sort key. Truncation
      records `truncated_collection`, makes the affected section/platform `partial`, and cannot be
      hidden by the generic report bounding pass.
- [ ] Bounded error codes, omitted-error count, and section-level
      `state`/`last_attempted_at`/`evidence_observed_at` survive ingest into Nautobot and the typed
      nctl snapshot.
- [ ] QEMU configuration interfaces and guest-agent interfaces remain separate. A joined
      interface exists only for one unique normalized-MAC match.
- [ ] Duplicate, missing, invalid, config-only, agent-only, and unmatched MAC cases retain bounded
      diagnostic evidence without name- or order-based pairing.
- [ ] LXC `rootfs` storage, volume, and size are parsed from config evidence. Aggregate
      `maxdisk`/`disk` remains display-only and is never labeled or consumed as root-disk evidence.
- [ ] `/nodes/{node}/storage/{storage}/content` is the only new privileged-helper path; it remains
      an exact `pvesh get` path with positive and negative boundary tests.
- [ ] Storage-content collection retains only the fields needed to prove an exact `vztmpl`
      identifier is currently present on one node/storage.
- [ ] The normal nauto Job is the sole Cluster/VM/VMInterface/IP writer. No historical
      nodeutils self-registration writer is restored.
- [ ] Stable matching uses Cluster type/name and then
      `(cluster, proxmox_guest_type, proxmox_vmid)`. Guest name is display data, not a primary key.
- [ ] A reliable joined QEMU interface or explicit LXC config creates a stable VMInterface.
      Unmatched evidence creates no VMInterface or IP relation.
- [ ] Existing foreign IP or MAC ownership conflicts fail locally and never steal, reassign, or
      guess a relation. A complete fresh observation may detach only relations previously recorded
      as owned by this ingestor; it never deletes the IPAddress object or a foreign relation.
- [ ] IP change, empty-IP observation, MAC change, and interface disappearance have explicit
      complete-versus-partial convergence behavior, so retained old evidence cannot appear current.
- [ ] Collection and ingest freshness/completeness are persisted per platform and guest.
      Older/equal-conflicting evidence cannot overwrite newer ledger state.
- [ ] Observation timestamps are timezone-aware, normalized to UTC, and rejected before all
      writes when they exceed the configured future-skew allowance.
- [ ] A partial observation never marks an absent guest offline, disappeared, deleted, or
      otherwise changed. In Phase 2, even a complete observation never deletes an absent guest.
- [ ] One malformed guest rolls back all writes for that guest, leaves unrelated guests
      ingestible, and marks the platform observation `partial`.
- [ ] Newer partial observations merge by stable storage/guest/interface keys. Retained evidence
      keeps its original evidence time, and a newer parent timestamp is never inherited by an
      unobserved child section.
- [ ] First apply is preceded by a dry-run summary and a before image; apply is separately
      approved and followed by exact refetch.
- [ ] Identical repeat ingest is a no-op, including unchanged object `last_updated` values.
- [ ] nctl reads only the dedicated native fields and allowlisted custom fields into strict typed
      models; it never consumes `inventory_raw_json` or unrestricted provider payloads.
- [ ] A read-only nctl diagnostic renders
      `aghub -> aghub-proxmox -> agdnsmasq` with VMID, kind, state, observation time, and
      completeness.
- [ ] One exact operator-recorded Phase 5 candidate template `volid` is present in a fresh,
      complete storage-content section. If none is available, Phase 2 is `partially complete`;
      Phase 2 does not download a template or guess one.
- [ ] Automated tests cover all cases listed in Section 8, and the environment-backed
      collect/ingest/refetch/repeat path runs against the local Nautobot environment.
- [ ] Final audit proves no Proxmox guest state, desired object, generated inventory, SSH trust
      entry, or unrelated actual row changed.

An omitted live collection, first ingest, refetch, or repeat-ingest assertion makes the phase
`partially complete`, even if all unit tests pass.

## 3. Scope, Non-goals, and Safety Boundary

### 3.1 In scope

- `nodeutils` Proxmox schema, normalization, completeness, interface join, rootfs parsing, and
  storage-content observation;
- the `ansible_agdev` read-only helper allowlist and its deployment path;
- nauto prerequisite objects and dedicated Proxmox ledger fields;
- strict validation and idempotent Cluster/VM/VMInterface/IP upsert in the normal ingest Job;
- per-report and per-guest transaction/savepoint behavior;
- nctl typed Cluster/VM/VMInterface/storage-content actual models;
- one read-only nctl actual-compute diagnostic;
- coordinated deployment, one approved local-Nautobot ingest, refetch, repeat-ingest proof, and
  sanitized reporting.

### 3.2 Explicit non-goals

Phase 2 does not:

- add or seed desired compute platform/instance records;
- change or remove `DesiredNode.realized_vm`;
- compute desired compute drift, candidate links, or dashboard compute status;
- write `DesiredComputePlatform.realized_cluster` or `DesiredComputeInstance.realized_vm`;
- create, start, stop, resize, move, clone, replace, or delete a Proxmox guest;
- automate manual initial access or SSH enrollment;
- set desired endpoint MAC data or alter dnsmasq output;
- infer a QEMU root/boot disk;
- create VMInterfaces from config-only QEMU or agent-only evidence;
- infer interface relations from interface name, list order, ARP, bridge position, or incomplete
  strings;
- treat an absent observed guest as unwanted;
- add AWS, Azure, a generic provider, credentials, API URLs, tokens, or executable commands to
  nintent; or
- copy raw Proxmox responses into Nautobot custom fields, Git, Job artifacts, or nctl output.

### 3.3 Mutation boundary

Code and local test changes are authorized implementation work. Live/environment-backed changes
have separate gates:

1. Deploying the helper/nodeutils revision to `aghub` requires review of the exact pinned commits.
2. Creating prerequisite Nautobot ClusterType/Role/Status/CustomField objects requires a seed Job
   dry run and separate approval.
3. The first virtualization ingest requires an ingest dry run, exact before image, and separate
   approval.
4. Any cleanup/delete of an erroneously created Nautobot ledger row requires a dependency audit
   and separate approval.

No approval in this phase authorizes a Proxmox mutation. The helper must continue to execute only
`pvesh get`.

## 4. Current Implementation Baseline

### 4.1 nodeutils

- Top-level reports use `nodeutils.inventory.v2`.
- `facts.proxmox` has no nested schema version.
- QEMU agent interfaces replace configured interfaces when any agent result exists.
- QEMU configured NIC strings such as `virtio=<MAC>,bridge=vmbr0` do not yet have a proven
  normalized join representation.
- QEMU and LXC `disk_gb` are both derived from aggregate `maxdisk`/`disk`.
- Per-config and guest-agent errors are often converted to empty data, so absence and collection
  failure cannot be distinguished.
- Broad raw `cluster`, `resources`, `nodes`, `networks`, `storages`, and per-guest `raw` values
  remain in the current output.

### 4.2 privileged helper and Ansible

- The helper is a fixed root-owned `os.execve()` proxy that accepts one path and always runs
  `/usr/bin/pvesh get <path> --output-format json`.
- It allows current cluster/node/guest/config/network/storage-list/guest-agent reads.
- It does not allow `/nodes/{node}/storage/{storage}/content`.
- The supported Ansible collection play deploys the pinned nodeutils checkout and helper, runs as
  the configured non-root user, and writes a mode-`0600` report.

### 4.3 nauto and Nautobot

- The normal ingest Job validates the top-level report and upserts only `dcim.Device`.
- `facts.proxmox` is omitted even from the bounded `inventory_raw_json` subset.
- The live Phase 1 baseline contains zero ClusterType, Cluster, VirtualMachine, and VMInterface
  rows and zero `proxmox_*` custom fields.
- The Job currently wraps the whole batch in one transaction and catches `IngestError` inside it,
  but has no virtualization-specific per-report/per-guest savepoint contract.
- The ingest summary schema is `nodeutils.ingest.summary.v1` and has one row per submitted report.

### 4.4 nctl

- `ActualVirtualMachine` contains only `id` and `name`.
- No actual Cluster or VMInterface model exists.
- The actual GraphQL query reads unrestricted custom-field JSON only for the closed Device fact
  allowlist; it does not read Proxmox fields.
- `nctl status` intentionally reports controller/input health and must not become a second
  per-target state command.

## 5. Implementation Contracts

### 5.1 Ownership

| Value or action | Sole owner |
|---|---|
| Proxmox read execution | `nodeutils` through the installed read-only helper |
| Nested observation schema and normalization | `nodeutils/proxmox_inventory.py` |
| Helper path authorization | `ansible_agdev` `nodeutils_pvesh_helper` role |
| Cluster/VM/VMInterface/IP actual writes | nauto normal nodeutils ingest Job |
| Cluster name provenance | `nodeutils` observation schema |
| Durable Cluster scope key | nauto, derived from provider name or matched observer Device UUID |
| Guest stable identity | `(Cluster id, proxmox_guest_type, proxmox_vmid)` |
| Interface stable identity | `(VirtualMachine id, proxmox_config_slot)` |
| Observation time | top-level nodeutils `collected_at`, copied without regeneration |
| Future-skew allowance | nauto server-side ingest policy |
| Actual snapshot typing | `nctl_core.sources.actual` |
| Desired compute intent and actual links | deferred to nintent/nctl Phases 3 and 4 |
| Proxmox credentials and future actuator | outside nintent and outside Phase 2 |

The old nodeutils self-registration code remains historical evidence only.

### 5.2 Nested `facts.proxmox` schema

The nested version is exactly `nodeutils.proxmox.v1`. The top-level report remains
`nodeutils.inventory.v2`.

The normalized semantic shape is:

```yaml
facts:
  proxmox:
    schema_version: nodeutils.proxmox.v1
    enabled: true
    detected: true
    mode: auto | enabled
    inventory_source: nodeutils-proxmox
    observed_at: "<exact top-level collected_at>"
    collection:
      state: complete | partial
      last_attempted_at: "<exact top-level collected_at>"
      evidence_observed_at: "<latest complete shared evidence time or null>"
      omitted_error_count: 0
      errors:
        - scope_kind: platform | node | guest | interface | storage
          scope_id: "<bounded stable identifier>"
          section: "<closed section name>"
          code: "<closed error code>"
      sections:
        cluster_identity: {state: complete, evidence_observed_at: "<time>"}
        node_list: {state: complete, evidence_observed_at: "<time>"}
        qemu_guest_lists:
          - {node: aghub, state: complete | partial, evidence_observed_at: "<time or null>"}
        lxc_guest_lists:
          - {node: aghub, state: complete | partial, evidence_observed_at: "<time or null>"}
        storage_inventory:
          - {node: aghub, state: complete | partial, evidence_observed_at: "<time or null>"}
    cluster:
      name: "<cluster name>"
      name_source: proxmox_cluster_name | standalone_node_fallback
      identity_value: "<provider cluster name or standalone node name>"
      node_count: 1
      observed_node_names: ["aghub"]
    qemu_vms:
      - guest_type: qemu
        vmid: 102
        node: aghub
        name: aghaos
        proxmox_status: running
        vcpus: 2
        memory_mb: 4096
        disk_gb: 32.0
        observation:
          state: complete | partial
          last_attempted_at: "<exact top-level collected_at>"
          evidence_observed_at: "<fresh guest-list evidence time>"
          omitted_error_count: 0
          errors: []
          sections:
            identity: {state: complete, evidence_observed_at: "<time>"}
            config: {state: complete, evidence_observed_at: "<time>"}
            agent_interfaces: {state: complete | partial, evidence_observed_at: "<time or null>"}
        interfaces:
          config_interfaces: []
          agent_interfaces: []
          joined_interfaces: []
          unmatched: []
    lxc_containers:
      - guest_type: lxc
        vmid: 108
        node: aghub
        name: agdnsmasq
        proxmox_status: running
        vcpus: 1
        memory_mb: 512
        disk_gb: 7.78
        rootfs:
          storage: local-lvm
          volume: vm-108-disk-0
          size_gb: 8
        observation:
          state: complete
          last_attempted_at: "<exact top-level collected_at>"
          evidence_observed_at: "<fresh guest-list evidence time>"
          omitted_error_count: 0
          errors: []
          sections:
            identity: {state: complete, evidence_observed_at: "<time>"}
            config: {state: complete, evidence_observed_at: "<time>"}
            rootfs: {state: complete, evidence_observed_at: "<time>"}
        interfaces:
          config_interfaces: []
          agent_interfaces: []
          joined_interfaces: []
          unmatched: []
    storage_content:
      - node: aghub
        storage: local
        content_type: vztmpl
        state: complete | partial
        last_attempted_at: "<exact top-level collected_at>"
        evidence_observed_at: "<latest successful content-list time or null>"
        omitted_error_count: 0
        errors: []
        items:
          - volid: "local:vztmpl/<exact artifact name>"
            content: vztmpl
            format: "<allowlisted format or null>"
            size_bytes: 123
```

The implementation may use dataclasses or typed dictionaries internally, but emitted keys and
semantics are fixed by this section.

Rules:

- Unknown keys at the Proxmox envelope, collection, cluster, interface-envelope, rootfs, or
  storage-content level are invalid.
- Each guest/storage item is validated independently. An invalid item is omitted from ledger
  candidates, recorded by a bounded error, and makes the enclosing observation `partial`.
- `observed_at` must equal top-level `collected_at`; a host cannot provide a second clock.
- A provider cluster row from `/cluster/status` emits
  `name_source=proxmox_cluster_name`. When no such row exists, the current hostname-derived name
  emits `name_source=standalone_node_fallback`; the source is never inferred later from spelling.
- `identity_value` is the provider cluster name for clustered Proxmox and the observed standalone
  node name for fallback mode. Nautobot derives the durable fallback scope from the already
  matched observer Device UUID rather than treating the synthesized display name as the stable
  key.
- `name` is required for display but never replaces VMID identity.
- MACs are normalized to lowercase colon-separated form. Invalid MACs remain diagnostic errors,
  not normalized guesses.
- Config interface entries retain at least config slot, normalized MAC when valid, bridge, and
  the explicit config-side IP/gateway when present.
- Agent interface entries retain agent name, normalized MAC when valid, and typed address/prefix
  entries.
- QEMU `joined_interfaces` contain both config slot and agent name, their one normalized MAC,
  bridge, and agent IP evidence. Both source collections remain present.
- LXC config is explicit enough to create an interface candidate without guest-agent data.
- `disk_gb` remains an aggregate display estimate. It is never renamed, copied, or compared as
  `root_disk_gb`.
- `rootfs.size_gb` comes only from parsed LXC `rootfs` config. A missing or unsupported size
  grammar yields partial rootfs evidence rather than falling back to `disk_gb`.
- QEMU root/boot disk is absent from this schema.
- Storage content includes only `vztmpl` entries and the allowlisted identity/display fields
  above. No full storage response is retained.
- Every section error uses a closed code and bounded scope, with no raw stderr. If the bounded
  error list fills, `omitted_error_count` records how many additional errors were omitted and the
  section remains `partial`.
- `raw`, raw cluster status, unrestricted config, utilization, uptime, tags, task data, network
  lists, and resource lists are not part of `nodeutils.proxmox.v1`.

Disabled/non-detected hosts may keep the existing small
`enabled/detected/mode` result outside the supported observation form, but nauto must not treat
that result as a platform observation.

#### Semantic collection limits

Phase 2 replaces implicit bounding of Proxmox semantic collections with explicit, pre-serialization
limits:

| Collection | Maximum | Deterministic order |
|---|---:|---|
| Proxmox nodes | 64 | normalized node name |
| QEMU guests | 512 | `(node, vmid)` |
| LXC guests | 512 | `(node, vmid)` |
| config interfaces per guest | 64 | parsed numeric config slot |
| agent interfaces per guest | 256 | `(normalized_mac_or_empty, name)` |
| addresses per agent interface | 64 | `(address family, address, prefix)` |
| storage scopes | 128 | `(node, storage)` |
| `vztmpl` items per storage | 2048 | exact `volid` |
| bounded errors per platform/guest/storage scope | 128 | `(scope_kind, scope_id, section, code)` |

Cross-node guest lists are sorted before limiting. When a limit is exceeded, the collector keeps
the deterministic prefix, records `truncated_collection`, records the omitted count, and marks the
affected section and platform `partial`. A missing item from a truncated list is therefore
`unknown`, never absent or missing.

`build_inventory_report()` must either preserve the already validated Proxmox subtree or use a
schema-aware bounder that cannot silently apply the generic 200-list/200-key truncation to it.
The final 2 MiB serialized-report limit remains fail-closed: if the normalized report is still too
large, collection fails and emits no apparently complete report. Tests exercise each boundary,
201 generic-boundary items, the semantic maxima, omitted errors, and a report exceeding 2 MiB.

### 5.3 Completeness and freshness

Completeness is evidence about the observation, not guest power state.

- `complete` means every identity-bearing list required for the declared scope succeeded and
  every emitted object passed strict normalization.
- A failed per-node QEMU or LXC list makes the platform `partial`; absence from that list cannot
  prove guest disappearance.
- A failed guest config read makes that guest `partial`, but does not erase its VMID/name/power
  evidence from the successful guest list.
- Guest-agent unavailable is interface-section partial evidence, not proof that the QEMU guest
  itself is absent.
- A storage-content failure makes that storage entry `partial` and template availability
  unknown; it does not block unrelated VM identity ingest.
- A nauto per-guest validation/write rollback also makes the persisted platform observation
  `partial`.
- In Phase 2 no absent guest is mutated even after a complete observation. The completeness flag
  is recorded now so Phase 4 can later distinguish disappeared from unknown.
- Platform guest lists, guest identity, guest config, QEMU agent interfaces, LXC rootfs, and each
  storage-content scope have independent section state. A fresh guest-list observation does not
  make a failed config/agent/rootfs section fresh.

Freshness is monotonic:

- `collected_at` and every nested time must be timezone-aware ISO-8601. Naive values are rejected;
  accepted values are normalized to UTC before comparison.
- `max_future_skew_seconds` is owned by the server-side
  `nauto/seed/nodeutils_ingest.yaml` policy, with default `300`; it is not host supplied. A report
  newer than Job receipt time plus this allowance is rejected before Device, Cluster, guest,
  interface, or IP writes.
- A future timestamp within the allowance is retained as its true observation time, not clamped to
  Job time. A beyond-skew report cannot poison monotonic state; a subsequent normal report remains
  ingestible. A pre-existing ledger timestamp beyond the same allowance is
  `invalid_ledger_future_timestamp` and needs a before-image-based repair rather than automatic
  overwrite.
- Incoming `observed_at` older than the current object observation is `stale_evidence` and cannot
  update that object.
- Equal timestamps with equal allowlisted values are no-op.
- Equal timestamps with conflicting allowlisted values are rejected as
  `conflicting_same_generation`; arbitrary last-writer-wins behavior is forbidden.
- A newer partial observation may update objects it positively observed, but may not alter
  unobserved objects.
- Job execution time and Nautobot `last_updated` are not observation time.

Every persisted section has:

- `last_attempted_at` — the newest collection that attempted the section;
- `evidence_observed_at` — the collection time that produced the retained evidence;
- `state` — `complete`, `partial`, or `absent` where complete enumeration proves absence;
- bounded closed errors and `omitted_error_count`.

`last_attempted_at` can advance after a failed attempt; `evidence_observed_at` cannot. nctl uses
the latter for freshness and exposes both, so retained old data cannot appear to come from the
newer parent observation.

Multi-generation merge keys are fixed:

| Evidence | Merge key |
|---|---|
| platform | derived provider scope key from Section 5.5 |
| guest | `(Cluster id, guest_type, vmid)` |
| storage-content scope | `(Cluster id, node, storage, content_type)` |
| interface | `(VirtualMachine id, config_slot)` |
| agent address evidence | `(VirtualMachine id, config_slot, address, prefix)` |

For a newer partial observation, each successful key replaces only that key's evidence and times.
A failed/unobserved key retains its prior evidence and `evidence_observed_at`, advances only
`last_attempted_at`/error state, and is not eligible for a fresh-presence or template-availability
claim. Parent Cluster/VM timestamps never cascade into child evidence. For a complete, untruncated
enumeration, a previously managed key not present in the new key set may transition to `absent`
under the relation rules below; no row or provider resource is deleted.

### 5.4 Nautobot prerequisite and ledger mapping

`nauto/seed/home_cluster.yaml` and `SeedHomeCluster` remain the idempotent owner of prerequisite
objects. Phase 2 adds:

- ClusterType `Proxmox VE`;
- VM roles `virtual-machine` and `lxc-container`;
- VirtualMachine statuses for `Active`, `Offline`, and `Unknown`, extending content-type
  applicability without removing current Device applicability; and
- the dedicated custom fields below with only the listed content types.

#### Cluster

| Nautobot field | Source | Rule |
|---|---|---|
| native `name` | `cluster.name` | display name; not the sole standalone identity |
| native `cluster_type` | seeded `Proxmox VE` | required provider discriminator |
| native `comments` | constant managed-by text | no raw evidence |
| `proxmox_observer_device_id` | matched report Device UUID | diagnostic/dependency provenance |
| `proxmox_identity_source` | `cluster.name_source` | `proxmox_cluster_name\|standalone_node_fallback` |
| `proxmox_scope_key` | ingest derivation | stable matching key; rules below |
| `proxmox_observed_at` | platform identity evidence time | ISO timestamp; never child-section freshness |
| `proxmox_observation_state` | final collection+ingest state | `complete\|partial` |
| `proxmox_observation_detail` | section state/time/errors | closed bounded JSON; canonical detail owner |
| `proxmox_observed_node_names` | cluster list | bounded JSON string list |
| `proxmox_node_count` | cluster count | integer completeness evidence |
| `proxmox_storage_content` | normalized storage-content entries | closed bounded JSON keyed by node/storage/type with per-entry times |

No `proxmox_cluster_id` is created because the live single-node cluster returned `null`.

#### VirtualMachine

| Nautobot field | Source | Rule |
|---|---|---|
| native `name` | guest `name` | mutable display value |
| native `cluster` | matched Cluster | stable scope |
| native `status` | raw status mapping | running→Active, stopped/paused→Offline, other→Unknown |
| native `role` | guest kind | QEMU→`virtual-machine`, LXC→`lxc-container` |
| native `vcpus` | `vcpus` | positive integer when observed |
| native `memory` | `memory_mb` | MiB, after live model/unit assertion |
| native `disk` | parsed LXC `rootfs.size_gb` only | never populated from aggregate QEMU/LXC `disk_gb` |
| `proxmox_guest_type` | guest kind | `qemu\|lxc` |
| `proxmox_vmid` | VMID | positive integer; identity with Cluster/kind |
| `proxmox_node` | owning Proxmox node | matching/scope/display |
| `proxmox_status` | raw power status | power evidence |
| `proxmox_observed_at` | guest identity evidence time | never config/agent/rootfs freshness |
| `proxmox_observation_state` | guest state after ingest | `complete\|partial` |
| `proxmox_observation_detail` | identity/config/agent/rootfs state/time/errors | closed bounded JSON |
| `proxmox_lxc_rootfs` | parsed rootfs or null | closed JSON; invalid for QEMU |
| `proxmox_interface_evidence` | config/agent/join/unmatched evidence | closed bounded JSON keyed by slot with per-section times |

#### VMInterface and IPAddress

| Nautobot field | Source | Rule |
|---|---|---|
| native VMInterface `virtual_machine` | matched VM | required parent |
| native VMInterface `name` | config slot | stable within VM; not agent name |
| native `mac_address` | unique normalized MAC | required for Phase 2 materialization |
| `proxmox_config_slot` | config slot | identity/provenance |
| `proxmox_guest_interface_name` | QEMU agent or LXC config name | display, nullable |
| `proxmox_bridge` | config evidence | display/create comparison source |
| `proxmox_interface_source` | evidence class | `qemu_config_agent_join\|lxc_config` |
| `proxmox_observed_at` | this slot's retained evidence time | does not inherit the parent VM time |
| `proxmox_presence` | complete config enumeration | `present\|absent`; partial does not change it |
| `proxmox_managed_ip_evidence` | successful ingestor-owned relations | closed JSON IDs/address keys and evidence time |
| IPAddress host/prefix | joined-agent or explicit LXC config | only valid unicast addresses |
| IPAddress↔VMInterface relation | same evidence | converges only within the recorded managed set |

Loopback, link-local, multicast, unspecified, malformed, prefix-less agent addresses, and LXC
tokens such as `dhcp` create no IPAddress relation. Reusing one exact IPAddress row and adding a
VMInterface relation is permitted when Nautobot supports the dual Device/VM observation; existing
relations are not detached. Multiple exact candidates, a model constraint that forbids the
relation, or incompatible namespace/prefix evidence is a target-local conflict.

The same MAC on the Device-level guest interface and compute-level VMInterface is legitimate
dual-layer evidence. MAC conflict checks are scoped to incompatible VMInterfaces in the same
Proxmox Cluster; they do not conflate the Device and VM realization layers.

`proxmox_interface_evidence` and `proxmox_storage_content` are JSON custom fields, but they are not
generic bags. Both have exact nested validators in nauto and nctl; unknown keys fail validation.

### 5.5 Matching, transaction, and idempotence rules

Cluster matching:

1. For `proxmox_cluster_name`, derive
   `proxmox_scope_key="cluster-name:<exact provider name>"`. Match the exact scope key under
   ClusterType `Proxmox VE`; native name is a cross-check, not a second independent key.
2. Because Proxmox exposes no usable Cluster UUID in the live case, the same provider name from a
   clearly disjoint observer/node scope is an ambiguity, not authorization to create a second
   same-named Cluster. Stop with a shared-platform conflict for operator disambiguation.
3. For `standalone_node_fallback`, derive
   `proxmox_scope_key="standalone-device:<matched observer Device UUID>"`. This is the stable
   identity; the synthesized `<hostname>-proxmox` native name is display data and may be updated
   on a proven rename of the same Device.
4. A fallback observation whose observer Device UUID changes, or a transition between fallback
   and provider-name identity, requires an explicit migration plan. It must not auto-create or
   silently rewrite scope identity.
5. Zero scope-key candidates means create only after same-name, observer, and observed-node
   conflict checks return empty.
6. One candidate means update only changed allowlisted fields.
7. Multiple candidates are a shared-platform error; do not select the first.

Guest matching:

1. Query within the matched Cluster for exact `proxmox_guest_type` and integer
   `proxmox_vmid`.
2. Zero candidates means create unless an existing same-name row would make ownership ambiguous;
   a same-name-only row is a conflict, not an implicit match.
3. One stable candidate may receive a name update.
4. Duplicate stable candidates or cross-cluster/kind conflicts roll back that guest.

Interface matching:

1. Only a joined QEMU or explicit LXC interface is eligible.
2. Match by VM plus `proxmox_config_slot`.
3. A MAC already used by an incompatible interface is a conflict.
4. Agent interface name changes do not create a second interface.

Interface/IP convergence:

1. The Job persists the exact IP relations it successfully created or adopted for each managed
   VMInterface in `proxmox_managed_ip_evidence`. This is the only set it may later detach.
2. With a newer `complete`, untruncated relevant section and unchanged slot/MAC, replace the
   managed address-key set transactionally: attach newly observed exact IPAddress rows and detach
   previously managed relations no longer observed. Never delete an IPAddress object and never
   detach a relation outside the recorded managed set.
3. A complete authoritative empty IP set detaches the prior managed relations. A partial config,
   guest-agent, address, or truncated section retains the relations and their original
   `evidence_observed_at`; nctl marks them retained/stale and does not present them as fresh.
4. A MAC change on an existing config slot is `interface_mac_changed`, an unsupported
   target-local conflict. Phase 2 neither rewrites the MAC nor detaches its relations.
5. A managed config slot absent from a complete, untruncated config enumeration becomes
   `proxmox_presence=absent`; its ingestor-managed IP relations are detached, its row is retained,
   and foreign relations remain untouched. Partial enumeration cannot mark it absent.
6. An exact IPAddress already related to a Device interface may also relate to the VMInterface
   when the live Nautobot model allows it, preserving the two observation layers. Multiple exact
   IPAddress candidates or an incompatible existing VMInterface relation is a local conflict.
7. All attachment, detachment, evidence-set, and presence changes share the guest savepoint.
   Refetch must prove the native relations and managed evidence agree before commit is considered
   successful.

Transaction boundaries:

- Invalid top-level report or unsupported nested schema: no writes for that report.
- Invalid shared platform identity or prerequisite: no virtualization writes for that report.
- Each guest runs in its own savepoint. Any exception rolls back Cluster-independent writes for
  that guest, records a bounded local result, and makes the platform partial.
- Cluster final freshness/completeness is written only after guest/storage processing determines
  the final state.
- Dry run exercises the same matching/diff/validation path inside a rollback-only transaction.
- The batch may continue to another report after one report fails, without leaving the Django
  transaction in a broken state.

No save is called when the diff is empty. This includes native fields, custom fields, M2M IP
relations, and tags. Repeat-ingest proof checks object `last_updated`, not only the summary text.

The existing `nodeutils.ingest.summary.v1` top-level contract remains compatible with nctl
observation. Each report row gains an optional bounded `proxmox` section containing:

- platform identity and final completeness;
- counts of Cluster/VM/VMInterface/IP `created`, `updated`, `unchanged`, and `skipped`;
- stable IDs after apply;
- changed allowlisted field names; and
- bounded per-guest errors.

It contains no raw report, interface dump, template list, token, or credential. Because existing
nctl Pydantic rows ignore optional additions, no summary version bump is needed; tests must prove
both old Device-only and extended rows.

### 5.6 nctl typed actual snapshot and diagnostic

Extend `nctl_core.sources.actual` additively:

- `ActualCluster`;
- expanded `ActualVirtualMachine`;
- `ActualVMInterface`;
- strict nested Proxmox observation, rootfs, interface-evidence, and storage-content models; and
- `clusters` and `vm_interfaces` collections on `ActualSnapshot`.

Before coding the query, Step 0 captures live GraphQL introspection/REST OPTIONS for Cluster,
VirtualMachine, VMInterface, and IP assignment names. The implementation then pins those exact
names in fixtures; it must not assume that the DCIM `interfaces` root also contains VMInterfaces.

The actual query reads:

- native IDs, names, Cluster membership/type, status, role, vCPU, memory, disk;
- only the dedicated `proxmox_*` keys from `_custom_field_data`; and
- native VMInterface/IP relations needed to reproduce the ledger graph.

Each JSON custom field is revalidated with `extra="forbid"` nested models. Unrelated custom fields
and `inventory_raw_json` are ignored.

The typed models retain identity source/scope key, bounded errors, omitted-error count, and each
section's state, last-attempt time, and evidence time. Freshness is computed from the section
evidence time, never the containing Cluster/VM timestamp. Native IP relations not present in the
ingestor-managed evidence set remain visible as unrelated ledger relations but are not labeled as
fresh Proxmox-observed IP evidence.

Add a read-only `nctl actual` command with `nctl.actual.v1` output. It is not drift and has no
write path. Text mode renders:

```text
observer aghub
└─ cluster aghub-proxmox  complete  observed <time>
   ├─ lxc  vmid=108  agdnsmasq  running  node=aghub
   └─ ...
```

JSON mode contains the same typed relationships, identity provenance, per-section
attempt/evidence times, bounded errors, capacity, rootfs source, interface provenance summary,
managed-versus-unrelated IP relations, storage-template identifiers, and validation errors. It
does not call the future actual Cluster `aghub-pve`, infer desired ownership, or write links.

`nctl status.v1`, current drift semantics, production composition, dashboard, and reconcile plans
remain unchanged in Phase 2.

### 5.7 Rollout and compatibility contract

The deployment order is:

1. finish and test all four participating repositories locally;
2. deploy/sync the nauto reader and seed capability first, but pause ingestion of old unversioned
   Proxmox reports during the maintenance window;
3. dry-run and apply prerequisite seed objects;
4. after user-managed pushes, update the superproject pins and deploy the exact nodeutils/helper
   revisions to `aghub`;
5. collect a fresh `nodeutils.proxmox.v1` report;
6. run nauto ingest dry-run, record before image, obtain approval, apply, and refetch;
7. repeat the identical ingest and prove no-op;
8. enable the matching nctl typed reader and diagnostic last.

Before Phase 2 live acceptance, the operator records one exact `vztmpl` `volid` from the selected
node/storage as the provisional Phase 5 LXC fixture candidate. Selection may occur only after the
new read path exposes the exact inventory; it is not copied into nintent and does not assert any
initial-access property. A subsequent fresh, complete storage-content observation must contain
the same exact `volid`. If no candidate exists, Phase 2 does not download one: actual-ledger work
may be reported `implemented`, but Phase 2 overall is `partially complete` and Phase 5 creation
remains blocked on template availability.

An old Proxmox report without the nested version is rejected for virtualization ingest; it is not
silently interpreted. Non-Proxmox Device-only reports remain supported.

The normal rollback point is immediately before the first live virtualization ingest:

- helper/nodeutils code can be rolled back to the Step 0 revisions because it performs reads only;
- seed objects may remain unused, but removing them requires a dependency audit;
- a transaction failure must refetch equal to the before image;
- a correctly identified but partially populated row may remain and be repaired by a newer
  re-ingest;
- a wrong identity, Cluster membership, or cross-guest relation is isolated from nctl matching
  and receives an exact repair plan based on the before image;
- restoring/deleting a Nautobot row requires explicit approval;
- deleting a Nautobot row never authorizes deleting a Proxmox guest; and
- disabling the nctl reader alone is not a data rollback.

## 6. Deliverables

### 6.1 Expected code/doc surfaces

`nodeutils`:

- `proxmox_inventory.py`;
- `tests/test_proxmox_inventory.py`;
- `tests/test_pvesh_helper_integration.py`;
- `README.md`.

`ansible_agdev`:

- `roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read`;
- `roles/nodeutils_pvesh_helper/tests/test_nodeutils_pvesh_read.py`;
- the collection/deployment playbook only if positive evidence or pin reporting needs adjustment;
- relevant README text.

`nauto`:

- `jobs/ingest_nodeutils_inventory.py`;
- new pure schema/diff helpers if needed to keep validation independently testable;
- `jobs/nodeutils_ingest_summary.py`;
- `jobs/seed_home_cluster.py`;
- `seed/home_cluster.yaml`;
- `seed/nodeutils_ingest.yaml` if a nested-version policy allowlist is added;
- unit and Nautobot-environment tests;
- `README.md` and `README_DEV.md`.

`nctl`:

- `src/nctl_core/sources/actual.py`;
- a small actual-diagnostic library/render module;
- `src/nctl_core/cli/main.py`;
- source, observation-compatibility, renderer, and CLI tests;
- `README.md`.

Superproject:

- `devdocs/big/vm/p2/plan.md` (canonical plan filename);
- `devdocs/big/vm/p2/report2.N.md` step reports;
- final submodule pointer updates after tested commits.

The implementation may split large modules, but it must not duplicate schema validation or
matching rules across Job, CLI, and tests.

### 6.2 Raw evidence

Store private execution evidence under `.local/vm-p2/<run-id>/`, mode `0700` with files `0600`:

- starting revision/status manifest;
- live GraphQL/REST schema probes;
- pre/post helper digest and remote nodeutils revision;
- sanitized fresh nodeutils report or a private raw copy;
- seed and ingest dry-run summaries;
- before/refetch/repeat ledger snapshots containing only allowlisted fields;
- nctl actual JSON;
- object IDs and `last_updated` comparison;
- command manifest with time, cwd, secret-free argv, exit code, and SHA-256.

Committed reports include only allowlisted values, counts, public object IDs where useful, schema
versions, timestamps, digests, and assertions. They do not include the Nautobot token, raw
provider response, private key material, SSH key blobs, or unrelated private prose.

## 7. Procedure

### Step 0 — Safety preflight and live contract recheck

1. Record root/submodule revisions and dirty state without modifying unrelated work.
2. Record the current live counts and allowlisted fields for ClusterType, Cluster,
   VirtualMachine, VMInterface, and relevant IPAddress rows.
3. Capture GraphQL introspection/REST OPTIONS for exact native field/root/relation names and
   native `memory`/`disk` units, including whether one IPAddress may relate to both Device and
   VMInterface objects and the exact detach API/ORM shape.
4. Inspect the live `/cluster/status` evidence and positively classify `aghub-proxmox` as
   provider-supplied or `standalone_node_fallback`; record the source row, observer Device UUID,
   and rename/migration baseline without assuming from the rendered name.
5. Record current nauto Git Repository revision/Job availability, current future-skew policy, and
   current nctl query success.
6. Record remote `/opt/nodeutils` HEAD, tree status, helper digest, and current report metadata.
7. Confirm `.local/vm-p2/<run-id>/` is ignored and private before saving evidence.
8. Assert no credential value appears in argv, logs, or report paths.

Gate: starting state, exact live API/relation shape, Cluster-name provenance, time policy, and
rollback revisions are known. If the source changed from this plan's manifest, audit the changed
paths before Step 1.

Output: `report2.0.md`.

### Step 1 — Implement and freeze the normalized observation contract

1. Add the nested schema constant and pure validators/normalizers.
2. Replace interface overwriting with separate config/agent collections and deterministic join.
3. Correctly extract QEMU config MACs from model-prefixed NIC values.
4. Normalize MACs once and record invalid/duplicate evidence.
5. Parse LXC rootfs storage, volume, and exact size independently of aggregate disk.
6. Add explicit collection state/error propagation instead of swallowing failures as empty data.
7. Implement deterministic semantic limits, truncation errors, omitted-error counts, and
   protection from the generic 200-item bounder.
8. Remove unrestricted raw fields from the v1 nested output.
9. Add golden fixtures for clustered/fallback identity, the Phase 1 live `aghaos` join, and the
   `agdnsmasq` LXC case.

Gate: schema fixtures validate exactly; intended QEMU/LXC actions are positive assertions;
cluster provenance is explicit; limits cannot silently truncate; and unknown keys/malformed data
fail at the correct shared or local scope.

Output: `report2.1.md`.

### Step 2 — Extend and prove the read-only storage-content boundary

1. Add an exact `_STORAGE` identifier grammar to the helper.
2. Allow only `/nodes/{node}/storage/{storage}/content`.
3. Add negative tests for traversal, query strings, whitespace, shell syntax, extra path
   segments, invalid node/storage identifiers, and any write/status path.
4. Update nodeutils to query content only for storages advertising `vztmpl`.
5. Filter returned items to the Section 5.2 allowlist.
6. Extend the cross-repository helper integration test so the new path actually executes.
7. Verify the helper still imports no subprocess/shell path and always dispatches `pvesh get`.

Gate: positive logs prove the exact content path ran, every negative path is rejected before
`execve`, and no write verb/path is possible.

Output: `report2.2.md`.

### Step 3 — Add Nautobot prerequisites and strict ingest parsing

1. Extend the seed Job/YAML with ClusterType, roles, status content types, and exact custom fields.
2. Add dry-run diffs for prerequisite objects; do not hide content-type changes.
3. Add a strict `nodeutils.proxmox.v1` parser independent of ORM writes.
4. Validate shared scope first, then guest/storage items independently.
5. Add closed error codes and bounded error evidence.
6. Require aware timestamps, normalize UTC, and reject beyond-policy future skew before writes.
7. Preserve Device-only report behavior and extended summary compatibility.
8. Test missing/unknown schema, unknown key, wrong type/unit, duplicate stable identity, malformed
   MAC/rootfs/storage content, future skew, and one-bad-guest isolation.

Gate: pure tests prove the exact report-to-candidate contract and beyond-skew rejection before any
ORM write is added.

Output: `report2.3.md`.

### Step 4 — Implement idempotent Cluster and guest upsert

1. Implement provenance-aware clustered/fallback scope-key matching and rename/migration
   ambiguity failure.
2. Implement Cluster create/update/no-op diffing.
3. Implement guest matching by Cluster/kind/VMID, with same-name conflict protection.
4. Map native status/role/capacity and dedicated custom fields.
5. Enforce monotonic observation time.
6. Persist bounded errors and section state/attempt/evidence times.
7. Implement stable-key multi-generation merge without parent-time inheritance.
8. Add per-report and per-guest transaction/savepoint handling.
9. Ensure one guest failure does not commit any row/relation for that guest.
10. Finalize Cluster completeness only after all local outcomes are known.
11. Extend the summary with bounded per-object results.

Gate: ORM-level or environment-backed tests prove clustered/fallback matching, create, rename,
update, stale/future reject, equal-conflicting reject, per-guest rollback, multi-generation
partial merge, and no `save()` for an identical object.

Output: `report2.4.md`.

### Step 5 — Implement reliable VMInterface and IP relations

1. Convert only joined QEMU and explicit LXC interface candidates.
2. Match interfaces by VM/config slot and enforce normalized MAC compatibility.
3. Create/update native VMInterface fields and exact provenance fields.
4. Validate address family/prefix and exclude unsafe/non-routable classes named in Section 5.4.
5. Attach only exact reliable IP evidence and record the ingestor-managed relation set.
6. Implement complete-section attach/detach/absent convergence only within that managed set.
7. Retain relations and their old evidence time on partial input; never present them as fresh.
8. Stop on MAC change or incompatible foreign ownership without detaching foreign data.
9. Retain unmatched evidence only in the bounded diagnostic field.
10. Verify multi-NIC guests do not cross-pair interfaces.

Gate: relation tests prove positive QEMU join and LXC config cases actually create the expected
interface/IP relation; complete IP change/empty/disappearance converges only managed relations;
partial input retains old-time evidence; and unmatched/ambiguous/foreign cases do not mutate
unowned relations.

Output: `report2.5.md`.

### Step 6 — Extend nctl typed actual state and add read-only diagnostic

1. Pin the live GraphQL roots/relations from Step 0 in the query and fixtures.
2. Add strict Cluster/VM/VMInterface/storage/rootfs/interface evidence models.
3. Read only native and dedicated allowlisted fields.
4. Preserve current Device/interface/IP consumers and `ActualSnapshot` compatibility.
5. Add `nctl actual` library, `nctl.actual.v1` envelope, text renderer, JSON output, and CLI.
6. Render observer→Cluster→guest membership, identity provenance, per-section
   attempt/evidence time, and managed/retained relation status.
7. Report malformed dedicated JSON as a structured read error; never silently accept unknown
   nested keys.
8. Assert `nctl status`, current drift, production, and observation-summary behavior remains
   unchanged.

Gate: query fixture and CLI tests positively contain `agdnsmasq` VMID 108 under
`aghub-proxmox`, and raw/unrelated custom data does not enter the typed output.

Output: `report2.6.md`.

### Step 7 — Full automated and fixture-backed verification

Run the Section 8 command matrix and the highest-practical local multi-round test:

```text
v1 report fixture
  -> ingest dry plan says exact creates
  -> apply in rollback-capable test DB/environment
  -> typed refetch has exact graph
  -> identical ingest
  -> zero writes and unchanged timestamps
```

Also run one batch with a good QEMU guest, good LXC guest, and malformed guest to prove only the
malformed guest rolls back and platform completeness becomes partial.

Run multi-generation fixtures in which storage B, guest config, and guest-agent sections fail
after an earlier complete observation. Assert successful keys advance, failed keys retain their
old evidence time, parent times do not leak, and a later complete observation converges IP and
presence state.

Gate: all focused and integration tests pass from documented working directories; no test passes
with an empty guest list, unused helper path, empty ingest action set, or absent refetch target.

Output: `report2.7.md`.

### Step 8 — Coordinated deployment and fresh read-only collection

1. Commit participating submodule changes in reviewable units.
2. Ask the user to push the commits required by GitHub-backed nauto/nodeutils deployment.
3. Sync/deploy the nauto reader; pause old Proxmox ingest during the compatibility window.
4. Run prerequisite seed with `dry_run=true`; review exact creates/updates.
5. After approval, apply seed and refetch every prerequisite.
6. Update the superproject nodeutils/helper pins.
7. Deploy the exact helper/nodeutils revisions to `aghub`.
8. Collect through the supported non-root Ansible path.
9. Assert the helper content path actually ran, the report is v1/positive/non-empty, and
   `agdnsmasq` VMID 108 is present.
10. From the exact fresh `vztmpl` inventory, have the operator record one provisional Phase 5
    candidate `volid`; perform another fresh collection and assert the identical `volid` is
    present in a complete storage-content scope.
11. Recheck that no Proxmox guest/resource state changed.

Gate: fresh supported observation exists, prerequisite Nautobot objects match the plan, Cluster
identity source is proven, and the same exact candidate `volid` appears in a second complete fresh
storage observation. If the candidate assertion cannot pass, record Phase 2 as partially complete
and do not fetch/download a template in this phase.

Output: `report2.8.md`.

### Step 9 — First live ingest, refetch, and repeat-ingest proof

1. Save a sanitized before image of all rows/fields/relations in scope.
2. Run ingest `dry_run=true`.
3. Assert exact expected Cluster/guest/interface/IP actions and no unrelated target.
4. Stop for separate apply approval.
5. Apply once.
6. Refetch stable IDs, Cluster membership, guest kind/VMID/node, capacity sources, freshness,
   identity provenance, per-section times/errors, interface provenance, rootfs, exact candidate
   template `volid`, storage content, and managed/unrelated IP relations.
7. Run nctl typed fetch/`nctl actual --json` and compare the same graph.
8. Run the identical ingest again.
9. Assert zero creates/updates, identical IDs/relations/allowlisted values, and unchanged
   `last_updated`.
10. Confirm unexplained guests remain informational actual rows and no deletion occurred.

Gate: the full live transition, exact candidate-template evidence, and no-repeat property are
proven. An empty action set on the first run or a non-empty action set on the identical repeat is
a failure.

Output: `report2.9.md`.

### Step 10 — Final audit, documentation, and phase report

1. Run final full tests and `git diff --check`.
2. Record final revisions and working-tree status.
3. Compare Proxmox guest list/state/resource data with the Step 0 baseline.
4. Compare desired rows, generated inventories, known_hosts, and unrelated Nautobot rows with
   their baselines.
5. Scan tracked reports/diffs for credentials, raw provider bodies, private keys, SSH key blobs,
   and private prose.
6. Record raw-evidence retention owner/date.
7. Complete an exit-criteria table with `met`, `unmet`, or `not applicable` and exact evidence.
8. Mark the phase precisely: `complete`, `partially complete`, `implemented, not deployed`, or
   `blocked`.

The final status cannot be `complete` without the exact candidate `volid` gate. Missing template
availability makes this phase `partially complete` and blocks Phase 5 creation, but it does not
retroactively invalidate correctly implemented and proven actual-ledger ingestion.

Gate: every completion claim has positive evidence and no unauthorized mutation is hidden.

Output: `report2.10.md`.

## 8. Verification Plan

### 8.1 Repository commands

Use the repository-standard commands from the named working directory. If the environment
requires a different supported command, record it rather than silently skipping tests.

```bash
# repository root
uv run --project nodeutils pytest \
  nodeutils/tests/test_proxmox_inventory.py \
  nodeutils/tests/test_pvesh_helper_integration.py

(cd ansible_agdev && \
  python3 -m unittest roles.nodeutils_pvesh_helper.tests.test_nodeutils_pvesh_read)

(cd nauto && python3 -m unittest discover -s tests)

uv run --project nctl pytest \
  nctl/tests/test_sources_actual.py \
  nctl/tests/test_observation.py \
  nctl/tests/test_actual_render.py \
  nctl/tests/test_cli_actual.py \
  nctl/tests/test_compatibility_snapshots.py
```

Add the actual new test filenames to the commands if implementation chooses different module
names. Run the broader affected project suites before deployment.

### 8.2 Required scenario matrix

| Area | Required cases |
|---|---|
| schema | exact v1; missing/unknown version; unknown key; wrong scalar/container type; deterministic limits; 201-item generic boundary; semantic truncation; omitted errors; >2 MiB fail-closed |
| cluster | provider-name and standalone-fallback provenance; single-node null provider ID; same observer hostname rename; fallback observer change; fallback↔clustered transition; same name/disjoint scope; duplicate scope key; missing name; partial/truncated node list |
| guest identity | QEMU and LXC; duplicate names/different VMIDs; duplicate VMID/kind; cross-Cluster conflict |
| capacity | vCPU/memory units; LXC rootfs parse; malformed/missing rootfs; aggregate disk never used as root; QEMU root absent |
| QEMU interface | unique MAC join; config-only; agent-only; unique-but-different; duplicate config MAC; duplicate agent MAC; invalid/missing MAC; partial agent results |
| LXC interface | static CIDR; DHCP token; missing MAC; duplicate MAC; multiple net slots |
| IP/interface convergence | IPv4/IPv6 with prefix; missing prefix; loopback/link-local/multicast/unspecified; Device/VM dual relation; foreign relation; complete IP change; authoritative empty; partial retention; MAC change; complete disappearance; later recovery |
| storage | exact allowed path; invalid paths; exact candidate `volid` present/missing; malformed item; truncation; one-scope partial merge; later recovery |
| freshness | aware UTC; naive reject; newer; older; equal identical; equal conflicting; future within skew; future beyond skew; rejected-future then normal recovery; invalid future ledger |
| multi-generation merge | storage `(node,storage)`; guest identity/config/rootfs split; interface slot; agent failure; retained evidence time; no parent-time inheritance |
| transaction | invalid report zero writes; shared platform rollback; one bad guest isolated; batch continues |
| idempotence | first create; changed update; identical no-op; unchanged `last_updated`; no duplicate M2M relation |
| nctl | strict custom JSON; unrelated custom keys ignored; identity source/scope; Cluster/VM/VMInterface membership; section attempt/evidence times; bounded/omitted errors; managed/retained/unrelated IP display; existing Device consumers unchanged |
| live | `aghub` Cluster-name source proven; non-empty fresh collection; `agdnsmasq` positive match; exact candidate `volid` in two complete observations; first dry-run/apply/refetch; identical repeat no-op |

### 8.3 Positive evidence requirements

A test or live check does not pass merely because no exception occurred. It must assert:

- the new helper path was invoked when storage content is under test;
- the expected QEMU/LXC guest was parsed;
- the expected Cluster/VM/VMInterface/IP action was planned and, in apply tests, executed;
- the expected stable scope identity, source provenance, and membership were refetched;
- partial input produced partial section state, retained original child evidence time, and did not
  mutate absent guests;
- a complete relation change affected only the ingestor-managed set;
- the exact candidate template `volid` was present in a complete fresh section; and
- identical repeat produced no save and no timestamp change.

## 9. Sequence and Dependencies

```text
Step 0 live/API/revision baseline
  -> Step 1 normalized schema and provenance
  -> Step 2 helper + storage-content read boundary
  -> Step 3 seed + strict parser
  -> Step 4 Cluster/VM upsert + transactions
  -> Step 5 VMInterface/IP relations
  -> Step 6 nctl typed reader + diagnostic
  -> Step 7 full automated verification
  -> Step 8 coordinated deploy + fresh read-only collect
  -> Step 9 approved first ingest + refetch + repeat
  -> Step 10 final audit/report
```

The parser must be frozen before ORM writes. Interface materialization must not begin before join
provenance is correct. The nctl reader is enabled only after the ledger writer and live fields are
deployed. Phase 3 must not seed desired compute records until Phase 2 has passed the live
idempotence gate.

## 10. Phase Handoff

Phase 2 hands Phase 3/4:

- stable actual Cluster and guest IDs with provider/fallback identity provenance;
- exact Cluster/kind/VMID matching fields;
- typed power/capacity/rootfs evidence with per-section attempt/evidence times;
- typed interface provenance and safely convergent ingestor-owned IP relations;
- current complete evidence for one exact operator-recorded template `volid`;
- explicit platform/guest completeness;
- bounded structured observation errors and truncation evidence;
- a read-only actual graph; and
- a proven non-destructive repeat-ingest path.

It does not hand off an implicit desired link. Phase 3 creates only operator-confirmed
`DesiredComputePlatform`, `DesiredComputeInstance`, and endpoint MAC intent. Phase 4 performs
explicit dry-planned ledger linking and compute drift.

If implementation discovers a need for another persisted provider field, raw key, matching
fallback, interface guess, credential location, or destructive action, stop and update the field
classification/contract with a named consumer and safety proof. Do not extend
`nodeutils.proxmox.v1` or the ledger opportunistically.
