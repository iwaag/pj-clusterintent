# Phase 3 Report — Step 4 (nintent 0.7.0: status fields and dashboard link)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 4. nintent commit: `p3s4`
(local only — not yet pushed; see "Next" below).

## Risk check (plan: "verify at the start of Step 4")

The report3 risk check already established the two things this step had to get right:
there is no `DesiredService` REST route today, and both serializers are
`NautobotModelSerializer` with `fields = "__all__"`, so new model fields become
PATCH-writable automatically. Confirmed directly in the source before editing
(`nautobot_intent_catalog/api/serializers.py`, `api/views.py`, `api/urls.py`): only
`nodes` and `endpoints` were registered.

Migration scoping risk: modeled `0009_reconciliation_status.py` on the minimal style of
`0008_remove_proto_drift_models.py` — four `AddField` operations only, nothing else. The
report8 `makemigrations --check` inherited-field noise is a pre-existing condition of the
Nautobot 3.1 environment (see [p2/report8.md](../p2/report8.md)); this migration doesn't
touch it and stays scoped to the two new fields on the two models, per the plan.

## What was built

All in `nintent/nautobot_intent_catalog/`:

- **Model fields** (`models.py`): `reconciliation_status` (`CharField`, choices
  `converged/drifting/converging/unknown`, blank-allowed default so "never pushed"
  renders empty rather than a fake status) and `reconciliation_checked_at`
  (`DateTimeField`, null) added identically to `DesiredNode` and `DesiredService`,
  matching the codebase's established per-model duplicated-constants choice style (no
  shared mixin exists for choices anywhere else in this app, so none was introduced
  here). Both fields carry `help_text` documenting them as "written by nctl, derived
  cache of the last run" per Decision 4.
- **Migration** `0009_reconciliation_status.py`: four `AddField` operations, nothing
  else — same minimal style as 0008.
- **DesiredService REST route** (the gap report3 flagged): added
  `DesiredServiceSerializer` (`api/serializers.py`), `DesiredServiceViewSet`
  (`api/views.py`, using the existing `DesiredServiceFilterSet`), and
  `router.register("services", views.DesiredServiceViewSet)` (`api/urls.py`). This is
  the route the Step 3 push client already targets — the PATCH path it was
  `skipped_no_row`-degrading against now resolves.
- **Read-only UI surface**: `reconciliation_status` added to both filter sets
  (`filters.py`), and to `DesiredNodeTable` / `DesiredServiceTable` (`tables.py`) as a
  "Reconciliation" column rendered as a colored Bootstrap `<span class="label ...">`
  badge (green/red/yellow/gray, mirroring the Step 1 dashboard's color mapping) — the
  first badge-style rendering in this codebase; existing status-like fields
  (`resolution_status`, `lifecycle`) render as plain `get_FOO_display` text, so this is
  a deliberate, scoped departure to make cluster health scannable in Nautobot's own
  tables too. Detail templates (`desirednode.html`, `desiredservice.html`) gained
  "Reconciliation Status" / "Reconciliation Checked At" rows; no GraphQL/edit-form
  exposure was added, matching "no GraphQL/UI editing" from the plan.
- **`dashboard_url` plugin setting**: `default_settings = {"dashboard_url": None}` in
  `__init__.py` (a plugin setting, not a model field, per Decision — the roadmap's
  "Nautobot is the ledger, visualization lives outside it"). Read via a
  `_configured_dashboard_url()` helper mirroring the existing
  `_configured_source_file()` pattern (`views.py`), and a duplicate helper in
  `navigation.py` (module-load-time nav construction can't call into `views.py`
  without a needless coupling). Wired into: a "nctl Dashboard" nav menu item shown only
  when `dashboard_url` is set, and a "(view dashboard)" link next to the reconciliation
  status row on both detail pages via `ObjectView.get_extra_context`.
- **Version bump**: `0.6.0` → `0.7.0` in both `pyproject.toml` and
  `IntentCatalogConfig.version` (the two independent copies report3's exploration
  flagged).

## Unverified-locally risk

`nautobot.apps.ui.NavMenuItem.link` is documented/typically used with a Nautobot URL
name (as every other entry in this file does); whether it accepts a raw external URL
string (needed for `dashboard_url`, which is LAN-external, not a Nautobot route) could
not be confirmed from source — Nautobot isn't installed in this local dev environment
(same constraint noted in report3). If it doesn't resolve as expected, this is a small,
isolated fix to make in Step 5 once the container is up.

## Tests

Nautobot/Django are not installed in the local `nintent` venv (a standing constraint of
this dev setup — DB/API-backed logic can only be exercised live, inside the dev
Nautobot container per [.local/localenv_memo.md](../../../../.local/localenv_memo.md)).
All new code lives behind the existing `try/except ImportError` guards, so it adds no
import-time risk to the loader-only test suite:

`uv run python -m unittest discover -s nautobot_intent_catalog/tests` — **92 passed**
(same count as [p2/report6.md](../p2/report6.md); unaffected, as expected, since no
loader-only-testable surface changed).

Model/migration/API/UI behavior itself is verified live in Step 5, after deployment.

## Phase status

Step 4 is committed locally in `nintent` (`p3s4`) but **not pushed** — per the
established flow (nintent changes require commit → user push →
`docker compose build --no-cache` → restart), pushing is left to the user. The parent
repo's `nintent` submodule pointer is locally advanced but intentionally left
uncommitted for now: the plan's suggested commit order groups the submodule bump with
Steps 5–6, after live verification confirms the deployed code actually behaves as
built.

**Next**: ask the user to push `nintent`'s `p3s4` commit, then rebuild the dev Nautobot
container without cache and restart it. Once that's done, Step 5 (live verification —
running `nctl dashboard` against the dev cluster, confirming the pushed
`reconciliation_status`/`reconciliation_checked_at` values, the dashboard nav link
including the `NavMenuItem.link` risk above, and the failure-path spot checks) can
proceed, followed by Step 6 (docs) and the parent-repo submodule/report commit.
