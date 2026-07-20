# Phase 1 Step 1.7 — Verification and implementation report

Parent: [plan.md](plan.md) Step 1.7. Final report for the whole phase; see `report1.1.md` through
`report1.6.md` for the per-step detail this summarizes.

## Commits

`nctl` submodule, `5b0b0d4` (Phase 0 baseline) → `fec5780`:

1. `11d59a5` — steps 1.1-1.2: composer local-code constants/carrier, Group C localization,
   classification (pulled forward to avoid an `UnclassifiedDiffCodeError` window).
2. `445fa42` — steps 1.3-1.4: `active_placement_not_applied`, drift/status/dashboard wiring.
3. `ef5f210` — step 1.5: reconcile blocked-host filtering, global/local blocking split, truthful
   terminal states.
4. `fec5780` — step 1.6: remaining failure/orchestration test gaps.

Root repo: one matching commit per nctl commit, each bumping the submodule pointer alongside its
report file(s).

## Focused test suite

```
uv run --project nctl pytest -q \
  nctl/tests/test_production_contract.py \
  nctl/tests/test_production_composer.py \
  nctl/tests/test_production_render.py \
  nctl/tests/test_cli_render_production.py \
  nctl/tests/test_drift_comparators.py \
  nctl/tests/test_drift_engine.py \
  nctl/tests/test_drift_status.py \
  nctl/tests/test_dashboard_html.py \
  nctl/tests/test_reconcile_classify.py \
  nctl/tests/test_reconcile_planner.py \
  nctl/tests/test_reconcile_executor.py \
  nctl/tests/test_compatibility_snapshots.py
```

Result: **199 passed**.

## Full regression

```
uv run --project nctl pytest -q nctl/tests
```

Result: **569 passed** (Phase 0 baseline was 518; Phase 1 added 51 net new/modified tests across
composer, drift comparators/engine/status, dashboard, and reconcile classify/planner/executor), 1
unrelated pre-existing `StarletteDeprecationWarning`. No nintent code changed in this phase, so the
88-test nintent baseline from `p0/report0.8.md` was not re-run.

## Read-only live checks (configured dev environment, 2026-07-20)

Ran against the running dev Nautobot (`nautobot-nautobot-1` et al., per
`.local/localenv_memo.md`), using the current all-`planned` dev ledger (5 `DesiredNode` rows, per
`p0/field-classification.md` §7's confirmed live state). No `--out`, no `dashboard` push, no
`reconcile --yes` was used — every command below is read-only.

**`nctl render production --json`**: `ok: true`. `summary.eligible: 0` (every dev node is still
`planned`, so none enters production scope — the plan's own predicted outcome). `errors: []`,
`skipped: []`. `report["drift"]` contains exactly one `active_placement_not_applied` entry, for
node `agdnsmasq`, with the full placement evidence preserved verbatim:

```json
{
  "code": "active_placement_not_applied",
  "desired_node_slug": "agdnsmasq",
  "node_lifecycle": "planned",
  "eligible_lifecycles": ["active", "approved"],
  "placement": {
    "instance_name": "dnsmasq",
    "deployment_profile": "dnsmasq",
    "config_schema_version": "1",
    "desired_state": "active",
    "config": {"listen_addresses": ["192.168.0.2"]}
  }
}
```

This is, live, exactly `discussion.md`'s Example 1 (the dnsmasq-loopback scenario the roadmap names
by name): the placement was previously silently dropped from every render/report; it is now visible
with its full config.

**`nctl drift --json`**: `ok: true`. `summary: {converged: 4, unknown: 1, drifting: 1}`,
`severity_summary: {error: 2, warning: 4, info: 0}`. Node `agdnsmasq` carries the
`active_placement_not_applied` warning and stays `status: "converged"` (Decision 4: a warning-only
finding never flips status) — visible in the payload but not raised as a false drift alarm. No
`Target(kind="global")` entry appears anywhere in the payload.

**`nctl reconcile --json`** (dry plan, `apply_changes` not passed): `ok: true`, `state: "planned"`,
`mode: "plan"`. `manual_review` contains 2 records, including
`{"code": "active_placement_not_applied", "target": {"kind": "node", "slug": "agdnsmasq", ...}}` —
confirming the code reaches real reconcile planning (not just test fixtures) without
`UnclassifiedDiffCodeError`. `unsupported: []`. No action executed; no ledger/Ansible/Nautobot
mutation occurred (plan mode only).

## Additional confirmations

- **No nintent/Django migration**: `nintent` submodule pointer and working tree unchanged (`git
  status --short` clean, `HEAD` unmoved from before this session).
- **Root changes scope**: `git diff --stat d6909da..HEAD -- . ':!nctl'` shows only the 6 new
  `devdocs/big/better_usability/p1/report1.*.md` files (this phase's own reports) plus the `nctl`
  submodule pointer bump in each commit — no other root file touched.
- **Other worktrees unchanged**: `nintent`, `nauto`, `ansible_agdev`, `nodeutils` all report clean
  `git status` with no new commits.
- **No secrets in artifacts**: the live-check commands above were run with `NAUTOBOT_TOKEN` sourced
  directly into the shell environment from `.local/localenv_memo.md` and never echoed, printed, or
  written into any test, report, or committed file. No live object UUID beyond the two already-
  public dev-ledger node ids shown above (their own slugs are non-sensitive hostnames already
  documented in `.local/localenv_memo.md`) appears in committed test fixtures — all test fixtures
  use synthetic ids (`n1`, `p1`, `dev-1`, etc.).

## Exit criteria — final check against `plan.md`

- [x] Every one of Phase 0 §6 Group C's 15 codes is caught only at its target-owned stage and
  produces a node-local structured skip/error; none becomes global. (`report1.2.md`, parameterized
  matrix in `test_production_composer.py`.)
- [x] Representative shared-profile and final-output contract failures still abort globally.
  (`test_group_a_shared_profile_error_still_aborts_globally`,
  `test_group_b_final_output_error_still_aborts_globally`.)
- [x] A mixed good+bad render succeeds, preserves healthy inventory/group/config output, and emits
  no partial membership for the skipped node. (Same matrix; also confirmed live above with `eligible:
  0` and a clean successful envelope rather than a failure.)
- [x] Every active placement on a lifecycle-ineligible, production-capable node emits
  `active_placement_not_applied`, including when `config == {}`; disabled placements do not.
  (`report1.3.md`; confirmed live above with non-empty config preserved verbatim.)
- [x] Each Phase 1 finding defines and tests target kind, severity, message/evidence, source list,
  render-report effect, drift/status/dashboard effect, and reconcile classification.
  (`report1.2.md`-`report1.5.md`.)
- [x] All 16 Phase 1 codes are `MANUAL_REVIEW`; classification coverage cannot miss a future local
  composer code. (`test_every_phase1_local_composer_code_is_classified`, imports the composer's own
  declared set rather than a second hand-maintained list.)
- [x] `nctl reconcile` never raises `UnclassifiedDiffCodeError` for these findings and never runs a
  production action against a blocked node. (`report1.5.md`'s planner tests; confirmed live above.)
- [x] A target-local blocker does not suppress independent healthy-target work; a global blocker
  still suppresses every action. (`report1.5.md`'s executor tests.)
- [x] Phase 1 makes no nintent/schema/data change, leaves production inventory schema `1.0`, and
  requires no Nautobot rebuild or compatibility shim. (Confirmed above; no `ContractError` code was
  renamed, no report/inventory top-level key added or removed, only the previously-empty
  `report["errors"]` array is now populated and `report["drift"]` gained one new code.)
- [x] Focused tests, full `nctl` tests, compatibility snapshots, and read-only live checks pass;
  unrelated submodules remain clean. (Above.)
- [x] The implementation report records exact evidence and confirms Phase 2 can now derive/remove
  operational config without inheriting a global-failure landmine: Phase 2 removing
  `DesiredNodeOperationalConfig` will change which of the 15 Group C codes are even reachable (some
  disappear entirely once the field is no longer required, as `report1.2.md` notes for
  `missing_operational_config`), but the isolation/classification/reconcile-blast-radius machinery
  built in this phase does not need to change shape to accommodate that — a node/placement failure
  already only ever affects its own target, by construction, at every layer from composer through
  executor.

Phase 1 is complete. No unresolved deviation from `plan.md` was required; no step needed to stop
for human judgment.
