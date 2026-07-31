# Opinion 1 — Retire `DesiredDependency`

Date: 2026-07-31
Status: investigation report and opinion. Not a roadmap and not an implementation plan.

## Scope

This document answers one question: **should `DesiredDependency` continue to exist?** It records
what the current code and the live cluster actually do with it, and argues that the model should be
retired.

What replaces it — how service-to-service or placement-to-placement dependency should be expressed
after removal — is deliberately **out of scope** and will be decided separately. Nothing here should
be read as a claim that dependency expression is unnecessary in general; the claim is only that
*this particular model, as built, is not the thing that expresses it.*

## Origin of this investigation

The question that started it was: *"nintent holds desired services and desired dependencies, but the
dependency itself carries almost no information, and a desired service depending on another desired
service cannot be expressed — is that correct?"*

The second half of that premise is **incorrect**, and it matters, because it changes the argument
from "the model lacks a feature" to "the model has the feature and nothing uses it." The first half
is correct, and understated.

## 1. The schema *can* express service → service

`DesiredDependency` has a nullable FK to `DesiredService`, and the full read/write path for it
exists end to end:

| Layer | Location | Evidence |
|---|---|---|
| Model | [nintent/nautobot_intent_catalog/models.py:189-195](../../../nintent/nautobot_intent_catalog/models.py#L189-L195) | `resolved_service = FK(DesiredService, SET_NULL)`, plus `resolution_status` with a `resolved` choice ([models.py:163-172](../../../nintent/nautobot_intent_catalog/models.py#L163-L172)) |
| Write | [batch.py:63](../../../nintent/nautobot_intent_catalog/batch.py#L63), [batch.py:219](../../../nintent/nautobot_intent_catalog/batch.py#L219) | `resolved_service` is an accepted batch field and resolves to a `desired_service` reference |
| HTTP | [api/views.py:62](../../../nintent/nautobot_intent_catalog/api/views.py#L62) | `desired_dependency` is in `_BATCH_MODELS` |
| Read | [nctl/src/nctl_core/sources/desired.py:142-152](../../../nctl/src/nctl_core/sources/desired.py#L142-L152) | GraphQL query selects `resolved_service { id }` |
| Domain | [sources/desired.py:273-282](../../../nctl/src/nctl_core/sources/desired.py#L273-L282) | `DesiredDependency.resolved_service_id` |

So the correct statement is not *"service-to-service dependency cannot be declared."* It is
**"service-to-service dependency can be declared, and declaring it changes nothing."** The model is
not missing; it is inert. That is a stronger reason to remove it, not a weaker one.

## 2. Findings

### 2.1 No consumer changes any outcome

Across the whole repository, the only code that reads a `DesiredDependency` for any purpose other
than copying it around is [nctl/src/nctl_core/drift/service_evaluation.py:31-35](../../../nctl/src/nctl_core/drift/service_evaluation.py#L31-L35):

```python
for dependency in expected["dependencies"]:
    if dependency["resolution_status"] == "unresolved":
        gaps.append({"code": "unresolved_dependency", ...})
        actions.append({"action": "resolve_service_dependency", ..., "requires_review": True})
```

That is the entire behaviour. Consequences:

- an **unresolved** dependency produces one `warning`-severity finding that is classified as
  human-review-only ([reconcile/classify.py:140](../../../nctl/src/nctl_core/reconcile/classify.py#L140));
- a **resolved** dependency produces *nothing at all*. It contributes a count to
  `dependency_counts` ([drift/evaluation.py:66-71](../../../nctl/src/nctl_core/drift/evaluation.py#L66-L71)) and is otherwise discarded.

There is no path by which `resolved_service` affects planning, ordering, actuation, convergence
status, rendering, or any generated artifact. The FK that makes the model a graph is decorative.

### 2.2 The real ordering mechanism is a different graph entirely

Actuation order *is* dependency-aware, but it reads a completely separate source:
`deployment_profile_reconciliation.<profile>.dependencies` in
[ansible_agdev/vars/deployment_profiles.yml:167-168](../../../ansible_agdev/vars/deployment_profiles.yml#L167-L168) (`grafana` → `prometheus`),
consumed by `_wire_profile_dependencies` in
[nctl/src/nctl_core/reconcile/planner.py:282-311](../../../nctl/src/nctl_core/reconcile/planner.py#L282-L311).

That graph is **profile → profile**, applies only when the two profiles' host sets overlap, is
validated for unknown names, and is cycle-checked
([reconcile/profiles.py:148](../../../nctl/src/nctl_core/reconcile/profiles.py#L148),
[profiles.py:217-229](../../../nctl/src/nctl_core/reconcile/profiles.py#L217-L229)).

So the system already carries **two dependency graphs that share nothing**: one in nintent that is
validated by nothing and consumed by nothing, and one in Ansible metadata that is validated,
consumed, and load-bearing. Keeping both means every future reader has to discover, the hard way,
which one is real.

### 2.3 There is no writer left except the operator's own hand

Historically `DesiredDependency` rows were produced automatically: the `AnalyzeIntentSources` Job
bulk-deleted and recreated all dependency rows per service on every analysis run, imported from
Backstage `spec.dependsOn` metadata. This is documented in
[devdocs/big/better_usability/p0/field-classification.md:408](../../big/better_usability/p0/field-classification.md#L408),
which also flagged that the blind delete+recreate destroyed any manual `notes`/`resolution_status`
edit.

That writer no longer exists. `nautobot_intent_catalog/jobs.py` today contains only
`ReconcileDesiredIPAMIntent`; `loaders.py` and `importers.py` are gone. The Nautobot UI views are
read-only — `DesiredDependencyListView`/`DesiredDependencyView` are `ObjectListView`/`ObjectView`
with no edit or delete view ([views.py:77-88](../../../nintent/nautobot_intent_catalog/views.py#L77-L88)).

The only remaining write path is the desired-state batch API, i.e. the operator hand-writing rows
into `.local/desired-state.yaml`. **`resolution_status` is therefore a derived field with no
deriving process.** The `resolved`/`unresolved` distinction the drift engine branches on can now
only be set by a human typing the word, which is precisely the opposite of what the field was
classified as ([field-classification.md:108-109](../../big/better_usability/p0/field-classification.md#L108-L109)
tiers both `resolution_status` and `resolved_service` as *Derived — a system match result*).

### 2.4 Live data contradicts the model's own concept

The live cluster (queried 2026-07-31 via GraphQL) holds exactly **two** `DesiredDependency` rows,
both attached to `pj-voxel3dprint`:

| dependency_kind | name | raw_ref | dependency_type | resolution_status | resolved_service | notes |
|---|---|---|---|---|---|---|
| `resource` | `blender-tool` | `host_tool:/snap/bin/blender` | `external` | `UNRESOLVED` | null | Host system blender binary |
| `resource` | `vdbmat-openvdb-cycles` | `docker:vdbmat-openvdb-cycles:blender4.5.11` | `external` | `UNRESOLVED` | null | Docker rendering image |

Neither is a service-to-service edge, and neither ever can be. One is *"a binary must exist at this
absolute path on the host"*; the other is *"this container image at this tag must be available."*
Those are host/artifact requirements, not references to a `DesiredService`, so `resolved_service`
can never be populated for them and `resolution_status` can never leave `unresolved`.

The one real-world use of the model is a use the model was not designed for, and the field that
defines the model's purpose (`resolved_service`) has **zero** live usage.

Consistent with that, `.local/desired-state.yaml` — the operator's canonical input document —
declares 6 `desired_service` and 0 `desired_dependency` operations. The two live rows predate it.

### 2.5 The result is permanent, unclearable drift noise

Because those two rows can never resolve, `nctl drift` emits two `unresolved_dependency` warnings on
every single run, forever:

```
error    service_missing         pj-voxel3dprint: service_missing
warning  unresolved_dependency   pj-voxel3dprint: unresolved_dependency
warning  unresolved_dependency   pj-voxel3dprint: unresolved_dependency
```

(Verified 2026-07-31. To be precise: `pj-voxel3dprint` is `drifting` primarily because of
`service_missing`; the two dependency warnings are not the sole cause of its status. But they are 2
of the 7 `warning`-severity findings in the whole cluster, they carry a `requires_review: true`
recommended action addressed to a human, and **no possible operator action clears them** short of
deleting the rows.)

A permanent warning that cannot be actioned is worse than no warning. It trains both the operator
and the agent to ignore the warning channel.

### 2.6 Two overlapping vocabularies, and the operator picked the wrong one

`dependency_type` is a free `CharField` and `resolution_status` is a choice field containing
`external`. The live rows set `dependency_type="external"` while leaving
`resolution_status="unresolved"` — i.e. the operator expressed *"this is satisfied outside the
system"* using the field that has no consumer, while the field that *does* have a consumer kept its
default and generated the noise in §2.5.

This is not operator error so much as a design defect: two adjacent fields with an overlapping
vocabulary, only one of which is load-bearing, and no validation relating them. Per
[nintent/CONCEPT.md:101-108](../../../nintent/CONCEPT.md#L101-L108) the intended home for `external`
is `resolution_status`. Nothing in the code enforces or even hints at that.

### 2.7 Granularity does not match the unit of actuation

The edge is `DesiredService` → `DesiredService`. The unit that is actually deployed is
`DesiredServicePlacement` (service × node × `instance_name`). A service placed on several nodes
cannot express *"the instance on node A depends on the instance on node B"*, which is the form
almost every real ordering constraint takes. Even if a consumer were written, the model's granularity
would not carry the information the consumer needs.

### 2.8 The identity key is a string, not the target

The uniqueness constraint is `(source_service, dependency_kind, namespace, name)`
([models.py:202-207](../../../nintent/nautobot_intent_catalog/models.py#L202-L207)) — the free-text
reference, not the resolved target. The same logical dependency written two ways is two rows.
`resolved_service` is an annotation bolted onto a string ref, not the edge's identity. Any future
graph built on this key inherits that ambiguity.

### 2.9 No integrity validation whatsoever

There is no check for self-dependency and no cycle detection anywhere in the nintent side
(`batch.py` contains no such validation). Compare with the profile graph, which *does* reject cycles
([profiles.py:217-229](../../../nctl/src/nctl_core/reconcile/profiles.py#L217-L229)). A dependency
model that permits `A → A` and `A → B → A` cannot be promoted to a consumer without that work being
done from scratch anyway.

### 2.10 The node at each end of the edge is nearly empty

`DesiredService` itself carries only `name`, `slug`, `service_type`, `lifecycle`,
`catalog_namespace`, `catalog_metadata_name` ([models.py:116-134](../../../nintent/nautobot_intent_catalog/models.py#L116-L134)).
`requirements` was removed from the schema; nctl retains an empty-dict stub purely so the evaluator
contract does not change ([sources/desired.py:268-270](../../../nctl/src/nctl_core/sources/desired.py#L268-L270)).
Everything with operational substance lives in `DesiredServicePlacement.config` and
`deployment_profile`.

A dependency graph over nodes that hold no operational facts cannot answer any operational question.
This is also a second piece of already-dead weight sitting in the same evaluator
(`requirements_present` in [service_evaluation.py:41](../../../nctl/src/nctl_core/drift/service_evaluation.py#L41)
is always `False`), worth folding into the same cleanup.

### 2.11 Nothing outside nintent and nctl references it

`nauto`, `nodeutils`, `ansible_agdev`, and `devtests` contain **zero** references to
`DesiredDependency` / `desired_dependency`. All mentions elsewhere in the repo are historical
devdocs. There is no downstream contract to break.

## 3. Removal surface

Recorded here as evidence that removal is bounded, not as a plan.

**nintent** (excluding migrations):

- `models.py` — the `DesiredDependency` class (lines 159-213) and `DesiredService.dependencies`
  reverse relation
- `batch.py` — kind entry in `KIND_ORDER`, `_KEYS`, `_FIELDS`, `_CREATE_REQUIRED`, and the
  `resolved_service` entry in `_REFERENCE_KIND` (6 sites)
- `api/views.py:62` — `_BATCH_MODELS` entry
- `views.py` — 2 view classes (9 reference sites)
- `urls.py:15-16`, `navigation.py:37-40` ("Dependencies" nav item)
- `tables.py` — `DesiredDependencyTable`, plus `dependency_count` column on the service table
  (lines 47-51, 60, 67)
- `filters.py` — `DesiredDependencyFilterSet`
- `templates/nautobot_intent_catalog/desireddependency.html`
- `tests/test_ui_contract.py` (11 sites), `tests/factories.py` (4), `tests/test_templates.py` (1)
- one new migration to drop the table; `CONCEPT.md` §`DesiredDependency` and the Current Boundaries
  entry; `README_QUICK.md`, `README_DEV.md`, `DEVLOG_PICKUP.md` mentions

**nctl**:

- `sources/desired.py` — GraphQL block, `DesiredDependency` model, `DesiredSnapshot.dependencies`
- `drift/evaluation.py` — `_dependency_facts`, `dependencies`/`dependency_counts` in
  `_expected_service_facts`
- `drift/service_evaluation.py` — the dependency loop, `dependency_counts` in the summary,
  `evaluation_scope` string
- `reconcile/classify.py:140` — the `unresolved_dependency` code
- ~12 test files, most of which only carry `"desired_dependencies": []` fixture noise

The two live rows would need an explicit `delete` batch operation, or would be removed by the
migration.

## 4. Opinion

**Retire it.**

The decisive argument is not that the model is unused — it is that the model is *actively
misleading*. Today the system presents an operator (and an AI agent reading the schema) with a
dependency model that:

- looks authoritative — it has a resolution state machine, a typed FK, a UI list view, a nav entry,
  and a documented concept chapter;
- is consumed by nothing that changes any outcome;
- coexists with a *second*, unadvertised dependency graph in Ansible vars that is the real one;
- and, in its only real-world use, generates permanent warnings that no action can clear.

That combination costs more than an empty table. It costs every future reader the time to discover
that the obvious-looking mechanism is the wrong one, and it costs the credibility of the drift
warning channel. This is exactly the failure mode
[devdocs/vision/refactor/vision.md](../refactor/vision.md) targets: *the smallest system that still
preserves user intent* — a surface that preserves no intent anyone acts on is not paying for itself.

Two secondary points reinforce it:

1. **Removal loses no derived information.** Because there is no automated writer, everything in the
   two live rows was hand-typed by the operator and exists in prose form as well. There is no
   computed state to reconstruct.
2. **Removal is a better starting position than mutation.** If placement-level dependency is wanted
   later, building it on top of `DesiredDependency` means inheriting the string-ref identity key
   (§2.8), the service-level granularity (§2.7), the dual vocabulary (§2.6), and the absent cycle
   validation (§2.9). Every one of those is something a real design would reject. Starting from an
   empty surface is cheaper than reforming this one.

The strongest counter-argument is that the two live rows *do* encode genuine user intent —
`pj-voxel3dprint` really does need a Blender binary and a specific container image — and deleting the
rows deletes that record. That is a real cost and it should be paid deliberately: the intent should
be transcribed somewhere before the table is dropped. But note that it argues for preserving *host
and artifact requirements*, which is a different concept from a service dependency graph, and which
`DesiredDependency` was never designed to hold. It is an argument about where that intent should
live next, not an argument for keeping this model.

## 5. Facts to re-verify before acting

Everything above was verified on 2026-07-31 against the working tree and the live Nautobot at
`http://localhost:8000`. Before a removal phase executes:

- re-query `desired_dependencies` live — the count must still be small and still contain no row with
  a non-null `resolved_service`; a non-null one would mean someone started using the model as
  designed and the argument needs re-examining;
- confirm the two `unresolved_dependency` warnings are still the only dependency-sourced findings in
  `nctl drift --json`;
- confirm no new writer has appeared in `nintent/nautobot_intent_catalog/jobs.py`.

## Out of scope

How dependency (service-level, placement-level, or host/artifact requirement) should be expressed
after this removal. To be decided separately.
