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
  runtime-matrix tests are part of the skipped Nautobot-dependent group in this environment).
- The full runtime UI contract suite (`UIRuntimeRenderTests`, `UINonMutationRuntimeTests`,
  `UIMissingPermissionRuntimeTests` in `test_ui_contract.py`) requires a live Nautobot test
  runner and was not executed in this pass — nintent here is deployed via
  `pip install git+https://github.com/iwaag/nintent.git@<branch>` (not a local source mount), so
  exercising it live requires the same commit → push → `docker compose build` → restart cycle as
  prior nintent changes. Committed locally in the `nintent` submodule; push and rebuild are left
  for the user per the established flow.

## Exit

- `DesiredWorkspace` now has the same read-only list/detail/nav/table/filter surface as every
  other retained desired-state model.
- Nothing about Phase 2's evaluation semantics (`nctl workspaces`, `nctl drift`) changed.
- Remaining: push the `nintent` submodule commit, rebuild/restart the Nautobot container, and
  bump the superproject's `nintent` submodule pointer — same live-deploy pattern used for prior
  submodule changes, deferred here pending approval.
