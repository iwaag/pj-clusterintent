# Node Agent — Phase 4 Report

Status: blocked pending publication of the pinned nodeutils commit (2026-07-31).

## Step 1 — Profile metadata and playbook adaptation

Added the `node_agent` deployment profile (`node_agent_hosts`, schema version
`"1"`) and its playbook reconciliation action at
`playbooks/agent/setup_opencode.yml`. The playbook now targets the generated
profile group while retaining its explicit `--limit` assertion, so the
reconcile executor's exact host limit remains the only service-actuation
scope.

Evidence:

```text
ansible-playbook -i inventories/generated/hosts_intent.yml \
  playbooks/agent/setup_opencode.yml --syntax-check
```

passed (the pre-declaration inventory correctly warned that the new generated
group did not yet exist). Compute conformance also passed (`1 passed`).

## Step 2 — Observation and ingest

nodeutils now emits a `node-agent` `observed_services` entry only when that
service is declared in nctl-generated probe hints. Linux probes the `eiji`
systemd user manager with `systemctl --user list-units --all`; macOS probes
the `com.clusterintent.opencode.agent` LaunchAgent. Inactive installed units
are retained as `inactive`, so they become `service_not_running` rather than
an ambiguous missing observation. The fact contains only state, unit/label,
and installed OpenCode version; it never includes configuration contents,
session data, or credentials.

The existing nauto `observed_services` custom-field path already persists
arbitrary service metadata unchanged, so no ingest change was needed.

Evidence: `cd nodeutils && uv run pytest -q --durations=20` — `56 passed`.

## Step 3 — Drift and planner coverage

The existing service-placement evaluator maps the normalized `active` state
to convergence and all other observed states to `service_not_running`.
`node_agent` therefore uses the established playbook profile action without
adding an nctl command surface. The new planner test verifies a two-placement
`node-agent` service scoped to `agpc` produces exactly one action with
`host_slugs: [agpc]` and
`playbooks/agent/setup_opencode.yml`.

Evidence: `cd nctl && uv run pytest -q --durations=20` — `1024 passed`.

## Step 4 — Desired-state declaration and dry plan

The normal desired-state batch preview reported `create: 3`, `conflict: 0`.
Its first commit attempt exposed an existing Nautobot batch endpoint error
when a newly-created `desired_service` supplied `values.slug` in addition to
its slug key (`DesiredService() got multiple values for keyword argument
'slug'`). Removing the redundant value made the second preview and commit
succeed:

```text
committed: {'create': 3, 'update': 0, 'delete': 0, 'unchanged': 22, 'conflict': 0}
```

The declared `node-agent` service has active `node_agent` placements on
`agstudio` and `agpc`. Dry reconcile evidence:

- `agstudio` planned only fresh observation because its existing ledger facts
  were stale.
- `agpc` planned `service_profile:node_agent:node-agent` with exact
  `host_slugs: [agpc]` and the expected setup playbook. Its unrelated
  observe-only `manual_toolchain` finding remained unsupported and was not
  included in that action.

## Step 5 — Live repair proof

Blocked before any agent was stopped or repaired. A fresh observation for
`agstudio` was started with:

```text
nctl reconcile agstudio --refresh-observation --yes
```

It failed during nodeutils deployment because the target could not check out
the deliberately pinned commit `070b656dd378a2f9d3de5a8086da5ef449e784bf`:

```text
fatal: unable to read tree (070b656dd378a2f9d3de5a8086da5ef449e784bf)
```

The commit exists locally but has not been published to the node's configured
nodeutils Git remote. nctl correctly refused to substitute mutable upstream
HEAD, so no new observation was ingested and no agent service was mutated.

To resume, an operator must push nodeutils commit `070b656` to the configured
remote (the local-environment rules reserve pushes for the user), then rerun
the fresh observation. After it succeeds, perform the planned reversible
`agpc` stop/reconcile proof and verify the immediate repeat has no action.

## Commits and current state

- `ansible_agdev` `c9d26e7` — profile and reconcile-compatible playbook.
- `nodeutils` `070b656` — user-service observation.
- `nctl` `cc409f0` — profile scope/contract coverage.
- Superproject `f1afd50` — submodule pointer integration.

All local component tests are green, but Phase 4 is not complete until the
pinned collector is available to the target nodes and the live stopped-agent
repair has converged with no repeated action.
