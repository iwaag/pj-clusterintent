# Interface Contract Phase 2 Implementation Plan: Contract REST and Canonicalize Confirmation Reads

Parent: [roadmap.md](../roadmap.md) — Phase 2.

Predecessors:

- [Phase 0 final report](../p0/report.md) — `complete`; the final interface matrix, GraphQL
  selections, and REST method/field manifest are frozen.
- [Phase 1 final report](../p1/report.md) — Phase 1 scope `complete`, overall initiative
  `implemented, not deployed`; the coordinated Phase 1 nintent/nauto changes remain intentionally
  undeployed until Phase 4.

Status: proposed; coordinated `nintent`/`nctl` implementation and disposable-environment
verification only. This phase does not authorize deployment, use of the live mutation endpoints,
or mutation of the live Nautobot database.

## 1. Goal and required transition

Retain REST only where a named current writer requires a mutation, and make GraphQL the sole nctl
domain-read and write-confirmation path.

The Phase 2 transition is:

```text
before
  7 nintent REST ModelViewSets with framework-wide create/read/update/delete behavior
  + 7 model serializers exposing fields = "__all__"
  + node POST/PUT/PATCH/DELETE and bulk operations broader than either current writer
  + DesiredService/DesiredEndpoint/compute REST collections with no current writer
  + link_actual_node reading DesiredNode through REST before and after PATCH
  + IntentSource registered in GraphQL despite having no GraphQL consumer

after Phase 2
  3 nintent REST mutation collections:
    nodes
    braindumps
    alignment-reviews
  + explicit response fields and exact writable-field sets
  + node detail PATCH limited to lifecycle or realized Device link/source
  + no node create, replace, delete, or bulk mutation
  + no bulk or PUT mutation on the two prose collections
  + 4 unused REST collections absent
  + link_actual_node using the pinned desired GraphQL snapshot before and after its PATCH
  + IntentSource absent from GraphQL while its ORM, Jobs, and UI model remain
  + Job protocol REST reads/downloads and /api/status/ unchanged
```

The positive node-link path is:

```text
pinned desired GraphQL snapshot
  -> resolve exactly one DesiredNode by immutable UUID
  -> prove realized_device is empty
  -> PATCH exactly realized_device + realized_device_source=derived
  -> fresh pinned desired GraphQL snapshot
  -> prove the same UUID has the requested link and source
  -> fresh drift/planning
  -> no repeated link_actual_node action
```

The positive direct-write paths are:

```text
lifecycle
  GraphQL current node
  -> PATCH lifecycle only
  -> GraphQL confirmation

Braindump update/delete
  GraphQL current document
  -> narrow REST PATCH/DELETE
  -> GraphQL confirmation

Braindump create
  locally validated payload
  -> narrow REST POST
  -> GraphQL confirmation by returned immutable UUID

Alignment Review create/replace/delete
  GraphQL current Braindump/review relation
  -> narrow REST POST/PATCH/DELETE
  -> GraphQL confirmation
```

A successful HTTP response is not confirmation. Every retained nctl write must return success only
after the canonical GraphQL representation proves the requested state, or absence after deletion.

## 2. Authority, prerequisites, and safety boundary

### 2.1 Governing inputs

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- the parent roadmap;
- the Phase 0 plan and all Phase 0 reports, with particular attention to
  [report1.md](../p0/report1.md), [report2.md](../p0/report2.md), and the frozen contract in
  [report7.md](../p0/report7.md);
- the Phase 1 plan and final report;
- `devdocs/vision/refactor/vision.md`;
- the current Braindump, core-reconcile, and VM roadmaps;
- the active `devdocs/big/vm/p3/plan.md` supersession note;
- `nintent/README.md`, `README_QUICK.md`, `README_DEV.md`, and `CONCEPT.md`;
- `nintent/nautobot_intent_catalog/models.py`;
- `nintent/nautobot_intent_catalog/api/serializers.py`;
- `nintent/nautobot_intent_catalog/api/views.py`;
- `nintent/nautobot_intent_catalog/api/urls.py`;
- nintent's active API, GraphQL, model, and Braindump tests;
- `nctl/README.md` and relevant `nctl/docs/`;
- `nctl/src/nctl_core/nautobot.py`;
- `nctl/src/nctl_core/sources/desired.py`;
- `nctl/src/nctl_core/sources/braindump.py`;
- `nctl/src/nctl_core/lifecycle.py`;
- `nctl/src/nctl_core/braindump.py`;
- `nctl/src/nctl_core/reconcile/ledger.py`;
- `nctl/src/nctl_core/reconcile/executor.py`;
- their focused nctl tests; and
- every active source/configuration/current-documentation match found by the searches in
  Section 9.

Phase 0's frozen matrix is authoritative. Phase 2 must not retain an unused REST collection,
invent another GraphQL query, widen a writable field set, or independently revise the ownership
decisions.

### 2.2 Inherited state

Phase 1 changed nintent and nauto source but did not deploy it. Phase 2 is developed on top of those
commits and must preserve all Phase 1 Import/Analyze behavior. The disposable environment must
therefore load the exact combined Phase 1 plus Phase 2 nintent source, not the older package
currently installed in the live development containers.

No Phase 1 YAML apply or live Job run is needed to prove Phase 2. API fixtures may use synthetic
rows in a disposable database.

### 2.3 Allowed changes

Phase 2 may change:

- nintent REST serializers, ViewSets, router registration, IntentSource GraphQL registration,
  active tests, and current API documentation;
- nctl's `link_actual_node` read/confirmation path, focused tests, and current documentation;
- the superproject pointers for coordinated nintent/nctl commits;
- this plan and Phase 2 reports; and
- private evidence under `.local/interface-contract/p2/<timestamp>/`.

It may build and use a disposable Nautobot/PostgreSQL/Redis environment with isolated containers,
networks, volumes, database names, credentials, and ports. It may execute synthetic REST and
GraphQL mutations only against that disposable environment.

### 2.4 Prohibited actions

Phase 2 must not:

- PATCH, POST, PUT, or DELETE any live nintent, Nautobot, Job, JobHook, or actual-ledger object;
- run a live Import, Analyze, IPAM, Ingest, Seed, or other Nautobot Job;
- apply Phase 1's canonical YAML to the live database;
- rebuild or restart the live `nautobot-nautobot-1`, worker, or scheduler containers;
- connect a disposable test to the live Postgres, Redis, media volume, or port 8000;
- run `nctl reconcile --yes`, `nctl lifecycle`, or a Braindump write against the live URL;
- run Ansible actuation, nodeutils collection, or actual ingest;
- delete or alter a domain model, model field, or migration history;
- remove GraphQL registration from any model except `IntentSource`;
- change the fields selected by the pinned desired, actual, Braindump-list, or Braindump-show
  queries unless a verified framework incompatibility forces a plan amendment;
- add a per-node GraphQL query, REST fallback reader, generic CRUD client, generic API passthrough,
  or compatibility route;
- implement Phase 3's UI/form/route deletions;
- implement compute linking, compute drift, Proxmox actuation, or guest creation;
- change Job REST run/poll/artifact behavior, `/api/status/`, drift, planner classification,
  evidence schemas, SSH, observation, render, or actuation behavior unrelated to node linking;
- copy tokens, credentials, Braindump bodies, Alignment Review summaries, or raw private API
  responses into tracked files or reports; or
- push commits. The user owns pushes, and Phase 4 owns deployment.

### 2.5 Planning-time repository snapshot

Observed while this plan was authored on 2026-07-26:

| Repository | Revision | State |
|---|---|---|
| superproject | `cedba743d0fa83446b451d8a0c0cc70d76a48577` | clean before this plan was added |
| `nintent` | `185479d2217f7530249a3cc5e9187e11fd9a295f` | clean |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean |
| `nauto` | `2635e648469d6e6bad87af113f7427b878b0a387` | clean; retained Phase 1 state |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean; out of scope |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean; out of scope |

Static orientation found seven serializer `Meta.fields = "__all__"` assignments, twelve
GraphQL-registered nintent models, seven registered nintent REST ViewSets, one nctl domain
`rest_get` caller in `reconcile/ledger.py`, and three retained Job-protocol `rest_get` call sites
in `nctl_core/jobs.py`. Static `def test_` counts were 287 under nintent and 888 under nctl; these
are orientation signals, not substitutes for runner-collected counts.

Step 0 must recapture the exact revision tuple, staged/unstaged/untracked state, runner-collected
tests, active routes, and live read-only baseline. Preserve unrelated user changes and stop if an
in-scope path has an unexplained overlapping edit.

## 3. Scope and non-goals

### 3.1 In scope

- delete `DesiredServiceSerializer`, `DesiredEndpointSerializer`,
  `DesiredComputePlatformSerializer`, and `DesiredComputeInstanceSerializer`;
- delete their four ViewSets and router registrations;
- remove imports used only by those deleted API surfaces;
- retain exactly the node, Braindump, and Alignment Review REST collections;
- replace every retained serializer's `fields = "__all__"` with the explicit contract in
  Section 4;
- reject unknown, read-only, or operation-inappropriate mutation keys rather than silently
  dropping them;
- disable unowned detail and bulk methods, including node create/replace/delete and all collection
  bulk mutations;
- keep incidental REST GET only because the retained mutation ViewSets provide it;
- remove `@extras_features("graphql")` from `IntentSource` only;
- retain all other nintent GraphQL roots and the four pinned nctl queries;
- replace both `link_actual_node` REST reads with the pinned desired GraphQL reader;
- preserve node-link conflict protection and positive post-write confirmation;
- prove the current lifecycle and Braindump/review paths still use GraphQL around applicable
  writes;
- retain and classify Job-protocol REST reads/downloads and `/api/status/`;
- update active tests that currently require removed REST collections or broad node writes;
- run local, Nautobot-runtime, and cross-component disposable verification; and
- document and report the final route/method/field/read contract.

### 3.2 Explicitly retained

- all nintent domain models, fields, constraints, and migration history through `0016`;
- IntentSource ORM access by Import/Analyze and its existing human UI;
- GraphQL registration for the eleven consumer-backed models other than IntentSource;
- the exact desired, actual, Braindump-list, and Braindump-show query selections;
- DesiredService, DesiredEndpoint, DesiredComputePlatform, and DesiredComputeInstance GraphQL
  reads, strict YAML imports, ORM behavior, filters, tables, forms, and UI routes;
- framework-provided incidental GET on the three retained mutation collections;
- `nctl lifecycle` behavior and `nctl.braindump.*` public envelopes;
- `link_actual_node`'s candidate type, exact target scope, non-replacement rule, PATCH payload,
  action result, and operation evidence behavior;
- `NautobotClient.rest_get` for Job discovery/result/artifact lookup only;
- `rest_download` for FileProxy artifacts, REST POST for Job invocation, and `/api/status/`;
- Import, Analyze, IPAM, Seed, Ingest, and AI Resource Review behavior;
- Phase 1 source-controlled YAML and writer ownership;
- all current UI mutation surfaces until Phase 3;
- historical plans, reports, migrations, and operation artifacts; and
- the live AI Resource Auto Review JobHook and custom fields.

### 3.3 Out of scope

- deployment or live smoke tests;
- running the Phase 1 Import plan against live state;
- making the nintent UI read-only;
- deleting filters, forms, tables, templates, or UI routes merely because the corresponding REST
  collection is deleted;
- denying incidental REST GET with a separate custom read-denial layer;
- adding broad duplicate tests for REST reads already canonically covered through GraphQL;
- changing DesiredNode lifecycle vocabulary or link provenance vocabulary;
- adding optimistic-lock columns, ETags, API versions, or compatibility aliases;
- changing Braindump prose semantics, authorship rules, review freshness, output schemas, or
  non-executable handling;
- changing native Nautobot REST/UI behavior for Device, Cluster, VirtualMachine, Interface,
  VMInterface, IPAddress, Notes, custom fields, or other framework models;
- removing nctl REST helper methods that still have a classified Job/write caller;
- modularizing nctl or consolidating unrelated tests; and
- Phase 4 backup, maintenance-window, push, deployment, live data transition, and rollback.

## 4. Frozen target contract

### 4.1 Canonical GraphQL contract

The four Phase 0-pinned nctl query documents remain the only domain queries:

| Query | Current owner | Phase 2 rule |
|---|---|---|
| desired snapshot (`DESIRED_QUERY`) | `nctl_core.sources.desired` | unchanged; reused by lifecycle and node-link confirmation |
| actual snapshot (`ACTUAL_QUERY`) | `nctl_core.sources.actual` | unchanged |
| Braindump list (`LIST_QUERY`) | `nctl_core.sources.braindump` | unchanged |
| Braindump show (`SHOW_QUERY`) | `nctl_core.sources.braindump` | unchanged |

Step 0 and final verification must recompute the normalized SHA-256 digests using Phase 0's method.
All four must match [Phase 0 report7](../p0/report7.md) unless the plan is explicitly amended.

`IntentSource` loses only its GraphQL decorator. The model, fields, relations, Import/Analyze ORM
readers, list/detail UI, and migration history remain. Runtime introspection must prove
`intent_source` and `intent_sources` are absent while every root used by the four pinned queries
still validates and returns its selected fields.

### 4.2 REST route and method contract

`HEAD` and `OPTIONS` may remain as normal protocol/framework methods. The domain contract is:

| Collection/endpoint | Allowed domain methods | Disallowed methods |
|---|---|---|
| `nodes/` | GET | POST, PUT, PATCH, DELETE, including bulk mutation |
| `nodes/{id}/` | GET, PATCH | POST, PUT, DELETE |
| `braindumps/` | GET, POST | PUT, PATCH, DELETE, including bulk mutation |
| `braindumps/{id}/` | GET, PATCH, DELETE | POST, PUT |
| `alignment-reviews/` | GET, POST | PUT, PATCH, DELETE, including bulk mutation |
| `alignment-reviews/{id}/` | GET, PATCH, DELETE | POST, PUT |
| `services[/...]` | none; route absent | all |
| `endpoints[/...]` | none; route absent | all |
| `compute-platforms[/...]` | none; route absent | all |
| `compute-instances[/...]` | none; route absent | all |

Nautobot's base `NautobotModelViewSet` includes bulk list PATCH and DELETE mixins. Merely setting
`http_method_names` is therefore insufficient: it would either leave an unowned bulk PATCH or
disable the required detail PATCH. Implement explicit action-level restrictions (and truthful
metadata/schema exposure where the framework permits) so list and detail behavior matches the
table. A disallowed existing route must return `405 Method Not Allowed`; a deleted collection must
return `404 Not Found` and have no reversible router name.

Incidental GET is not a canonical nctl read path. Test only that a retained collection can return
its contracted representation and permissions; do not create a second REST read parity suite.

### 4.3 Serializer field and write contract

The exact response and mutation fields are:

| Serializer | Response fields | Writable fields |
|---|---|---|
| DesiredNode | `id`, `name`, `slug`, `node_type`, `lifecycle`, `role`, `realized_device`, `realized_device_source`, `created`, `last_updated` | `lifecycle`, `realized_device`, `realized_device_source` |
| BrainDumpDocument | `id`, `title`, `body`, `authorship`, `created`, `last_updated` | `title`, `body`, `authorship` |
| AlignmentReview | `id`, `braindump`, `summary`, `created`, `last_updated` | create: `braindump`, `summary`; patch: `summary` only |

`accepted_actual_types`, `expected_spec`, `intent_source`, descriptions, notes, custom fields,
relationships, and other framework/model fields are not needed by a retained REST writer and are
omitted from the final REST representation. They remain available through their approved
GraphQL/UI/YAML/ORM contracts where applicable.

The implementation must distinguish:

- a response field that is read-only;
- a field writable for create but not update;
- an allowed writable field with an invalid value; and
- an unknown field.

For mutation requests, every supplied key outside the operation's exact writable set must produce
a deterministic `400` error naming the rejected key, with zero database change. It is not
sufficient for DRF to ignore an unknown/read-only key and return success. In particular:

- node PATCH with `name`, `slug`, `node_type`, `role`, `notes`, an unknown key, or a timestamp is
  rejected;
- Alignment Review PATCH with `braindump`, even when it names the existing parent, is rejected;
- system fields such as `id`, `created`, and `last_updated` are never client-writable;
- node link/source presence remains symmetric;
- clearing `realized_device` also clears its source through the serializer's existing contract;
- a supplied link without an explicit source retains the existing intentional `override`
  default, while nctl's derived linker continues to supply `derived` explicitly;
- Braindump and review accepted text is preserved byte-for-byte, with whitespace-only content
  rejected as today; and
- partial PATCH preserves every omitted writable field.

### 4.4 Write-confirmation contract

All applicable preconditions and every success confirmation use GraphQL:

| Operation | Before write | Write | Positive confirmation |
|---|---|---|---|
| lifecycle no-op/change | desired GraphQL by slug | none or node PATCH | desired GraphQL by slug after PATCH |
| link actual node | desired GraphQL by immutable node ID | node PATCH | fresh desired GraphQL by the same ID |
| Braindump create | local input validation; no server identity exists yet | Braindump POST | Braindump-show GraphQL by returned ID |
| Braindump update | Braindump-show GraphQL | Braindump PATCH | Braindump-show GraphQL exact changed fields |
| Braindump delete | Braindump-show GraphQL | Braindump DELETE | Braindump-show GraphQL returns null |
| review create/replace | Braindump-show GraphQL and current review relation | review POST/PATCH | Braindump-show GraphQL exact summary |
| review delete | Braindump-show GraphQL and current review relation | review DELETE | Braindump-show GraphQL shows no review |

Braindump create is the only natural case without a server-side GraphQL pre-read because its UUID
does not exist before POST. The returned REST representation is used only to obtain the new UUID;
it is not accepted as confirmation.

Any absent target, ambiguous identity, conflicting current link, rejected write, GraphQL transport
failure, GraphQL validation error, missing post-write row, mismatched value, or wrong provenance
fails closed. A failure after a successful PATCH must remain recorded as a failed action with
mutation/progress evidence preserved by the existing executor boundary.

### 4.5 `link_actual_node` implementation contract

Use `fetch_desired_snapshot()` and its existing `DesiredNode` transport model. Do not define a
second node-only GraphQL document.

Before PATCH:

1. validate the action kind, target ID, candidate object type, and candidate ID as today;
2. fetch the pinned desired snapshot;
3. resolve by immutable node UUID, not by name or REST representation;
4. require exactly one match and require its slug to agree with the action target when the target
   supplies a slug;
5. reject if `realized_device_id` or its source already indicates an existing/partial link; and
6. perform no PATCH after any failed precondition.

Write exactly:

```json
{
  "realized_device": "<Device UUID>",
  "realized_device_source": "derived"
}
```

After PATCH:

1. ignore the REST response body as proof;
2. fetch a fresh pinned desired snapshot;
3. resolve the same immutable DesiredNode UUID;
4. require `realized_device_id` to equal the candidate UUID;
5. require `realized_device_source` to equal `derived`; and
6. return the existing `LinkActualNodeResult` only after both assertions pass.

Retain typed, bounded action errors. Error names may be clarified for GraphQL identity failures,
but public action evidence must not include full GraphQL payloads, tokens, or unrelated desired
rows.

### 4.6 Remaining REST helper classification

At phase completion, every `rest_get` in active nctl source must be one of:

- Job lookup by name;
- JobResult polling;
- FileProxy lookup; or
- the helper method definition itself.

`rest_download` remains FileProxy protocol. `rest_post` remains Job invocation plus retained
Braindump/review create. `rest_patch` remains node lifecycle/link and retained prose updates.
`rest_delete` remains retained prose deletion. `/api/status/` continues to use the dedicated
health/version probe.

Job protocol records are operational API resources, not domain read models. Do not replace them
with GraphQL or change their behavior in this phase.

## 5. Implementation procedure

### Step 0 — Recapture the boundary and establish evidence

1. Create `.local/interface-contract/p2/<timestamp>/` with directory mode `0700` and evidence files
   mode `0600`.
2. Record timestamp/timezone, tool versions, governing documents reviewed, revisions, submodule
   pointers, branches, staged/unstaged/untracked state, and runner-collected test counts.
3. Recompute all four frozen GraphQL query digests.
4. Re-run the roadmap and Section 9 searches across active code, tests, configuration, Makefiles,
   wrappers, and current documentation; classify active versus historical references.
5. Read-only inspect the currently installed live nintent revision, migration state, REST router
   names, `OPTIONS`, GraphQL roots, and aggregate row counts. Record no prose bodies/summaries,
   tokens, raw custom-field values, or complete API payloads.
6. Confirm no live Job is pending/running and do not start one.
7. Inspect the Nautobot 3.1.3 ViewSet/router behavior used by the installed environment, including
   bulk list PATCH/DELETE mapping, so the method restriction is implemented against normative
   framework behavior.
8. Define a new disposable project/database/network/volume/port tuple with no live resource
   reference.

Gate: implementation starts from one explained revision tuple, the Phase 0 frozen contract still
matches active callers, and the test environment cannot reach live state.

### Step 1 — Freeze executable tests for the final contract

Add or revise tests before changing implementation:

1. Assert exactly three router registrations and exact route names.
2. Assert every removed collection name is non-reversible and its list/detail URL returns 404.
3. Assert node list/detail GET returns exactly the explicit representation.
4. Assert node detail PATCH accepts each of the three owned fields and valid combinations.
5. Assert node POST, detail PUT/DELETE, list bulk PATCH, and list bulk DELETE return 405.
6. Assert node PATCH rejects every response-only field and an arbitrary unknown field with 400 and
   no row change.
7. Assert invalid lifecycle and inconsistent link/source values return 400 with no row change.
8. Assert Braindump/review list/detail methods match Section 4.2, including no PUT or bulk mutation.
9. Assert their response fields and operation-specific writable fields are exact.
10. Assert Braindump/review unknown, system, and update-inappropriate fields fail rather than being
    ignored.
11. Retain byte-preserving prose, validation, uniqueness-race, cascade, and partial-update tests.
12. Assert IntentSource GraphQL roots fail schema validation while its ORM and retained UI routes
    still load.
13. Assert all eleven retained GraphQL model roots, especially compute, remain present.
14. Rewrite `test_reconcile_ledger` to prove GraphQL-before/PATCH/GraphQL-after ordering, exact
    payload, conflict/no-write behavior, missing/mismatched identity, post-write mismatch, and
    GraphQL failure.
15. Retain lifecycle and Braindump nctl tests, strengthening them where necessary to assert that no
    domain REST GET occurs.
16. Remove or rewrite active tests whose purpose is to preserve service/endpoint/compute REST or
    broad node create/update behavior; do not leave skipped compatibility assertions.

Gate: tests describe the frozen Phase 2 contract and fail against the broad pre-Phase-2
implementation for the intended reasons.

### Step 2 — Contract nintent REST and IntentSource GraphQL

1. Replace the three retained serializer `fields = "__all__"` assignments with the exact explicit
   field lists.
2. Encode read-only, create-only, and update-writable fields explicitly.
3. Add strict mutation-key validation before normal DRF field processing so disallowed keys cannot
   be silently ignored.
4. Preserve node link/source validation and exact prose handling.
5. Delete the four unused serializers and all imports/docstrings used only by them.
6. Delete the four unused ViewSets and filter/model imports used only by those ViewSets.
7. Remove their four router registrations.
8. Restrict retained ViewSet actions to the list/detail matrix, explicitly disabling Nautobot bulk
   mutation paths and PUT.
9. Remove the GraphQL decorator from `IntentSource` only.
10. Do not edit a model field or generate a migration.

Gate: static imports load, only three REST collections register, their effective actions and
writable keys are exact, and only IntentSource changes GraphQL exposure.

### Step 3 — Move node-link reads and confirmation to GraphQL

1. Replace `_get_node()` and both REST GET calls in `reconcile/ledger.py` with a helper over
   `fetch_desired_snapshot()`.
2. Resolve the node by immutable UUID and validate the target slug.
3. Preserve the no-clear/no-replace precondition and strengthen partial link/source inconsistency
   handling.
4. Keep the exact two-field derived-link PATCH.
5. Perform a fresh GraphQL fetch after PATCH and confirm both ID and source.
6. Do not trust or parse the PATCH response body beyond HTTP success/failure.
7. Keep `LinkActualNodeResult` and executor evidence shape stable.
8. Ensure post-mutation read failure remains a failed mutated action rather than erasing the
   attempted mutation from round evidence.
9. Delete now-unused REST serialization normalization such as `_linked_id`.
10. Re-run all nctl `rest_get` searches and classify only Job-protocol results as retained.

Gate: no nctl domain object is read through REST, no new GraphQL query exists, and the linker fails
closed on every unconfirmed state.

### Step 4 — Local and static verification

Run at minimum:

```bash
cd nintent
python3 -m unittest discover -s nautobot_intent_catalog/tests

cd ../nctl
uv run pytest

cd ..
git diff --check
git -C nintent diff --check
git -C nctl diff --check
```

Also:

1. compile edited Python modules;
2. import the Django-free test modules successfully;
3. recompute the four pinned query digests;
4. inspect router source for exactly three registrations;
5. assert no retained serializer uses `fields = "__all__"`;
6. assert no deleted serializer/ViewSet is imported;
7. classify every remaining `rest_get`;
8. confirm no model/migration, Phase 1 import/analyze, nauto, nodeutils, or ansible_agdev file
   changed; and
9. record exact collected test counts and failures.

Gate: local suites pass and the diff is limited to Phase 2 scope.

### Step 5 — Disposable Nautobot API and GraphQL proof

Use an isolated Nautobot 3.1.3 environment built from the exact local nintent source. It must have
new Postgres/Redis containers and volumes, no live external host references, and no production
token or private data.

In that environment:

1. initialize Nautobot and apply nintent migrations through `0016`;
2. prove `makemigrations nautobot_intent_catalog --check --dry-run` reports no changes;
3. run the Nautobot-runtime nintent test modules against their disposable test database;
4. introspect GraphQL and prove IntentSource roots are absent and every retained root is present;
5. execute the complete route/method matrix with a broadly permitted synthetic test user;
6. prove removed routes are 404, not permission-hidden 403;
7. prove disallowed methods are 405 and never mutate;
8. prove rejected fields are 400 and never mutate;
9. prove exact response/writable field metadata, including create-only review ownership;
10. exercise valid node lifecycle/link/source PATCHes and valid Braindump/review CRUD;
11. prove incidental GET does not expose omitted unowned fields;
12. verify no migration, Job registration, UI route, or Phase 1 Job contract changed; and
13. retain only sanitized route names, status codes, field names, aggregate counts, and synthetic
    fixture values as evidence.

Gate: the real framework proves the contracted route/method/serializer/GraphQL behavior, not only
mocked unit tests.

### Step 6 — Cross-component nctl confirmation and non-repetition proof

Point an nctl test harness at the same disposable API using a disposable token and synthetic,
non-private rows.

Prove:

1. `nctl lifecycle` reads through GraphQL, PATCHes only lifecycle, refetches through GraphQL, and
   reports the confirmed state; repeat is a no-write no-op.
2. A synthetic unlinked DesiredNode and uniquely matching Device produce
   `actual_node_not_linked`.
3. The real planner produces the expected `link_actual_node` action for that exact node/candidate.
4. The real ledger executor performs GraphQL-before, exact PATCH, and GraphQL-after.
5. A fresh snapshot/drift/plan shows the link and does not repeat `link_actual_node`.
6. Pre-existing link, wrong target identity, rejected PATCH, and post-PATCH GraphQL mismatch/read
   failure all fail closed with no false success.
7. Braindump create/update/delete and review create/replace/delete use their real nctl operations
   and are confirmed through GraphQL; repeat/no-op behavior remains truthful where defined.
8. The four removed REST collections are never called by nctl.
9. Job lookup/run/poll/artifact protocol tests still pass unchanged.
10. No Ansible, nodeutils, IPAM Job, actual ingest, or live operation is invoked.

The node-link proof must assert positive evidence that drift classification, planning, the intended
action, the exact target/candidate, the PATCH, and the fresh non-repetition check all occurred. An
empty action list or an already-linked initial fixture does not exercise the path.

Gate: all four retained writer families work across the exact nintent/nctl contract, and the
changed reconciler proves a real state transition and non-repetition.

### Step 7 — Documentation, compatibility searches, and schema audit

1. Update nintent current documentation to state that GraphQL is the canonical domain read path.
2. Document only the three retained REST mutation collections, exact methods, writable fields,
   incidental GET status, and explicit rejection behavior.
3. Remove current instructions that query/write services, endpoints, or compute objects through
   REST.
4. Update nctl documentation only where it fails to state node-link GraphQL precondition and
   confirmation or incorrectly describes broad ViewSets.
5. Preserve truthful UI documentation until Phase 3; do not claim the current UI is read-only
   before that phase lands.
6. Recheck the VM Phase 3 plan. Its existing interface-contract supersession note remains
   authoritative; edit only if an active instruction still directs Phase 3 to use a removed REST
   collection.
7. Do not rewrite historical reports. Classify their removed-surface references as history.
8. Re-run all required searches and query digests.
9. Confirm schema remains through `0016`, with no migration file or model-field diff.

Gate: every active instruction matches the final Phase 2 contract, while historical evidence and
Phase 3's still-current UI behavior remain truthful.

### Step 8 — Coordinated commits and final report

1. Record before/after REST registrations, serializers, methods, writable fields, GraphQL roots,
   `rest_get` classifications, test counts, and source-line measurements.
2. Record local, runtime, and cross-component results, including every omitted or substituted
   check.
3. Commit nintent and nctl independently at reviewable boundaries.
4. Update both submodule pointers in a coordinated superproject commit. Do not push.
5. Write `devdocs/big/interface_contract/p2/report.md` and per-step reports as useful.
6. Use `complete`, `implemented, not deployed`, `partially complete`, or `blocked` according to the
   evidence.

The normal successful Phase 2 status is **implemented, not deployed**: the implementation and
disposable proof are complete, but the matched live rollout is intentionally deferred to Phase 4.
State separately that Phase 2's own implementation scope is complete.

## 6. Required verification matrix

| Area | Required positive proof |
|---|---|
| REST registration | exactly nodes, Braindumps, and Alignment Reviews remain |
| Removed routes | all four list/detail route families are non-reversible and return 404 |
| Node methods | list GET and detail GET/PATCH only; create/PUT/delete/bulk mutation return 405 |
| Node fields | exact response list; exactly three writable fields |
| Node rejection | unowned/read-only/unknown keys return 400 and cause zero writes |
| Node validation | lifecycle and link/source constraints fail closed |
| Braindump methods | collection GET/POST and detail GET/PATCH/DELETE; no PUT/bulk mutation |
| Review methods | collection GET/POST and detail GET/PATCH/DELETE; parent create-only |
| Prose fields | exact explicit fields, byte preservation, validation, partial update, cascade |
| IntentSource | ORM/Jobs/UI retained; GraphQL singular/plural roots absent |
| Retained GraphQL | all four pinned queries validate; normalized digests unchanged |
| Lifecycle | GraphQL before, exact PATCH, GraphQL after, repeat no-op |
| Node link | real drift/plan/action, GraphQL before/after, exact derived PATCH, no repetition |
| Link conflicts | existing/partial/wrong identity and failed confirmation never report success |
| Braindump writes | POST/PATCH/DELETE positively GraphQL-confirmed |
| Review writes | create/replace/delete positively GraphQL-confirmed, race behavior retained |
| nctl REST reads | only Job lookup/result/FileProxy protocol remains |
| Job/status protocol | run/poll/download and `/api/status/` unchanged |
| Schema | migrations stay through `0016`; dry-run makemigrations clean |
| Phase 1 regression | Import/Analyze/YAML tests and Job discovery unchanged |
| Isolation | disposable proof cannot reach live DB/Redis/media/API |
| Live safety | no live mutation, Job run, rebuild, restart, or actuation |
| Secrets/prose | no credential or private prose enters tracked or report evidence |

## 7. Report requirements

The final report must include:

1. status and explicit deployed/not-deployed statement;
2. exact start/end repository tuple and dirty state;
3. private evidence location and redaction statement;
4. before/after REST registration, method, serializer, and GraphQL-root tables;
5. the final nctl REST helper classification;
6. unchanged pinned-query digests;
7. local and Nautobot-runtime test results;
8. disposable route/method/field results;
9. node-link planner/executor/non-repetition evidence;
10. lifecycle and prose-writer confirmation evidence;
11. migration and Phase 1 regression results;
12. active/historical search classification;
13. deviations, omitted checks, and explicitly deferred work;
14. non-mutation proof for the live environment; and
15. a Phase 3/Phase 4 handoff.

Do not include a live token, raw API authorization header, Braindump body, Alignment Review
summary, full ObjectChange payload, or credential-bearing configuration.

## 8. Failure handling and rollback

### 8.1 Before disposable mutation

If tests, serializer design, route restriction, query digest, or worktree scope is wrong:

- do not start disposable mutation;
- correct the implementation and rerun the static gate;
- leave live services and data untouched; and
- report the exact failing contract if work stops.

If an in-scope GraphQL query field unexpectedly must change, stop and amend this plan plus the
frozen digest manifest before implementation. Do not silently change the pinned consumer contract.

### 8.2 Disposable-environment failure

If a disposable API or cross-component proof fails:

1. preserve sanitized logs, status/field matrices, operation events, and aggregate before/after
   state;
2. determine whether any synthetic mutation committed;
3. recreate the disposable database from a known empty state rather than manually compensating;
4. fix the code and rerun the complete relevant transition, including non-repetition; and
5. remove only the explicitly named disposable containers, networks, volumes, credentials, and
   temporary files after evidence capture.

Never compensate for a disposable failure by modifying live state.

### 8.3 Post-PATCH confirmation failure

A failed GraphQL confirmation after a successful disposable PATCH means mutation may have occurred:

- record the attempted action and mutation uncertainty truthfully;
- fetch sanitized state through the canonical GraphQL path if possible;
- do not retry blindly or trust the REST response body;
- reset the disposable fixture before rerunning; and
- retain regression coverage for the failure.

The production executor's existing partial-progress semantics must continue to preserve evidence
after side effects.

### 8.4 Source rollback

No live data rollback is required because Phase 2 does not deploy. Before Phase 4, source rollback
means restoring the coordinated prior nintent/nctl commits and superproject pointers.

Do not roll back by restoring removed collections, `fields = "__all__"`, broad node methods,
IntentSource GraphQL, or REST confirmation reads as compatibility paths inside the new revisions.

## 9. Required searches

Search active code, tests, configuration, and current documentation for at least:

```text
DesiredServiceSerializer
DesiredEndpointSerializer
DesiredComputePlatformSerializer
DesiredComputeInstanceSerializer
DesiredServiceViewSet
DesiredEndpointViewSet
DesiredComputePlatformViewSet
DesiredComputeInstanceViewSet
router.register("services"
router.register("endpoints"
router.register("compute-platforms"
router.register("compute-instances"
fields = "__all__"
rest_get
_get_node
_linked_id
@extras_features("graphql")
intent_source
intent_sources
/api/plugins/intent-catalog/services
/api/plugins/intent-catalog/endpoints
/api/plugins/intent-catalog/compute-platforms
/api/plugins/intent-catalog/compute-instances
desiredservice-list
desiredendpoint-list
desiredcomputeplatform-list
desiredcomputeinstance-list
bulk_update
bulk_partial_update
bulk_destroy
http_method_names
```

Every remaining `rest_get` caller must be classified as Job lookup, JobResult polling, FileProxy
lookup, or the helper definition. Every remaining `fields = "__all__"` in an active nintent REST
serializer blocks completion. Every remaining deleted serializer/ViewSet/router symbol in active
runtime code, current tests, or current documentation blocks completion.

Every remaining `@extras_features("graphql")` must correspond to one of the eleven retained
consumer-backed models. IntentSource's decorator must be absent, while references to the
IntentSource model in Import/Analyze/UI code remain expected.

Expected removed-surface references are limited to:

- the parent roadmap, refactoring vision, and this plan;
- Phase 0/1 and other historical plans/reports explicitly treated as history;
- normal Git history; and
- the Phase 2 final report explaining the contraction.

Historical reports are not edited to make old interfaces disappear retroactively.

## 10. Definition of done

Phase 2 is complete in its implementation scope only when:

- nintent registers exactly three REST collections;
- service, endpoint, compute-platform, and compute-instance REST serializers, ViewSets, routes,
  imports, active tests, and current documentation are absent;
- node list/detail methods are exactly bounded, including no create, PUT, delete, or bulk mutation;
- Braindump and review methods retain only the nctl-used create/PATCH/delete operations and no
  PUT/bulk mutation;
- all three serializers have explicit response fields and exact writable fields;
- unknown, read-only, and operation-inappropriate mutation keys are rejected rather than ignored;
- IntentSource is absent from GraphQL but unchanged for ORM Jobs and UI;
- every consumer-backed GraphQL root and all four pinned query selections remain;
- normalized pinned-query digests are unchanged;
- `link_actual_node` performs no domain REST GET and uses GraphQL before and after the exact PATCH;
- its real drift/planner/executor transition is positively exercised and a fresh plan does not
  repeat the link action;
- lifecycle, Braindump, and review writers remain positively GraphQL-confirmed;
- every nctl domain read is GraphQL and every remaining REST read has a classified Job/status
  protocol purpose;
- Job protocol, `/api/status/`, Phase 1 Import/Analyze, IPAM, nauto, UI, migrations, drift,
  evidence, SSH, observation, rendering, and actuation remain unchanged;
- local tests, Nautobot-runtime tests, route/method/field checks, migration checks, strict
  searches, and disposable cross-component proofs pass;
- live Nautobot and cluster state were not mutated, rebuilt, restarted, or actuated;
- no secret or private prose appears in tracked files or reports;
- coordinated nintent/nctl commits and superproject pointers exist without being pushed; and
- the final report states accurately that implementation is complete but deployment remains
  Phase 4 work.

The strongest completion evidence is not the number of deleted classes. It is a real retained
writer reaching only its owned mutation, a canonical GraphQL refetch proving the resulting state,
and a fresh computation showing that the same action is no longer required.
