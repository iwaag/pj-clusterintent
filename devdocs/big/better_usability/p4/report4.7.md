# Phase 4 Step 4.7 — Test the literal isolation and orchestration matrix

Parent: [plan.md](plan.md), Step 4.7.

## New integration test

`nctl/tests/test_p4_mixed_node_orchestration.py` — one six-node snapshot run through the **real**
`compute_drift` → `build_plan` pipeline (not synthetic diffs, unlike most existing
`test_reconcile_planner.py` cases): a healthy converged node, an ambiguous-endpoint node, a
stale-observation node, an invalid-placement-config node, a planned-with-active-placement node,
and a node-type-ineligible (container) node, all in one snapshot with one shared service placed on
three of them. Asserts per node: the exact diff code and status; that the healthy node's own
diffs/status/plan membership are untouched by any neighbor in both cluster-scope and host-scope
reconcile; that every `intent_effect_summary` INFO diff is excluded from `manual_review` in both
scopes; and that the OBSERVATION-classified `stale_actual_data` code becomes an `observe_node`
action rather than a `manual_review` record, distinguishing it correctly from the four
MANUAL_REVIEW-classified neighbors. Full suite: **617 passed** (up from Step 4.6's 616).

## Coverage against the plan's bullet list

| Plan item | Status | Evidence |
|---|---|---|
| New default device, one primary endpoint, fresh observation, no override, no accepted-type override | Covered | `test_production_composer.py::test_linux_node_joins_actual_facts_and_service_group`; `linux_node()` fixture defaults to `node_type="device"`, no override |
| Explicit VM/service-host accepted-type override, preview never becomes false persisted intent | Partially covered | `test_operations_hosts.py::test_create_desired_node_with_primary_endpoint_accepts_explicit_actual_types` (operation level); `forms.py::clean_accepted_actual_types` returns `None` for blank input by construction (Step 4.2) — the live Quick Add form's JS-preview-never-submitted behavior itself needs a browser, deferred below |
| Generic endpoint omission vs. Quick Host contextual DNS publishing, with/without IP | Covered | `test_importers.py` (generic `ip_policy=external` omission), `test_operations_hosts.py` (Quick Host `dhcp_reserved`/`generate_dnsmasq=True` defaults) |
| One healthy node beside ambiguous-endpoint/stale-observation/invalid-placement-config/planned-active-placement/unsupported-node-type neighbors | **New this step** | `test_p4_mixed_node_orchestration.py` |
| Derived/safe-default/override records in text, JSON, dashboard, report 3.0 | Covered | `test_production_composer.py` (`accepted_actual_types_source`), `test_drift_render.py` (`_intent_effect_summary_lines`), `test_dashboard_html.py`, `test_production_contract.py` (report 3.0 value-record validation) |
| Placement `applied`/`inactive_by_intent`/every `not_applied` route | Covered | `test_production_composer.py`'s placement-effect tests (Step 4.4) plus the new mixed test's `agplanned`/`agcontainer` `not_applied` cases |
| Missing/malformed shared profiles blocking globally with a classified code | Covered | `test_drift_render.py::test_build_drift_reports_missing_deployment_profiles_as_global_error_without_failing`, `test_p4_deployment_profiles_unavailable_contract.py`, `test_reconcile_planner.py::test_deployment_profiles_unavailable_is_a_global_blocking_finding` |
| Cluster/host-scoped dry reconcile retaining independent healthy actions, ignoring only the INFO summary | Covered | New mixed test's cluster/host assertions; `test_intent_effect_summary_info_is_omitted_from_reconcile_plan` |
| Service analysis refresh preserving requirements and dependency notes/resolution/link | Covered at unit level; **not** covered end-to-end | `test_importers.py`'s `desired_service_update_fields`/`plan_dependency_sync` tests (Step 4.3) prove the pure logic; an actual two-run `AnalyzeIntentSources` Job execution needs a live Nautobot DB (Django-free local suite policy, `nintent/README_DEV.md`) — deferred to Step 4.8 |
| Service REST list/detail/status PATCH with non-null source | Covered at fixture level; **not** live-verified | `p4/fixtures/service_rest_list_pre.json` (Step 4.1) reproduced the pre-fix bug; the fix itself (Step 4.2) has no local REST test per this repo's documented policy — deferred to Step 4.8 |
| Report/inventory artifact writes: inventory 2.0 byte-stable, report 3.0 closed/deterministic | Covered | `test_production_composer.py::test_output_is_byte_stable`, `test_group_c_output_is_byte_stable_across_runs`, `test_production_contract.py`'s full v3 validator suite |

## Literal recipe execution — explicitly deferred, not skipped

The plan's closing instruction is to "follow both recipes literally in an isolated fixture
environment," creating/deleting a disposable node or service row "only with operator
authorization." This repository has one Nautobot instance (`devenv/nautobot/`) — there is no
separate throwaway environment, so "isolated fixture environment" here means live disposable rows
on the same dev instance Step 4.1's live preflight already read from. Per this phase's own
established rule (and this session's standing instructions), creating/deleting live rows is a
judgment call the operator makes explicitly, not one to take unilaterally mid-step.

Rather than run a disposable creation/deletion cycle now and a second live verification pass at
Step 4.8, this report defers literal recipe execution to Step 4.8, which already plans exactly this
work ("with operator approval, run ... the reviewed recipe/reconcile apply paths") as part of the
coordinated rollout — running it twice would be redundant risk on the same live system for no
added confidence. Everything achievable without touching live Nautobot rows is done and green
above.

## Result

No blocking surprise. The mixed-node orchestration gap is closed with a real integration test;
every other bullet has cited unit/integration coverage or an explicit, reasoned deferral to Step
4.8 rather than a silent gap. Full suites remain green: nctl 617, nintent 98, nauto 14 (unchanged
this step). Step 4.8 is last — it needs the user's explicit push, DB backup, and live-recipe
approval per `.local/localenv_memo.md` and this phase's own rollout decision.
