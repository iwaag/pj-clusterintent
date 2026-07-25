# Phase 1 Step 4 — Refactor Import into read-only plan and atomic apply

Parent: [plan.md](plan.md), Step 4.

## 1. Ownership-split helper functions (`importers.py`)

- `desired_node_update_fields(node, intent_source_id=None)`: everything `desired_node_defaults()`
  returns except `lifecycle` — create-only, per Section 5.3.
- `desired_service_entry_update_fields(entry)`: exactly `{lifecycle, notes}` — every other field
  (`requirements`, `name`/`slug`/`display_name`, and every Analyze-owned catalog/source field) is
  never in the update-owned set, so a re-import cannot reset them.
- `desired_service_entry_locked_fields(entry)`: `{name, slug, display_name}` — a disagreement
  here blocks the whole row as a `conflict` (Section 5.3's explicit "emit an ownership conflict
  instead of overwriting or silently ignoring the disagreement").

## 2. `ImportIntentSources` Job (`jobs.py`)

- Public variables are now exactly `source_file` and `apply` (`BooleanVar`, default `false`).
  `disable_missing` and `preview` are deleted, not aliased.
- `run()` is now: load → (if loader errors, emit a blocked/errors-only artifact and raise) →
  `_plan_import()` (always, read-only) → if `apply` and the plan has no `conflict` objects,
  `_apply_import()` inside `transaction.atomic()` → `_confirm_import()` → assemble and write the
  one `intent-import-result.json` / `nintent.intent-import.v1` artifact via
  `import_plan.build_artifact()`. `apply=false` never reaches `_apply_import()` — structurally,
  not just behaviorally, since the `if apply:` branch is the only caller.
- `_plan_import(load_result)`: read-only, walks all nine roots in canonical order, fetches
  existing rows via `.values()` (plain dicts, no model instances), resolves each cross-root
  reference (`intent_source`, `desired_node`, `desired_endpoint`, `platform`, `desired_service`)
  against the union of already-existing rows and rows planned for creation in this same
  document; an unresolvable reference becomes a `conflict` object (via
  `import_plan.unresolved_reference()`) rather than raising, so one bad row doesn't prevent the
  rest of the document from being planned/reported. Delegates every create/update/unchanged/
  conflict decision to the pure `plan_upsert()` from Step 1.
- `_apply_import(load_result)`: only called when the plan is clean; re-resolves and writes via
  `_validated_upsert_split()`, which writes only `update_fields` on an existing row (never
  `create_fields`), and raises (aborting/rolling back the whole transaction) if a `locked_fields`
  entry disagrees — a defense-in-depth precondition recheck, since `_plan_import()` already
  refused to reach apply in that case.
- `_confirm_import(load_result)`: post-commit, refetches every planned `DesiredNode`/
  `DesiredService` by natural key and compares the update-owned fields against what was
  requested, returning a mismatch list (empty ⇒ `confirmation.status=confirmed`).
- Deleted `_import_intent_rows`, `_validated_upsert`, `_validated_upsert_diff`, and
  `_object_matches_defaults` (superseded). Kept `_resolve_desired_node`,
  `_resolve_desired_compute_platform`, `_resolve_desired_service`, `_resolve_desired_endpoint`,
  `_intent_source_lookup`, `_json_safe` — still used by `_apply_import`/`_confirm_import`.

## 3. Artifact

One filename (`intent-import-result.json`) and one schema (`nintent.intent-import.v1`) for both
preview and apply, assembled by the shared `import_plan.build_artifact()` from Step 1: `mode`,
`source` (configured/resolved path, sha256, best-effort git revision), `scope.counts_by_root`
(every root, including zero-count ones), `objects`/`conflicts` (sorted deterministically by
`(root, identity)`), `errors`, `totals`, `writes.{requested,attempted,committed}`,
`transaction.{status,error}`, `confirmation.{status,mismatches}`. `writes.requested` is exactly
`apply`; a preview always reports `attempted=false`/`committed=false`/
`transaction.status=not_requested`; a blocked apply reports `transaction.status=blocked` without
claiming an attempt; a failed apply reports `transaction.status=rolled_back` with the exception
class/message, never silently claiming `committed=false` alone.

## 4. Test updates

Updated `tests/test_jobs_import.py` for the new `_validated_upsert_split()` API (idempotent
no-op, create, update, a new test proving a preserved field like `lifecycle` is never touched
even when `create_fields` disagrees, and a new test proving a `locked_fields` disagreement
raises); replaced `ValidatedUpsertDiffTests` (tested the deleted `_validated_upsert_diff`) with
`ImportSourceInfoAndCountsTests` for the new `_import_counts_by_root()`/`_project()` helpers.

## 5. Verification

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: 210 tests, `OK` — all four Step
1 ownership-function errors now resolved, no regression anywhere else. `python3 -m py_compile`
on `jobs.py`/`importers.py`/`loaders.py`/`import_plan.py`: clean. `nauto` suite (110 tests):
unaffected, `OK`.

The full ORM-backed plan→apply→confirm path (`_plan_import`/`_apply_import`/`_confirm_import`)
cannot be exercised by this local Django-free suite — Nautobot is not installed here, so
`jobs = ()` and the Job class body never executes locally, same as before Phase 1. That live
proof is Step 8's explicit responsibility (disposable Nautobot database), not this step's.

## Gate

Satisfied: `preview` invokes no mutation method (architecturally, since the `if apply:` guard is
the only path that calls `_apply_import`); `apply=true` is all-or-nothing
(`transaction.atomic()`, single exception handler); ownership conflicts (`DesiredService`
`name`/`slug`/`display_name` disagreement) are reported as `conflict` before any write is
attempted; preview and apply plans are structurally identical for the same DB state (both call
`_plan_import()`). Proceeding to Step 5.
