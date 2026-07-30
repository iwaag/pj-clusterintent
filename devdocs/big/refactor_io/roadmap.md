p5# Desired-State I/O Refactor — Development Roadmap

## Purpose

Move private, cluster-specific desired state out of Git and make the nintent database the
authoritative current state.

The target flow is:

```text
local YAML or JSON
  -> one desired-state batch REST endpoint
  -> validation and plan
  -> one database transaction
  -> existing nintent models
  -> GraphQL reads
  -> nctl drift and reconcile
```

Git continues to define the system's framework, schemas, policies, code, and synthetic fixtures.
It does not contain the real cluster's hosts, addresses, MAC addresses, VM identifiers, service
placements, or operational overrides.

Each phase below will receive a separate implementation plan when it starts. This roadmap fixes
the direction and exit criteria without prescribing internal class or module structure.

## Working principles

- **Current state only.** Persist only data needed by a current reader, validator, reconciler, or
  actuator. Do not add raw request storage, import revisions, rollback snapshots, approval
  records, Git provenance, or speculative metadata.
- **One desired-state writer.** Provide one batch REST mutation endpoint. A one-object change is a
  batch containing one operation. Do not retain parallel per-model desired-state write APIs or a
  database-writing import Job.
- **Explicit operations.** The batch contract supports explicit create/update/upsert/delete or an
  equivalent small vocabulary selected in Phase 0. Omission from a partial request does not imply
  deletion.
- **Atomic apply.** Validate the whole batch before writing and commit it in one transaction.
  Partial success is not useful for this control-plane input.
- **Read paths remain stable where practical.** nctl continues to read normalized desired state
  through GraphQL. The existing nintent models remain the default storage shape unless the field
  audit proves that a model or field has no current consumer.
- **Private data stays local.** Operator input may live in an ignored `.local/` file, standard
  input, or another private location. The server consumes it but does not preserve the submitted
  document.
- **Experimental environment.** Breaking schema and API changes are acceptable. The local
  Nautobot/PostgreSQL stack may be migrated, reset, or reseeded. Prefer simple coordinated
  cutovers over compatibility layers.

## Minimum constraints

These are the only initiative-wide prohibitions:

1. Do not commit real cluster desired state or credentials to Git.
2. Do not leave two supported desired-state mutation paths after cutover.
3. Do not apply only part of an accepted batch.
4. Do not add persistent data without naming its current consumer.

Use Nautobot's existing authentication, permissions, validation conventions, and change logging.
This roadmap does not require a new RBAC design, signatures, approval workflow, immutable audit
log, encrypted payload archive, revision store, or production-grade disaster recovery.

## Scope boundary

The single-writer rule applies to structured desired state:

- intent sources;
- desired nodes and endpoints;
- desired IP ranges;
- desired compute platforms and instances;
- desired services and placements; and
- desired node operational overrides.

Desired lifecycle changes and desired-to-actual realization links currently written by nctl are
part of the same batch API contract.

Braindumps, Alignment Reviews, actual-state ingest, IPAM ledger reconciliation, and operation
evidence are separate domains. Their existing write paths are not removed merely to make every
plugin mutation look alike.

## Phases

| Phase | Goal |
|---|---|
| 0 | Freeze the minimal persistence and batch contracts |
| 1 | Build one reusable batch planning and apply service |
| 2 | Expose the canonical REST endpoint |
| 3 | Move every desired-state writer to the batch endpoint |
| 4 | Remove private desired state and file-based ownership from Git |
| 5 | Verify the cutover and simplify documentation |

### Phase 0 — Freeze the minimal contracts

**Goal:** make the later implementation mechanical rather than reopening ownership decisions.

- Inventory every persisted desired-state field and its current readers and writers.
- Classify each field as required current intent, required realization link, derived value, or
  unused. Assign unused fields to removal; do not invent replacement metadata.
- Define the smallest batch operation vocabulary, identity keys, reference rules, deletion
  semantics, dry-run/apply switch, and response shape.
- Decide how YAML and JSON map to the same request contract.
- List every current desired-state writer, including the Import Intent Sources Job, nctl lifecycle
  and linking calls, UI/form mutations if any, tests, and maintenance scripts.
- Record the coordinated nintent/nctl deployment order and the disposable-data migration choice.

**Exit criteria:** one field table, one wire-contract sketch, one writer inventory, and an explicit
cutover order are ready for the Phase 1 plan.

### Phase 1 — Reusable batch planning and apply service

**Goal:** separate desired-state mutation logic from server-side file paths and Jobs.

- Refactor the existing strict loader, planner, reference resolution, validation, and confirmation
  logic so it accepts an in-memory request document.
- Plan all operations without writes and return deterministic create/update/delete/unchanged/
  conflict results.
- Apply an accepted plan in one transaction and report the committed result truthfully.
- Preserve only current model-owned fields that are outside the requested operation.
- Implement explicit deletion with dependency-aware ordering or clear conflicts.
- Remove fields or models assigned to removal by Phase 0, using ordinary Django migrations.
- Keep the service independent enough to test without HTTP.

**Exit criteria:** focused tests prove dry-run performs no writes, apply is atomic, references work
within one batch, explicit deletion works, and invalid input leaves current state unchanged.

### Phase 2 — Canonical batch REST endpoint

**Goal:** make the reusable service remotely usable through one mutation surface.

- Add one nintent REST endpoint for desired-state batches.
- Accept YAML and/or JSON using the single Phase 0 contract; do not create a second semantic
  contract for the other encoding.
- Use one request flag or mode for dry-run versus apply rather than separate mutation APIs.
- Return the Phase 1 plan/result with ordinary HTTP validation and conflict responses.
- Use existing Nautobot token authentication and permissions.
- Set a practical request-size bound only if the framework does not already provide one.
- Do not save the raw request body after processing.

**Exit criteria:** an authenticated caller can preview and atomically apply a mixed-kind batch, and
GraphQL immediately returns the resulting normalized current state.

### Phase 3 — Cut all desired-state writers over

**Goal:** leave the batch endpoint as the only supported desired-state writer.

- Change nctl lifecycle and realization-link writes to submit one-operation or multi-operation
  batches through the canonical endpoint.
- Move any remaining assisted desired-state workflow to the same endpoint.
- Remove desired-state PATCH/POST/DELETE routes from per-model REST viewsets.
- Remove or make read-only the Import Intent Sources Job and any UI/form path that writes the same
  models. Prefer deletion when the surface has no remaining purpose.
- Remove direct ORM writes from tests or utilities when they claim to exercise an operator or nctl
  workflow; fixture setup may still use the ORM.
- Delete superseded serializers, settings, compatibility adapters, and documentation in the same
  coordinated rollout.

**Exit criteria:** repository search and runtime tests find one supported desired-state mutation
surface, while nctl lifecycle, linking, drift, and reconcile still complete their current paths.

### Phase 4 — Remove private desired state from Git

**Goal:** separate reusable framework configuration from cluster instance data.

- Apply the current cluster state to the database through the canonical endpoint.
- Remove `nauto/seed/intent_sources.yaml` and the nintent setting/environment fallback that points
  to it.
- Remove real cluster desired data from tests, examples, docs, and generated artifacts.
- Keep a synthetic example only if it has a concrete documentation or test consumer.
- Keep `nauto/seed/home_cluster.yaml` for reusable Nautobot prerequisites and
  `nauto/seed/nodeutils_ingest.yaml` for ingest policy.
- Document a minimal operator command using an ignored local file or standard input. A thin nctl
  client is allowed if it only calls the canonical endpoint and stores no second copy of state.
- Confirm the repository and its history going forward contain no credentials or newly introduced
  private cluster payloads. Historical rewriting is outside this roadmap.

**Exit criteria:** a fresh code checkout contains no real cluster desired state, while the scratch
database retains a usable current desired state and can be updated without a Git commit.

### Phase 5 — End-to-end verification and simplification

**Goal:** prove the new ownership boundary and remove temporary work.

- Exercise dry-run, mixed create/update/delete apply, invalid atomic rollback, one-object batch,
  nctl lifecycle/linking, GraphQL reads, drift, and one bounded reconcile path.
- Re-run the applicable ordinary nintent, nctl, nauto, and Nautobot runtime suites from
  `README_DEV.md`.
- Verify that restarting or rebuilding Nautobot does not require a private seed file.
- Update the root, nintent, nauto, nctl, and local-environment documentation to state:
  database=current desired state, batch REST=only desired writer, GraphQL=desired reader,
  Git=framework and policy.
- Remove temporary migration helpers, duplicated fixtures, and obsolete file-path configuration.

**Exit criteria:** the normal workflow is documented and tested, no supported path depends on
`intent_sources.yaml`, and no redundant writer or custom historical-storage mechanism remains.

## Completion condition

This initiative is complete when private cluster intent is absent from Git, the database contains
only the normalized current state needed by active consumers, all structured desired-state
mutations use one atomic batch REST endpoint, and existing nctl read/reconcile behavior works
against that state.
