# Braindump Phase 1 Implementation Plan: Store and Edit the Exchange Diary in nintent

Parent: [roadmap.md](../roadmap.md) — Phase 1.

Contract: [Phase 0 plan](../p0/plan.md). Phase 0 is authoritative for domain semantics; this plan
chooses implementation details without adding fields or behavior to that contract.

Status: proposed.

## Goal

Make the current exchange diary durable and usable in nintent:

- a user can create one or many `BrainDumpDocument` records containing arbitrary Unicode prose;
- an AI agent can create, replace, or delete the one current `AlignmentReview` for each document;
- Nautobot UI clearly separates user-originated text from AI-authored review text;
- GraphQL exposes both models for reads and REST exposes both for ordinary CRUD writes; and
- storing or editing either kind of prose has no path into desired state, drift, reconcile, Jobs,
  nodeutils, Ansible, or host actuation.

This phase changes nintent only. It does not add nctl commands or an LLM runtime; those belong to
Phase 2.

Implementation begins only after the user accepts the Phase 0 plan as the minimal contract. If
that review changes the model shape, update Phase 0 first and then revise this plan rather than
quietly widening Phase 1.

## Current state (as of 2026-07-21)

- nintent is at version `0.8.0`; the local Django-free suite passes all 98 tests with:

  ```bash
  uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
  ```

- The running development instance is Nautobot 3.1.3. Its `PrimaryModel` supplies UUID identity,
  `created`, `last_updated`, custom-field data, and tags; neither new model needs to redeclare
  those framework fields.
- `nintent/nautobot_intent_catalog/models.py` declares all current app models as
  `@extras_features("graphql")` `PrimaryModel` subclasses. There is no app-specific GraphQL schema
  module; the decorator is the established read-registration mechanism.
- The latest migration is
  `0013_analysis_provenance_and_generic_endpoint_policy.py`, so the single new migration should be
  `0014_*` and contain both new models.
- UI support is explicit across `models.py`, `forms.py`, `filters.py`, `tables.py`, `views.py`,
  `urls.py`, `navigation.py`, and per-object templates. Creating a model alone does not make a
  usable plugin page.
- The REST API currently registers `nodes`, `services`, and `endpoints` through the serializer,
  viewset, and router pattern under `nautobot_intent_catalog/api/`. The two diary collections must
  be registered deliberately.
- The local nintent environment intentionally has no Django or Nautobot dependency. Pure/import
  checks run locally; model, form, view, REST, GraphQL, permission, and migration tests must also
  run with Nautobot's test runner in the rebuilt container.
- The development Nautobot image installs nintent from GitHub, not from the local checkout.
  Runtime verification therefore requires one coordinated nintent commit, a user-performed push,
  a cache-busted image rebuild, restart, and migration. Codex does not push.

## Decisions taken head-on

### 1. Add exactly the two Phase 0 models

`BrainDumpDocument` has exactly these app-declared fields:

| Field | Implementation |
|---|---|
| `title` | `CharField(max_length=255)`; required, not unique |
| `body` | required `TextField`; preserve Unicode, newlines, and meaningful surrounding whitespace |
| `authorship` | required `CharField` choice, `user_direct` or `agent_transcribed`; no model/API default |

Model behavior:

- use `@extras_features("graphql")` and inherit `PrimaryModel`;
- order by newest `last_updated` first, then `title`, so the current conversation is easy to find;
- `__str__()` returns `title`;
- `get_absolute_url()` returns the Braindump detail route; and
- `clean()` rejects a title or body for which `value.strip()` is empty, but never assigns the
  stripped value back to the field; accepted content is stored unchanged.

The UI may initially select `user_direct`, but `authorship` has no domain or serializer default.
Every REST writer must state its provenance explicitly.

`AlignmentReview` has exactly these app-declared fields:

| Field | Implementation |
|---|---|
| `braindump` | `OneToOneField(BrainDumpDocument, on_delete=CASCADE, related_name="alignment_review")` |
| `summary` | required `TextField`; preserve Unicode, newlines, and meaningful surrounding whitespace |

Model behavior:

- use `@extras_features("graphql")` and inherit `PrimaryModel`;
- `clean()` rejects a summary for which `value.strip()` is empty without rewriting valid text;
- `__str__()` identifies the related Braindump; and
- `get_absolute_url()` returns the related Braindump detail URL because that paired page is the
  review's canonical UI location.

The `OneToOneField` is the database uniqueness mechanism. No review row means unreviewed. Updating
the existing row replaces the current summary; creating a second row fails normally; deleting the
Braindump cascades to its review; deleting only the review leaves the Braindump intact.

Do not override `save()` to call `full_clean()` and do not add a second history mechanism. Model
tests call `full_clean()` explicitly, while forms and serializers enforce the same boundary on
supported write paths.

### 2. Keep the UI centered on the exchange pair

The public UI shape is deliberately asymmetric:

- `BrainDumpDocument`: list, detail, add, edit, and delete;
- `AlignmentReview`: add, edit, and delete from its Braindump detail page; and
- navigation: one top-level `Braindumps` item, with no separate review menu or review list.

There is no standalone review detail template. The Braindump detail page is the canonical detail
view for both halves of the exchange and shows them in separate panels. This satisfies the Phase 0
decision that AI-derived prose must not be mistaken for the user's words while avoiding a second,
duplicative document browser.

Review creation uses a parent-scoped URL and binds the relation in the view:

```text
/plugins/intent-catalog/braindumps/<braindump_pk>/review/add/
```

The review form contains only `summary`; it cannot accidentally attach the review to a different
document. Review edit/delete routes use the review UUID and return to the related Braindump after
success. If a review already exists when the add route is opened or posted, redirect to that
review's edit route with an informational message; it must not create history or silently append a
row. A database uniqueness failure from a true race is shown as a form error.

### 3. Preserve prose byte-for-byte at supported input boundaries

Django and Django REST Framework character fields trim surrounding whitespace by default. The
forms and serializers therefore explicitly disable trimming for `title`, `body`, and `summary`,
reject whitespace-only input with `value.strip()`, and return the original accepted string.

This rule applies to Japanese, English, mixed Unicode, multiline text, HTML-looking text, shell
commands, and prompt-like text. Content is stored as opaque text. The UI relies on Django
autoescaping and a pre-wrapped text container; it never uses `safe`, renders stored Markdown, or
interprets HTML.

### 4. Pin REST names and use generated GraphQL names only after introspection

The public REST collections are fixed now:

```text
/api/plugins/intent-catalog/braindumps/
/api/plugins/intent-catalog/alignment-reviews/
```

Both use ordinary `NautobotModelViewSet` CRUD. The review serializer represents `braindump` as a
UUID primary key, not a nested write. `BrainDumpDocumentSerializer.authorship` is explicitly
required on create; PATCH may omit an unchanged value.

GraphQL remains read-only and framework-generated through `@extras_features("graphql")`. Do not
guess a top-level query name or add a compatibility alias. After installing the migration, inspect
the live schema, record the canonical collection/type/relationship names in the Phase 1 report,
and pin a successful query that returns:

- Braindump `id`, `title`, `body`, `authorship`, `created`, and `last_updated`; and
- review `id`, `summary`, `created`, `last_updated`, and related Braindump `id`.

Phase 2 adopts those exact names. No mixed-version reader or alternate schema name is added.

### 5. Validation stays at the minimal contract boundary

Supported writers validate only:

- title, body, and summary are not empty or whitespace-only;
- authorship is one of the two choices;
- the referenced Braindump exists; and
- at most one review exists for each Braindump.

They do not validate language, grammar, Markdown, node/service names, contradictions, feasibility,
freshness, whether a service is wanted, or whether the prose matches desired/actual state. They do
not add status, findings, scores, fingerprints, or source links.

### 6. Framework timestamps are presentation facts, not state-machine fields

No freshness column is persisted. The Braindump list and detail page expose the Braindump's
`last_updated`; the detail review panel exposes the review's `last_updated`, or visibly says
`Unreviewed` when there is no row. A review older than its Braindump may be described in neutral UI
copy as needing attention, computed from the two timestamps only; it must never be labeled
`aligned`, `valid`, or `converged`.

The first implementation does not compare desired/actual observation timestamps in nintent. Phase
2 can present the broader conservative hint while the external agent reads current cluster state.

### 7. Roll out one schema, without compatibility artifacts

Migration `0014_*` creates both tables and no seed rows. It has no data migration because the
feature has no predecessor. Normal migration reversal may drop the two new empty/current tables,
but operational rollback uses a database backup plus the prior coordinated code revision so real
diary text is not silently discarded.

Version both `pyproject.toml` and `IntentCatalogConfig.version` as `0.9.0`. Do not add feature
detection, dual REST routes, deprecated fields, copy jobs, old-name aliases, or temporary JSON
storage.

## Reader, writer, and side-effect matrix

| Surface | Reads | Writes | Required behavior |
|---|---|---|---|
| Nautobot ORM | both models | both models | exact fields, validation, one-to-one, cascade |
| Braindump list/detail UI | both halves of the pair | none directly | escaped text, authorship and timestamps visible, missing review visible |
| Braindump forms/views | existing/new Braindump | create/update/delete Braindump | UI initial `user_direct`; deletion uses normal confirmation |
| Review forms/views | current review | create/update/delete current review | parent-bound create, summary-only edit, return to Braindump |
| REST | both collections | CRUD on both collections | explicit authorship on create; UUID relation; validation errors are 4xx |
| GraphQL | both collections | none | canonical generated names; timestamps and relation identity readable |
| Navigation | Braindump list | none | one `Braindumps` item only |
| nctl drift/reconcile | none | none | unchanged and independently available |
| Jobs/nodeutils/Ansible | none | none | no import, signal, callback, task, or actuation path |

## Step 1.1 — Freeze the implementation baseline and guardrails

Before editing nintent:

1. confirm Phase 0 user approval and record it in the Step 1.1 report;
2. record the nintent commit, version, latest migration, installed Nautobot version, and the
   passing local 98-test baseline;
3. search nintent and nctl for existing `BrainDumpDocument`, `AlignmentReview`, `braindump`, and
   `alignment_review` runtime names to ensure this is additive and has no abandoned prototype to
   migrate; and
4. capture an `nctl drift --json` baseline for the later no-side-effect check, retaining no token
   or private Braindump content in the report.

Do not create live diary rows or run a migration in this step.

Deliverable: `report1.1.md` with baseline evidence and any discrepancy that would change this
plan. A schema discrepancy blocks Step 1.2.

## Step 1.2 — Implement the models and the single migration

Change:

- `nintent/nautobot_intent_catalog/models.py`; and
- new `nintent/nautobot_intent_catalog/migrations/0014_braindump_exchange_diary.py`.

Implement the exact model definitions from Decision 1. Generate the migration in a Nautobot 3.1.3
environment rather than handwriting inherited `PrimaryModel` state, then review it to confirm:

- exactly two `CreateModel` operations;
- only the app fields and normal inherited `PrimaryModel` fields;
- the authorship choices and absence of a default;
- the one-to-one uniqueness and `CASCADE` behavior;
- no seed/data operation; and
- a dependency on migration `0013` plus any framework dependency generated for inherited fields.

Run `makemigrations --check --dry-run` after generating `0014`; it must report no residual model
state. Do not apply the migration to the live database yet.

Deliverable: `report1.2.md` recording the reviewed migration shape and model validation results.

## Step 1.3 — Add forms, filters, and the Braindump list table

Change:

- `nintent/nautobot_intent_catalog/forms.py`;
- `nintent/nautobot_intent_catalog/filters.py`; and
- `nintent/nautobot_intent_catalog/tables.py`.

Add:

- `BrainDumpDocumentForm` with `title`, `body`, `authorship`; UI initial authorship is
  `user_direct`, while all three strings follow Decision 3's preservation rule;
- `AlignmentReviewForm` with `summary` only and the same preservation rule;
- `BrainDumpDocumentFilterSet` with ID, title, authorship, and a `q` title search;
- `AlignmentReviewFilterSet` with ID and Braindump filters for REST, but no prose/full-text search;
  and
- `BrainDumpDocumentTable` with selection, linked title, authorship, Braindump update time, review
  presence/update time, and edit/delete actions.

The list query uses `select_related("alignment_review")` so review presence does not create an
N+1 query. Missing review is rendered as `Unreviewed`; an existing review is represented by its
timestamp, not an alignment badge or score.

Deliverable: `report1.3.md` with field/filter/table choices and form preservation evidence.

## Step 1.4 — Add the paired UI, routes, template, and navigation

Change:

- `nintent/nautobot_intent_catalog/views.py`;
- `nintent/nautobot_intent_catalog/urls.py`;
- `nintent/nautobot_intent_catalog/navigation.py`;
- new `templates/nautobot_intent_catalog/braindumpdocument.html`; and
- `nintent/nautobot_intent_catalog/tests/test_templates.py`.

Add generic list/detail/edit/delete views for Braindumps. The detail queryset loads the optional
review, and its template contains two clearly labeled panels:

1. **User-originated Braindump** — title, displayed authorship semantics, body, created time, and
   update time; and
2. **AI Alignment Review** — escaped summary and timestamps with edit/delete actions, or an
   `Unreviewed` message and add action.

Use a pre-wrapped text container so multiline text remains readable while Django autoescaping
remains active. Never use the `safe` filter.

Add the parent-bound review create view using Nautobot 3.1.3's `ObjectEditView.alter_obj()` hook,
plus review edit and delete views. Override return-URL behavior so all review operations return to
the related Braindump. Use the standard Nautobot delete confirmation path for both models.

Pin these UI route names once, without aliases:

```text
braindumpdocument_list
braindumpdocument_add
braindumpdocument
braindumpdocument_edit
braindumpdocument_delete
alignmentreview_add
alignmentreview_edit
alignmentreview_delete
```

Add one `Braindumps` navigation entry. Do not add a review list, review navigation item, dashboard
score, aggregate review, or desired-object link.

Deliverable: `report1.4.md` with route/view coverage, screenshots or concise rendered-HTML
evidence, and explicit escaping evidence.

## Step 1.5 — Add complete REST CRUD for both models

Change:

- `nintent/nautobot_intent_catalog/api/serializers.py`;
- `nintent/nautobot_intent_catalog/api/views.py`; and
- `nintent/nautobot_intent_catalog/api/urls.py`.

Add `BrainDumpDocumentSerializer` and `AlignmentReviewSerializer` following the existing
`NautobotModelSerializer` pattern. Keep framework identity/timestamps in output. Declare text
fields explicitly where required to disable trimming, declare `authorship` as a required choice on
create, and expose the review relation as a UUID primary key.

Add corresponding `NautobotModelViewSet` classes and reuse the Step 1.3 filters. Register exactly:

```python
router.register("braindumps", views.BrainDumpDocumentViewSet)
router.register("alignment-reviews", views.AlignmentReviewViewSet)
```

Raw REST behavior is ordinary resource CRUD:

- a duplicate review POST returns the framework's uniqueness validation response;
- replacement is `PATCH`/`PUT` of the existing review row, not a special action endpoint;
- deleting a review makes its Braindump unreviewed;
- deleting a Braindump cascades to its review; and
- invalid text/authorship/relation input returns a 4xx without partial writes.

Do not add an upsert endpoint, bulk action, LLM action, desired-state conversion endpoint, or
special approval route. Phase 2 implements client-side create-or-replace over this ordinary REST
contract.

Deliverable: `report1.5.md` with final route names, representative response shapes with synthetic
content, and the duplicate-review error shape. Never record a real API token.

## Step 1.6 — Register and pin GraphQL reads; update nintent documentation and version

The model decorators from Step 1.2 provide GraphQL registration. In a Nautobot test environment:

1. introspect the schema;
2. record the generated types, top-level collection fields, filters, and the review-to-Braindump
   relationship field;
3. execute one query reading multiple Braindumps and reviews with the fields in Decision 4; and
4. make the tested query the Phase 2 handoff contract.

If generated naming differs from an expected snake-case spelling, use the canonical generated
name. Do not introduce a custom alias. If a required contract field is missing, fix GraphQL
registration in this step; do not fall back to REST for Phase 2 reads without revising the parent
roadmap.

Update:

- `nintent/README.md` with diary semantics, UI entry, REST paths, canonical GraphQL query, writer
  ownership, and the non-executable boundary;
- `nintent/README_DEV.md` so the REST model list becomes five models and its verification examples
  include the two new routes;
- `nintent/pyproject.toml` to `0.9.0`; and
- `nintent/nautobot_intent_catalog/__init__.py` to the same version.

Deliverable: `report1.6.md` with schema-introspection evidence, the pinned query, and documentation
and version consistency checks.

## Step 1.7 — Test the complete model, UI, REST, GraphQL, and isolation contract

Add a focused Django/Nautobot test module such as
`nintent/nautobot_intent_catalog/tests/test_braindump.py`. Guard its imports so the existing
Django-free local discovery remains usable, but execute the real cases with Nautobot's test runner
inside the image.

### Model and form coverage

- exact app-declared fields, authorship values, and absence of an authorship default;
- arbitrary Japanese/English/mixed Unicode and multiline round trips;
- accepted surrounding whitespace is not rewritten;
- empty and whitespace-only title/body/summary are rejected;
- multiple Braindumps may have the same title;
- zero or one review per Braindump, including concurrent/database uniqueness enforcement;
- update replaces one row rather than appending another;
- review-only deletion preserves its Braindump; and
- Braindump deletion cascades to its review.

### UI coverage

- Braindump list/detail/add/edit/delete routes and standard permissions;
- review add/edit/delete routes, parent binding, return URL, and duplicate-add handling;
- initial UI authorship is `user_direct`, but agent transcription can be selected explicitly;
- missing review is visible as `Unreviewed`;
- user body and AI summary render in distinct labeled sections; and
- `<script>`, HTML, template-looking, and shell-looking strings render escaped and are never
  executed.

### REST coverage

- create/read/list/update/delete for each collection;
- POST without authorship, unknown authorship, whitespace-only text, and unknown Braindump fail;
- duplicate review creation fails without changing the existing review;
- PATCH preserves omitted fields and accepted text exactly;
- timestamps and UUID relation fields are present; and
- cascade and review-only deletion are observable through subsequent API reads.

### GraphQL and side-effect coverage

- the pinned GraphQL query returns multiple independent documents, exact prose, timestamps, and
  review-to-Braindump IDs;
- a missing review remains a normal readable condition;
- no signal, Job, task, webhook, nctl call, desired-model mutation, or Ansible invocation occurs on
  diary CRUD; and
- repository searches confirm neither model is imported by nctl drift/reconcile, nintent Jobs,
  nodeutils, nauto ingestion, or ansible_agdev.

Run:

```bash
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
docker exec nautobot-nautobot-1 nautobot-server test nautobot_intent_catalog.tests.test_braindump
```

Use an image/test database containing the new code for the second command; do not mistake the
currently installed Git revision for the local checkout. The full local suite must remain green,
and every Django/Nautobot case must pass before live migration.

Deliverable: `report1.7.md` with command results, counts, skips, and any environment limitations.

## Step 1.8 — Deploy once, run live smoke checks, and close the phase

Batch all nintent work into one deployable revision, then:

1. review the nintent diff and commit it locally;
2. ask the user to push the nintent commit; never push on the user's behalf;
3. verify the pushed commit is reachable before touching the live database;
4. back up the local Nautobot PostgreSQL database and record only the backup location/check result,
   not credentials, in the report;
5. rebuild from `devenv/nautobot` with cache busting or `--no-cache`, restart web/worker/scheduler,
   and confirm the installed nintent revision/version is the intended one;
6. run `nautobot-server migrate nautobot_intent_catalog` and
   `makemigrations --check --dry-run`;
7. run `nautobot-server check`, the Phase 1 Nautobot test module, and the existing local suite;
8. exercise UI add/edit/delete with synthetic Unicode prose;
9. exercise live REST CRUD and the pinned GraphQL query with synthetic content, including review
   replacement, review-only deletion, recreation, and final Braindump cascade deletion; and
10. run `nctl drift --json` immediately before and after the synthetic diary CRUD window and
    compare deterministic target/findings content, excluding ordinary fetch timestamps; also
    confirm the command remains compatible with the Step 1.1 baseline shape. Do not run
    `reconcile --yes` or any Ansible actuation for this feature.

All smoke rows are deleted at the end through the normal API/UI path. If verification fails after
migration, stop writes, retain diagnostic output without secrets, and choose between fixing
forward or restoring the database backup plus prior nintent image. Do not solve rollback with
compatibility code.

Write `report1.8.md` with:

- committed and installed nintent revisions/version;
- migration and system-check results;
- local and Nautobot test counts;
- final REST paths and canonical GraphQL names/query;
- synthetic CRUD/cascade/escaping evidence;
- the drift-isolation comparison;
- cleanup confirmation; and
- each exit criterion marked pass/fail.

Update the parent repository's nintent submodule pointer only after the pushed/rebuilt revision is
verified.

## Verification summary

Phase 1 is not complete from unit tests alone. Required gates are:

1. local Django-free regression suite;
2. migration state check in Nautobot 3.1.3;
3. Django/Nautobot model, form, view, REST, and GraphQL tests;
4. live UI/REST/GraphQL smoke checks after the Git-based rebuild;
5. explicit escaping and Unicode preservation checks;
6. review uniqueness and both deletion directions;
7. static and live evidence that drift/reconcile remain independent; and
8. database backup, smoke-data cleanup, and documented rollback readiness.

## Out of scope

- Any nctl Braindump command, output envelope, attention hint, or REST/GraphQL client operation
  (Phase 2).
- Reading desired state, actual state, or drift to compose a review (external-agent workflow in
  Phases 2–3).
- Embedding an LLM, prompt framework, scheduler, worker, signal, webhook, or automatic review
  trigger.
- Automatically translating prose into desired state or invoking reconcile/Ansible.
- Alignment status, scores, JSON findings, confidence, fingerprints, grounding links, per-object
  provenance, or an aggregate review.
- Braindump/review revisions, archive rows, soft deletion, temporal queries, or semantic search.
- Markdown/HTML rendering of stored prose.
- Separate user/agent identities, document-level permissions, approval workflows, signatures,
  encryption, or production-grade secrets handling.
- A separate Alignment Review list/navigation page.
- `nctl serve`, dashboard integration, or another client (optional Phase 4 after live proof).

## Exit criteria

- [ ] The Phase 0 contract has explicit user approval and no schema-affecting question remains.
- [ ] Migration `0014_*` adds exactly `BrainDumpDocument` and `AlignmentReview`, with the exact
      fields, choices, one-to-one relation, timestamps, and cascade behavior in this plan.
- [ ] UI users can list, view, create, edit, and delete arbitrary Unicode Braindumps.
- [ ] A Braindump detail page visibly separates user-originated text from the zero-or-one current
      AI review and exposes both update times.
- [ ] Review create, replacement, review-only deletion, and Braindump cascade deletion work through
      the supported UI and API paths without history rows.
- [ ] REST CRUD is live at the two pinned routes, requires explicit programmatic authorship, and
      preserves accepted text unchanged.
- [ ] Canonical generated GraphQL names are introspected, documented, tested, and return both
      models with timestamps and relation identity.
- [ ] Whitespace validation, Unicode/multiline round trips, one-to-one enforcement, cascade,
      permissions, escaping, REST failures, GraphQL reads, and multiple documents are covered by
      passing tests.
- [ ] Diary CRUD produces no desired-state mutation, drift/reconcile change, Job, nodeutils,
      Ansible, or host side effect.
- [ ] nintent `0.9.0` is committed, user-pushed, cache-busted into the local Nautobot image,
      migrated once, and verified with system checks and live smoke tests.
- [ ] The database backup is verified, synthetic smoke rows are removed, and `report1.1.md` through
      `report1.8.md` record the implementation and rollout evidence without secrets.

## Suggested commit order

1. Parent repository: this Phase 1 plan only.
2. nintent: models/migration + UI + REST/GraphQL + tests + docs/version as one coordinated,
   deployable `0.9.0` change. Multiple local commits are acceptable, but perform one user push and
   one image rebuild after the whole surface passes review.
3. Parent repository: verified nintent submodule pointer plus `p1/report1.1.md`–`report1.8.md`.
