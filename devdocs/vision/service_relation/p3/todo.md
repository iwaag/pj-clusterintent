# Phase 3 — Remaining Work

Steps 1-3 of [plan.md](plan.md) are implemented and committed (see
[report.md](report.md)): metadata/probe-config plumbing, nodeutils binding
observation, and nctl's five-state evaluation folded into drift/convergence.
`nodeutils`/`nctl`/`ansible_agdev` are pushed to origin and the superproject
gitlink already points at the pushed commits (`ansible_agdev` `9b3afae`,
`nctl` `d72d873`, `nodeutils` `7030bbd`) — no gitlink move is outstanding.

## Step 4 — Deploy and live baseline (binding checks done; cluster check open)

Run from the repository root on 2026-08-01 JST:

```
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
uv run --project nctl nctl reconcile agpc --refresh-observation --yes
uv run --project nctl nctl reconcile agstudio --refresh-observation --yes
```

Results are recorded in [report.md](report.md):

- done: evidence is present for all three nodes' `llm_provider` binding
  (`observed_services["node-agent"].bindings.llm_provider`), with the desired
  endpoint, HTTP 200, and `reachable`;
- done: all three evaluate as `satisfied`; the final `node-agent` service is
  `converged` with no `binding_*` diffs;
- open: whole-cluster drift is not converged (`drifting=3`, `converged=10`,
  `unknown=3`) because of pre-existing non-binding gaps on `agdnsmasq`,
  `agbach`, `pj-voxel3dprint`, and `prometheus`.

Report the exact `nctl drift --json` output (or at least the per-node
binding state and overall convergence) back so it can be recorded in
`report.md`.

## Step 5 — Fault drills (done; provider-state observation gap found)

Executed with explicit approval on 2026-08-01 JST; full outputs and operation
IDs are in [report.md](report.md).

1. done: hand-editing `agpc`'s `opencode.json` -> fresh observation produced
   `binding_misbound`; reconcile restored the desired endpoint.
2. done with a discrepancy: stopping Ollama on `agstudio` -> fresh observation
   produced `binding_unreachable` for its consumer binding. The provider was
   reported as `service_missing`, not `service_not_running`, because a stopped
   Homebrew service disappears from nodeutils enumeration.
3. done for bindings: Ollama and all node-agent bindings were restored to
   converged. Literal whole-cluster convergence remains unavailable due to the
   pre-existing non-binding gaps recorded in Step 4.

Record all three outputs in `report.md`.

## Completion criteria status

From plan.md's "Completion criteria" section:

- mis-editing OpenCode config produces `misbound` drift on that consumer —
  done live on `agpc`;
- stopping Ollama produces `unreachable` — done live for the consumer binding;
  the provider's own state is currently surfaced as `service_missing` rather
  than the planned `service_not_running`;
- restoring both returns Ollama and all node-agent bindings to converged —
  done live; literal whole-cluster convergence remains unavailable until the
  pre-existing non-binding cluster gaps are resolved;
- freshness threshold is chosen and written down — done
  (`service_observation_max_age_hours`, default 24h, threaded into every
  binding's evidence as `stale_after_hours`) — this one criterion is
  already satisfied;
- all gate runs with counts recorded in `report.md` — done for Steps 1-3
  (nctl 1085 passed, nodeutils 68 passed, Ansible conformance 3 passed); no
  additional gate is expected from Steps 4-5 (they are live verification,
  not code changes).
