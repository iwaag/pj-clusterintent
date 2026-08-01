# Phase 2ex — Minimal read-only GUI for DesiredWorkspace

## Trigger

After Phase 2 (`nctl workspaces` / `nctl drift` evaluation) shipped, a check confirmed
`DesiredWorkspace` had no Nautobot UI presence at all: no `ListView`/`ObjectView`, no table, no
filterset, no nav entry, no template. Every other retained desired-state model (`DesiredService`,
`DesiredNode`, `DesiredIPRange`, ...) has had a read-only list+detail pair since the Interface
Contract Phase 4 UI cleanup. `DesiredWorkspace` was added later (creative_workspace Phase 0/1) and
that step was skipped. This phase closes that specific gap; it is not part of the roadmap's Phase
3 actuation ladder and adds no new behavior beyond visibility.

## What changed

All changes are in the `nintent` submodule, following the existing read-only-model pattern
exactly (no add/edit/delete views, no mutation surface):

- `views.py` — `DesiredWorkspaceListView` / `DesiredWorkspaceView` (mirrors `DesiredIPRange*View`).
- `tables.py` — `DesiredWorkspaceTable`: name, desired_node, source_remote_url, expected_path,
  lifecycle, desired_presence; default columns trimmed to name/node/remote/lifecycle/presence.
- `filters.py` — `DesiredWorkspaceFilterSet` with a free-text `q` search over name/slug/
  source_remote_url.
- `urls.py` — `workspaces/` (list) and `workspaces/<uuid:pk>/` (detail), no `add/edit/delete`
  routes.
- `navigation.py` — new "Desired Workspaces" item under the existing "Desired State" nav group.
- `templates/nautobot_intent_catalog/desiredworkspace.html` — new read-only detail template
  (same attr-table style as `desirediprange.html`).
- `tests/factories.py` — `make_desired_workspace()`.
- `tests/test_ui_contract.py` — extended the route manifest (20 → 22 retained routes), the
  list/detail URL-prefix map, and the runtime render/permission-matrix (`RUNTIME_MODEL_MATRIX`)
  to include `DesiredWorkspace`, so it is covered by the same render/no-mutation/permission-gate
  proof every other model gets.

No model, migration, or API change — `DesiredWorkspace` and its serializer already existed from
Phase 0/1.

## Verification

- `python3 -m unittest discover -s nautobot_intent_catalog/tests` (nintent Django-free fast gate,
  per README_DEV.md matrix): 130 tests, OK, 10 expected skips (unchanged skip count — the new
  runtime-matrix tests belong to the skipped Nautobot-dependent group in this local unittest
  runner).
- Committed to the `nintent` submodule (`0c594d3`, "Add minimal read-only GUI for
  DesiredWorkspace") and pushed to `origin/main` by the user.
- Deployed live: `docker compose --env-file ../.env build --no-cache nautobot` from
  `devenv/nautobot`, then `docker compose --env-file ../.env up -d`. Per the known rebuild-cache
  gotcha, verified the resolved commit in both the build log
  (`Resolved https://github.com/iwaag/nintent.git to commit 0c594d3a5ad0b2...`) and the running
  container (`/opt/nautobot/build_info.json` → `{"nintent_commit": "0c594d3a5ad0b2..."}`), both
  matching the pushed commit.
- Live proof against the running scratch Nautobot (session-authenticated as `admin`, real desired
  state, no test fixtures):
  - `/plugins/intent-catalog/workspaces/` → 200, htmx-rendered table lists the real
    `pj-voxel3dprint` row (node `agpc`).
  - `/plugins/intent-catalog/workspaces/<pk>/` → 200, detail page shows Desired Node,
    Source Remote URL, Expected Path, Lifecycle, Desired Presence, and the workspace name
    `pj-voxel3dprint`.
  - An unauthenticated request to the same list URL correctly redirects to login (302), and a
    nonexistent `/plugins/intent-catalog/does-not-exist/` still 404s, confirming the new route is
    real and not masking a catch-all.

## Exit

- `DesiredWorkspace` now has the same read-only list/detail/nav/table/filter surface as every
  other retained desired-state model, live and confirmed against the real declared
  `pj-voxel3dprint` workspace — not just passing tests.
- Nothing about Phase 2's evaluation semantics (`nctl workspaces`, `nctl drift`) changed.
- Remaining: bump the superproject's `nintent` submodule pointer to `0c594d3` (this repo's
  root commit, done alongside this report).
