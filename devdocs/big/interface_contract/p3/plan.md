# Interface Contract Phase 3 Implementation Plan: Make the nintent Human UI Read-Only

Parent: [roadmap.md](../roadmap.md) — Phase 3.

Predecessors:

- [Phase 0 final report](../p0/report.md) — final consumers, ownership, and interface matrix
  frozen.
- [Phase 1 final report](../p1/report.md) — source-controlled desired writer implemented but not
  deployed; its coordinated rollout remains Phase 4 work.
- [Phase 2 final report](../p2/report.md) — core REST/GraphQL implementation is present and local
  suites pass, but the audit in Section 2 found reproducibility, coverage, documentation, and
  reporting gaps that this phase must close before changing the UI.

Status: proposed; coordinated `nintent` implementation plus disposable-environment verification.
This phase does not authorize deployment, a live desired-state mutation, a live Job run, or a
live UI write probe.

## 1. Goal and required transition

Preserve a useful human inspection surface for every object in the frozen matrix while removing
every nintent Nautobot-page path capable of changing domain state.

The Phase 3 transition is:

```text
before
  60 declared UI path() calls
  + ObjectEditView/ObjectDeleteView mutation classes
  + 13 model/utility forms
  + edit/delete ButtonsColumn actions on every list table
  + ToggleColumn selection affordances on every list table
  + Quick Host Add form, route, template, JavaScript, and transactional helper
  + Source YAML diagnostic route and template
  + Braindump and Alignment Review UI create/edit/delete controls
  + stale current documentation describing broad REST and UI CRUD

after Phase 3
  exactly 22 active nintent UI routes:
    11 model list routes
    11 model detail routes
  + navigation only to retained list pages
  + list tables containing inspection links and fields, with no row actions or bulk selection
  + detail pages showing identity, lifecycle, links, provenance, timestamps, and relationships
  + one separated, autoescaped, read-only Braindump/Alignment Review detail
  + no nintent model form, edit/delete view, mutation URL, Quick Host Add, or Source YAML page
  + current documentation directing writes to YAML/Jobs, nctl, or the retained narrow REST writers
```

The final human interaction is:

```text
navigation
  -> authenticated list/filter/table
  -> read-only detail and related-object links
  -> no domain mutation form, button, bulk selector, or POST target
```

The UI is an inspection adapter over the live models. It is not a fallback desired-state writer,
proposal editor, approval workflow, Braindump editor, or status dashboard.

## 2. Phase 2 audit and mandatory follow-up

Phase 2 was performed quickly. Its implementation must not be treated as fully proven merely
because the two local suites are green.

### 2.1 What the current audit positively confirmed

At planning time on 2026-07-26:

- `nintent` registers only `nodes`, `braindumps`, and `alignment-reviews` in its API router.
- The four unused REST serializers and ViewSets are absent.
- The three retained serializers use explicit field lists and reject supplied keys outside their
  operation-specific writable set.
- `IntentSource` no longer has the GraphQL feature decorator, while eleven retained models do.
- `nctl` `execute_link_actual_node()` uses `fetch_desired_snapshot()` before and after the exact
  derived-link PATCH; no domain-object `rest_get()` remains.
- The remaining `rest_get()` calls are the helper definition and Job discovery, JobResult
  polling, and FileProxy lookup.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` passes
  227 tests with 5 Nautobot-runtime skips.
- `cd nctl && uv run pytest` passes 954 tests.
- The root and submodule worktrees were clean when this plan was authored.

These facts establish that the central Phase 2 code transition exists. They do not close the
following proof gaps.

### 2.2 Gaps that block unqualified acceptance of Phase 2

| Phase 2 claim or requirement | Current retained evidence | Phase 3 disposition |
|---|---|---|
| Complete REST list/detail route, method, response-field, writable-field, and zero-write rejection matrix | `test_api_contract.py` currently exercises removed collection list GETs and node collection POST; other tests cover selected positive operations, not the frozen complete matrix | Add one table-driven Nautobot-runtime contract suite covering every required list/detail/method/field case and database non-mutation |
| Removed routes are non-reversible and both list/detail families return 404 | Only literal collection-list GETs are directly covered in the retained Phase 2 contract test | Assert reverse failure plus literal list and representative/detail paths for all four families |
| IntentSource GraphQL singular/plural roots fail schema validation | Registry membership is tested; direct schema queries for both roots are not retained | Execute both invalid GraphQL queries and prove the eleven retained roots still validate |
| Wrong/missing node identity, GraphQL read failures, partial link/source state, and post-PATCH read failure fail closed | The focused ledger file covers the happy path, existing link, PATCH failure, one refetch mismatch, wrong action, and candidate type; several planned boundaries are absent | Add the missing focused tests and verify executor evidence after a simulated successful PATCH followed by confirmation failure |
| A real planner, real ledger executor, and real nintent API perform one node-link transition and a fresh computation does not repeat it | The cited ledger tests mock HTTP responses; the executor non-repetition test replaces `execute_link_actual_node()` with a lambda and sequences synthetic drift | Run an HTTP-level disposable cross-component scenario against the exact local nintent source, using the real nctl planner and ledger executor |
| Lifecycle and Braindump/review writers work across the exact disposable nintent/nctl contract | Existing nctl operation tests monkeypatch GraphQL source functions and mock REST | Exercise representative lifecycle and prose mutations over the same disposable HTTP boundary and confirm through real GraphQL |
| Current documentation contains no deleted Phase 2 API contract | `nintent/README_DEV.md` still names deleted service/endpoint serializers and ViewSets and says serializers use `fields = "__all__"` | Correct it in the Phase 2 follow-up documentation step and search all current docs |
| Final revisions and private evidence are reproducible | The Phase 2 final report names an intermediate nintent revision and a superproject placeholder; its `.local` evidence directory is not present in this workspace | Do not invent or rewrite missing historical evidence; record a fresh Phase 3 baseline and explicitly report which Phase 2 claims were re-proved |

The Phase 2 report remains historical evidence and is not rewritten. The Phase 3 final report must
state that Phase 2 closure was re-audited, list each newly executed proof, and distinguish:

- a code defect found and fixed;
- a missing test added around already-correct behavior;
- a stale current document corrected; and
- a historical proof that could not be recovered and was replaced with a fresh reproducible proof.

### 2.3 Phase 2 closure gate

No UI implementation deletion may be reported complete until:

1. the full REST/GraphQL contract suite passes in Nautobot's real runtime;
2. the disposable HTTP cross-component link transition and non-repetition proof passes;
3. lifecycle and prose writers are positively GraphQL-confirmed over that boundary;
4. stale active Phase 2 API documentation is corrected;
5. any defect exposed by those tests is fixed without broadening the Phase 2 contract; and
6. a sanitized, reproducible result is recorded in the Phase 3 reports.

This gate may be implemented alongside early UI tests, but a failure blocks final Phase 3
completion rather than being relabeled as unrelated work.

## 3. Authority, prerequisites, and safety boundary

### 3.1 Governing inputs

Before implementation, re-read:

- root `README.md` and `README_DEV.md`;
- `.local/localenv_memo.md`;
- the parent interface-contract roadmap;
- every Phase 0, Phase 1, and Phase 2 plan/final report, with the Phase 2 qualification above;
- `devdocs/vision/refactor/vision.md`;
- current Braindump, core-reconcile, and VM roadmaps;
- the supersession note and still-active instructions in `devdocs/big/vm/p3/plan.md`;
- `nintent/README.md`, `README_QUICK.md`, `README_DEV.md`, and `CONCEPT.md`;
- `nintent/nautobot_intent_catalog/views.py`;
- `urls.py`, `navigation.py`, `forms.py`, `filters.py`, and `tables.py`;
- every template below `templates/nautobot_intent_catalog/`;
- `operations/hosts.py` and `operations/__init__.py`;
- nintent UI, template, operation, API, GraphQL, Import, Analyze, and compute tests;
- Phase 2's retained nintent API implementation and focused nctl writer tests; and
- every active match found by Section 10 searches.

The parent roadmap's interface matrix and ownership table are authoritative. Phase 3 must not
retain an ordinary form because it seems convenient, add a replacement mutation page, or weaken a
retained non-UI writer.

### 3.2 Planning-time repository snapshot

Observed while this plan was authored on 2026-07-26:

| Repository | Revision | State |
|---|---|---|
| superproject | `46c5d7f` | clean before this plan was added |
| `nintent` | `cb573b7516b08eaa30aa706e1d2624585c6864c3` | clean |
| `nctl` | `8175f260b8427b4a93c86df7fb85a1b4cfd9923d` | clean |
| `nauto` | `2635e648469d6e6bad87af113f7427b878b0a387` | clean; retained Phase 1 state |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean; out of scope |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean; out of scope |

Static UI orientation found:

- 60 `path()` declarations in the current URL module;
- 25 `ObjectEditView`/`ObjectDeleteView` subclasses;
- 13 form classes, including Quick Host Add;
- 11 table action columns and 11 row-selection toggle columns;
- one Source YAML page and fallback alias;
- one Quick Host Add operation module with dedicated tests;
- mutation controls in the Braindump and DesiredNode detail templates; and
- current Quick Host Add/CRUD instructions in nintent documentation.

These are remeasurement baselines, not deletion quotas. Step 0 must recapture exact revisions,
dirty state, runtime route names, and collected tests before relying on them.

### 3.3 Allowed changes

Phase 3 may change:

- nintent UI views, URLs, navigation, tables, detail templates, forms, the Quick Host Add
  operation, tests, and current documentation;
- nintent Phase 2 API tests and implementation only where the mandatory audit exposes a real
  contract defect;
- nctl focused tests and implementation only where the Phase 2 closure proof exposes a real
  retained-writer defect;
- superproject nintent/nctl pointers for any necessary coordinated fix;
- this plan and Phase 3 reports; and
- private evidence under `.local/interface-contract/p3/<timestamp>/`.

It may use isolated disposable Nautobot/PostgreSQL/Redis instances and synthetic rows. The
disposable environment must use the exact local Phase 1+2+3 source state, not the older live
package.

### 3.4 Prohibited actions

Phase 3 must not:

- POST, PATCH, PUT, or DELETE a live nintent/Nautobot object;
- submit a live nintent UI form, even to demonstrate that the old route exists;
- run a live Import, Analyze, IPAM, Ingest, Seed, or other Job;
- rebuild or restart the live Nautobot containers;
- connect disposable tests to the live Postgres, Redis, media volume, token, or port 8000;
- run `nctl reconcile --yes`, `nctl lifecycle`, or a Braindump mutation against the live URL;
- apply the Phase 1 YAML proposal to live state;
- delete or alter a domain model, field, migration, GraphQL root, or retained REST collection;
- remove the IntentSource, dependency, compute, provenance, or Braindump/review inspection models;
- remove filters merely because forms are deleted;
- add a replacement UI mutation route, generic CRUD API, compatibility alias, redirect, or
  catch-all handler for an old URL;
- make the Source YAML page read-only instead of deleting it;
- preserve Quick Host Add as a hidden helper with no current caller;
- change Import/Analyze/IPAM writer ownership, nctl output schemas, drift, planning, evidence, SSH,
  rendering, observation, or actuation semantics;
- implement compute drift/linking/actuation or seed compute rows;
- copy a live token, Braindump body, Alignment Review summary, raw private payload, or credential
  into tracked reports; or
- push commits. The user owns pushes and Phase 4 owns deployment.

## 4. Scope and non-goals

### 4.1 In scope

- close every Phase 2 gap in Section 2;
- retain exactly the list/detail UI routes in Section 5;
- delete every nintent UI model add/edit/delete route and view;
- delete all nintent model mutation forms;
- delete Quick Host Add end to end, including its helper and tests;
- delete the Source YAML diagnostic page end to end;
- remove table action buttons, row-selection toggles, and any bulk mutation affordance;
- remove mutation controls from custom detail templates;
- preserve and improve read-only identity, relationship, lifecycle, actual-link, provenance, and
  timestamp rendering where needed;
- retain Braindump and Alignment Review as distinct, autoescaped prose panels;
- prove removed routes are absent rather than merely permission-hidden;
- prove retained pages have no domain-mutation POST path and do not change rows;
- retain filter/table/list/detail behavior for every frozen read model;
- update current documentation to the final read/write ownership contract;
- run local/static, Nautobot-runtime, and disposable HTTP verification; and
- commit and report the coordinated nintent change without deployment.

### 4.2 Explicitly retained

- all nintent models, fields, constraints, and migrations through `0016`;
- all eleven consumer-backed GraphQL registrations and four pinned nctl queries;
- the three Phase 2 REST mutation collections and their exact fields/methods;
- nctl lifecycle, node-link, and Braindump/review mutation behavior;
- strict YAML and Import/Analyze dry-plan/apply contracts;
- IPAM and actual-ledger writers;
- list/detail classes, filters, tables, navigation links, and custom detail templates needed by
  the final UI route matrix;
- related-object links between desired nodes, endpoints, placements, dependencies, compute
  objects, actual links, and sources;
- the nested Alignment Review display on a Braindump detail;
- native Nautobot UI/API for core Device, Cluster, VM, Interface, and IPAddress models;
- normal authentication and `view_*` permission enforcement on retained pages;
- historical plans, reports, migrations, and Git history; and
- the deferred live AI Resource Auto Review JobHook and its custom-field data.

### 4.3 Out of scope

- live deployment and live removed-route smoke tests;
- Phase 4 database backup, maintenance window, YAML apply, and rollback;
- changing desired-state content or reconciling live/YAML identity differences;
- replacing the Source YAML page with another tracked-file browser;
- adding a UI link that invokes nctl, a Job, REST, or GraphQL mutation;
- adding standalone Alignment Review list/detail pages;
- redesigning the UI, introducing a component framework, or broadly restyling templates;
- test-suite consolidation unrelated to the removed UI;
- nctl modularization;
- changing Braindump authorship or review semantics;
- compute drift, linking, guest creation, stop/delete/replace behavior, or Proxmox actuation; and
- removing active AI Resource Review behavior.

## 5. Frozen target UI contract

### 5.1 Retained routes

The final active plugin UI contains exactly these 22 domain routes:

| Object | List route name | Detail route name |
|---|---|---|
| IntentSource | `intentsource_list` | `intentsource` |
| DesiredService | `desiredservice_list` | `desiredservice` |
| DesiredDependency | `desireddependency_list` | `desireddependency` |
| DesiredNode | `desirednode_list` | `desirednode` |
| DesiredEndpoint | `desiredendpoint_list` | `desiredendpoint` |
| DesiredComputePlatform | `desiredcomputeplatform_list` | `desiredcomputeplatform` |
| DesiredComputeInstance | `desiredcomputeinstance_list` | `desiredcomputeinstance` |
| DesiredServicePlacement | `desiredserviceplacement_list` | `desiredserviceplacement` |
| DesiredNodeOperationalOverride | `desirednodeoperationaloverride_list` | `desirednodeoperationaloverride` |
| BrainDumpDocument | `braindumpdocument_list` | `braindumpdocument` |
| DesiredIPRange | `desirediprange_list` | `desirediprange` |

Alignment Review remains nested in the Braindump detail and has no standalone UI route.

All retained list/detail routes:

- are GET/HEAD inspection surfaces;
- require the normal model view permission;
- return the framework's normal unavailable/method response for domain POST;
- contain no form action, submit control, mutation button, bulk selector, or link to a removed
  route; and
- may link only to retained read pages or native read pages.

### 5.2 Removed route families

Delete, do not redirect or alias:

- `source_yaml_list` and the import-unavailable `source_list` fallback;
- `desiredhost_quick_add`;
- every `*_add`, `*_edit`, and `*_delete` route;
- `alignmentreview_add`, `alignmentreview_edit`, and `alignmentreview_delete`; and
- all literal URL paths served only by those names.

The expected active-route contraction is from the current 59 runtime domain/utility routes to 22.
The source-only fallback route is also deleted, yielding 22 `path()` declarations in the final
module. Step 0 must confirm framework behavior before freezing exact counts in tests.

A deleted route must:

- fail `reverse()` with `NoReverseMatch`;
- return 404 for its former literal URL when requested by an authenticated broadly permitted
  synthetic user; and
- have no alternate trailing-slash, query-parameter, parent-detail, or navigation path that
  invokes the old operation.

### 5.3 Views and forms

`views.py` retains only:

- eleven `ObjectListView` subclasses;
- eleven `ObjectView` subclasses; and
- read-only context helpers used by those views.

Delete:

- all `ObjectEditView` and `ObjectDeleteView` imports/subclasses;
- `FormView`, message, redirect, form-validation, and mutation-operation imports/helpers;
- Alignment Review mutation views;
- Source YAML rendering and configured-file helpers; and
- any fallback branch that maps an unavailable model UI to the YAML page.

All classes in `forms.py` exist only for removed nintent UI writers at planning time. Re-run caller
searches, then delete the entire module if that remains true. Do not retain model forms as a
future convenience or test fixture.

### 5.4 Quick Host Add deletion boundary

Delete all of:

- `DesiredHostQuickAddView`;
- `DesiredHostQuickAddForm`;
- `desiredhost_quick_add` URL and navigation group/item;
- `desiredhost_quick_add.html` and `inc/quick_add_field.html`;
- Quick Host Add JavaScript and constants;
- `operations/hosts.py`;
- `DesiredHostCreationResult` and `create_desired_node_with_primary_endpoint` exports;
- `test_operations_hosts.py` and Quick Host Add-specific UI/template tests; and
- current documentation instructing users to use the operation.

Before deleting `operations/hosts.py`, prove repository-wide that it has no caller other than the
removed form/view/tests. Preserve `operations/ipam.py` and the IPAM exports used by Jobs.

### 5.5 Source YAML page deletion boundary

Delete:

- `source_yaml_intent_source_list`, its alias, and configured-path UI helper;
- the `source_yaml_list` route and navigation item;
- `source_yaml_list.html`; and
- tests and documentation whose purpose is the diagnostic page.

Do not delete `load_default_intent_sources()` or configured-file resolution used by the Import Job.
The supported human review surfaces are the checked-in
`nauto/seed/intent_sources.yaml` file and the versioned Import Job plan/apply artifact.

### 5.6 Read-only tables

For all eleven list tables:

- retain stable identity links and useful inspection columns;
- remove `ButtonsColumn` and every `actions` field/default column;
- remove `ToggleColumn` and every `pk` bulk-selection field/default column;
- remove `TABLE_ACTION_BUTTONS` and now-unused imports;
- retain filters, pagination, sorting, related counts, and HTMX list rendering; and
- prove rendered HTML contains no edit/delete link, checkbox selection control, bulk action, or
  form targeting domain mutation.

The absence of a URL is the authority boundary; hiding a button with CSS or permissions is not
sufficient.

### 5.7 Read-only detail content

Each retained detail page must visibly expose the fields that help a human identify ownership and
current relationships. Where the model provides them, include:

- immutable identity/display values;
- lifecycle or effective lifecycle;
- IntentSource or analysis provenance;
- placement assignment source;
- realized object and realized-link source;
- endpoint/IP provenance where relevant;
- compute default/override provenance;
- created and last-updated timestamps; and
- related-object links that resolve only to retained read pages or native Nautobot read pages.

Remove the DesiredNode “Add an exception” link. When no operational override exists, render a
neutral read-only statement.

Do not expose secrets, raw credentials, token-bearing source configuration, or private data that
the current read contract intentionally omits. JSON/config fields already approved for human
inspection remain autoescaped or safely rendered as inert text.

### 5.8 Braindump and Alignment Review boundary

The Braindump detail retains:

- a panel explicitly labeled as user-originated Braindump content;
- title, authorship, timestamps, and body;
- a separate panel explicitly labeled as AI Alignment Review;
- review timestamps and summary when present; and
- an unreviewed indicator when absent.

Delete Add/Edit/Delete review controls and all Braindump mutation controls inherited from tables
or routes. Continue using Django autoescaping and whitespace-preserving display. Tests must use
synthetic script/HTML/template-looking strings and prove they remain inert without placing live
prose in evidence.

## 6. Implementation procedure

### Step 0 — Recapture boundary, evidence, and Phase 2 status

1. Create `.local/interface-contract/p3/<timestamp>/` with directory mode `0700` and evidence
   files mode `0600`.
2. Record timestamp/timezone, tool versions, revisions, branches, submodule pointers, staged,
   unstaged, and untracked state.
3. Record governing documents reviewed and every deviation from this planning snapshot.
4. Collect current runtime UI route names/methods, navigation items, view classes, forms, table
   columns, templates, and test counts.
5. Recompute the four pinned GraphQL query digests and classify every `rest_get()`.
6. Re-run Phase 2 and Phase 3 searches across code, tests, configuration, wrappers, current docs,
   and historical docs.
7. Read-only inspect the installed live revision, migration state, aggregate row counts, current UI
   route availability, and pending/running Jobs. Do not submit a form or record prose.
8. Define a fresh disposable project/database/network/volume/port tuple with no reference to live
   resources.
9. Inspect Nautobot 3.1.3 `ObjectListView`, `ObjectView`, table rendering, URL dispatch, method
   handling, and permission behavior used by this implementation.

Gate: work starts from one explained revision tuple, in-scope files have no unexplained overlapping
changes, Phase 2 gaps are explicitly open, and disposable resources cannot reach live state.

### Step 1 — Freeze and close the Phase 2 contract gaps

Add or strengthen executable tests before UI deletion:

1. Assert exactly three REST router registrations and exact reverse names.
2. Assert all four removed REST collections are non-reversible and list/detail literal URLs return
   404.
3. Exercise the complete node method matrix: list/detail GET, detail PATCH, and every disallowed
   POST/PUT/DELETE/list PATCH/list DELETE case.
4. Assert exact node response fields and exact writable combinations.
5. For every response-only, unknown, invalid lifecycle, and inconsistent link/source input,
   assert 400 plus an unchanged row snapshot.
6. Exercise the equivalent Braindump/review method, explicit field, strict-key, create-only parent,
   byte-preservation, validation, and zero-write rejection matrix.
7. Query the GraphQL schema for absent IntentSource singular/plural roots and present retained
   roots.
8. Add missing nctl linker cases for absent ID, absent node, slug mismatch, partial pre-existing
   link/source, GraphQL errors before/after PATCH, wrong confirmed source, and preserved executor
   mutation/progress evidence.
9. Correct `nintent/README_DEV.md` and all other current Phase 2 API descriptions.
10. Fix any implementation defect found by these tests without adding a fallback route/reader or
    widening fields/methods.

Gate: the full runtime matrix passes and Phase 2's static/current-document contract is reproducible.

### Step 2 — Freeze executable tests for the final UI

Before deleting UI code:

1. Define the exact 22-name retained route manifest and 37-name removed manifest.
2. Assert each retained list/detail name reverses and each removed name does not.
3. Assert authenticated GET for every retained list/detail returns 200 with an object-specific
   identifying value.
4. Assert normal view permissions remain required.
5. Assert former literal mutation/utility URLs return 404 for a broadly permitted user.
6. Assert POST to retained list/detail routes cannot mutate and leaves row fingerprints unchanged.
7. Assert final navigation contains all eleven retained list destinations and no Source YAML,
   Quick Host Add, or mutation item.
8. Assert every final table lacks action and selection columns while retaining its identity link,
   filter behavior, and important fields.
9. Assert retained detail pages show lifecycle/link/provenance/timestamp fields applicable to each
   model.
10. Assert every related link in custom templates resolves to a retained read route.
11. Assert the Braindump and review panels remain separate, escaped, and read-only with both
    reviewed and unreviewed fixtures.
12. Assert no retained template renders a POST form, CSRF token, submit control, add/edit/delete
    label, or old reverse name.
13. Replace old positive UI mutation tests with absence/non-mutation tests; do not leave skipped
    compatibility tests.

Gate: tests fail against the pre-Phase-3 UI for the intended mutation-surface reasons and
positively define the inspection behavior that must remain.

### Step 3 — Remove ordinary model mutation views, forms, and URLs

1. Delete every ObjectEditView/ObjectDeleteView class and import.
2. Delete all `*_add`, `*_edit`, and `*_delete` URL patterns.
3. Delete Alignment Review mutation classes and routes.
4. Remove mutation-only Django imports and helper functions.
5. Re-run caller searches and delete `forms.py` if it remains UI-only.
6. Simplify `urls.py` to the explicit 22-route manifest; remove conditional mutation and YAML
   fallbacks.
7. Keep list/detail querysets, `select_related()`/`prefetch_related()` behavior, filters, and
   read-only context calculations.
8. Compile/import the final modules before proceeding.

Gate: only ObjectListView/ObjectView domain classes and 22 read routes remain; no form module or
mutation reverse name loads.

### Step 4 — Delete Quick Host Add and Source YAML UI

1. Delete the Quick Host Add view, form, route, navigation, templates, helper operation, exports,
   tests, and documentation.
2. Delete the Source YAML view, aliases, route, navigation, template, and UI-only tests/docs.
3. Prove Quick Host Add helper symbols have no active caller.
4. Prove Import Job still uses its loader/configured path and all Phase 1 import tests pass.
5. Prove IPAM operation exports and Job discovery remain intact.
6. Search for orphan template includes, JavaScript, constants, URLs, imports, and operation names.

Gate: both utility pages are absent end to end without removing the supported YAML Job or IPAM
paths.

### Step 5 — Make tables, navigation, and templates explicitly read-only

1. Remove all table `ButtonsColumn`, `ToggleColumn`, `actions`, and selectable `pk` columns.
2. Keep object links and useful list columns.
3. Remove the Operational Tools group if it becomes empty.
4. Keep only navigation links to the eleven retained list pages.
5. Remove review mutation buttons and DesiredNode exception-add link.
6. Add missing lifecycle, realized-link/source, assignment/source provenance, and timestamps
   needed by Section 5.7.
7. Preserve effective compute context and all safe related-object links.
8. Preserve autoescaping and whitespace display for the two prose panels.
9. Inspect final HTML rather than relying only on Python symbol absence.

Gate: every retained page remains useful for inspection and emits no mutation affordance.

### Step 6 — Update current documentation and dependent plans

Review and update at least:

- root `README.md` and `README_DEV.md`;
- `nintent/README.md`, `README_QUICK.md`, `README_DEV.md`, and `CONCEPT.md`;
- `nctl/README.md` where it links to the nintent UI;
- `nauto/README.md`;
- `devdocs/big/braindump/roadmap.md`;
- `devdocs/big/core_reconcile/roadmap.md`;
- `devdocs/big/vm/roadmap.md`;
- the active `devdocs/big/vm/p3/plan.md`; and
- `devdocs/vision/refactor/vision.md` only if a discovered fact requires correction.

Current documentation must say:

- the nintent UI is list/detail inspection only;
- YAML plus Import/Analyze own bulk structural intent;
- `nctl lifecycle` and node linking own their node fields;
- nctl plus narrow REST own Braindump/review writes;
- the Source YAML page and Quick Host Add do not exist; and
- pending compute seed work uses the canonical YAML Import contract, not forms or deleted REST.

For older roadmaps/plans, preserve historical implementation narrative but add or retain an
unambiguous supersession note where old instructions would otherwise be mistaken for current
authority. Do not rewrite completed history as though forms never existed.

Gate: no active instruction directs a user or agent to a removed UI writer or deleted Phase 2 REST
surface.

### Step 7 — Local and static verification

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

1. compile/import every edited Python module;
2. assert exactly 22 UI `path()` declarations and retained route names;
3. assert zero ObjectEditView/ObjectDeleteView/FormView/model form/Quick Host Add/Source YAML
   runtime symbols;
4. assert zero ButtonsColumn/ToggleColumn/action-field UI definitions;
5. assert no retained template refers to a removed route or emits a mutation form/control;
6. rerun the complete Phase 2 API static suite and query digest audit;
7. confirm no model/migration diff and no pending migration;
8. confirm Phase 1 Import/Analyze, IPAM, nauto, nodeutils, and ansible files are unchanged except
   for explicitly documented current-doc edits; and
9. record exact collected counts and failures.

Gate: local suites and strict searches pass, and the diff is limited to Phase 2 closure plus Phase
3 UI/documentation scope.

### Step 8 — Disposable Nautobot runtime UI proof

Use an isolated Nautobot 3.1.3 environment built from the exact local nintent source:

1. initialize and migrate an empty synthetic database through `0016`;
2. prove `makemigrations nautobot_intent_catalog --check --dry-run` reports no changes;
3. create synthetic rows for all eleven retained UI objects plus reviewed/unreviewed Braindumps and
   safe actual-link relations;
4. run the full nintent Nautobot-runtime suite;
5. introspect URL names and execute all retained/removed route tests;
6. render every retained list/detail page with its normal permission;
7. prove missing permissions are enforced;
8. prove POST attempts to retained UI routes do not change aggregate counts or row field digests;
9. inspect navigation, table columns, rendered forms/controls, and related links;
10. prove escaped prose/config content remains inert;
11. rerun the complete Phase 2 REST/GraphQL method/field matrix; and
12. retain only synthetic values, route names, status codes, field names, and aggregate counts as
    evidence.

Gate: the real framework proves that the final UI is read-only and complete, not merely that source
symbols were deleted.

### Step 9 — Disposable HTTP cross-component Phase 2 closure proof

Against the same isolated environment, expose the exact local Nautobot application on a disposable
port and use the real nctl client:

1. create a synthetic DesiredNode and uniquely matching Device with no realized link;
2. fetch real desired and actual GraphQL snapshots;
3. produce `actual_node_not_linked`;
4. run the real planner and assert the exact `link_actual_node` action/target/candidate;
5. run the real ledger executor, which must GraphQL-read, PATCH the contracted node API, and
   GraphQL-refetch;
6. fetch a fresh snapshot, compute fresh drift/plan, and assert no repeated link action;
7. exercise one lifecycle change and repeat no-op over real GraphQL/PATCH/GraphQL;
8. exercise synthetic Braindump create/update/delete and review create/replace/delete with real
   GraphQL confirmations;
9. execute representative fail-closed cases from clean/reset fixtures;
10. assert the four removed REST collections are never called;
11. do not invoke Jobs, Ansible, nodeutils, ingest, or live services; and
12. destroy only the exact disposable resources after sanitized evidence is recorded.

An empty plan, pre-linked fixture, mocked transport, or replaced executor does not satisfy this
gate.

### Step 10 — Coordinated commits and final report

1. Record before/after route, view, form, table, template, navigation, and source-line
   measurements.
2. Record Phase 2 closure results separately from Phase 3 UI results.
3. Record local, runtime, and HTTP cross-component results, including every omitted or substituted
   check.
4. Commit nintent at reviewable boundaries.
5. Commit nctl only if the mandatory Phase 2 proof reveals a real required change.
6. Update changed submodule pointers in the superproject; do not push.
7. Write `devdocs/big/interface_contract/p3/report.md` and per-step reports as useful.
8. State deployment separately: the normal successful status is **implemented, not deployed**,
   because Phase 4 owns the matched live rollout.

## 7. Required verification matrix

| Area | Required positive proof |
|---|---|
| Phase 2 REST routes | exactly three collections; four removed families non-reversible and 404 |
| Phase 2 methods/fields | complete list/detail matrix, strict writable keys, invalid inputs, zero-write failures |
| Phase 2 GraphQL | IntentSource roots absent; eleven retained roots and four pinned queries valid |
| Phase 2 nctl link | real planner/executor/API state transition and fresh non-repetition |
| Phase 2 direct writers | lifecycle and prose writers GraphQL-confirmed across disposable HTTP |
| UI route registration | exactly 22 retained list/detail names |
| Removed UI | all 37 mutation/utility names non-reversible and former literal URLs 404 |
| Retained lists | all eleven render identities, filters, useful fields, and read links |
| Retained details | all eleven render safe identity, relationships, provenance, and timestamps |
| UI methods | no retained domain page accepts a mutation POST; rows remain unchanged |
| Tables | no ButtonsColumn, ToggleColumn, edit/delete action, or bulk selection |
| Navigation | eleven retained lists; no Quick Host Add, Source YAML, or mutation link |
| Quick Host Add | view/form/URL/template/operation/export/test/current-doc contract absent |
| Source YAML UI | view/URL/template/navigation absent; Import loader and artifact retained |
| Forms | no nintent domain model mutation form remains |
| Braindump boundary | separated autoescaped user/AI panels; reviewed and unreviewed; no controls |
| Compute UI | platform/instance list/detail/effective provenance retained but read-only |
| Writer ownership | YAML/Jobs, nctl node operations, and nctl prose operations unchanged |
| Schema | migrations stay through `0016`; dry-run makemigrations clean |
| Phase 1 regression | Import/Analyze preview/apply tests and strict YAML remain |
| Isolation | disposable proof cannot reach live DB/Redis/media/API |
| Live safety | no live mutation, Job, rebuild, restart, or actuation |
| Secrets/prose | no credential or private live prose enters tracked/report evidence |

## 8. Report requirements

The final report must include:

1. status and explicit deployed/not-deployed statement;
2. exact start/end repository tuple and dirty state;
3. private evidence location, retention state, and redaction statement;
4. the Phase 2 audit table with each gap's final disposition;
5. before/after UI route manifest and counts;
6. deleted view/form/table/template/operation inventory;
7. retained list/detail/navigation/provenance/Braindump proof;
8. full REST/GraphQL runtime matrix result;
9. disposable real nctl node-link and non-repetition result;
10. lifecycle and prose writer cross-component result;
11. local/runtime test counts and migration result;
12. active/historical search classification;
13. documentation and dependent-plan updates;
14. every deviation, omitted check, or unavailable historical artifact;
15. non-mutation proof for the live environment; and
16. Phase 4 deployment handoff.

Do not include a live token, authorization header, Braindump body, Alignment Review summary, full
ObjectChange payload, raw custom-field value, or credential-bearing configuration.

## 9. Failure handling and rollback

### 9.1 Phase 2 closure failure

If the strengthened tests expose a retained Phase 2 defect:

- stop UI completion claims;
- add a focused regression test;
- fix the narrow retained contract without restoring deleted interfaces;
- rerun the complete Phase 2 closure matrix; and
- report the defect and side-effect boundary explicitly.

If the real cross-component harness cannot be made reproducible, Phase 3 may still contain useful
source changes but its status is `partially complete`, not complete.

### 9.2 Before disposable mutation

If route manifests, worktree scope, query digests, or test isolation are wrong:

- do not start disposable mutations;
- correct the baseline or plan;
- leave live services and data untouched; and
- preserve the exact failure in sanitized evidence.

### 9.3 Disposable-environment failure

If an API/UI/cross-component proof fails:

1. record whether any synthetic mutation committed;
2. preserve sanitized route/status/field and operation evidence;
3. recreate the disposable database from a known empty state;
4. fix the implementation and rerun the complete relevant transition; and
5. remove only explicitly named disposable containers, networks, volumes, and temporary
   credentials.

Never compensate by modifying live state.

### 9.4 Source rollback

No live data rollback is required because Phase 3 does not deploy.

Before Phase 4, source rollback means restoring the coordinated prior nintent/nctl commits and
superproject pointers. Do not roll back by carrying both read/write and read-only UI variants,
redirecting old routes, or restoring hidden compatibility forms.

If a post-Phase-4 live rollback is later required, Phase 4 owns the maintenance stop, database
backup restore if data changed, matched revision tuple, and verification. Phase 3 must provide the
exact source tuple and route manifests needed for that procedure.

## 10. Required searches

Search active code, tests, configuration, and current documentation for at least:

```text
ObjectEditView
ObjectDeleteView
FormView
NautobotModelForm
DesiredHostQuickAdd
desiredhost_quick_add
desiredhost_quick_add.html
quick_add_field.html
create_desired_node_with_primary_endpoint
DesiredHostCreationResult
QUICK_HOST_GENERATE_DNSMASQ
QUICK_HOST_IP_POLICY
source_yaml_intent_source_list
source_yaml_list
source_list
source_yaml_list.html
AlignmentReviewAddView
AlignmentReviewEditView
AlignmentReviewDeleteView
alignmentreview_add
alignmentreview_edit
alignmentreview_delete
ButtonsColumn
ToggleColumn
TABLE_ACTION_BUTTONS
actions
_add
_edit
_delete
form method="post"
csrf_token
type="submit"
Add an exception
Quick Host Add
Source YAML
normal Nautobot CRUD
fields = "__all__"
DesiredServiceSerializer
DesiredEndpointSerializer
DesiredComputePlatformSerializer
DesiredComputeInstanceSerializer
DesiredServiceViewSet
DesiredEndpointViewSet
DesiredComputePlatformViewSet
DesiredComputeInstanceViewSet
rest_get
@extras_features("graphql")
```

Classify, do not blindly delete:

- `_add`, `_edit`, `_delete`, `actions`, forms, and POST references belonging to retained Jobs,
  REST mutations, native Nautobot models, test utilities, or unrelated applications;
- `load_default_intent_sources` and configured-source helpers used by the Import Job;
- `operations/ipam.py` and its Job-owned writers;
- historical plans/reports/migrations;
- nctl REST mutation calls; and
- GraphQL decorators for the eleven retained models.

Expected references to removed UI surfaces are limited to:

- the parent roadmap and refactoring vision;
- historical plans/reports with explicit historical context;
- this plan and the Phase 3 final report; and
- ordinary Git history.

An active runtime import, current instruction, template reverse, URL name, navigation item, or
positive compatibility test for a removed UI surface blocks completion.

## 11. Definition of done

Phase 3 is complete in its implementation scope only when:

- every Phase 2 audit gap in Section 2 is closed with fresh reproducible evidence;
- Phase 2 defects found by the stronger proof are fixed without widening the contract;
- nintent exposes exactly the 22 retained human list/detail routes;
- every retained model in the frozen matrix remains human-inspectable;
- all nintent add/edit/delete/review mutation routes and views are absent;
- all nintent domain mutation forms are absent;
- Quick Host Add and its helper implementation are absent end to end;
- the Source YAML page is absent while the checked-in YAML and Import artifact remain supported;
- list tables have no mutation actions or bulk-selection affordances;
- navigation has no mutation/utility entry;
- retained detail pages show applicable lifecycle, realized links, provenance, timestamps, and
  safe relationships;
- the Braindump and Alignment Review remain separated, autoescaped, read-only, and
  human-inspectable;
- removed route names fail reversal and former literal URLs return 404;
- retained page POST attempts cannot change domain rows;
- the three REST mutations, canonical GraphQL reads, YAML/Job writers, and nctl adapters remain
  functional and positively confirmed;
- local, Nautobot-runtime, migration, static search, and disposable HTTP cross-component gates
  pass;
- current documentation and active dependent plans use only the final ownership/interface matrix;
- no live state was mutated, no live Job ran, and no live service was rebuilt/restarted;
- no secret or private live prose entered evidence;
- coordinated reviewable commits and superproject pointers exist without being pushed; and
- the final report truthfully states `implemented, not deployed` until Phase 4 completes the
  matched live rollout.

The strongest completion evidence is not the number of deleted forms. It is that every retained
human page still renders the state a person needs to inspect, no page can mutate that state, and
every non-UI writer still reaches only its owned field through a positively confirmed contract.
