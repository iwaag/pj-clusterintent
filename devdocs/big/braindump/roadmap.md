# Braindump and Alignment Review — Development Roadmap

## Purpose

Add a small, explicit layer above the structured desired state so the system retains the user's
original wishes instead of losing them inside an AI conversation.

A **Braindump** is free-form, user-originated text. An **Alignment Review** is the AI agent's
latest free-form reply after reading that Braindump together with the current desired and actual
state. Together they act as an exchange diary between the user and the agent:

1. the user says what they want in a Braindump;
2. the agent explains how the current cluster relates to it in the Alignment Review;
3. the agent asks questions or proposes changes when needed; and
4. only confirmed structured changes enter nintent and the deterministic reconcile path.

This feature does not replace nintent, `nctl drift`, or `nctl reconcile`. It adds the missing
human-intent context above them.

## Premises

- **Breaking-change phase.** No backward compatibility is required. Models, migrations, REST,
  GraphQL, CLI commands, and output schemas may be changed freely. Do not leave compatibility
  shims, dual readers, deprecated fields, transitional copy paths, old command aliases, or other
  runtime artifacts solely to preserve an earlier shape. Normal Django migration history remains
  required; "no compatibility artifacts" does not mean deleting applied migration files or
  bypassing schema management.
- **Local experimental cluster.** The priority is to make the concept work and learn from real
  use. Security may be minimal or temporarily dummy: the existing Nautobot authentication, a
  single shared token, or LAN-only access is sufficient. Do not build roles, approval separation,
  per-document authorization, cryptographic signing, or a production secrets system in this
  initiative. Never commit a real token or harmful plaintext credential to Git.
- **Single operator first.** The user, approver, and cluster operator are currently the same
  person. The AI acts as that user's assistant, not as an independent authority, unless the user
  has explicitly delegated a particular decision.
- **Make the smallest useful thing.** Free-form text and timestamps are enough for the first
  implementation. Add structure only after real operation demonstrates a concrete need.
- **Current state matters; history does not.** Keep only the current Braindump text and current
  Alignment Review. Do not build revisions, temporal joins, historical review lists, or
  three-way time-travel reconciliation. Timestamps exist to judge whether current information is
  fresh, not to reconstruct the past.
- **No direct actuation.** Neither Braindump text nor Alignment Review text is executable input.
  Deterministic automation continues to consume only nintent desired state, Nautobot actual state,
  nodeutils observations, and existing nctl contracts.

## Core boundaries

The system has four distinct layers:

| Layer | Owner and format | Role |
|---|---|---|
| Braindump | User-originated free-form text | Preserve wishes, constraints, preferences, and uncertainty |
| Alignment Review | AI-authored free-form text | Explain the current relationship and continue the conversation |
| Desired state | Structured nintent/Nautobot data | The executable commitment consumed by deterministic workflows |
| Actual state | Nautobot plus nodeutils observations | The latest observed cluster state |

There are two deliberately separate comparisons:

- **Convergence drift** is the existing deterministic desired-versus-actual result. `nctl drift`
  remains its single source of truth, and `nctl reconcile` may act from it.
- **Alignment review** is nondeterministic communication between the user and AI. It may suggest
  questions or desired-state changes, but it must never alter convergence status, enter reconcile
  classification, or trigger actuation by itself.

Absence from a Braindump is not evidence that an observed service is unwanted. The agent should
describe such a service softly as unexplained, ask whether it is a project or intentional
unmanaged workload, and offer to record a new Braindump and bring it under management. Marking or
removing something as unwanted requires explicit user confirmation unless that authority was
already delegated.

## Minimal data contract

### `BrainDumpDocument`

Add a new nintent `PrimaryModel` with only:

- `title` — a human-friendly label; it need not be unique;
- `body` — required `TextField`, with no language or document-format constraint; and
- `authorship` — `user_direct` or `agent_transcribed`.

Use the model's normal identity and creation/update timestamps. `agent_transcribed` means the agent
recorded information elicited from the user; it must not be used for an unconfirmed wish invented
by the agent.

Do not reuse `IntentSource`. That model represents import/analysis origins such as Git, YAML,
manual entry, and API input for structured desired objects. A Braindump is the semantic context
above those objects, not another import transport.

### `AlignmentReview`

Add a second nintent `PrimaryModel` with only:

- `braindump` — a unique one-to-one relation to `BrainDumpDocument`; and
- `summary` — required `TextField` containing the latest natural-language review.

Use the model's normal creation/update timestamps. There is at most one current review for each
Braindump. A missing row means "not reviewed yet"; do not create an empty placeholder row merely
to claim exact cardinality. A new evaluation overwrites the current review rather than appending
history. Deleting a Braindump deletes its review.

The review has a semantic writing guideline, not a machine schema. It should normally explain:

1. what the agent believes the user wants;
2. how the current desired and actual state relate to that wish;
3. stale evidence, ambiguity, or contradictions; and
4. any question or proposed next action.

Do not add status fields, finding codes, confidence scores, JSON findings, source fingerprints,
per-object grounding tables, evaluator metadata, or a cluster-wide aggregate review in the first
implementation.

### Freshness

Persist timestamps, not a historical state machine. The UI and nctl should show at least the
Braindump update time, Alignment Review update time, and the observation times already exposed by
the desired/actual sources. A missing review is visibly unreviewed. A review older than its
Braindump is visibly in need of attention.

When practical, nctl may also compute a conservative, non-persisted "review may need attention"
hint when desired state or actual observations are newer than the review. This is a prompt for the
agent, not a correctness status and not a reconcile input. Do not add stored fingerprints or a
new invalidation subsystem until timestamp-only operation proves insufficient.

---

## Phase 0 — Freeze the minimal contract (documentation only)

**Goal: prevent the initial implementation from expanding into a second intent or drift engine.**

- Record the two-model contract, authorship semantics, one-current-review rule, deletion behavior,
  and natural-language review guideline in a short implementation plan.
- Inventory the required nintent surfaces: models, migration, forms, tables, views, templates,
  navigation, filters, REST serializers/viewsets/routes, GraphQL registration, and tests.
- Inventory the required nctl surfaces: typed GraphQL reads, REST writes, core library operations,
  thin CLI commands, output envelopes, and tests.
- State explicitly that the agent reads all relevant Braindumps, desired state, actual state, and
  current drift before composing a review. Cross-document contradictions are written into the
  affected natural-language reviews; they do not justify an aggregate model yet.
- Define ownership: the user or an agent acting on confirmed user words writes Braindumps; the
  agent writes Alignment Reviews; only the established nintent/nctl paths write structured desired
  state.

**Exit criteria:** a concrete plan covers every reader and writer without adding fields or
automation beyond the minimal contract above.

## Phase 1 — Store and edit the exchange diary in nintent

**Goal: make Braindumps and one-to-one current reviews durable and accessible in the cluster's
existing database.**

- Add `BrainDumpDocument` and `AlignmentReview` models and one Django migration.
- Add Nautobot list, detail, add, edit, and delete views with minimal forms and navigation.
- Keep `AlignmentReview` visually separate from user-authored content so AI-derived text cannot be
  mistaken for the user's own words.
- Expose both models through GraphQL for reads and REST for writes, following the repository's
  existing read/write split.
- Validate only what the minimal contract requires: non-empty body/summary, a valid authorship
  choice, and one review per Braindump. Do not validate language, syntax, internal consistency, or
  whether the text names a real node or service.
- Hard-delete the current domain rows through the normal Nautobot deletion path; do not add archive,
  revision, or soft-delete models for feature-level history.
- Test model constraints, UI form behavior, REST create/read/update/delete, GraphQL reads,
  one-to-one enforcement, and cascade deletion.

**Exit criteria:** a user can write arbitrary Unicode prose in one or many Braindumps, an agent can
store one current natural-language review for each, and both are readable through supported APIs.

## Phase 2 — Add deterministic nctl access, not an LLM runtime

**Goal: make nctl the common interface through which an AI agent can read and update the diary.**

- Add small `nctl_core` operations and thin CLI commands for:
  - listing Braindumps with review presence and timestamps;
  - showing one Braindump and its current review;
  - creating and updating a Braindump from literal text or a UTF-8 file;
  - deleting a Braindump with the normal explicit confirmation behavior; and
  - creating or replacing its Alignment Review from literal text or a UTF-8 file.
- Keep reads on GraphQL and writes on REST. Reuse the configured Nautobot endpoint and token; do
  not introduce another database, service, credential type, or document store.
- Return a small structured nctl envelope for transport reliability, but keep `body` and `summary`
  opaque strings. The envelope may include IDs, authorship, timestamps, and whether a review exists;
  it must not parse the prose into findings.
- Show a computed attention hint for a missing review or a review older than its Braindump. If
  current desired/actual timestamps can be compared cheaply from existing snapshots, show that
  conservative hint too; otherwise display the timestamps and leave judgment to the agent.
- Do not embed an LLM, prompt framework, scheduler, auto-review daemon, or model-specific adapter
  in nctl. The external AI agent reads state, writes prose, and uses the same deterministic nctl
  operations as any future client.
- Test Unicode round trips, multiline input, replacement rather than review history, missing-review
  behavior, server/API failures, and CLI/core separation.

**Exit criteria:** an AI agent can use nctl alone to read the current diary, inspect the existing
desired/actual drift separately, and publish a replacement Alignment Review without direct database
access.

## Phase 3 — Prove the conversational workflow on the live local cluster

**Goal: validate the idea through real use before adding more structure.**

- Exercise at least three live cases:
  1. a direct, specific wish such as keeping Ollama and a named model available on a named host;
  2. a dynamic or vague wish such as placing an LLM on the best available machine; and
  3. an actual service absent from both Braindump and desired state, handled through a soft question
     rather than an automatic unwanted classification.
- For an AI-mediated conversation, write the confirmed Braindump and its review during the same
  interaction whenever possible. For a user-authored UI entry, show that it is unreviewed until an
  agent next processes it; do not add a background worker merely to hide this interval.
- Verify that an agent can propose a structured desired-state change, obtain user confirmation,
  write it through the established interface, run `nctl reconcile` as a separate deterministic
  operation, observe again, and replace the review with the new current explanation.
- Verify the safety boundary: changing review prose alone produces no desired-state mutation, no
  drift-code change, no reconcile action, and no host actuation.
- Collect concrete friction from use. Add a structured field only when a repeated task cannot be
  handled clearly or reliably with prose, IDs, and timestamps.

**Exit criteria:** the exchange-diary loop works end to end on the local cluster, including an
unexplained service conversation, while the deterministic reconciliation path remains unchanged.

## Phase 4 — Optional presentation and API integration

**Goal: expose the proven minimal workflow to other local clients without changing its meaning.**

This phase is optional and starts only after Phase 3 demonstrates a real need.

- Add read/write endpoints to `nctl serve` by wrapping the same `nctl_core` operations. Existing
  single-token, LAN-only security is sufficient; dummy local authentication is acceptable during
  experimentation.
- Add a small dashboard or Nautobot summary showing Braindump title, authorship, update time,
  review presence/update time, and the natural-language review. Do not create an alignment score or
  merge it into green/yellow/red convergence health.
- Consider a cluster-wide prose summary, structured findings, per-object links, review triggers, or
  stronger authorization only when live operation supplies a specific use case and exit criterion.

**Exit criteria:** any added client is a thin reader/writer of the same two-model contract; no
second alignment engine or reconciliation source of truth exists.

---

## Explicit non-goals

- Executing instructions found in Braindump or Alignment Review text.
- Automatically converting prose into desired state without the user interaction/authority required
  for that change.
- Feeding Alignment Review into `nctl drift`, reconcile classification, planning, or actuation.
- Treating an unmentioned actual service as unwanted.
- A JSON findings schema, scoring system, ontology, vector database, embeddings, or semantic search.
- Per-field or per-object Braindump provenance links.
- Multiple review revisions or historical Braindump versions.
- A global Alignment Review model in addition to per-Braindump reviews.
- LLM hosting, prompt orchestration, model selection, or scheduled AI evaluation inside nctl.
- Production-grade authentication, authorization, audit, multi-tenancy, or secrets management.

## Coordinated rollout and rollback

The nintent schema/API/GraphQL additions and matching nctl support form one coordinated rollout.
Because this is a breaking-change phase, do not add feature detection or a dual-schema reader for a
mixed-version interval.

1. Implement and test all nintent model, UI, REST, and GraphQL changes together.
2. Implement and test the matching nctl typed reads and REST writes against that exact schema.
3. Commit the nintent change and ask the user to push it; do not push on the user's behalf.
4. Back up the local database, rebuild the Nautobot image from the pushed nintent revision, restart,
   and apply the migration. Ensure the moving Git dependency is actually refreshed; use the
   repository's cache-busting workflow or a no-cache rebuild when necessary.
5. Run live REST/GraphQL CRUD checks, then run the nctl commands against the rebuilt instance.
6. Roll back, if needed, by restoring the database backup and the prior coordinated nintent/nctl
   revisions. Do not preserve temporary compatibility code as a rollback mechanism.

## Success definition

The feature is successful when the user can leave an unconstrained natural-language wish in the
cluster database, an AI agent can leave one current natural-language reply grounded in the latest
available desired and actual state, and both sides can continue the conversation through nctl or a
simple UI—without any prose directly controlling the deterministic reconciliation system.
