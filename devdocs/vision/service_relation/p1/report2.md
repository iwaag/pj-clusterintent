# Step 2 Report — Batch Kind + Per-Row Validation

Status: complete.

## Changes

- `batch.py`: wired `desired_service_binding` through `KIND_ORDER` (after
  `desired_service_placement`, so upserts apply after the placement/service
  they reference and deletes apply before them), `_KEYS`
  (`("consumer_placement", "binding_name")`), `_FIELDS`/`_CREATE_REQUIRED`
  (all three fields required, none optional), `_models()`, and
  `_REFERENCE_KIND` (`consumer_placement -> desired_service_placement`,
  `provider_service -> desired_service`). `consumer_placement`'s dict identity
  resolution ("desired_service"/"instance_name") comes for free from the
  existing `_reference_identity` dict-identity path.
- `api/views.py`: added `desired_service_binding` to `_BATCH_MODELS` so the
  batch endpoint's permission check covers the new kind.
- `models.py`: added the closed `PROFILE_BINDING_NAMES = {"node_agent":
  ("llm_provider",)}` map and `REFUSED_PROFILE_CONFIG_KEYS = {"node_agent":
  ("llm_provider_service",)}` map (idea-A §4.7 binding-name declaration and
  the old-key refusal, kept next to each other since they're the two halves
  of the same profile-contract decision).
  - `DesiredServiceBinding.clean()`: rejects a `binding_name` not declared for
    the consumer placement's `deployment_profile`.
  - `DesiredServicePlacement.clean()`: rejects a `config` that still carries
    a key in `REFUSED_PROFILE_CONFIG_KEYS[deployment_profile]`.
- `tests/factories.py`: added `make_desired_service_binding` (defaults to a
  `node_agent`-profile consumer placement and `binding_name="llm_provider"`
  so the factory satisfies its own `clean()`).
- `tests/test_batch.py`: one Django-free envelope test
  (`desired_service_binding` dict-identity decode + unknown-field rejection),
  and a new `ServiceBindingPerRowValidationTests` (ORM) class: declared name
  saves, undeclared name rejected, declared-elsewhere name rejected on a
  profile that doesn't declare it, old key rejected/absent key accepted on a
  `node_agent` placement, and two `apply_batch` end-to-end cases (binding
  created via the batch endpoint; a batch reintroducing the old key rolls
  back).

## Verification

- `python3 -m unittest discover -s nautobot_intent_catalog/tests` from
  `nintent/`: `Ran 129 tests ... OK (skipped=10)`.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
  nautobot_intent_catalog.tests.test_batch`: `cases=25`, all green (used to
  spot-check the new ORM-backed tests early; the full-package `--clean` gate
  run is Step 4).

## Next

Step 3: final-state graph invariants (§4.1–4.6) and §8 retirement/deletion
protection inside `apply_batch`'s transaction, plus the `_DELETE_BLOCKERS`
extension for `desired_service`/`desired_service_placement`.
