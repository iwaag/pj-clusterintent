# Phase 2 Plan — Canonical Batch REST Endpoint

Status: **planned** (implementation not started).

Input contracts: [`../p0/report.md`](../p0/report.md) (wire contract, identities, cutover order) and
[`../p1/plan.md`](../p1/plan.md) plus its step reports (the in-memory service that already exists).
Neither is restated here.

## Goal

`nautobot_intent_catalog.batch.plan_batch()` / `apply_batch()` become remotely callable through one
authenticated HTTP surface, and that surface is deployed to the local scratch Nautobot so a real
client can preview and apply a batch and read the result back through GraphQL.

## Scope

In scope:

- One POST endpoint that decodes JSON or YAML into the Phase 0 envelope and returns the Phase 1
  result artifact.
- Authentication, permission, and HTTP status mapping for that endpoint.
- Endpoint contract tests (runtime and Django-free).
- The first deployment of the Phase 1 schema reduction: commit, push (user), image rebuild,
  restart, migrate.
- A live acceptance smoke against the deployed endpoint.

Out of scope: moving nctl's lifecycle/ledger writes onto the endpoint and deleting the per-model
PATCH routes and the Import Job (Phase 3), removing `nauto/seed/intent_sources.yaml` (Phase 4).
The endpoint is added beside the existing routes in this phase; that overlap is the deployment
bridge Phase 0 already allowed.

## Design decisions to implement

Everything not listed here — module layout, naming, error wording, helper structure — is the
implementer's choice.

### 1. Route

```text
POST /api/plugins/intent-catalog/desired-state/batch/
```

Registered in `nautobot_intent_catalog/api/urls.py` next to `router.urls` (a plain `path()`, not a
router registration — this is not a model collection). POST only; every other method is 405.

`dry_run` stays a body field. No `?dry_run=` query parameter, no second route, no separate
plan/apply endpoint.

### 2. Encodings

The deployed DRF stack parses JSON only (`JSONParser` + `NautobotCSVParser`); `pyyaml` is installed
but no YAML parser is registered. Set `parser_classes` on this view explicitly to `JSONParser` plus
a small YAML parser (`yaml.safe_load`) accepting `application/yaml`, `text/yaml`, and
`application/x-yaml`. Drop the CSV parser here.

Both encodings decode to the same `dict` and then take the identical `plan_batch`/`apply_batch`
path — no second semantic contract. A YAML syntax error or a non-mapping document is a 400.
Responses are always JSON.

### 3. Status mapping

| Condition | Status | Body |
|---|---|---|
| `dry_run: true`, decoded | 200 | result artifact |
| `dry_run: false`, `transaction.status == committed` | 200 | result artifact |
| plan holds a conflict (`blocked`) or apply reports `rolled_back` | 409 | result artifact |
| `BatchValidationError`, YAML/JSON syntax error, non-object body | 400 | DRF error body |
| unsupported `Content-Type` | 415 | DRF error body |
| body over `DATA_UPLOAD_MAX_MEMORY_SIZE` (2.5 MB, already configured) | 400 | Django error |

A conflict body is the full artifact, not a bare error string: the caller needs the per-operation
reasons. No new size bound is introduced; Django's existing one is sufficient.

### 4. Authentication and permission

Nautobot's default `TokenAuthentication` + `SessionAuthentication` apply unchanged. The default
`TokenPermissions` cannot be used as-is — it is a `DjangoObjectPermissions` subclass and needs a
view `queryset`, which a multi-model batch view does not have. Required behaviour:

- unauthenticated → 401/403;
- authenticated but missing the nintent model permission for a kind present in the batch → 403;
- token without `write_enabled` and `dry_run: false` → 403 (`dry_run: true` needs only read rights).

Suggested implementation: `permission_classes = [IsAuthenticated]`, then after decoding, map each
operation's `kind` to its model and check `request.user.has_perms([...])` for the
`add`/`change`/`delete` permissions the batch actually needs, plus an explicit `request.auth`
`write_enabled` check for apply. Permission failures are decided before any planning.

### 5. Nothing is persisted

The request body is not stored, logged, or attached to a Job result. The response artifact is
returned to the caller only. No new model, field, or table.

Add a `@extend_schema` annotation (or an explicit exclusion) so drf-spectacular does not warn or
break `/api/docs/` on a serializer-less APIView.

## Steps

One commit and one short report entry per step, as usual.

### Step 1 — Endpoint

The parser, the view, the URL, the status mapping, and the permission check. Thin: decode → permit
→ `plan_batch()`/`apply_batch()` → `as_dict()` → `Response`. No planning logic in the view.

### Step 2 — Endpoint contract tests

Runtime (`nautobot.core.testing.api.APITestCase`, the pattern already used in
`tests/test_api_contract.py`):

- unauthenticated POST is rejected; a permitted user's `dry_run: true` returns 200 and writes zero
  rows; a read-only token cannot apply;
- a mixed-kind apply (create + update + delete in one batch) returns 200 `committed` and the rows
  match;
- a batch containing one conflict returns 409 and leaves every row unchanged;
- the same batch expressed as YAML and as JSON produces the same artifact;
- malformed YAML → 400; unknown field → 400; a non-POST method → 405.

Django-free: the YAML parser's media types and its error path.

### Step 3 — Local gates, commit, deploy

Run the gate table below, commit, then **stop and ask the user to push `nintent`** (pushes are the
user's). After the push:

1. `pg_dump` the `nautobot` database to `.local/` — cheap insurance before the first application of
   the Phase 1 reduction migration on real scratch rows.
2. `cd devenv/nautobot && docker compose --env-file ../.env build --no-cache` and confirm the
   resolved nintent SHA in the build log matches the pushed commit (the build cache has silently
   pinned a stale commit before).
3. `docker compose --env-file ../.env up -d`.
4. `docker exec nautobot-nautobot-1 nautobot-server post_upgrade` (migrate + job registry refresh).
   Migrations `0019`/`0020` land here for the first time: the removed columns are dropped from the
   live scratch database.
5. Expect the `Analyze Intent Sources` Job to become uninstalled; delete the stale `JobModel` row if
   it lingers in the UI.

This step is the phase's only hard-to-reverse action. Pause before it and report the result before
continuing.

### Step 4 — Live acceptance and report

Against the deployed instance, using the token from `.local/secrets` (never echo it):

1. POST a mixed-kind batch (`desired_node` + `desired_endpoint` upsert) with `dry_run: true`;
   confirm the plan and that GraphQL still shows no such rows.
2. Repeat with `dry_run: false`; confirm 200 `committed` and that a GraphQL query returns the new
   normalized rows immediately.
3. POST a `delete` batch for the same two rows; confirm 200 and that GraphQL no longer returns them.
   This both proves delete over HTTP and cleans up the smoke rows.
4. Run `uv run --project nctl nctl drift --json` and confirm the reduced schema did not break the
   live read path (this is the first live exercise of the Phase 1 nctl alignment).

Use synthetic identities (e.g. `p2-smoke`); do not touch real cluster rows. Write results into
`devdocs/big/refactor_io/p2/report4.md` and close the phase.

## Gates

| gate | working directory | command |
|---|---|---|
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` |
| Nautobot runtime clean | superproject root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` |

The runtime gate runs the endpoint against staged local sources, so the contract is fully verified
before the push. Re-run the nctl gate after deployment only if Step 4 exposes a read-path problem.
If the Django-free suite's expected skip count changes, update the number in `README_DEV.md`.

## Prohibitions

Only these:

1. One desired-state mutation endpoint, one contract for both encodings, one `dry_run` switch.
2. The endpoint owns no planning or apply logic of its own — it calls the Phase 1 service.
3. Nothing about the request or the response is persisted.
4. A rejected or conflicting batch leaves every row unchanged.
5. The live smoke touches only synthetic rows it creates and deletes.

Everything else is at the implementer's discretion.

## Exit criteria

- An authenticated caller can preview and atomically apply a mixed-kind batch over HTTP, in JSON and
  in YAML, and GraphQL immediately returns the resulting normalized state.
- Conflicts, invalid input, and insufficient permission return ordinary HTTP responses and write
  nothing.
- The rebuilt image is running the pushed commit, the Phase 1 migrations are applied to the scratch
  database, and `nctl drift` still works against it.
- All gates pass and every worktree is clean.

## Known risks

- **First live application of the Phase 1 reduction.** Dropping the removed columns is irreversible
  on the scratch database. The `pg_dump` in Step 3 is the whole mitigation; the data itself is
  reproducible from `nauto/seed/intent_sources.yaml` through the Import Job.
- **Build cache pinning a stale nintent commit.** Verify the SHA in the build log; do not trust a
  successful build alone.
- **`TokenPermissions` does not fit a queryset-less view.** Do not paper over it with a dummy
  `queryset` attribute — that would silently check the wrong model's permission.
