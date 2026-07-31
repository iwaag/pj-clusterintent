# Phase 3 — Remaining Work

Steps 1-3 of [plan.md](plan.md) are implemented and committed (see
[report.md](report.md)): metadata/probe-config plumbing, nodeutils binding
observation, and nctl's five-state evaluation folded into drift/convergence.
`nodeutils`/`nctl`/`ansible_agdev` are pushed to origin and the superproject
gitlink already points at the pushed commits (`ansible_agdev` `9b3afae`,
`nctl` `d72d873`, `nodeutils` `7030bbd`) — no gitlink move is outstanding.

## Blocked: live actuation cannot run from this session

`nctl reconcile <slug> --refresh-observation --yes` (real SSH/Ansible
actuation against aghub/agpc/agstudio) is rejected by this environment's
auto-mode tool classifier, independent of in-conversation approval. Retrying
the identical command does not help. This blocks both remaining steps below
until the operator runs the commands directly from their own terminal.

## Step 4 — Deploy and live baseline (not done)

Run from the repository root:

```
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
uv run --project nctl nctl reconcile agpc --refresh-observation --yes
uv run --project nctl nctl reconcile agstudio --refresh-observation --yes
```

Then confirm via `uv run --project nctl nctl drift --json`:

- evidence present for all three nodes' `llm_provider` binding
  (`observed_services["node-agent"].bindings.llm_provider`);
- all three show binding state `satisfied` (not `binding_unknown`, which is
  the current state — confirmed live before this session paused);
- whole-cluster drift converged.

Report the exact `nctl drift --json` output (or at least the per-node
binding state and overall convergence) back so it can be recorded in
`report.md`.

## Step 5 — Fault drills (not started, needs separate approval)

Per plan.md Step 5, requires explicit approval before running (it mutates a
live node and stops the shared Ollama provider):

1. Hand-edit `opencode.json` on one consumer node -> refresh observation ->
   confirm `binding_misbound` in drift.
2. Stop Ollama on agstudio -> refresh observation -> confirm
   `binding_unreachable` (and the provider's own `service_not_running`).
3. Restore both -> reconcile -> refresh observation -> confirm whole-cluster
   convergence again.

Record all three outputs in `report.md`.

## Completion criteria still open

From plan.md's "Completion criteria" section, not yet verified live:

- mis-editing OpenCode config produces `misbound` drift on that consumer
  (verified only via a doctored unit-test snapshot in Step 3, not live);
- stopping Ollama produces `unreachable` (not yet exercised live);
- restoring both and reconciling returns the cluster to converged (not yet
  exercised live);
- freshness threshold is chosen and written down — done
  (`service_observation_max_age_hours`, default 24h, threaded into every
  binding's evidence as `stale_after_hours`) — this one criterion is
  already satisfied;
- all gate runs with counts recorded in `report.md` — done for Steps 1-3
  (nctl 1085 passed, nodeutils 68 passed, Ansible conformance 3 passed); no
  additional gate is expected from Steps 4-5 (they are live verification,
  not code changes).
