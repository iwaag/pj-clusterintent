# Phase 4 Implementation Plan: Automatic convergence loop

Parent: [roadmap.md](../roadmap.md) — Phase 4: turn drift detection into resolution with one
bounded operation, and make AI the exception handler rather than the routine executor.

## Current state (as of 2026-07-16)

- Phases 0, 0-EX1, 1, 1.5, 2, and 3 are complete. The normal nctl surface is now `status`,
  `drift`, `dashboard`, `render dnsmasq`, `render hosts-intent`, `render production`, and
  `apply dnsmasq`. `nctl drift --json` (`nctl.drift.v1`) is the desired/actual/observed source
  of truth; `nctl dashboard` is a subscriber of that payload and writes only a derived status
  cache back to nintent.
- The Phase 1.5 closeout is newer than the Phase 3 closeout: the last Job-based export has now
  been removed. Bootstrap and production inventory rendering both belong to nctl. The only
  Ansible-to-Nautobot Job plumbing still active is the collect/ingest path assigned to this
  phase.
- `nctl_core.events.OperationLog` already writes one JSONL file per operation and
  `apply dnsmasq` is the reference long-running command. Its Ansible invocation, inventory
  validation, recap parsing, and artifact layout are currently private to
  `dnsmasq_apply.py`; Phase 4 must factor and reuse them rather than create a second subprocess
  implementation.
- `converging` already exists in `nctl.drift.v1`, but its current implementation treats any
  event-data mention of a target slug as an operation affecting that target. That was adequate
  scaffolding before reconcilers existed, but is too broad once `reconcile` itself emits many
  events. Without tightening it, a harmless `step_started` event can make unresolved drift look
  like change is in flight.
- `ansible_agdev/playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml` currently owns
  four concerns in one playbook: run host collection, slurp reports, construct a batch, and POST
  the nauto `Ingest Nodeutils Inventory` Job. It does **not** wait for the JobResult to reach a
  terminal state. The old deleted shared Job helper did poll, so Phase 4 needs to restore that
  correctness in nctl rather than copy the present fire-and-forget behavior.
- `run_nodeutils_collect.yml` is already the correct host-side boundary and remains. It writes
  `/var/lib/nodeutils/inventory.json` on each selected host. nctl's
  `[inventory].dumps_dir`, however, is a **controller-side** observed-report cache; the current
  playbook never refreshes it. Phase 4 must explicitly transport and atomically install the
  selected reports there before building the ingest batch.
- nauto's `Ingest Nodeutils Inventory` Job validates reports and writes Device facts including
  `last_seen`, network facts, `observed_services`, and `service_inventory_updated_at`. It
  reports its per-item outcome only in Job logs today; a completed Job can therefore have
  skipped one or all reports without giving nctl a structured result.
- nintent retains the correctly placed transactional `Reconcile Desired IPAM Intent` Job. It
  can create/link explicit DHCP-reserved IP addresses and already emits
  `ipam-reconcile-summary.json`, but it is cluster-wide today; a host-scoped reconcile must not
  mutate unrelated endpoints.
- Service convergence has a blocking observability gap:
  - nodeutils already produces normalized `observed_services` and nauto persists it;
  - nctl's actual-state allowlist does not read those fields, so
    `evaluate_all_services()` always calls `evaluate_service_intent(..., observed_facts=None)`;
  - every service consequently gets `service_observed_facts_unknown`, and no service playbook
    can prove convergence;
  - nauto still contains a separate pure `service_placement_eval.py` used by the AI-oriented
    `Service Placement Review` Job. It is another proto drift engine and conflicts with the
    roadmap's one-engine rule.
- `ansible_agdev/vars/deployment_profiles.yml` already maps placement profiles to inventory
  groups, and the matching idempotent playbooks exist for dnsmasq, Grafana, Prometheus, node
  exporter, Nomad server/client, and node bootstrap. It does not yet declare which playbook(s)
  reconcile a profile, their dependencies, or how nodeutils recognizes the resulting service.
- Local deployment constraint (`.local/localenv_memo.md`): nintent changes require one
  commit → user push → no-cache Nautobot rebuild/restart cycle. Sequence all nintent changes
  into one such cycle. Never commit the local Nautobot token. nauto Job changes require the
  corresponding Git Repository sync/reload in Nautobot before live verification.

## Decisions taken head-on

**1. `nctl reconcile [HOST]` is plan-only unless `--yes` is supplied.** Reconciliation can
install packages, restart services, and write to the ledger. The existing `apply dnsmasq`
convention is retained: `nctl reconcile agpc` computes and persists a plan without mutation;
`nctl reconcile agpc --yes` performs it. This is still one command from detection through
verification — `--yes` is an execution acknowledgement, not a separate workflow. No interactive
prompt is used, so human, cron, and AI callers behave identically.

With no host argument, the scope is all eligible desired nodes. A host argument is a desired-node
slug, not a raw Ansible host pattern; zero or multiple matches are errors. Service actions are
selected by placements on the scoped nodes. Independent targets continue after another target
fails, but the overall operation succeeds only if every selected target reaches the final success
rule.

Every boundary still computes one **full-cluster** drift payload. The planner projects the selected
node and its placed services from that payload; it does not call filtered `build_drift` and lose
global diagnostics. Global production-contract errors block every scope because reconcile
atomically regenerates the full canonical production inventory. Unrelated node/service drift is
shown in the cluster payload/dashboard but does not make a host-scoped operation fail. This also
ensures a host reconcile can never overwrite the Phase 3 dashboard with a partial cluster view.

**2. A planner consumes drift; an executor never improvises from prose.** Reconcilers register
against stable diff codes and typed snapshot evidence. Planning produces a serializable DAG of
actions before any mutation. An action contains its reconciler ID, target IDs/slugs, claimed diff
codes, typed parameters, dependencies, whether it mutates state, and whether fresh observation is
required afterward. Message text is display-only and never parsed.

The planner classifies every error diff (and selected actionable warning/info diffs) as exactly
one of:

- `automatic` — a registered reconciler can produce a deterministic action;
- `observation` — fresh nodeutils evidence may resolve or refine it;
- `manual_review` — ambiguity/conflict means automation would be unsafe;
- `unsupported` — no reconciler exists yet.

Unknown codes never trigger a best-guess playbook. They are preserved in `plan.json` and stop an
applying operation with `manual_intervention_required`/`no_reconciler`, giving AI the drift and
event artifacts it needs.

**3. Reconcile is a bounded re-plan loop, not a one-shot shell script.** Collection, ingest, and
ledger linking can change which production hosts and service actions exist, so nctl refetches and
re-plans after those boundaries. The default maximum is three rounds. A canonical fingerprint of
the remaining error diffs detects a no-progress cycle and stops immediately. There is no unbounded
retry and no rollback fiction: the underlying Jobs/playbooks are idempotent, completed actions are
recorded, and a later run resumes from freshly computed drift.

**4. nctl owns sequencing and API calls; Ansible owns host transport and actuation.** nctl runs
`run_nodeutils_collect.yml`, then invokes Ansible's ad-hoc `slurp` module with `--tree` to retrieve
the exact selected reports. This deliberately reuses inventory connection settings instead of
adding an SSH client to nctl. The slurp/batch/REST/poll sequence lives in Python and is tested as
such; no Nautobot URL/token enters an Ansible playbook. The combined
`collect_nodeutils_and_ingest_nautobot.yml` is deleted after cutover.

**5. Transactional ledger writes remain REST/Jobs.** nctl performs only two kinds of ledger
mutation:

- PATCH an unlinked DesiredNode to one uniquely ranked actual Device/VM candidate through the
  existing nintent ViewSet. The evaluator must already have produced `actual_node_not_linked`,
  the candidate must be a unique top-ranked accepted type, and no realized link may exist. The
  exact candidate evidence is saved before PATCH.
- Trigger retained Nautobot Jobs for multi-row transactions: nauto ingest and nintent IPAM
  reconciliation. Job lookup/run/poll/artifact handling is a shared nctl client, not duplicated
  per reconciler.

Ambiguous candidates, mismatches, unexpected service locations, invalid IP policy, and destructive
removal are never auto-corrected in this phase.

**6. Service observation becomes part of `nctl.drift.v1` before service actuation is enabled.**
Port nauto's deterministic placement evaluator into nctl and adapt it to the Phase 2 snapshot.
Active placement + observed running service on the intended realized node is the convergence
fact. Missing/stopped, stale, wrong-node, insufficient-facts, and OS mismatch remain distinct diff
codes with placement/node evidence. Declared nodes (for example HAOS) remain explicitly
observation-exempt rather than falsely unknown.

To keep observation extensible, nctl renders a non-secret nodeutils probe-hints file per selected
host from deployment-profile metadata; `run_nodeutils_collect.yml` copies it and passes
`nodeutils collect --config`. nodeutils's Docker and systemd detection both honor these hints.
There is no hard-coded nctl list of service process names.

Once parity is proven, nauto's `Service Placement Review` deterministic drift path is deleted.
AI diagnosis reads `nctl.drift.v1`, `plan.json`, and the event log, matching the roadmap; it does
not run a second Nautobot-side drift computation.

**7. Actuation mapping is declarative but closed.** Extend the Ansible-owned deployment-profile
contract with optional reconciliation metadata: observed-service key/probe hints, a list of known
action kinds (`playbook` or the built-in `dnsmasq_config` action), and profile dependencies. nctl
validates this closed schema, confines playbook paths below `ansible.playbook_dir`, rejects unknown
actions/dependencies/cycles before mutation, and invokes subprocesses with argument arrays
(`shell=False`). It never executes arbitrary command strings from desired state.

Profile actions are grouped so each playbook runs once with an explicit `--limit` over the selected
inventory hosts. Profile dependencies give deterministic order (for example Prometheus before its
node-exporter scrape refresh, Nomad server before clients). The existing dnsmasq render/deploy
logic is factored into a reusable action rather than nesting a second `apply dnsmasq` operation.

**8. Final success means freshly observed convergence.** Plan-only success means “the plan was
built,” not “the cluster is healthy.” An applying operation succeeds only when:

- every selected node/service target is `converged` in a fresh final drift payload;
- no global error relevant to shared inventory/workflow execution remains;
- every mandatory action and Job completed successfully; and
- any host actuation requiring observation is followed by a newer successfully ingested report.

`converging`, `unknown`, and `drifting` are not final success states. Warning/info diffs may remain
because Phase 2 defines `converged` as “no error diff”; they stay visible as residual diagnostics.
An already-converged scope performs no mutation and exits successfully.

## Output and artifact contracts

### `nctl.reconcile.plan.v1`

The plan is both embedded in dry-plan output and written to
`<events.log_dir>/<operation_id>/plan.json`:

- `scope`: requested host (or cluster) and resolved node/service targets;
- `drift_fingerprint` and source/generated timestamps;
- ordered `actions`: ID, reconciler, action kind, targets, claimed codes, reason/evidence,
  dependencies, `mutates`, `requires_observation`, and sanitized parameters;
- `manual_review` and `unsupported` records, each retaining target + diff code + evidence;
- expected terminal codes/statuses used by verification.

The plan never contains a Nautobot token, raw report content, Ansible Vault values, or arbitrary
shell text.

### `nctl.reconcile.v1`

`data` contains:

- `operation_id`, `mode` (`plan|apply`), `scope`, and terminal `state`
  (`planned|already_converged|converged|manual_intervention_required|non_converged|failed`);
- `event_log_path`, `artifact_dir`, initial/final drift paths, and the latest plan path;
- round summaries and per-action results (status, timing, target list, Ansible recap or JobResult
  ID/URL, artifact paths; large stdout/report bodies are not embedded);
- final cluster and selected-scope status/severity summaries, selected/global residual diffs,
  dashboard update result, and whether progress was made.

Plan mode returns exit 0 when planning itself succeeds, even if it describes drift. Apply mode
returns exit 0 only for `already_converged`/`converged`; manual, unsupported, non-converged, and
execution-failure states return exit 1. Configuration/argument errors retain exit 2.

### Operation directory

Each run uses `<events.log_dir>/<operation_id>/`:

```text
plan.json
round-00/drift-before.json
round-00/drift-after-ledger.json
round-00/drift-final.json
round-00/ansible/<action-id>.stdout
round-00/ansible/<action-id>.stderr
round-00/jobs/<action-id>.json
round-00/reports/<host>.json
round-00/probe-config/<host>.yaml
result.json
```

Report/config/job artifacts are mode `0600`; directories are `0700`. Raw report text and base64
never enter stdout or the JSONL event log. Before `--yes` mutates anything, nctl verifies that the
operation directory and event log are writable. This command refuses mutation if its audit trail
cannot be established, while the existing best-effort `OperationLog` behavior for non-mutating
commands remains unchanged.

## Approach and implementation order

The first four steps establish truthful observation and reusable transports without executing a
general convergence loop. Steps 5–7 add planning, deterministic mutations, and the bounded
executor. Step 8 cuts over the old orchestration path. Step 9 proves the exit criteria live and
closes documentation.

**Risks to verify first:**

- Capture the live Nautobot 3.1 Job run response and JobResult terminal-status shapes before
  implementing the generic client. Support the response-body and `Location` variants already
  handled by the historical Ansible helper, but pin tests to shapes actually observed locally.
- Confirm `DesiredNodeSerializer(fields="__all__")` accepts PATCH of `realized_device` and
  `realized_vm` by UUID, and that the response preserves all unrelated fields. Do this read-first
  and use a disposable/already-correct row for the write test.
- Verify `ansible -m ansible.builtin.slurp --tree` output shape and filename behavior on macOS
  controller + both Linux/macOS targets before building the parser. Never parse colorized human
  stdout as the report transport.
- Verify which custom fields Nautobot GraphQL exposes only through `_custom_field_data`;
  `observed_services` and `service_inventory_updated_at` should follow the existing actual-facts
  raw-map path.
- Prove service-evaluator parity against nauto fixtures/live facts before deleting the old review
  path.

## Step 1 — Reusable operation, Ansible, and Job transports

- Factor `dnsmasq_apply.py`'s generic pieces into small nctl_core services:
  - inventory load/group expansion and explicit target validation;
  - `AnsibleRunner` for playbook/ad-hoc calls, recap parsing, timeout, sanitized command display,
    stdout/stderr artifact writes, and per-host failure extraction;
  - operation-artifact directory creation/permissions and atomic JSON/text writes.
- Keep `build_dnsmasq_apply` behavior and `nctl.apply.dnsmasq.v1` stable by making it consume the
  extracted runner. Its tests are the regression gate for the refactor.
- Extend `NautobotClient` with authenticated REST POST and streamed/file download primitives,
  preserving the GraphQL-read/REST-write boundary.
- Add `NautobotJobRunner`:
  - exact Job lookup (zero/duplicate matches fail);
  - POST `data` + `commit`, extract JobResult ID from supported body/URL/Location variants;
  - poll with monotonic timeout and explicit success/failure/cancel terminal vocabularies;
  - save a sanitized final JobResult and optionally fetch an exact named FileProxy artifact;
  - emit `job_started`, `job_poll`, `job_completed`/`job_failed` events with IDs/status only.
- Config: add strict `[reconcile]` fields with conservative defaults:
  `max_rounds = 3`, Job poll interval/timeout, Ansible timeout, remote report path, and local
  operation lock path. `inventory.dumps_dir` remains the controller cache and its example default
  changes to a writable `~/.local/state/nctl/dumps`; remote report location is no longer conflated
  with it.
- Tests: Job response variants, terminal states, timeout, auth/connection failures, ambiguous Job
  lookup, exact FileProxy selection, path confinement, recap parsing, command redaction, and
  failure to establish the audit directory.

## Step 2 — Take over collect → report cache → ingest

- Add a library-level observation pipeline (not yet the full CLI loop):
  1. resolve eligible scoped hosts from the freshly rendered bootstrap inventory;
  2. render per-host probe-hints artifacts from active placements/profile metadata;
  3. run `run_nodeutils_collect.yml` with the bootstrap inventory and explicit `--limit`;
  4. retrieve each successful host's remote report with ad-hoc Ansible slurp `--tree`;
  5. base64-decode, enforce the configured byte limit, validate with `load_dump`, verify the
     report identity belongs to the selected inventory host, and reject duplicate identities;
  6. atomically update `<inventory.dumps_dir>/<host>.json` and retain the operation copy;
  7. build the nauto `report_batch` only from validated reports, trigger `Ingest Nodeutils
     Inventory`, poll to completion, and refetch actual state.
- Partial-host behavior: a failed/unreachable host is recorded and does not prevent valid reports
  for independent hosts from being ingested. It can never be silently counted as converged, and
  the overall apply operation remains unsuccessful if that selected host cannot be verified.
- Modify nauto's ingest Job to write a versioned `nodeutils-ingest-summary.json` artifact with one
  row per source (`created|updated|unchanged|skipped`, changed fields, sanitized error), plus batch
  counts and dry-run state. Refactor `ingest_report()` to return this result without changing its
  transaction/policy behavior. nctl requires the artifact and cross-checks that every submitted
  source has one result; “Job completed but report skipped” becomes an explicit action failure.
- `run_nodeutils_collect.yml` gains only host-side support for an optional controller-provided
  probe config and continues to own clone/update/dependency-sync/collection. It gets no Nautobot
  variables or REST tasks.
- nodeutils: make both Docker and systemd service recognition include configured
  `service_probe_hints` keys; add fixtures for dnsmasq/Nomad/node-exporter-style services and keep
  the report schema at `nodeutils.inventory.v1` (an additive fact behavior, not a shape break).
- Tests: mixed Linux/macOS slurp fixtures, wrong identity, oversized/invalid/stale report,
  duplicate identity, atomic cache preservation, partial collection, batch serialization, ingest
  skips, and no raw report/token leakage in events/CLI output.

## Step 3 — Make service drift observable in nctl

- Extend `ActualFacts`/the actual GraphQL adapter to read `observed_services` and
  `service_inventory_updated_at` from Device `_custom_field_data`, with typed accessors and the
  existing stale-age policy made explicit in `DriftContext`/config.
- Port nauto `service_placement_eval.py` into nctl_core and adapt it to:
  `DesiredService`, active `DesiredServicePlacement`, operational configs, realized devices, and
  the typed actual service observations. Preserve the useful separate findings while using
  Phase-2-style diff names/evidence, for example:
  - `service_missing` / `service_not_running`;
  - `service_observation_stale` / `service_observation_missing`;
  - `service_observed_on_wrong_node`;
  - `service_placement_os_mismatch`;
  - `service_has_no_active_placement` (warning/manual, not an invented placement).
- Replace blanket `service_observed_facts_unknown` with placement-aware results. Keep the existing
  service lifecycle/dependency evaluator and merge, rather than lose, its findings.
- Give service targets an `observed_at` derived from their active placements' Device service
  timestamps so `converging` and post-actuation freshness work for services as well as nodes.
- Additive evidence in each diff must include service/placement/profile/node IDs and the observed
  service key/state/source/checked-at. The dashboard needs no special code; it remains a generic
  `nctl.drift.v1` subscriber.
- Parity gate: run the port against all nauto evaluator fixtures plus one saved/live
  desired-placement + Device-facts snapshot. Normalize naming/schema differences and require the
  same placement status, missing/stale/insufficient/OS/wrong-node findings.
- After parity, delete nauto `ServicePlacementReview`, `service_placement_eval.py`, and their
  drift-review tests/docs. Keep legitimate ledger-writing/import/generation Jobs. This makes nctl
  the only service-placement drift computer.

## Step 4 — Tighten `converging` and event semantics

- Stop scanning arbitrary event `data` for a slug. Only successful
  `actuation_completed` events explicitly carrying `target_slugs`, `claimed_diff_codes`, and
  `requires_observation=true` can represent an in-flight observed change.
- A target is `converging` only when:
  - the latest matching successful actuation is newer than its relevant observation timestamp;
  - every current error diff is claimed by that action (unrelated errors stay
    `drifting`/`unknown`); and
  - no later failure/cancellation event invalidates it.
- Ledger-only actions do not use `converging`; nctl refetches immediately and reports their real
  result. Failed Ansible/Job actions never create a converging state.
- Update `docs/event-log.md` with core reconcile events:
  `plan_created`, `round_started`, `action_started`, `action_completed`, `actuation_completed`,
  `observation_completed`, `drift_resolved`, `non_converged`, and the existing terminal events.
- Tests cover the dangerous cases: a generic event mentioning a slug, failed actuation, one
  claimed + one unclaimed error, service timestamp freshness, and successful actuation followed
  by newer observation.

## Step 5 — Reconciler registry, plan schema, and Ansible workflow metadata

- Add `nctl_core.reconcile` with typed `Reconciler`, `ReconcileAction`, `ReconcilePlan`, registry,
  deterministic planner, DAG validation/topological sort, and drift fingerprinting. Registry
  order must not affect serialized plan order.
- Initial reconcilers:
  - `observe_node`: missing/stale/insufficient node or service evidence and `ingest_lag`;
  - `link_actual_node`: the unique `actual_node_not_linked` case from Decision 5;
  - `reconcile_ipam`: `missing_actual_ip_address`/`actual_ip_address_not_linked` only when the
    endpoint is eligible for the retained Job;
  - `service_profile`: missing/not-running service on an active placement with a declared
    reconciliation action;
  - `dnsmasq_config`: render/deploy the whole deterministic config, limited to selected
    dnsmasq target hosts;
  - `new_node_baseline`: run the Linux baseline only for a node newly realized during this
    operation and eligible for that workflow.
- Extend `deployment_profiles.yml`'s validator and data with optional reconciliation metadata.
  Encode the existing playbooks/actions and dependencies there, including platform-specific
  Nomad client playbooks. A declared/externally managed profile may say `observe_only`; a profile
  with neither action nor exemption is `unsupported`, never silently satisfied.
- `new_node_baseline` is a bootstrap action, not a permanent drift assertion: current nodeutils
  facts cannot prove each baseline setting. Record successful execution, but do not invent a
  “baseline converged” fact. A future collector/comparator can promote it to standing
  reconciliation when there is observable evidence.
- Manual-review table (tests pin it) includes at least: ambiguous/multiple candidates, actual
  type/hostname/serial/platform conflicts, invalid/ambiguous IP ranges or interfaces,
  unresolved service dependencies, inactive service lifecycle, unexpected service removal, and
  production contract errors.
- Planner tests cover each known current diff code. A test fails when a new error code is added
  without explicit automatic/observation/manual/unsupported classification — preventing silent
  behavior drift.

## Step 6 — Ledger reconcilers and host scoping

- Node link reconciler:
  - save precondition evidence and current row representation;
  - PATCH exactly one of `realized_device`/`realized_vm` by UUID;
  - refetch and assert that exact link; never clear or replace an existing link;
  - emit the selected candidate score/reasons but no unrelated Device facts.
- nintent 0.9.0: add an optional DesiredNode selector to `Reconcile Desired IPAM Intent` so a
  host-scoped operation filters endpoints to that node; cluster scope retains current behavior.
  Keep `include_inactive=false`. Version the existing summary artifact and include selected node
  IDs/slugs so nctl can verify scope. No model migration is expected.
- nctl's IPAM reconciler runs the Job, requires success + exact summary artifact, verifies no
  out-of-scope plan row, and refetches drift. Conflicts/skips remain manual findings rather than
  being hidden by Job success.
- Land all nintent work in one commit/push/rebuild cycle. Verify `nctl status` and existing CRUD,
  GraphQL, dashboard-status PATCH, and IPAM dry-run behavior after deployment.

## Step 7 — `nctl reconcile`: bounded executor, verification, and dashboard

- CLI: `nctl reconcile [HOST] [--yes] [--max-rounds N] [--json]`.
  `--max-rounds` is bounded to a small safe range and overrides config for diagnosis/tests.
- Acquire one controller-local reconcile lock before planning. Phase 5 can replace this with a
  server-side operation lock; Phase 4 deliberately permits only one mutating reconcile at a time
  to avoid inventory replacement and Job races.
- Plan mode: build initial drift + plan, persist both, update no ledger/dashboard state, emit the
  `nctl.reconcile.v1` envelope with `state=planned`, and stop.
- Apply mode execution per round:
  1. build/save one fresh full-cluster drift, project the selected scope + global blockers, and
     create the plan;
  2. stop successfully if already converged and there are no selected automatic maintenance
     actions;
  3. stop before mutation if the plan has blocking manual/unsupported error findings;
  4. run required bootstrap observation/ingest actions for missing actual state;
  5. refetch/re-plan; run deterministic node-link and scoped IPAM ledger actions;
  6. refetch; atomically regenerate the **full** production inventory (even for host scope, so a
     partial document never replaces the canonical inventory);
  7. execute service/profile/dnsmasq actions in DAG order, once per playbook with explicit host
     limits; continue independent targets after a per-target failure;
  8. collect/ingest fresh reports for every successfully actuated host that requires observation;
  9. build/save one final full-cluster drift, verify the selected scope/global blockers, compare
     fingerprints/progress, and either converge, start the next round, or stop non-converged.
- Factor Phase 3 dashboard generation into a function accepting the already-built final drift
  envelope. On every apply terminal path with a valid full-cluster drift payload, atomically refresh
  `index.html`/`drift.json` and push the same statuses; never call `build_drift` a second time and
  risk dashboard/result disagreement. Dashboard/write-back failure is recorded as a warning and
  does not overwrite the reconcile terminal reason.
- Write `result.json` last and emit exactly one `finished` event. Handle SIGINT/termination by
  marking the current action/operation interrupted where possible; do not start another action.
- End-to-end tests with fake runners/clients cover: already converged, dry plan, new-node
  discovery→ingest→link→production render, scoped IPAM, service playbook→fresh observation→
  convergence, independent partial failure, manual block before mutation, no-progress stop,
  max-round stop, dashboard degradation, lock contention, and interruption.

## Step 8 — Cut over Ansible entry points and remove old orchestration

- Delete `playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml`; verify there is no
  remaining Ansible task that calls Nautobot's Jobs API or reads a Nautobot token.
- Keep `run_nodeutils_collect.yml` and document it as a host-side primitive normally invoked by
  nctl, still usable directly for diagnostics.
- Replace the old Makefile `pipeline`/`collect-ingest` sequencing with the canonical nctl entry
  point (`nctl reconcile --yes`). Keep explicit bootstrap/production inventory targets for
  diagnostics and manual recovery.
- Update ansible_agdev README/admin/contract docs: nctl performs collection sequencing, report
  cache installation, Job polling, and verification; Ansible performs remote collection and
  playbook actuation only.
- Re-run repository-wide searches for `collect_nodeutils_and_ingest_nautobot`, inline
  `/api/extras/jobs/` calls in Ansible, and Nautobot token variables outside legitimate nctl/dev
  config documentation.

## Step 9 — Live rollout, failure proof, docs, and closeout

- Preflight against the local dev environment:
  - `nctl reconcile agpc` (or another reachable node) produces a plan and zero writes;
  - inspect action scope/limits and manual classifications before `--yes`;
  - confirm operation directory permissions and absence of secrets/raw reports in event/output.
- Deploy/sync in dependency order: nodeutils/ansible changes, nauto ingest summary + removal of the
  duplicate service-review path, the single nintent 0.9.0 push/rebuild, then nctl.
- Happy-path live proof on one reachable node:
  collection → controller dump cache → completed ingest Job + summary → optional deterministic
  node link/IPAM → production inventory → applicable playbook(s) → newer collection/ingest →
  final `converged`, with matching dashboard/status cache. Use an existing harmless placement or
  a documented temporary fixture whose creation/removal is explicitly recorded.
- Cluster/partial proof: include a known unreachable host and confirm reachable targets still
  progress, the unreachable target remains non-converged, overall exit is 1, and the final drift,
  per-host failure, plan, Job/Ansible results, and event log remain available.
- Failure-path spot checks: bogus Job terminal failure, Job timeout, report rejected by ingest,
  Ansible nonzero/unreachable, unchanged diff fingerprint, unknown diff code, lock contention,
  and unwritable audit directory (must fail before mutation).
- Documentation:
  - nctl README and output/event docs for reconcile modes, schemas, artifacts, config, exit codes,
    bounded retries, and AI exception workflow;
  - parent README's routine path becomes `nctl reconcile --yes`;
  - nintent/nauto/nodeutils/ansible docs reflect their final boundaries;
  - reports record exact live commands, Job API shapes, parity evidence, deployment commits, test
    counts, and any deliberately unsupported diff codes.
- Optional only after the exit criteria pass: document a cron/systemd/launchd example invoking
  `nctl reconcile --yes --json` and notifying on nonzero exit. Do not build a scheduler or a
  client-specific AI skill into nctl.

## Out of scope

- A daemon, remote operation queue, HTTP API, WebSocket streaming, or distributed lock — Phase 5.
- MCP or any ChatGPT/Codex-specific skill as part of reconciliation core. AI consumes neutral JSON
  and event files.
- Automatic destructive correction: unlinking realized objects, deleting IPs, removing services
  observed on the wrong node, changing desired intent, resolving ambiguous candidates/ranges, or
  inventing service placements/dependencies.
- Rollback of successful idempotent playbook/Job actions. Failure is diagnosed from current drift
  and artifacts; the next run computes a fresh plan.
- Claiming convergence for unobservable settings (the new-node baseline is execution-recorded
  only) or declared/external systems beyond their explicit observation policy.
- Parallel reconcile operations. Parallelism inside one operation may be added later only where
  action dependencies and logs remain deterministic; Phase 4 favors correctness and evidence.
- Notification delivery itself. A nonzero exit and stable artifacts are the integration boundary.

## Exit criteria (from roadmap, made checkable)

- [ ] `nctl reconcile [HOST]` creates a complete deterministic dry plan without writes;
  `nctl reconcile [HOST] --yes` performs drift → required ledger/Ansible actions → fresh
  nodeutils collection → completed/verified ingest → final drift in one bounded operation.
- [ ] Every mutating step is represented in the JSONL event log and typed action results; initial,
  intermediate, and final drift plus `plan.json`/`result.json` remain under the operation ID on
  success and failure, with no token/raw-report leakage.
- [ ] The collect/ingest orchestration lives in nctl. Ansible retains
  `run_nodeutils_collect.yml` and host actuation but contains no report batching, Nautobot Job API,
  polling, or token plumbing; the combined old playbook is deleted.
- [ ] nctl polls nauto ingest and nintent IPAM Jobs to terminal success and validates their
  structured summary artifacts. A skipped/rejected report or out-of-scope IPAM action cannot be
  mistaken for success.
- [ ] Service drift reads real placement-scoped `observed_services`; at least one registered
  service profile is live-proven missing/not-running → playbook → newer observation → converged.
  nauto no longer computes a second service-placement drift result.
- [ ] Automatic reconcilers are registered for observation/ingest, unique actual-node linking,
  scoped IPAM, dnsmasq, current service-profile playbooks, and new-node bootstrap. Ambiguous,
  destructive, invalid-policy, and unknown cases stop with explicit manual/unsupported records.
- [ ] Host scope never mutates/actuates an unrelated desired node. Cluster scope preserves
  independent progress while returning failure if any selected target remains
  drifting/converging/unknown or a mandatory action fails.
- [ ] Reconcile stops on convergence, unchanged error fingerprint, maximum rounds, manual block,
  or execution failure; it never loops indefinitely. `converging` is based only on successful
  observation-requiring actuation and cannot be triggered by an arbitrary event mention.
- [ ] Reconcile always computes full-cluster drift once per boundary and projects host scope from
  it. The final full-cluster payload is the exact payload used to regenerate the Phase 3 dashboard
  and status cache; no partial dashboard or second drift read creates a disagreement.
- [ ] Live proof covers one reachable happy path and one partial/failure path. Final nctl,
  nintent, nauto, nodeutils, and ansible_agdev suites/lint/syntax checks pass, with counts and
  deployment state recorded in `p4/report*.md`.

## Suggested commit order

1. nctl: shared artifact/Ansible runner + generic Nautobot Job runner + config/tests (Step 1).
2. nodeutils + ansible_agdev + nauto + nctl: probe hints, host collection transport, structured
   ingest result, observation pipeline/tests (Step 2; do not delete old playbook yet).
3. nctl: service observation/evaluator + parity tests; nauto: delete duplicate service drift review
   only after the parity gate (Step 3).
4. nctl: precise converging/event semantics + docs/tests (Step 4).
5. ansible_agdev + nctl: reconciliation metadata contract, planner/registry/plan schema/tests
   (Step 5).
6. nintent 0.9.0 + nctl: scoped IPAM Job and ledger reconcilers (Step 6; the single nintent
   push/rebuild cycle).
7. nctl: bounded executor/CLI/dashboard reuse/end-to-end tests (Step 7).
8. ansible_agdev: delete the combined collect/ingest playbook, Makefile/docs cutover (Step 8).
9. All affected repositories + parent: live verification fixes, final docs, submodule pointers,
   exit checklist, and `p4/report*.md` (Step 9).
