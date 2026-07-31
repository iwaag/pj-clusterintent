# minimize_desired_services — Implementation Plan

Implements [devdocs/vision/minimize_system/opinion2.md](../../opinion2.md). Read it first; this document
does not restate the evidence.

Goal: make `slug` the sole identity of `DesiredService`, and drop the four fields that exist only to serve
the old Backstage four-part key — `intent_source`, `catalog_namespace`, `catalog_metadata_name`,
`service_type` — plus the `IntentSource` model and the dead `intent_contract.py`.

End state: `DesiredService` = `slug` (unique) + `lifecycle`, and optionally `name`.

## Why this is worth doing

An agent turning a braindump into intent has to pick values for every field in the key. Today that key is
a four-tuple whose components are a Backstage entity reference — the agent must invent an `intent_source`,
a `catalog_namespace`, and a `service_type` that nothing reads and nothing validates against reality, and
get all four byte-identical again the next time it references the same service. Four chances to produce a
duplicate row that looks correct. `slug` alone is one chance, and the database rejects the collision.

The same argument runs the other way for the deterministic half: `slug` is already what the reconcile path
joins on, so making it the declared identity is aligning the schema with the code, not changing behaviour.

Existing rows are exploration filler with no protective value. Drop columns and tables freely; rewrite
`.local/desired-state.yaml` and re-apply rather than migrating data.

This is a coordinated breaking change under [README_DEV.md:87-104](../../../../../README_DEV.md#L87-L104):
one rollout, final contract everywhere, superseded implementation deleted. In particular the batch API
must **not** learn to accept both the old four-key `desired_service` reference and the new `slug` one —
a dual reader is exactly the artifact the policy names. Django migration history stays.

## Prerequisite

Land [cull_desired_dependency](../cull_desired_dependency/plan.md) first. It rewrites
`DesiredServiceTable`, `desiredservice.html`, `factories.py`, and the UI-contract tests — the same files
this plan touches. Doing it after means editing them twice.

## Ordering constraint

**nctl's read side first, then nintent's schema.** nctl selects `service_type`, `catalog_namespace`, and
`catalog_metadata_name` in its GraphQL query
([sources/desired.py:137-140](../../../../../nctl/src/nctl_core/sources/desired.py#L137)); dropping the
model fields first breaks every `nctl drift` until nctl catches up.

Within that, commit splitting, migration splitting, and test restructuring are the implementer's call.

## Step 1 — nctl stops reading the doomed fields

- `sources/desired.py` — remove `service_type`, `catalog_namespace`, `catalog_metadata_name` from the
  GraphQL selection (137, 139-140), the `DesiredService` model (264, 266-267), and `_build_service`
  (428, 430-431).
- `drift/evaluation.py:65` — `service_type` in `_expected_service_facts`.
- Fixtures in `nctl/tests/` construct `DesiredService(...)` with these kwargs
  (`test_sources_desired.py`, `test_drift_render.py`, `test_mixed_node_orchestration.py`,
  `test_observation.py`, and others) — drop them.

Verify: `cd nctl && uv run pytest -q --durations=20`.

## Step 2 — nintent schema

Two migrations, in this order. The first is required before the second: `service_type` is a component of
the existing unique constraint and cannot be dropped while it holds.

1. Drop `nic_unique_desired_service_entity`; add `unique=True` to `DesiredService.slug`.
2. Drop `DesiredService.service_type` / `intent_source` / `catalog_namespace` / `catalog_metadata_name`;
   delete the `IntentSource` model.

Then in `models.py`: remove `SERVICE_TYPE_*` constants and `SERVICE_TYPE_CHOICES` (82-99), the four field
declarations (118-122, 128-134), the `IntentSource` class (61-75), and the constraint block (140-150).

`batch.py`:

- `KIND_ORDER` (11) — drop `intent_source`.
- `_KEYS` (46, 49) — drop the `intent_source` entry; `desired_service` becomes `("slug",)`.
- `_FIELDS` (56, 62) and `_CREATE_REQUIRED` (69, 74) — drop the `intent_source` entry; `desired_service`
  becomes `{"slug", "lifecycle"}` / `{"slug"}` (plus `name` if kept).
- model map (202), `_REFERENCE_KIND` (219), cascade table (269).

Delete `intent_contract.py` entirely — 98 lines, zero importers. Its
`validate_desired_service_reference` enforces the very key being removed, and `batch.py` is what actually
validates batch input. Fix the stale claim in
[nintent/README_DEV.md:27-28](../../../../../nintent/README_DEV.md#L27-L28) that it is "used by the YAML loader"
(there is no loader).

## Step 3 — nintent read surfaces

Remove:

- `views.py` — `IntentSourceListView` / `IntentSourceView` (49-60), imports (17, 30, 43), and
  `select_related("intent_source")` on both service views (66, 74).
- `urls.py:11-12`; `navigation.py:30` (the "Sources" nav item).
- `tables.py` — `IntentSourceTable` (27-39), `intent_source` on `DesiredServiceTable` (46, 59, 66).
- `filters.py` — `IntentSourceFilterSet` (27-41), `service_type` (55) and `intent_source` (57) on
  `DesiredServiceFilterSet`.
- `templates/…/intentsource.html` (whole file), and in `desiredservice.html` the Intent Source row (34-43)
  plus the eleven rows within 22-91 that reference attributes migration 0019 already deleted
  (`display_name`, `source_ref`, `source_catalog_path`, `catalog_kind`, `catalog_owner`,
  `catalog_lifecycle`, `prefers_gpu`, `min_memory_gb`, `last_analyzed_at`, `requirements`,
  `analysis_provenance`).

**Sweep the same 0019 leftovers elsewhere while you are here**: `DesiredNodeTable.intent_source`
(`tables.py` 101, 117, 126) and `desirednode.html` 40 (`intent_source`) and 48 (`description`). Both
reference fields that no longer exist and render silently as empty.

Tests: `tests/factories.py` (41-45, 66, 68-69), `tests/test_batch.py`, `tests/test_batch_api.py`,
`tests/test_ui_contract.py` (249, 258-259).

Docs: `CONCEPT.md` — the `IntentSource` bullet (11) and chapter (27-36). `README_QUICK.md:36` still
lists an `Analyze Intent Sources` Job that writes "`IntentSource` status, `DesiredService` catalog
fields"; that Job no longer exists (`jobs.py` holds only `ReconcileDesiredIPAMIntent`). Delete the row.

## Step 4 — the agent-facing recipes

**Do not skip this step.** [nctl/docs/add-a-basic-service.md](../../../../../nctl/docs/add-a-basic-service.md)
and [nctl/docs/register-a-new-pc.md](../../../../../nctl/docs/register-a-new-pc.md) are what an agent
reads when turning a braindump into intent. Leaving them describing the four-key form would defeat the
entire point of this change — the schema would accept only `slug` while the instructions still teach the
old shape.

- `add-a-basic-service.md` — lines 37, 43-48, 88, 93 spell out `service_type`, `intent_source`,
  `catalog_namespace`, `catalog_metadata_name`, including a worked `key:` example and a nested
  `desired_service:` reference. Rewrite both to `slug`.
- `register-a-new-pc.md` — delete §1 "One-time prerequisite: an `IntentSource`" (17-33) outright. Its
  opening claim, *"Every `DesiredNode`/`DesiredService` needs a non-null `intent_source` FK"*, is
  **already false**: migration 0019 removed `DesiredNode.intent_source`. It is a live example of the
  documentation drift this plan is correcting.
- Re-check `nctl/docs/usage_example.md` (the file `agentdocs/brainforge/README.md` tells agents to read
  first) — it had no hits at plan time, but confirm rather than assume.

## Step 5 — operator document

Rewrite `.local/desired-state.yaml`:

- delete the two `intent_source` operations;
- each `desired_service` key becomes `slug: <name>`;
- each placement's `desired_service` reference collapses from a five-line nested object to
  `desired_service: <slug>`.

Rebuild the container (`docker compose build --no-cache`, and check the log for the resolved nintent SHA —
the build caches a stale commit otherwise), `nautobot-server migrate`, restart, then
`nctl desired apply -f .local/desired-state.yaml` dry, then `--yes`.

nintent installs from GitHub, not the local checkout: commit, then **ask the user to push** before
rebuilding.

## Verification gates

Per the matrix in [README_DEV.md:48-62](../../../../../README_DEV.md#L48-L62):

| gate | where | command |
|---|---|---|
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` |
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` |
| Nautobot runtime clean | repo root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |

The runtime gate is **required**. Two migrations land here, one of them adding a unique index, and the
Django-free suite loads neither Django nor Nautobot — it cannot prove either migration applies. Use
`--clean` (not `--keepdb`): a half-built reused test database reports the failure at a different column
each run and reads like a migration defect. Record the reported `cases=` count.

Compute conformance, OpenSSH, and Ansible gates are not required — no such boundary changes.

## Exit criteria

- `grep -ri "intent_source\|intentsource\|catalog_namespace\|catalog_metadata_name\|service_type\|intent_contract"`
  over `nintent/nautobot_intent_catalog/` (excluding migrations), `nctl/src/`, `nctl/tests/`, and
  `nctl/docs/` returns nothing.
- All three gates pass, with the runtime gate's `cases=` count recorded.
- `DesiredService._meta.get_field("slug").unique` is `True`.
- The batch API rejects a four-key `desired_service` reference — no dual reader survived.
- `nctl drift` runs clean against the rebuilt instance; `nctl reconcile` dry-plans as before.
- The service list and detail pages render with no empty leftover rows, and the node list has no empty
  Intent Source column.
- Every worktree is clean.

Report status in the vocabulary of [README_DEV.md:282-300](../../../../../README_DEV.md#L282-L300).

## Optional, implementer's call: collapse `name` into `slug`

`name` and `slug` are both `SlugField(255)` holding the same value, but `name` is load-bearing: it keys
the per-node observation hints map that carries `managed_files` digests
([nctl/src/nctl_core/observation.py:82,90,96](../../../../../nctl/src/nctl_core/observation.py#L82)), and
it is the display label in drift targets
([drift/service_evaluation.py:26,34,39](../../../../../nctl/src/nctl_core/drift/service_evaluation.py#L26)).

Collapsing it means switching those readers to `service.slug` and dropping the field — behaviour-neutral
on any data where the two agree. Keeping `name` as a human label distinct from the machine key is also
defensible. Decide it on its own merits; either answer satisfies this plan's exit criteria.

## Explicitly out of scope

- Whether `DesiredService` should exist at all once it is `slug` + `lifecycle`. Real question, separate
  opinion — `lifecycle` is the only service-level drift signal left after cull_desired_dependency, and the
  model is a drift target kind in its own right.
- Shrinking `LIFECYCLE_CHOICES` from six members.
