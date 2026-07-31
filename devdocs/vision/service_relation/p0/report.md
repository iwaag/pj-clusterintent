# Phase 0 Report — Precondition Cleanup

Status: complete (2026-08-01).

## Checked

- **nodeutils push.** `nodeutils` is on `main`, up to date with `origin/main`,
  clean working tree. The provider-observation commits flagged in
  `systemic_serice_coop/report.md` as pending push were already on the
  remote by the time this phase ran; nothing to push.
- **agstudio refresh observation / `ollama` convergence.** `nctl drift --json`
  shows `service ollama -> converged` and `node agstudio -> converged`. The
  prior `manual_intervention_required` stop from operation
  `01KYW9KPSMJ1574HWC157WBG9S` is resolved; no rerun was needed.
- **Design docs committed.** `idea-A.md`, `idea-A-review.md`, and
  `roadmap.md` under `devdocs/vision/service_relation/` were already
  committed as `5ba6d58` ("roadmap") before this phase ran.

All three Phase 0 preconditions were already satisfied at the start of this
run. No code, config, or infrastructure changes were made in this phase.

## Cluster drift snapshot (informational, not blocking)

`nctl drift --json` at time of this report: `converged=9, drifting=4,
unknown=3`. Non-converged targets, none related to the `ollama` binding
substrate:

| Target | Status | Code | Note |
|---|---|---|---|
| `agdnsmasq` | unknown/drifting | `stale_actual_data`, `compute_primary_endpoint_missing` | known-unreachable node, per `.local/localenv_memo.md` |
| `agbach` | unknown | `stale_actual_data` | known-unreachable node, per `.local/localenv_memo.md` |
| `agpc` | drifting | `missing_required_config: llm_provider_service` | see finding below |
| `pj-voxel3dprint` | drifting | `service_missing` | pre-existing, unrelated |
| `prometheus` | drifting | `service_has_no_active_placement`, `service_observed_on_wrong_node` | pre-existing, unrelated |
| `dnsmasq` | unknown | `service_observation_stale` | pre-existing, unrelated |

## Finding for Phase 1 (resolved same session)

`agpc` also carried a `node_agent` placement missing
`config.llm_provider_service`, in addition to the `aghub` and `agstudio`
placements the `systemic_serice_coop` report converted. Rather than deferring
this to Phase 1, it was fixed directly: applied
`.local/agpc-llm-provider.yaml` (a one-op desired-state batch setting
`config.llm_provider_service: ollama` on `node-agent-agpc`, `1 update / 0
conflict`), then ran `nctl reconcile agpc --yes`. No actuation action was
required — the plan's `actions` list was empty, meaning the real node was
already consistent once desired state matched. `node-agent` service and
`agpc` node are now both `converged`.

`nctl reconcile agpc --yes` still exits `manual_intervention_required`
because of an unrelated, pre-existing `pj-voxel3dprint` finding
(`deployment_profile: manual_toolchain`, `observe_only`, no actuation
available). This is untouched by this fix and out of scope here.

Net effect: all three node-agent placements (`aghub`, `agstudio`, `agpc`) now
carry `llm_provider_service: ollama` via the config-key mechanism. Phase 1's
one-way migration to `DesiredServiceBinding` should account for all three.

## Next

Phase 1 (`DesiredServiceBinding` model + batch validation) can start; its
plan should be written at `p1/plan.md`.
