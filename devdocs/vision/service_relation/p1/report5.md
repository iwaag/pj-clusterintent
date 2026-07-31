# Step 5 Report — Profile Contract Edit

Status: complete.

## Changes

- `ansible_agdev/vars/deployment_profiles.yml`: removed the `llm_provider_service`
  variable from the `node_agent` profile (`variables: {}` now, matching the
  `ollama`/`manual_toolchain`/`prometheus_node_exporter` profiles' shape).
  Nothing else in the file changed; `deployment_profile_reconciliation` is
  untouched, as the plan specified.
- Searched `ansible_agdev/` for any other reference to
  `nintent_llm_provider_service`/`llm_provider_service`: none found, so no
  playbook or template needed a parallel edit.

## Verification

- `uv run pytest -q` in `nctl/`: `1040 passed`. No fixture referenced the
  live `deployment_profiles.yml` file directly (they use inline config
  dicts), so removing the variable didn't need any nctl-side test changes.
- `uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py`
  (superproject root): `3 passed`. This gate covers Ansible inventory/apply
  scope, not `deployment_profiles.yml` variable declarations, so it was
  unaffected as expected — run anyway per the plan's "if the file's consumers
  changed shape" clause.

## Known transitional state (expected, not a defect)

`nctl_core/production/service_dependencies.py` still reads
`config.llm_provider_service` directly (untouched in this phase, per the
plan's explicit "do not touch" instruction — that's Phase 2's job). Now that
the profile no longer declares the key, if `nctl drift`/`nctl reconcile` is
run against the live cluster before Step 7's migration batch converts the
three live placements, `node_agent` on `aghub`/`agstudio`/`agpc` will show
new drift (their live config still carries the now-undeclared key). This is
the accepted interim gap the plan already documents; Step 7 both migrates
those three placements and re-checks `nctl drift --json` for the expected
convergence afterward. No `nctl reconcile --yes` actuation should run against
`node_agent` placements until Phase 2 lands.

## Next

Step 6 (pause point): deploy the nintent changes to the local scratch
Nautobot. This needs the user to push the `nintent` commits (Steps 1-3 are
already committed locally: model, batch wiring, graph invariants), then a
`--no-cache` container rebuild with resolved-SHA verification, migrate, and
restart.
