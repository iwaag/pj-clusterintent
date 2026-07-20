# Phase 3 Step 3.1 — Freeze baselines and executable lifecycle contracts

Parent: [plan.md](plan.md), Step 3.1.

## Test baselines

- nintent local unit suite, run from `nintent/`:
  `uv run python -m unittest discover -s nautobot_intent_catalog/tests -p 'test_*.py'` —
  **89 passed**, matching the plan's stated Phase 2 baseline.
- nctl full suite: `uv run --project nctl pytest -q nctl/tests` — **587 passed**, 1 pre-existing
  `StarletteDeprecationWarning` from `test_serve_ws.py`, matching the plan's stated baseline.

## Live desired-node lifecycle counts (read-only)

Read-only GraphQL query for `desired_nodes { slug lifecycle }` against the configured development
Nautobot returned exactly **5 nodes**, all `PLANNED`: `agbach`, `agdnsmasq`, `aghub`, `agpc`,
`agstudio`. This matches the plan's "5 planned rows" premise exactly. No token or unrestricted
actual facts were recorded beyond slug/lifecycle.

## Phase 2 read-only production/drift/reconcile re-check

No promotion or actuation was performed; every command below was read-only.

- `nctl drift --json`: envelope `nctl.drift.v1`, **ok**, 6 targets, status summary
  converged 4 / unknown 1 / drifting 1, severity summary error 3 / warning 4 / info 5 — identical
  to the Phase 2 deployment baseline in `p2/report2.8.md`. Finding codes present:
  `active_placement_not_applied`, `derived_value_provenance`, `missing_actual_ip_address`,
  `missing_actual_node`, `missing_interface_candidate`, `no_realized_object`, `service_missing`.
  No `missing_operational_config` or dead expected-OS code exists.
- `nctl reconcile --json`: envelope `nctl.reconcile.v1`, **ok**, state `planned`, 0 rounds, 3
  manual-review findings (`active_placement_not_applied`, `missing_interface_candidate`,
  `no_realized_object`), no unclassified code, no mutation attempted.

Phase 1/2 target-local prerequisites remain deployed and unchanged.

## Lifecycle defaults/readers/writers inventory (`rg`, from Phase 0 §7)

Confirmed the plan's four independent `DesiredNode.lifecycle` default sites, and that no new site
was added since the Phase 0 audit:

| Site | File:line | Current default |
|---|---|---|
| model field | `nautobot_intent_catalog/models.py:299` (class `DesiredNode`) | `LIFECYCLE_PLANNED` |
| regular form initial | `nautobot_intent_catalog/forms.py:36` | `DesiredNode.LIFECYCLE_PLANNED` |
| host creation operation | `nautobot_intent_catalog/operations/hosts.py:37` | `lifecycle: str = "planned"` |
| strict YAML loader | `nautobot_intent_catalog/loaders.py:64,100,445,866` and `_LIFECYCLES` at `:1150` | `"planned"` |

The other two `LIFECYCLE_PLANNED`-named constant blocks in `models.py` (line ~103, `DesiredService`,
default `LIFECYCLE_PROPOSED`; line ~804, `DesiredIPRange`) are separate models/fields explicitly
out of scope for this phase's node-lifecycle default change, per the plan's Decision 5 and Out of
scope section.

nctl-side lifecycle readers (composer eligibility, drift/dashboard, reconcile classification) were
confirmed unchanged from Phase 2 by the drift/reconcile re-check above; `NautobotClient.rest_patch`
(`src/nctl_core/nautobot.py:69`) is confirmed available for the new command's single-field PATCH,
and `dnsmasq_apply.py`/`test_dnsmasq_apply.py` were reviewed as the existing pattern for a focused
core module with a matching test file.

## Contract tests

Added `nctl/tests/test_lifecycle_contract.py` ahead of any implementation, asserting (all currently
failing with `ModuleNotFoundError` for the not-yet-created `nctl_core.lifecycle` module, confirming
the tests are executable specifications and not accidentally vacuous):

- the exact CLI state vocabulary (`planned`, `approved`, `active`, `deprecated`, `retired`) and
  rejection of any other value;
- the `nctl.lifecycle.v1` envelope shape (`schema`, `generated_at`, `ok`, `data` with `node_id`,
  `node_slug`, `previous_state`, `requested_state`, `current_state`, `changed`, `errors`);
- idempotent no-write behavior when current state already equals the requested state
  (`changed=false`, no PATCH call recorded against a fake client);
- exactly one PATCH call with body `{"lifecycle": STATE}` against
  `/api/plugins/intent-catalog/nodes/{id}/` when a change is required; and
- a post-write GraphQL refetch that must confirm ID, slug, and lifecycle before `changed=true` is
  returned, failing closed (`lifecycle_confirmation_mismatch`) on mismatch.

## Result

No blocking surprise. Both suite baselines, the live 5-planned-node count, and the Phase 1/2
drift/reconcile findings all match the plan's stated current state exactly. The lifecycle
default-site inventory confirms no scope drift since Phase 0. Step 3.2 can implement
`nctl_core/lifecycle.py` against the frozen contract tests above.
