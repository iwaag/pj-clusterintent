# Canonical Read/Write Interface Contraction — Development Roadmap

## Purpose

Give each retained model and operation one minimal, named interface contract. Canonical structured
domain reads use Nautobot GraphQL. Mutations use only the narrow REST collection or Nautobot Job
that has a current writer. The nintent Nautobot UI is a read-only human inspection surface; YAML
remains the source-controlled bulk-write interface.

This roadmap implements item 2 of
[`devdocs/vision/refactor/vision.md`](../../vision/refactor/vision.md). The vision and
[`README_DEV.md`](../../../README_DEV.md) are authoritative for safety, evidence, and completion
language.

The observable outcome is:

```text
current
  12 nintent models exposed through GraphQL
  + 7 broad REST ModelViewSets
  + 60 nintent UI routes
  + 9 desired-state YAML roots
  + overlapping nintent and nauto desired-state writers
  + nctl REST reads mixed into otherwise GraphQL-based domain reads

to
  one documented GraphQL read contract
  + three narrow nintent REST mutation collections
  + one source-controlled bulk desired-state import contract
  + one read-only human inspection UI
  + mutation Jobs that are dry by default
  + no duplicate nauto desired-state writer or candidate generator
```

The consumers that justify the retained surfaces are:

- `nctl` for joined desired/actual reads, drift, rendering, planning, and write confirmation;
- the user for read-only inspection of Braindump, Alignment Review, and desired state;
- the external AI agent for Braindump/Alignment Review exchange and confirmed desired proposals;
- nintent Jobs for YAML import, source analysis, and transactional IPAM writes;
- nauto's ingest Job for actual-ledger materialization; and
- the pending VM Phase 3 seed for the already-approved compute schema.

This initiative removes interfaces, not domain models or confirmed intent. It does not make
Braindump prose executable, implement compute drift, create a guest, consolidate the whole test
suite, or split large nctl modules.

## Governing decisions

### 1. GraphQL is the canonical domain read path

Retain one pinned nctl desired query for:

- DesiredNode;
- DesiredEndpoint;
- DesiredIPRange;
- DesiredNodeOperationalOverride;
- DesiredServicePlacement;
- DesiredService;
- DesiredDependency;
- DesiredComputePlatform; and
- DesiredComputeInstance.

Retain the separate pinned Braindump query for BrainDumpDocument plus its current
AlignmentReview. Retain one pinned actual query for Nautobot Device, Cluster, VirtualMachine,
Interface, VMInterface, and IPAddress.

Do not add parallel nctl REST loaders, per-model list clients, or YAML-as-read-model code. A
GraphQL root stays only when one of these named queries consumes it. Remove GraphQL registration
from IntentSource because its only current readers are nintent's in-process Jobs.

The pinned query and typed transport model are the consumer contract. Do not add snapshots for
every framework-generated GraphQL field. Test the selected fields and joined relations that nctl
actually consumes.

### 2. REST exists only for current mutations

Retain these nintent REST collections:

| Collection | Current writer | Required mutations |
|---|---|---|
| `nodes` | `nctl lifecycle` and the `link_actual_node` reconciler | PATCH lifecycle or the derived Device link only |
| `braindumps` | nctl on behalf of the user/agent | POST, PATCH, DELETE |
| `alignment-reviews` | nctl on behalf of the agent | POST, PATCH, DELETE |

Delete the DesiredService, DesiredEndpoint, DesiredComputePlatform, and
DesiredComputeInstance REST collections. No current caller writes them.

The retained node serializer must use an explicit field list. Identity and display fields may be
returned by incidental REST GET, but only `lifecycle`, `realized_device`, and
`realized_device_source` are writable. Disable node POST, PUT, and DELETE at this collection.
Nautobot's standard ModelViewSet may continue to provide incidental GET while PATCH is retained;
do not add a custom read-denial layer or a duplicate REST-read test matrix.

Braindump and Alignment Review serializers must also use explicit fields rather than
`fields = "__all__"`. Their full current create/replace/delete behavior remains because nctl is a
real writer.

When a later compute-linking phase implements a real writer, that phase may add the smallest
required mutation collection then. Do not retain an unused compute ViewSet now merely to avoid a
future change.

### 3. REST write confirmation returns to GraphQL

Every successful domain mutation is confirmed through the canonical GraphQL read:

- `nctl lifecycle` already follows this rule;
- Braindump and review writes already follow this rule; and
- `link_actual_node` must replace its precondition and post-PATCH REST GETs with a narrow
  GraphQL read or the pinned desired snapshot.

REST polling of a Nautobot JobResult and REST download of its FileProxy are part of the Job
execution protocol, not a competing domain read interface. `/api/status/` remains the health and
version probe.

### 4. YAML is the source-controlled bulk desired-state interface

Retain one strict YAML document with these roots:

```text
intent_sources
desired_nodes
desired_endpoints
desired_ip_ranges
desired_compute_platforms
desired_compute_instances
desired_services
desired_service_placements
desired_node_operational_overrides
```

These roots have current consumers in nintent's Import Job, nctl's GraphQL snapshot, the checked-in
cluster seed, or the pending VM Phase 3 seed. Reject every unknown top-level root instead of
silently ignoring it. Continue rejecting old aliases such as `service_repositories` and
`desired_node_operational_configs`; do not add compatibility names.

YAML omission never means delete. Import may create or update an explicitly named object, but it
must not retire, unlink, or delete an existing row merely because the row is absent from a file.

The configured `nauto/seed/intent_sources.yaml` becomes the only checked-in bulk desired-state
document. Move the `infrastructure` IntentSource and its five DesiredService declarations out of
`nauto/seed/home_cluster.yaml` and into this file. `Seed Home Cluster` must stop importing nintent
IntentSource or DesiredService rows.

### 5. The nintent Nautobot UI is read-only

Retain human-readable list and detail pages for:

- IntentSource;
- DesiredNode;
- DesiredEndpoint;
- DesiredIPRange;
- DesiredNodeOperationalOverride;
- DesiredService;
- DesiredDependency;
- DesiredServicePlacement;
- DesiredComputePlatform;
- DesiredComputeInstance; and
- BrainDumpDocument with its current AlignmentReview rendered in a clearly separate panel.

Delete every nintent add, edit, and delete form, route, button, and view. Delete Quick Host Add and
its composed host-creation operation completely. Delete the Source YAML diagnostic page; the
checked-in file and versioned Import Job artifact are its supported replacements.

The retained UI is an inspection adapter over the same live models that back the canonical
interfaces. It does not become another writer, proposal editor, approval surface, or source of
status. Navigation may link to the retained list pages, and detail pages may show relationships
and provenance, but no page may POST a domain mutation.

Braindump creation/update/deletion and Alignment Review creation/replacement/deletion occur only
through nctl and the retained narrow REST collections. The user supplies wishes in conversation;
the agent records confirmed words with the correct authorship. The UI displays both prose layers
without allowing either to be changed.

### 6. Operational fields have one writer

The retained field-level ownership is:

| Value | Owner |
|---|---|
| Braindump title/body/authorship | external agent through nctl, transcribing confirmed user words |
| Alignment Review summary | external AI agent through nctl |
| Bulk desired structure | nintent Import Job from the confirmed YAML document |
| Existing DesiredNode lifecycle transition | `nctl lifecycle` |
| DesiredNode realized Device link/source | nctl `link_actual_node` reconciler |
| DesiredEndpoint realized IPAddress link/source | `Reconcile Desired IPAM Intent` Job |
| Source-derived service metadata and dependencies | `Analyze Intent Sources` Job |
| Operator-owned service lifecycle/requirements/notes | confirmed YAML import |
| Actual Device/Cluster/VM/interface/IP ledger | nauto `Ingest Nodeutils Inventory` Job |
| Future compute realized links | deferred until the compute-linking roadmap has a real writer |

YAML may set an initial DesiredNode lifecycle on create, but re-import must not overwrite a later
operator transition made by `nctl lifecycle`. No UI form remains. Source analysis must continue to
leave operator-owned DesiredService fields unchanged.

This is field ownership, not a compatibility layer. Do not add dual writes, shadow columns, or
fallback readers.

### 7. Consolidate import and analysis Jobs around dry-plan/apply

Retain and contract the nintent Jobs as follows:

- `Import Intent Sources`
  - loads the one strict YAML contract;
  - defaults to preview with zero committed writes;
  - writes a versioned artifact containing exact create/update/unchanged rows and scope;
  - requires an explicit apply flag for mutation; and
  - never treats absence as deletion.
- `Analyze Intent Sources`
  - reads imported IntentSource rows;
  - defaults to preview with zero committed writes;
  - writes a versioned analysis/change artifact;
  - requires an explicit apply flag before updating source metadata, DesiredService source fields,
    or DesiredDependency rows; and
  - preserves operator-owned fields.
- `Reconcile Desired IPAM Intent`
  - remains dry by default;
  - remains the one transactional IPAddress create/link writer; and
  - keeps exact host scope and its existing versioned summary artifact.

Delete `Preview Intent Source Analysis`; its behavior becomes the preview mode of
`Analyze Intent Sources`. Do not keep the old Job name as an alias.

In nauto:

- keep `Seed Home Cluster` only for Nautobot/native actual-ledger prerequisites;
- keep `Ingest Nodeutils Inventory`, the real nctl-called actual writer;
- delete `Generate Desired Services`, `seed/service_repositories.yaml`, and generated-output
  documentation because nintent analysis owns that workflow; and
- remove nintent IntentSource/DesiredService imports and write code from `Seed Home Cluster`.

The live `AI Resource Auto Review` JobHook and its four populated Device custom fields are
explicitly deferred. They are active live state, not an unused interface that this roadmap may
silently delete. Their relationship to Braindump Alignment Review needs a separate semantic/data
decision. No new code is added for them here.

### 8. Keep CLI adapters only where a named caller uses them

Retain:

- all drift, render, reconcile, ops, SSH, session, and actual/status commands;
- `nctl lifecycle`, because it is the canonical existing-node lifecycle writer; and
- the complete `nctl braindump` command family, because it is the agent adapter over the retained
  GraphQL/REST contract.

Do not add generic `nctl get`, generic CRUD, GraphQL passthrough, REST passthrough, or a command for
every retained model. The Import and Analyze Jobs remain invocable through Nautobot's Job
interface and REST Job protocol; add a CLI adapter only after repeated operation demonstrates a
current need.

## Current-state baseline

This baseline was measured on 2026-07-25 and must be repeated in Phase 0.

### Revisions and worktrees

| Component | Revision | State |
|---|---|---|
| superproject | `853ffac2408801106dc53eea6fa6a60068e3b58f` | clean before this roadmap was added |
| nctl | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean |
| nintent | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

### Live deployment

- Nautobot `3.1.3` is reachable and authenticated at the configured local URL.
- nintent is deployed at `c343c5a56047b0df9ad901dd4459863ef1954053`.
- migrations are applied through `0016_remove_reconciliation_dashboard_surfaces`.
- live nintent row counts are:

| Model | Rows |
|---|---:|
| IntentSource | 2 |
| DesiredService | 6 |
| DesiredDependency | 0 |
| DesiredNode | 5 |
| DesiredEndpoint | 5 |
| DesiredComputePlatform | 0 |
| DesiredComputeInstance | 0 |
| DesiredServicePlacement | 1 |
| DesiredNodeOperationalOverride | 0 |
| DesiredIPRange | 3 |
| BrainDumpDocument | 5 |
| AlignmentReview | 5 |

All five live DesiredNodes have no IntentSource link, the one placement reports
`assignment_source=manual`, and all five Braindumps report `authorship=user_direct`. These are
ownership signals, not proof of how each row was originally created. Because no UI writer remains
after this initiative, Phase 0 must capture every confirmed structural row in the canonical YAML
contract before removing its old form. It must inspect ObjectChange/audit evidence and ask for a
user decision where ownership remains ambiguous. It must not copy Braindump body or review prose
into tracked evidence.

The live `AI Resource Auto Review` JobHook exists, and all four related Device custom fields have
five non-empty values. This supports the explicit deferral above.

### Interface and size signals

- 12 nintent models have framework GraphQL registration.
- 7 nintent REST ModelViewSets are registered.
- nintent declares 60 plugin UI `path()` entries and 48 view classes.
- UI support is about 1,926 Python lines plus 1,327 template lines.
- REST support is 278 Python lines.
- YAML loader/import/Job code is about 2,877 Python lines.
- nctl has 11 top-level commands.
- nctl collects 954 tests, with 17,763 tracked source lines and 19,380 tracked test lines.
- nintent's Django-free suite runs 187 tests; tracked non-test Python is 9,560 lines, tests are
  4,029 lines, and templates are 1,327 lines.

These are remeasurement baselines, not deletion quotas.

## Required interface matrix

`G`, `R`, `U`, `Y`, and `C` below mean GraphQL read, REST mutation, human UI, YAML, and CLI.
An em dash means the surface is absent from the final contract.

### nintent objects

| Object | Named current consumer | G | R | U | Y | C | Decision |
|---|---|---:|---:|---:|---:|---:|---|
| IntentSource | Import/Analyze Jobs; human inspector | — | — | read | yes | — | keep model/YAML/ORM and read-only UI; delete GraphQL |
| DesiredNode | nctl control loop; human inspector | yes | PATCH | read | yes | lifecycle | keep, narrow writers |
| DesiredEndpoint | nctl drift/render/IPAM; human inspector | yes | — | read | yes | — | keep; delete REST |
| DesiredIPRange | nctl dnsmasq/IPAM logic; human inspector | yes | — | read | yes | — | keep; YAML-only mutation |
| DesiredNodeOperationalOverride | nctl production composition; human inspector | yes | — | read | yes | — | keep; YAML-only mutation |
| DesiredService | nctl drift/composition; Analyze Job; human inspector | yes | — | read | yes | — | keep; split source/operator field owners |
| DesiredDependency | nctl service drift; Analyze Job; human inspector | yes | — | read | — | — | keep; analysis-owned mutation |
| DesiredServicePlacement | nctl drift/composition; human inspector | yes | — | read | yes | — | keep; YAML-only mutation |
| DesiredComputePlatform | nctl typed desired snapshot; VM Phase 3 seed; human inspector | yes | — | read | yes | — | keep inert model; delete unused REST |
| DesiredComputeInstance | nctl typed desired snapshot; VM Phase 3 seed; human inspector | yes | — | read | yes | — | keep inert model; delete unused REST |
| BrainDumpDocument | external agent; human inspector | yes | CRUD | read | — | yes | keep minimal exchange-diary contract |
| AlignmentReview | external agent; human reads on Braindump detail | yes | CRUD | nested read | — | yes | keep REST/CLI; remove UI mutations |

### Actual-ledger objects

| Object | Named current consumer | Canonical read | Mutation owner | Decision |
|---|---|---|---|---|
| Device | nctl actual/drift/composition | GraphQL | nauto ingest | keep |
| Cluster | nctl Proxmox diagnostic/compute source | GraphQL | nauto ingest | keep |
| VirtualMachine | nctl Proxmox diagnostic/compute source | GraphQL | nauto ingest | keep |
| Interface | nctl node/endpoint matching | GraphQL | nauto ingest/native admin | keep selected fields |
| VMInterface | nctl Proxmox interface/IP matching | GraphQL | nauto ingest | keep selected fields |
| IPAddress | nctl endpoint matching/IPAM | GraphQL | nintent IPAM Job and nauto ingest | keep provenance-separated writers |

Native Nautobot UI and framework APIs for these core Nautobot models are not owned by nintent and
are not removed here. nctl must not add a second actual-state REST reader.

### Operations

| Operation | Real caller | Read path | Write path | Decision |
|---|---|---|---|---|
| Import Intent Sources | user/operator | YAML + DB ORM | nintent ORM in one transaction | keep; dry by default, versioned plan/apply artifact |
| Analyze Intent Sources | user/operator | IntentSource ORM + remote catalog files | nintent ORM in scoped transactions | keep; add dry preview/apply |
| Preview Intent Source Analysis | user/operator | duplicate of Analyze preview | none | delete after replacement |
| Reconcile Desired IPAM Intent | nctl reconcile/operator | ORM plus actual observation fields | IPAddress and endpoint link ORM | keep |
| Seed Home Cluster | operator | `home_cluster.yaml` | native Nautobot prerequisites | replace: remove nintent desired writes |
| Generate Desired Services | no unique consumer | duplicate source analysis | generated YAML file | delete; nintent Analyze owns this |
| Ingest Nodeutils Inventory | nctl reconcile/operator | validated report | native actual ledger | keep |
| nctl lifecycle | operator/agent | GraphQL | narrow DesiredNode REST PATCH | keep |
| nctl link_actual_node | reconcile executor | GraphQL | narrow DesiredNode REST PATCH | keep; remove REST GET |
| nctl Braindump/review operations | user/agent | GraphQL | Braindump/Review REST | keep |
| AI Resource Auto Review | live JobHook | Device facts | four Device custom fields | defer to separate semantic/data roadmap |

## Deletion and edit inventory

Phase plans must re-run repository-wide searches before relying on this list.

### nintent deletions

Delete REST serializer/ViewSet/router support for:

```text
DesiredService
DesiredEndpoint
DesiredComputePlatform
DesiredComputeInstance
```

Delete every UI mutation surface:

```text
all ObjectEditView classes
all ObjectDeleteView classes
all nintent model forms
DesiredHostQuickAddForm
DesiredHostQuickAddView
create_desired_node_with_primary_endpoint
all add/edit/delete URL patterns
all add/edit/delete buttons and bulk actions
AlignmentReview add/edit/delete
Source YAML diagnostic page
```

Retain ObjectListView/ObjectView, filters, tables, navigation, and detail templates for the
read-only models in the matrix. Do not delete the underlying domain models, migrations, retained
GraphQL roots, or the Braindump detail's read-only review panel.

### nintent edits

At minimum, review and edit:

- `nautobot_intent_catalog/models.py`
  - remove GraphQL registration from IntentSource only;
  - retain every domain model and migration history;
- `api/serializers.py`, `api/views.py`, and `api/urls.py`
  - retain only the three final collections;
  - use explicit fields and narrow node methods/writability;
- `views.py`, `urls.py`, `navigation.py`, `forms.py`, `filters.py`, and `tables.py`
  - implement the read-only UI matrix;
  - delete every mutation view/form/route/action;
  - delete Quick Host Add and Source YAML diagnostic support;
  - keep list/detail/filter/table behavior;
- templates
  - remove mutation buttons and form/utility templates;
  - retain all model inspection templates and the separated Braindump/review rendering;
- `loaders.py`
  - reject unknown top-level roots;
- `importers.py` and `jobs.py`
  - enforce field ownership;
  - make Import and Analyze dry by default;
  - add exact versioned artifacts;
  - delete the standalone Preview Job; and
- tests and current documentation
  - remove surface-multiplication tests;
  - retain model validation, GraphQL consumer fields, mutation boundaries, import atomicity, and
    Job artifact contracts.

No model field removal is planned, so no new database migration should be created unless Phase 0
finds a genuinely necessary schema change. `makemigrations --check --dry-run` must remain clean.

### nctl edits

At minimum:

- `src/nctl_core/reconcile/ledger.py`
  - replace DesiredNode REST GET precondition/confirmation reads with GraphQL;
- `src/nctl_core/nautobot.py`
  - retain generic REST methods only where a remaining mutation/Job/status call uses them;
- `src/nctl_core/sources/desired.py`
  - retain the single joined desired query and its exact fields;
- `src/nctl_core/sources/actual.py`
  - retain the single actual query and selected actual-ledger fields;
- `src/nctl_core/sources/braindump.py` and `braindump.py`
  - retain GraphQL reads plus narrow REST writes;
- `src/nctl_core/lifecycle.py`
  - retain GraphQL/PATCH/GraphQL behavior;
- `src/nctl_core/jobs.py`
  - retain only the general protocol used by Ingest and IPAM; and
- compatibility docs/tests
  - do not claim removed nintent model collections as supported nctl interfaces.

Do not add a second desired query per command as part of contraction.

### nauto edits

At minimum:

- remove nintent IntentSource and DesiredService imports/writes from
  `jobs/seed_home_cluster.py`;
- remove the matching sections from `seed/home_cluster.yaml`;
- delete `jobs/generate_desired_services.py`;
- delete `seed/service_repositories.yaml`;
- remove Generate Desired Services registration, tests, and documentation;
- retain Seed Home Cluster's native Nautobot prerequisites;
- retain Ingest Nodeutils Inventory and Proxmox actual-ledger behavior; and
- leave the active AI Resource Review JobHook implementation untouched except for a documentation
  note pointing to its explicit deferral.

### Current documentation to edit

Review at least:

- root `README.md` and `README_DEV.md`;
- `nintent/README.md`, `README_QUICK.md`, `README_DEV.md`, and `CONCEPT.md`;
- `nctl/README.md` and relevant `nctl/docs/`;
- `nauto/README.md`;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md`; and
- `devdocs/vision/refactor/vision.md` only if a discovered fact requires an explicit correction.

Historical phase reports remain historical evidence. Do not rewrite them to pretend removed
interfaces never existed.

## Scope boundaries

### In scope

- approve and implement the final interface matrix;
- contract nintent REST and make the human UI read-only;
- preserve one joined GraphQL read path;
- make YAML root validation strict;
- transition every confirmed structural row to the canonical YAML writer;
- make Import and Analyze dry-plan/apply operations;
- remove the duplicate preview Job;
- remove duplicate nauto desired-service writers/generator;
- replace nctl DesiredNode REST reads with GraphQL;
- transition current live desired rows without inventing or deleting intent;
- coordinate with the pending VM Phase 3 seed; and
- update tests and current documentation for the final contract.

### Out of scope

- deleting any nintent domain model;
- deleting native Nautobot Device/Cluster/VM/IPAM UI or APIs;
- changing drift, planner, SSH, Ansible, observation, or evidence semantics;
- implementing compute drift, compute linking, Proxmox actuation, or guest creation;
- adding a generic desired-state proposal engine;
- converting Braindump or Alignment Review prose into executable input;
- removing the live AI Resource Review JobHook or its data;
- broad test-suite consolidation unrelated to removed interfaces;
- modularizing nctl;
- adding a server, MCP endpoint, daemon, or replacement dashboard; and
- forbidding framework-provided REST GET where a retained ModelViewSet is needed for mutation.

## Ownership and dependency map

| Concern | Owner after this initiative |
|---|---|
| User wishes and constraints | BrainDumpDocument, authored by user/confirmed transcription |
| Current AI explanation | AlignmentReview, written by external agent through nctl |
| Confirmed structured desired state | nintent models |
| Bulk desired transport | strict `nauto/seed/intent_sources.yaml` plus nintent Import Job |
| Human inspection | read-only nintent list/detail UI |
| Canonical domain reads | Nautobot GraphQL |
| Narrow desired mutations | retained nintent REST collections or named Jobs |
| Source-derived service analysis | nintent Analyze Job |
| Actual-ledger materialization | nauto Ingest Job |
| Drift/planning/evidence | nctl |
| Host actuation | ansible_agdev through nctl |
| Push/deploy/maintenance approval | user/operator |

`remove_unused_surfaces` is complete and is a prerequisite already satisfied. This roadmap must
finish before risk-based test consolidation and nctl modularization so those initiatives work only
on retained surfaces.

The pending VM Phase 3 Steps 9–12 must not seed compute records through REST or removed UI. They
share this roadmap's final YAML Import contract. Pause the old seed procedure until Phase 0
reconciles the checked-in nine-node YAML with the five-node live state and the user approves the
exact desired proposal.

VM compute-linking work may later introduce one narrow real writer for
DesiredComputePlatform.realized_cluster or DesiredComputeInstance.realized_vm. That later roadmap
owns the REST addition, dry plan, exact scope, refetch, and non-repetition proof.

## Phases

Concrete plans and one final report per phase should live under
`devdocs/big/interface_contract/pN/`.

### Phase 0 — Freeze consumers, live ownership, and the final matrix

**Goal:** prove which surfaces have real callers and resolve current desired-record ownership
without mutation.

Work:

1. Re-read this roadmap, the refactoring vision, README_DEV, local environment memo, Braindump
   roadmap, core-reconcile roadmap, VM roadmap, latest VM Phase 3 report, and
   remove-unused-surfaces final report.
2. Record exact root/submodule revisions, dirty state, installed nintent commit, migration state,
   running Jobs, JobHooks, REST routes, GraphQL roots, UI routes, YAML roots, CLI commands, tests,
   and line measurements.
3. Search code, current docs, shell wrappers, Makefiles, Job schedules, and live audit records for
   every REST collection and UI route in the matrix.
4. Record aggregate live counts, source links, placement assignment sources, realized-link
   provenance, and ObjectChange origin without recording Braindump/review prose or secrets.
5. Compare the five live DesiredNodes/endpoints with the nine checked-in YAML nodes/endpoints.
   Classify each difference as confirmed live intent, confirmed checked-in intent, stale seed, or
   unresolved.
6. Compare the two live IntentSources and six DesiredServices with declarations in
   `home_cluster.yaml`, `intent_sources.yaml`, and source-analysis inputs.
7. Ask the user to resolve every identity whose ownership or desired presence cannot be
   established from evidence. Do not infer that a missing YAML row should be deleted or that an
   extra checked-in row should be imported.
8. Freeze explicit REST methods/fields, retained GraphQL selections, UI routes, YAML roots, and Job
   variables/artifact schemas.
9. Amend the active VM Phase 3 seed steps to depend on the final Import Job contract.

**Exit criteria:** every retained checkmark has a named caller; every deleted surface has no real
caller; current live/YAML discrepancies have a confirmed disposition or the phase is `blocked`;
and no live or desired mutation occurred.

### Phase 1 — Establish one source-controlled desired writer

**Goal:** remove overlapping seed/generator ownership and make desired imports safely reviewable.

Work:

1. Move confirmed infrastructure IntentSource/DesiredService declarations from
   `home_cluster.yaml` to `intent_sources.yaml`.
2. Reconcile the checked-in node, endpoint, range, placement, override, and pending compute rows
   with the Phase 0 decisions.
3. Reject unknown YAML roots and preserve strict field validation.
4. Change Import Intent Sources to dry preview by default and require an explicit apply flag.
5. Write one versioned preview/apply artifact with source path identity, mode, exact object
   identities, create/update/unchanged decisions, scope, and errors.
6. Capture every confirmed live structural DesiredNode, DesiredEndpoint, DesiredIPRange,
   DesiredServicePlacement, and override row in the canonical YAML proposal. An import must stop
   before writes if its proposal conflicts with live intent or would overwrite an nctl/Job-owned
   operational field.
7. Make an existing node's lifecycle create-only for YAML so a later `nctl lifecycle` transition is
   not reset by re-import.
8. Change Analyze Intent Sources to preview by default, add the exact versioned change artifact,
   and require explicit apply.
9. Delete Preview Intent Source Analysis and prove Analyze preview covers its unique read-only
   behavior.
10. Remove nintent desired writes from Seed Home Cluster.
11. Delete nauto Generate Desired Services and its seed/output contract.
12. Run local tests plus a disposable Nautobot database preview/apply/repeat proof.

**Exit criteria:** one YAML file and one nintent Import Job own bulk desired writes; source analysis
has one dry-plan/apply Job; nauto no longer writes nintent desired rows; preview is zero-write;
apply is atomic; and a repeat apply reports no changes.

### Phase 2 — Contract REST and canonicalize confirmation reads

**Goal:** retain only current REST mutations and remove REST as a domain read path.

Work:

1. Delete four unused REST collections and their serializer/ViewSet/router/test/docs support.
2. Give the node, Braindump, and review serializers explicit fields.
3. Limit the node collection to incidental GET plus PATCH of the three owned mutation fields.
4. Reject unrelated node fields and unsupported POST/PUT/DELETE methods.
5. Replace `link_actual_node` REST GET precondition/confirmation calls with GraphQL.
6. Prove lifecycle, node-link, Braindump, and review writes still perform
   GraphQL-before/write/GraphQL-after and fail closed on mismatch.
7. Prove removed collection URLs are absent and no current source imports their serializers or
   ViewSets.
8. Keep Job REST lookup/run/poll/artifact and `/api/status/` behavior unchanged.

**Exit criteria:** all nctl domain reads are GraphQL; only three nintent REST mutation collections
remain; node writes are field- and method-bounded; and every retained write is positively
confirmed.

### Phase 3 — Make the nintent human UI read-only

**Goal:** preserve human inspection while removing every Nautobot-page mutation path.

Work:

1. Delete all nintent ObjectEditView/ObjectDeleteView classes, model forms, mutation URLs, action
   buttons, and bulk mutation actions.
2. Delete Quick Host Add, its operation/helper code, templates, tests, URL, and navigation group.
3. Delete the Source YAML diagnostic page; direct users inspect the checked-in file and Import Job
   artifact instead.
4. Retain navigation to read-only list pages for IntentSource, all desired-state models, and
   Braindumps.
5. Retain list/detail/filter/table/template behavior for every object marked `read` in the matrix.
6. Render lifecycle, realized links, source/assignment provenance, and timestamps without edit
   affordances.
7. Retain the Braindump detail's separated, autoescaped, read-only Braindump and Alignment Review
   panels.
8. Prove every former add/edit/delete/Quick Host Add URL returns 404 or the framework's normal
   unavailable-route result and no retained page emits a domain-mutation POST.
9. Run authenticated list/detail/navigation/template tests in a disposable Nautobot environment.

**Exit criteria:** every retained nintent UI route is read-only; every domain model in the matrix
remains human-inspectable; all mutation utilities and forms are absent; and user prose cannot be
mistaken for the Alignment Review.

### Phase 4 — Coordinated data transition and deployment

**Goal:** deploy the contracted interface without losing current intent or disrupting the pending
VM work.

Work:

1. Prepare exact matched nintent, nctl, nauto, and superproject revisions. Ask the user to push
   submodule commits; do not push on the user's behalf.
2. Begin an approved maintenance window. Stop desired writes, Import/Analyze/IPAM/Ingest Jobs,
   routine nctl mutation operations, and VM Phase 3 seed work.
3. Back up the database and record the rollback tuple.
4. Run the final YAML preview against live state. Require the exact expected create/update/unchanged
   set and zero unreviewed ownership conflicts.
5. Apply only after separate user approval. Confirm row identities, user-owned prose counts,
   realized links, provenance, and source/operator fields through GraphQL.
6. Deploy the matched code revisions. No database migration is expected; prove migration state
   remains through `0016` and `makemigrations --check --dry-run` is clean.
7. Run live GraphQL, retained REST mutation, removed REST, retained UI, removed UI, Job dry-run,
   nctl status/actual/drift/render/dry-reconcile/ops/Braindump, and VM Phase 3 read-only smoke
   checks.
8. Prove no JobHook, desired row, actual-ledger row, operation artifact, or private prose was
   unintentionally changed.
9. Resume operations and hand the final YAML contract to VM Phase 3 Steps 9–12.
10. Record before/after measurements and one final report with every deviation or deferred item.

**Exit criteria:** live state uses the final matrix; confirmed intent and links are preserved;
removed routes are absent; retained read/write paths pass; Import preview/apply/repeat is proven;
and VM Phase 3 can proceed without a removed interface.

## Verification matrix

| Area | Required proof |
|---|---|
| GraphQL desired | one joined query returns every retained desired root and selected relation |
| GraphQL actual | one joined query returns Device/Cluster/VM/interfaces/IP fields used by nctl |
| GraphQL Braindump | list/show returns current review relation without prose entering reports |
| IntentSource | no framework GraphQL root remains; Jobs read ORM rows and read-only UI still renders |
| REST routes | only nodes, Braindumps, and reviews remain under the nintent API |
| Node REST | GET incidental; PATCH only owned fields; POST/PUT/DELETE and unrelated fields rejected |
| Write confirmation | lifecycle, node link, Braindump, and review each prove GraphQL before/after |
| YAML | exactly nine roots accepted; unknown/old roots rejected; omission causes no deletion |
| Import Job | dry by default; exact artifact; apply requires authority; transaction rollback works |
| Analyze Job | preview replaces old Job; operator fields preserved; apply/repeat is idempotent |
| IPAM Job | existing dry/apply/scope/artifact behavior remains |
| nauto seed | no IntentSource or DesiredService import/write remains |
| nauto ingest | nctl-called actual materialization and Proxmox upsert remain |
| Human UI | every retained model list/detail renders read-only, including separated prose panels |
| Removed UI | all add/edit/delete/Quick Host Add/Source YAML routes, forms, actions, and utility templates are absent |
| Braindump boundary | user prose and AI prose remain distinct and non-executable |
| Evidence | operation IDs, JSONL, plans, results, and historical artifacts are unchanged |
| VM handoff | compute GraphQL/YAML remain; no compute drift/write/action is introduced |
| Secrets | no token, private prose, raw key, or credential enters tracked artifacts/reports |

## Required searches

Completion must search active code, tests, configuration, and current documentation for at least:

```text
DesiredServiceViewSet
DesiredEndpointViewSet
DesiredComputePlatformViewSet
DesiredComputeInstanceViewSet
PreviewIntentSourceAnalysis
GenerateDesiredServices
service_repositories.yaml
desired_services.generated.yaml
DesiredHostQuickAdd
desiredhost_quick_add
create_desired_node_with_primary_endpoint
ObjectEditView
ObjectDeleteView
source_yaml_list
alignmentreview_add
alignmentreview_edit
alignmentreview_delete
rest_get
fields = "__all__"
@extras_features("graphql")
```

Each remaining `rest_get` caller must be classified as status, Job lookup/poll/artifact, or an
explicitly approved exception. Each remaining `fields = "__all__"` and GraphQL registration must
have a retained consumer; otherwise it blocks completion.

Expected references to removed surfaces are limited to:

- this roadmap and the refactoring vision;
- normal historical migrations;
- historical plans/reports explicitly treated as history; and
- the final report explaining the removal.

## Safety and rollback

### Safety

- Braindump and Alignment Review prose remains opaque and non-executable.
- Desired write authority and reconcile apply authority remain separate.
- Import and Analyze default to zero-write preview.
- Missing YAML never authorizes deletion, retirement, unlinking, shutdown, or replacement.
- Direct-entry/YAML ownership conflicts stop before mutation.
- The read-only UI cannot mutate desired rows, realized links, Braindumps, or reviews.
- Successful writes are refetched through GraphQL before success is reported.
- Existing operation evidence and partial-progress behavior remain unchanged.
- No live mutation occurs without a reviewed plan and separate user approval.
- Reports contain aggregate IDs/counts and public schema facts, not secret values or private prose.

### Rollback

No schema migration is expected. Rollback is still coordinated because routes, Job variables, seed
ownership, and nctl call paths change together.

If failure occurs before live apply:

- leave live desired rows and deployed revisions unchanged;
- correct the preview or report `implemented, not deployed`; and
- do not reintroduce compatibility routes.

If failure occurs after YAML apply or deployment:

1. stop desired writes and relevant Jobs;
2. restore the pre-window database backup if data changed incorrectly;
3. restore the prior nintent/nctl/nauto revision tuple;
4. restore the prior checked-in YAML only if it was part of the failed transition;
5. verify migrations remain through `0016`, desired/prose/link counts, GraphQL, and ordinary nctl
   operation; and
6. record every side effect produced before rollback.

Do not roll back by keeping both old and new Jobs, routes, serializers, or readers active.

## Definition of done

This initiative is `complete` only when:

- the final interface matrix is implemented and documented;
- every retained interface has a named current consumer;
- nctl uses GraphQL for all domain reads and REST only for retained mutations/Job protocol;
- only the node, Braindump, and Alignment Review nintent REST collections remain;
- node REST methods and writable fields are narrow;
- YAML has one strict nine-root contract and unknown roots fail closed;
- Import and Analyze are dry by default, emit exact artifacts, and require explicit apply;
- Preview Intent Source Analysis and nauto Generate Desired Services are absent;
- Seed Home Cluster no longer writes nintent desired models;
- every retained nintent UI page is read-only and all desired/Braindump/review objects remain
  human-inspectable;
- Quick Host Add and every add/edit/delete UI path are absent;
- Alignment Review remains visible but is not human-UI writable;
- current desired rows, realized links, and user/AI prose survive the coordinated transition;
- retained mutation paths are positively exercised and GraphQL-refetched;
- removed routes/imports/tests/docs are proven absent;
- live and disposable verification pass with no unintended actuation;
- the pending VM Phase 3 seed uses the final YAML contract; and
- the final report records before/after measurements and the explicitly deferred live AI Resource
  Review surface.

A smaller route or test count alone is not completion. Completion is one minimal, truthful
read/write contract with preserved intent, bounded authority, and positive proof of every retained
mutation.
