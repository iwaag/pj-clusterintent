# Step 4 Report — Full-Package Runtime Gate

Status: complete.

## Runs

- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
  nautobot_intent_catalog`: `cases=206`, all green. `makemigrations --check
  --dry-run` reports `No changes detected`.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean
  nautobot_intent_catalog`: dropped and rebuilt `test_nautobot` from scratch
  (required since this phase added migration `0025_desiredservicebinding`),
  full Nautobot migration/cleanup sequence completed, `cases=206`, all green.

206 is the whole `nautobot_intent_catalog` package (Step 3's `test_batch.py`
alone accounted for 33 of those). No other test file needed changes for this
phase — the new model/batch kind is additive and nothing else in the package
referenced `llm_provider_service` or the placement config shape directly.

## Next

Step 5: remove `llm_provider_service` from
`ansible_agdev/vars/deployment_profiles.yml`'s `node_agent` profile, then run
the nctl ordinary suite and the Ansible conformance gate.
