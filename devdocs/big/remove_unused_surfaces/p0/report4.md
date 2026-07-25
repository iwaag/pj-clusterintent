# Phase 0 Step 4 — Build the exhaustive deletion manifest

Parent: [plan.md](plan.md), Step 4.

## Method

Ran `git grep -nIE '<token-alternation>'` separately inside the superproject and each of the five
submodules (`git ls-files`-scoped by construction, so `.venv`/`uv`/`.git`/`__pycache__`/generated
local output are excluded). The token alternation is the exact union of plan §4's parent-roadmap
tokens and structural/coupling tokens. Raw output (938 matched lines across 101 distinct tracked
files) is saved to the private evidence file `tracked-token-matches.tsv`; the classified,
one-row-per-file manifest is saved to `manifest.tsv` (both `0600`).

## Manifest summary

| Classification | Files |
|---|---|
| `delete` | 23 |
| `edit` | 32 |
| `historical` | 42 |
| `keep-shared` | 4 |
| **Total matched** | **101** |

By repository: superproject 44, `nctl` 39, `nintent` 14, `ansible_agdev` 4, `nauto` 0, `nodeutils`
0. No file has more than one classification row; every row has a non-empty `reason`.

## `delete` (23 files, all in `nctl`)

`nctl_core/serve/` (7: `__init__.py`, `app.py`, `dashboard.py`, `live_dashboard.html`, `runner.py`,
`runtime.py`, `snapshots.py`), `nctl_core/dashboard/` (4: `__init__.py`, `html.py`, `push.py`,
`template.html`), `nctl_core/dashboard_render.py` (1), and 11 dedicated tests
(`test_cli_dashboard.py`, `test_cli_serve.py`, `test_dashboard_html.py`, `test_dashboard_push.py`,
`test_dashboard_render.py`, `test_events_bus.py`, `test_serve_app.py`, `test_serve_dashboard.py`,
`test_serve_operations.py`, `test_serve_runner.py`, `test_serve_ws.py`). This is exactly the
minimum §5 `delete` list plus the plan's own known addition `test_events_bus.py` — no more, no
fewer.

## `edit` (32 files)

- `nctl` (13): `pyproject.toml`, `uv.lock` (drop `serve` extra / `fastapi`/`uvicorn` pins),
  `example.nctl.toml` (`[dashboard]`/`[serve]` sections), `cli/main.py`, `config.py`, `events.py`
  (durable subset stays, subscriber bus goes), `reconcile/executor.py` (`ReconcileData.dashboard`
  field), `drift_render.py`, `test_config.py`, `test_compatibility_snapshots.py`,
  `test_reconcile_executor.py`, `README.md`, 4 files under `docs/` (`compatibility.md`,
  `event-log.md`, `output-format.md`, `usage_example.md`).
- `nintent` (12): `models.py`, `api/serializers.py`, `filters.py`, `tables.py`, `views.py`,
  `urls.py`, `navigation.py`, `__init__.py` (`default_settings = {"dashboard_url": None}`),
  `desirednode.html`, `desiredservice.html`, `README.md`, `README_QUICK.md`.
- superproject (7): root `README.md`, `devenv/nautobot/nautobot_config.py`
  (`PLUGINS_CONFIG.dashboard_url`), `devdocs/big/braindump/roadmap.md`,
  `devdocs/big/core_reconcile/roadmap.md` (both still narrate the dashboard/realtime-API goal as
  current — superseded by `devdocs/vision/refactor/vision.md`, corrected in Phase 4).

Every `nintent` file here matches exactly the plan §5 `edit` minimum list; grep evidence for the
representative fields (`reconciliation_status`/`reconciliation_checked_at` column definitions in
`tables.py`/`filters.py`, `dashboard_url`/`dashboard_redirect` in `navigation.py`/`views.py`/
`urls.py`, the docstring justification "nctl dashboard is the writer" in `api/serializers.py`) was
spot-checked directly, not inferred from filename alone.

## `historical` (42 files)

Past-phase reports/plans/fixtures across `better_usability/p0`, `/p2`, `/p4`; `braindump/p0`–`p3`;
`core_reconcile/p3`–`p5`; `vm/p1`; `vm/p3/report3.5.md` (the current phase's own latest report —
kept as-is per plan §2's "do not edit their narrative to pretend the removed features never
existed"); `devdocs/small/fix_sshkey/` and `fix_sshkey4/`; and this initiative's own
`report0.md`/`report2.md`/`report3.md` (self-referential token matches from quoting the search
tokens/field names in this very report series). None of these are rewritten by this initiative.

## `keep-shared` (4 files, all in `ansible_agdev/api/`)

`README.md`, `app/main.py`, `pyproject.toml`, `uv.lock`. Verified by reading `api/README.md` and
`api/app/main.py`: this is an unrelated, pre-existing "Minimal FastAPI webhook server for this
Ansible repository" that runs playbooks over HTTP — it matched only the generic structural tokens
`FastAPI`/`uvicorn`, has no `nctl_core` import, no `nctl serve`/`nctl dashboard` reference, and no
coupling to the removal scope. Recorded here so it is not later misclassified as an nctl-serve
remnant by filename pattern-matching alone.

## Gate

Every one of the 101 matched files has exactly one classification, phase, and reason; the `delete`
set matches plan §5's minimum list plus the known `test_events_bus.py` addition exactly; no row is
`unknown`/`investigate`/unowned.
