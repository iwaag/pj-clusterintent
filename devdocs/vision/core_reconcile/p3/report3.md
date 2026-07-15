# Phase 3 Report — Step 3 (status write-back client)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 3. nctl commit: `p3s3`.

## Risk check (plan: "verify at the start of Step 3")

Findings from the nintent 0.6.0 source (`nautobot_intent_catalog/api/`):

- **The REST router registers only `nodes` and `endpoints`** — there is **no DesiredService
  ViewSet today**. Step 4's nintent work therefore includes adding the
  `services/` route (ViewSet + serializer + router registration), not just model fields.
  The push client already targets `/api/plugins/intent-catalog/services/<id>/`; against a
  pre-Step-4 server that PATCH 404s, which the client counts as `skipped_no_row` — visible,
  not fatal, per Decision 4.
- Both serializers are `NautobotModelSerializer` with `fields = "__all__"`, so the new model
  fields become PATCH-writable automatically once Step 4's migration lands; no serializer
  field list needs editing (the DesiredService serializer must still be created).
- Target→row mapping: the drift engine populates `Target.id` with the Nautobot UUID for both
  kinds (confirmed in the live payload), so the id path is primary; slug/name lookup is the
  fallback the plan asked for.

## What was built

- **`NautobotClient.rest_get` / `rest_patch`** — the client's first write surface, per the
  Phase 0-EX1 split (reads = GraphQL, writes = REST). Connection failures raise the existing
  `NautobotConnectionError`.
- **`nctl_core/dashboard/push.py`** — `push_statuses(client, drift_data) -> StatusPushData`:
  - routes: `node` → `nodes/`, `service` → `services/`; open-set kinds (global diagnostics
    etc.) have no ledger row by construction → `skipped_no_row`;
  - PATCH body: `reconciliation_status` (the target's status value) and
    `reconciliation_checked_at` (the payload's `generated_at` — so a `--from` push is visibly
    stale rather than silently rejected, per the plan);
  - outcome mapping: 2xx → `updated`, 404 → `skipped_no_row`, other HTTP / connection error →
    `failed` with a per-target error string; one target's failure never aborts the rest;
  - missing-id fallback: `?slug=`/`?name=` lookup, used only on an exactly-one match.
- **Wiring in `build_dashboard`**: push runs only for a successful drift payload after a
  successful write, is skipped by `--no-push`, and its failures stay inside `status_push`
  (envelope `ok` is unaffected — Decision 4). A token-resolution error degrades the same way.

## Tests

`tests/test_dashboard_push.py`, 9 respx-mocked tests: node+service PATCH bodies, open-set-kind
skip, 404→`skipped_no_row`, 500→`failed`+continue, connection-error degradation, slug-fallback
lookup (hit and no-unique-match), and two `build_dashboard` integration tests (push after
write; push failure keeps `ok: true` and the artifacts).

Full nctl suite after the step: **263 passed**.

## Live smoke check (not the Step 5 verification)

`nctl dashboard --no-push --out <tmp>` against the dev cluster: wrote `index.html` +
`drift.json`, summary `converged=3 unknown=2` — matching the Phase 2 closeout baseline
([p2/report8.md](../p2/report8.md)). The full live verification (real push, nintent UI, failure
paths) remains Step 5, after Step 4 deploys nintent 0.7.0.

## Phase status

Steps 1–3 (all nctl-side work) are complete — nctl commits `p3s1`..`p3s3`. Next is Step 4, the
single nintent push cycle: model fields + migration 0009 + **the DesiredService REST route
(per the risk check above)** + read-only UI surface + `dashboard_url` plugin setting + 0.7.0
bump, which requires a user-side `git push` and a dev Nautobot rebuild.
