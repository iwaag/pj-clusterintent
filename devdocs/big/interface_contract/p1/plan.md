# Interface Contract Phase 1 Implementation Plan: Establish One Source-Controlled Desired Writer

Parent: [roadmap.md](../roadmap.md) — Phase 1.

Predecessor: [Phase 0 final report](../p0/report.md) — `complete`.

Status: proposed; coordinated `nintent`/`nauto` implementation and disposable-environment
verification only. No live deployment or live desired-state mutation is authorized in this phase.

## 1. Goal and required transition

Establish `nauto/seed/intent_sources.yaml` plus the nintent `Import Intent Sources` Job as the one
source-controlled bulk desired-state writer. Make both Import and Analyze safe review operations
that default to a zero-write preview, and remove nauto's overlapping desired-state seed and
candidate-generation paths.

The Phase 1 transition is:

```text
before
  desired declarations split across home_cluster.yaml and intent_sources.yaml
  + confirmed live-only intent absent from source control
  + six stale nodes and their placement/override declarations still checked in
  + unknown YAML roots silently ignored
  + Import defaults to apply and can disable omitted IntentSources
  + Import preview performs writes and relies on transaction rollback
  + Analyze writes immediately and has no versioned plan artifact
  + a separate Preview Intent Source Analysis Job
  + Seed Home Cluster writes nintent IntentSource/DesiredService rows
  + Generate Desired Services produces a second desired-service proposal format

after Phase 1
  one strict, reviewed nauto/seed/intent_sources.yaml document
  + one nintent Import Job that previews by default and applies atomically only when requested
  + one nintent Analyze Job that previews by default and applies only source-owned changes
  + deterministic, versioned artifacts for preview and apply
  + omission that never disables, deletes, retires, or unlinks
  + no nintent desired-state writes in Seed Home Cluster
  + no Preview Intent Source Analysis Job
  + no Generate Desired Services Job or service_repositories seed/output contract
```

The observable success path is:

```text
strict YAML
  -> deterministic Import preview
  -> zero database writes
  -> exact reviewed object plan
  -> explicit Import apply
  -> one atomic commit
  -> repeat Import apply
  -> every object unchanged

selected IntentSource rows
  -> deterministic Analyze preview
  -> zero database writes
  -> exact reviewed source/service/dependency plan
  -> explicit Analyze apply
  -> source-owned changes only
  -> repeat Analyze with identical fetched inputs
  -> no repeated database changes
```

This phase is complete only when those transitions run through the real Job implementation against
an isolated Nautobot database. Passing pure helper tests alone is not sufficient.

## 2. Authority, prerequisites, and safety boundary

### 2.1 Governing inputs

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- the parent roadmap;
- [Phase 0 plan](../p0/plan.md);
- all Phase 0 reports, with [report.md](../p0/report.md) authoritative;
- especially [report4.md](../p0/report4.md), [report5.md](../p0/report5.md),
  [report6.md](../p0/report6.md), and [report7.md](../p0/report7.md);
- `devdocs/vision/refactor/vision.md`;
- `devdocs/big/vm/p3/plan.md`, including the Phase 0 supersession note;
- `nintent/README.md`, `README_QUICK.md`, `README_DEV.md`, and `CONCEPT.md`;
- `nauto/README.md` and `README_DEV.md`;
- `nintent/nautobot_intent_catalog/loaders.py`;
- `nintent/nautobot_intent_catalog/importers.py`;
- `nintent/nautobot_intent_catalog/jobs.py`;
- the related nintent loader/importer/analysis/Job tests;
- `nauto/jobs/seed_home_cluster.py`;
- `nauto/jobs/generate_desired_services.py`;
- `nauto/jobs/__init__.py`;
- both nauto seed documents and their tests; and
- all current documentation found by the required searches in Section 9.

Phase 0's disposition ledger and frozen interface contract are authoritative. Phase 1 must not
independently resurrect a stale node, drop a confirmed row, add a tenth YAML root, or retain an old
Job as an alias.

### 2.2 Allowed changes

Phase 1 may change:

- nintent YAML loading, import planning/apply, analysis planning/apply, Job registration, tests,
  and current documentation;
- nauto's canonical desired YAML, home-cluster seed, Job registration, tests, and current
  documentation;
- the superproject pointers for coordinated nintent/nauto commits;
- this plan and the Phase 1 report; and
- untracked evidence under `.local/interface-contract/p1/<timestamp>/`.

The phase may build and run a disposable Nautobot/PostgreSQL/Redis environment whose database,
containers, network, volumes, ports, and credentials are isolated from the running development
stack.

### 2.3 Prohibited actions

Phase 1 must not:

- run Import, Analyze, Seed Home Cluster, Generate Desired Services, IPAM, Ingest, or another Job
  against the current live Nautobot database;
- connect a disposable test to `my_postgres_db`, `service_scripts-redis-1`, the live Nautobot
  database name, or the live media volume;
- apply the edited canonical YAML to the live database;
- rebuild or restart `nautobot-nautobot-1`, its worker, or its scheduler;
- use the existing development compose stack as a disposable test target;
- mutate or delete live desired, actual-ledger, Braindump, Alignment Review, JobHook, ScheduledJob,
  JobResult, or custom-field state;
- run `nctl reconcile --yes`, Ansible actuation, nodeutils collection, or ingest;
- implement VM compute rows, compute linking, compute drift, or guest creation;
- change REST, GraphQL, or nintent UI contracts assigned to Phases 2 and 3;
- create a database migration unless implementation unexpectedly changes models, in which case
  stop and amend the governing plan before proceeding;
- add compatibility Job names, legacy variables, dual readers/writers, or deprecated YAML roots;
- copy secrets, tokens, Braindump bodies, Alignment Review summaries, or credential-bearing URLs
  into tracked files or evidence; or
- push commits. Per the local environment memo, deployment later requires the user to push the
  nintent commit; Phase 4 owns that coordinated rollout.

### 2.4 Planning-time repository snapshot

Observed while this plan was authored on 2026-07-25:

| Repository | Revision | State |
|---|---|---|
| superproject | `590f8f3c3784ae0a3f68a2bbba5c7f5dd3f1e988` | clean before this plan was added |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean; out of scope |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean; out of scope |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean; out of scope |

This is orientation only. Step 0 must recapture exact revisions, submodule pointers, staged and
unstaged changes, and untracked files. Preserve unrelated user changes and stop if an in-scope
worktree has an unexplained overlapping edit.

## 3. Scope and non-goals

### 3.1 In scope

- materialize the complete Phase 0 disposition ledger in
  `nauto/seed/intent_sources.yaml`;
- remove nintent roots from `nauto/seed/home_cluster.yaml`;
- require the canonical checked-in document to declare all nine roots, using empty lists where
  this phase has no confirmed rows;
- reject every unknown top-level YAML root while retaining strict per-entry validation;
- preserve obsolete-root-specific errors for `service_repositories` and
  `desired_node_operational_configs`;
- replace Import's `disable_missing` and `preview` variables with `apply=false`;
- build a read-only Import plan before any mutation;
- preserve existing-node lifecycle and every realized-link field;
- fail before writes on ownership conflict or validation error;
- apply an accepted Import plan in one transaction and positively confirm the committed rows;
- add one stable, versioned Import artifact shape shared by preview and apply;
- add `apply=false` to Analyze and make its preview read-only;
- plan Analyze changes before mutation and constrain apply to analysis-owned fields;
- preserve operator-owned DesiredService and DesiredDependency fields;
- add one stable, versioned Analyze artifact shape shared by preview and apply;
- remove `PreviewIntentSourceAnalysis`;
- remove nintent imports and writes from `SeedHomeCluster`;
- delete `GenerateDesiredServices`, its registration, tests, seed file, output documentation, and
  candidate-output contract;
- verify no schema migration is generated;
- verify preview/apply/repeat against an isolated real Nautobot database; and
- update current documentation and produce one Phase 1 report.

### 3.2 Explicitly retained

- all nintent domain models and migration history through `0016`;
- the nine canonical YAML roots, including empty compute roots reserved for the approved VM
  Phase 3 handoff;
- `Import Intent Sources`, `Analyze Intent Sources`, and `Reconcile Desired IPAM Intent`;
- IPAM Job variables, artifact, transactions, and behavior unchanged;
- nintent GraphQL registration, REST collections, UI forms/routes, and nctl read/write behavior
  unchanged until their assigned phases;
- `Seed Home Cluster` for native Nautobot prerequisites only;
- `Ingest Nodeutils Inventory`, its Proxmox actual-ledger behavior, and its registration;
- `AI Resource Review`, its JobHook behavior, and its four Device custom fields;
- nintent source-analysis fetch and normalization behavior except where necessary to expose a
  deterministic plan;
- historical migrations, plans, reports, and already-created JobResult/FileProxy records; and
- omission-as-no-op behavior for both missing roots and missing rows.

### 3.3 Out of scope

- applying the canonical YAML to live state or deploying the new Jobs;
- adding a Job CLI adapter to nctl;
- changing the canonical GraphQL selections;
- contracting REST or making the nintent UI read-only;
- deleting domain rows absent from YAML;
- reconciling the semantic provenance of the `home.arpa` convention;
- writing Braindump or Alignment Review prose;
- adding desired dependencies as a tenth YAML root;
- seeding compute platform/instance rows before VM Phase 3 supplies its approved values;
- changing `nctl lifecycle`, IPAM, actual ingest, drift, render, reconcile, evidence, SSH, or
  actuation behavior;
- broad refactoring of the large loader, importer, analysis, or Job modules unrelated to the
  retained contracts; and
- live deployment, backup, rollback, and maintenance-window work assigned to Phase 4.

## 4. Canonical YAML contract and exact Phase 0 disposition

### 4.1 Document and root contract

`nauto/seed/intent_sources.yaml` is the only checked-in bulk desired-state document. The checked-in
file must explicitly contain these roots in this order:

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

The loader continues to accept an omitted known root as an empty no-op for an operator-supplied
partial document. The canonical checked-in file is stricter for readability: it declares all nine
roots, including `[]` for confirmed-empty compute and operational-override roots.

An unknown top-level key is an error even if every known root is valid. The loader may collect all
validation errors for reporting, but Import must not plan or apply any row when at least one root
or entry error exists.

### 4.2 Canonical identity set after this phase

The target checked-in document contains:

| Root | Exact target scope |
|---|---|
| `intent_sources` | `infrastructure`, `manual` |
| `desired_nodes` | `agbach`, `agdnsmasq`, `aghub`, `agpc`, `agstudio` |
| `desired_endpoints` | one `primary` endpoint for each of the five nodes |
| `desired_ip_ranges` | `dhcp-reserved`, `network-infra`, `dhcp-unreserved` |
| `desired_compute_platforms` | empty; VM Phase 3 owns later additions |
| `desired_compute_instances` | empty; VM Phase 3 owns later additions |
| `desired_services` | Infrastructure's `prometheus`, `grafana`, `nomad`, `prometheus-node-exporter`, `haos`, plus Manual's `dnsmasq` |
| `desired_service_placements` | one `dnsmasq` instance on `agdnsmasq` |
| `desired_node_operational_overrides` | empty |

The six checked-in-only nodes `agmbp2019`, `agmbp2018`, `agprometheus`, `aggrafana`, `agnomad`,
and `aghaos` are stale seed data and must be removed from the checked-in document. Remove all six
old service placements and all six old operational overrides, including the old
`agbach`/`agpc`/`agstudio` override rows that Phase 0 confirmed are not live current intent.
Omitting those YAML rows does not request a live delete; no matching live rows existed in Phase 0.

### 4.3 Exact content source and field handling

Use Phase 0's private structural evidence and a fresh read-only query at Step 0 to transcribe every
YAML-owned field. Do not infer missing values from display labels, Quick Host Add defaults, or
realized objects.

At minimum:

- encode `agbach` and `aghub` with lifecycle `approved`, and `agdnsmasq`, `agpc`, and `agstudio`
  with lifecycle `active`, matching the Phase 0 confirmed state; lifecycle is used only if a row is
  created and is preserved for an existing row;
- encode each primary endpoint with its confirmed `dns_name`, explicit IP address, and normalized
  `ip_policy: static`;
- explicitly encode every confirmed DNS or mDNS name; an omitted optional name must not acquire a
  hidden Quick-Host-Add-era default during import;
- do not encode `realized_ip_address`, `realized_ip_address_source`, Device links, IPAddress IDs,
  or other actual-ledger identifiers;
- preserve the exact YAML-owned dnsmasq generation fields found on the live endpoint rows rather
  than guessing from the service name;
- encode all three IP ranges with their current slug, start/end address, range policy, lifecycle,
  dnsmasq flag/options, and description;
- encode the Manual/dnsmasq service and placement from their complete live model fields, including
  normalized lower-case `assignment_source: manual`;
- do not derive the Manual/dnsmasq declaration from private Braindump prose; the user's Phase 0
  attestation is the authority for its desired presence;
- move the Infrastructure source and its five services from `home_cluster.yaml` without changing
  their confirmed fields; and
- leave all compute roots empty. Do not copy pending VM Phase 3 proposals into this phase.

The canonical file must pass the production nintent loader with zero errors. A deterministic
round-trip comparison must show exactly the counts in Section 4.2 and no reference to a removed
node. Compare the normalized endpoint defaults with the complete read-only live fields before
accepting the proposal. If the current `default_dns_name()`/`default_mdns_name()` importer behavior
would synthesize a value not present in confirmed intent, remove that implicit synthesis and update
its focused tests in this phase; do not alter the YAML proposal merely to preserve an obsolete
default.

## 5. Import Intent Sources contract

### 5.1 Public Job variables

The final public variables are:

| Variable | Contract |
|---|---|
| `source_file` | optional path; empty resolves through the existing App configuration |
| `apply` | Boolean, default `false`; the only authority to commit |

Delete `disable_missing` and `preview`. Do not accept them as aliases and do not invert a legacy
value. Existing schedules using an old variable must fail visibly after deployment rather than
silently changing behavior; Phase 0 found no such schedule.

### 5.2 Plan/apply separation

Refactor the current `_import_intent_rows()` mutation-and-diff path into two explicit boundaries:

1. a read-only planner that compares normalized entries with current ORM state and returns a
   deterministic plan; and
2. an applier that consumes a valid plan inside one `transaction.atomic()` block.

The planner must:

- perform no `save()`, `update()`, `delete()`, `bulk_create()`, M2M mutation, or rollback-dependent
  temporary write;
- resolve references against the union of existing identities and rows planned for creation;
- classify every YAML row as `create`, `update`, `unchanged`, or `conflict`;
- report exact changed field names and JSON-safe before/after values;
- order roots by the canonical dependency order and objects by stable natural identity;
- identify duplicate or ambiguous existing rows as conflicts;
- reject a reference that is neither existing nor planned;
- report the configured path, resolved path, source digest, and Git revision when available;
- include every known root in scope counts, including zero-count roots;
- stop the apply boundary when loader errors, validation errors, reference errors, or ownership
  conflicts exist; and
- never produce `disable`, `retire`, `unlink`, or `delete` actions from omission.

For `apply=false`, finish after plan and artifact creation. The preview must leave row counts,
field values, ObjectChange counts, JobHooks, and related actual objects byte-for-byte/logically
unchanged; transaction rollback is not the mechanism used to obtain that result.

For `apply=true`:

1. load and normalize the source once;
2. build the read-only plan;
3. reject the run before mutation if the plan is not applicable;
4. enter one transaction;
5. lock all existing rows in scope in deterministic model/identity order;
6. revalidate that the locked values still match the plan's preconditions;
7. apply creates and updates in dependency order with `full_clean()` before save;
8. commit only if every planned row succeeds;
9. refetch every planned identity and confirm the committed YAML-owned values; and
10. report the truthful transaction/confirmation result even when a post-commit confirmation or
    artifact-write step fails.

A validation or persistence exception rolls back the entire Import transaction. A concurrent
change that invalidates a precondition becomes a conflict; it is not overwritten.

### 5.3 Import field ownership

The planner must encode ownership explicitly rather than relying on which keys happen to be in a
defaults dictionary.

| Model/root | Create behavior | Existing-row update behavior |
|---|---|---|
| IntentSource | create all accepted declared fields | update declared source configuration only; preserve analysis status/timestamps/summary |
| DesiredNode | create declared fields including initial lifecycle | update declared structural fields except lifecycle; preserve lifecycle and all realized links/sources |
| DesiredEndpoint | create declared endpoint intent | update declared intent fields; preserve realized IP link/source and framework fields |
| DesiredIPRange | create declared range intent | update declared range fields |
| DesiredComputePlatform | create declared compute intent | update declared intent; preserve realized Cluster link/source |
| DesiredComputeInstance | create declared compute intent | update declared intent; preserve realized VM link/source |
| DesiredService | create accepted initial/operator fields | update only YAML-owned operator fields; preserve analysis-owned fields and operational analysis evidence |
| DesiredServicePlacement | create declared placement | update declared placement fields |
| DesiredNodeOperationalOverride | create declared override | update declared override fields |

For an existing DesiredService:

- YAML may update `lifecycle` and `notes`;
- preserve `requirements` because the current YAML schema has no corresponding explicit input
  field;
- treat identity fields as immutable identity, not updates;
- preserve source-analysis fields such as source/catalog metadata, analysis provenance, and
  `last_analyzed_at`;
- preserve existing `name`, `slug`, and `display_name` unless a later governing amendment assigns
  them to YAML update ownership; and
- if YAML proposes a different value for a preserved field, emit an ownership conflict instead of
  overwriting or silently ignoring the disagreement.

The accepted YAML entry may still supply create-time values for fields allowed by the existing
strict loader. Create-time authority does not imply repeat-import update authority.

### 5.4 Import artifact

Preview and apply use one filename and one schema:

```text
filename: intent-import-result.json
schema_version: nintent.intent-import.v1
```

The top-level shape is:

```text
schema_version
mode                         # preview | apply
source
  configured_path
  resolved_path
  sha256
  repository_revision       # null when unavailable
scope
  roots                     # canonical ordered root names
  counts_by_root
objects
  - model
    root
    identity
    action                   # create | update | unchanged | conflict
    changed_fields
    preserved_fields
conflicts
errors
totals
  create
  update
  unchanged
  conflict
writes
  requested
  attempted
  committed
transaction
  status
  error
confirmation
  status
  mismatches
```

Requirements:

- JSON object keys and object lists are deterministically ordered;
- preview and apply have the same shape;
- `writes.requested` is exactly `apply`;
- preview reports `attempted=false`, `committed=false`, and
  `transaction.status=not_requested`;
- a blocked apply reports `attempted=false`, `committed=false`, and
  `transaction.status=blocked`;
- successful apply reports `attempted=true`, `committed=true`,
  `transaction.status=committed`, and `confirmation.status=confirmed`;
- rolled-back apply reports `committed=false` and names the failing stage without claiming that
  no writes were attempted;
- identities use stable natural keys, never temporary preview UUIDs;
- changed fields contain no credentials, raw tokens, Braindump bodies, or Alignment Review
  summaries; and
- the Job logs one bounded aggregate summary in addition to the FileProxy artifact so a
  post-mutation artifact failure does not erase the transaction outcome.

Old `intent-import-preview.json` and `intent-import-apply.json` names are not retained as aliases.
Historical FileProxy artifacts with those names remain historical data and are not modified.

## 6. Analyze Intent Sources contract

### 6.1 Public Job variables

The final public variables are:

| Variable | Contract |
|---|---|
| `fetch_timeout` | existing positive timeout |
| `include_disabled` | existing scope flag, default `false` |
| `apply` | Boolean, default `false`; the only authority to commit |

Delete `PreviewIntentSourceAnalysis`, its `source_file` and `include_service_preview` variables,
registration, tests, and documentation. Do not retain the old Job name as a wrapper around
Analyze.

### 6.2 Read-only analysis plan

Separate source fetching/normalization and ORM diff planning from mutation. Analyze preview must:

- select exact IntentSource identities in deterministic order;
- run the existing analyzer without changing its source-discovery semantics;
- record available input URL/ref/path/digest information without credentials;
- calculate proposed IntentSource analysis-status changes;
- calculate DesiredService create/update/unchanged actions;
- calculate DesiredDependency create/update/delete/unchanged actions only within a successfully
  and completely analyzed service scope;
- list operator-owned fields that are deliberately preserved;
- treat malformed dependencies, duplicate natural keys, ambiguous rows, credential-bearing input,
  and model-validation failures as errors;
- perform no ORM mutation; and
- emit its artifact even when the plan is blocked.

Do not infer deletion of a DesiredService because it was absent from one analysis. Phase 1 does not
introduce service retirement or deletion semantics. Dependency deletion remains permitted only
because Analyze already owns the complete dependency set for a successfully analyzed service; if
the source result is incomplete or erroneous, do not plan dependency deletions for that scope.

### 6.3 Analyze ownership and apply

Analyze owns:

- `IntentSource.last_import_status`, `last_imported_at`, and `last_import_summary`;
- source/catalog-derived DesiredService fields returned by
  `desired_service_update_fields()`;
- `DesiredService.analysis_provenance` and `last_analyzed_at`; and
- DesiredDependency creation plus source-owned `raw_ref` and `dependency_type`, and removal of a
  dependency key absent from a successful complete analysis of that service.

Analyze must preserve:

- existing DesiredService `name`, `slug`, `display_name`, `lifecycle`, `requirements`, and `notes`;
- DesiredDependency `resolution_status`, `resolved_service`, and `notes` for retained keys;
- all placements and operational overrides; and
- every field outside the explicit analysis-owned set.

For a newly analyzed service, retain the current create contract: deterministic identity and
display defaults, lifecycle `proposed`, empty requirements, source-derived metadata, provenance,
and dependencies. For an existing service, never reset operator fields to create defaults.

`apply=true` must:

1. finish all remote reads and construct the complete read-only plan before the first DB write;
2. refuse mutation when any ownership conflict or validation error exists;
3. use a deterministic, documented transaction scope;
4. lock matching IntentSource, DesiredService, and DesiredDependency rows;
5. revalidate plan preconditions;
6. apply only analysis-owned fields and dependency actions;
7. roll back the transaction scope on any persistence failure;
8. refetch and confirm the owned fields after commit; and
9. preserve a truthful result when later artifact creation fails.

Use one atomic transaction for the selected Job scope unless a real Nautobot limitation discovered
in the disposable proof requires per-IntentSource transactions. Such a change affects partial
failure semantics and therefore requires an explicit plan/report amendment before implementation,
not an undocumented fallback.

To prove repeat idempotence, replay Analyze with identical fetched bytes. A live network ref that
changes between runs is not valid repeat evidence; use a local deterministic HTTP fixture or a
pinned source fixture in the disposable test.

### 6.4 Analyze artifact

Preview and apply use one filename and one schema:

```text
filename: intent-analysis-result.json
schema_version: nintent.intent-analysis.v1
```

The top-level shape is:

```text
schema_version
mode                         # preview | apply
selected_sources
inputs
objects
  - model
    identity
    action                   # create | update | delete | unchanged | conflict
    changed_fields
    preserved_fields
conflicts
errors
totals_by_model_and_action
writes
  requested
  attempted
  committed
transaction
  status
  error
confirmation
  status
  mismatches
```

The same determinism, redaction, truthful write-state, stable-identity, preview/apply parity, and
bounded-log requirements as the Import artifact apply here. A dependency `delete` action must name
the owning service and complete dependency natural key.

## 7. Nauto ownership contraction

### 7.1 Seed Home Cluster

`SeedHomeCluster` remains responsible only for native Nautobot prerequisites used by actual-ledger
ingest. Remove:

- imports of `IntentSource` and `DesiredService`;
- the optional ImportError fallback for those nintent models;
- `ensure_intent_sources()`;
- `ensure_desired_services()`;
- their calls from `run()`; and
- the `intent_sources` and `desired_services` blocks from `seed/home_cluster.yaml`.

Do not replace those calls with an nintent Job invocation. The operator runs the canonical nintent
Import Job separately after reviewing its artifact.

Add a focused contract test proving that Seed Home Cluster does not import, reference, or mutate
nintent desired models and that `home_cluster.yaml` contains no nintent desired roots. Retain tests
and behavior for Location, Role, Status, Cluster Type, manufacturer, Device Type, Tag, and Custom
Field prerequisites.

### 7.2 Generate Desired Services

Delete:

- `nauto/jobs/generate_desired_services.py`;
- its import, registration, and `__all__` entry in `nauto/jobs/__init__.py`;
- `nauto/tests/test_generate_desired_services.py`;
- `nauto/seed/service_repositories.yaml`;
- current documentation for `service_repositories.yaml`,
  `desired_services.generated.yaml`, and `Generate Desired Services`; and
- any ignored generated-output rule that exists only for this deleted Job.

After deletion, the registered Home Inventory Jobs are:

```text
Seed Home Cluster
Ingest Nodeutils Inventory
AI Resource Review
```

Do not alter `AI Resource Review` while editing the shared registration module. Source-derived
desired-service analysis belongs only to nintent's retained Analyze Job.

## 8. Implementation procedure

### Step 0 — Recapture the boundary and establish evidence

1. Create `.local/interface-contract/p1/<timestamp>/` with directory mode `0700` and evidence files
   mode `0600`.
2. Record timestamp, timezone, tool versions, exact documents reviewed, repository revisions,
   submodule pointers, branches, dirty/staged/untracked state, and current test counts.
3. Re-run the parent roadmap's required searches and classify every active Phase 1 occurrence.
4. Record current canonical/home-cluster YAML counts and SHA-256 digests.
5. Use the canonical desired GraphQL query or a read-only in-container ORM query to recapture all
   YAML-owned fields for the Phase 0-confirmed rows. Do not record prose or secrets.
6. Confirm that live structural identities/counts still match the Phase 0 disposition. A changed
   identity or ownership-relevant field does not authorize a new proposal; stop and request a
   disposition update.
7. Confirm no Import/Analyze/Seed/Generate Job is pending or running. Do not start one.
8. Confirm the disposable environment design names a new database, network, volume set, and
   compose/project prefix and does not reference the live external Postgres/Redis.

Gate: implementation is tied to one clean or explained revision tuple, the confirmed YAML proposal
still matches read-only live evidence, and no disposable resource can reach the live database.

### Step 1 — Freeze tests for the final YAML and ownership rules

1. Add loader tests for every accepted root and an otherwise-valid document with an unknown root.
2. Retain focused tests for both obsolete aliases and strict unknown per-entry fields.
3. Add canonical-file tests for the exact identity set/counts in Section 4.2.
4. Add tests proving no realized-link/source field is accepted from YAML.
5. Add endpoint tests proving omitted DNS/mDNS fields remain omitted and explicit names survive
   normalization unchanged.
6. Add planner tests for create/update/unchanged/conflict, missing references, duplicate existing
   rows, deterministic ordering, and omission-as-no-op.
7. Add ownership tests proving an existing DesiredNode lifecycle survives a differing YAML value.
8. Add ownership tests for every realized Device/IP/Cluster/VM link and source.
9. Add DesiredService tests proving Analyze fields survive Import and operator fields survive
   Analyze.
10. Add preview tests that fail if any model save/update/delete method is called.
11. Make the new tests fail against the current implementation for the intended reasons.

Gate: tests describe the retained contract rather than the old mutation-first implementation.

### Step 2 — Build the canonical YAML proposal

1. Move Infrastructure and its five services from `home_cluster.yaml` to
   `intent_sources.yaml`.
2. Add Manual and dnsmasq from the confirmed live structural fields.
3. replace the nine stale checked-in nodes with the five confirmed nodes;
4. replace the old endpoint set with the five confirmed DNS/static-IP endpoints;
5. add the three confirmed IP ranges;
6. remove all six stale service placements and add only dnsmasq-on-agdnsmasq;
7. remove all six stale operational overrides and declare the root as `[]`;
8. declare both compute roots as `[]`; and
9. run the production loader and canonical identity/count assertions.

Gate: the proposal is strict, contains exactly the confirmed Phase 0 identity set, contains no
realized IDs or source fields, and has no stale-node reference.

### Step 3 — Make top-level YAML validation closed

1. Define one canonical immutable root-name set in `loaders.py`.
2. Compare the parsed mapping keys with that set before normalizing any section.
3. Preserve the clearer obsolete-alias errors for the two explicitly rejected historical roots.
4. Return deterministic errors for all other unknown roots.
5. Keep missing known roots as empty no-op sections.
6. Keep current entry-level field, choice, duplicate, reference, and normalization validation.
7. Ensure Import refuses all planning/apply when loader errors exist.

Gate: exactly the nine roots are accepted, aliases and arbitrary unknown roots fail closed, and no
error path writes.

### Step 4 — Refactor Import into read-only plan and atomic apply

1. Extract explicit identity, create-owned, update-owned, and preserved-field metadata.
2. Implement the deterministic read-only planner.
3. Implement ownership conflict detection and cross-root planned-reference resolution.
4. Remove all omission-driven IntentSource disabling and delete `disable_missing`.
5. Make existing DesiredNode lifecycle create-only.
6. Ensure no realized link/source enters defaults for create or update.
7. Implement `apply=false` and delete the old `preview` variable.
8. Implement locked precondition checks and one atomic applier.
9. Add post-commit ORM confirmation.
10. Implement `nintent.intent-import.v1` and the single artifact filename.
11. Preserve bounded truthful Job logging for blocked, rolled-back, committed, and confirmation
    failure states.
12. Remove or rename mutation-first helpers only after every retained caller has moved.

Gate: preview invokes no mutation method, apply is all-or-nothing, ownership conflicts stop before
mutation, and preview/apply plans are structurally identical for the same state.

### Step 5 — Refactor Analyze into read-only plan and explicit apply

1. Add `apply=false`.
2. Extract a pure ORM-diff plan for IntentSource, DesiredService, and DesiredDependency.
3. Preserve the existing analyzer's source fetch/parse behavior.
4. Encode the exact analysis-owned and preserved field sets.
5. Reject malformed or ambiguous plans before writes.
6. Guard dependency deletion behind a successful complete service analysis.
7. Implement the atomic locked apply and post-commit confirmation.
8. Implement `nintent.intent-analysis.v1` and the single artifact filename.
9. Delete `PreviewIntentSourceAnalysis` and remove it from `jobs`.
10. Add a test proving Analyze preview contains the former Preview Job's unique read-only
    information without logging the full desired-service payload.
11. Prove repeat idempotence using identical fetched fixture bytes.

Gate: one Analyze Job covers preview/apply, preview writes nothing, apply touches only owned fields,
and no old Preview Job registration or alias remains.

### Step 6 — Remove nauto's duplicate writers

1. Remove nintent imports, calls, and helper methods from `SeedHomeCluster`.
2. Remove the matching roots from `home_cluster.yaml`.
3. Add the focused Seed Home Cluster ownership test.
4. Delete `GenerateDesiredServices`, its test, and `service_repositories.yaml`.
5. Contract `nauto/jobs/__init__.py` to the three retained Jobs.
6. Remove current documentation and generated-output references.
7. Run syntax and nauto unit tests.

Gate: nauto contains no code that creates or updates an nintent desired model and no candidate
generator/input/output contract.

### Step 7 — Local and static verification

Run at minimum:

```bash
cd nintent
python3 -m unittest discover -s nautobot_intent_catalog/tests

cd ../nauto
python3 -m unittest discover -s tests
python3 -m py_compile jobs/*.py

cd ..
git diff --check
git -C nintent diff --check
git -C nauto diff --check
```

Also:

1. load the canonical YAML through the exact production loader;
2. assert all nine roots, target identities, references, and counts;
3. run the required searches with active/historical classifications;
4. verify `nauto/jobs/__init__.py` exposes only the three retained Jobs;
5. verify no model file or migration changed; and
6. verify `nctl`, `nodeutils`, and `ansible_agdev` worktrees and pointers remain unchanged.

Gate: all local tests pass and the diff is limited to Phase 1 scope.

### Step 8 — Disposable Nautobot preview/apply/repeat proof

Create an isolated Nautobot 3.1.3 environment with:

- a new temporary compose/project name;
- a new PostgreSQL container/database and volume;
- a new Redis container and volume;
- no bind or network reference to the live Postgres, Redis, Nautobot media, or port 8000;
- the exact local nintent source under test, not the GitHub-installed live package; and
- the coordinated local nauto Job source under test.

In that environment:

1. initialize Nautobot and apply migrations through `0016`;
2. prove `makemigrations nautobot_intent_catalog --check --dry-run` reports no changes;
3. verify discovered nintent Jobs are Import, Analyze, and IPAM only;
4. verify discovered nauto Jobs are Seed, Ingest, and AI Resource Review only;
5. create a fixture containing existing operational lifecycle and realized-link fields;
6. record aggregate before-state and ObjectChange counts;
7. run Import with default variables and prove `mode=preview`, exact expected plan, and zero writes;
8. run Import `apply=true` and prove one atomic commit plus preserved operational fields;
9. run Import `apply=true` again and prove all target rows are unchanged;
10. inject a late validation failure and prove the whole Import transaction rolls back;
11. inject an ownership conflict and prove apply never attempts a write;
12. serve deterministic analysis fixture bytes from a disposable local endpoint;
13. run Analyze with default variables and prove exact preview plus zero writes;
14. run Analyze `apply=true` and prove source-owned changes plus preserved operator fields;
15. run Analyze again against identical bytes and prove no repeated changes;
16. inject malformed dependency/source input and prove blocked zero-write behavior;
17. inspect both FileProxy artifacts for schema, deterministic ordering, stable identities,
    redaction, truthful transaction state, and preview/apply shape parity; and
18. remove only the explicitly named disposable containers, networks, volumes, and temporary
    files after capturing sanitized evidence.

Do not use a rollback-only unit test as the preview proof. Do not point this test at the current
development database for convenience.

Gate: real Jobs prove preview/apply/repeat and failure atomicity on an isolated real ORM/database.

### Step 9 — Documentation, searches, coordinated commits, and report

1. Update nintent current docs for strict roots, Import/Analyze variables, default preview,
   artifacts, ownership, and removed Preview Job.
2. Update nauto current docs so Seed Home Cluster is native-prerequisite-only and source analysis
   points to nintent Analyze.
3. Remove current documentation for Generate Desired Services and its files.
4. Recheck the VM Phase 3 plan. Edit only if a discovered fact changes the existing supersession
   note; do not duplicate or rewrite it otherwise.
5. Re-run every required search and classify allowed historical matches.
6. Record before/after Job names, files, tests, seed identities, root counts, artifact schemas,
   and verification results.
7. Commit nintent and nauto independently, then update their superproject pointers. Do not push.
8. Write `devdocs/big/interface_contract/p1/report.md` with status `complete`, `implemented, not
   deployed`, `partially complete`, or `blocked` according to the actual evidence.

The normal successful Phase 1 status is **implemented, not deployed**: local/disposable proof is
complete, but the live YAML apply and matched deployment intentionally remain Phase 4 work. Use
`complete` only to mean the Phase 1 scope itself is fully complete, while stating explicitly that
the overall roadmap is not deployed.

## 9. Required verification and searches

### 9.1 Verification matrix

| Area | Required positive proof |
|---|---|
| Canonical YAML | exactly nine declared roots and the exact Phase 0-confirmed identity set |
| Unknown roots | arbitrary unknown and both obsolete aliases fail before planning |
| Omission | missing root/row causes no disable, delete, retire, unlink, or update |
| Import default | `apply=false`, exact artifact, no mutation method invoked |
| Import ownership | existing node lifecycle and every realized link/source survive |
| Import conflict | conflicting preserved field blocks before write |
| Import apply | one transaction, exact plan applied, ORM confirmation succeeds |
| Import rollback | late failure leaves every row at the before-state |
| Import repeat | second apply reports only unchanged objects |
| Analyze default | `apply=false`, former preview behavior covered, zero writes |
| Analyze ownership | source fields change; operator service/dependency fields survive |
| Analyze errors | malformed/incomplete scope cannot trigger dependency deletion or any apply |
| Analyze repeat | identical fetched bytes produce no repeated DB changes |
| Artifacts | one versioned shape per Job, deterministic and truthful in every mode |
| Seed Home Cluster | no import/reference/write of nintent desired models |
| Generate Job | module, registration, test, seed, output contract, and current docs absent |
| Job discovery | nintent 3 retained Jobs; nauto 3 retained Jobs |
| Schema | migrations remain through `0016`; dry-run makemigrations is clean |
| Isolation | disposable proof uses no live DB/Redis/media/container/port |
| Secrets/prose | no token, credential, Braindump body, or review summary in artifacts/reports |

### 9.2 Required searches

Search active code, tests, seed/configuration, and current documentation for at least:

```text
PreviewIntentSourceAnalysis
Preview Intent Source Analysis
GenerateDesiredServices
Generate Desired Services
generate_desired_services
service_repositories
service_repositories.yaml
desired_services.generated.yaml
disable_missing
intent-import-preview.json
intent-import-apply.json
preview = BooleanVar
ensure_intent_sources
ensure_desired_services
IntentSource
DesiredService
transaction.set_rollback
create_file
last_import_status
last_analyzed_at
dependencies_deleted
desired_node_operational_configs
```

For `IntentSource` and `DesiredService`, scope the nauto result separately: neither model may
remain imported or mutated by nauto, while both correctly remain in nintent.

Every remaining `transaction.set_rollback` must be classified. Rollback may remain in unrelated
IPAM or test code, but Import/Analyze preview must not depend on it. Every remaining `create_file`
must have a named retained artifact contract.

Expected references to deleted Job/file names are limited to:

- the parent roadmap, refactoring vision, and this plan;
- Phase 0 and Phase 1 historical reports explaining the transition;
- normal Git history outside the active tree; and
- a final current documentation sentence only if needed to direct an operator away from a stale
  deployed revision before Phase 4. Do not retain runtime aliases to support that sentence.

## 10. Failure handling and rollback

### 10.1 Before any disposable apply

If loader, planner, test, ownership, or artifact behavior is wrong:

- do not run the disposable apply;
- fix the implementation and regenerate the preview;
- leave live services and data untouched; and
- report the exact failing gate if work stops.

### 10.2 Disposable-environment failure

If an isolated apply fails:

1. preserve sanitized logs/artifacts and the before/after aggregate comparison;
2. verify the transaction result instead of assuming rollback;
3. correct the code and recreate the disposable database from a known empty state;
4. rerun preview/apply/repeat from the start; and
5. remove only the explicitly named disposable resources after evidence capture.

Never compensate for a disposable failure by editing the live database.

### 10.3 Source rollback

No live rollback is needed because Phase 1 does not deploy or apply live. Before Phase 4, source
rollback consists of restoring the coordinated prior nintent/nauto commits and superproject
pointers. Do not roll back by restoring duplicate Jobs, legacy variables, or two desired writers
inside the new revisions.

If the canonical YAML proposal is found to conflict with a changed live intent, stop. Do not
silently restore stale seed rows, overwrite the live row, or reinterpret omission as deletion.
Obtain a new explicit disposition and amend the plan/report.

## 11. Definition of done

Phase 1 is complete in its implementation scope only when:

- `nauto/seed/intent_sources.yaml` is the sole checked-in bulk desired document;
- it declares all nine roots and exactly the confirmed five-node/three-range/six-service/one-
  placement identity set;
- `home_cluster.yaml` contains no nintent desired roots;
- unknown roots and obsolete aliases fail closed;
- omission never disables, deletes, retires, or unlinks;
- Import exposes only `source_file` and `apply=false`;
- Import preview executes no database mutation;
- Import ownership preserves existing lifecycle, realized links, analysis fields, and other
  non-YAML-owned values;
- Import apply is atomic, confirmed, and repeat-idempotent;
- Analyze exposes `fetch_timeout`, `include_disabled`, and `apply=false`;
- Analyze preview executes no database mutation;
- Analyze apply touches only analysis-owned fields, protects incomplete dependency scopes, and is
  repeat-idempotent for identical inputs;
- both Jobs emit their exact versioned artifact in preview, blocked, rollback, and success paths;
- Preview Intent Source Analysis is absent with no alias;
- Seed Home Cluster no longer imports or writes nintent models;
- Generate Desired Services, its registration/test/seed/output/current docs are absent;
- IPAM, Ingest, AI Resource Review, GraphQL, REST, UI, nctl, migrations, and live state are
  unchanged;
- local tests, strict searches, migration check, and disposable real-Job preview/apply/repeat
  proofs pass;
- the final report contains no secrets or private prose and distinguishes the Phase 1 feature from
  unrelated cluster drift; and
- no live deployment, Job run, or desired-state mutation occurred.

The strongest completion evidence is not a smaller file or Job count. It is a deterministic
preview that makes no writes, an explicitly authorized atomic apply of the same contract, and a
repeat run that truthfully reports no remaining change while preserving every field owned by
another operation.
