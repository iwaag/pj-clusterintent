# Phase 1 Implementation Plan: Freeze the Minimal Contract and Live Baseline

Parent roadmap: [VM Platforms and Proxmox Guest Reconciliation](../roadmap.md) — Phase 1

## 1. Purpose

The purpose of this phase is to inspect the Proxmox VE installation on `aghub` and the existing
`agdnsmasq` LXC through read-only paths, then freeze a contract that Phases 2 and later can
implement without guesswork.

Phase 1 does not change desired state, the Nautobot ledger, any Proxmox guest, any target host, or
the SSH trust store. It also does not yet implement model, migration, ingest, drift, or actuator
code. Its only implementation deliverables are documents that pin the investigation procedure,
strict contracts, migration sequence, safety boundaries, and verification results.

The intended transition is:

```text
Start:
  Proxmox facts exist in nodeutils reports but normal ingest does not consume them
  + no desired compute model exists
  + DesiredNode.realized_vm may conflict with the meaning of compute realization
  + the manual initial-access and SSH-trust gates after guest creation are not defined

End:
  fresh read-only Proxmox evidence
  + live Nautobot object/schema evidence
  + one unambiguous agdnsmasq platform/instance/NIC mapping
  + versioned observation/model/API/YAML contracts
  + an explicit manual LXC initial-access/SSH-enrollment stop/resume contract
  + coordinated Phase 2/3 rollout and rollback contracts
```

Completion evidence belongs in `devdocs/big/vm/p1/report.md`. Raw inventory, Braindump prose,
tokens, SSH key blobs, and generated inventories that may contain personal information must not be
committed.

## 2. Phase 1 Exit Criteria

Phase 1 is `complete` only when every item below is satisfied.

1. The inspected commit SHA for the superproject and every submodule, local time, and
   Proxmox/Nautobot observation times are recorded.
2. A fresh Proxmox observation has been collected read-only from `aghub` using the exact nodeutils
   commit pinned by the superproject.
3. The live source paths, types, units, and missing-value semantics are pinned for cluster, node,
   QEMU, LXC, VMID, power, capacity, configured NICs, guest-agent NICs, and LXC `rootfs`.
   The storage-content path and types that Phase 2 will use to verify template availability are
   also pinned.
4. The live Nautobot representation of `aghub`, `agdnsmasq`, Cluster, VirtualMachine,
   VMInterface, IPAddress, and CustomField objects is recorded, together with the native fields
   Phase 2 can use.
5. Normal nodeutils-to-nauto ingest is selected as the sole owner of virtualization-ledger
   writes, and the old self-registration write path is explicitly rejected.
6. Every persisted field is classified as `Intent`, `Derived/contract`, or
   `Actual link/cache` and has a named drift, planning, actuation, safe-identification, or
   freshness consumer.
7. The proposed platform, instance kind, VMID, Proxmox node, primary endpoint, MAC, bridge, and
   NIC slot for `agdnsmasq` map uniquely. Values come from live evidence, not the illustrative
   roadmap example.
8. The disposable LXC has an explicit `waiting_for_manual_initial_access` gate. The report names
   the operator-owned manual procedure and completion checks for the Ansible user, approved public
   key, privilege path, SSH service, mDNS service, hostname, and unique SSH host keys. No template
   property or automatic bootstrap mechanism is assumed. Live template availability remains
   unverified until Phase 2 obtains fresh storage-content evidence.
9. The out-of-band source for initial SSH host-key verification and the
   `waiting_for_manual_initial_access -> waiting_for_ssh_enrollment -> nctl ssh enroll -> resume`
   procedure are explicit and dry-walked rather than assumed.
10. Versioned contracts and rollout/rollback points are pinned for nodeutils observation, nauto
    ingest, nintent model/API/YAML/GraphQL, and the nctl snapshot.
11. Pre-schema-change baselines for `nctl drift`, hosts-intent render, production render,
    Braindump metadata, and generated inventories are retained locally. Existing artifacts have
    digests; missing artifacts have an `absent` status. Only safe summaries remain in the report.
12. Before/after comparison proves that no live state, remote file, Nautobot row, known_hosts
    entry, or desired state changed beyond modifications already present at the start.

If any item is unverified, substituted, or unexercised, the phase is `partially complete` or
`blocked`, and the report names the gap. An empty Proxmox guest list, empty interface evidence, a
stale report, or a successful exit code alone is not execution evidence.

## 3. Non-goals and Safety Boundary

Phase 1 does not perform any of the following:

- implement models or migrations for `DesiredComputePlatform`, `DesiredComputeInstance`, or
  `DesiredEndpoint.mac_address`;
- create, update, or delete Nautobot Cluster, VirtualMachine, VMInterface, IPAddress, or
  CustomField objects;
- create, update, or import nintent records, or migrate `DesiredNode.realized_vm`;
- run the nauto ingest Job or any non-dry-run Job;
- deploy nodeutils, the privileged helper, or an Ansible role, or update a remote checkout;
- run `nctl reconcile --yes`, push status through `nctl dashboard`, or run
  `nctl ssh enroll --yes`;
- create, start, stop, resize, move, clone, or delete a Proxmox guest;
- modify dnsmasq, IPAM, or known_hosts;
- select or implement a golden-template, cloud-init, OpenTofu, `pct exec`, or other automatic
  initial-access mechanism;
- select the QEMU initial-access mechanism; or
- design AWS, Azure, or generic/custom providers.

`ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml` clones or updates code, installs
packages and the helper, and writes a remote report. It must not be used for the Phase 1 live
observation. Phase 1 runs an already-installed collector whose pin matches the superproject, in
stdout mode. A pin mismatch or missing helper is recorded as a blocker; it is not repaired or
deployed around.

Read-only commands still save API responses and inventory on the controller. Raw evidence is
stored under `.local/vm-p1/<run-id>/` in a mode `0700` directory, with files at mode `0600`.
Nothing is moved into Git. Raw evidence is retained until the report review is complete. It is
then deleted with explicit user approval, or its retention owner and date are recorded in the
report. Braindump prose is not written even to this raw evidence directory.

## 4. Current Implementation Baseline

The following facts were confirmed by source audit when this plan was written on 2026-07-24.
Phase 1 re-records all commit SHAs and updates the report if the source has changed.

### 4.1 nodeutils and the privileged read boundary

- `nodeutils/nodeutils_collect.py` emits top-level schema `nodeutils.inventory.v2` and includes
  the result from `nodeutils/proxmox_inventory.py` under `facts.proxmox`.
- The collector reads `/cluster/status`, `/cluster/resources`, `/nodes`, per-node
  QEMU/LXC/config/storage/network data, and QEMU guest-agent interfaces through `pvesh get`.
- When any guest-agent interface exists, `normalize_qemu_vm()` replaces the configured-interface
  list. It cannot therefore preserve bridge/NIC-slot evidence and guest-agent IP provenance at
  the same time.
- Current QEMU/LXC `disk_gb` comes from aggregate `maxdisk`/`disk`; it is not exact evidence for
  LXC rootfs or a QEMU root/boot disk.
- `ansible_agdev/roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read` has a closed read-only
  path allowlist, but does not yet allow
  `/nodes/{node}/storage/{storage}/content`, which template-availability observation needs.
- The current helper can execute only `pvesh get`. Phase 1 does not weaken that boundary.

### 4.2 nauto and the Nautobot actual ledger

- `nauto/jobs/ingest_nodeutils_inventory.py` currently upserts Devices and allowlisted Device
  custom fields.
- Normal ingest neither materializes `facts.proxmox` as Cluster/VirtualMachine/VMInterface
  objects nor places it in `inventory_raw_json`.
- Historical `nodeutils/nautobot_self_register.py` and Proxmox upsert code exist in nodeutils Git
  history, including Proxmox registration commit `9ab3abd`, but not at current HEAD. Phase 1 uses
  this history only to audit ownership and field mapping; it does not restore the old writer.

### 4.3 nintent desired model

- `DesiredNode` has both `realized_device` and `realized_vm`, each with `derived|override`
  provenance.
- `DesiredEndpoint` owns IP/DNS/mDNS intent and an actual IP link, but has no desired MAC field.
- `@extras_features("graphql")` provides GraphQL reads, while REST provides selected write
  surfaces.
- The YAML loader/importer supports roots such as `desired_nodes` and `desired_endpoints`, but no
  compute platform or instance roots.

### 4.4 nctl

- The desired snapshot reads `DesiredNode.realized_vm`.
- The actual snapshot reads only `id` and `name` for VirtualMachine objects. It has no Cluster,
  VMID, guest-kind, power, capacity, freshness, or interface-provenance data.
- Production composition supports only Device realization for actual-backed composition;
  VirtualMachine realization produces `unsupported_actual_type`.
- Bootstrap `select_mdns_endpoint()` has a sorted-first fallback after endpoint-type priority.
  Compute NIC selection must not reuse it.
- DHCP reservation rendering currently depends on observed MAC candidates. A new guest needs an
  explicit change that prefers desired MAC before the guest is observable.
- `nctl ssh enroll` and the stable DesiredNode UUID alias trust store already exist. Initial guest
  enrollment reuses them rather than creating another trust store.

### 4.5 Local environment

- Nautobot is available at `http://localhost:8000/`.
- The existing `nctl.toml` reads the token through `.local/secrets` using `token_file`. The value
  must never appear in command arguments, reports, conversation, or logs.
- Generated inventories existed in the checkout when this plan was written, while
  `.local/localenv_memo.md` describes an older state. Neither is the authoritative runtime
  baseline. Step 0 rechecks each path as `present|absent`, recording a digest for present files
  and the check time for absent files.
- The known unreachability of `agdnsmasq.local` does not fail the Proxmox-side observation. Guest
  OS reachability is recorded as a separate layer.

## 5. Contracts to Freeze in Phase 1

The semantic set in this section does not change the parent roadmap. If live audit requires a name
or value adjustment, the report decision log records the reason, consumer, and affected phase.

### 5.1 Ownership

| Value or operation | Sole owner |
|---|---|
| Logical node and guest-OS identity | `DesiredNode` |
| Guest-OS actual link | `DesiredNode.realized_device` |
| Desired IP/DNS/mDNS/MAC | `DesiredEndpoint` |
| Compute-platform intent | `DesiredComputePlatform` |
| Compute-guest intent and actual VM link | `DesiredComputeInstance` |
| Proxmox actual collection | nodeutils on the platform control node |
| Cluster/VM/VMInterface ledger writes | normal nauto nodeutils ingest |
| Desired reads | nintent GraphQL |
| Confirmed structured writes | nintent REST/YAML import |
| Drift, matching, planning, dependency closure | nctl |
| Ensure-present/start actuation | future nctl-to-Ansible boundary |
| Credential and actuator resolution | controller-local nctl/Ansible configuration |
| SSH trust | existing nctl-managed known_hosts plus `nctl ssh enroll` |

Proxmox platform config must not contain API URLs, credentials, commands, IPs, DNS names, or MACs.
Instance config must not duplicate endpoint data.

### 5.2 Target contract for DesiredComputePlatform

The Phase 1 report pins field type, nullability, database constraint, UI label, and
REST/GraphQL/YAML representation.

| Field | Class | Target type or rule | Consumer |
|---|---|---|---|
| `name` | Intent | non-empty string | UI and plan evidence |
| `slug` | Intent | unique stable slug | config/instance/adapter lookup |
| `provider_type` | Contract | closed choice containing only `proxmox` | schema/adapter dispatch |
| `lifecycle` | Intent | existing planned/approved/active/deprecated/retired vocabulary | observe/link/create/start gate |
| `control_node` | Intent | FK to a suitable non-retired DesiredNode | observation/actuation dependency target |
| `config_schema_version` | Contract | exact platform-schema identifier, immutable within a row version | strict validation |
| `config` | Intent | closed Proxmox platform object | default derivation |
| `realized_cluster` | Actual link | nullable FK to Nautobot Cluster | explicit-first matching |
| `realized_cluster_source` | Actual cache | null or `derived|override`, present exactly with the link | provenance |

Platform config v1 allows only these keys:

| Key | Rule | Consumer |
|---|---|---|
| `cluster_name` | optional only when fresh observation derives it uniquely | wrong-scope guard and matching |
| `default_storage` | optional only when it can be derived uniquely | create validation and payload |
| `default_bridge` | optional only when it can be derived uniquely | single-NIC create payload |

Every write path rejects unknown keys. Drift and plan evidence always includes the derivation
source, observation time, and provenance (`intent|derived`) of an optional effective value.

### 5.3 Target contract for DesiredComputeInstance

| Field | Class | Target type or rule | Consumer |
|---|---|---|---|
| `desired_node` | Intent | one-to-one owner | scope/identity/lifecycle |
| `platform` | Intent | FK that protects platform deletion | provider scope and dependency closure |
| `instance_kind` | Intent | `container|virtual_machine` | matching/schema/adapter |
| `desired_power_state` | Intent | `running|stopped` | start plan; stop remains non-automatic |
| `vcpus` | Intent | bounded positive integer | create and drift |
| `memory_mb` | Intent | bounded positive integer, fixed to MiB | create and drift |
| `root_disk_gb` | Intent | bounded positive integer, fixed to GiB | create; drift only with exact evidence |
| `config_schema_version` | Contract | exact instance-schema identifier | strict validation |
| `config` | Intent | closed object per instance kind | safe identification and create |
| `realized_vm` | Actual link | nullable FK to Nautobot VirtualMachine | explicit-first matching |
| `realized_vm_source` | Actual cache | null or `derived|override`, present exactly with the link | provenance |

Instance config v1 allows only:

- `vmid`: optional integer; Phase 1 confirms the valid range of the installed Proxmox version;
- `template`: required for create; Phase 1 pins the LXC identifier grammar and storage relation;
- `storage`: optional override of the platform default;
- `bridge`: optional override of the platform default; and
- `unprivileged`: boolean valid only for LXC and rejected for QEMU.

CPU, memory, disk, and VMID bounds are not guessed. The report derives them from the installed
Proxmox/Nautobot fields and the safe range of the Phase 5 fixture. `template` is creation-only
intent and does not create post-creation drift without a fresh comparable actual source.

### 5.4 DesiredEndpoint.mac_address and the single-NIC rule

`mac_address` is nullable Intent, normalized before save to one canonical lower-case,
colon-separated form. Every non-null desired MAC is unique across endpoints. Model, serializer,
form, YAML loader/importer, and database constraint use the same validator.

An actionable compute instance must have exactly one endpoint on its owning DesiredNode that
satisfies all of:

- `endpoint_type == primary`;
- a canonical desired `mac_address`;
- a non-empty `mdns_name`; and
- a usable guest-NIC IP policy/address contract.

Zero candidates produce `compute_primary_endpoint_missing`; multiple candidates produce
`compute_primary_endpoint_ambiguous`. Ordering never selects one. The effective bridge resolves
once from instance override and then platform default. The Proxmox adapter derives `net0` or the
confirmed corresponding LXC slot. The slot is not stored as desired intent.

A DHCP reservation with desired MAC can render before guest observation. A mismatch with observed
MAC is a conflict and never silently rewrites desired intent.

### 5.5 Data transition for DesiredNode.realized_vm

The final sole owner of the compute link is `DesiredComputeInstance.realized_vm`. Current nctl
GraphQL, drift, production adapter, and reconcile ledger directly consume
`DesiredNode.realized_vm`, so nintent must not remove the field first.

Phase 1 first records the number and meaning of live non-null rows, then adopts this
add/migrate/remove sequence:

1. **Add:** Add compute models in the first part of Phase 3. Retain
   `DesiredNode.realized_vm` and its source as deprecated legacy fields so the existing nctl query
   continues to work.
2. **Read compatibility:** In the same bounded compatibility window, update the nctl desired
   reader. A row without DesiredComputeInstance uses the legacy link; a row with an instance uses
   the compute-instance link as canonical. Different simultaneous links are a fail-closed
   conflict. This step adds no compute drift or actuation.
3. **Operator-confirmed intent:** Create a DesiredComputeInstance containing required `vcpus`,
   `memory_mb`, `root_disk_gb`, and `template` only through a reviewed dry import. A data migration
   must not invent desired intent from actual VM capacity, aggregate disk, or template history.
4. **Link migration:** Only after an operator-confirmed instance exists, verify platform
   membership, guest kind, and stable provider identity, then move the legacy `realized_vm`
   link/provenance. Move only actual link/cache data; generate no intent. Ambiguity stops for
   explicit review.
5. **Consumer cutover:** Use GraphQL refetch, production render, fresh drift, and a link dry plan
   to prove the legacy field is no longer needed. Deploy an nctl revision that no longer queries
   the legacy field while the field still exists.
6. **Remove:** A later migration asserts that all live rows are migrated and no old query remains,
   then removes `DesiredNode.realized_vm` and its source.

Even with zero live non-null rows, Steps 1, 2, 5, and 6 remain mandatory. Zero-row evidence only
skips data movement in Steps 3 and 4; it does not justify removing the field first.

`DesiredNode.realized_device` remains the guest-OS actual link. The
`virtual_machine|container` values of `accepted_actual_types` have concrete current drift and
production consumers, so Phase 3 does not remove them. After compute-drift cutover, their
continued semantics are reviewed as a separate decision; this initiative does not delete them
automatically.

### 5.6 Versioned Proxmox observation contract

In addition to top-level `nodeutils.inventory.v2`, `facts.proxmox` receives an explicit nested
schema version. The Phase 1 report pins at least:

- platform observation time and collection completeness;
- cluster stable identity/name and observed Proxmox node;
- per-guest `guest_type`, VMID, owning node, name, and raw power status;
- vCPU and memory sources and units;
- QEMU/LXC configured interfaces;
- QEMU guest-agent interfaces;
- a joined interface created only by a unique normalized-MAC match;
- unmatched config-only, agent-only, duplicate-MAC, and missing-MAC evidence;
- parsed LXC `rootfs` volume, storage, and capacity;
- an explicit unsupported value for QEMU root/boot disk; and
- the per-node/storage fresh template storage-content evidence slot and source grammar that the
  Phase 2 collector will add.

Typed snapshots and the ledger exclude raw provider responses, utilization, uptime, task history,
and arbitrary configuration. Diagnostic raw evidence may be stored temporarily on the controller,
but is not copied into a Nautobot custom field or Git.

Interface joining follows this truth table:

| Config MAC | Agent MAC | Result |
|---|---|---|
| one unique match | one unique match | joined, retaining both provenances |
| config only | absent | config-only; retain bridge/slot, create no IP relation |
| absent | agent only | agent-only observation; do not guess a config match |
| duplicate or invalid | any | ambiguous target-local blocker |
| unique but different | unique but different | both unmatched; never join by order or name |

### 5.7 Initial access and SSH trust

Phase 1 deliberately does not select or implement an automatic LXC initial-access mechanism.
The first creation workflow treats guest bootstrap as an operator-owned manual gate. Creation and
fresh Proxmox observation may complete before guest-OS access exists, without converting the
successful compute actions into a failed create.

The manual procedure is executed through an authenticated Proxmox console or another
operator-approved out-of-band route. It establishes and then checks:

- the shared Ansible user selected by existing inventory/vault;
- that user's approved public key and required privilege path;
- a running SSH service;
- a running mDNS service advertising the primary endpoint's `mdns_name`;
- the intended per-guest hostname; and
- unique per-guest SSH host keys.

The selected LXC OS template is only a creation input. Phase 1 does not infer any initial-access
property from its name or origin. Because the current helper cannot read the storage-content path,
Phase 1 does not claim the template currently exists on live storage. It freezes the exact
read-only path/schema/least-privilege contract and prohibits Phase 5 create until Phase 2 fresh
observation proves the exact template identifier is available.

The manual gate is not represented as per-instance intent and does not accept arbitrary commands,
paths, packages, passwords, or public keys from nintent. The report names the operator, procedure
location, required outcome checklist, evidence that is safe to retain, and the condition that
advances the instance. Automating this procedure is explicitly deferred until after the core LXC
and QEMU management workflows are proven.

Initial host-key trust uses one out-of-band source independent from network keyscan, such as an
authenticated Proxmox console. The report pins the exact console command that displays host
public-key fingerprints, who compares them, and how multiple key types are handled.

```text
create/start succeeds
  -> fresh Proxmox observation and compute link succeed
  -> waiting_for_manual_initial_access (safe stop retaining successful compute evidence)
  -> operator completes and checks the manual bootstrap procedure
  -> mDNS route is reachable
  -> read-only scan returns offered public fingerprints
  -> waiting_for_ssh_enrollment (safe stop retaining successful compute evidence)
  -> operator compares an out-of-band fingerprint
  -> nctl ssh enroll <slug> --fingerprint SHA256:...   # dry plan
  -> nctl ssh enroll <slug> --fingerprint SHA256:... --yes
  -> a later reconcile resumes guest observation
```

`accept-new`, `StrictHostKeyChecking=no`, an unverified keyscan, or an assumption based on template
origin must never bypass this stop.

### 5.8 Cross-component impact matrix

The Phase 1 report explicitly records “no change in this phase” and pins the first implementation
phase and contract owner for every surface.

| Surface | Contract frozen in Phase 1 | First implementation phase |
|---|---|---:|
| nintent model/migration | fields, constraints, data transition | 3 |
| nintent UI/form/table/filter | display/edit boundary between intent and actual cache | 3 |
| YAML loader/importer | roots, identity, strict validation, transaction order | 3 |
| REST | write surface, link provenance, refetch contract | 3; link apply in 4 |
| GraphQL | exact desired roots, fields, and enum shape | 3 |
| nodeutils observation | nested schema, sources, units, provenance, completeness | 2 |
| privileged helper/Ansible | read-only storage-content path and least privilege | 2 |
| nauto ingest | Cluster/VM/VMInterface upsert owner, freshness, idempotence | 2 |
| nctl actual snapshot | Cluster/VM allowlist and typed freshness | 2 |
| nctl desired snapshot | legacy-compatible platform/instance/endpoint-MAC shape | 3; drift consumer in 4 |
| drift/status | code, severity, scope, fresh-evidence requirement | 4 |
| planner/dependency closure | desired target, platform, control node, unrelated-guest isolation | 4 |
| executor/evidence | link/create/start/manual-access/enrollment-stop action and evidence boundaries | 4/5 |
| dashboard | dual realization, provenance, freshness, blocker display | 4 |
| dnsmasq/production inventory | desired-MAC and unique compute-endpoint consumer boundary | 3/5 |
| documentation | operator workflow, unsupported actions, recovery | each phase |
| tests | focused errors and multi-round positive-action assertion | each implementation phase |

Phase 1 does not add schema or code early. A later consumer not listed here reopens the decision
log rather than silently reusing a field.

## 6. Deliverables

### 6.1 Git-managed deliverables

- `devdocs/big/vm/p1/plan.md` — this plan
- `devdocs/big/vm/p1/report.md` — execution results, decision log, sanitized baseline

The report contains at least these appendices:

1. source and revision manifest;
2. live Proxmox shape table;
3. live Nautobot object/schema table;
4. ownership audit of normal ingest and old self-registration;
5. field-classification and rejected-field tables;
6. exact model/config/YAML/GraphQL/REST contract;
7. observation-schema and freshness/completeness contract;
8. `agdnsmasq` platform/instance/endpoint/NIC mapping;
9. disposable-LXC manual-initial-access and SSH-enrollment contract;
10. finding vocabulary/classification table;
11. data migration, rollout, and rollback plan;
12. baseline artifact manifest and before/after non-mutation proof; and
13. exit-criteria checklist and phase status.

### 6.2 Raw evidence outside Git

Store the following under `.local/vm-p1/<run-id>/`:

- fresh nodeutils JSON report;
- Proxmox source-path probe results;
- Nautobot GraphQL and REST GET/OPTIONS responses;
- `nctl drift --json`;
- `nctl render hosts-intent --json`;
- `nctl render production --json`;
- Braindump metadata and prose digest produced by an allowlist sanitizer;
- a copy of generated inventories from before schema changes; and
- a command manifest with time, cwd, a secret-free argv representation, exit code, and SHA-256.

The report copies only required allowlisted fields, counts, schema version, observation time,
digest, and verification results—not raw bodies.

## 7. Procedure

### Step 0 — Safety preflight and revision manifest

1. Record `git status --short`, HEAD SHA, and superproject pin for the root and every submodule.
2. Distinguish existing user changes from Phase 1 files. Do not stash, checkout, reset, or format
   existing changes.
3. Create `.local/vm-p1/<run-id>/` at mode `0700` as a raw-evidence root outside Git.
4. Confirm only that `nctl.toml` uses `token_file` and contains no inline token. Do not display the
   token value.
5. Record generated `hosts_intent.yml`, `production.yml`, and production reports per path as
   `present|absent`. Existence is not a precondition. Digest and parse only present files.
6. Check Nautobot/API health and create side-effect-free fresh hosts-intent and production renders
   under the controller-local evidence directory. If a render returns a structured error, retain
   its envelope, scope, and exit code, distinguishing existing cluster drift from a Phase 1
   blocker.
7. Use a fresh production inventory as probe transport only if it contains `aghub` and satisfies
   the closed SSH trust contract. Otherwise, the sole fallback is the mDNS bootstrap route and
   stable DesiredNode UUID alias generated for the same `aghub` DesiredNode by a fresh
   hosts-intent render. Stop if neither contains `aghub`. Do not use a hand-written IP, another
   node, an `agdnsmasq` route, or a sorted fallback.
8. Expand temporary inventory only under a private controller-local directory. If Ansible
   transport is needed, create a controller-local read-only symlink from that inventory root to
   canonical `group_vars`, and use the `ansible_agdev` `ansible.cfg` and vault-password path.
   Stop instead of typing a user or secret if group vars or vault cannot resolve.
   Use `ansible-inventory --list` only to check parse exit and do not save stdout. Check membership
   with `--graph` or the sanitized nctl render payload so secret-bearing host vars are never
   emitted. Never place unsanitized `--host` or `--list` output in evidence, reports, or
   conversation.
9. Run a read-only SSH trust preflight for the selected `aghub` route.
10. Compare `/opt/nodeutils` HEAD with the superproject pin, and inspect the collector executable,
    execution user, root-owned helper, and helper allowlist.

**Gate:** A remote pin mismatch, broken helper, or failed trust preflight stops the phase. Do not
deploy or repair around the Phase 1 non-mutation boundary.

### Step 1 — Current data-flow and ownership audit

Trace read/write/derive/cache flow at line level through:

- `nodeutils/nodeutils_collect.py`;
- `nodeutils/proxmox_inventory.py`;
- `ansible_agdev/roles/nodeutils_pvesh_helper/`;
- `ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml`;
- `nauto/jobs/ingest_nodeutils_inventory.py`;
- historical `nodeutils/nautobot_self_register.py` and historical Proxmox upsert functions;
- `nintent/nautobot_intent_catalog/models.py`;
- forms, tables, views, filters, API serializers/viewsets, loaders, and importers;
- `nctl/src/nctl_core/sources/desired.py`;
- `nctl/src/nctl_core/sources/actual.py`; and
- drift, production adapter/composer, dnsmasq, hosts-intent, and reconcile ledger code.

Compare matching keys, field mapping, custom-field dependencies, idempotence, partial failure, and
delete/offline behavior between old self-registration and normal ingest. The report declares
normal nauto ingest the sole write owner. Only sanitized normalization and mapping knowledge may
be reused from the old path.

### Step 2 — Fresh read-only Proxmox observation

1. Before execution, record `/opt/nodeutils` HEAD and tracked-file digest/status, the existing
   `.venv` entry point, helper digest/owner/mode, and the existing remote report digest/mtime.
2. Use the verified normal nodeutils user and existing `/opt/nodeutils/.venv/bin/nodeutils` entry
   point whose pin matched in Step 0. The exact command contract is:

   ```text
   env PYTHONDONTWRITEBYTECODE=1 \
     /opt/nodeutils/.venv/bin/nodeutils collect \
     --proxmox enabled --format json
   ```

   Do not use `uv run`, dependency sync, root execution, or `--output`.
3. If Ansible is the transport, use a local-only probe playbook with
   `changed_when: false`, `failed_when: false`, `become_user: <verified nodeutils user>`, and
   `PYTHONDONTWRITEBYTECODE=1`. Apply no role, copy, git, package, template, or file module to the
   remote host. Mark the collector and controller-local capture tasks `no_log: true`; save
   registered stdout/stderr/exit code only through `delegate_to: localhost` into a private mode
   `0600` file. Use `copy` only for this controller-local capture and never save inventory/vault
   variables. After capture, a sanitized assertion task treats nonzero exit as failure and
   displays only schema, timestamp, counts, and exit code.
4. Assert in the manifest that argv contains no `--output`. After execution, prove tracked
   checkout status/digest, helper, and existing remote report digest/mtime are unchanged. If the
   existing executable/environment cannot satisfy this, deploy nothing and record a blocker.
5. Assert `collected_at`, schema, collector identity, and `facts.proxmox.enabled` from stdout.
   Do not substitute an existing `/var/lib/nodeutils/inventory.json` as fresh evidence.
6. Positively assert not only cluster/node/QEMU/LXC counts, but also `agdnsmasq` guest kind, VMID,
   owning node, power, capacity source, configured NIC, MAC, bridge, and rootfs evidence.
7. For a guest that returns QEMU guest-agent data, check whether the current schema actually loses
   configured-interface evidence.
8. Confirm the selected storage from the storage list. The storage-content path is outside the
   current helper allowlist, so do not bypass it with direct root `pvesh` or helper edits. Pin the
   minimal Phase 2 allowlist extension and its tests.
9. Confirm the raw LXC `rootfs` grammar and unit. Equality with aggregate `maxdisk` does not make
   them the same source.

**Gate:** An empty Proxmox list, missing `agdnsmasq`, unknown collection time, or swallowed
collector error does not count as a confirmed live shape.

### Step 3 — Live Nautobot schema and object baseline

Use the existing nctl config/client for read-only GraphQL/REST probes without expanding the token
into a process argument. Inspect:

- Device, interface, assigned IP, status, role, and custom fields for `aghub` and `agdnsmasq`;
- Cluster, VirtualMachine, VMInterface, and IPAddress fields, types, and relations;
- existing Cluster/VM objects and the `agdnsmasq` VM candidate;
- existence, content type, type, and required/unique behavior of `proxmox_*` custom fields;
- exact GraphQL root and field names and ChoiceField serialization;
- REST endpoints, GET representation, and OPTIONS metadata;
- required model/object permissions and any current user/role grants available read-only;
- live values and provenance for `DesiredNode.realized_device` and `realized_vm`; and
- duplicate names/VMIDs, stale rows, and orphan interfaces/IPs.

Send only GET, GraphQL queries, and OPTIONS. Do not run Jobs or send POST, PATCH, PUT, or DELETE.
Do not write a candidate link.

`OPTIONS` and `Allow` prove only method availability, not successful field- or object-level write
permission. Phase 1 records the required Phase 3/4 permission contract and, when possible, a
static comparison with current grants. Proof that the real token can PATCH remains at the Phase
3/4 approved-write-and-refetch gate.

### Step 4 — Unambiguous agdnsmasq mapping

Join evidence by stable identity and freeze one row containing:

```text
DesiredNode agdnsmasq
  -> proposed DesiredComputePlatform
  -> observed Nautobot Cluster candidate
  -> proposed DesiredComputeInstance
  -> observed Proxmox node + guest_type + VMID
  -> observed Nautobot VirtualMachine candidate
  -> one primary DesiredEndpoint
  -> desired/proposed MAC + observed config MAC
  -> effective bridge
  -> derived NIC slot
```

Do not join only on `name == agdnsmasq`; use platform scope, guest kind, VMID, and normalized MAC.
Because the desired MAC model does not yet exist, a MAC taken from observation is labeled
`operator confirmation required` if shown as proposed intent, and is not written to desired
state.

Zero or multiple endpoint candidates, duplicate MACs, a conflict between Proxmox config and a
Nautobot interface, or unknown Cluster membership leaves the exit criterion unmet.

Apply the same rule to the proposed endpoint of the disposable LXC fixture and confirm that all
intent fields required before creation can be enumerated.

### Step 5 — Freeze the observation and ledger contract

Using the live shapes from Steps 2 and 3, define the Phase 2 strict nested Proxmox schema field by
field. For each field, record:

- source `pvesh` path and provider key;
- normalized type, unit, and enum;
- stable identity versus volatile observation;
- freshness owner and observation time;
- meaning under complete and partial collection;
- Nautobot native-field or dedicated-custom-field mapping;
- nctl typed-snapshot field;
- matching, drift, and display consumers; and
- finding code and scope for missing, malformed, or duplicate data.

One absent guest in one collection never deletes a Cluster/VM or marks it offline. Unless
collection completeness is proven, “not seen” must not become “does not exist.”

For the storage-content helper extension, pin the exact path grammar, storage-identifier grammar,
the fact that only the equivalent of `get` is permitted, and negative path tests.

### Step 6 — Freeze the desired model, API, and YAML contract

For every Section 5 field, decide and turn into a Phase 3 implementation checklist:

- Django field type, `on_delete`, null/blank, choice, default, index, and constraint;
- responsibility split between model `clean()` and transaction-wide validation;
- normal form, list/detail table, and filter;
- REST serializer/viewset read/write/read-only fields;
- GraphQL root/field and enum representation;
- YAML root, identity key, strict unknown-key failure, and transactional import order; and
- nctl pydantic desired-snapshot field.

The YAML roots are:

```yaml
desired_compute_platforms: []
desired_compute_instances: []
```

An actual link specified through ordinary CRUD/import gets `override` provenance. An explicit nctl
derived-link action sends the relation and `*_source=derived` in the same PATCH. Reject a relation
without source, a source without relation, silent replacement of an existing link, and a VM link
to another Cluster.

### Step 7 — Field classification and rejected-field audit

Create a table for every retained field with:

```text
model/schema | field | class | owner | source | consumer
validation | freshness | output surfaces | missing behavior
```

The rejected-field table includes, by default:

- API URL, username, token ID, TLS flag, secret or vault reference;
- CPU model, sockets, NUMA, ballooning, BIOS/UEFI, machine type;
- arbitrary arguments, config, or cloud-init;
- utilization, uptime, task/history, HA, replication, backup, or snapshot policy;
- bind mounts, passthrough, USB/PCI, or tags;
- provider-generic, AWS, or Azure fields;
- duplicate IP/DNS/MAC ownership or persisted `net0`; and
- any field that calls QEMU aggregate `maxdisk` the root disk.

Moving a rejected field into the retained set requires a current concrete use case, named
consumer, safe actuator mapping, and fresh actual evidence.

### Step 8 — Freeze the manual initial-access and SSH contract

1. Confirm the owner and secret-free identity source of the current Ansible `default_user`.
2. Record that the LXC OS template is not trusted to provide the shared user, key, privilege,
   sshd, mDNS, hostname, or unique-host-key requirements. Do not select an automatic bootstrap
   mechanism in this phase.
3. Confirm only that the selected storage exists in the Step 2 storage list; do not claim live
   template availability. Pin the exact template identifier and comparison rule expected from the
   Phase 2 storage-content path.
4. Write the operator-owned manual procedure, entered through an authenticated Proxmox console or
   another approved out-of-band route, that establishes and checks the user/key, privilege, sshd,
   mDNS, hostname, and unique-host-key requirements one by one. Keep passwords, private keys, and
   raw public-key material out of the report.
5. Define `waiting_for_manual_initial_access` as a safe, resumable post-create state. Pin its
   evidence retention, operator remediation, completion checklist, and transition to fingerprint
   discovery. A guest in this state is compute-created and is not recreated.
6. Select an out-of-band fingerprint source such as an authenticated Proxmox console and perform
   a dry walkthrough of the display command and comparison procedure.
7. With an existing node or disposable local fixture, verify that the `nctl ssh enroll` dry plan
   names the DesiredNode UUID alias, endpoint, port, and fingerprint correctly.
8. Define the `waiting_for_ssh_enrollment` finding, safe-stop state, evidence retention,
   remediation, and resume precondition. Record automatic initial-access provisioning as deferred
   work after the core LXC and QEMU management workflows.

Do not create a guest, write an enrollment, or replace the existing `agdnsmasq` key for this test.

### Step 9 — Finding vocabulary and scope classification

For every case in the parent roadmap, pin:

| Column | Meaning |
|---|---|
| `code` | stable machine vocabulary |
| `target_kind` | platform / compute_instance / endpoint / guest_os |
| `target_id/slug` | exact desired scope |
| `severity` | info / warning / error |
| `status_effect` | converged / drifting / unknown |
| `reconcile_class` | noop / link / observe / create / start / manual / unsupported |
| `failure_scope` | target-local / shared-platform |
| `evidence` | allowlisted human and machine fields |
| `remediation` | exact safe next action |

At minimum, `waiting_for_manual_initial_access` means compute creation, fresh Proxmox observation,
and compute linking succeeded but the operator completion checklist has not yet passed.
`waiting_for_ssh_enrollment` means that checklist passed and offered fingerprints are available,
but no fingerprint has yet been verified and enrolled. Both are target-local safe stops, not
failed creates, and neither permits a repeated create action.

Unavailable credentials, wrong cluster scope, or unavailable platform observation may be shared
platform blockers. Bad guest config, duplicate guest candidate, NIC-join ambiguity, and guest-OS
unreachability are target-local by default and do not block unrelated guests on the platform.

### Step 10 — Pre-schema-change baseline

Use only side-effect-free command surfaces:

- `uv run --project nctl nctl drift --json`;
- `uv run --project nctl nctl render hosts-intent --json`;
- `uv run --project nctl nctl render production --json`;
- `uv run --project nctl nctl braindump list --json`;
- allowlisted metadata and body/review digests for required Braindumps; and
- `present + digest` or `absent + checked_at` for generated `hosts_intent.yml`,
  `production.yml`, and production reports.

Do not use `dashboard`, which pushes status. Never point `--out` at the existing generated
directory. Only when Step 0 needs an inventory file for probe transport may the private
controller-local evidence directory be used as output root; existing artifacts are not replaced.

Never write a full Braindump `show` response to disk. A sanitizer using the existing nctl client
converts the in-memory response into ID, timestamp, authorship category, review freshness, and
body/review SHA-256, then saves only that sanitized document. Do not send prose through a stdout
pipe or debug log.

A structured render/drift error is still retained as baseline evidence with an assertion that the
expected target and scope were exercised. Distinguish absent artifacts and unrelated drift from a
Phase 1 transport blocker.

For each baseline, the manifest records schema version, generated/observed time, exit code,
SHA-256, and positive content assertions. A successful exit code alone does not prove capture.

### Step 11 — Coordinated rollout and rollback point

The Phase 1 report freezes the following sequence.

#### Phase 2 rollout

1. Implement the nested Proxmox schema, normalizer, helper allowlist extension, and tests.
2. Update nauto ingest for the new schema and fail closed on an unknown schema or key.
3. Freeze the transaction/savepoint boundary for Cluster/VM/VMInterface/IP/custom-field writes
   from one Proxmox report. Even an error caught so the batch can continue must not commit partial
   writes for that report or guest.
4. If malformed data for one guest is isolated by a target-local savepoint, roll back all writes
   for that guest and mark the platform collection `partial`. Missing guests in a `partial`
   observation are never classified as offline or disappeared.
5. Choose a compatible reader/writer deployment order. Never ingest a new report into an
   unsupported nauto revision.
6. Deploy the pinned nodeutils/helper revision and collect fresh evidence.
7. Use the nauto dry-run summary to verify exact create/update scope, stable identity, Cluster
   membership, freshness, and interface provenance.
8. Before apply, store the operation ID and before image of every allowlisted field/relation that
   may be updated. Exclude tokens, raw inventory, and unrestricted custom fields.
9. After explicit approval, ingest once and refetch stable identity, membership, freshness, and
   relations. Then assert that an identical repeat dry run is empty/noop.
10. Enable the nctl typed actual snapshot last.

The normal rollback point is immediately before the first live ingest, but post-write recovery is
also defined:

- a transaction failure rolls back through the savepoint/outer transaction, and refetch must
  match the before image;
- a row with correct stable identity but missing allowlisted fields may remain as actual evidence
  and be repaired by fresh re-ingest;
- a committed wrong identity, wrong Cluster membership, or cross-guest relation is isolated from
  matching/read consumers and receives an exact repair plan based on the before image; it is not
  automatically justified as retained evidence;
- an erroneous update is restored from the before image after explicit approval; deleting an
  erroneously created ledger row requires a dependency/link audit and separate approval, and does
  not authorize deleting a Proxmox guest; and
- disabling a reader alone is not recovery.

#### Phase 3 rollout

1. **Add release:** Add nintent compute models, endpoint MAC, UI, REST, GraphQL, and YAML in a
   tested migration commit. Do not remove legacy `DesiredNode.realized_vm`.
2. Ask the user to push, rebuild the Nautobot image, and run the additive migration. Smoke-test
   that the current nctl query still works.
3. **Compatibility reader release:** Add the Section 5.5 dual-read/conflict contract to nctl.
   Test both old rows without new models and canonical rows with them. Do not enable compute drift
   or actuation yet.
4. Confirm the live GraphQL/REST read contract. Final write-permission proof remains at the next
   approved dry-plan/write gate.
5. Only after dry import and exact diff review, seed desired `aghub-pve` and `agdnsmasq` records.
   Capacity and template intent come only from operator-confirmed input.
6. For a non-null legacy link, require the new instance row and exact VM identity, then migrate
   only link/cache data. Record before image, PATCH, and refetch.
7. **Consumer cutover release:** While the nintent legacy field still exists, deploy an nctl
   revision that removes its consumers from query, drift, production, and ledger.
8. Use fresh drift, production render, link dry plan, and GraphQL query to prove the legacy field
   is unnecessary.
9. **Remove release:** A later nintent migration asserts all rows are migrated, then removes the
   legacy field.

The normal rollback point is before the first desired compute record write. Because the add
release retains the legacy field, nctl can be rolled back. Link migration has a before image and
reverse PATCH plan. The remove release occurs only after consumer cutover and an all-row
assertion; add and remove are not collapsed into one migration. This is a bounded compatibility
window with a working revision at every stage, not a permanent ad hoc dual model.

### Step 12 — Final non-mutation audit and report

1. Compare root/submodule Git status with Step 0.
2. Compare before/after Nautobot object counts, IDs, `last_updated`, and desired links.
3. Compare generated-inventory, dnsmasq-artifact, and known_hosts digests.
4. Compare Proxmox guest list, VMID, power, and resource config.
5. Compare remote nodeutils checkout/report/helper revision, mtime, and digest.
6. Scan report, staged diff, and sanitized manifest for tokens, private prose, and private/raw SSH
   keys. Scan raw infrastructure evidence for unintended credentials and stop report completion
   if any are found. Assert that Braindump prose was never saved.
7. Record the raw-evidence retention owner/date or user-approved deletion.
8. Complete `report.md` by evaluating every exit criterion with an evidence reference.

Changes to read-only access logs or provider observation time are distinguished from resource
mutation. Any changed remote file means the phase did not satisfy “no live state changed.”

## 8. Verification Plan

Phase 1 changes no production code, but focused tests verify that the current premises reproduce:

```bash
uv run --project nodeutils pytest \
  nodeutils/tests/test_proxmox_inventory.py \
  nodeutils/tests/test_pvesh_helper_integration.py

(cd ansible_agdev && \
  python3 -m unittest roles.nodeutils_pvesh_helper.tests.test_nodeutils_pvesh_read)

uv run --project nctl pytest \
  nctl/tests/test_sources_actual.py \
  nctl/tests/test_sources_desired.py \
  nctl/tests/test_hosts_intent.py \
  nctl/tests/test_dnsmasq.py \
  nctl/tests/test_production_adapter.py
```

If a project's actual pytest invocation or dependency environment differs, use the
repository-standard command and record why. A contract with no corresponding test is not passing.

Run these checks on documents and evidence:

- `git diff --check`;
- existence of relative links and referenced paths in the report;
- JSON parsing and schema/version assertions;
- no unintended credential/private key in raw infrastructure evidence; no token, private prose,
  or raw SSH key blob in the sanitized manifest, report, or staged diff; and proof that Braindump
  prose was not written to disk; and
- recomputation of every baseline-manifest SHA-256.

Live acceptance for Phase 1 comes from positive evidence in Steps 2, 3, 4, 8, 10, and 12—not from
unit tests alone.

Compute drift/planner/executor does not yet exist in Phase 1, so no compute-action multi-round test
is claimed. Instead, the report hands off these mandatory scenarios:

- Phase 2:
  `fresh collect -> first ingest -> refetch -> identical second ingest -> unchanged`;
- Phase 3:
  `strict import -> refetch -> identical second import -> unchanged`; and
- Phases 4/5:
  `drift -> intended action actually ran -> fresh observation -> no repeated action`.

Later phases may not substitute narrower unit tests for these positive assertions.

## 9. Sequence and Dependencies

```text
Step 0 safety/revisions
  -> Step 1 source/owner audit
  -> Step 2 fresh Proxmox observation
  -> Step 3 Nautobot baseline
  -> Step 4 agdnsmasq mapping
  -> Step 5 observation/ledger contract
  -> Step 6 desired/API/YAML contract
  -> Step 7 field classification
  -> Step 8 manual initial access + SSH trust
  -> Step 9 finding vocabulary
  -> Step 10 pre-change baseline
  -> Step 11 rollout/rollback
  -> Step 12 non-mutation proof + report
```

Do not freeze the field contract before Steps 2 and 3 provide live evidence. Do not treat model
migration planning as complete while Step 4 remains ambiguous. Do not start the Phase 5 LXC
create path while Step 8's manual gate and SSH trust contract remain undefined. An unselected
automatic bootstrap mechanism does not block Phase 1 or Phase 5.

## 10. Phase Handoff

Once Phase 1 is `complete`, Phase 2 implements only the observation schema, allowlist, freshness,
and ledger mapping frozen in the report. Phase 3 implements only the frozen desired model/API/YAML
and data transition.

If a later phase requires a new persisted field, provider config key, matching fallback,
credential location, network owner, or initial-access mechanism, it does not add one implicitly.
It updates this phase's field classification and decision log with a consumer and safety proof.
