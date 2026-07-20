# Phase 4 Step 4.1 — Freeze baselines, live data, and executable contracts

Parent: [plan.md](plan.md), Step 4.1.

## Test baselines

- nintent local unit suite, run from `nintent/`:
  `uv run python -m unittest discover -s nautobot_intent_catalog/tests -p 'test_*.py'` —
  **92 passed**, matching the plan's stated Phase 3 baseline exactly.
- nctl full suite: `uv run --project nctl pytest -q nctl/tests` — **607 passed**, 1 pre-existing
  `StarletteDeprecationWarning` from `test_serve_ws.py`, matching the plan's stated baseline
  exactly.
- nauto relevant suite: `uv run --project nctl python -m pytest -q nauto/tests` — **12 passed**
  (`test_nodeutils_ingest_summary.py`, `test_nodeutils_ingest_batch.py`).
- Submodule revisions match the plan's stated current state exactly: nintent `e018ffe`, nctl
  `e804620`.

## Live read-only data (bounded, no secrets recorded)

`NAUTOBOT_TOKEN` was not exported in the initial shell; `nctl status` failed
`nautobot_unauthenticated` until exported from the token already on file in
`.local/localenv_memo.md`. Not a plan surprise — resolved by setting the env var for this
session's commands; `nctl status` then reported `authenticated: True` against the running
`nautobot-nautobot-1` container (v3.1.3).

Fetched via `nctl_core.sources.desired.fetch_desired_snapshot` against the live dev Nautobot:

- **Nodes (5):** `agbach` planned/device/`[device]`, `agdnsmasq` planned/service_host/
  `[device, virtual_machine]`, `aghub` planned/device/`[device]`, `agpc` active/device/`[]`,
  `agstudio` active/device/`[]`. Matches Phase 3's final live state exactly
  ([[project-better-usability-p3]]).
- **Endpoints (5):** `ip_policy` counts `{dhcp_reserved: 4, static: 1}`; all 5 have
  `generate_dnsmasq=True`.
- **Services (1):** `dnsmasq`, lifecycle active, `requirements={}`, `placement_policy={}`.
- **Dependencies (0).**
- **Operational overrides (0). Placements (1). IP ranges (3).**
- **IntentSource (1):** slug `manual`, `source_type=MANUAL`, `ref=null`, `enabled=true`,
  `last_import_status=null`, `last_imported_at=null` (fetched via `intent_sources` GraphQL query;
  no REST endpoint exists for this model per `nintent/nautobot_intent_catalog/api/urls.py`).

**Item 3 assertion — every live `placement_policy` is empty:** confirmed, 0 of 1 services has a
non-empty `placement_policy`. Decision 6's `RemoveField` may proceed as planned; no consumer/data
mapping amendment is needed.

## Pre-change fixtures (secrets stripped, saved under `p4/fixtures/`)

- `drift_agpc_pre.json`, `drift_full_pre.json` — `nctl drift --host agpc --json` / `nctl drift
  --json`.
- `render_production_2.0_pre.json` — `nctl render production --json`, schema `2.0`.
- `dashboard_pre.json`, `dashboard_drift_pre.json` — `nctl dashboard --from drift_full_pre.json
  --no-push --json` (no-push; no reconciliation_status write-back performed).
- `service_rest_list_pre.json` — `GET /api/plugins/intent-catalog/services/`. Reproduces the
  plan's documented current-state defect exactly: `ImproperlyConfigured` — "Could not resolve URL
  for hyperlinked relationship using view name
  `...intentsource-detail`". Confirms `DesiredServiceSerializer(fields="__all__")` cannot serve
  GET/list today because the live `dnsmasq` service has this REST route auto-built despite no
  registered `intentsource` viewset. This is the concrete repro Decision 7 / Step 4.2 item 7 must
  fix; no separate live investigation needed at that step.

`grep -rl` for the exported `NAUTOBOT_TOKEN` across `p4/fixtures/` returned no matches before
these files were written to disk.

## Executable contracts added (nctl only)

Per `nintent/README_DEV.md`'s documented policy, the API layer has **no local Django-free test
coverage** — it "only exists inside a real Nautobot process" and is verified live via `curl`
(confirmed above, `service_rest_list_pre.json`). The same applies to migration behavior, which
needs a real Postgres-backed Nautobot. Both are pinned as fixtures/live-preflight evidence above
and at Step 4.8, not as nintent pytest files — forcing an artificial local DB test would contradict
this repo's established test architecture rather than follow it.

For nctl, where the fast mocked-GraphQL suite is the real test story, two failing contract tests
were added ahead of implementation and confirmed to fail for the intended reason (not vacuously):

- `nctl/tests/test_p4_intent_effect_summary_contract.py` — pins that `production_policy` must
  emit code `intent_effect_summary`, not `derived_value_provenance`, for every desired node.
  **Fails now:** `'intent_effect_summary' in ['derived_value_provenance', 'missing_actual_node',
  'no_realized_object']` is false.
- `nctl/tests/test_p4_deployment_profiles_unavailable_contract.py` — pins that a missing or
  structurally invalid `vars/deployment_profiles.yml` produces a global `ERROR`
  `deployment_profiles_unavailable` diff instead of silently degrading to `{}` (today's documented
  behavior in `drift_render.py`'s module docstring and `comparators.py`'s `production_policy`
  guard). **Fails now:** no global target is produced in either the missing-file or
  wrong-top-level-key case.

**Deliberately deferred to Step 4.2/4.4's own test-first work:** a frozen pytest pin of the full
report `3.0` closed `nodes` collection shape and the complete `intent`/`effective`/`application`
JSON shape from Decision 2's example. That shape's exact fields depend on `NodeInput`/
`PlacementInput` enrichment the composer does not yet have (Step 4.4 items 2 and 4); writing a
byte-exact pin now, before that data model exists, would very likely need to be rewritten rather
than implemented against, unlike the two contracts above which pin an existing, already-callable
seam (`production_policy`'s code string; `build_drift`'s global-target handling of
`DeploymentProfilesError`). The plan's own suggested commit order groups "frozen report 3.0"
contracts together with the nctl GraphQL/report batch (commit 3), which is where `NodeInput`/
`PlacementInput` are actually extended — Step 4.4 will write and freeze that shape test-first as
its own first sub-item, consistent with this step's intent rather than skipping it.

Full nctl suite after adding both new test files: **607 passed, 3 failed (both new contract
files, all failing for the pinned reason)** — no regression in the existing 607.

## Result

No blocking surprise beyond the missing `NAUTOBOT_TOKEN` export, resolved within this step. Live
counts match the plan's stated current-state premises exactly (5 nodes, 1 service, 0
dependencies, 0 non-empty `placement_policy`). Decision 6's field removal is now confirmed safe by
live evidence rather than assumption. Step 4.2 can proceed against these frozen contracts plus the
pre-change fixtures above.
