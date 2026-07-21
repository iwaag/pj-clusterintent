# Braindump Phase 0 Implementation Plan: Freeze the Minimal Contract

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: proposed; documentation-only phase.

## Goal

Freeze the smallest useful Braindump and Alignment Review contract before runtime implementation
begins. This phase changes no code, database schema, API, CLI, or live data. Its output is the
authoritative boundary that the Phase 1 nintent implementation and Phase 2 nctl implementation
must follow without independently adding structure.

Phase 0 is complete only when the following are unambiguous:

1. what a Braindump and an Alignment Review mean;
2. who writes each one;
3. their exact minimal fields and cardinality;
4. how unreviewed and potentially outdated content is represented;
5. every nintent and nctl surface later phases must change;
6. what remains outside deterministic drift and reconcile; and
7. which tempting extensions are explicitly deferred until real use justifies them.

## Premises carried from the roadmap

- **Breaking-change phase.** No backward compatibility is required. Later implementation may
  change model, REST, GraphQL, CLI, and output shapes freely. It must not retain deprecated fields,
  dual readers, old aliases, transitional data-copy paths, or other runtime compatibility
  artifacts. Normal Django migrations remain required and stay in migration history.
- **Local experimental cluster.** Working behavior and rapid learning matter more than
  production-grade security. Existing Nautobot authentication, a single shared token, LAN-only
  access, or a temporary dummy mechanism is enough. Do not design roles, approval separation,
  per-document authorization, signing, or a secrets platform. Never commit a real credential.
- **Single operator.** The user remains the authority. The AI is an assistant and may act without
  a new confirmation only within authority the user has explicitly delegated.
- **Minimal first implementation.** Free-form text, identity, authorship, relationships, and
  timestamps are sufficient. New structure requires evidence from live operation.
- **Current state only.** Do not design domain revision history, old reviews, temporal joins,
  archive states, or time-travel reconciliation. Framework change logs and database backups may
  still exist operationally; they are not a Braindump history feature.
- **No direct actuation.** Braindump and review prose is data for a conversation, never an
  executable automation contract.

## Current state (as of 2026-07-21)

- `BrainDumpDocument` and `AlignmentReview` do not exist in nintent or nctl.
- nintent models inherit Nautobot `PrimaryModel` and opt into GraphQL with
  `@extras_features("graphql")` in `nintent/nautobot_intent_catalog/models.py`.
- nintent's UI surface is explicit rather than generated from the model alone: forms, tables,
  views, URL routes, templates, filters, and navigation are maintained separately.
- The intent-catalog REST API currently registers only desired nodes, services, and endpoints.
  Both new models therefore require deliberate serializer, filter, viewset, and router work in
  Phase 1; model creation alone will not provide the required write API.
- nctl's established boundary is GraphQL for Nautobot reads and REST for writes. Phase 2 must
  preserve that split.
- Existing deterministic reconciliation already has its own structured drift model and code
  classification. Alignment Review must not be added to that registry or source snapshot.
- The last documented live baselines are nintent 98 tests and nctl 617 tests in
  `devdocs/big/better_usability/p4/report4.8.md`. Phase 0 changes documentation only and must not
  alter either runtime baseline.
- nintent reaches the local Nautobot image through a Git-based install. Runtime rollout therefore
  requires commit, user push, rebuild, restart, and migration; Phase 1 must batch the nintent
  surface into one coordinated rebuild.

No live Nautobot query is required in Phase 0. If read-only inspection is used to confirm framework
behavior, record only non-secret aggregate evidence and never copy the local API token or private
content into checked-in documentation.

## Authoritative minimal contract

This section is the Phase 0 decision record. Later plans may refine implementation details, but
must not expand this domain shape without updating this plan and stating the live evidence that
requires the expansion.

### 1. `BrainDumpDocument`

`BrainDumpDocument` is current, unconstrained prose that records wishes, constraints, preferences,
questions, and uncertainty originating from the user.

App-declared fields:

| Field | Contract |
|---|---|
| `title` | Required human-readable label, maximum 255 characters, not unique |
| `body` | Required unbounded `TextField`; arbitrary Unicode and multiline text are preserved |
| `authorship` | Required choice: `user_direct` or `agent_transcribed` |

Framework-owned `PrimaryModel` identity and creation/update timestamps are used as-is. Do not add a
second slug, language, format, status, scope, owner, source URL, revision, archive flag, or
fingerprint in Phase 1.

Authorship semantics are exact:

- `user_direct` means the user directly entered or supplied the prose.
- `agent_transcribed` means the agent wrote down information elicited from the user and confirmed
  as representing that user's wish.
- It must never mean an agent-generated recommendation, assumption, or guessed wish. Those belong
  in the Alignment Review until the user confirms them.

The model field has no silent authorship default at the API/domain boundary. A human-facing form
may initially select `user_direct` for convenience, but every programmatic writer must supply the
choice explicitly so an agent cannot accidentally misattribute its transcription.

Validation is deliberately narrow:

- reject a title or body that is empty or whitespace-only;
- do not rewrite or normalize meaningful body whitespace;
- reject an unknown authorship value; and
- do not validate language, grammar, syntax, contradictions, hostnames, services, or whether the
  wish can be implemented.

### 2. `AlignmentReview`

`AlignmentReview` is the AI agent's latest natural-language reply after considering one Braindump
in the context of all relevant Braindumps, current structured desired state, current actual state,
and current deterministic drift.

App-declared fields:

| Field | Contract |
|---|---|
| `braindump` | Required `OneToOneField` to `BrainDumpDocument`, with cascade deletion |
| `summary` | Required unbounded `TextField` containing the latest free-form review |

Framework-owned identity and creation/update timestamps are used as-is. The summary rejects
empty/whitespace-only input but otherwise remains opaque Unicode text.

Cardinality and lifecycle are exact:

- a Braindump has zero or one current Alignment Review;
- no review row means `unreviewed`;
- do not auto-create an empty review to simulate exact one-to-one presence;
- re-evaluation replaces the existing summary in place;
- do not append revisions or retain previous summaries as domain records; and
- deleting a Braindump deletes its review. Deleting only the review returns the Braindump to the
  unreviewed state.

The review prose should normally answer four questions, but these are agent-writing guidance and
not schema fields:

1. What does the agent believe the user wants?
2. How do the current desired and actual state relate to that wish?
3. What evidence is stale, ambiguous, contradictory, or missing?
4. What should be asked or proposed next?

The review is visually and semantically separate from the Braindump so AI-derived prose cannot be
mistaken for user-originated intent. Phase 1 does not enforce a distinct review-writer permission;
the local experimental system relies on the existing Nautobot access boundary and documented
writer ownership.

### 3. Multiple documents and cross-document interpretation

- Multiple Braindumps are allowed and expected.
- Each has its own current review; Phase 1 does not add a global review row.
- Before writing one review, the agent may read all Braindumps to detect relevant overlap or
  contradiction.
- A cross-document contradiction is explained in the affected natural-language review or reviews.
  It does not create a relationship table or structured conflict finding.
- If repeated use shows that per-document prose is insufficient, a later proposal may add an
  aggregate view. Phase 0 does not reserve a model or API shape for it.

### 4. Freshness and attention

Timestamps support present-time judgment; they do not form a temporal consistency model.

The minimum facts later clients expose are:

- Braindump `last_updated`;
- whether a review exists and, if so, its `last_updated`; and
- desired/actual observation timestamps already available from current sources when the agent
  inspects them.

Only the following coarse attention concepts may be computed; they are not persisted domain
fields:

| Condition | Meaning |
|---|---|
| no review row | unreviewed |
| review older than its Braindump | review needs attention |
| newer desired/actual evidence is cheaply visible | review may need attention |
| none of the above | review exists; this is not a proof of semantic alignment |

Do not call the last condition `aligned`, `converged`, or `valid`. Timestamp order cannot prove
semantic agreement. Phase 2 may expose a conservative attention hint, but Phase 1 stores no
status, invalidation marker, fingerprint, or last-reviewed source snapshot.

### 5. Authority and safety boundary

- User-originated prose can justify a proposal but cannot itself mutate desired state.
- Review prose can propose a change but cannot itself mutate desired state.
- Writing either model must not invoke a Job, playbook, reconcile operation, nodeutils collection,
  drift comparison, or event-driven automation.
- An unmentioned actual service is `unexplained`, not unwanted. The agent asks whether it should be
  brought under management, left unmanaged, or removed.
- Removing or disabling a service requires ordinary user confirmation unless prior delegation
  clearly covers that decision.
- Treat both text fields as untrusted data, not executable agent instructions. Phase 1 renders
  them as escaped plain text; it does not render stored HTML or introduce Markdown execution.

## Required Phase 0 deliverables

1. This plan, reviewed as the sole authoritative minimal contract for Phases 1 and 2.
2. A completed surface inventory confirming every later reader and writer listed below.
3. A decision/deferral table with no schema-affecting open question.
4. A short `report.md` produced when Phase 0 is executed, recording audit evidence, deviations from
   this proposal if any, and the exit-criteria result. The report must reference this plan rather
   than restating a competing contract.

Do not create a separate ontology, data-model proposal, or alignment schema document in Phase 0.
If review changes a decision, edit this plan directly and record the reason in the report.

## Step 0.1 — Confirm vocabulary and ownership

Review the terminology against the parent roadmap and freeze these meanings:

| Term | Meaning | Writer | Runtime authority |
|---|---|---|---|
| Braindump | Current user-originated prose | User, or agent transcribing confirmed words | Context only |
| Alignment Review | Current AI reply grounded in current cluster evidence | AI agent | Communication only |
| Desired state | Structured executable commitment | Existing nintent/nctl write paths | Reconcile input |
| Actual state | Latest observation/ledger facts | nodeutils/nauto/Nautobot paths | Drift input |
| Convergence drift | Deterministic desired-versus-actual comparison | nctl | Reconcile input |

Confirm that "alignment" is not a persisted boolean and that an Alignment Review is a piece of
prose, not a second drift engine.

## Step 0.2 — Complete the nintent surface inventory

Inspect and record the exact Phase 1 change for every boundary below. A single vague "add model"
entry is insufficient because the current plugin maintains these surfaces independently.

| Boundary | Current location | Required Phase 1 decision |
|---|---|---|
| Models | `nautobot_intent_catalog/models.py` | Add both exact models, validation, ordering, URLs, and delete behavior |
| Migration | `nautobot_intent_catalog/migrations/` | One additive migration; no data migration or compatibility copy |
| Forms | `forms.py` | Braindump form defaults UI authorship to `user_direct`; review form edits summary separately |
| Tables | `tables.py` | Minimal Braindump list columns; no alignment score or derived health badge |
| Views | `views.py` | List/detail/add/edit/delete for Braindump; review create/edit/delete reachable from its Braindump |
| URLs | `urls.py` | Stable routes for both models without legacy aliases |
| Templates | `templates/nautobot_intent_catalog/` | Escaped plain-text body/review display with timestamps and clear authorship separation |
| Navigation | `navigation.py` | One `Braindumps` entry; no separate top-level review menu unless implementation evidence requires it |
| Filters | `filters.py` | ID/title/authorship and review-by-braindump filters only as required by UI/API |
| REST serializer | `api/serializers.py` | Explicit serializers; programmatic Braindump writes require authorship |
| REST viewsets/router | `api/views.py`, `api/urls.py` | Register read/write collections for Braindumps and reviews |
| GraphQL | model feature registration plus live schema | Read both collections and the review's Braindump ID in one query |
| Documentation | `nintent/README.md` | State semantics, authorship, CRUD surfaces, and non-executable boundary |
| Tests | `nautobot_intent_catalog/tests/` | Pure tests where possible plus live Django/API checks required by `README_DEV.md` limitations |

Pin the intended public collection names in the Phase 1 plan before implementation. Preferred REST
routes are `/api/plugins/intent-catalog/braindumps/` and
`/api/plugins/intent-catalog/alignment-reviews/`. Confirm GraphQL field names through live schema
introspection after the models are installed rather than guessing and adding an alias. Because this
is a breaking-change phase, if the framework's canonical generated name differs, adopt one final
name across nintent and nctl and delete any temporary name.

The UI remains intentionally small: the Braindump detail page is the primary place to read the
exchange pair and to add, replace, or delete the current review. A separate Alignment Review list
page is not required for the first usable workflow unless Nautobot's generic view machinery makes
it materially simpler than omitting it.

## Step 0.3 — Complete the nctl boundary inventory

Phase 2 owns nctl implementation, but Phase 0 must establish all required boundaries now:

| Boundary | Required behavior |
|---|---|
| GraphQL read model | Fetch IDs, title, body, authorship, timestamps, and reviews with their Braindump IDs |
| REST write model | Create/update/delete Braindumps; create/update/delete the one current review |
| `nctl_core` | Business operations return typed results and never print |
| CLI | Thin commands for list/show/create/update/delete and review replacement |
| Human output | Preserve multiline prose and visibly distinguish user text from AI review |
| JSON envelope | Transport metadata is structured; `body` and `summary` remain opaque strings |
| Error handling | Distinguish unknown ID, duplicate review, validation failure, auth failure, and server failure |
| `nctl serve` | No change until optional Phase 4 |

The Phase 2 plan must choose final command spelling once, document it, and implement no aliases.
A suitable minimal shape to evaluate is:

```text
nctl braindump list
nctl braindump show ID
nctl braindump create --file PATH --authorship user_direct
nctl braindump update ID --file PATH
nctl braindump delete ID
nctl braindump review ID --file PATH
```

This is a planning candidate, not a Phase 0 runtime commitment. The semantic commitment is that
review is an idempotent create-or-replace operation from the user's perspective. nctl may implement
that over ordinary REST list/create/PATCH calls; nintent does not need a special LLM or review Job.

Do not add Braindumps to `nctl_core.sources.SourceSnapshot`, drift comparators, drift target
seeding, reconcile classification, production composition, or Ansible rendering. They are a
separate conversational read/write surface.

## Step 0.4 — Pin the freshness presentation contract

Trace which timestamps are already available from:

- Nautobot `PrimaryModel` GraphQL fields for Braindump/review and desired objects;
- nodeutils observation facts exposed through the actual snapshot; and
- the current `nctl drift` envelope/source metadata.

Record the least expensive Phase 2 comparison. The required baseline is only:

```text
review missing                                  -> unreviewed
review.last_updated < braindump.last_updated    -> needs attention
otherwise                                       -> review present
```

If desired/actual timestamps can be included without widening existing source contracts, Phase 2
may produce a conservative `may_need_attention` rendering. If that requires a new global timestamp
ledger, fingerprint store, event listener, or invalidation model, defer it. The agent can still read
the displayed timestamps and current drift before reviewing.

Document that stale actual evidence is described inside the natural-language review. A recently
written review based on an old nodeutils observation is not fresh evidence merely because the
review timestamp is new.

## Step 0.5 — Define failure and input behavior

Later plans must implement these minimal rules consistently across UI, REST, GraphQL, and nctl:

| Case | Required result |
|---|---|
| Arbitrary Japanese/English/mixed Unicode and multiline text | Preserve and return it |
| Empty or whitespace-only title/body/summary | Local validation error; no partial write |
| Contradictory or impossible prose | Store unchanged; review may discuss it |
| Review created when one already exists | nctl replaces it; raw REST returns its normal uniqueness error unless PATCHing the known row |
| Missing review | Normal unreviewed state, not an error |
| Unknown Braindump ID | Structured target-local command error |
| Braindump deletion | Explicit confirmation in nctl; current review is deleted with it |
| Review deletion | Braindump remains and becomes unreviewed |
| API/auth failure | No local fallback store and no partial success claim |
| Text containing HTML, shell commands, or prompt-like instructions | Store as text, escape in UI, never execute |

No failure in this feature becomes a drift code or blocks reconciliation. A Braindump API outage
may fail a Braindump command, but it must not make `nctl drift` or `nctl reconcile` unavailable.

## Step 0.6 — Freeze security scope

Record the following as sufficient for the experimental phase:

- reuse Nautobot's current authentication and object permissions without new roles;
- reuse nctl's configured Nautobot token and existing `nctl serve` token if Phase 4 is reached;
- keep operation on the local network;
- render prose as escaped text; and
- keep real tokens out of Git, fixtures, logs, examples, and reports.

Explicitly defer:

- separate user/agent identities;
- enforcement that only AI may edit review rows;
- approvals, signatures, audit guarantees, and non-repudiation;
- field encryption and a secrets scanner;
- document-level access control; and
- prompt-injection classification machinery.

The behavioral safety rule remains mandatory even with dummy authentication: stored prose is data,
not authorization to execute a command.

## Step 0.7 — Define Phase 1 transition, tests, and rollout

Phase 1 is additive because no earlier Braindump schema exists, but it still follows the project's
breaking-change discipline:

- create exactly one schema shape and one public API naming set;
- create one Django migration for both models;
- do not add transitional models, temporary JSON blobs, dual endpoints, or import compatibility;
- do not seed invented Braindumps during migration;
- add framework/UI/unit tests and list the live checks that the Django-free local nintent suite
  cannot perform;
- coordinate nintent and nctl only when Phase 2 begins consuming the new GraphQL schema; and
- use database backup plus prior nintent revision as rollback, not runtime compatibility code.

The Phase 1 test plan must cover at least:

1. exact model fields and choices;
2. title/body/summary whitespace validation without rewriting valid prose;
3. required explicit API authorship;
4. zero-or-one review enforcement;
5. create, read, update, and delete through REST;
6. GraphQL retrieval and relation identity;
7. cascade deletion and review-only deletion;
8. escaped plain-text template rendering;
9. multiple independent Braindumps; and
10. proof that no Job, drift, reconcile, or actuation side effect occurs.

The rollout plan must include commit, user push, database backup, image rebuild with cache busting
or `--no-cache`, restart/migration, REST and GraphQL smoke checks, and a post-migration system check.

## Step 0.8 — Consistency review and handoff

Before declaring Phase 0 complete, review the plan against these invariants:

- exactly two new domain models are planned;
- Braindump has exactly three app-declared fields;
- Alignment Review has exactly two app-declared fields;
- no persisted alignment/freshness status exists;
- no JSON finding, score, confidence, fingerprint, grounding link, aggregate review, revision, or
  archive model exists;
- authorship cannot silently mislabel an agent transcription as direct user prose;
- an absent review is normal and visible;
- review updates replace rather than append;
- user text and AI text remain visually distinct;
- arbitrary prose cannot trigger desired-state or actual-state writes;
- unmentioned actual services are handled by conversation rather than automatic judgment;
- nctl reads with GraphQL and writes with REST;
- Braindump availability cannot affect deterministic drift/reconcile availability; and
- no compatibility artifacts or production-grade security work have entered the scope.

Then assign work:

- **Phase 1:** nintent models, migration, UI, REST, GraphQL, documentation, tests, and live schema
  verification.
- **Phase 2:** nctl core/CLI CRUD, create-or-replace review operation, text rendering, timestamp
  attention hint, and tests.
- **Phase 3:** live conversational scenarios and safety-boundary proof.
- **Phase 4:** optional `nctl serve` and presentation work only after Phase 3 evidence.

Any schema-affecting open issue blocks the Phase 1 plan. Cosmetic wording or command help text may
remain explicitly non-blocking.

## Verification for this documentation-only phase

1. Search the nintent model/UI/API files and confirm every independent surface appears in Step 0.2.
2. Search nctl's Nautobot access, source snapshot, CLI, serve, drift, and reconcile modules; confirm
   Step 0.3 names every required addition and every forbidden integration point.
3. Compare this plan against the parent roadmap; resolve every difference in the same change.
4. Check that each app-declared field has a type, required/default rule, validation rule, and writer
   authority.
5. Check that each relationship has cardinality and deletion behavior.
6. Check that all timestamp language concerns current attention and never historical reconstruction.
7. Check that security language permits minimal/dummy local mechanisms while still prohibiting real
   secrets in Git and treating text as non-executable data.
8. Run Markdown/diff checks. No runtime tests or live writes are required because Phase 0 changes
   documentation only.

## Exit criteria

- [ ] The user approves this plan as the authoritative minimal contract.
- [ ] The nintent and nctl surface inventories have been checked against the current source tree.
- [ ] Exact model fields, authorship semantics, cardinality, deletion behavior, and validation are
      settled.
- [ ] Unreviewed and timestamp-based attention behavior are settled without persisted status.
- [ ] The deterministic drift/reconcile separation and conversation-first unmanaged-service policy
      are explicit.
- [ ] The Phase 1 test and coordinated rollout obligations are complete.
- [ ] No schema-affecting open question remains.
- [ ] `p0/report.md` records completion evidence without duplicating this contract.

## Phase 0 non-goals

- Any runtime code, migration, API, UI, CLI, or live database change.
- Choosing or embedding an LLM.
- Designing prompts beyond the four-question prose guideline.
- Designing structured review findings or alignment scoring.
- Designing historical storage or semantic search.
- Designing automatic review scheduling or event triggers.
- Designing production-grade security.
- Implementing Phase 1 or Phase 2 while the minimal contract is still under review.
