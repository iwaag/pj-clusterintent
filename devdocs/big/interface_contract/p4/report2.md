# Phase 4 Step 2 Report — Re-prove Phase 2/3 in disposable Nautobot and HTTP

Plan: [plan.md](plan.md), Step 2.

Status: complete except item 13 (see "What Step 2 does not close" below). Disposable-only work,
as authorized without a live-maintenance approval by Section 3.4. No live mutation, no live Job
run, no live service stop/restart, no live database/media action, no push.

## 1. Disposable isolation (plan item 1)

New compose project `nic-p4-disposable` at
`.local/interface-contract/p4/20260726_disposable/docker-compose.yml`, modeled on
[`p1/disposable/docker-compose.yml`](../../../../.local/interface-contract/p1/disposable/docker-compose.yml)
with a distinct project/volume/network namespace and non-live host port:

- network `nic-p4-disposable_default` (distinct from live's `nautobot_default`).
- volumes `nic-p4-disposable_nic_p4_pg_data` / `..._nic_p4_redis_data` (distinct from live's
  `nautobot_nautobot_media`/`_static` and `my_postgres_db`/`service_scripts-redis-1`, which this
  compose project never references).
- postgres/redis ports not published to the host at all; Nautobot web published only at
  `18000:8080` (live is `8000:8080`).

`docker compose down -v` at the end of this step removed all four containers, both volumes, and
the network; confirmed absent via `docker ps -a`/`docker volume ls`/`docker network ls` (all
`nic-p4-disposable*` names gone) while the three live `nautobot-*` containers remained running
and untouched throughout.

## 2. Migration and schema checks (plan items 2-3)

- Fresh `nic_p4_pg_data` volume, migrated cleanly: `nautobot-server showmigrations
  nautobot_intent_catalog` ends at `0016_remove_reconciliation_dashboard_surfaces`, matching live.
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`: `No changes
  detected`.

## 3. A real blocker found and fixed before any suite could run (not in plan Section 2's audit)

Bringing up `nic-p4-disposable-nautobot-1` with the exact repaired Step 1 source failed its own
startup gate: `docker-entrypoint.sh` runs `nautobot-server check --deploy` before `runserver`, and
this failed with `drf_spectacular.E001: Schema generation threw exception
"'AlignmentReviewSerializer' object has no attribute 'child'"`. This is not a test artifact — the
same command is what the real container entrypoint (`devenv/nautobot/Dockerfile` /
`docker-compose.yml`) runs on every start, so an unrepaired rebuild would have failed to come up
at all, a defect Section 2's planning-time audit (which never ran a real `runserver`/`check
--deploy`) could not have found.

Root cause, traced via a monkeypatched traceback (full chain in
`nautobot/core/api/schema.py:113`'s `NautobotAutoSchema.get_operation`): Nautobot's
`BulkDestroyModelMixin.bulk_destroy` carries `@extend_schema(request=BulkOperationSerializer(many=True))`,
which is what makes drf-spectacular treat a bulk-DELETE request body as a `ListSerializer` (with a
`.child`). `BrainDumpDocumentViewSet`, `AlignmentReviewViewSet`, and `DesiredNodeViewSet` each
override `bulk_destroy` (Phase 2's "bulk DELETE returns 405" contract) with a bare method that does
not carry that decorator, so drf-spectacular fell back to `view.get_serializer()`, got a plain
(non-list) serializer, and `NautobotAutoSchema.get_operation`'s DELETE-bulk branch crashed calling
`.child` on it. Verified reproducible 3/3 via the real `nautobot-server check --deploy` CLI
(non-reproducible through equivalent manual `django.setup()` + `SchemaGenerator().get_schema()`
calls, which take a different Nautobot plugin-loading path that never exercises this exact code
path — worth remembering if this class of bug recurs).

Fix: added `@extend_schema(request=BulkOperationSerializer(many=True))` to all three overriding
`bulk_destroy` methods in `nintent/nautobot_intent_catalog/api/views.py`, preserving their 405
runtime behavior while restoring the schema contract. `check --deploy` then passed with only the
five expected `security.W00x` warnings (no `SECRET_KEY`/HSTS hardening in a disposable container).
An earlier apparent recurrence of the same error was traced to Redis cache poisoning from my own
concurrent web+worker `pip install` race during initial setup (both containers rebuilding the
package into the same bind-mounted `nintent/build/`), not a real defect; `redis-cli FLUSHALL`
resolved it and the fix above is unrelated to that artifact.

## 4. Complete disposable Nautobot App suite (plan items 4-7)

First real run (before any fix) reproduced Section 2.2's finding and went further: 18 failures
(not the audit's 9 failures/6 errors, because the audit's isolated run predates several Step 1
tests). Summary retained at
`.local/interface-contract/p4/20260726_170500/disposable_app_suite_planning_fail_summary.txt`.
Six were genuine test-authoring defects introduced by Step 1's new runtime tests, exposed only by
a real Nautobot process (the Django-free suite cannot catch any of these):

| Test | Wrong assumption | Fix |
|---|---|---|
| `RESTMethodFieldMatrixTests.test_desired_node_response_fields_are_exact` | Expected only the 10 `DesiredNodeSerializer.Meta.fields`; `NautobotModelSerializer` always adds `display`/`object_type`/`notes_url`/`custom_fields` regardless of `Meta.fields` | expected set now includes the four universal fields |
| `...test_desired_node_full_put_delete_and_bulk_patch_return_405` | Test user had no `delete_desirednode`, so DELETE hit DRF's permission check (403) before ever reaching the `destroy()` override that returns 405 | granted `delete_desirednode` so the 405 assertion proves the override, not a permission gate |
| `GraphQLContractTests.test_intent_source_singular_and_plural_queries_fail_schema_validation` | Assumed graphene-django returns 200-with-`errors` for an unknown root field; it returns HTTP 400 | assert `400`, not `200` |
| `BrainDumpViewTests.test_detail_view_has_no_mutation_control` | `"csrf_token"` needle false-matched the base template's `nautobot_csrf_token` JS variable, present on every page regardless of mutation | needle narrowed to `"csrfmiddlewaretoken"`, the actual rendered hidden-field name |
| `UIContractManifestTests.test_navigation_only_links_the_eleven_retained_lists` | Compared rendered nav `href` paths (`/plugins/.../nodes/`) against route *names* (`plugins:...:desirednode_list`) | expected set now built with `reverse()` |
| `UIRuntimeRenderTests.test_every_retained_list_and_detail_renders` | Asserted the raw `pk` renders in the body (no retained template shows a bare UUID) and asserted `DesiredComputeInstance.instance_kind`'s raw value (`"container"`) instead of its rendered choice label (`"Container"`) | dropped the pk assertion (every entry already has a `label_field` identity check); `DesiredComputeInstance` and `DesiredNodeOperationalOverride` (previously untested, `label_field: None`) now use `get_instance_kind_display`/`desired_node` |

After both the `check --deploy` fix and these six test fixes: **304/304 pass**, 0 failures, 0
errors. Full pass log:
`.local/interface-contract/p4/20260726_170500/disposable_app_suite_pass.log`. This suite includes
the complete UI (22 list/detail render, 38 removed-route, navigation/table, before/after
mutation-fingerprint), REST (method/field/zero-write matrix), and GraphQL (`IntentSource`
schema-validation-failure plus 11-root joined query) matrices from Section 2.2's table — every row
of that table is now closed by a passing runtime assertion, not a skip.

Local Django-free suite re-checked after the same edits: still 226 passed/13 skipped, unchanged.

## 5. Real HTTP proof beyond the Django test client (plan items 7-14)

Exposed on `http://localhost:18000` with a disposable-only superuser token (never the live
token). A separate `nctl.toml` at
`.local/interface-contract/p4/20260726_disposable/nctl.toml` points a real `nctl` at this port
(via `$NCTL_CONFIG`); it is git-ignored and was never merged into the repo-root `nctl.toml` that
points at live.

**Synthetic fixture** (`step2_link_fixture.py`): one native `dcim.Device` ("p4stephost") and one
`DesiredNode` (slug `p4stephost`, `accepted_actual_types=["device"]`, no realized link) — minimal
Location/DeviceType/Manufacturer/Role prerequisites only, no realized link set.

**Real planner, real GraphQL** (plan item 9): `nctl drift --host p4stephost --json` against the
disposable server (not mocked) produced diff code `actual_node_not_linked` for the fixture,
confirming the real drift/candidate-ranking code path recognizes the uniquely-matching Device.

**Real ledger writer through GraphQL/PATCH/GraphQL** (plan item 10, `step2_link_execute.py`):
called nctl's actual `execute_link_actual_node()` (not a mock) against the disposable server. It
performed the real GraphQL precondition read, the real REST `PATCH .../nodes/<id>/`, and the real
post-PATCH GraphQL refetch, and returned confirmed:
```
LINK_EXECUTED {"node_id":"90ce77df-...","node_slug":"p4stephost","field":"realized_device","candidate_id":"98b1a505-...","candidate_name":"p4stephost"}
```

**Fresh non-repetition** (plan item 11): calling the same action again against the now-linked node
correctly raised `LedgerActionError` with code `node_already_linked` (`REPEAT_CORRECTLY_REFUSED`),
and a fresh `nctl drift --host p4stephost --json` afterward no longer reports
`actual_node_not_linked`/`missing_actual_node` for the node (only the expected
`missing_actual_data`, since no real nodeutils ingest ran here — out of scope for this step).

**Lifecycle change/no-op and Braindump/review CRUD with GraphQL confirmation** (plan item 12,
`step2_lifecycle_braindump.py`): real REST PATCH + real GraphQL refetch for each step —
`LIFECYCLE_CHANGE_CONFIRMED` → `LIFECYCLE_NOOP_CONFIRMED` (repeat PATCH, same value, GraphQL still
shows it) → `BRAINDUMP_CREATE_CONFIRMED` → `BRAINDUMP_UPDATE_CONFIRMED` →
`ALIGNMENT_REVIEW_CREATE_CONFIRMED` → `ALIGNMENT_REVIEW_UPDATE_CONFIRMED` →
`ALIGNMENT_REVIEW_DELETE_CONFIRMED` → `BRAINDUMP_DELETE_CONFIRMED`. All confirmations queried the
GraphQL API (not the REST response body), proving the write is visible through the read side
Phase 2 retained.

**HTTP method/path/status counts, zero calls to removed collections** (plan item 14): the same
script recorded every call to `http_log.json` (27 calls total: 1 GraphQL-schema-check-adjacent
lookup, the lifecycle/Braindump/AlignmentReview CRUD sequence, 9 removed-collection probes) and
asserted all nine removed REST families (`services`, `dependencies`, `endpoints`,
`compute-platforms`, `compute-instances`, `placements`, `operational-overrides`, `ip-ranges`,
`sources`) return `404` — `REMOVED_REST_COLLECTIONS_404_CONFIRMED 9`. Sanitized log retained at
`.local/interface-contract/p4/20260726_170500/http_call_log.json` (method/path/status only, no
tokens or bodies).

## 6. nctl full suite (plan item 15)

`uv run pytest -q` in `nctl/`: **962 passed** (unchanged from Step 1's count; no new failures from
this step's real-HTTP exercises, which used nctl's library functions directly rather than
modifying nctl source).

## 7. Evidence retention and teardown (plan items 16-17)

Evidence retained at `.local/interface-contract/p4/20260726_170500/` (mode `0700`; files `0600`):
`check_deploy_pass.log`, `disposable_app_suite_pass.log`,
`disposable_app_suite_planning_fail_summary.txt`, `http_call_log.json`, `migrations_list.txt`,
`makemigrations_check.txt`. No token, authorization header, Braindump/AlignmentReview body beyond
the synthetic probe strings above, or raw ObjectChange payload was written. The disposable-only
API token (`eeee...`, never used by live) appears nowhere in retained evidence.

Teardown: `docker compose -p nic-p4-disposable down -v` removed all 4 containers, both volumes,
and the network; confirmed absent by name in `docker ps -a`/`docker volume ls`/`docker network
ls`. The three live `nautobot-*` containers were never stopped, rebuilt, or otherwise touched.

## What Step 2 does not close

**Plan item 13 (representative fail-closed reset fixtures) was not exercised as real HTTP.** The
missing nctl node-link boundary cases (absent id, absent node, slug mismatch, partial link,
pre/post GraphQL failure, wrong confirmed source) that Step 1 added
(`test_reconcile_ledger.py`/`test_reconcile_executor.py`) remain unit-level with mocked HTTP, not
re-run against this disposable server. They are lower-risk than the positive-path proof above (all
are guard clauses that run before any mutation), but this is a real gap against the plan's Step 2
item list, not a silent pass. Flagging for Step 10's "every skipped, substituted, declined, or
failed check" accounting rather than closing it here unreviewed.

Deployment-path items (exact commit pinning, canonical YAML path in all three containers, image
build) are explicitly Step 3's job, not this step's; the `nautobot_config.py` used here still has
empty `PLUGINS_CONFIG` like Step 0's baseline, unchanged on purpose.

## Verification

- `nautobot-server check --deploy` (disposable): clean, 0 errors, 5 expected warnings.
- `nautobot-server test nautobot_intent_catalog` (disposable): 304 passed, 0 failed, 0 errors.
- `python3 -m unittest discover -s nautobot_intent_catalog/tests` (repo checkout): 226 passed, 13
  skipped — unchanged.
- `uv run pytest -q` (nctl): 962 passed — unchanged.
- Real HTTP link/lifecycle/braindump/review/removed-route proof: all assertions in
  `step2_link_execute.py`/`step2_lifecycle_braindump.py` passed (scripts exited 0).
- `git -C nintent diff --check`: clean.
- Disposable teardown: containers/volumes/network confirmed removed; live stack confirmed
  untouched throughout (`docker ps` before/after identical for `nautobot-*`).

Next: Step 3 (freeze commits and build a reproducible candidate) — requires the user to push the
nintent commit made in this step (and any from Step 1) before remote-SHA verification can pass.
