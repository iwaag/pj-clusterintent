# Manual Intent Restructure Plan

## Purpose

Fixed/implicit infrastructure services (dnsmasq, prometheus, grafana, nomad,
prometheus-node-exporter, haos) are "should be running" desired state. Today they
are declared in `nauto/seed/home_cluster.yaml` under `intent_sources` +
`desired_services` and written by the `nauto` `Seed Home Cluster` Job. That blurs
the architecture boundary:

- `nintent` is the **intent / desired-state** owner.
- `nauto` is the Nautobot **Jobs + object-bootstrap** repository: base taxonomy
  (manufacturers, platforms, roles, tags) in `home_cluster.yaml`, plus
  **actual-state ingest** from nodeutils (`ingest_nodeutils_inventory`).

Seeding `DesiredService` (intent) from `nauto`'s bootstrap/actual side is an
expedient that exists only because `nintent` has no entry point for declaring
intent that has no Git repository:

- the intent YAML loader has no `desired_services` root;
- the loader's `intent_sources` root requires a `url` (no manual, slug-only
  source); `importers.intent_source_defaults` hardcodes
  `source_type="git_repository"` and the importer upserts by `url`;
- there is no `services/add/` UI route (only edit).

The data model already supports manual intent: `IntentSource.source_type` includes
`manual`, `IntentSource.url` is nullable, and `DesiredService` only needs an
`intent_source` FK. So the fix is to give `nintent` a first-class way to declare
manual/fixed desired services, and reduce `nauto` to taxonomy bootstrap + actual
ingest.

## Constraints (important)

- **Destructive-change phase.** Do not keep backward-compatibility artifacts of
  any kind except DB data migrations. No legacy code paths, no compatibility
  shims, no dual loaders, no old YAML shapes preserved "just in case." The old
  `nauto` intent-seeding path is removed, not deprecated-in-place.
- **No live environment here.** Do not assume a running Nautobot for verification.
  Validation is pure unit tests (loader/importer), matching the existing
  `nintent/nautobot_intent_catalog/tests` approach. Nautobot-runtime behavior
  (Job discovery, UI views, DB persistence) is documented for later manual
  verification, not unit-tested locally.
- **Schema impact is expected to be zero.** No new model fields are anticipated
  (`IntentSource` and `DesiredService` already model manual sources). Therefore no
  schema migration is expected. A **data migration is allowed** only if existing
  rows need reconciliation that re-import cannot do (see Step 6); none is
  anticipated because identity keys are preserved.

## Target ownership boundary

- **nintent owns all intent**, including fixed/manual services:
  - a `source_type=manual` `IntentSource` (e.g. slug `infrastructure`) is the
    provenance for non-Git intent;
  - manual `DesiredService` rows are declared in nintent's intent YAML and
    imported by `Import Intent Sources`, alongside `desired_nodes` /
    `desired_endpoints` / `desired_service_placements`.
- **nauto owns Nautobot bootstrap + actual state only**: taxonomy in
  `home_cluster.yaml` and nodeutils ingest. It no longer creates `IntentSource` or
  `DesiredService`.

Note: nintent's intent YAML source-of-truth file is currently
`nauto/seed/intent_sources.yaml` (physically in `nauto`, consumed by nintent via
`PLUGINS_CONFIG.intent_sources_file`). Relocating that file out of `nauto` is a
non-goal here (see Non-goals); this plan only changes ownership of the
`desired_services` / manual `intent_sources` content, not the file's location.

## Implementation steps

### Step 1 — [nintent] Support manual, URL-less IntentSource declarations

Goal: allow the intent YAML `intent_sources` root to declare a manual,
slug-identified source with no `url`.

- `loaders.py`:
  - Extend `IntentSourceEntry` with `slug`, `name`, and `source_type` (default
    `git_repository`).
  - Extend `_normalize_intent_source_entry` so an entry may be a manual source:
    when `source_type` is `manual` (or any non-Git type), `url` is optional and
    `slug` is required; Git entries keep requiring `url` as today. Reject unknown
    keys consistently with the other strict roots.
- `importers.py`:
  - `intent_source_defaults` / identity must stop hardcoding
    `source_type="git_repository"` and instead carry the entry's `source_type`,
    and derive `slug`/`name` from the entry (not only from `url`).
  - The intent-source upsert in `jobs.py` `_import_intent_rows` must key manual
    sources by **slug** (Git sources stay keyed by `url`). Make the identity
    selection explicit per source type.
- Acceptance (pure unit test): a YAML `intent_sources` entry
  `{slug: infrastructure, name: Infrastructure, source_type: manual}` normalizes
  without error and produces importer defaults with `source_type=manual`, no
  `url`, and slug `infrastructure`.

### Step 2 — [nintent] Add a `desired_services` import root

Goal: declare fixed/manual services in the intent YAML and import them.

- `loaders.py`:
  - Add a `DesiredServiceEntry` dataclass with the identity fields
    (`intent_source` slug, `catalog_namespace`, `catalog_metadata_name`,
    `service_type`) and the persisted display/lifecycle fields (`name`, `slug`,
    `display_name`, `lifecycle`, plus any other model-required fields).
  - Add `_normalize_desired_service_entry`, strict allowed/required key checking,
    `desired_services` section parsing in `load_intent_sources`, and duplicate
    detection on `(intent_source, catalog_namespace, catalog_metadata_name,
    service_type)`.
  - Add `desired_services` to `IntentSourceLoadResult`.
- `importers.py`:
  - Add `desired_service_defaults` (and reuse the existing
    `desired_service_identity`) for the YAML entry shape, resolving the owning
    `IntentSource` by slug.
- `jobs.py` `_import_intent_rows`:
  - Import `desired_services` **after** `intent_sources` and **before**
    `desired_service_placements`, so placement service references resolve against
    the just-imported services. Add `services_created/updated/unchanged` counts to
    the summary.
- Acceptance (pure unit test): loader parses a `desired_services` block; importer
  helpers produce the right identity/defaults; placement resolution still works
  when the service is declared in the same document.

### Step 3 — [nintent] (optional) Manual DesiredService CRUD add route

Goal: allow ad-hoc creation of a manual service in the UI.

- `urls.py`: add `services/add/` mapped to `DesiredServiceEditView` (the existing
  `DesiredServiceForm` already exposes all fields, including `intent_source`).
- `navigation.py`: optional menu entry near `Desired Services`.
- Secondary to Step 2 (YAML import is the primary path). Implement only if cheap;
  otherwise defer.

### Step 4 — [nauto] Remove intent seeding from Seed Home Cluster

Goal: stop `nauto` from creating intent.

- `jobs/seed_home_cluster.py`: remove `ensure_desired_services` and any
  intent-source seeding it performs, and their call sites in `run`. Keep taxonomy
  bootstrap (manufacturers, platforms, roles, tags, prerequisite objects).
- Drop the now-unused `nautobot_intent_catalog` import for `DesiredService` /
  `IntentSource` if nothing else needs it.

### Step 5 — [nauto] Move fixed-service intent into nintent's intent YAML

Goal: relocate the content (ownership), not invent it.

- `seed/home_cluster.yaml`: delete the `intent_sources` and `desired_services`
  blocks.
- `seed/intent_sources.yaml` (nintent's intent source-of-truth): add the manual
  `intent_sources` entry `slug: infrastructure` and the `desired_services` entries
  for prometheus, grafana, nomad, prometheus-node-exporter, haos — and add
  `dnsmasq` (the originally-missing service that motivated this work).
- Ensure the existing `desired_service_placements` in `intent_sources.yaml` still
  resolve against the moved services (same identity keys).

### Step 6 — [nintent] / [nauto] Reconciliation and data migration

Goal: ensure existing DBs converge without orphaned rows.

- Existing `infrastructure` `IntentSource` + `DesiredService` rows were created by
  the old `Seed Home Cluster`. Because identity keys (IntentSource slug, service
  catalog identity) are preserved, running `Import Intent Sources` on the updated
  intent YAML **updates the same rows in place** — no deletion needed.
- [nintent] Confirm the importer upserts (not duplicates) these rows. Document the
  one-time operator action: run `Import Intent Sources` after the move.
- Add a DB **data migration only if** a provenance key actually changes (e.g. if
  the manual source previously had a different slug or `source_type`). None is
  anticipated; do not add an empty migration.

### Step 7 — [nintent] / [nauto] Tests

- [nintent] Pure unit tests (no Nautobot):
  - loader: manual `intent_sources` entry (no url) and `desired_services` parsing,
    strict key rejection, duplicate detection;
  - importer: manual-source identity-by-slug, `desired_service_defaults`, import
    ordering so placements resolve in-document services.
- [nauto] Update/remove `Seed Home Cluster` tests that asserted desired-service /
  intent-source seeding; keep taxonomy-bootstrap tests.
- Run `python3 -m unittest discover -s nautobot_intent_catalog/tests` (nintent) and
  the nauto job test suite. Record Nautobot-runtime checks (Job discovery, import
  run, optional UI add) in `README_DEV` as manual verification, per the
  no-live-env constraint.

### Step 8 — [docs] Documentation

- [nintent] `README.md`, `README_QUICK.md`, `CONCEPT.md`, `README_DEV.md`:
  document the `desired_services` intent root and the manual `IntentSource`
  pattern for fixed services; state that all intent (including fixed
  infrastructure services) is declared and owned in nintent. Update the earlier
  claim that `DesiredService` "cannot be hand-created" to reflect the manual
  declaration path.
- [nauto] `README.md`: clarify that `nauto` provides Nautobot taxonomy bootstrap +
  actual-state ingest and no longer seeds intent; point to nintent's intent YAML
  for service intent.

## Non-goals

- Relocating nintent's intent YAML file physically out of `nauto/seed/` (could be
  a later cleanup; this plan changes content ownership, not file location).
- Reconciling/removing the legacy git-analysis duplication in
  `nauto/jobs/generate_desired_services.py` vs nintent's `analyze_intent_sources`
  (separate concern).
- Any change to the deployment_profiles flow, `Export Production Inventory`, or
  `Sync Deployment Profiles`.
- `nauto` `service_placement_review` / `ai_resource_review` behavior.
- New persistent models or generic frameworks.

## Risks / open questions

- **IntentSource identity split** (Git → url, manual → slug): slug is already
  unique on the model, so slug identity is safe; confirm no Git source relies on
  url-only identity in a way the change breaks.
- **Single canonical intent YAML location**: keeping it under `nauto/seed/` while
  declaring it nintent-owned is awkward; flag for a follow-up relocation decision.
- **Operator rollout**: after deploy, intent services exist only after
  `Import Intent Sources` runs against the updated YAML; the old `Seed Home
  Cluster` no longer creates them. Document the run order so a deploy does not
  briefly drop service intent.
