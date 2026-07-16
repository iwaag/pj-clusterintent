# Phase 4 Report — Step 5 (reconciler registry, plan schema, and Ansible workflow metadata)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 5. This is the fifth suggested commit
boundary. `nctl` gained a new `nctl_core.reconcile` package that turns a full-cluster `nctl drift`
result into a deterministic `nctl.reconcile.plan.v1` plan — classification, planning, and DAG
validation only. No execution (PATCH/Job/Ansible calls) exists yet; that is Steps 6-7.

## What was built

### `nctl_core/reconcile/model.py`

Typed pydantic schema matching `p4/plan.md`'s "Output and artifact contracts" section:
`PlanScope` (`cluster`/`host`), `ReconcileAction` (id, reconciler, action kind, targets, claimed
diff codes, reason/evidence, dependencies, `mutates`, `requires_observation`, sanitized
parameters), `ManualReviewRecord`/`UnsupportedRecord`, and `ReconcilePlan` itself
(`schema_version="nctl.reconcile.plan.v1"`).

### `nctl_core/reconcile/classify.py` — Decision 2's fail-closed guard

A static `code -> (classification, reconciler_id)` table covering every diff code the current
comparators/evaluators (`drift/comparators.py`, `drift/evaluation.py`, `drift/service_placement.py`,
`sources/actual.py`'s skip-reason helpers) can produce, split into:

- **observation** (`observe_node`) — evidence gaps fresh nodeutils collection/ingest may resolve:
  `ingest_lag`, `missing_actual_data`/`stale_actual_data`/`invalid_actual_timestamp`,
  `missing_actual_node`, `no_realized_device`, `missing_observed_system`/`missing_mac_address`/
  `missing_network_interface`, `service_observation_missing`/`_stale`;
- **automatic** — `actual_node_not_linked` (`link_actual_node`),
  `missing_actual_ip_address`/`actual_ip_address_not_linked` (`reconcile_ipam`), and
  `service_missing`/`service_not_running` (`service_profile`, though a specific instance can still
  resolve to `unsupported` — see below);
- **manual_review** — every ambiguity/conflict/destructive-by-design code (multiple/ambiguous
  candidates, serial/uuid/platform/hostname mismatches, IP-range/interface ambiguity, unresolved
  dependencies, inactive lifecycle, wrong-node service placement, ...).

`Target.kind == "global"` diffs are always `manual_review` regardless of code — every current
global diff is a `production/contract.py` `ContractError`, and enumerating its ~30 codes here would
duplicate an unrelated module's internals for no behavioral gain (Decision 1: contract errors block
every scope).

`classify()` raises `UnclassifiedDiffCodeError` for any node/service-level code missing from the
table. `tests/test_reconcile_classify.py::test_every_producible_diff_code_is_classified` regex-scans
the actual source files (independent of the table itself) and fails if a new literal diff code is
ever added there without a matching classification — the concrete form of "a test fails when a new
error code is added without explicit classification."

### `nctl_core/reconcile/registry.py`

`Reconciler` metadata registration (mirrors `drift/registry.py`'s shape) plus `topological_order`,
a deterministic (ties break on action id) DAG sort over `ReconcileAction.dependencies` that raises
`PlanCycleError` for a cycle, a self-dependency, or a dependency naming an action absent from the
plan.

### `nctl_core/reconcile/profiles.py` and `ansible_agdev/vars/deployment_profiles.yml`

Decision 7's "optional reconciliation metadata" lives under a new sibling top-level YAML key,
`deployment_profile_reconciliation`, keyed by the same profile names as `deployment_profiles` —
deliberately *not* an extra field inside each `deployment_profiles.<name>` entry, since that entry is
the frozen, digested production-inventory contract (`production/contract.py`) and must not grow an
unrelated key. Each entry declares exactly one of `action` (`{kind: playbook, playbook: ...}` or
`{kind: playbook, playbook_by_os: {linux: ..., macos: ...}}`, or `{kind: dnsmasq_config}`) or
`observe_only: true`; `dependencies` lists other profile names that must actuate first on any
overlapping host. `load_profile_reconciliation` validates a closed schema, confines every playbook
path under `ansible.playbook_dir`, and rejects unknown profile names, unknown dependencies, and
dependency cycles before any mutation could occur. The real checked-in file now declares: `dnsmasq`
(`dnsmasq_config`), `grafana`/`prometheus`/`prometheus_node_exporter`/`nomad_server`/`nomad_client`
(`playbook`, with `prometheus_node_exporter`→`prometheus` and `nomad_client`→`nomad_server`
dependencies; `nomad_client` uses `playbook_by_os` for its existing Linux/macOS-specific playbooks),
and `home_assistant` (`observe_only`, matching its declared/HAOS observation exemption).

### `nctl_core/reconcile/reconcilers.py` and `planner.py`

Six reconcilers are registered (`observe_node`, `link_actual_node`, `reconcile_ipam`,
`service_profile`, `dnsmasq_config`, `new_node_baseline`). `build_plan()`:

- projects the full-cluster diff list onto the requested `PlanScope` (`select_scoped_diffs`):
  global diffs always pass through; a host scope keeps that node's diffs and any service diff whose
  service has an active placement on that node; `resolve_host_node` raises `HostScopeError` for zero
  or multiple slug matches (Decision 1);
- classifies every diff (raising for an unclassified error diff, silently dropping an unclassified
  non-error diagnostic — only error diffs carry the fail-closed guarantee);
- batches every `observation`-classified diff across all targets into one `observe_node` action;
- for `link_actual_node`, re-derives the candidate from typed snapshot evidence
  (`evaluation_snapshot.evaluate_all_nodes(snapshot)[node_id].actual_refs[0]`) rather than trusting
  diff text, per Decision 2 — and falls back to `manual_review` if the snapshot no longer supports a
  unique candidate;
- for `reconcile_ipam`, adds a same-node dependency on a `link_actual_node` action in the same plan;
- for `service_profile`, resolves the service's active placements to one deployment profile (falling
  back to `manual_review` if placements disagree on profile), looks up its reconciliation metadata,
  and either builds a `service_profile`/`dnsmasq_config` action (the two share this code path; which
  reconciler id lands on the action depends on the profile's declared action kind, since Step 7 will
  dispatch a playbook run and the built-in dnsmasq apply through different code) or falls back to
  `unsupported` (no metadata, or `observe_only`);
- wires cross-action dependencies for profile-declared dependencies when the depending and
  depended-on actions' host sets overlap;
- validates the resulting DAG via `topological_order` and returns actions in that order;
- computes `drift_fingerprint` (`nctl_core/reconcile/fingerprint.py`) over the scoped diffs'
  error-severity subset only, reusing `production/contract.py::canonical_json_digest` — matches
  Decision 3's "canonical fingerprint of the remaining error diffs."

`new_node_baseline` is registered for identity only; it claims no diff code (it is a bootstrap
action Step 7's executor triggers procedurally after a fresh node link, not a drift-diff response —
matches the plan's "not a permanent drift assertion").

## Tests

`tests/test_reconcile_classify.py`, `test_reconcile_registry.py`, `test_reconcile_profiles.py`
(including one test that validates the real checked-in `ansible_agdev/vars/deployment_profiles.yml`,
not just a synthetic fixture), and `test_reconcile_planner.py` (11 new files' worth of scenarios:
host-scope projection, unknown-host error, link_actual_node candidate derivation and its manual
fallback, the reconcile_ipam→link_actual_node dependency edge, both service_profile action kinds,
its unsupported/manual fallbacks, profile-dependency ordering across overlapping hosts, observe_node
aggregation, fingerprint stability across non-error-diff changes, and the fail-closed/ignore split
for unclassified error vs. non-error diffs).

Verification:

- `cd nctl && uv run pytest -q` — **393 passed** (up from 382 before this boundary; +11 new files
  covering the reconcile package, 382 prior tests unaffected);
- `cd nctl && python3 -m compileall -q src tests` — passed;
- an AST-based unused-import scan over the seven new modules found nothing beyond the expected
  `from __future__ import annotations` false positive;
- `git diff --check` (parent, nctl, ansible_agdev) — passed.

## Deliberate non-work

- no PATCH/Job/Ansible execution — `build_plan` never mutates anything; Steps 6-7 consume this
  plan schema to actually act;
- no `nctl reconcile` CLI, operation directory, or event emission (`plan_created`/`round_started`/
  `actuation_completed`/...) — Step 7;
- no per-instance IPAM Job eligibility check beyond the code-level classification (Decision 5's
  "only when the endpoint is eligible for the retained Job" is Step 6, once the Job actually exists
  to call);
- no endpoint-level granularity inside a `reconcile_ipam` action's evidence — a node with multiple
  endpoints needing IPAM work gets one action claiming all such codes for that node, since the
  current `DiffRecord` for an endpoint gap only carries the owning node's target identity, not the
  endpoint id (a pre-existing Step 2/4 evidence gap, not something this step needed to fix to plan
  correctly);
- no `deployment_profile_reconciliation.<profile>.observed_service_key` override wiring into the
  Step 3 service-observation evaluator; `evaluate_all_services` still uses authoritative
  `DesiredService.name` as the observed key. Nothing in this step needed it, and adding it later is
  purely additive;
- no changes to `nintent`, `nauto`, or the drift engine itself (`drift/context.py`,
  `drift/engine.py`, `evaluation_snapshot.py`) — this boundary is nctl-reconcile-package plus one
  `ansible_agdev` data file, no cross-repo rebuild cycle required;
- no commit, push, or Nautobot deployment.

## Files changed in this boundary

nctl (all new except the test list, which is entirely new files):

- `src/nctl_core/reconcile/__init__.py`, `model.py`, `classify.py`, `registry.py`, `profiles.py`,
  `reconcilers.py`, `planner.py`, `fingerprint.py`;
- `tests/test_reconcile_classify.py`, `test_reconcile_registry.py`, `test_reconcile_profiles.py`,
  `test_reconcile_planner.py`.

ansible_agdev:

- `vars/deployment_profiles.yml` — added the `deployment_profile_reconciliation` section.

Parent repository:

- added this report. No commit was created.
