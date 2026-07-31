# Node Agent — Phase 4 Report

Status: complete (2026-07-31).

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

The first fresh observation was deliberately pinned to the new nodeutils
commit. Its initial deployment correctly failed rather than falling back to
mutable `HEAD`, because the target had not yet received the commit. After the
operator published it, a Linux-only collector defect was found and corrected:
the deployed unit is `opencode-agent.service`, not `opencode.service`. The
corrected pinned revision `d5a4cf6` was then published and observed on agpc
as:

```text
source=systemd_user, state=active, unit=opencode-agent.service, version=1.18.10
```

The reversible repair fixture stopped only agpc's user service:

```text
XDG_RUNTIME_DIR=/run/user/1000 systemctl --user stop opencode-agent.service
```

The read-only `nctl reconcile agpc --refresh-observation` plan retained its
normal forced-observation action. `nctl reconcile agpc --refresh-observation
--yes` then followed the authoritative normal loop: fresh observation,
detected `service_not_running`, exactly one `node_agent` playbook action
against agpc (exit 0), post-actuation observation, and fresh node-agent drift
converged. Operation evidence is `01KYW1TH45TE8F8ZE8HS15F85C`.

An immediate repeat plan (`01KYW1VTEMRYX2912Z0G5CFX1Y`) contained no actions.
It retained only the unrelated, pre-existing observe-only
`pj-voxel3dprint`/`manual_toolchain` unsupported finding; it contained no
node-agent action or node-agent drift. `nctl agent status agpc --json` also
passed through the managed SSH path and returned HTTP 200 from the node-local
agent endpoint.

## Earlier publication blocker

For completeness, the first pinned observation attempt was:

```text
nctl reconcile agstudio --refresh-observation --yes
```

It failed during nodeutils deployment because the target could not check out
the deliberately pinned commit `070b656dd378a2f9d3de5a8086da5ef449e784bf`:

```text
fatal: unable to read tree (070b656dd378a2f9d3de5a8086da5ef449e784bf)
```

The failure was expected safe behavior: nctl refused to substitute mutable
upstream `HEAD`. It was resolved by publishing the exact revision, as above.

## Commits and current state

- `ansible_agdev` `c9d26e7` — profile and reconcile-compatible playbook.
- `nodeutils` `070b656` — user-service observation.
- `nodeutils` `d5a4cf6` — corrected Linux user-unit name.
- `nctl` `cc409f0` — profile scope/contract coverage.
- Superproject `b5294bd` — Linux observation correction and pointer update.

All touched local suites passed. Both declared node-agent placements are
observed as running, and the stopped agpc service was repaired through the
normal reconciliation action with no repeated node-agent action.
