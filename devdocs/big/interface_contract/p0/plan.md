# Interface Contract Phase 0 Implementation Plan: Freeze Consumers, Live Ownership, and the Final Matrix

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: proposed; read-only audit and documentation-only phase.

## 1. Goal

Phase 0 freezes the evidence-backed boundary for the canonical interface contraction before any
runtime interface, desired row, Job, or live deployment is changed.

The phase must answer two independent questions:

1. Which GraphQL roots and selections, REST mutations, UI pages, YAML roots, Jobs, and CLI
   adapters have a named current caller?
2. Which live desired rows and checked-in YAML rows represent confirmed intent, and which remain
   unresolved?

The phase is complete only when:

- every retained interface has a named current caller and exact contract;
- every interface selected for deletion has no real caller in the declared audit boundary;
- every difference between live desired state and the checked-in seed has a confirmed
  disposition;
- the active VM Phase 3 seed procedure depends on the final YAML Import contract; and
- all inspection was non-mutating.

Phase 0 does not implement the contraction. It produces the contract that Phases 1–4 must
implement without independently re-expanding the surface.

## 2. Required outputs

Phase 0 produces:

1. this implementation plan;
2. a private, untracked evidence directory under
   `.local/interface-contract/p0/<timestamp>/`;
3. a classified consumer manifest covering active code, current documentation, wrappers,
   Makefiles, repository automation, live schedules, and live audit metadata;
4. a live-versus-YAML disposition ledger for every affected desired identity;
5. exact frozen contracts for REST methods and fields, GraphQL selections, UI routes, YAML
   roots and fields, Job variables, and Job artifacts;
6. a narrowly amended `devdocs/big/vm/p3/plan.md`;
7. `devdocs/big/interface_contract/p0/report.md`; and
8. a final phase state of `complete` or `blocked`.

Only the following tracked files may change during Phase 0:

- this plan;
- `devdocs/big/vm/p3/plan.md`; and
- `devdocs/big/interface_contract/p0/report.md`.

If evidence requires a correction to the parent roadmap or refactoring vision, stop and amend the
applicable governing document explicitly before claiming Phase 0 complete. Do not hide a changed
decision only in the report.

## 3. Authority and non-mutation boundary

### 3.1 Allowed actions

Phase 0 may:

- read tracked and untracked configuration metadata needed to locate the environment;
- inspect Git revisions, diffs, worktree state, code, tests, documentation, and generated route
  registries;
- run local test collection or other non-mutating discovery commands;
- query live Nautobot through GraphQL queries;
- use REST `GET`, `HEAD`, and `OPTIONS`;
- use authenticated UI `GET` only if an already-valid session exists and the request does not
  create or update a session;
- run read-only Django ORM queries and schema/route introspection in the existing containers;
- inspect Job, JobHook, ScheduledJob, JobResult, and ObjectChange metadata;
- read current desired and actual rows needed for identity and ownership comparison;
- fetch public source-analysis inputs without credentials when their exact current content is
  required; and
- write private local evidence plus the three tracked documentation files listed above.

GraphQL queries normally use HTTP `POST`. That transport is allowed only for a query document.
No GraphQL mutation, Job run, or REST mutation is allowed.

### 3.2 Prohibited actions

Phase 0 must not:

- call REST `POST`, `PUT`, `PATCH`, or `DELETE`;
- invoke any Nautobot Job, including a Job described as preview or dry-run;
- run `nctl lifecycle`, Braindump writes, `nctl reconcile`, `nctl apply`, SSH enrollment,
  collection, ingest, or Ansible;
- create, update, disable, retire, link, unlink, or delete a desired or actual row;
- change a Braindump, Alignment Review, JobHook, ScheduledJob, or custom field;
- edit `nauto/seed/intent_sources.yaml` or another seed file;
- create a live authenticated UI session merely to inspect a page;
- rebuild or restart Nautobot;
- create or apply a migration;
- push a commit;
- weaken authentication or SSH policy;
- read shell history or broadly scan unrelated home-directory content for hypothetical callers;
  or
- copy a token, credential, raw SSH key, Braindump body, or Alignment Review summary into any
  evidence file or report.

No missing YAML row authorizes deletion. No checked-in-only row authorizes import. No live-only
row authorizes silently copying it to YAML.

### 3.3 User decisions

Repository and audit evidence may establish provenance, but it cannot invent the user's current
intent. The user must resolve every identity for which desired presence or field ownership remains
ambiguous.

The decision request must show a compact sanitized table containing:

- stable object identity;
- whether it exists live and/or in each checked-in source;
- the conflicting non-secret fields;
- the available provenance;
- the proposed classification, if evidence supports one; and
- the consequence for the Phase 1 YAML proposal.

Do not mutate state while waiting for answers. If any required identity remains unresolved at the
end of the phase, publish the evidence gathered so far and set the phase status to `blocked`.

## 4. Governing inputs and planning-time orientation

Before executing Step 0, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md`;
- the latest applicable reports under `devdocs/big/vm/p3/`;
- `devdocs/big/remove_unused_surfaces/p5/report.md`;
- current component READMEs named by the parent roadmap; and
- current source and tests for every interface being classified.

The latest numbered VM report alone is not a complete live-state record: the coordinated
`remove_unused_surfaces` Phase 5 report documents the later deployment of migrations `0015` and
`0016`. Phase 0 must reconstruct the current state from both histories rather than copying the
older VM report's pre-deployment state.

Historical plans and reports are evidence. They are not current callers and must not be rewritten
to pretend removed interfaces never existed.

### 4.1 Planning-time repository snapshot

The following was observed while this plan was authored on 2026-07-25. It is orientation only.
Phase 0 execution must recapture all values:

| Repository | Planning-time revision | Planning-time state |
|---|---|---|
| superproject | `d73ea3d0937407d3a0d1de8b3bd743ec6907c234` | clean before this plan was added |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

Current source still shows:

- seven nintent REST ViewSets;
- broad serializers using `fields = "__all__"`;
- nintent UI mutation routes and Source YAML display;
- four nintent Jobs, including the duplicate Preview Job;
- an Import Job whose `preview` default is false and which still exposes `disable_missing`;
- an Analyze Job that writes without a dry-by-default mode;
- nauto's duplicate Generate Desired Services Job;
- nctl DesiredNode confirmation through one remaining REST GET;
- nine nodes and nine endpoints in `nauto/seed/intent_sources.yaml`;
- nintent declarations still present in `nauto/seed/home_cluster.yaml`; and
- the obsolete `nauto/seed/service_repositories.yaml`.

These are findings to recheck, not permission to remove or rewrite anything in Phase 0.

### 4.2 Expected live orientation

The parent roadmap records a 2026-07-25 live baseline of:

- Nautobot `3.1.3`;
- nintent deployed at `c343c5a56047b0df9ad901dd4459863ef1954053`;
- migrations through `0016_remove_reconciliation_dashboard_surfaces`;
- five DesiredNodes and five DesiredEndpoints;
- two IntentSources and six DesiredServices;
- one manual DesiredServicePlacement;
- five Braindumps and five Alignment Reviews; and
- an active AI Resource Auto Review JobHook with populated Device custom fields.

All of these facts must be queried again. Counts are signals, not expected values to force.

## 5. Audit vocabulary and proof standard

### 5.1 Reference classifications

Every match in the consumer manifest must receive exactly one classification:

| Classification | Meaning |
|---|---|
| `runtime_caller` | Active code actually invokes or renders the interface |
| `operator_workflow` | A current documented command or live schedule is genuinely used |
| `contract_test` | A test protects a retained caller's unique behavior |
| `surface_test` | A test exists only because a broad framework surface exists |
| `current_documentation` | Current documentation claims the interface is supported |
| `framework_incidental` | Framework behavior exists only because a retained mutation adapter provides it |
| `migration_history` | Normal historical schema evidence |
| `historical_document` | A historical plan/report, not a current caller |
| `generated_or_cache` | Ignored generated output with no contract authority |
| `dead_reference` | Active-tree reference with no real caller |
| `unresolved` | Purpose or caller could not yet be established |

`contract_test`, `surface_test`, documentation, migration history, and "could be useful later" do
not independently justify a runtime interface.

### 5.2 Positive proof for retention

A retained interface requires:

1. the exact caller file, command, Job, page, or operator workflow;
2. the operation it performs;
3. the exact fields or behavior it consumes;
4. proof that the caller is current rather than historical; and
5. the owner responsible for future changes.

For nctl, a query constant and its typed parser are the field-level consumer contract. For UI,
human inspection of a named model is a caller only for list/detail rendering, not for generic
editability. For a Job, registration alone is not a caller; a current operator workflow,
scheduled invocation, or another named programmatic caller is required.

### 5.3 Positive proof for deletion

A surface may be selected for deletion only after:

- repository-wide active-source and current-documentation searches find no runtime caller;
- current wrappers, Makefiles, and repository automation find no caller;
- live schedules and running Job metadata find no caller;
- relevant ObjectChange metadata finds no unexplained recent origin;
- known nctl REST/GraphQL/Job call sites are classified; and
- the user is asked whether any off-repository client exists.

The audit cannot prove the absence of an unknown external client. The report must therefore state
the exact search boundary and record the user's external-caller attestation.

## 6. Roadmap-prescribed target contract to be frozen

The following is the target under audit. Phase 0 may contract it further only if doing so preserves
all named workflows. It may expand it only after documenting a concrete caller and amending the
governing roadmap.

### 6.1 Canonical domain reads

Retain:

- the one joined desired query in `nctl/src/nctl_core/sources/desired.py`;
- the one joined actual query in `nctl/src/nctl_core/sources/actual.py`;
- the Braindump list/show queries in `nctl/src/nctl_core/sources/braindump.py`; and
- GraphQL-before/write and GraphQL-after-write confirmation for every nctl domain mutation.

Remove GraphQL registration from IntentSource because its retained readers are in-process nintent
Jobs. Do not add REST or YAML readers to replace any of these GraphQL paths.

The Phase 0 report must list every retained root, selected field, selected relation, typed consumer,
and query owner. It must also record a normalized SHA-256 of each pinned query so later phases can
detect accidental selection drift while still keeping the readable selection list authoritative.

Braindump query execution may be proved structurally without saving response content. Never write
the returned body or review summary to Phase 0 evidence.

### 6.2 Final nintent REST collections

| Collection | Final methods | Writable application fields | Current writer |
|---|---|---|---|
| `nodes` | incidental GET plus PATCH | `lifecycle`, `realized_device`, `realized_device_source` | nctl lifecycle and `link_actual_node` |
| `braindumps` | GET plus POST/PATCH/DELETE | `title`, `body`, `authorship` | nctl Braindump adapter |
| `alignment-reviews` | GET plus POST/PATCH/DELETE | `braindump` on create and `summary` on create/replace | nctl review adapter |

Delete the service, endpoint, compute-platform, and compute-instance REST collections.

Phase 0 must freeze explicit serializer output fields after comparing live `OPTIONS`, model fields,
and actual nctl response consumers. The minimum application payload is expected to be:

- node: stable identity/display fields, lifecycle, realized Device link/source, and framework
  timestamps;
- Braindump: ID, title, body, authorship, and framework timestamps; and
- Alignment Review: ID, Braindump ID, summary, and framework timestamps.

Framework metadata is retained only when the final serializer or current nctl behavior genuinely
needs it. `fields = "__all__"` is not a frozen contract.

REST Job lookup/run/poll/artifact calls and `/api/status/` are protocol or health interfaces, not
domain reads. Each remaining `rest_get` must be classified as:

- status;
- Job lookup;
- Job result polling;
- FileProxy artifact retrieval; or
- an explicitly approved exception.

The known DesiredNode confirmation REST GET in `nctl_core/reconcile/ledger.py` is not an approved
exception and must be assigned to Phase 2 replacement.

### 6.3 Final human UI

Retain read-only list/detail inspection for:

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
- BrainDumpDocument, with its current Alignment Review displayed in a distinct nested panel.

Alignment Review does not need an independent list/detail page. Its human read path is the
Braindump detail page.

Remove every nintent add/edit/delete route, view, form, action, and button, plus Quick Host Add and
Source YAML diagnostics. Native Nautobot UI for Device, Cluster, VirtualMachine, Interface,
VMInterface, and IPAddress is outside this initiative.

The Phase 0 report must freeze route names and URL patterns, not only route counts.

### 6.4 Final YAML roots

The canonical document is `nauto/seed/intent_sources.yaml` with exactly these roots:

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

Unknown roots and obsolete aliases must fail before any write. Omitted roots and rows mean no
change, never deletion.

The Phase 0 report must freeze, for every root:

- identity fields;
- accepted input fields;
- defaults and normalization;
- references and ordering constraints;
- create-owned fields;
- update-owned fields;
- fields rejected because another operation owns them; and
- whether an existing row's value is preserved on repeat import.

In particular:

- an existing DesiredNode lifecycle is not overwritten by YAML;
- realized links and link-source fields are not YAML-owned;
- source-analysis fields are not YAML-owned;
- operator-owned DesiredService lifecycle, requirements, and notes are preserved from analysis;
  and
- omission cannot disable an IntentSource.

### 6.5 Final Job boundary

Phase 0 must freeze the exact public variables and versioned artifact schema for the three retained
nintent Jobs.

The target variable contract is:

| Job | Variables after contraction |
|---|---|
| Import Intent Sources | `source_file`; `apply` defaulting to false |
| Analyze Intent Sources | `fetch_timeout`; `include_disabled`; `apply` defaulting to false |
| Reconcile Desired IPAM Intent | existing `commit_changes`, `include_inactive`, and `desired_node` |

`disable_missing` is removed because missing input never authorizes disabling. The current
`preview` flag is replaced by the safer polarity of `apply=false`. Preview Intent Source Analysis
is deleted rather than aliased.

Freeze one schema for Import preview and apply, with at least:

- schema version;
- mode;
- configured and resolved source identity;
- source SHA-256 and repository revision when available;
- exact scope and root counts;
- per-object model, identity, action, and changed fields;
- conflicts and validation errors;
- create/update/unchanged totals;
- whether writes were requested and committed; and
- transaction result.

Freeze one schema for Analyze preview and apply, with at least:

- schema version and mode;
- exact selected IntentSource identities;
- input reference/digest information available from the analyzer;
- exact proposed IntentSource, DesiredService, and DesiredDependency changes;
- preserved operator-owned fields;
- source and validation errors;
- create/update/delete/unchanged totals; and
- whether writes were requested and committed.

The Phase 0 report must choose the final filenames, schema identifiers, field names, ordering, and
transaction scope. Preview and apply must use the same planner and artifact shape. Apply must
refuse to begin writes when planning has ownership conflicts or validation errors.

Retain `ipam-reconcile-summary.json` and
`nctl.ipam.reconcile.summary.v1` unchanged unless the audit finds a concrete incompatibility.

### 6.6 CLI boundary

Retain the current eleven top-level nctl commands:

```text
status
actual
drift
reconcile
lifecycle
render
apply
ops
braindump
ssh
session
```

Phase 0 does not add a generic CRUD, REST passthrough, GraphQL passthrough, or Job wrapper.

## 7. Procedure

### Step 0 — Establish the evidence boundary and recapture the baseline

1. Create `.local/interface-contract/p0/<timestamp>/` with mode `0700`.
2. Create evidence files with mode `0600`; set a restrictive umask before capture.
3. Record timestamp, timezone, working directory, OS/tool versions needed to reproduce the audit,
   and the exact list of documents reviewed.
4. Record root/submodule revisions, branches, remotes, submodule pointers, dirty state, staged
   state, and untracked paths.
5. Do not clean, reset, stash, or overwrite a dirty worktree. Classify every overlapping change.
6. Record the installed nintent package revision and image/container identity independently for
   web, worker, and scheduler.
7. Record Nautobot/Django/PostgreSQL versions and applied nintent migrations.
8. Record running containers and service health without rebuilding or restarting them.
9. Record active/running Jobs, JobHooks, ScheduledJobs, and JobResults using metadata-only
   queries.
10. Record the current GitRepository revision that supplies nauto Jobs and seeds, if exposed.

Gate: all later evidence is tied to one exact repository/live tuple. An unexplained in-scope dirty
change or mixed installed nintent revision blocks the freeze.

### Step 1 — Build the static interface and consumer inventory

1. Inventory nintent model GraphQL registration, REST serializers/ViewSets/router entries, UI
   views/forms/routes/templates/navigation, YAML loaders/importers, Jobs, and tests.
2. Inventory nctl GraphQL query constants, typed parsers, REST calls, Job protocol calls, CLI
   commands, docs, and tests.
3. Inventory nauto seed writers, generated-service code, seed roots, Job registration, schedules,
   docs, and tests.
4. Search tracked shell scripts, Makefiles, task runners, CI/workflows, and current docs across the
   superproject and all submodules.
5. Search active source and current documentation for every term in the parent roadmap's Required
   Searches section.
6. Search for the literal REST route paths and UI route names, not only class names.
7. Enumerate every `rest_get`, `rest_post`, `rest_patch`, and `rest_delete` caller.
8. Enumerate every `fields = "__all__"` and every `@extras_features("graphql")`.
9. Separate active references from historical reports, migrations, generated caches, and private
   evidence.
10. Classify every match using Section 5.1 and record file plus line number.

The search must include, at minimum:

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

Gate: the manifest contains no unclassified active match.

### Step 2 — Record live interface, schema, and measurement baselines

Using only the allowed read paths:

1. Introspect GraphQL root names and field availability.
2. Execute structural forms of the pinned desired and actual queries and record root counts and
   schema success.
3. Validate Braindump query shape without persisting prose.
4. Enumerate registered REST collection paths, allowed methods, serializer input/output fields,
   filters, and permissions through source plus `OPTIONS`.
5. Enumerate nintent UI route names and URL patterns through Django's resolver.
6. Enumerate YAML roots accepted by the current loader, including the current unknown-root defect
   and explicit obsolete-alias errors.
7. Record Job names, public variables/defaults, registration, schedules, recent execution
   aggregates, artifact names, and artifact schemas without downloading private artifact content.
8. Record `nctl --help` and relevant subcommand help.
9. Record test counts by component and interface area. Prefer collection-only commands where
   available.
10. Repeat the parent roadmap's line measurements with commands and inclusion/exclusion rules in
    the evidence.

Do not use a successful empty response as proof that a populated path works. For Phase 0, route and
schema presence can be proved structurally; live data counts prove only that the roots return the
expected object categories.

Gate: the final report can reproduce every current-state count and explain every deviation from
the parent roadmap baseline.

### Step 3 — Capture live ownership and provenance without private prose

For every nintent model in the final matrix, capture:

- aggregate row count;
- stable identity and relationship IDs needed for comparison;
- IntentSource links;
- placement `assignment_source`;
- realized links and link-source provenance;
- lifecycle and other ownership-sensitive fields;
- create/update timestamps;
- aggregate Braindump authorship and review-presence counts; and
- ObjectChange metadata sufficient to identify origin class.

For ObjectChange, read only bounded metadata such as content type, object ID, action, timestamp,
actor, request/correlation identifier, and change context when safe. Do not read or save serialized
object data, request bodies, Braindump bodies, review summaries, or secrets.

For free-form desired fields such as notes or descriptions:

- record presence, length, and SHA-256 when equality must be checked;
- do not reproduce live-only text in the tracked report; and
- show the user the text only through an already-supported private inspection path when a semantic
  decision is unavoidable.

Classify provenance as `yaml_import`, `source_analysis`, `nctl`, `ipam_job`, `nauto_seed`,
`human_ui`, `rest_client`, `migration`, `unknown`, or another evidence-backed origin. Do not infer
provenance solely from a current field value.

Gate: all structural rows have provenance evidence or are explicitly marked unknown.

### Step 4 — Reconcile live nodes/endpoints with the checked-in YAML

1. Parse `nauto/seed/intent_sources.yaml` using the current loader and a second independent YAML
   root/identity inventory.
2. Compare the union of live and checked-in DesiredNode identities.
3. Compare each node's structural fields, preserving the distinction between create-owned,
   YAML-update-owned, nctl-owned, and realized-link fields.
4. Compare the union of live and checked-in DesiredEndpoint identities using the compound identity
   required by the importer.
5. Compare endpoint IP/DNS/mDNS/MAC values, source fields, policies, dnsmasq fields, and realized
   links without treating an operational field as YAML-owned.
6. Include IP ranges, placements, operational overrides, and pending compute rows so that Phase 1
   cannot accidentally omit a confirmed structural row.
7. Assign each object and each conflicting field one disposition:
   `confirmed_live_intent`, `confirmed_checked_in_intent`, `stale_seed`, or `unresolved`.
8. Record the evidence supporting each non-unresolved classification.

Rules:

- presence in both locations does not prove field agreement;
- a checked-in-only row is not automatically desired;
- a live-only row is not automatically stale;
- a previously approved report may prove historical approval but not necessarily current intent;
- operational fields remain with their named writer; and
- no comparison command may write a normalization result back to either source.

Gate: every node, endpoint, range, placement, override, and compute identity has a disposition or
is listed for user resolution.

### Step 5 — Reconcile IntentSources and DesiredServices

1. Compare all live IntentSources with:
   - `nauto/seed/home_cluster.yaml`;
   - `nauto/seed/intent_sources.yaml`;
   - `nauto/seed/service_repositories.yaml`; and
   - configured source-analysis inputs.
2. Compare all live DesiredServices by their canonical source/catalog/service identity.
3. Separate source-derived fields from operator-owned lifecycle, requirements, and notes.
4. Compare DesiredDependency rows and source-analysis proposals.
5. Identify which live rows came from Seed Home Cluster, Import, Analyze, UI, REST, or an unknown
   writer using bounded audit metadata.
6. Determine which declarations must move to the canonical YAML in Phase 1 and which obsolete
   nauto source/generator artifacts have no unique consumer.
7. Never run Analyze or Generate Desired Services during this audit.
8. Assign the same four dispositions used in Step 4.

Gate: each live and checked-in source/service identity has a disposition or is listed for user
resolution, and field ownership is explicit.

### Step 6 — Resolve ownership and desired-presence decisions

1. Produce one sanitized unresolved-decision table from Steps 4 and 5.
2. Group questions by identity so the user can decide without reading raw audit logs.
3. Ask the user whether each unresolved identity should:

   - remain as confirmed desired intent and be represented in canonical YAML;
   - be treated as a stale checked-in seed and omitted from the Phase 1 proposal;
   - be treated as a confirmed stale live row, remain untouched by this initiative, and receive a
     separately authorized removal follow-up; or
   - remain unresolved and block the phase.
4. Ask the user to disclose any current off-repository REST/UI clients or operational wrappers in
   the affected scope.
5. Record the decision, date, decision authority, and affected identity in the report.
6. Do not translate "omit" into delete. Any later removal of a live desired row requires its own
   explicit plan and authority.

Gate: no unresolved desired-presence or caller question remains. Otherwise the phase is `blocked`.

### Step 7 — Freeze the final interface matrix and field-level contracts

1. Complete the parent roadmap matrix with one evidence reference for every retained checkmark.
2. For every removed surface, reference the no-caller proof and external-caller attestation.
3. Freeze normalized GraphQL query texts, roots, selections, relations, typed consumers, and query
   digests.
4. Freeze REST collection paths, methods, request fields, response fields, permissions, and
   GraphQL confirmation reads.
5. Freeze retained UI route names, paths, displayed relationships/provenance, and the prohibition
   on domain-mutation POSTs.
6. Freeze the nine YAML roots and per-root identity/input/ownership contracts.
7. Freeze Import, Analyze, and IPAM Job names, variables, defaults, transaction boundaries,
   artifact filenames, schema identifiers, and ordered payload fields.
8. Freeze the final nctl command set and classify all REST helpers.
9. Record the active AI Resource Auto Review JobHook as explicitly deferred and untouched.
10. Confirm that no model deletion or new migration is required by the frozen contract.

If a genuinely necessary model/schema change is discovered, Phase 0 may still finish only after
the roadmap is amended and the later migration owner is named. Do not create the migration here.

Gate: Phases 1–4 can implement the contract without making a new ownership or interface decision.

### Step 8 — Amend the active VM Phase 3 plan

Make a narrow current-state amendment to `devdocs/big/vm/p3/plan.md`:

1. State that the interface-contract roadmap supersedes Phase 3's broad UI/REST/Source YAML
   mutation assumptions.
2. Preserve completed historical compute-schema, desired-MAC, migration, and safety evidence.
3. Make Steps 9–12 depend on:

   - the Phase 0 disposition ledger;
   - Phase 1's strict canonical YAML and dry-by-default Import implementation; and
   - the final matched live interface from Phase 4.
4. Prohibit seeding through the compute REST collections, editable UI, or Source YAML diagnostic
   page.
5. Require the compute seed to be part of the one reviewed
   `nauto/seed/intent_sources.yaml` proposal.
6. Keep VM Phase 3 ownership of compute values, desired MAC, dnsmasq safety, target isolation, and
   no-Proxmox-actuation proof.
7. Keep interface-contract ownership of importer behavior, source identity/digest, exact
   preview/apply artifact, coordinated desired-data transition, and route contraction.
8. Prevent duplicate applies: one approved Import apply and repeat proof may satisfy both
   initiatives when it carries both sets of evidence.
9. Replace stale status language with the deployed-through-`0016` baseline and the current
   `implemented, not seeded` state where applicable.

Do not rewrite earlier VM reports or erase the fact that broader interfaces existed when their
tests were originally run.

Gate: the VM plan cannot proceed through a route that this initiative removes.

### Step 9 — Verify the audit and publish the report

1. Re-run all required searches after the VM plan amendment.
2. Confirm that only documentation and private evidence changed.
3. Confirm root and submodule diffs contain no runtime, seed, migration, or dependency edits.
4. Confirm no live row counts, links, timestamps, Job state, or migration state changed because of
   Phase 0.
5. Confirm no new nctl operation/event log or Nautobot JobResult was created by the audit.
6. Confirm no secret or private prose appears in tracked changes or private command logs.
7. Run `git diff --check` in the root and every submodule.
8. Write `report.md` using the structure in Section 8.
9. Mark the phase `complete` only if every exit criterion passes; otherwise mark it `blocked` and
   name each unresolved item.

## 8. Required report structure

`report.md` must contain:

1. **Status and timestamp**
2. **Evidence location and redaction statement**
3. **Exact repository/live revision tuple and dirty state**
4. **Installed package/container and migration parity**
5. **Current interface and size measurements**
6. **Classified consumer manifest summary**
7. **Final interface matrix with evidence references**
8. **Frozen GraphQL selection manifest**
9. **Frozen REST method/field manifest**
10. **Frozen read-only UI route manifest**
11. **Frozen YAML root/field/ownership manifest**
12. **Frozen Job variable and artifact schemas**
13. **Live ownership/provenance summary**
14. **Node/endpoint/live-YAML disposition ledger**
15. **IntentSource/service disposition ledger**
16. **User decisions and external-caller attestation**
17. **VM Phase 3 amendment summary**
18. **Non-mutation proof**
19. **Deviations and explicitly deferred items**
20. **Exit-criteria table and Phase 1 handoff**

The tracked report may include public model names, route names, aggregate counts, stable UUIDs
needed for the transition, and non-secret configuration identities. It must not include:

- token or credential values;
- raw API headers;
- Braindump bodies;
- Alignment Review summaries;
- raw ObjectChange snapshots;
- private desired notes or descriptions;
- raw SSH keys;
- private artifact content; or
- broad user-environment details unrelated to this initiative.

## 9. Verification checklist

### Contract and consumers

- [ ] Every retained GraphQL root and field has a typed caller.
- [ ] Every retained REST mutation has a named writer.
- [ ] Every retained UI route maps to a named human inspection need.
- [ ] Every retained YAML root has an importer or pending approved seed consumer.
- [ ] Every retained Job has a named operator or nctl caller.
- [ ] Every retained CLI command remains outside this initiative's deletion scope.
- [ ] Every deleted REST/UI/Job surface has no real caller in the audit boundary.
- [ ] Every generic REST helper and serializer-wide field declaration is classified.

### Live ownership

- [ ] Live counts and source/link provenance were recaptured.
- [ ] ObjectChange inspection excluded serialized content.
- [ ] Every live/YAML node and endpoint difference has a disposition.
- [ ] Every live/YAML IntentSource and DesiredService difference has a disposition.
- [ ] Ranges, placements, overrides, and compute rows cannot be lost by the Phase 1 proposal.
- [ ] Operator-owned and source-derived service fields are separated.
- [ ] User decisions are recorded for every evidence gap.

### Safety

- [ ] No REST mutation, Job run, reconcile operation, seed apply, migration, rebuild, or restart
      occurred.
- [ ] No desired or actual row changed.
- [ ] No live session was created for UI inspection.
- [ ] No private prose or secret entered evidence.
- [ ] AI Resource Auto Review remained untouched and explicitly deferred.
- [ ] Missing YAML was never interpreted as deletion.

### Coordination and reporting

- [ ] VM Phase 3 Steps 9–12 depend on the final Import contract.
- [ ] Historical reports remain historical.
- [ ] Current docs and runtime facts are not conflated.
- [ ] All measurements include reproducible commands and scopes.
- [ ] Root/submodule diffs contain documentation only.
- [ ] `git diff --check` passes.
- [ ] `report.md` states `complete` or `blocked` truthfully.

## 10. Exit criteria

Phase 0 is `complete` only when:

- the exact revision/live tuple is recorded and reproducible;
- every retained matrix checkmark has a named caller and exact evidence;
- every planned deletion has no real caller within the declared audit boundary;
- the user has attested to any off-repository caller status;
- REST methods/fields, GraphQL selections, UI routes, YAML roots/fields, Job variables, and
  artifact schemas are frozen;
- all current structural desired identities have an evidence-backed disposition;
- no live/YAML discrepancy remains unresolved;
- the VM Phase 3 seed steps use only the final canonical Import path;
- no live, desired, actual, Job, migration, or operational mutation occurred; and
- the final report contains no secret or private prose.

If the audit is otherwise complete but one identity or caller remains unresolved, the correct
state is `blocked`, not partially complete and not complete.

## 11. Rollback

There is no runtime or data rollback because Phase 0 performs no runtime or data mutation.

If a documentation decision is wrong:

1. stop before Phase 1 implementation;
2. correct this plan, the parent roadmap if necessary, the VM amendment, and the report;
3. preserve the old report in Git history rather than fabricating a clean narrative; and
4. repeat the affected audit and user-decision gate.

Private evidence may be archived or removed only after confirming it is under the intended
`.local/interface-contract/p0/` directory. Do not use a broad recursive deletion target.

## 12. Phase handoff

After a `complete` Phase 0:

- Phase 1 receives the confirmed live-to-YAML disposition ledger, strict nine-root contract, and
  frozen Import/Analyze Job schemas;
- Phase 2 receives the exact REST deletion/narrowing manifest and GraphQL confirmation contract;
- Phase 3 receives the exact read-only UI route manifest;
- Phase 4 receives the revision tuple, live baseline, user-approved desired proposal boundary,
  and rollback inputs; and
- VM Phase 3 receives the same canonical seed/import contract without a duplicate writer or apply.

No later phase may reinterpret an omitted row as deletion, add a compatibility route, retain an
unused writer, or broaden a mutation surface without naming a new real caller and amending the
governing contract.
