# Remove Unused Surfaces Phase 3 Implementation Plan: Remove the nintent Cache and Dashboard Links

Parent: [roadmap.md](../roadmap.md) — Phase 3.

Predecessor: [Phase 2 final report](../p2/report8.md) — `complete`.

Status: proposed; local nintent implementation, disposable-database proof, and matched-revision
preparation only. The live migration and coordinated deployment remain Phase 5 work.

## 1. Goal and required transition

Remove the nintent database, API, Nautobot UI, navigation, URL, plugin-setting, and development
configuration residue that belonged exclusively to the deleted nctl dashboards.

Phase 2 already removed the last nctl writer and reader of this data. Phase 3 therefore removes
the now-ownerless derived cache instead of assigning it a replacement writer.

The Phase 3 transition is:

```text
before
  DesiredNode
    + reconciliation_status
    + reconciliation_checked_at
  DesiredService
    + reconciliation_status
    + reconciliation_checked_at
  + status filters and list-table badges
  + status/timestamp detail rows
  + dashboard URL in detail-view context
  + nctl Dashboard navigation and redirect route
  + dashboard_url App default and development setting
  + REST and GraphQL schema exposure inherited from the model fields

after Phase 3
  DesiredNode and DesiredService contain confirmed desired-state fields only
  + no persisted reconciliation cache
  + no reconciliation filter, badge, detail row, dashboard context, link, or redirect
  + no dashboard_url plugin/deployment setting
  + REST and GraphQL retain the normal node/service resources but omit the four removed fields
  + current status is obtained from nctl drift
  + operation-specific status is obtained from reconcile artifacts and nctl ops
```

The schema transition is a new Django migration:

```text
0014_braindump_exchange_diary
  -> 0015_compute_platform_instance_and_endpoint_mac
  -> 0016_remove_reconciliation_dashboard_surfaces
       - DesiredNode.reconciliation_status
       - DesiredNode.reconciliation_checked_at
       - DesiredService.reconciliation_status
       - DesiredService.reconciliation_checked_at
```

Migration `0009_reconciliation_status.py` and its historical dependency from `0010` remain
unchanged. `0016` discards disposable cache values without translating them. It must not add a
replacement table, custom field, JSON blob, local snapshot, Job, writer, alias, or compatibility
property.

The observable outcome is:

- the four fields and duplicated reconciliation constants/choices are absent from the current
  models;
- the four physical columns are absent after applying `0016` to a disposable database;
- node and service list/detail pages still render without reconciliation status rows;
- node and service REST/GraphQL reads still work but no longer expose the removed fields;
- the dashboard route, navigation item, links, setting, and development URL are absent;
- Braindump/Alignment Review UI, REST, GraphQL, storage, and authorship boundaries are unchanged;
  and
- exact nintent/nctl revisions are ready for the later coordinated deployment.

This is a coordinated breaking deletion. Do not retain deprecated properties, serializer aliases,
hidden URL names, ignored settings fallbacks, empty status placeholders, or migration-time data
copying.

## 2. Governing inputs and current baseline

Before implementation, re-read:

- root `README.md`;
- root `README_DEV.md`;
- `.local/localenv_memo.md`;
- `devdocs/vision/refactor/vision.md`;
- the parent roadmap;
- [Phase 0 plan](../p0/plan.md), especially §3 and §4.7;
- [Phase 0 final report](../p0/report9.md), especially the migration contract and coordinated
  sequence;
- [Phase 2 plan](../p2/plan.md), especially its Phase 3 boundary;
- every Phase 2 report, treating [report8.md](../p2/report8.md) as authoritative;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md` and latest VM Phase 3 reports;
- `nintent/README.md`, `nintent/README_DEV.md`, and `nintent/README_QUICK.md`;
- `nintent/nautobot_intent_catalog/migrations/0009_reconciliation_status.py`;
- `nintent/nautobot_intent_catalog/migrations/0015_compute_platform_instance_and_endpoint_mac.py`;
- every current nintent source/template file named in §5; and
- the current nintent test suite and Nautobot-runtime test conventions.

Phase 0's removal/migration contract and coordinated sequence are authoritative. Phase 2's final
report is the direct handoff: nctl has no dashboard command, dashboard schema/config, HTML
renderer, cache PATCH, or reconcile coupling, while nintent still has all four cache fields and
their presentation residue.

### 2.1 Planning-time repository snapshot

Observed while this plan was written on 2026-07-25:

| Repository | Revision | State relevant to Phase 3 |
|---|---|---|
| superproject | `02c466cd0493056a85b04ea259924c8a59b1ee54` | clean before this plan was added |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean; Phases 1–2 complete |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean; VM Phase 3 schema work present, cache residue unchanged |

This snapshot is orientation only. Step 0 must recapture revisions, upstream state, and dirty-file
ownership. Preserve unrelated user changes if any repository has moved.

The active VM Phase 3 latest complete implementation report is `report3.5.md` (its Step 5);
VM Step 6 has not started. The frozen coordinated order remains:

```text
remove_unused_surfaces Phase 3
  -> VM Phase 3 Step 6
  -> remove_unused_surfaces Phase 4 + VM Phase 3 Step 7
  -> one maintenance window applying 0015 then 0016 with matching nctl
  -> VM Phase 3 Step 8+ and remove_unused_surfaces Phase 5
```

Do not let this phase absorb VM desired-MAC/dnsmasq behavior or deploy either migration early.

### 2.2 Planning-time live baseline

Read-only checks while this plan was written confirmed:

- all three Nautobot containers are healthy;
- the running Nautobot instance has nintent migrations through `0014` applied;
- local migrations `0015` and the planned `0016` are not installed live;
- the installed `nautobot-intent-catalog` distribution is `0.9.0`;
- its installed Git commit remains
  `ad9d36397d23c269ad748e13acbccc532fa29f52`; and
- local nintent source is not mounted into the container, matching
  `.local/localenv_memo.md`.

Phase 0 recorded five DesiredNodes with a nonblank cached status and checked timestamp, plus one of
six DesiredServices with a nonblank cached status and checked timestamp. Step 0 must repeat only
aggregate read-only counts because these values may have changed. Do not copy row prose, dashboard
content, authentication headers, or secret values into evidence.

No live rebuild, migration, setting edit, cache-row write, Job, desired-state mutation, or
Nautobot restart belongs to Phase 3.

### 2.3 Current implementation and test baseline

At the planning-time nintent revision:

- local Django-free tests pass: **187 tests**;
- tracked nintent non-test Python is 9,665 lines;
- tracked nintent tests are 3,633 lines;
- tracked templates are 1,353 lines;
- there are 15 numbered migrations plus `migrations/__init__.py`;
- `DesiredNode` and `DesiredService` each duplicate four reconciliation constants, one choices
  tuple, and two fields;
- `DesiredNodeFilterSet` and `DesiredServiceFilterSet` expose
  `reconciliation_status`;
- both list tables declare and render a reconciliation badge column;
- both detail templates render status and checked-at rows, plus an optional dashboard link;
- both object views inject `dashboard_url`;
- `views.dashboard_redirect` reads the plugin setting and performs the external redirect;
- the main URL configuration exposes `dashboard/` as `dashboard_redirect`;
- navigation conditionally appends `nctl Dashboard` to Operational Tools;
- `IntentCatalogConfig.default_settings` contains only `dashboard_url`;
- the development `PLUGINS_CONFIG` contains only the concrete dashboard URL;
- `DesiredNodeSerializer` and `DesiredServiceSerializer` use `fields = "__all__"`, so model-field
  removal automatically contracts REST output;
- `@extras_features("graphql")` on both models similarly makes model-field removal contract the
  generated GraphQL schema; and
- current tests contain no focused positive proof for removal of these fields/surfaces.

The line/test measurements are diagnostic only. Completion is defined by the migration and
positive retained-path proofs, not by a deletion quota.

## 3. Scope, non-goals, and authority boundary

### 3.1 In scope

- remove all eight duplicated reconciliation constants/choice references from the two models;
- remove the four current model fields;
- add migration `0016_remove_reconciliation_dashboard_surfaces.py` directly after `0015`;
- preserve `0009` and all applied migration history unchanged;
- remove reconciliation-status fields from node/service FilterSet metadata;
- remove both status columns, render methods, shared badge helper, badge mapping, and imports used
  only by the badge;
- remove status/timestamp/dashboard-link rows from both detail templates;
- remove dashboard extra-context methods, setting resolver, redirect view, URL route, and imports
  used only by the redirect;
- remove conditional dashboard navigation and setting access;
- remove the `dashboard_url` App default;
- remove the dashboard-writer explanation from the DesiredService serializer docstring without
  deleting the serializer or its ViewSet;
- remove `dashboard_url` from local development Nautobot configuration;
- add focused Nautobot-runtime model/filter/table/template/URL/navigation/REST/GraphQL checks;
- prove `0015 -> 0016` against a disposable PostgreSQL database without touching the live
  `nautobot` database;
- prove ordinary DesiredNode/DesiredService UI and API reads remain usable;
- rerun and preserve Braindump/Alignment Review tests;
- run current-source deletion searches and classify every expected historical/test/documentation
  exception;
- prepare exact matched nintent/nctl and rollback revision tuples;
- ask the user to push the nintent commit; never push on the user's behalf; and
- produce one final Phase 3 report.

### 3.2 Retained owners and surfaces

| Concern | Owner/surface retained after Phase 3 |
|---|---|
| Fresh convergence status | `nctl drift`, human text, and `nctl.drift.v1` JSON |
| Per-operation result | reconcile JSONL and artifact directory |
| Operation history | `nctl ops list/show` |
| Desired node/service storage | nintent `DesiredNode` / `DesiredService` |
| Desired node/service REST | existing ViewSets and routes, with the four fields absent |
| Desired node/service GraphQL | existing `@extras_features("graphql")` registration |
| Desired node/service UI | existing list/detail/edit/delete views without status cache presentation |
| VM compute schema | VM Phase 3's `0015` models, fields, UI, API, GraphQL, YAML, and nctl contracts |
| Braindump semantic Ground Truth | `BrainDumpDocument` and user/agent workflow |
| Current Alignment Review | `AlignmentReview` and user/agent workflow |
| Actual ledger and observations | Nautobot, nodeutils, and nauto |
| Live migration/rebuild authority | user/operator in Phase 5 |

The normal node/service REST endpoints remain because agents and humans still use them for desired
state. GraphQL registration remains because nctl reads desired state there. Removing a field used
by a retired dashboard does not authorize deleting a shared resource.

### 3.3 Out of scope

- editing or deleting migration `0009_reconciliation_status.py`;
- rewriting `0010` merely because it depends on `0009`;
- rewriting migration `0015`;
- translating cache values into another store;
- preserving cache values across rollback without the required database backup;
- changing DesiredNode/DesiredService REST or GraphQL ownership generally;
- deleting REST ViewSets/routes or GraphQL registration;
- changing forms that already omit the cache fields;
- changing desired-state semantics, validation, YAML import, Jobs, IPAM reconciliation, drift,
  planner, render, SSH, or Ansible behavior;
- implementing VM desired-MAC/dnsmasq behavior owned by VM Phase 3 Step 6;
- changing the compute models or endpoint MAC contract introduced by `0015`;
- changing Braindump/Alignment Review fields, prose rendering, routes, APIs, authorship, or
  non-executable boundary;
- updating root/nintent READMEs and active cross-initiative roadmaps, which are the repository-wide
  Phase 4 documentation pass;
- rewriting historical reports to pretend dashboard/cache behavior never existed;
- deleting the generated `~/.local/state/nctl/dashboard` directory, which remains Phase 5 work;
- rebuilding/restarting live Nautobot;
- applying `0015` or `0016` to the live database;
- running live desired writes, Jobs, reconcile apply, Ansible, or host actuation; and
- pushing any repository.

The current nintent READMEs intentionally remain temporarily stale during this code phase. They
must be classified as Phase 4 work, not silently treated as clean deletion-search results.

## 4. Frozen Phase 3 contracts

### 4.1 Model and migration contract

After Phase 3, neither `DesiredNode` nor `DesiredService` has:

```text
RECONCILIATION_CONVERGED
RECONCILIATION_DRIFTING
RECONCILIATION_CONVERGING
RECONCILIATION_UNKNOWN
RECONCILIATION_STATUS_CHOICES
reconciliation_status
reconciliation_checked_at
```

Do not move the constants to a shared module. They have no nintent consumer after the fields and
badges are removed. nctl's own drift vocabulary is independent and remains unchanged.

`0016_remove_reconciliation_dashboard_surfaces.py` must:

- depend directly on
  `("nautobot_intent_catalog", "0015_compute_platform_instance_and_endpoint_mac")`;
- contain exactly four `migrations.RemoveField` schema operations for the fields above;
- contain no `RunPython`, data copy, replacement model, rename, default, or compatibility branch;
- be generated/reconciled with the installed Nautobot/Django version and then reviewed;
- leave every other node/service/compute/Braindump field and row intact; and
- make `makemigrations --check --dry-run` report no changes at the final source revision.

`0009` remains normal historical evidence. `0010` remains dependent on `0009`; Django's migration
graph reaches `0016` through the existing chain.

Removing `0016` backward in a scratch database may recreate empty columns, but it cannot recover
discarded cache values. This is not the operational rollback. Exact rollback after live migration
requires the Phase 5 pre-window database backup plus the prior matched nintent/nctl revisions.

### 4.2 Nautobot UI, URL, navigation, and configuration contract

After Phase 3:

- `DesiredNodeTable` and `DesiredServiceTable` contain no reconciliation column;
- their `fields` and `default_columns` contain no cache field;
- `RECONCILIATION_BADGE_CLASSES` and `_render_reconciliation_status()` do not exist;
- `django.utils.html.format_html` is removed if it has no surviving consumer;
- node and service detail templates contain no reconciliation status/checked-at row and no
  dashboard link;
- `DesiredNodeView` and `DesiredServiceView` do not inject `dashboard_url`;
- `_configured_dashboard_url()` and `dashboard_redirect()` do not exist;
- the redirect-only `Http404` and `HttpResponseRedirect` imports are absent;
- the existing `settings` import remains because `_configured_source_file()` still uses it;
- `/plugins/intent-catalog/dashboard/` is not registered;
- reversing
  `plugins:nautobot_intent_catalog:dashboard_redirect` fails normally because the route name is
  absent;
- navigation has no conditional setting read, `_dashboard_items`, or `nctl Dashboard` item;
- the Operational Tools group retains Quick Host Add;
- `IntentCatalogConfig` has no `dashboard_url` default and does not retain an empty compatibility
  alias; and
- `devenv/nautobot/nautobot_config.py` retains `PLUGINS` but sets `PLUGINS_CONFIG = {}` unless a
  non-dashboard plugin setting is discovered at Step 0.

Do not replace the removed link with an `nctl drift` link, another web view, a stale status
placeholder, or a custom removal notice.

### 4.3 REST and GraphQL contract

Retain:

- `DesiredNodeSerializer` and `DesiredServiceSerializer`;
- `DesiredNodeViewSet` and `DesiredServiceViewSet`;
- the `nodes` and `services` REST routes;
- `DesiredNodeFilterSet` and `DesiredServiceFilterSet` for their surviving filters; and
- `@extras_features("graphql")` on both models.

The final REST representation and `OPTIONS` metadata omit
`reconciliation_status` and `reconciliation_checked_at`. The final filter metadata does not list
`reconciliation_status`.

The final GraphQL object types omit both fields. A supported query over surviving fields must
return non-empty node/service results without errors. A query that explicitly requests either old
field must fail GraphQL validation as an unknown field; it must not return `null` through an alias
or compatibility resolver.

DRF may apply its normal behavior to unknown request keys. Do not add a custom request-key
compatibility layer or a one-off strictness subsystem solely for the deleted fields. The required
contract is structural absence from the supported serializer/schema/filter surface and the
impossibility of persisting the old values.

### 4.4 Braindump and Alignment Review preservation contract

This phase must not change:

- `BrainDumpDocument` or `AlignmentReview` model fields and constraints;
- one current review per Braindump;
- cascade and review-only deletion behavior;
- user/agent authorship semantics;
- opaque, autoescaped Unicode prose rendering;
- UI list/detail/add/edit/delete paths;
- REST CRUD routes and serializers;
- GraphQL roots and the pinned read query;
- the absence of reconciliation fields from both models; or
- the rule that prose cannot affect desired state, drift, planning, or actuation.

The full `test_braindump` Nautobot-runtime module is a mandatory Phase 3 regression, not a
substitute for the new cache-removal checks.

### 4.5 Matched revision and deployment boundary

Phase 3 prepares, but does not deploy:

```text
nintent: new Phase 3 commit containing model/migration/UI/API/test removal
nctl:    exact current CLI-only/dashboard-free revision, unless Step 0 finds a later approved one
root:    superproject pointer + development config + Phase 3 report
```

Record separately:

- the exact local matched nintent/nctl tuple ready for Phase 5;
- the exact currently deployed nintent commit and live migration state;
- the pre-window rollback tuple; and
- whether the new nintent commit is present on the remote after the user pushes it.

Do not rebuild Nautobot merely to prove the pushed commit. A read-only remote commit check is
sufficient in this phase.

## 5. File-level implementation inventory

Step 0 must rerun repository-scoped searches before relying on this inventory.

### 5.1 Add

`nintent/nautobot_intent_catalog/migrations/0016_remove_reconciliation_dashboard_surfaces.py`

- direct dependency on `0015`;
- four `RemoveField` operations only; and
- no cache translation or reverse data reconstruction.

`nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py`

- guarded by the same Nautobot/Django `try/except ImportError` convention as
  `test_braindump.py`;
- model, filter, table, view, URL, navigation, REST, and GraphQL assertions;
- normal node/service UI/API positive cases; and
- no dependency on live cluster rows or credentials.

If the implemented tests split into more than one file for a concrete reason, record the exact
inventory in the final report. Do not create a large generic integration-test framework for this
one deletion.

### 5.2 Edit nintent runtime and presentation

`nintent/nautobot_intent_catalog/models.py`

- remove both duplicated reconciliation constant/choice blocks;
- remove all four model fields; and
- leave node/service/compute/Braindump behavior otherwise unchanged.

`nintent/nautobot_intent_catalog/api/serializers.py`

- remove the DesiredService docstring claim that the cache fields stay writable because nctl
  dashboard writes them;
- keep the serializer, ID-based `intent_source` field, and existing read-only analysis fields.

`nintent/nautobot_intent_catalog/filters.py`

- remove `reconciliation_status` from `DesiredNodeFilterSet.Meta.fields`;
- remove it from `DesiredServiceFilterSet.Meta.fields`; and
- preserve every other filter and search method.

`nintent/nautobot_intent_catalog/tables.py`

- remove the reconciliation badge mapping/helper;
- remove both declared columns and render methods;
- remove the field from both `fields` and `default_columns`; and
- remove `format_html` only if the final file has no other caller.

`nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desirednode.html`

- remove the complete Reconciliation Status and Reconciliation Checked At rows;
- preserve realized-device, compute-realization, operational-override, placement, and endpoint
  panels.

`nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desiredservice.html`

- remove the complete Reconciliation Status and Reconciliation Checked At rows;
- preserve service attributes, analysis provenance, and desired placements.

`nintent/nautobot_intent_catalog/views.py`

- remove the two dashboard-only `get_extra_context()` methods;
- remove `_configured_dashboard_url()` and `dashboard_redirect()`;
- remove redirect-only HTTP imports;
- retain `settings` for `_configured_source_file()` and retain all compute/Braindump views.

`nintent/nautobot_intent_catalog/urls.py`

- remove only the `dashboard/` route;
- retain every ordinary node/service/compute/Braindump route.

`nintent/nautobot_intent_catalog/navigation.py`

- remove dashboard setting access, conditional construction, and tuple concatenation;
- remove the settings import if it has no surviving consumer; and
- retain all Braindump, Desired State, Source YAML, and Quick Host Add items.

`nintent/nautobot_intent_catalog/__init__.py`

- remove `default_settings = {"dashboard_url": None}`;
- do not leave an obsolete key set to `None`;
- retain App identity, version, base URL, home view, and required settings.

### 5.3 Edit local deployment configuration

`devenv/nautobot/nautobot_config.py`

- remove the concrete `dashboard_url`;
- retain `PLUGINS = ["nautobot_intent_catalog"]`;
- use `PLUGINS_CONFIG = {}` if no other current plugin setting is present at implementation time;
  and
- do not restart or rebuild the live containers in this phase.

This tracked configuration edit is not a live configuration mutation until the later image rebuild.

### 5.4 Add or edit focused tests

The preferred new runtime test module must cover at least:

1. model `_meta` has neither removed field on either model;
2. neither model class retains `RECONCILIATION_*` constants/choices;
3. filter metadata omits `reconciliation_status`;
4. table base columns, configured fields, and default columns omit the cache;
5. node and service list/detail pages return 200 using real test rows;
6. those pages contain no reconciliation labels or dashboard link;
7. `dashboard_redirect` cannot be reversed and the old direct path returns 404;
8. navigation contains Quick Host Add and no `nctl Dashboard`;
9. App defaults contain no `dashboard_url`;
10. node/service REST list/detail reads return real rows and omit both removed fields;
11. REST metadata exposes no removed field;
12. supported node/service GraphQL queries return real rows without errors;
13. explicit old-field GraphQL queries fail validation;
14. node/service create or ordinary update still works through at least one supported UI/API path;
    and
15. compute/Braindump routes are not accidentally removed from navigation or URL configuration.

Also rerun:

- `nautobot_intent_catalog.tests.test_braindump`;
- the complete Nautobot-runtime App test suite if runtime permits; and
- `python3 -m unittest discover -s nautobot_intent_catalog/tests` outside Nautobot.

`test_templates.py` should remain unchanged unless implementation discovers a real template
inventory change. Both edited detail templates continue to exist.

### 5.5 Intentionally unchanged

Do not edit:

- `migrations/0009_reconciliation_status.py`;
- `migrations/0010_operational_overrides_and_provenance.py`;
- `migrations/0015_compute_platform_instance_and_endpoint_mac.py`;
- `forms.py`, because the cache fields are already absent from editable form field lists;
- `api/views.py` or `api/urls.py`, because node/service REST resources remain;
- compute model/form/filter/table/view/serializer/template behavior;
- Braindump/Alignment Review implementation or tests except for running them;
- nctl source or tests unless Step 0 finds an unexplained Phase 2 regression;
- root/nintent READMEs and cross-initiative roadmaps assigned to Phase 4; and
- historical plans/reports.

An unexpected need to edit one of these files must be explained in the final report before it is
included.

## 6. Disposable-database and runtime proof design

### 6.1 Safety boundary

All migration and Nautobot-runtime mutation tests run against disposable state.

Use an evidence directory such as:

```text
.local/remove-unused-surfaces/p3/<timestamp>/
```

Set directories to mode `0700` and files to `0600`. Store only command output and narrowly scoped
proof. A temporary database dump may contain private rows and must remain untracked, mode `0600`,
and be deleted after the scratch database is ready or after the proof, whichever is operationally
required.

Never print or copy:

- `.local/secrets`;
- the Nautobot token or authentication headers;
- Braindump bodies or Alignment Review prose;
- raw database rows unrelated to field names/counts;
- private keys or SSH key material; or
- generated dashboard HTML/JSON contents.

Before every migration command, positively print and verify the selected database name. The live
database name `nautobot` is prohibited for Phase 3 migration commands.

### 6.2 Local-source loading constraint

The running container installs nintent from GitHub and does not mount `nintent/`. For local proof,
use the already-proven VM Phase 3 scratch technique:

1. record the installed package path and commit;
2. create a backup of the installed package inside the container's writable layer;
3. copy the local Phase 3 package into that layer only for the scratch proof;
4. point every command at an explicit scratch database;
5. run migration/runtime checks;
6. restore the original installed package and ownership; and
7. recheck live migration state and installed commit.

Use a `try/finally`-equivalent shell procedure and record restoration even when a test fails. Do
not mistake this temporary local override for the supported deployment path.

### 6.3 Forward migration scenario

The required forward proof is:

```text
disposable PostgreSQL database at 0014
  -> verify DesiredNode/DesiredService cache columns exist
  -> apply 0015 and verify its compute schema/precondition succeeds
  -> record node/service IDs, counts, and non-cache checksums/selected stable values
  -> seed or retain representative blank and nonblank cache values
  -> apply 0016
  -> verify all four cache columns are physically absent
  -> verify ORM model fields are absent
  -> verify original rows/counts and all selected non-cache values are unchanged
  -> verify compute tables/endpoint MAC from 0015 remain
  -> makemigrations --check --dry-run reports no changes
```

If cloning the live database is used, report only aggregate cache counts and stable public IDs
needed for proof. If a fresh scratch database is used, create minimal synthetic rows at historical
migration state `0015` through Django's historical models; do not alter current models to make old
fields writable.

The proof must demonstrate actual deletion with nonblank data present. Applying `0016` only to an
empty database does not exercise the data-discarding transition.

Do not treat a backward migration as cache rollback. An optional scratch-only reverse-schema
check may show that empty columns can be recreated, but the report must say explicitly that old
values are unrecoverable and operational rollback requires the backup.

### 6.4 Runtime surface scenario

Against disposable state at `0016`, create or select:

- at least one DesiredNode;
- at least one DesiredService with its required IntentSource;
- at least one DesiredComputePlatform/DesiredComputeInstance path or existing fixture sufficient
  to prove the `0015` surfaces still load; and
- Braindumps with and without an Alignment Review through the existing tests.

Positive proof must inspect content/schema, not merely status codes:

- node/service list and detail pages contain the actual test names;
- cache labels and dashboard text are absent;
- Quick Host Add remains in navigation;
- REST returns the actual node/service IDs and surviving fields;
- GraphQL returns non-empty node/service roots and rejects old fields;
- compute URLs/schema remain registered;
- Braindump queries return the test documents/review relation; and
- no test invokes nctl, SSH, Ansible, Jobs, or host operations.

## 7. Procedure

### Step 0 — Reconfirm the Phase 2 handoff and non-mutation boundary

1. Record root, nctl, nintent, nauto, nodeutils, and ansible_agdev HEADs, upstream state, and dirty
   files with ownership.
2. Confirm Phase 2's final nctl revision has no dashboard command, cache PATCH, dashboard schema,
   or reconcile dashboard field.
3. Record live installed nintent version/commit, migration state, and running Job count using
   read-only commands.
4. Recount cache values by status and checked-at nullability without printing row contents.
5. Confirm local `0015` still directly follows `0014` and has not been applied live.
6. Confirm VM Phase 3 Step 6 has not created a conflicting nintent/nctl commit.
7. Re-run removal-token searches in nintent source, tests, migrations, local deployment config,
   current docs, and historical docs.
8. Reconfirm `.local/secrets` is ignored and do not read it.
9. Create the private evidence directory and record its retention/cleanup owner.

Gate: the Phase 2 handoff is intact, live remains on `0014`, the local migration graph has no
unexpected `0016`, dirty-state ownership is known, and no mutation has occurred.

### Step 1 — Freeze focused removal and retained-path tests

1. Add the focused Nautobot-runtime test module from §5.4.
2. Make every assertion name the exact removed or retained contract.
3. Run the local Django-free suite; the guarded runtime tests may be skipped outside Nautobot, but
   test discovery/import must remain clean.
4. Against disposable Nautobot test state before implementation, show that the new removal
   assertions fail for the expected pre-change reasons while existing Braindump/ordinary UI
   assertions pass.
5. Record the exact test-to-contract matrix rather than using one broad “page rendered” test.

Gate: intentional failures map only to the current cache/link residue; retained-path tests are
green before deletion.

### Step 2 — Remove model fields and generate migration 0016

1. Remove both duplicated reconciliation constant/choices blocks and all four model fields.
2. In a Nautobot/Django environment using local source and a scratch database, generate the named
   migration.
3. Review the dependency and operation list against §4.1.
4. Reject any generated operation beyond the four field removals until its cause is understood.
5. Confirm `0009`, `0010`, and `0015` have no diff.
6. Run `makemigrations --check --dry-run` against the same local source.
7. Run import/static checks sufficient to catch syntax and model-definition errors.

Gate: current models have no cache contract; `0016` is exactly four removals after `0015`; no
historical migration changed.

### Step 3 — Remove filters, tables, templates, views, URLs, navigation, and settings

1. Remove the two FilterSet entries.
2. Remove the table helper/mapping/import, two columns, two render methods, and four field-list
   entries.
3. Remove the two status/timestamp row pairs from the detail templates.
4. Remove dashboard context, resolver, redirect, route, navigation, and now-unused imports.
5. Remove the App default setting.
6. Remove the stale serializer writer commentary.
7. Remove the concrete development `dashboard_url`, preserving plugin enablement.
8. Re-read diffs around DesiredNode/DesiredService and Operational Tools to confirm no adjacent
   compute, endpoint, placement, or Quick Host Add behavior was deleted.

Gate: no current runtime reader/presenter/link/setting remains, while shared node/service and
Braindump/compute paths are still present.

### Step 4 — Run local tests and structural deletion checks

1. Run the complete local nintent suite from the documented working directory.
2. Run focused source-level checks for model constants, model fields, filter/table fields,
   template text, URL names, navigation labels, and settings.
3. Run `git diff --check`.
4. Inspect every changed file and confirm the inventory matches §5.
5. Confirm nctl remains byte-for-byte unchanged in this phase unless a separately explained
   correction was required.

Gate: local tests pass, the diff is clean, and the active source/config token set is reduced to
the migration/test exceptions defined in Step 7.

### Step 5 — Prove the 0015-to-0016 migration on a disposable database

1. Create the scratch database using §6's safety procedure.
2. Confirm it is not the live `nautobot` database before each command.
3. Establish migration state `0014`; verify the four columns exist.
4. Apply `0015`, satisfying and recording its existing legacy-realized-VM precondition.
5. Ensure representative blank and nonblank cache values exist.
6. Capture only row counts, IDs, and selected non-cache checksums/values needed for comparison.
7. Apply `0016`.
8. Inspect Django migration state, PostgreSQL columns, current ORM fields, and preserved row data.
9. Verify the `0015` compute tables/relations/endpoint MAC still exist.
10. Run `makemigrations --check --dry-run`.
11. If an optional reverse-schema check is run, state that it recreates empty columns and is not
    rollback.

Gate: nonblank cache data is discarded exactly as designed, all four columns are absent, unrelated
rows/schema are unchanged, and no live database state changed.

### Step 6 — Prove retained UI, REST, GraphQL, and Braindump behavior

1. Run the new focused runtime test module against disposable Nautobot test state.
2. Run `test_braindump` in the same installed-source context.
3. Run the complete Nautobot-runtime App tests if practical; if not, name the exact omitted
   modules and do not substitute the local suite for them.
4. Exercise non-empty node/service UI and API paths described in §6.4.
5. Prove the old redirect route and navigation item are absent.
6. Prove supported GraphQL queries work and old-field queries fail schema validation.
7. Prove compute UI/API/GraphQL registration from VM Phase 3 still loads.
8. Record framework versions and every warning/failure.

Gate: absence of the cache/link is positively proven and ordinary desired-state, compute, and
Braindump paths are positively exercised.

### Step 7 — Restore the environment, run deletion searches, and measure the final state

1. Restore the container's original installed package and file ownership.
2. Drop the scratch database and delete any temporary dump.
3. Reconfirm live migration state still ends at `0014`.
4. Reconfirm the live installed nintent commit is unchanged.
5. Re-run the complete local nintent suite after restoration.
6. Search at least:

   ```text
   reconciliation_status
   reconciliation_checked_at
   RECONCILIATION_
   dashboard_url
   dashboard_redirect
   nctl Dashboard
   nctl dashboard
   view dashboard
   ```

7. Classify remaining matches:
   - `0009` and `0010` migration history;
   - `0016` removal operations;
   - negative assertions in the focused removal tests;
   - Phase 4-owned current README/roadmap wording;
   - this roadmap/plan and historical reports.
8. Treat any unexplained match in current runtime source, templates, local deployment config, or
   current model/API schema as a blocker.
9. Record final source/test line counts, test counts, and exact changed-file inventory.

Gate: scratch/local-package cleanup is complete, live state is unchanged, and no unexplained
active implementation/configuration match remains.

### Step 8 — Prepare commits and matched revision tuples

1. Review the final nintent diff as one coherent model/migration/UI/API/test deletion.
2. Commit nintent in a reviewable unit.
3. Record the exact nintent commit and the exact Phase 2/VM-compatible nctl commit.
4. Commit the superproject pointer, development config, and Phase 3 evidence/report in a
   reviewable unit.
5. Record the deployed pre-change nintent commit/migration state and the prior matched rollback
   tuple.
6. Ask the user to push the nintent commit; do not push it.
7. After the user pushes, verify read-only that the exact commit is reachable remotely.
8. Do not rebuild, restart, or migrate Nautobot.

Gate: exact matched and rollback tuples are recorded, the nintent commit is available for the
later GitHub-based rebuild, and no live mixed-version interval has begun. If the push is not yet
available, report `implemented, awaiting push` rather than `complete`.

### Step 9 — Produce one final Phase 3 report

Write `report.md` with:

- precise completion status;
- execution timestamp and private evidence path;
- starting/ending root and submodule revisions plus dirty-state ownership;
- live installed nintent commit/migration state before and after;
- aggregate pre-removal cache counts;
- exact added/edited/unchanged file inventory;
- exact `0016` dependency and operations;
- disposable-database setup and forward-migration results;
- proof that nonblank cache data was exercised and discarded;
- before/after column, row-count, and selected non-cache comparisons;
- UI/URL/navigation/config results;
- REST/GraphQL results, including non-empty supported queries and old-field rejection;
- Braindump/Alignment Review regression results;
- local and Nautobot-runtime test summaries;
- deletion-search exceptions;
- source/test measurements;
- matched and rollback tuples plus push availability;
- explicit confirmation that no live migration/rebuild/state mutation occurred;
- every omitted, substituted, failed, or optional check; and
- an exit-criteria table referencing exact evidence.

Do not mark the phase `complete` if a required runtime path was not exercised, the disposable
migration used only empty cache rows, scratch cleanup is incomplete, or the matched nintent commit
is not ready for the supported GitHub rebuild path.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| Models | both models omit all four fields and duplicated reconciliation constants/choices |
| Migration graph | `0016` depends directly on `0015`; `0009`, `0010`, and `0015` unchanged |
| Migration content | exactly four `RemoveField` operations, no data copy/replacement |
| Disposable forward path | `0014 -> 0015 -> 0016` succeeds with representative nonblank cache values |
| Physical schema | all four columns absent; compute/endpoint-MAC and unrelated columns retained |
| Row preservation | node/service IDs, counts, and selected non-cache values unchanged |
| Migration consistency | `makemigrations --check --dry-run` reports no changes |
| Filters/tables | no reconciliation filter, column, renderer, badge mapping, or default column |
| Detail UI | real node/service pages render and omit both cache rows/dashboard link |
| URL/navigation | redirect name/path and nctl Dashboard item absent; Quick Host Add retained |
| App/deployment config | no `dashboard_url` default or development setting; plugin stays enabled |
| REST | real node/service reads work; representations and metadata omit both fields |
| GraphQL | non-empty supported reads work; explicit old fields fail validation |
| Compute preservation | `0015` models, endpoint MAC, UI/API/GraphQL registration still load |
| Braindump preservation | model/UI/REST/GraphQL tests and prose authority boundary unchanged |
| Local tests | documented Django-free suite passes from `nintent/` |
| Runtime tests | focused removal tests and Braindump tests pass in Nautobot |
| Deletion search | no unexplained active runtime/template/config match |
| Environment cleanup | scratch DB/dump gone; original installed package restored |
| Live non-mutation | live remains at `0014` on the same installed commit |
| Revision readiness | exact nintent/nctl and rollback tuples recorded; nintent commit push verified |
| Secrets | no token, header, private prose, dump content, or dashboard content in tracked evidence |

## 9. Exit criteria

- [ ] Phase 2's nctl dashboard-free/no-PATCH handoff is still intact.
- [ ] Both current models have no reconciliation constants, choices, status field, or timestamp
      field.
- [ ] `0016_remove_reconciliation_dashboard_surfaces.py` depends directly on `0015`.
- [ ] `0016` contains exactly four field removals and no replacement/cache-translation behavior.
- [ ] `0009`, `0010`, and `0015` remain unchanged.
- [ ] A disposable database reaches `0016` through `0015`.
- [ ] The forward proof starts with representative nonblank cache values.
- [ ] All four physical columns are absent after migration.
- [ ] Node/service row identity, counts, and selected non-cache data are preserved.
- [ ] Compute tables/relations and endpoint MAC introduced by `0015` remain.
- [ ] `makemigrations --check --dry-run` reports no changes.
- [ ] FilterSet metadata contains no reconciliation-status filter.
- [ ] Node/service tables contain no status column, badge, or render helper.
- [ ] Node/service detail templates contain no cache rows or dashboard link.
- [ ] Dashboard context, resolver, redirect view, URL name/path, and navigation item are absent.
- [ ] App defaults and development configuration contain no `dashboard_url`.
- [ ] Normal node/service list/detail UI pages render real rows.
- [ ] Normal node/service REST responses/metadata omit the fields and retain surviving data.
- [ ] Normal non-empty node/service GraphQL reads work.
- [ ] Explicit GraphQL requests for removed fields fail as unknown fields.
- [ ] Braindump/Alignment Review model, UI, REST, GraphQL, authorship, and prose boundaries pass.
- [ ] Compute UI/API/GraphQL registration remains available.
- [ ] Local and required Nautobot-runtime tests pass.
- [ ] Deletion searches have no unexplained active source/template/config matches.
- [ ] Scratch database/dump and temporary container package override are removed/restored.
- [ ] Live nintent remains on its original commit with migrations through `0014`.
- [ ] Exact matched nintent/nctl and rollback tuples are recorded.
- [ ] The user, not the agent, pushed the nintent commit and its remote availability is verified.
- [ ] No live rebuild, migration, Job, desired write, nctl apply, Ansible, or host mutation occurred.
- [ ] The final report records all deviations, omissions, warnings, exceptions, and status.

A passing local test suite alone is not completion. Completion requires a non-empty
data-discarding migration proof, physical/schema/API/UI absence of the retired surface, positive
proof of the retained paths, complete environment restoration, and revision readiness for the
coordinated deployment.

## 10. Handoff to Phase 4

Phase 4 receives:

- nintent source with no reconciliation cache or dashboard presentation/link/config residue;
- migration `0016` ready after `0015`;
- disposable-database proof that nonblank cache values are discarded and unrelated state remains;
- retained DesiredNode/DesiredService UI, REST, and GraphQL proofs;
- retained compute and Braindump/Alignment Review proofs;
- a clean local development configuration with the plugin still enabled;
- exact matched nintent/nctl and rollback tuples;
- the pushed nintent commit ready for the later image rebuild;
- live Nautobot still unchanged at `0014`;
- one final Phase 3 report; and
- an explicit list of current documentation references intentionally deferred to Phase 4.

Phase 4 must update root/nctl/nintent READMEs, output/compatibility docs, core-reconcile and
Braindump supersession notices, the VM roadmap/active plan, and all other current instructions.
It must preserve migration/history references as history and must not deploy `0015`/`0016`.

The live cache-column removal, matched-version activation, removed-command smoke checks, and
generated dashboard-directory cleanup remain one coordinated Phase 5 maintenance-window
operation.
