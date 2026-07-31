# Step 1 Report — Model + Migration

Status: complete.

## Changes

- `nintent/nautobot_intent_catalog/models.py`: added `DesiredServiceBinding`
  (`@extras_features("graphql")`, `PrimaryModel`) with exactly `consumer_placement`
  (FK to `DesiredServicePlacement`, `PROTECT`), `binding_name` (`SlugField`),
  `provider_service` (FK to `DesiredService`, `PROTECT`), and a
  `UniqueConstraint(consumer_placement, binding_name)` named
  `nic_unique_binding_per_placement`. No status/type/notes/lifecycle field, per
  idea-A §3.1 and the plan's anti-model note. No UI surfaces added (table,
  filter, urls, views, navigation) — left as discretionary per the plan; the
  fixed `RETAINED_UI_ROUTE_NAMES`/`RUNTIME_MODEL_MATRIX` manifests in
  `test_ui_contract.py` do not enumerate it, so nothing there needed updating.
- `nintent/nautobot_intent_catalog/migrations/0025_desiredservicebinding.py`:
  generated inside the running `nautobot-nautobot-1` container against a
  staged copy of the local checkout (same staging mechanism as
  `run_nautobot_runtime_gate.sh`, `nautobot-server makemigrations
  nautobot_intent_catalog`), then copied back into the repo unmodified.

## Verification

- `nautobot-server makemigrations --check --dry-run` inside the container
  against the staged checkout (including this new migration file): `No
  changes detected`, exit 0.
- `python3 -m unittest discover -s nautobot_intent_catalog/tests` from
  `nintent/`: `Ran 128 tests ... OK (skipped=10)` — same skip count as before
  this change, no regressions.

## Next

Step 2: wire `desired_service_binding` through `batch.py` (`KIND_ORDER`,
`_KEYS`, `_FIELDS`, `_CREATE_REQUIRED`, `_models()`, `_REFERENCE_KIND`), add
the `PROFILE_BINDING_NAMES` declaration and old-key refusal, and add the kind
to `api/views.py`'s `_BATCH_MODELS`.
