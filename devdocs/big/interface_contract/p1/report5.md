# Phase 1 Step 5 — Refactor Analyze into read-only plan and explicit apply

Parent: [plan.md](plan.md), Step 5.

## 1. New pure module: `analysis_plan.py`

- `is_dependency_scope_complete(service)`: a service's dependency `delete` actions are only
  authorized when that service's own analysis has no `malformed_dependencies` (plan Section
  6.2/6.3) — a service with no `analysis` block, or with malformed dependency refs, never
  authorizes deleting a retained dependency for that same service; create/update/unchanged are
  still reported normally.
- `dependency_planned_objects(...)`: converts one `plan_dependency_sync()` result (already pure,
  from Braindump/Phase 4) into `PlannedObject`s, gating `delete_keys` behind
  `is_dependency_scope_complete()` and reporting a gated delete as `unchanged` with
  `resolution_status`/`resolved_service`/`notes` listed as `preserved_fields` instead.

## 2. New artifact shape: `import_plan.build_analysis_artifact()`

Analyze's artifact shape differs from Import's (plan Section 6.4): no `scope`/`source`,
`selected_sources`/`inputs` instead, `totals_by_model_and_action` instead of a flat `totals`, and
per-object dicts omit `root`. A dependency `delete` action names the owning service (nested
`desired_service` identity) and the complete dependency natural key
(`dependency_kind`/`namespace`/`name`).

## 3. `AnalyzeIntentSources` Job (`jobs.py`)

- Public variables are now `fetch_timeout`, `include_disabled`, and `apply` (`BooleanVar`,
  default `false`).
- `run()`: fetch/normalize via the unchanged `analyze_intent_sources()` → `_plan_analysis()`
  (always, read-only) → if `apply` and the plan has zero conflicts/errors, `_apply_analysis()`
  inside `transaction.atomic()` → `_confirm_analysis()` → assemble and write the one
  `intent-analysis-result.json` / `nintent.intent-analysis.v1` artifact.
- `_plan_analysis()`: for each analyzed `IntentSource`, plans the `last_import_status`/
  `last_imported_at`/`last_import_summary` update (always non-empty since the timestamp legitimately
  changes every run — this is the field's purpose, not a repeat-idempotence violation). For each
  analyzed `DesiredService`, rejects duplicate dependency keys as a plan-level error (no write
  attempted for that service), then plans the service via `plan_upsert()` using
  `desired_service_create_defaults()`/`desired_service_update_fields()` (already correctly scoped
  from Phase 4 — no `lifecycle`/`requirements`/`name`/`slug`/`display_name` in the update-owned
  set), then plans that service's dependencies via `dependency_planned_objects()`.
- `_apply_analysis()`: only reached when the plan is clean; mirrors the pre-Phase-1 write logic
  (`select_for_update()`, `full_clean()`, `bulk_create()`/`update()`/`delete()`) but additionally
  gates dependency deletion behind `is_dependency_scope_complete()`.
- `_confirm_analysis()`: post-commit, refetches every planned `DesiredService` and compares the
  update-owned fields.
- Deleted the standalone `PreviewIntentSourceAnalysis` Job entirely (no alias, no wrapper);
  `Analyze` preview now covers its unique read-only information (source/catalog detection
  status, `desired_services` count) through the artifact's `selected_sources`/`inputs`/`objects`,
  without logging the full desired-service payload as the old Job's
  `include_service_preview=True` default did.
- `jobs = (ImportIntentSources, AnalyzeIntentSources, ReconcileDesiredIPAMIntent)` — 3 registered
  Jobs, matching plan Section 9.1's "Job discovery: nintent 3 retained Jobs".

## 4. Verification

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: 216 tests, `OK`. `python3 -m
py_compile` on `jobs.py`/`analysis_plan.py`/`import_plan.py`: clean. A repository-wide search for
`PreviewIntentSourceAnalysis`/`include_service_preview` inside `nintent/nautobot_intent_catalog`
returns zero matches — no alias, no dead reference. `nauto` suite (110 tests): unaffected, `OK`.

As with Step 4, the full ORM-backed plan→apply→confirm path cannot be exercised locally (Nautobot
is not installed; `jobs = ()` here). That live proof is Step 8's responsibility.

## Gate

Satisfied: one `AnalyzeIntentSources` Job covers preview/apply; preview writes nothing
(`_apply_analysis()` is reached only through the `if apply:` guard, same architecture as Import);
apply touches only analysis-owned fields (source/catalog fields via `desired_service_update_fields()`,
`analysis_provenance`, dependency create/update/gated-delete); no old Preview Job registration or
alias remains. Proceeding to Step 6.
