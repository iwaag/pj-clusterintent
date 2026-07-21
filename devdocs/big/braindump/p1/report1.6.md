# Step 1.6 — Register and pin GraphQL reads; update nintent documentation and version

Status: complete.

## GraphQL introspection

The Step 1.2 `@extras_features("graphql")` decorator on both models is sufficient — no app-specific
GraphQL schema module exists or was needed, matching the established pattern (Step 1.1 baseline).

Schema introspected (with all Step 1.1–1.5 files temporarily `docker cp`'d into the Nautobot 3.1.3
container, same method as prior steps, then reverted) using:

```bash
docker exec nautobot-nautobot-1 nautobot-server graphql_schema --out /tmp/schema.graphql
```

This management command builds and dumps the full GraphQL SDL by introspecting model registration;
it does **not** execute any database query, so it works correctly even though migration `0014` is
not applied to this database.

Canonical generated names:

```graphql
type BrainDumpDocumentType {
  id: UUID!
  created: DateTime
  last_updated: DateTime
  _custom_field_data: GenericScalar
  tags: [TagType]
  title: String!
  body: String!
  authorship: NautobotIntentCatalogBrainDumpDocumentAuthorshipChoices!
  alignment_review: AlignmentReviewType
  ...
}

type AlignmentReviewType {
  id: UUID!
  created: DateTime
  last_updated: DateTime
  _custom_field_data: GenericScalar
  tags: [TagType]
  braindump: BrainDumpDocumentType!
  summary: String!
  ...
}

enum NautobotIntentCatalogBrainDumpDocumentAuthorshipChoices {
  USER_DIRECT
  AGENT_TRANSCRIBED
}
```

Top-level query fields:

```
braindump_document(id: ID): BrainDumpDocumentType
braindump_documents(...): [BrainDumpDocumentType]
alignment_review(id: ID): AlignmentReviewType
alignment_reviews(...): [AlignmentReviewType]
```

All generated names use the plain snake_case model-name convention already used throughout this
schema (e.g. `desired_node_documents`-style pluralization); no custom alias was added and none was
needed.

## Pinned Phase 2 handoff query

```graphql
query {
  braindump_documents {
    id
    title
    body
    authorship
    created
    last_updated
    alignment_review {
      id
      summary
      created
      last_updated
    }
  }
}
```

This matches Decision 4's required field list exactly (Braindump `id`/`title`/`body`/
`authorship`/`created`/`last_updated`; review `id`/`summary`/`created`/`last_updated` plus the
related Braindump's `id`, available in the reverse direction by simply asking for `id` on the
parent `braindump_documents` query — the equivalent forward-relation query
`alignment_reviews { id summary created last_updated braindump { id } }` is the alternate direction
and is the one Step 1.7 will execute against Nautobot's disposable test database, since it does
not require a nested query to prove the relation).

### Deferred to Step 1.7: query execution needs a migrated database

Attempting to execute either pinned query via `graphene.test.Client` against this same schema
object failed at the import stage (`nautobot.core.graphql.schema` does not export a plain `schema`
instance at that import path — the real schema is only assembled through Nautobot's GraphQL view
machinery) and, more fundamentally, any successful execution would still need to run a real SELECT
against `nautobot_intent_catalog_braindumpdocument`/`..._alignmentreview`, which do not exist until
migration `0014` is applied. Executing the pinned query against real synthetic rows is Step 1.7's
job (Nautobot's own disposable per-test-run database) and Step 1.8's job (live smoke test after the
coordinated rollout).

## Documentation and version updates

- `nintent/README.md`: added a "Braindump and Alignment Review" section — UI entry, REST paths,
  the pinned GraphQL query, writer ownership (user/agent-transcribing writes Braindumps; only the
  agent writes reviews; nothing else writes either model), and the non-executable boundary
  (opaque autoescaped text, never Markdown/HTML-rendered, never a path into desired
  state/drift/reconcile/Jobs/nodeutils/Ansible).
- `nintent/README_DEV.md`: REST API section now lists five models
  (`DesiredNode`/`DesiredService`/`DesiredEndpoint`/`BrainDumpDocument`/`AlignmentReview`), updated
  serializer/viewset/router bullet lists, and two added `curl` verification examples for
  `/braindumps/` and `/alignment-reviews/`.
- `nintent/pyproject.toml` and `nintent/nautobot_intent_catalog/__init__.py`
  (`IntentCatalogConfig.version`): both bumped `0.8.0` → `0.9.0`.

## Verification

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.017s
OK
```

(`uv` rebuilt the local package wheel once, picking up the `pyproject.toml` version bump; no test
behavior changed.)

Container state was restored to the committed `HEAD` (pre-Step-1.6, since docs/version changes
don't need container verification) afterward; `nautobot-server check` came back clean.
