# Step 2 — Batch writer wiring (nintent)

All changes in `nintent/nautobot_intent_catalog/batch.py`, table-driven per the existing pattern:

- `KIND_ORDER`: appended `"desired_workspace"` at the end.
- `_KEYS["desired_workspace"] = ("slug",)`.
- `_FIELDS["desired_workspace"]`: `{name, slug, lifecycle, source_remote_url, desired_node,
  expected_path, desired_presence}` — exactly the model shape.
- `_CREATE_REQUIRED["desired_workspace"]`: `{name, slug, source_remote_url, desired_node,
  expected_path}` — `lifecycle` and `desired_presence` excluded because they have model defaults,
  matching the pattern for every other kind (e.g. `desired_compute_instance` excludes
  `desired_presence` for the same reason).
- `_models()`: added `"desired_workspace": models.DesiredWorkspace`.
- `_REFERENCE_KIND`: no change needed — `desired_node` already maps to `"desired_node"`, so
  `desired_workspace`'s `desired_node` field gets slug resolution for free, as the plan predicted.
- `_DELETE_BLOCKERS["desired_node"]`: added `("desired_workspaces", "desired_workspace")`.

## Tests (`nintent/nautobot_intent_catalog/tests/test_batch.py`)

- `test_desired_workspace_envelope_accepts_known_fields_and_rejects_unknown_ones` (Django-free,
  `BatchDecodeTests`): accepts a full valid envelope, rejects an unknown field
  (`desired_branch`) — this doubles as the hard-rule-1 guard (no desired branch/commit field
  reaches the batch writer even at decode time).
- Inside the Django-gated `BatchRuntimeTests` (only runs under the Nautobot runtime gate, not
  locally — consistent with the existing 10 skips):
  - `test_desired_workspace_create_required_fields_are_enforced` — omitting
    `source_remote_url`/`expected_path` plans as `conflict` naming both missing fields.
  - `test_desired_workspace_batch_apply_creates_and_is_readable` — full apply, row readable back
    via the ORM with the right `desired_node`/`expected_path`.
  - `test_deleting_a_node_with_a_desired_workspace_is_blocked_in_the_plan` — mirrors the existing
    `test_deleting_a_provider_service_with_an_inbound_binding_is_blocked_in_the_plan` pattern;
    deleting the node plans as `conflict` naming `desired_workspace:<pk>`.
  - `test_retiring_a_node_with_a_desired_workspace_is_rejected` — exercises the Step 1
    `DesiredNode.clean()` retirement guard end-to-end through `full_clean()`.

No factory added to `tests/factories.py` — that module is explicitly scoped to the eleven UI
models (per its own docstring) and `DesiredWorkspace` has no UI (Step 1 decision); the new tests
build rows directly with `DesiredWorkspace.objects.create(...)`.

`nctl desired apply` needs no change, as the plan predicted — `.local/desired-state.yaml` passes
through as the raw batch envelope and unknown kinds/fields are already rejected server-side by
`decode_batch`.

## Gate run (Django-free, local)

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 130 tests in 0.004s
OK (skipped=10)
```

130 tests (was 129 after Step 1) — the one new Django-free decode test runs; skip count unchanged
at 10, confirming no new Django-gated test accidentally leaked into the free-standing count.

## Deviations from plan

None.
