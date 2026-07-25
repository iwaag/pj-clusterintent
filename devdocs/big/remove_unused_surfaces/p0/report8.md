# Phase 0 Step 8 — Freeze the post-Phase-0 implementation manifest

Parent: [plan.md](plan.md), Step 8.

## Frozen manifest counts

| Classification | Files |
|---|---|
| `delete` | 24 |
| `edit` | 32 |
| `historical` | 42 |
| `keep-shared` (rows) | 4 |
| **Total matched/manifested** | **102** |

(24, not 23: Step 5 added `nctl/src/nctl_core/serve/artifacts.py` after import-tracing found it.)
Plus the five explicitly-protected shared-kernel modules confirmed in report5.md
(`artifacts.py`, `operations_index.py`, `ops_render.py`, `output.py`, `reconcile/lock.py`), which
have zero token matches and so are not manifest rows, only protection evidence.

## Cross-check against the parent roadmap and every newly discovered match

Every file in the parent roadmap's (`devdocs/big/remove_unused_surfaces/roadmap.md`) "Removal
inventory that the roadmap must verify" list is present with a `delete` or `edit` row: the
`nctl serve` FastAPI application/runner/WebSocket/live-dashboard/config/dependencies/schemas/tests
(`delete`), the static `nctl dashboard` renderer/templates/output-config/status-push/schemas/tests
(`delete`), automatic dashboard generation from reconcile terminal handling
(`reconcile/executor.py`, `edit`), the nintent `reconciliation_status`/`reconciliation_checked_at`
fields and every serializer/form/filter/table/template/navigation/redirect/settings/test surface
that exists only for them (12 `nintent` `edit` rows), and compatibility snapshots whose only
consumer is a removed surface (`nctl/tests/test_compatibility_snapshots.py`, `edit`). The one
newly discovered match beyond the roadmap's starting list, `serve/artifacts.py`, is folded into
the same `delete` set (report5.md).

## Imports and test fixtures, not only string matches

- Re-verified every `delete`-classified module's importers: only `cli/main.py` and
  `reconcile/executor.py` (both `edit`) import `nctl_core.dashboard`/`dashboard_render`/`serve`/
  `serve.runtime`; `test_compatibility_snapshots.py` (`edit`) is the only test referencing those
  module names outside the `test_serve_*`/`test_dashboard_*`/`test_cli_serve`/`test_cli_dashboard`/
  `test_events_bus` files already in `delete`. No shared kernel helper is imported *by* a delete
  file that isn't itself already `delete`, and nothing outside the delete/edit sets imports a
  delete file.
- `devdocs/big/better_usability/p4/fixtures/dashboard_pre.json`: searched the whole tree for
  `dashboard_pre` outside its own historical phase directory — zero references. It is a
  self-contained fixture belonging to the already-shipped Better Usability Phase 4 (confirmed
  complete per this project's own memory record), correctly `historical`, not an active test input
  for this initiative.

## `pyproject.toml`/lockfile dependency reachability

- `nctl/pyproject.toml` core `dependencies` are `typer`, `httpx`, `pydantic`, `pyyaml` — none tied
  to serve/dashboard. `httpx` is the Nautobot REST/GraphQL client used by `nctl_core/nautobot.py`
  (a retained, unrelated consumer) — confirmed by direct import-site read, not token grep.
- `[project.optional-dependencies].serve = ["fastapi", "uvicorn[standard]"]` is removable outright
  once `serve/` is deleted (`edit`, already in the manifest).
- `[dependency-groups].dev` currently also lists `fastapi` and `uvicorn[standard]` unconditionally
  (alongside `pytest`, `respx`) — these two entries exist only so the serve test suite can run
  without installing the `serve` extra separately; **they become removable from `dev` too** once
  the `serve` tests are deleted. This is a Phase 1 dependency-cleanup detail not previously called
  out at file level; recorded here for Phase 1 to act on.
- `respx` (an `httpx` mock library) is used by 14 test files, only one of which
  (`test_dashboard_push.py`) is in the `delete` set — the rest mock the retained Nautobot `httpx`
  client for unrelated features (braindump, jobs, lifecycle, drift render, sources, ledger, etc.).
  `respx` must **not** be removed from `dev` — it is a non-server dependency with 13 non-deleted
  consumers.

## Local deployment config

No local `nctl.toml` exists (report0.md/report2.md). `example.nctl.toml`'s `[dashboard]`/`[serve]`
sections are `edit`. `devenv/nautobot/nautobot_config.py`'s `PLUGINS_CONFIG` `dashboard_url` key is
`edit` (Phase 3, alongside nintent's `navigation.py`/`views.py` consumers of that same setting).

## Current docs versus historical docs

Confirmed in report4.md/report5.md: 42 `historical` files are all past-phase reports/plans/
fixtures that describe what existed at the time and issue no active instruction; the two active
roadmaps that still narrate dashboard/serve as a current/future goal
(`devdocs/big/braindump/roadmap.md`, `devdocs/big/core_reconcile/roadmap.md`) are `edit`
(Phase 4), not `historical`, per `devdocs/vision/refactor/vision.md`'s explicit supersession
statement.

## VM plan amendment

Folded into this freeze: `devdocs/big/vm/p3/plan.md` no longer has an unexplained active
dependency on dashboard/serve/cache fields (report7.md); it is not itself a manifest row (it is
governed directly by plan §7 Step 7, already executed) but its diff is cross-referenced here as
part of the frozen implementation state.

## Explicit call-outs

- `nctl/tests/test_events_bus.py` — confirmed present in `delete` (report4.md/report5.md).
- No server module is "actually shared and must be decoupled rather than blindly deleted" — the
  import trace above found none; `serve/artifacts.py` wraps the shared `operations_index` module
  but is itself server-only and has no retained importer, so it is a clean `delete`, not a
  decouple-first case.
- Dependency remaining for a non-server consumer: `httpx` (core) and `respx` (dev, 13 non-deleted
  consumers) must both be kept; only the `dev`-group's duplicate `fastapi`/`uvicorn` entries and
  the `serve` extra are removable.
- Every expected historical exception: nintent migrations `0009`/`0010`, and the 42-file historical
  set enumerated in report4.md.
- The exact known generated dashboard directory: `/Users/eiji/.local/state/nctl/dashboard`
  (`index.html` + `drift.json`, report2.md) — inspected now, to be archived/removed only with
  approval in Phase 5, per plan §7 (Expected Phase 0 manifest table).

## Gate

No `unknown`, `investigate`, or unowned row remains in `manifest.tsv` (103 lines including header:
1 header + 102 data rows, all with exactly one of the four classifications). Every Phase 1–4
implementation path in the manifest can be derived without a new ownership decision, with the two
dependency-reachability nuances above (dev-group `fastapi`/`uvicorn` removable, `respx`/`httpx`
retained) now recorded for Phase 1 to consume directly.
