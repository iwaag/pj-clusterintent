# Opinion 2 — Re-key `DesiredService` on `slug` and drop its Backstage identity

Date: 2026-07-31
Status: investigation report and opinion. Not a roadmap and not an implementation plan.

## Scope

This document answers one question: **which `DesiredService` fields should survive the minimal-data-field
policy, and on what grounds?**

The answer turns out not to be a list of unused fields. It is a single structural change — the model's
declared identity is a four-part Backstage entity reference that no consumer reads, while every consumer
joins on `slug`. Four fields exist only to serve that key. Removing them is a consequence of fixing the
key, not an independent cleanup.

Whether `DesiredService` should exist **at all** is deliberately out of scope; see the closing section.

## Origin of this investigation

The question that started it was: *"nintent's desired state follows a minimal-data-field policy — start
from the minimum and add only what is needed. But `DesiredService` was designed before that policy was
fixed, so it probably still carries fields added on a 'we might use this' basis, plus artifacts of the
old Backstage-oriented era such as Source Catalog Path. Should those be removed?"*

The premise is right in direction and wrong in one detail: **`source_catalog_path` and the rest of that
generation were already removed from the database** by
[0019_reduce_desired_state_schema.py](../../../nintent/nautobot_intent_catalog/migrations/0019_reduce_desired_state_schema.py).
What is still visible is a stale template (§2.1). Correcting that detail matters, because it moves the
argument from "there is old junk in the schema" to "the schema is already small, and what remains is
small **but wrongly shaped**" — which is a different and more valuable finding.

## 1. What is actually left

`DesiredService` carries seven fields
([models.py:116-134](../../../nintent/nautobot_intent_catalog/models.py#L116-L134)):

| Field | Declared at |
|---|---|
| `name` | [models.py:116](../../../nintent/nautobot_intent_catalog/models.py#L116) |
| `slug` | [models.py:117](../../../nintent/nautobot_intent_catalog/models.py#L117) |
| `service_type` | [models.py:118-122](../../../nintent/nautobot_intent_catalog/models.py#L118-L122) |
| `lifecycle` | [models.py:123-127](../../../nintent/nautobot_intent_catalog/models.py#L123-L127) |
| `intent_source` (FK) | [models.py:128-132](../../../nintent/nautobot_intent_catalog/models.py#L128-L132) |
| `catalog_namespace` | [models.py:133](../../../nintent/nautobot_intent_catalog/models.py#L133) |
| `catalog_metadata_name` | [models.py:134](../../../nintent/nautobot_intent_catalog/models.py#L134) |

The uniqueness constraint is
`(intent_source, catalog_namespace, catalog_metadata_name, service_type)`
([models.py:140-150](../../../nintent/nautobot_intent_catalog/models.py#L140-L150)), mirrored as the batch
identity key at [batch.py:49](../../../nintent/nautobot_intent_catalog/batch.py#L49).

## 2. Findings

### 2.1 The Backstage-era fields are gone from the schema; the UI still shows them

[templates/nautobot_intent_catalog/desiredservice.html:22-91](../../../nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desiredservice.html#L22-L91)
renders eleven rows for attributes that migration 0019 deleted: `display_name`, `source_ref`,
`source_catalog_path`, `catalog_kind`, `catalog_owner`, `catalog_lifecycle`, `prefers_gpu`,
`min_memory_gb`, `last_analyzed_at`, `requirements`, `analysis_provenance`. Django templates resolve a
missing attribute to the empty string rather than raising, so each renders as `-` and nothing fails.

The same class of leftover exists outside `DesiredService`:

- `DesiredNodeTable` declares `intent_source = tables.LinkColumn()` and lists it in both `fields` and
  `default_columns` ([tables.py:101,117,126](../../../nintent/nautobot_intent_catalog/tables.py#L101)),
  but `DesiredNode.intent_source` was removed by the same migration. Verified 2026-07-31 in the live
  Django shell: the table **does not raise** — it renders a permanently empty "Intent Source" column for
  all 5 nodes.
- [desirednode.html:40,48](../../../nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/desirednode.html#L40)
  renders the removed `intent_source` and `description`.

This is worth stating plainly because it is the mechanism by which the whole question arose: **a schema
reduction landed without its read surfaces, so the UI kept advertising fields the database no longer
has.** Any future reduction phase should treat template/table sweep as part of the migration, not a
follow-up.

### 2.2 Four of the seven fields are constant or duplicated in live data

Queried 2026-07-31 via GraphQL against `http://localhost:8000` — all 7 rows:

| slug | `name` | `catalog_metadata_name` | `catalog_namespace` | `service_type` | `lifecycle` |
|---|---|---|---|---|---|
| `dnsmasq` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `grafana` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `haos` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `nomad` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `pj-voxel3dprint` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `prometheus` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |
| `prometheus-node-exporter` | = slug | = slug | `default` | `SERVICE` | `ACTIVE` |

`name`, `slug`, and `catalog_metadata_name` hold the same string in every row. `catalog_namespace` and
`service_type` are constant. `intent_source` takes two values, `infrastructure` (5 rows) and `manual`
(2 rows), and is used for nothing but grouping.

Constancy alone is a weak argument — a field can be legitimately constant today. The findings below are
the substantive ones.

### 2.3 The declared identity is a four-tuple that no consumer reads

The reconcile path resolves services **by `slug`**, in three places:

| Site | Code |
|---|---|
| [planner.py:58](../../../nctl/src/nctl_core/reconcile/planner.py#L58) | `services_by_slug = {service.slug: service for service in snapshot.desired.services}` |
| [planner.py:82](../../../nctl/src/nctl_core/reconcile/planner.py#L82) | `next((s for s in snapshot.desired.services if s.slug == target.slug), None)` |
| [executor.py:811](../../../nctl/src/nctl_core/reconcile/executor.py#L811) | `services_by_slug = {s.slug: s for s in snapshot.desired.services}` |

Everything else joins on `id` (placements carry `service_id`). A repository-wide grep for
`intent_source` under `nctl/src/` returns **zero hits**; `catalog_namespace` and `catalog_metadata_name`
appear only in the GraphQL selection set
([desired.py:139-140](../../../nctl/src/nctl_core/sources/desired.py#L139-L140)), the Pydantic model
([desired.py:266-267](../../../nctl/src/nctl_core/sources/desired.py#L266-L267)), and the row parser
([desired.py:430-431](../../../nctl/src/nctl_core/sources/desired.py#L430-L431)). They are fetched,
parsed, stored, and never read.

So the database asserts one identity and the system operates on another. That divergence is the root
finding; §2.4-§2.8 are its consequences.

### 2.4 `slug` — the key everyone uses — has no uniqueness constraint

`DesiredService.slug` is `models.SlugField(max_length=255)` with no `unique=True`
([models.py:117](../../../nintent/nautobot_intent_catalog/models.py#L117)). Nothing prevents two rows
under different `intent_source` values from sharing a slug.

If that happened, [planner.py:58](../../../nctl/src/nctl_core/reconcile/planner.py#L58) would silently
keep whichever row iterated last, and [planner.py:82](../../../nctl/src/nctl_core/reconcile/planner.py#L82)
would take whichever iterated first — two sites in the same module disagreeing about which service a
`service`-kind diff refers to, with no error and no warning. Live data is currently 7 rows / 7 distinct
slugs (verified 2026-07-31), so this is latent, not active.

This is a genuine defect independent of the minimality question, and it is fixed for free by the change
proposed in §4.

### 2.5 `DesiredService` is the only desired model that is not slug-keyed

From [batch.py:46-49](../../../nintent/nautobot_intent_catalog/batch.py#L46-L49):

| Kind | Identity key |
|---|---|
| `intent_source` | `("slug",)` |
| `desired_node` | `("slug",)` |
| `desired_ip_range` | `("slug",)` |
| `desired_compute_platform` | `("slug",)` |
| **`desired_service`** | **`("intent_source", "catalog_namespace", "catalog_metadata_name", "service_type")`** |

All four slug-keyed models carry `unique=True` on `slug`; `DesiredService` is the only `Desired*` model
with a `slug` field that does not (verified 2026-07-31 via `_meta.get_field("slug").unique` in the live
Django shell). The exception is not motivated by anything in the current system — it is the shape a Backstage
`kind:namespace/name` entity reference takes when copied into a relational schema.

### 2.6 `service_type` is carried end to end and branched on nowhere

It is selected in GraphQL ([desired.py:137](../../../nctl/src/nctl_core/sources/desired.py#L137)),
lower-cased on parse ([desired.py:428](../../../nctl/src/nctl_core/sources/desired.py#L428)), and copied
into the expected-facts dict ([evaluation.py:65](../../../nctl/src/nctl_core/drift/evaluation.py#L65)).
No code anywhere compares it to a value. The eight-member `SERVICE_TYPE_CHOICES` enum
([models.py:82-99](../../../nintent/nautobot_intent_catalog/models.py#L82-L99)) — `website`, `worker`,
`database`, `queue`, `storage`, `agent`, `other` — is a taxonomy imported from Backstage's
`spec.type`, and seven of its eight members have never been used.

Note the coupling: `service_type` is *both* dead weight *and* a constraint component, so it cannot be
dropped without touching the identity key. That is the clearest single illustration of why this cleanup
is one change rather than several.

### 2.7 `IntentSource` is a one-column table that nothing can read

After 0019 stripped eleven fields
([0019:16-26](../../../nintent/nautobot_intent_catalog/migrations/0019_reduce_desired_state_schema.py#L16-L26)),
`IntentSource` is `slug` and nothing else
([models.py:61-75](../../../nintent/nautobot_intent_catalog/models.py#L61-L75)). It holds two rows,
`infrastructure` and `manual` (verified 2026-07-31).

It carries **no** `@extras_features("graphql")` decorator — unlike every `Desired*` model — so it is not
in the GraphQL schema at all. A live query for `intent_sources` returns
`Cannot query field 'intent_sources' on type 'Query'`. **nctl cannot read it even in principle.** Its
entire function is to be one quarter of the key described in §2.3, and it still costs a model, a table, a
list view and a detail view ([views.py:49-60](../../../nintent/nautobot_intent_catalog/views.py#L49-L60)),
two URLs ([urls.py:11-12](../../../nintent/nautobot_intent_catalog/urls.py#L11-L12)), a nav entry
([navigation.py:30](../../../nintent/nautobot_intent_catalog/navigation.py#L30)), a table, a filterset,
and a template.

### 2.8 The composite key makes the operator document verbose for no gain

Every placement must name its parent service as a four-key nested object
([.local/desired-state.yaml:294-301](../../../.local/desired-state.yaml)):

```yaml
- op: upsert
  kind: desired_service_placement
  key:
    desired_service:
      catalog_metadata_name: dnsmasq
      catalog_namespace: default
      intent_source: manual
      service_type: service
    instance_name: dnsmasq
```

Five lines to say `dnsmasq`. Compare `desired_node: agdnsmasq` on the next line of the same document.
[intent_contract.py:38-51](../../../nintent/nautobot_intent_catalog/intent_contract.py#L38-L51) enforces
that all four keys be present and exact.

That module is itself dead: a repository-wide grep for `intent_contract` finds **no importer** in
`nautobot_intent_catalog/` or `nctl/`. All 98 lines are unreachable, and
`validate_desired_service_reference` is not what actually validates batch input — `batch.py` is. Worth
folding into the same sweep.

### 2.9 `name` versus `slug`: two fields, one value, two consumers

Both are `SlugField(max_length=255)` and hold identical values in all live rows (§2.2). They have
different readers:

- `slug` — the reconcile join key (§2.3).
- `name` — the display label in drift targets
  ([service_evaluation.py:26,34,39](../../../nctl/src/nctl_core/drift/service_evaluation.py#L26)) **and**,
  more consequentially, the key of the per-node observation hints map
  ([observation.py:82,90,96](../../../nctl/src/nctl_core/observation.py#L82)), which is what carries
  `managed_files` digests to nodeutils.

So `name` is load-bearing today; it is not a free deletion. But since both fields are constrained to slug
syntax and hold the same value, keeping two is redundancy, not expressiveness. Collapsing `name` into
`slug` requires one nctl-side change (`service_names` keyed on `service.slug`) that is behaviour-neutral
on current data.

This is the one item in this document that is genuinely optional. Deleting `name` is defensible; keeping
it as a human label distinct from the machine key is also defensible. It should be decided on its own
merits, not bundled.

### 2.10 `lifecycle` is the only field with real behaviour, and should stay

[service_evaluation.py:24-30](../../../nctl/src/nctl_core/drift/service_evaluation.py#L24-L30) raises a
`service_lifecycle_inactive` gap with a `review_service_lifecycle` action for `deprecated`/`retired`, and
a `missing_service_lifecycle` gap when empty. With `DesiredDependency` retired per
[opinion1.md](opinion1.md), this becomes the **only** service-level drift signal that exists.

Keep it. Whether the six-member choice list should shrink (`proposed`/`planned`/`approved` are unused,
and `DesiredNode.LIFECYCLE_CHOICES` at
[models.py:245-251](../../../nintent/nautobot_intent_catalog/models.py#L245-L251) already has five) is a
separate, smaller question.

### 2.11 Nothing outside nintent and nctl references any of it

`nauto`, `nodeutils`, and `ansible_agdev` contain zero references to `intent_source`, `catalog_namespace`,
`catalog_metadata_name`, or `service_type`. `nauto` explicitly asserts it writes no nintent rows
([test_seed_home_cluster_ownership.py:28-36](../../../nauto/tests/test_seed_home_cluster_ownership.py#L28-L36)).
There is no downstream contract to break.

### 2.12 Context: five of seven services have no placement

Verified 2026-07-31: `dnsmasq` and `pj-voxel3dprint` have one placement each; `grafana`, `haos`, `nomad`,
`prometheus`, and `prometheus-node-exporter` have none. Those five therefore have no path to any
generated artifact or actuation — they are catalog entries only.

This is recorded as context, not as an argument for removal. It does mean the blast radius of the change
proposed here is two rows' worth of real behaviour.

## 3. Removal surface

Recorded as evidence that the change is bounded, not as a plan.

**nintent** (excluding migrations):

- `models.py` — `IntentSource` class (61-75); `DesiredService.service_type` (118-122),
  `intent_source` (128-132), `catalog_namespace` (133), `catalog_metadata_name` (134); the
  `nic_unique_desired_service_entity` constraint (140-150), replaced by `unique=True` on `slug`
- `batch.py` — `intent_source` in `KIND_ORDER` (11), `_KEYS` (46, 49), `_FIELDS` (56, 62),
  `_CREATE_REQUIRED` (69, 74), the model map (202), `_REFERENCE_KIND` (219), and the cascade table (269)
- `api/views.py:58` — `_BATCH_MODELS` entry
- `views.py` — `IntentSourceListView`/`IntentSourceView` (49-60), imports (17, 30, 43), and the
  `select_related("intent_source")` on both service views (66, 74)
- `urls.py:11-12`, `navigation.py:30` ("Intent Sources" nav item)
- `tables.py` — `IntentSourceTable` (27-39), `intent_source` on `DesiredServiceTable` (46, 59, 66)
- `filters.py` — `IntentSourceFilterSet` (27-41), `service_type` (55) and `intent_source` (57) on
  `DesiredServiceFilterSet`
- `templates/…/intentsource.html` (whole file); `desiredservice.html` — the eleven stale rows within
  22-91 and the Intent Source row (34-43)
- `intent_contract.py` — entire module (§2.8), unreferenced
- `tests/factories.py` (41-45, 66, 68-69), `tests/test_batch.py`, `tests/test_batch_api.py`,
  `tests/test_ui_contract.py` (249, 258-259)
- one migration; `CONCEPT.md`, `README_QUICK.md`, `README_DEV.md` mentions

**Unrelated stale surfaces to sweep at the same time** (§2.1): `DesiredNodeTable.intent_source`
(tables.py 101, 117, 126) and `desirednode.html` 40, 48.

**nctl**:

- `sources/desired.py` — `service_type`/`catalog_namespace`/`catalog_metadata_name` in the GraphQL block
  (137, 139-140), the model (264, 266-267), and `_build_service` (428, 430-431)
- `drift/evaluation.py:65` — `service_type` in `_expected_service_facts`
- test fixtures in `nctl/tests/` that construct `DesiredService` with these kwargs
  (`test_sources_desired.py`, `test_drift_render.py`, `test_mixed_node_orchestration.py`,
  `test_observation.py`, and others)

**Operator input**: `.local/desired-state.yaml` loses its two `intent_source` operations and collapses
each `desired_service` key to a single `slug`.

## 4. Opinion

**Re-key `DesiredService` on `slug`, and drop `intent_source`, `catalog_namespace`,
`catalog_metadata_name`, and `service_type` as a consequence. Keep `slug` and `lifecycle`. Decide `name`
separately.**

The framing matters more than the field list. "These fields are unused, delete them" is a weak
justification that invites the reply *"but they might be used later."* The actual justification is
stronger and does not depend on predicting the future:

1. **The model's declared identity is not the identity the system uses.** Every reconcile-path lookup
   goes through `slug` (§2.3). A schema whose uniqueness constraint describes something other than how
   rows are actually addressed is a correctness hazard, not merely surplus.
2. **The key everyone relies on is unconstrained** (§2.4), and two sites in one module would resolve a
   collision differently. Adding `unique=True` to `slug` is the fix, and once `slug` is unique the
   four-part key has no remaining job.
3. **It restores a rule that already holds everywhere else.** Four of five keyed desired models use
   `slug` alone (§2.5). Making `DesiredService` the fifth removes an exception a reader must otherwise
   learn and remember.
4. **The removed fields cannot be reintroduced by accident.** They are Backstage `catalog-info.yaml`
   entity-reference components (§2.6, §2.7) with no writer left — the importer, loaders, and the
   `AnalyzeIntentSources` Job are all gone (per [opinion1.md §2.3](opinion1.md)). Nothing produces these
   values but an operator typing them by hand into a key they gain nothing from.

Secondary benefits: the operator document loses five lines per placement (§2.8), a dead 98-line module
goes with it, and the same sweep can finally retire the read surfaces migration 0019 left behind (§2.1).

Two cautions:

- **Order matters against opinion1.** `DesiredDependency` removal touches
  `DesiredServiceTable.dependency_count`, the dependency panel in `desiredservice.html`, and the same
  factories/UI tests. Doing opinion1 first means `DesiredService`'s table, template, and tests are
  rewritten once instead of twice.
- **Sequence the migration in two steps.** `service_type` is a constraint component (§2.6), so the
  constraint must be swapped for `slug`-unique *before* the field can be dropped. Live data is 7 rows
  with 7 distinct slugs, so the unique index will build.

Finally, note what this opinion does *not* claim. It does not claim minimality is served by deleting
whatever is currently constant — `lifecycle` is nearly constant too and should stay (§2.10), and `name`
is redundant but load-bearing (§2.9). The test applied throughout is whether a field carries intent that
some consumer acts on, which is the same test [devdocs/vision/refactor/vision.md](../refactor/vision.md)
sets: *the smallest system that still preserves user intent.*

## 5. Facts to re-verify before acting

Everything above was verified on 2026-07-31 against the working tree, the live Nautobot at
`http://localhost:8000` (GraphQL and Django shell), and the live database. Before a change phase
executes:

- re-confirm `DesiredService.slug` values are still distinct across all rows — a duplicate would mean the
  `unique=True` migration fails and the collision in §2.4 has become real;
- re-confirm `service_type` is still a single value and that no code has begun branching on it;
- re-confirm no importer has appeared for `intent_contract.py`, and no `@extras_features("graphql")` has
  been added to `IntentSource`;
- re-confirm `nauto` / `nodeutils` / `ansible_agdev` still contain zero references (§2.11);
- confirm opinion1's `DesiredDependency` removal has landed, or explicitly accept doing the shared UI
  surfaces twice.

## Out of scope

**Whether `DesiredService` should exist at all.** After this change and opinion1's, the model is
`slug` + `lifecycle` — a grouping node holding no operational facts, while `deployment_profile` and
`config` on `DesiredServicePlacement` hold everything that actuates. Five of its seven rows have no
placement (§2.12). The question *"could placements carry a service slug directly?"* is legitimate and
follows naturally, but `lifecycle` is the only service-level drift signal left (§2.10) and the model is a
drift target kind in its own right. That trade deserves its own opinion; mixing it into this one would
make neither decidable.

Also out of scope: shrinking `LIFECYCLE_CHOICES` (§2.10), and whether `name` should collapse into `slug`
(§2.9).
