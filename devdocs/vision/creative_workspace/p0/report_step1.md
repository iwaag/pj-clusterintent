# Step 1 — Model + migration (nintent)

## Changes

`nintent/nautobot_intent_catalog/models.py`:
- Added `DesiredWorkspace(PrimaryModel)`, `@extras_features("graphql")`, at the end of the
  try/except-guarded model block. Fields exactly per plan's proposed shape:
  `name`, `slug` (unique), `lifecycle` (6-value vocabulary copied verbatim from `DesiredService`,
  default `proposed`), `source_remote_url` (plain `CharField`), `desired_node` (FK, `PROTECT`,
  `related_name="desired_workspaces"`), `expected_path` (plain `CharField`), `desired_presence`
  (reuses `DesiredComputeInstance`'s `DESIRED_PRESENCE_PRESENT`/`ABSENT` constants, default
  `present`).
- Node-retirement protection: added a second check to `DesiredNode.clean()` mirroring the existing
  `controlled_compute_platforms` block — a retired `DesiredNode` with **any** attached
  `desired_workspaces` (not just non-retired ones) now raises `ValidationError`. Chose "any" to
  match the exact shape of the existing compute-platform check (`controlled_compute_platforms.exists()`),
  which also doesn't filter by the child's own lifecycle.
- **UI skipped**: no views/tables/templates/navigation/urls entry added for `DesiredWorkspace`.
  `test_ui_contract.py` enumerates models explicitly, so this doesn't break gates (verified by the
  Step 3 local test run below). Revisit if Phase 1 debugging wants a web-UI view of workspaces.
- No `get_absolute_url()` override — nothing in the batch writer or API calls it, and without a
  registered detail URL it would only ever raise if invoked, which it isn't.

## Migration

Generated inside the Nautobot container (local Python has no Nautobot/Django):
1. `docker cp` the modified `models.py` into the running `nautobot-nautobot-1` container's
   installed `nautobot_intent_catalog` package (container has no volume mount for this app; this
   was a temporary in-place edit purely to run `makemigrations`, not a deployment).
2. `docker exec nautobot-nautobot-1 nautobot-server makemigrations nautobot_intent_catalog` →
   `nautobot_intent_catalog/migrations/0027_desiredworkspace.py` (`+ Create model DesiredWorkspace`).
3. Copied the generated migration back into the repo via `docker cp`.
4. Restored the container to its original pre-edit state: `docker cp`'d back the pre-change
   `models.py` (from `git show HEAD:...`), deleted the stray `0027_desiredworkspace.py` +
   `.pyc` copied into the container, and `docker restart`'d it. Confirmed post-restart the
   container's `models.py` no longer contains `DesiredWorkspace` — the container is not running
   ahead of what's pushed. Migration is **not yet applied**; that happens in Step 4 after the real
   image rebuild.

Migration head is now `0027_desiredworkspace` (was `0026_braindumpdocument_completed_status`),
depends on `extras.0142_remove_scheduledjob_approval_required` — consistent with sibling
migrations' pattern (UUID pk, `created`/`last_updated`, `_custom_field_data`, `tags`, standard
`PrimaryModel` mixins).

## Sanity check

Ran the pure-domain test gate after this step to confirm nothing broke before moving to Step 2
(formal Step 3 run happens after Step 2 too, and is what gets committed/pushed):

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 129 tests in 0.007s
OK (skipped=10)
```

10 skips match the plan's expectation.

## Deviations from plan

None. UI was explicitly optional per plan and skipped as documented above.
