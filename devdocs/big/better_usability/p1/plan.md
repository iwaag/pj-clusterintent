# Better Usability Phase 1 Implementation Plan: Honest, Target-Local Production Findings

Parent: [roadmap.md](../roadmap.md) — Phase 1. Rationale:
[discussion.md](../discussion.md). Authoritative field/failure decisions:
[p0/field-classification.md](../p0/field-classification.md), especially §2
(`DesiredServicePlacement.config`), §5 (runtime consumers and transition impact), §6
(failure-scope matrix), and §8 (Phase 1 assignment).

## Goal

Make production composition honest and safe before Phase 2 changes any mechanism model or
derivation rule:

1. a missing or invalid value owned by one node or one of its placements skips only that node;
2. every active placement that is recorded but cannot enter production because its node lifecycle
   is out of scope produces a visible, structured finding, including an empty `config` object;
3. `nctl drift`, the dashboard, and `nctl reconcile` preserve the finding's target, severity,
   message, and evidence instead of turning it into a global error or losing its context; and
4. a target-local blocker prevents unsafe production actuation on that target but does not suppress
   independent work for healthy targets in the same cluster reconcile.

This phase changes `nctl` only. It does not change nintent models, GraphQL, live ledger rows,
Ansible roles, deployment-profile schemas, or production inventory host variables.

## Current state (as of 2026-07-20)

- Phase 0 is complete (`p0/report0.8.md`). Its verification baseline is 518 passing `nctl` tests
  and 88 passing nintent tests. Phase 1 touches only `nctl`, so the nintent suite is a regression
  check, not an implementation surface.
- `compose_production_inventory()` validates the shared deployment-profile map before iterating
  nodes and validates the assembled inventory/report afterward. These are correctly global
  boundaries and must remain so.
- Inside the eligible-node loop, `missing_operational_config` and 14 other node/placement-owned
  `ContractError` codes escape to `production_render.py` or `drift/comparators.py`. One bad node
  therefore aborts the entire render or becomes one `Target(kind="global")` drift record.
- `_host_actual_skip_reasons()` already demonstrates the required isolation shape for missing,
  stale, or insufficient actual data: add a node entry to `report["skipped"]`, omit that host and
  all of its placement memberships, and continue composing other nodes.
- The composer filters out lifecycle-ineligible nodes before the loop. Active placements on a
  `planned`, `deprecated`, or `retired` node therefore leave no report or drift evidence. This is
  the exact silent-discard path from `discussion.md` Example 1.
- `production_policy()` currently understands only string skip reasons and the
  `desired_actual_os_mismatch` drift shape. It cannot preserve a caught exception's human message,
  stage, placement identity, or config evidence.
- Every target-scoped Phase 1 code is absent from `reconcile/classify.py`; converting its target
  from `global` to `node` without registering it would fail closed with
  `UnclassifiedDiffCodeError`.
- The reconcile executor stops before all actions whenever `plan.has_blocking_findings()` is true.
  Thus merely localizing a diff is not enough: a bad node's manual-review record would still
  suppress unrelated healthy-node actions at execution time.
- `nctl status` is controller-health output (Nautobot reachability, dumps, submodules), not the
  desired/actual target-status surface. Target status is derived by `nctl drift` and rendered by
  the dashboard; this phase does not overload the health command with drift computation.

## Decisions taken head-on

### 1. All per-node composition failures use a node target

The six errors raised while mapping placement config are attributed to the owning node, not to a
new `Target.kind="placement"`:

- production inventory is atomic at the host-variable/host-membership boundary, so the observable
  consequence is that this host is skipped;
- host-scoped reconcile already selects node targets and the services placed on them;
- dashboard tiles and nintent status push already have a durable node row to address; and
- `DiffRecord.desired`/`actual` and the render report can retain the exact placement ID,
  `instance_name`, profile, schema version, desired state, and config without overloading `Target`.

This settles the implementation-detail question left to Phase 1 by
`p0/field-classification.md` §6/§9. A new placement target would add filtering, grouping,
dashboard, status-push, and reconcile-scope semantics without improving diagnosis.

### 2. Local errors are an explicit allowlist, not a blanket `except ContractError`

Define and test stable code sets close to the composer:

- node/policy/connection: `missing_operational_config`, `invalid_actual_state_policy`,
  `unsupported_observed_host_os`, `invalid_platform_power`, `endpoint_node_mismatch`,
  `unresolved_connection_path`, `invalid_connection_path`, `invalid_connection_address`;
- placement mapping: `unknown_profile`, `unsupported_config_schema`,
  `invalid_placement_config`, `unknown_config_key`, `missing_required_config`,
  `invalid_profile_value_type`; and
- host merge: `conflicting_host_variable`.

Catch each group only around the stage that gives it target ownership. In particular,
`invalid_connection_address` is local only when raised by connection resolution for the current
node; the same code raised during final document validation remains global. An unexpected code
escaping a per-node helper is re-raised, not silently downgraded. This preserves the Group A/B/C
boundary in Phase 0 §6 by construction.

### 3. Use the existing report collections; do not invent an unversioned side channel

Keep `report["skipped"]` as the deterministic list of omitted hosts and their reason codes. Populate
the already-defined, currently empty `report["errors"]` array with structured detail for caught
target-local contract errors:

```json
{
  "item_type": "desired_node",
  "desired_node": "Node display name",
  "desired_node_slug": "node-slug",
  "desired_node_id": "node-id",
  "code": "unknown_profile",
  "severity": "error",
  "message": "unknown_profile: unknown deployment profile 'missing'",
  "stage": "placement_config",
  "evidence": {
    "placement": {
      "id": "placement-id",
      "instance_name": "primary",
      "deployment_profile": "missing",
      "config_schema_version": "1",
      "desired_state": "active",
      "config": {}
    }
  }
}
```

The exact evidence keys are part of the tests. Node-only stages use an equally structured node,
operational-config, endpoint, or assignment summary and never include secrets or arbitrary actual
facts. `validate_production_report()` must validate the required shape of new error entries rather
than accepting arbitrary values in the array.

`production_policy()` emits one `DiffRecord` per structured error and suppresses the duplicate
generic record that the matching `skipped[].reasons` code would otherwise create. Existing actual-
state skip reasons, which have no `errors` entry, retain their current generic conversion.

This is additive use of collections already present in production report schema `1.0`; inventory
variables and report top-level keys do not change. `nctl.render.production.v1` and
`nctl.drift.v1` likewise already expose open `dict` evidence. No schema-version bump is required in
Phase 1. Phase 2 still owns the intentional production schema bump for provenance and removal of
`nintent_operational_config_id`.

### 4. The unapplied-intent code is `active_placement_not_applied`

For every `DesiredServicePlacement` with `desired_state="active"` whose owning node lifecycle is
not in `PRODUCTION_ELIGIBLE_LIFECYCLES`, emit a report drift entry and a node-targeted diff with:

- code: `active_placement_not_applied`;
- severity: `warning`;
- message: the placement is recorded as active but not applied because node lifecycle
  `<value>` is outside production scope;
- desired evidence: placement ID, `instance_name`, `deployment_profile`,
  `config_schema_version`, `desired_state`, and the complete JSON `config` value; and
- actual/effective evidence: node lifecycle, sorted eligible lifecycle values, and
  `application_status="not_applied"`.

The finding is emitted even when `config == {}` because the entire active placement, not merely a
non-empty config key, is deferred. A disabled placement is intentionally off and produces no such
finding. Phase 1 limits this code to the lifecycle gate identified by Phase 0; an unsupported
`node_type` remains outside this initiative unless a separate audit assigns it.

The lifecycle check must not depend on loading deployment profiles. Extract it as a pure helper
used by both the composer and `production_policy()`: when drift degrades an unreadable/missing
profile file to `{}`, it still emits unapplied-placement warnings before returning from the
profile-dependent production comparison. Recorded intent must not disappear merely because a
second diagnostic source is unavailable.

Warning severity follows Phase 0 §6. It appears in `nctl drift` text/JSON, the dashboard's warning
count and node detail, and the production render report. Under the existing status rule, warnings
do not turn a target from `converged` to `drifting`; the dashboard tile remains green but shows a
warning badge/detail when opened. The reconcile classification below still makes the deliberate
human decision visible in its plan.

### 5. Every Phase 1 code is manual review, with target-local execution semantics

Register all 15 localized contract codes plus `active_placement_not_applied` as
`Classification.MANUAL_REVIEW` with no reconciler ID, matching Phase 0 §6. Strengthen the
classification coverage test so it imports/compares the composer's declared local code set and
the unapplied-intent code; the current source scan omits `production/composer.py` and therefore
cannot guard this vocabulary.

Classification and blast radius are separate concerns:

- a global production-contract finding still blocks every reconcile action;
- a node-targeted production finding blocks production actuation for that node;
- ledger-link/IPAM and observation actions remain independently plannable when they are safe and
  may improve evidence; and
- healthy nodes/services in a cluster plan continue to act even while another node remains in
  manual review.

The planner derives the set of production-blocked node slugs from these 16 node-targeted codes.
When it constructs a service-profile/dnsmasq action, it removes blocked slugs from that action's
`parameters.host_slugs`; an action with no remaining hosts is omitted. It must not silently erase
the reason: the original manual-review record remains in `plan.json`. Other automatic actions are
not discarded merely because the same cluster plan contains a local finding.

The executor changes its stop order accordingly:

1. global blockers stop before any action;
2. local blockers plus no executable actions terminate as `manual_intervention_required`;
3. local blockers plus independent actions execute those actions, regenerate the production
   inventory (where blocked nodes are safely skipped), and re-plan; and
4. after independent progress is exhausted, a still-present local blocker terminates as
   `manual_intervention_required`, with `progress_made=true` and completed rounds retained.

If the round limit is reached immediately after independent progress while a known local blocker
remains, the terminal reason is `manual_intervention_required`, not a misleading
`max_rounds_reached`. This is the orchestration half of “fail locally”: render isolation without
executor isolation is incomplete.

### 6. Phase 1 remains an nctl-only, non-schema rollout

- Django migration: none.
- nintent model/form/REST/GraphQL/YAML/seed changes: none.
- Existing ledger rows: read-only and unchanged.
- Production inventory schema: remains `1.0`; host variables are byte-compatible for included
  healthy nodes.
- nctl envelopes: remain `nctl.render.production.v1`, `nctl.drift.v1`,
  `nctl.reconcile.plan.v1`, and `nctl.reconcile.v1`; only additive findings/evidence appear.
- Deployment: one nctl commit can be tested and used immediately. No nintent push, image rebuild,
  Nautobot restart, or coordinated mixed-schema window exists.
- Rollback: return to the preceding nctl revision. No data rollback is needed. If Phase 1 generated
  an inventory while a bad node was skipped, regenerate with the selected revision; never restore
  an unvalidated artifact by hand.

### 7. The `ip_policy` default disagreement is deferred to Phase 4

Phase 0 §8 allowed the model-default (`static`) versus YAML-import-default (`external`) conflict to
be owned by Phase 1 or Phase 4. It is assigned to Phase 4 here because correcting it requires an
nintent writer/default change and possibly a rebuild, while the roadmap defines Phase 1 as the
pure-nctl safety phase. The discrepancy remains documented in the authoritative classification
table and is not forgotten or silently reclassified.

## Reader/writer and failure integration matrix

Phase 0's mandatory planning checks require every applicable boundary to be explicit:

| Boundary | Phase 1 read/write behavior | Required change | Tests |
|---|---|---|---|
| nintent models/forms/REST/GraphQL/YAML/import Jobs/seeds | Read by the existing GraphQL snapshot only; no writes | None | Existing desired-source tests remain green |
| `sources/desired.py` typed snapshot | Supplies nodes, placements, config, lifecycle, and operational config | No shape change | Existing source/adapter tests |
| `production/adapter.py` | Converts snapshot placements/config into composer inputs | No field addition required | Adapter regression test proves config (including `{}`) reaches the composer |
| `production/composer.py` | Produces inventory plus structured skipped/error/drift findings | Add scoped catches, error evidence, lifecycle-gated placement warnings, deterministic ordering | Composer matrix below |
| `production/contract.py` | Validates shared profiles and final inventory/report | Keep Group A/B global; validate the new report error/drift member shapes | Contract tests for valid and malformed entries |
| `production_render.py` / CLI | Converts only remaining global `ContractError` to failed envelope | No control-flow change; success envelope now carries local findings | Render and CLI mixed-node tests |
| `drift/comparators.py` | Converts report findings to target-scoped diffs | Preserve message/evidence/sources; deduplicate skip/error pairs; dispatch both drift codes | Comparator and end-to-end drift tests |
| `drift/status.py` | Error → drifting/unknown; warning-only → converged | No code change unless a regression is exposed; pin intended behavior | Status tests |
| dashboard render/push | Renders drift payload; pushes node status only | No special backend; pin visibility and no synthetic placement row | Dashboard HTML/push tests |
| `reconcile/classify.py` | Fail-closed code classification | Add all 16 manual-review codes and exhaustive coverage | Classification tests |
| `reconcile/planner.py` | Builds manual records and automatic actions | Retain evidence; filter production host lists by local blockers without suppressing unrelated actions | Mixed good/bad plan tests |
| `reconcile/executor.py` | Executes bounded plan rounds | Global stop, local partial progress, then truthful terminal state | Mixed good/bad executor tests |
| output docs/compatibility | Additive v1 payload rules | No frozen field removal/rename | Compatibility snapshot suite |

## Mandatory Phase 0 gate coverage

The six planning gates in `roadmap.md` are closed as follows:

1. **Failure scope:** Decision 2 preserves Groups A/B as global and makes exactly the 15 audited
   Group C codes node-local, including the dual-site `invalid_connection_address` distinction.
2. **End-to-end findings:** Decisions 3–5 define code, target, severity, message/evidence, sources,
   report/drift/status/dashboard effects, and reconcile classification/execution behavior.
3. **Readers and writers:** the boundary matrix inventories every applicable model ingress and
   nctl consumer. There are no Phase 1 ledger writers.
4. **Overrides and provenance:** Phase 1 derives/defaults no values and moves no override. It
   preserves the operator's placement config verbatim as evidence and never guesses a correction;
   Phase 2 retains ownership of derived/override provenance.
5. **Schema/data transition:** Decision 6 states no Django/data transition, no top-level/output
   version bump, an nctl-only rollout, and the rollback procedure. The new payload content is
   additive within existing v1 dictionaries/arrays.
6. **Isolation and orchestration:** Steps 1.2, 1.5, and 1.6 test pure composition, mixed good/bad
   drift, scoped planning, partial safe execution, global blocking, and read-only live behavior.

## Step 1.1 — Freeze the baseline and local-failure contract

Before changing behavior:

1. Run the focused production, drift, classification, planner, and executor suites, then the full
   `nctl/tests` suite. Record the exact count in `p1/report1.1.md` when the phase is implemented.
2. Reconfirm the 57 `raise ContractError` sites recorded by Phase 0 §6 and compare them to the
   declared Group A/B/C sets. If source has changed, update the classification artifact and this
   plan in the same change before implementation.
3. Add constants for the three target-local code groups and a union used by implementation and
   tests. Do not duplicate an unconnected 15-code list in composer, comparator, and classifier.
4. Add a small internal structured finding/error carrier containing code, message, stage, node,
   optional placement, and JSON evidence. It is an internal implementation object, not a second
   public diff schema.

## Step 1.2 — Localize every Group C failure in the composer

Refactor the eligible-node loop around one deterministic “include or skip this host” boundary:

1. Missing operational config becomes a structured local error and skipped-host entry immediately;
   it no longer raises.
2. Wrap platform-policy evaluation, endpoint ownership, and connection resolution with the
   node-code allowlist. Preserve the original `ContractError` message/path in the report and attach
   only the relevant input summary.
3. Wrap each active placement's `map_placement_config()` call with the placement-code allowlist so
   the exact placement evidence is available at the catch site.
4. Wrap host-variable merge with the merge-code allowlist and include the sorted active assignment
   sources/placement IDs in evidence.
5. On a local error, omit the entire node, mark all of its placements inactive for report counts,
   add exactly one deterministic `skipped` entry and one `errors` entry, and continue to the next
   node. Never leave partial selector/service group membership behind.
6. On an unexpected `ContractError` code, re-raise to the existing outer boundary. Shared profile
   validation remains before the loop and final closed-document/report validation remains after it.
7. Sort errors deterministically by node slug, code, stage, and placement instance/ID so repeated
   input produces byte-stable report JSON.

The first-error-per-node behavior is intentional for this phase: composition cannot safely proceed
farther for that host, while the structured stage/evidence makes the discovered blocker actionable.
A later pass may reveal the next blocker after the first is fixed; the cluster and other nodes still
render on every pass.

## Step 1.3 — Report active placements deferred by lifecycle

Retain a sorted view of all input nodes before constructing the eligible subset. For every node
whose type is production-capable but lifecycle is not `approved`/`active`, inspect its placements
and emit one deterministic `active_placement_not_applied` report drift entry per active placement.

Implement the selection/evidence construction as a pure helper that does not accept or validate
deployment profiles. The composer uses its entries in the render report, and the drift comparator
uses the same helper when `context.profiles` is empty so its current degraded-profile early return
does not hide lifecycle findings.

- Include `config` verbatim after confirming it is a JSON object from the typed snapshot; `{}` is
  evidence, not grounds for omission.
- Do not map or validate config against deployment profiles for an ineligible node; the finding is
  about the lifecycle gate, and profile validation at this point would turn deferred intent into a
  second, speculative error.
- Do not add the host to inventory/groups or change the existing meaning of the `eligible`,
  `included`, `active_placements`, and `inactive_placements` summary counts. The drift array is the
  new visibility surface; silently redefining old counters is unnecessary.
- Use stable ordering by node slug, placement instance name, and placement ID.

## Step 1.4 — Carry findings through drift, target status, and dashboard

Update `production_policy()` to consume the richer report:

1. Emit structured local errors first as node-targeted, error-severity diffs. Copy the report
   message, put input/intent evidence under `desired`, effective/observed evidence under `actual`,
   and use `sources=["desired"]` or `["desired", "actual"]` according to the stage.
2. Convert remaining skipped reason codes exactly as today, excluding `(node, code)` pairs already
   represented by structured errors.
3. Dispatch report drift by code: preserve the existing OS-mismatch mapping and add the placement
   mapping. Unknown composer drift codes must fail a focused unit test rather than be rendered with
   the OS-specific message template.
4. Evaluate the pure lifecycle helper before the current `if not context.profiles: return` path;
   when profiles are present, consume the composer's copy and do not emit duplicates.
5. Assert a local error affects only its node's status (`drifting`, except existing evidence-gap
   codes which remain `unknown`) and a placement warning leaves status `converged` while incrementing
   warning severity and remaining visible in the detail list.
6. Render an envelope containing `active_placement_not_applied` through the real dashboard template
   and assert its message, warning badge, placement config evidence, and safe HTML escaping are
   present. Status push must update only the owning node row and must not invent a placement target.

No change is made to the controller-health `nctl status` command; `nctl drift`/dashboard are the
target-state/status surfaces defined by the existing architecture.

## Step 1.5 — Classify findings and isolate reconcile execution

1. Add the 16 codes to the manual-review set and assert every declared local composer code has
   exactly one classification with `reconciler_id is None`.
2. Preserve report evidence through `ManualReviewRecord.evidence`; plan text may remain concise,
   while `plan.json` must contain the placement/config or local contract context needed for repair.
3. Derive production-blocked node slugs from Phase 1 local codes after scope selection. Because all
   such diffs are node-targeted, `nctl reconcile HOST` automatically selects only the matching
   blocker and cluster scope sees the complete set.
4. Filter those slugs from service/dnsmasq action host lists. Retain actions for other hosts and all
   independent ledger/observation actions. Do not create an empty-host action.
5. Split `has_blocking_findings()` semantics into global versus local queries without changing the
   serialized plan model. Global records stop immediately; local records allow non-conflicting
   actions to run.
6. Re-plan after partial progress. When local findings remain and no safe action remains, return
   `manual_intervention_required` with the manual records, completed rounds, final drift/dashboard,
   and `progress_made=true` where applicable.

## Step 1.6 — Test the full failure and orchestration matrix

### Composer isolation

Use parameterized fixtures to exercise all 15 Group C codes. Each case must contain at least one
healthy node and one bad node and assert:

- composition returns successfully;
- only the bad node is absent from `ssh_hosts` and every selector/service group;
- the healthy node and its mapped placement variables remain intact;
- `skipped`, `errors`, counts, message, stage, and evidence are correct;
- output ordering and rendered JSON remain byte-stable; and
- representative Group A and Group B errors still abort globally.

Include explicit tests for both `invalid_connection_address` call sites: the node endpoint/address
case is local, while malformed assembled-document data remains global.

### Unapplied intent

Cover `planned`, `deprecated`, and `retired` lifecycles; active versus disabled placements;
`config={}` versus non-empty config; more than one placement; a production-eligible control node;
empty/missing deployment-profile context; and deterministic evidence/order. Confirm node-type-only
ineligibility does not accidentally gain this lifecycle-specific code and the fallback path does
not duplicate findings when profiles are available.

### Drift/dashboard

Run a mixed snapshot through the real composer comparator and drift engine. Assert one bad node's
error does not create a global target, the healthy node's other diffs are still evaluated, the
placement warning is visible with complete evidence, status/severity summaries follow Decision 4,
and the static dashboard renders both code and evidence.

### Reconcile planner/executor

Cover at least these orchestration cases:

1. one local composition error and no actions → dry plan succeeds, apply ends
   `manual_intervention_required` without mutation;
2. one bad node plus an independent healthy-node action → the healthy action and production
   regeneration execute, the bad node remains skipped, and terminal state is
   `manual_intervention_required` after progress;
3. service action spans blocked and healthy host slugs → only healthy slugs remain; all-blocked
   action is omitted;
4. host-scoped reconcile for the healthy node excludes the other node's local blocker;
5. host-scoped reconcile for the bad node includes its manual record and no unsafe actuation;
6. global Group A/B error plus otherwise actionable drift → zero actions execute; and
7. every error-level code and the intentionally classified warning reaches planning without
   `UnclassifiedDiffCodeError`.

Use fakes for executor mutation tests. Live verification is dry/read-only unless the user separately
authorizes a real `--yes` actuation.

## Step 1.7 — Verification and implementation report

Focused tests:

```bash
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

Full regression:

```bash
uv run --project nctl pytest -q nctl/tests
```

Read-only/local live checks against the configured development environment:

```bash
uv run --project nctl nctl render production --json
uv run --project nctl nctl drift --json
uv run --project nctl nctl reconcile --json
```

For the current all-`planned` dev ledger, the expected Phase 1 live result is a successful
production render (possibly with no included production hosts), one
`active_placement_not_applied` warning per active placement with its config preserved, a successful
drift envelope with node-local targets, and a dry reconcile plan containing manual-review evidence.
Do not use `--out`, `dashboard` with push enabled, or `reconcile --yes` for this read-only check.

Also confirm:

- no nintent/Django migration exists;
- root changes are limited to Phase 1 docs and the intended `nctl` submodule revision;
- the `nintent`, `nauto`, `ansible_agdev`, and `nodeutils` worktrees are unchanged; and
- no token, live object UUID, or full unrestricted actual-fact payload appears in tests, reports,
  or committed artifacts.

Record implementation results in `p1/report1.1.md` (baseline/contract), then one concise report per
implementation step or a final consolidated `p1/report.md`. Reports must state the exact test count
and live-check outcome; they must not copy the local API token from `.local/localenv_memo.md`.

## Out of scope

- Changing or dissolving `DesiredNodeOperationalConfig`; deriving OS, connection path, or endpoint;
  adding provenance fields; or bumping production schema — Phase 2.
- Changing `DesiredNode.lifecycle` defaults or adding lifecycle promotion/demotion commands —
  Phase 3.
- Fixing nintent creation-path defaults, including `DesiredEndpoint.ip_policy`, `node_type`, or
  `generate_dnsmasq` — Phase 4 per Decision 7 and Phase 0 §8.
- Changing placement config, auto-promoting a node, or guessing a valid profile/value in response
  to an error. Phase 1 reports and isolates; it does not rewrite intent.
- Introducing placement targets, new nintent status rows, or a compatibility adapter.
- Mutating the live ledger, rebuilding Nautobot, or running real reconcile/Ansible actions as part
  of plan verification.

## Exit criteria

- [x] Every one of Phase 0 §6 Group C's 15 codes is caught only at its target-owned stage and
  produces a node-local structured skip/error; none becomes global.
- [x] Representative shared-profile and final-output contract failures still abort globally.
- [x] A mixed good+bad render succeeds, preserves healthy inventory/group/config output, and emits
  no partial membership for the skipped node.
- [x] Every active placement on a lifecycle-ineligible, production-capable node emits
  `active_placement_not_applied`, including when `config == {}`; disabled placements do not.
- [x] Each Phase 1 finding defines and tests target kind, severity, message/evidence, source list,
  render-report effect, drift/status/dashboard effect, and reconcile classification.
- [x] All 16 Phase 1 codes are `MANUAL_REVIEW`; classification coverage cannot miss a future local
  composer code.
- [x] `nctl reconcile` never raises `UnclassifiedDiffCodeError` for these findings and never runs a
  production action against a blocked node.
- [x] A target-local blocker does not suppress independent healthy-target work; a global blocker
  still suppresses every action.
- [x] Phase 1 makes no nintent/schema/data change, leaves production inventory schema `1.0`, and
  requires no Nautobot rebuild or compatibility shim.
- [x] Focused tests, full `nctl` tests, compatibility snapshots, and read-only live checks pass;
  unrelated submodules remain clean.
- [x] The implementation report records exact evidence and confirms Phase 2 can now derive/remove
  operational config without inheriting a global-failure landmine.

## Suggested commit order

Keep commits independently reviewable but do not ship a commit that exposes node-targeted errors
before their reconcile classification exists:

1. **Composer/report contract:** declare local code sets, add structured local findings, localize
   all 15 Group C failures, register those 15 codes for manual review, and add
   composer/contract/classification tests.
2. **Unapplied-intent visibility:** add `active_placement_not_applied`, drift conversion,
   status/dashboard coverage, and that code's manual-review classification in the same commit.
3. **Reconcile isolation:** filter blocked production hosts, permit unrelated local progress,
   preserve truthful terminal state/evidence, and add planner/executor tests.
4. **Verification report:** run focused/full/live-read-only checks and add Phase 1 report(s).

Every commit that introduces a producible target-local code must include its classification and
planner coverage. Never rely on the next commit to close an `UnclassifiedDiffCodeError` window.
