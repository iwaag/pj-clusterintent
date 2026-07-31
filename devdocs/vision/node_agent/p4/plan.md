# Node Agent — Phase 4 Plan: Cluster intent and observation

Status: not started.
Input: [Phase 2 report](../p2/report.md), [Phase 3 report](../p3/report.md),
[roadmap Phase 4](../roadmap.md).

## Goal

Make the node agent a declared, observed, reconciled cluster service: a
`node_agent` deployment profile whose placements converge through the normal
`nctl reconcile HOST --yes` path, with `nctl drift` truthfully reporting agent
service state on each declared node. Both target nodes (`agstudio`, `agpc`)
already run the agent from Phase 2, so the live proof is *repair*: a stopped
or broken agent is detected as drift and restored by reconcile.

## Scope and decisions

- **Reuse the existing generic profile machinery.** Everything needed already
  exists for playbook-kind profiles: `deployment_profiles` +
  `deployment_profile_reconciliation` in
  `ansible_agdev/vars/deployment_profiles.yml`, `plan_service_profile` in the
  nctl planner, and the `service_missing` / `service_not_running` drift codes
  from `drift/service_placement.py`. No new orchestration concept is wanted.
- **Profile entry**: name `node_agent`, inventory group e.g.
  `node_agent_hosts`, `config_schema_version: "1"`. Profile variables are
  implementer's discretion — projecting `ollama_url` / `model` / `port`
  through the profile is allowed but not required; the existing per-host
  `vars/opencode_agent.yml` may stay as the value source this phase.
- **Reconciliation entry**: `kind: playbook` pointing at the existing
  `playbooks/agent/setup_opencode.yml` (it already handles both OSes; no
  `playbook_by_os` split needed). Adapt the playbook as needed so reconcile
  can drive it (hosts pattern vs. the new group, and the existing explicit
  `--limit` assert must accept reconcile's own `--limit` invocation).
- **Desired state**: one `DesiredService` (suggested slug `node-agent`) with
  active placements on `agstudio` and `agpc` using
  `deployment_profile: node_agent`, declared through the normal
  `.local/desired-state.yaml` batch apply. `deployment_profile` is a free
  slug field in nintent, so **no nintent model change is expected** — which
  avoids the GitHub push/rebuild cycle. If a schema change turns out to be
  required after all, stop and report before touching nintent.
- **Observation**: extend nodeutils so the agent appears in
  `observed_services` with at least presence/state, and whatever of
  {installed version, endpoint, config digest} is cheap to collect. Known
  gap: nodeutils currently lists only *running Linux system* systemd units;
  the agent is a systemd **user** service (Linux) and a **LaunchAgent**
  (macOS), so neither is observed today. Collecting user-level service state
  on both platforms is the real work of this phase's observation step; the
  exact probe commands are implementer's discretion.
- **Config digest** (roadmap's "relevant configuration digest") is
  discretionary, not required for completion. The `managed_files` probe-hint
  mechanism is currently restricted to `dnsmasq_config` actions and assumes
  one absolute path, but `opencode.json` lives at a different path per OS.
  Acceptable resolutions, smallest first: (a) skip digest drift this phase
  and converge on presence/running(+version); (b) record the digest as a
  plain observed fact without a drift code; (c) lift the `managed_files`
  restriction with per-OS paths. Do not contort the frozen dnsmasq contract
  to force option (c).
- **Ingest**: if the new facts need nauto changes to reach the Nautobot
  actual ledger, make them in the same step as the nodeutils change and run
  the nauto suite.
- **Out of scope**: Phase 5 programmatic delegation (`run`/`send`/`abort`),
  authentication beyond the loopback+SSH posture, multi-runtime abstraction,
  and any reconciliation of live conversation state.

## Minimum prohibitions (everything else is implementer's discretion)

1. No credentials, tokens, or key material in facts, drift evidence,
   operation logs, or commits.
2. Exact host scope: the same host set flows through
   plan → SSH preflight → `--limit` → post-actuation observation.
3. Session lists, transcripts, and `~/agent-work` contents never enter
   observation, the ledger, or drift — service metadata only.
4. Live cluster mutation only in the approved live steps below.

## Deliverables

```text
ansible_agdev/vars/deployment_profiles.yml       # node_agent profile + reconciliation entry
ansible_agdev/playbooks/agent/setup_opencode.yml # reconcile-compatible hosts/limit handling
nodeutils/nodeutils_collect.py                   # user-service observation (launchd + systemd --user)
nauto/...                                        # only if ingest needs the new facts mapped
nctl/tests/...                                   # multi-round planner/executor test for node_agent
devdocs/vision/node_agent/p4/report.md
```

## Steps

Usual style: one report section + commit per step; pause for user approval
before each live step.

### Step 1 — Profile metadata and playbook adaptation (local only)

- Add the `node_agent` profile and reconciliation entries; adapt
  `setup_opencode.yml` for reconcile-driven invocation.
- `--syntax-check` passes; run the compute/production conformance gate if the
  profile contract digest is affected.

### Step 2 — Observation and ingest (local only)

- nodeutils collects the agent's user-service state on macOS (LaunchAgent)
  and Linux (systemd user unit), plus any chosen extra facts.
- nodeutils suite passes; nauto suite passes if ingest changed.

### Step 3 — Drift and planner coverage in nctl (local only)

- Ensure the observed facts drive `service_missing` / `service_not_running`
  for `node-agent` placements and that the planner emits the `node_agent`
  playbook action with the exact host scope.
- One real multi-round planner/executor test: agent absent → action planned
  and executed (fixture actuation) → simulated observation of a running
  agent → fresh drift converged → no repeated action. Full nctl suite green.

### Step 4 — Desired-state declaration and dry plan (live desired write; approval required)

- Apply the `.local/desired-state.yaml` batch declaring the `node-agent`
  service and both placements (preview first, then `--yes`).
- `nctl reconcile agstudio` / `agpc` dry: with fresh observation the already
  deployed agents should read as satisfied, or show exactly the expected
  `node_agent` action if observation says otherwise. No live actuation yet.

### Step 5 — Live repair proof (approval required)

- On one node (suggest `agpc`), stop the agent service as a reversible
  fixture. Dry `nctl reconcile agpc` must show `service_not_running` and plan
  exactly the `node_agent` action for that host.
- `nctl reconcile agpc --yes` repairs it: playbook runs against exactly that
  host, fresh observation and drift show convergence, and an immediate rerun
  plans no second action.
- Confirm `nctl agent status` / `attach` from Phase 3 still work afterward.

### Step 6 — Report and close

- `p4/report.md` with per-step evidence and precise completion language.
- Commit per submodule, bump submodule pointers, update the roadmap Phase 4
  status line.

## Completion criteria

- The `node-agent` service and its placements are declared desired state,
  and `nctl drift` reports their real observed state on both nodes.
- A stopped agent is detected and repaired by `nctl reconcile HOST --yes`
  through the normal profile action path, with converged fresh drift and no
  repeated action.
- All touched component suites pass; no new nctl command surface was needed.
