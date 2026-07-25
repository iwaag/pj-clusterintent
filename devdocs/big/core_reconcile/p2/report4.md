# Phase 2 Report — Step 4 (Evaluation-port comparators, dnsmasq MAC-source switch)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 4.

## What was built

New modules in `nctl/src/nctl_core/`:

- `names.py` — `canonical_node_name` (+ `default_dns_name`/`default_mdns_name`) ported unchanged
  from nintent's `nautobot_intent_catalog/names.py`; the node-candidate scorer needs it for
  suffix-insensitive name/hostname comparison, and Step 1 never had a reason to port it since
  nothing before this step compared names.
- `drift/evaluation.py` — the core port of nintent's `evaluations.py` (1266 lines): pure functions
  `evaluate_node_intent`, `evaluate_endpoint_intent`, `evaluate_service_intent`,
  `classify_endpoint_ip_ranges`, `normalize_desired_range_addresses`, `desired_ip_range_facts`,
  `matching_desired_ip_ranges`/`invalid_desired_ip_ranges`/`overlapping_desired_ip_ranges`,
  `_status_from_gaps`, all adapted from ORM-`getattr` chains to the Step 1 pydantic read-models.
  Candidate-scoring weights, gap-code vocabulary, and the DHCP-readiness rule are unchanged.
  Returns `EvaluationResult` (drops `source_hash`/`as_defaults()` — nothing is persisted per
  Decision 1, so there is nothing to hash or dedupe by). The module docstring documents four
  structural deviations forced by typed read-models replacing live Django relations:
  - A dangling `realized_device_id`/`realized_vm_id` (references an object no longer in the
    `ActualSnapshot`) is treated as "not realized" and falls through to candidate ranking here,
    rather than re-reporting the dangling-reference diagnostic — that stays `node_existence`'s job
    (Step 3), avoiding a duplicate code in two comparators.
  - `ActualVirtualMachine` (Step 1) carries only `id`/`name` — no custom fields, no interfaces,
    since no consumer before this step needed VM facts. VM candidates therefore only ever score on
    `name_or_hostname` (weight 50); the `serial`/`uuid`/`platform` weights (80/80/10) are
    structurally unreachable for VMs until Step 1's actual query is extended. Device candidates use
    the full original rubric.
  - `evaluate_endpoint_intent` takes `desired_node`/`realized_ip` as explicit parameters instead of
    walking `desired_endpoint.desired_node`/`.realized_ip_address` — the read-model only carries
    `node_id`/`realized_ip_address_id`, so the caller (the snapshot adapter, below) resolves both
    once and passes them in.
- `drift/evaluation_snapshot.py` — `evaluate_all_nodes`/`evaluate_all_endpoints`/
  `evaluate_all_services`, mirroring `production/adapter.py`'s role for the composer: resolves
  `SourceSnapshot` relations (realized device/VM by id, interfaces grouped by device id, a node's
  own evaluation feeding its endpoints' MAC-candidate fallback per nintent's `node_evaluation=`
  parameter) once per snapshot, so both the drift comparators and the dnsmasq MAC-source switch
  compute identical evaluations from the same snapshot instead of duplicating resolution logic.
  Node evaluations are computed before endpoint evaluations because the endpoint evaluator's
  interface-candidate fallback reads a node's `observed_facts.actual.interfaces` when the node has
  no direct realized-device link.

Modified:

- `drift/comparators.py` — three new comparators: `node_intent_matching` (`@register("node")`),
  `endpoint_intent_matching` (`@register("endpoint")`), `service_intent_matching`
  (`@register("service")`). Each is a thin wrapper turning every gap the ported evaluator produces
  into one `DiffRecord` via `_gap_diffs`: `code` passes through unchanged, severity maps via
  `_SEVERITY_BY_GAP_SEVERITY` (nintent's `conflict`/`missing`/`unknown` → `error`,
  `partial`/`needs_review` → `warning`). `node_existence` (Step 3) is kept, not removed or merged:
  it is a strictly faster, narrower check (dangling FK / policy-requires-realization) whose codes
  (`realized_device_missing`, `realized_vm_missing`, `no_realized_object`) stay distinguishable from
  the fuzzy-matching stream rather than collapsing into it. `endpoint_intent_matching`'s diffs use
  `Target(kind="node", ...)` (attributed to the endpoint's owning node) rather than a
  `kind="endpoint"` target — a desired endpoint has no independent drift-status lifecycle in the
  roadmap's vocabulary, only nodes and services do; the `@register("endpoint")` resource-type string
  is registry bookkeeping only and doesn't determine the emitted `Target.kind`.
- `drift/engine.py` — now seeds every desired service as a `converged`-by-default target (mirroring
  node seeding), a direct consequence of `service_intent_matching` being able to produce
  `kind="service"` diffs where nothing did before.
- `drift/status.py` — `UNKNOWN_CODES` extended with `evaluation.NO_DATA_GAP_CODES`
  (`missing_actual_node`, `missing_service_lifecycle`, `service_observed_facts_unknown`) so a target
  whose only diffs are "we have no reliable data" (not "the data disagrees") still resolves to
  `unknown`, consistent with the rule `node_existence`/`production_policy` already followed.
- `sources/desired.py` / `sources/actual.py` — extended the Step 1 GraphQL queries and read-models
  with fields the evaluation port structurally needs but Step 1 never fetched, because no consumer
  needed them before this step: `DesiredNode.accepted_actual_types`/`expected_spec`,
  `DesiredEndpoint.realized_ip_address_id`, `ActualDevice.serial`/`platform`,
  `ActualInterface.enabled`, `ActualIPAddress.dns_name`. All are real Nautobot/nintent model fields
  (not derived), empirically checked against the live dev schema (2026-07-15) before pinning —
  documented in each module's docstring as a Step 4 schema-completeness addition, not new domain
  logic. Existing Step 1 tests were updated with real assertions on the new fields.
- `dnsmasq_query.py` — rewritten. The `intent_evaluations` GraphQL query and the
  `latest_evaluations` reduction (which existed to pick the newest of possibly-many persisted rows
  per target) are both gone. New `dnsmasq_inputs_from_snapshot(snapshot)` computes both evaluation
  mappings fresh via `evaluate_all_nodes`/`evaluate_all_endpoints` and shapes them into the same
  `DnsmasqFetch` contract `dnsmasq.py` already expects (`{target_id: row}` mappings with
  `observed_facts`/`deterministic_summary`/`actual_refs`, via `EvaluationResult.as_row()`) — there
  is now exactly one evaluation per target, so no "keep latest" reduction is needed at all.
  `_endpoint_mapping`/`_ip_range_mapping` build the same mapping shapes the old GraphQL normalizer
  produced.
- `dnsmasq_render.py` — `build_dnsmasq_render` now calls `sources.snapshot.build_source_snapshot`
  (desired + actual, one extra GraphQL round trip versus the old dnsmasq-only query) instead of
  `fetch_dnsmasq_inputs`, then `dnsmasq_inputs_from_snapshot`. `dnsmasq.py` itself — the pure
  renderer — is untouched, per the plan's explicit boundary.

## Tests

- `tests/test_drift_evaluation.py` (31 tests) — direct coverage of the ported pure functions:
  node candidate scoring/ranking (name/serial/uuid/platform weights, ambiguous-candidate ties,
  dangling realized ids falling through to ranking), node mismatch detection, endpoint IP
  matching/linking/ambiguity, IP-range classification (valid/invalid/overlap, `_ip_policy_range_gaps`
  for each `ip_policy` value), DHCP-MAC candidate extraction and `dhcp_reservation_ready`
  (including the primary-mac-address fallback path and the node-evaluation-observed-facts fallback
  when a node has no realized link), service lifecycle/dependency gap detection, and
  `_status_from_gaps`'s full severity-to-status precedence order.
- `tests/test_drift_evaluation_snapshot.py` (4 tests) — `evaluate_all_nodes`/`evaluate_all_endpoints`/
  `evaluate_all_services` against a synthetic `SourceSnapshot`, confirming the relation-resolution
  wiring (realized device/VM lookup, interfaces-by-device grouping, node-evaluation propagation into
  endpoint evaluation) produces one evaluation per target.
- `tests/test_drift_comparators.py` (+6 tests) — `node_intent_matching`/`endpoint_intent_matching`/
  `service_intent_matching` each tested directly: gap-to-`DiffRecord` conversion, severity mapping
  for both `error`- and `warning`-mapped gap severities, endpoint diffs attributed to the owning
  node target.
- `tests/test_drift_engine.py` — 2 existing fixtures adjusted: a node with no realized link and no
  scoring candidate now legitimately gets flagged `missing_actual_node` (`unknown` status) where it
  previously stayed silent under Step 3's placeholder-only `node_existence` check. This is the
  intended Step 4 behavior change (real fuzzy matching now runs), not a regression.
- `tests/test_dnsmasq_query.py` / `tests/test_dnsmasq_render.py` — rewritten for the
  snapshot-based fetch path (no more respx-mocked `intent_evaluations` query).
- `tests/test_sources_actual.py` / `tests/test_sources_desired.py` — new assertions for the added
  fields (`serial`/`platform`/`enabled`/`dns_name`/`accepted_actual_types`/`expected_spec`/
  `realized_ip_address_id`).

## Parity Gate A (evaluations) — PASS

Ran the live `Evaluate Node/Endpoint/Service Intent` Jobs via the Nautobot REST Jobs API
(`/api/extras/jobs/{id}/run/`, dev instance at `http://localhost:8000`), polled to `SUCCESS`,
dumped the resulting `intent_evaluations` rows via GraphQL, and compared per-target status and gap
codes against the ported comparators run over `nctl_core.sources.snapshot.build_source_snapshot`
on the same live data.

Result: **5/5 nodes and 5/5 endpoints matched exactly** on status and gap codes —

- `agbach`/`agpc`/`agstudio` → `partial` / `actual_node_not_linked` (a single strong candidate found
  but not explicitly linked in Nautobot).
- `agdnsmasq`/`aghub` → `missing` / `missing_actual_node` (no candidate scored ≥40).
- All 5 endpoints → `partial` / `missing_actual_ip_address`, plus `missing_interface_candidate`
  where the owning node has no realized/candidate device to source interfaces from.

0 desired services exist in the current dev dataset (as documented in report1/report2 — nothing
seeded this phase's scope needed to change), so service-evaluation parity is an
empty-matches-empty result, consistent with the established convention from Steps 1–2 for
under-seeded data: it proves the composer/comparator *shape and behavior* are identical on
identical input, not that a rich dataset was exercised.

One incidental finding, not a bug: the live `intent_evaluations` table contains several orphaned
rows referencing target ids that no longer exist in `desired_nodes`/`desired_endpoints` (stale
historical data from earlier dev-database fixture churn). These were correctly excluded by
filtering to the latest row per *current* target id before comparing — harmless for this parity
check, and moot for Step 6 anyway since the whole model is deleted, not migrated.

## Parity Gate B (dnsmasq) — PASS

Captured `nctl render dnsmasq --json` against the live dev Nautobot instance immediately before
touching `dnsmasq_query.py`/`dnsmasq_render.py`, then again immediately after the MAC-source
switch, both against the same live data.

Result: **byte-identical** after excluding only the `generated_at` timestamp (both the envelope
field and the `# generated_at:` conf comment line, per the established parity-gate convention of
excluding generation-specific fields). `dns_records`, `dhcp_reservations`, `dhcp_ranges`,
`skipped`, and `summary` all matched exactly — including the 3 real MAC-address DHCP reservations
resolved from devices that are candidate-matched but not explicitly linked as `realized_device`.
This is the regression gate protecting Phase 1's deliverable, and it holds.

## Verification

- `uv run pytest -q` — **221 passed** (38 new: 31 `test_drift_evaluation.py` + 4
  `test_drift_evaluation_snapshot.py` + 6 `test_drift_comparators.py`, net of adjustments to
  existing dnsmasq/engine tests; 183 pre-existing from Phases 0–1 and Steps 1–3, no regression).
  Reconfirmed independently after the implementing agent's own run.
- Parity Gate A — see above, 5/5 nodes and 5/5 endpoints matched against the live Evaluate Jobs.
- Parity Gate B — see above, byte-identical `nctl render dnsmasq` output before/after the switch.

## Deviations from plan

- Extended Step 1's `sources/desired.py`/`sources/actual.py` schemas rather than keeping Step 1
  frozen. Necessary, not a scope creep: several fields the evaluation port structurally requires
  (`Device.serial`/`.platform`, `Interface.enabled`, `IPAddress.dns_name`,
  `DesiredNode.accepted_actual_types`/`.expected_spec`, `DesiredEndpoint.realized_ip_address`) are
  real model fields nintent's ORM-based evaluator read directly, simply never fetched because no
  consumer before Step 4 needed them. Each addition is documented at its query site with the live
  schema-check date, matching Step 1's own precedent for schema documentation.
- `node_existence` (Step 3) was kept alongside the new `node_intent_matching`, not merged or
  removed, even though Decision 1 frames the evaluation port as "superseding" `IntentEvaluation`.
  Read narrowly, Decision 1 is about deleting the *persistence* (the Jobs/model), not about
  collapsing Step 3's fast existence check into the heavier fuzzy-matching pass — the two answer
  different questions (`node_existence`: "does the linked object still exist / is a required link
  present at all?"; `node_intent_matching`: "if not linked, what's the best deterministic guess,
  and does a linked object's identity actually match?"), and keeping both keeps their diagnostic
  codes distinguishable in `nctl drift`'s output.
- `engine.py` gained service-target seeding as a direct, expected consequence of adding
  `service_intent_matching`, not a separate design decision.

## Real bugs/surprises

None found in nctl, nintent, or ansible_agdev code this step (contrast report2's ansible_agdev
`vars_files` bug). The one incidental finding — orphaned `intent_evaluations` rows for deleted
targets in the dev database — is pre-existing data staleness, not a code defect, and is moot once
Step 6 deletes the model outright.

## Commit boundary

Comparator port, dnsmasq MAC-source switch, and both parity gates all landed together, fully
green, with no partial state — committed as one self-contained unit (`nctl` commit `p2s4`,
18 files changed, 2498 insertions). This is commit 4 of the plan's suggested order ("nctl:
evaluation-port comparators + dnsmasq MAC-source switch + tests").

**Not done yet, deliberately left for the next commit(s):**

- Step 5 — `nctl drift` CLI (`Config`/`Envelope` wiring around `engine.compute_drift`, text
  rendering, `--host`/`--service` filters). The drift core itself (Step 3) already gained real
  node/endpoint/service diagnostics this step, so Step 5's CLI now has substantially more to show
  than Step 3's smoke test did.
- Step 6 — the single nintent push cycle deleting both proto-drift-engines
  (`ExportProductionInventory`, `SyncDeploymentProfiles`, the three Evaluate Jobs,
  `IntentEvaluation`/`DeploymentProfileProjection` models, their UI/API surface).
- Step 7 — ansible_agdev cleanup (including the already-documented `vars_files` bug in
  `export_nintent_production.yml`, moot once the playbook is deleted) and the deferred Phase 1
  live-apply proof.
- Step 8 — docs and report closeout.

Next: Step 5 — the `nctl drift` CLI.
