# Step 5 — Declare pj-voxel3dprint (in progress, paused)

Appended the planned `desired_workspace` upsert to `.local/desired-state.yaml` (values from
Step 0):

```yaml
- op: upsert
  kind: desired_workspace
  key: {slug: pj-voxel3dprint}
  values:
    name: pj-voxel3dprint
    lifecycle: active
    source_remote_url: https://github.com/iwaag/pj-voxel3dprint.git
    desired_node: agpc
    expected_path: /home/eiji/projects/pj-voxel3dprint
    desired_presence: present
```

## Bug found: preview failed with HTTP 500

```
$ uv run --project nctl nctl desired apply -f .local/desired-state.yaml
error: desired-state batch failed: HTTP 500
```

`--json` surfaced the underlying error: `{"error": "'desired_workspace'", "exception": "KeyError", ...}`.

Root cause: `nautobot_intent_catalog/api/views.py` has a second, independent kind→model registry,
`_BATCH_MODELS` (used only for the REST permission check in `DesiredStateBatchView._check_permissions`).
Step 2 wired `desired_workspace` into `batch.py`'s `KIND_ORDER` / `_KEYS` / `_FIELDS` / the
apply-time model dict, but `_BATCH_MODELS` in `views.py` is a separate list that nothing keeps in
sync, and it was never updated. Any batch document containing a `desired_workspace` operation hit
`_BATCH_MODELS[operation.kind]` → `KeyError` → uncaught 500, even in `dry_run` mode (the
permission check runs before the dry-run/apply branch).

## Fix applied (nintent, uncommitted-push)

- `api/views.py`: added `"desired_workspace": models.DesiredWorkspace` to `_BATCH_MODELS`.
- `tests/test_batch_api.py`: added `BatchModelRegistryTests.test_batch_models_covers_kind_order`,
  a Django-gated regression test asserting `set(_BATCH_MODELS) == set(KIND_ORDER)` so this class
  of bug (a new kind added to `batch.py` but not to the view's permission-check registry) fails
  the runtime gate instead of surfacing as a live 500.

Committed in `nintent` (`c17f646`, "Fix DesiredWorkspace missing from batch API permission-check
registry"). Local Django-free gate re-run clean: `Ran 130 tests ... OK (skipped=10)` (the new
test is Django-gated, so it's part of the 10 local skips, not yet exercised).

## Pause: ask the user to push nintent again

This is a second push request in this phase (first was Steps 1-2, already pushed and rebuilt in
Step 4). The fix cannot be verified by the runtime gate or used to actually declare the workspace
until the container is rebuilt from the new nintent commit. Stopping here per the established
push boundary (`.local/localenv_memo.md`: nintent reaches the container only via GitHub push,
never local mount) to ask the user to `git -C nintent push`.

Once pushed, remaining work: `--no-cache` rebuild, runtime gate (expect 216 cases, one more than
Step 4's 215), retry the `nctl desired apply` preview (expect one `create`, rest `unchanged`),
then `--yes`, then Step 6 (GraphQL proof + phase report + submodule pointer bump).
