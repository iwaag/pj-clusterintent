# Phase 3 Step 3.4 — Creation-path consistency and service non-change

Parent: [plan.md](plan.md), Step 3.4.

## What the local (Django-free) suite proves

Extending the fake-Django/pure-Python tests already used across this codebase (Step 3.3's
precedent, per `README_DEV.md`'s documented local-testing limitation):

- **Host creation operation**: `test_operations_hosts.py` proves omission yields
  `lifecycle == "active"` and an explicit `"planned"` request survives unchanged. No override row
  is manufactured — `create_desired_node_with_primary_endpoint()` only builds `DesiredNode` and
  `DesiredEndpoint` objects; reviewed by inspection.
- **Strict YAML loader**: `test_loaders.py` now covers omission (`"active"`), explicit `"planned"`
  preservation, and an unrecognized value (`_choice()`'s pre-existing leniency silently falls back
  to the current default rather than erroring — unchanged validation behavior, only the fallback
  value moved from `"planned"` to `"active"`).
- **Importer**: `test_desired_node_identity_and_defaults` (pre-existing) already proves the
  importer upserts an already-normalized entry's `lifecycle` value exactly (`"approved"` in that
  fixture) with no importer-added fallback — unaffected by this phase, confirmed unchanged.
- **Seed files**: `nauto/seed/intent_sources.yaml`'s 9 desired nodes all set `lifecycle: active`
  explicitly already; the default change is a no-op for seed loading by construction (explicit
  values always win), so no seed edit or new test was needed.
- **`DesiredService` non-change**: the pre-existing `test_loader_defaults...` (line ~506 fixture)
  already proves an omitted service lifecycle stays `"proposed"`; `nctl`'s
  `test_reconcile_classify.py` already covers the `service_lifecycle_inactive` warning. Neither
  was touched by this phase's edits (verified: no diff to `DesiredService` model/loader/importer
  code in Step 3.3).
- **Production composition reaching schema 2.0**: `nctl/tests/test_production_composer.py` already
  has multiple fixtures with `lifecycle="active"` nodes reaching full composed output with
  provenance (Phase 2 coverage) — this is data-shape coverage, not code that changed, so it stays
  valid evidence that an active node with a usable endpoint and fresh observation composes
  correctly; nothing here depends on *how* the node became active.

Full nintent suite: **92 passed** (91 after Step 3.3 + 1 new unrecognized-value case). Full nctl
suite unaffected (`nctl_core` has no nintent-side dependency to update): **600 passed**.

## What is deferred to Step 3.7's live verification

Nautobot/Django are not installed in the local dev environment (confirmed in Step 3.3: `import
nautobot` fails locally), so these plan-matrix rows have no meaningful local execution path and are
verified against the real server instead, per Step 3.7:

- direct `DesiredNode` model construction (omission and explicit `planned`) — real Django field
  default behavior;
- regular `DesiredNodeForm` (ModelForm) initial/omission and explicit `planned` — confirmed by
  source inspection in Step 3.3 that no `initial` override exists, so it inherits the model
  default, but the actual form-bound behavior needs Django;
- `DesiredHostQuickAddForm` default submission and deliberate staged submission — same;
- REST `POST /nodes/` omission, explicit `planned`, and lifecycle-only PATCH — same, and this is
  also the exact code path `nctl lifecycle` PATCHes against;
- YAML import Job repeat-import / update-of-an-existing-row idempotence — this requires the live
  ORM upsert path; no fake-Django harness for the Job layer exists in this codebase today, and
  none was added speculatively.

These are not gaps introduced by this phase; they are the same class of environment-dependent
behavior every prior nintent phase report (e.g. `p2/report2.8.md`) verified live after deployment
rather than locally.

## Result

Every creation path this environment can exercise without a running Nautobot instance is proven
table-driven: correct omitted-value default, correct explicit-value preservation, no manufactured
override, and no change to `DesiredService`'s separate default or warning behavior. The remaining
Django-dependent rows are explicitly named rather than silently skipped, and are covered by Step
3.7's live model/serializer verification plus the full local integration scenario referenced there.
