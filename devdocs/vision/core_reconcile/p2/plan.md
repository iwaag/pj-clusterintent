# Phase 2 Implementation Plan: Reconciliation Engine (drift engine)

Parent: [roadmap.md](../roadmap.md) — Phase 2: consolidate desired-vs-actual drift computation
into a single engine (`nctl drift`), absorb the two proto-drift-engines
(`ExportProductionInventory` and the `Evaluate * Intent` Jobs), and delete the
deployment-profiles byte-contract machinery.

## Current state (as of 2026-07-15)

- Phase 1 is complete ([p1/report7.md](../p1/report7.md)): `nctl render/apply dnsmasq` exist,
  nintent 0.5.0 is deployed without the dnsmasq Job. The one open Phase 1 item — a live
  `apply dnsmasq` — is blocked on `inventories/generated/production.yml` not existing; **this
  phase owns that generation path**, so finishing it unblocks that proof.
- Phase 1.5 (hosts-intent export) is planned before this phase in the roadmap but not started.
  Nothing here depends on its code; if it lands first, its inventory-writing pattern
  (`ansible-inventory` validation + atomic replace) is reused in Step 3, otherwise Step 3
  establishes that pattern.
- nctl today: `Config` (`[nautobot]`, `[inventory]`, `[events]`, `[repo]`, `[ansible]`),
  `NautobotClient.graphql()`, output envelopes, JSON Lines events + operation IDs, and
  `dumps.py` reading `nodeutils.inventory.v1` dumps (identity/collected_at typed;
  `facts`/`self_reported` deliberately left raw for this phase to type).
- The first proto-drift-engine, `ExportProductionInventory`
  (`nintent/nautobot_intent_catalog/jobs.py:536`), is a thin ORM adapter
  (`_build_production_node_inputs`, `jobs.py:715`) around **already-pure modules**:
  - `production_inventory.py` — `compose_production_inventory()` joins NodeInputs
    (desired node + operational config + placements + realized actual facts) with the
    deployment-profile map into a schema `1.0` inventory document plus a companion report
    containing `hosts` / `skipped` (structured reasons) / `drift` (platform-policy drift).
  - `production_inventory_contract.py` — profile/config validation,
    `evaluate_platform_policy`, connection-variable resolution, document/report validators,
    and the Job-input byte contract (`canonical_json`, `canonical_json_digest`,
    `parse_profile_job_input`).
  - `actual_facts.py` — the closed allowlist reading actual facts from realized-Device custom
    fields (`host_system`, `primary_ip_address`, `primary_mac_address`, `network_interface`,
    `last_seen`, `inventory_source`) that the nauto ingest Job persists.
  The byte contract exists only because `vars/deployment_profiles.yml` lives in ansible_agdev
  while composition runs inside Nautobot: `playbooks/tasks/nintent_serialize_deployment_profiles.yml`
  serializes it to canonical JSON + SHA-256 digest for the Job input, and
  `playbooks/nautobot/verify_deployment_profiles_contract.yml` +
  `playbooks/nautobot/sync_nintent_deployment_profiles.yml` (→ `SyncDeploymentProfiles` Job →
  `DeploymentProfileProjection` model) keep the digest-keyed projection in sync.
- The second proto-drift-engine, `Evaluate Node/Endpoint/Service Intent` Jobs
  (`jobs.py:276/311/366`), wraps the pure `evaluations.py` (1266 lines): candidate matching
  of DesiredNode↔Device/VM, endpoint IP↔IPAddress/interface matching, DesiredIPRange
  classification, DHCP-MAC candidate extraction, gap lists, and a `_status_from_gaps` verdict —
  persisted as `IntentEvaluation` rows keyed `(target_type, target_id, source_hash)` with
  `reviewed_at` recency. Consumers today:
  - **nctl** `render dnsmasq` reads `intent_evaluations` via GraphQL for
    `observed_facts.dhcp_mac_candidates`, `deterministic_summary.dhcp_reservation_ready`, and
    node `actual_refs` (`nctl/src/nctl_core/dnsmasq_query.py`).
  - `ReconcileDesiredIPAMIntent` (`jobs.py:448`) upserts endpoint evaluations as a side effect
    after each IPAM plan; the plan computation itself (`plan_endpoint_ipam_reconcile`) does
    **not** read evaluations.
  - nintent UI (views/tables/filters/forms/urls/navigation) and the REST/GraphQL API surface.
- GraphQL exposure (Phase 0-EX1): all nintent models except `DeploymentProfileProjection`
  carry `@extras_features("graphql")`; pinned snake_case collection names exist for the
  dnsmasq set. **Not yet exercised**: `desired_service_placements`,
  `desired_node_operational_configs` (names unverified), device custom-field data
  (`_custom_field_data`) and interface/MAC fields on core DCIM types.
- Deployment constraint (`.local/localenv_memo.md`): nintent changes cost a push +
  `docker compose build --no-cache` + restart cycle. As in Phase 1, the plan sequences nintent
  work into **one** push cycle, after parity is proven.

## Decisions taken head-on (as the roadmap requires)

**1. The drift engine supersedes `IntentEvaluation` (delete, don't keep as ingest cache).**
The evaluations are deterministic pure functions of state the drift engine already reads
(desired via GraphQL, actual Nautobot objects via GraphQL, dumps via `dumps.py`); persisting
them buys only staleness (rows are correct as of the last manual Job run) and a second source
of truth, which contradicts the vision's "drift engine as the single source of truth". The
logic is ported into nctl comparators (Step 4); the Jobs, model, and UI surface are deleted
(Step 6); `render dnsmasq` switches its MAC source to the ported logic *before* the deletion
lands. `ReconcileDesiredIPAMIntent` stays (transactional ledger write) and simply loses its
evaluation-upserting side effect.

**2. "Shared library" for the desired-state schema = move, don't share.** A literal shared
package would drag Django into nctl or force nintent through an indirection for its own ORM.
Instead: after this phase, desired-state *processing* (rendering, evaluation, composition)
exists only in `nctl_core`, typed as pydantic read-models of the GraphQL shapes; nintent keeps
only the ORM models as the storage schema plus transactional Jobs. The GraphQL schema is the
contract between the two, pinned by nctl's query tests (the Phase 0-EX1 name-pinning plus this
phase's field checks). This satisfies "no duplicated desired-state schema" without a
cross-runtime package.

**3. Production composition is a render command; drift reuses its pure functions.** The
roadmap allows "`nctl render production` or a drift-engine output" — we do the former, and the
drift engine calls the same ported `evaluate_platform_policy` / skip-reason helpers, so the
composer's `skipped`/`drift` report entries and `nctl drift` diffs can never disagree.

## Approach

Same template as Phase 1: port pure logic into `nctl_core`, prove **output parity** against the
live Jobs before deleting anything, then cut over in one nintent push cycle plus one
ansible_agdev cleanup. New in this phase: a typed three-source fetch layer and a comparator
registry that both the production composer and `nctl drift` sit on.

Ordering rationale: Steps 1–5 touch only nctl (fetch layer → production render + parity →
comparators/evaluation port + dnsmasq MAC-source switch + parity → `nctl drift`). Step 6 is the
single nintent push (delete both proto-engines). Step 7 cleans ansible_agdev. Docs and report
close out.

**Risks to verify first (start of Step 1):**
- GraphQL names/filterability of `desired_service_placements` and
  `desired_node_operational_configs` (incl. `local_endpoint`/`tailscale_endpoint` relations),
  and JSONField behavior of `placement.config`.
- Reading realized-Device custom fields via GraphQL (`_custom_field_data` or per-field), and
  interface/MAC/IP traversal on `devices`/`virtual_machines` needed by the evaluation port.
- Resolve empirically against live, pin the queries, and record deviations (REST fallback per
  collection is acceptable, as in Phase 1 Step 2).

## Step 1 — Typed three-source fetch layer (`nctl_core/sources/`)

- `sources/desired.py` — one pinned GraphQL query fetching the full desired graph: nodes
  (+lifecycle/node_type/realized ids), endpoints, IP ranges, operational configs (+endpoint
  relations), placements, services (+dependencies). Pydantic read-models for each (the
  Decision-2 schema home). The existing `dnsmasq_query.py` desired-side fetch migrates onto
  this layer.
- `sources/actual.py` — pinned GraphQL query for the actual side: devices/VMs with
  custom-field actual facts, interfaces (+MACs), IP addresses. Port `actual_facts.py`'s
  allowlist (`ActualFacts`, `read_actual_facts`, `actual_type_problem`,
  `missing_required_facts`) here unchanged.
- `sources/observed.py` — typed accessors over `dumps.py`'s raw `facts`/`self_reported`
  (hostname, system, primary IP/MAC, interfaces, collected_at), fulfilling the "Phase 2 owns
  their typing" note. One bad dump degrades that node to `unknown`, never fails the run.
- `SourceSnapshot` — one object bundling the three sources plus fetch timestamps/errors; every
  consumer (drift, production render, dnsmasq render) takes a snapshot, so a command reads each
  source at most once.
- Tests: respx fixtures for the pinned queries; dump fixtures for typed accessors.

## Step 2 — Port the production composer, `nctl render production` + parity gate

- Port `production_inventory.py`, `production_inventory_contract.py` (minus the Job-input byte
  contract), and the already-ported-in-Step-1 `actual_facts.py` into `nctl_core/production/`.
  Input dataclasses stay; the adapter builds NodeInputs from the Step 1 snapshot instead of the
  ORM (mirror `_build_production_node_inputs`, `jobs.py:715`).
- Deployment profiles are read **directly** from `<ansible.playbook_dir>/vars/deployment_profiles.yml`
  and validated with the ported `validate_deployment_profiles`. Keep computing
  `canonical_json_digest` locally from that mapping so the schema `1.0` document/report shapes
  (and the parity diff) are unchanged; the digest becomes provenance-only. The transport half
  of the contract (`parse_profile_job_input`, the serialize/verify playbook handshake) is not
  ported.
- CLI: `nctl render production [--out DIR] [--json]` (envelope `nctl.render.production.v1`,
  `data` = report + inventory YAML text).
  - Default: inventory YAML to stdout.
  - `--out` (default: the configured generated-inventory dir): write `production.yml` +
    `production.reports/<generation_id>.json`, validating with `ansible-inventory --list`
    against a temp copy before an atomic replace (the Phase 1.5 pattern).
- **Parity gate (before Step 6 deletes anything)**: run the live `Export Production Inventory`
  Job once (via the existing `export_nintent_production.yml` path), diff `production.yml` and
  the report against `nctl render production` on the same live data — host vars, group
  membership, skipped reasons, and drift entries must match exactly (generation_id /
  generated_at excluded). Record procedure and result in the report; mismatch = Step 1/2 bug.
- Port nintent's production/contract/actual-facts test suites to pytest alongside.

## Step 3 — Comparator framework and drift core (`nctl_core/drift/`)

- **Diff record** (the stable Phase 3/4 interface): `target` (kind: node/service, slug/name,
  ids), `code` (stable snake_case vocabulary, seeded from the existing skip/gap/drift codes),
  `severity` (`error` | `warning` | `info`), `desired` / `actual` (small JSON evidence
  values), `sources` (which of the three sides produced each value), `message` (one prose
  sentence — the "desired has a DHCP reservation, but actual has no MAC registered" line).
- **Status vocabulary** per target, derived not stored:
  - `unknown` — required actual data missing or stale (no realized device, no/stale dump,
    fetch error), reusing `actual_state_problem` freshness rules;
  - `drifting` — any `error`-severity diff;
  - `converged` — no diffs (or `warning`/`info` only — warnings surface in the payload either
    way);
  - `converging` — diffs exist but an nctl apply/reconcile operation targeting the node is
    newer than the newest actual observation (read from the Phase 0 events/operations
    directory). Until Phase 4 makes such operations common this will rarely fire; the enum and
    rule are defined now so the schema doesn't change later.
- **Comparator registry**: `register(resource_type)` decorator; a comparator takes the
  `SourceSnapshot` (plus per-node context) and yields diff records. Registration order never
  affects output — results are sorted by `(target, code)`. This is the pluggability the
  roadmap asks for; Phase 4 reconcilers will map `code` → playbook.
- Initial comparators (Step 4 fills the heavyweight ones): node identity/existence,
  dump-vs-Nautobot ingest lag (dump newer than `last_seen` custom field ⇒ `info`
  `ingest_lag`, feeding `unknown`/`converging` decisions), production policy (reusing
  `evaluate_platform_policy` + skip-reason helpers from Step 2, so composer `skipped`/`drift`
  and `nctl drift` agree by construction).

## Step 4 — Port the evaluation logic as comparators; switch dnsmasq's MAC source

- Port `evaluations.py`'s pure logic into `nctl_core/drift/` comparators, adapted from
  ORM-`getattr` to Step 1 read-models (Phase 1 did the same for dnsmasq): node
  candidate-ranking and mismatch lists; endpoint IP/interface matching, DesiredIPRange
  classification (valid/invalid/overlap), DHCP-MAC candidate extraction and
  `dhcp_reservation_ready`; service lifecycle/dependency gaps. Gap entries map onto the Step 3
  diff record (`code` from the gap vocabulary, status via the ported `_status_from_gaps`
  severity mapping). Port nintent's evaluation tests to pytest with dict fixtures.
- `render dnsmasq` MAC-source switch: replace the `intent_evaluations` GraphQL fetch in
  `dnsmasq_query.py` with the ported extraction over the Step 1 snapshot (same inputs the
  Evaluate Jobs read, computed fresh instead of persisted).
- **Parity gate A (evaluations)**: run the live Evaluate Jobs once, dump the resulting
  `IntentEvaluation` rows (REST/GraphQL), and compare per-target status, gap codes, and
  dhcp-mac candidates against the ported comparators on the same live data. Differences that
  are pure staleness (rows older than current actual state) are re-checked after a fresh Job
  run, not waved through.
- **Parity gate B (dnsmasq)**: `nctl render dnsmasq` output must be byte-identical
  (conf record lines, summary, skip reasons) before vs after the MAC-source switch on live
  data. This is the regression gate protecting Phase 1's deliverable.

## Step 5 — `nctl drift`

- CLI: `nctl drift [--host SLUG] [--service NAME] [--json]`.
  - `--json`: envelope `nctl.drift.v1` — `data` = `summary` (counts by status/severity),
    `targets` (per node/service: status + diffs), `sources` (fetch timestamps, dump errors),
    `generated_at`. This payload is the Phase 3 dashboard input and the Phase 4 reconcile
    input; treat additions as cheap, renames as expensive.
  - Text mode: one line per target (`slug  status  n diffs`) plus diff messages — a rendering
    of the JSON, per the Phase 0 convention.
  - Exit code 0 (drift is a successful answer, not an error) unless the run itself fails;
    `--check`-style gating can come later if a caller needs it.
- Drift is a read (fast, synchronous): no operation ID; it *reads* the operations directory
  for the `converging` rule but does not write events.
- Tests: snapshot fixtures covering each status and a golden `nctl.drift.v1` payload.

## Step 6 — Delete both proto-engines in nintent (single push cycle)

- Delete: `ExportProductionInventory`, `SyncDeploymentProfiles`,
  `EvaluateNodeIntent/EndpointIntent/ServiceIntent` Jobs; `production_inventory.py`,
  `production_inventory_contract.py`, `actual_facts.py`, `deployment_profiles.py`,
  `evaluations.py` (whatever `ReconcileDesiredIPAMIntent` still needs — e.g.
  `plan_endpoint_ipam_reconcile` lives elsewhere; keep only what a grep proves is still
  imported); models `IntentEvaluation` + `DeploymentProfileProjection` with migrations; their
  UI/API surface (views, tables, filters, forms, urls, navigation, serializers — enumerate by
  grep at implementation time); `_upsert_evaluation` / `_latest_evaluations`;
  `ReconcileDesiredIPAMIntent`'s evaluation side effect (the IPAM plan/apply logic is
  untouched); the ported test files.
- Bump nintent to 0.6.0; run the nintent test suite locally.
- Commit, ask the user to push, rebuild dev Nautobot without cache, restart; verify the Job
  list shows neither proto-engine, `nctl status` stays green, and `nctl drift` /
  `render dnsmasq` / `render production` still work (their GraphQL queries must not reference
  the deleted types — guaranteed by Steps 2/4).

## Step 7 — ansible_agdev cleanup

- Delete `playbooks/nautobot/export_nintent_production.yml`,
  `playbooks/nautobot/verify_deployment_profiles_contract.yml`,
  `playbooks/nautobot/sync_nintent_deployment_profiles.yml`, and
  `playbooks/tasks/nintent_serialize_deployment_profiles.yml`.
  `vars/deployment_profiles.yml` stays (now read by nctl directly);
  `docs/production_inventory_contract.md` is rewritten to describe the nctl-owned composition
  and the death of the byte contract (or folded into nctl docs with a pointer).
- With `production.yml` now generated by `nctl render production`, complete the deferred
  Phase 1 live proof when `agdnsmasq.local` is reachable: `nctl apply dnsmasq` check+diff and
  real apply against the dev cluster; record in the report (still environment-gated — do not
  block phase exit on host availability, mirror Phase 1's handling).

## Step 8 — Docs and report

- `nctl README`/docs: `drift` and `render production` usage, the `nctl.drift.v1` and
  `nctl.render.production.v1` schemas, comparator registry (how Phase 4 adds one), the
  three-source model and status vocabulary.
- Update nintent/ansible_agdev READMEs where they describe the deleted Jobs/playbooks.
- `p2/report*.md` in the established style: pinned queries, parity procedures/results
  (production, evaluations, dnsmasq before/after), the Decision-1/2 outcomes as implemented,
  and any REST fallbacks taken.

## Out of scope

- The dashboard (Phase 3) — but `nctl.drift.v1` is designed as its input.
- Reconcile orchestration, collect→ingest takeover, `code`→playbook mapping (Phase 4).
- Phase 1.5's hosts-intent migration (independent; whichever lands first establishes the
  inventory-write pattern).
- nauto's `Ingest Nodeutils Inventory` Job and the custom-field vocabulary it writes — the
  drift engine reads them as-is; changing ingest is Phase 4 territory.
- `Import/Analyze/Preview Intent Sources` and the IPAM write path of
  `ReconcileDesiredIPAMIntent` — correctly ledger-side, untouched beyond the side-effect
  removal.

## Exit criteria (from roadmap, made checkable)

- [x] `nctl drift --json` returns cluster-wide status (`converged/drifting/converging/unknown`
  per node/service) with structured diffs in one run against the live dev cluster, computed
  from the three sources (nintent desired via GraphQL, Nautobot actual, nodeutils dumps).
- [x] Comparators are registered per resource type via the registry; adding one requires no
  change to the drift core.
- [x] `nctl render production` output matches the last live Job export (host vars, groups,
  skipped, drift; procedure recorded), and writes a validated
  `inventories/generated/production.yml`.
- [x] The deployment-profiles byte contract is gone: no serialize/verify/sync playbooks, no
  `SyncDeploymentProfiles`/`DeploymentProfileProjection`, profiles read directly from the
  ansible_agdev checkout.
- [x] The Evaluate Jobs and `IntentEvaluation` are deleted (Decision 1 executed); `render
  dnsmasq` output is unchanged through the MAC-source switch; nintent 0.6.0 deployed and
  `nctl status` green.
- [x] Desired-state processing logic exists only in `nctl_core` (Decision 2): nintent retains
  ORM models, importers, and transactional Jobs only.
- [x] `uv run pytest` passes in nctl including the ported production/contract/evaluation
  suites; nintent's remaining suite passes.

## Suggested commit order

1. nctl: three-source fetch layer + read models + tests (Step 1).
2. nctl: production composer port + `render production` + tests (Step 2; parity gate run
   against live before proceeding).
3. nctl: comparator framework + drift core (Step 3).
4. nctl: evaluation-port comparators + dnsmasq MAC-source switch + tests (Step 4; parity
   gates A/B against live).
5. nctl: `nctl drift` CLI + envelope + tests (Step 5).
6. nintent: delete proto-engines, migrations, 0.6.0 bump (Step 6; the single push/rebuild
   cycle).
7. ansible_agdev: playbook/task deletions + doc rewrite (Step 7).
8. Parent repo: submodule bumps, docs, `p2/report*.md` (Step 8).
