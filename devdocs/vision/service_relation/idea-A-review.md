# Review of Idea A — Service Binding as Desired and Actual State

## Verdict

The direction is correct and the timing is right. Idea A precisely reverses
every cause of death of the removed `DesiredDependency` model (nintent
`aca2fa9`), and the trigger condition that `systemic_serice_coop/plan.md` set
for promoting the config-field approach to a dedicated model — needing graph
queries and invariants — has now arrived.

## Why the old model failed, and how Idea A fixes it

| Old `DesiredDependency` defect | Idea A counterpart |
|---|---|
| `raw_ref` free-form string reference; typos passed silently | FK references only; no free-form target |
| `resolution_status` stored as data, maintained by hand; rotted | Resolution is a deterministic computation, never stored |
| `dependency_kind` / `dependency_type` unused classification axes | No type field; `binding_name` is a consumer profile slot with a closed contract |
| Service→service edge; no placement concept, but config/observation happen at placement level | Consumer end is a placement; provider end is a logical service resolved to a placement |
| No actual-state evidence at all | Consumer-side observed config value + reachability probe, five explicit states |

## Points endorsed as-is

- **Consumer = placement, provider = logical service.** Configuration and
  observation are placement-scoped; the need is service-scoped. This split is
  what the old model lacked.
- **Reachability tested from the consumer node.** The 2026-07-31 agstudio
  incident proved this is not optional: the provider could not resolve its own
  client-facing DNS name (`agstudio.home.arpa`) while consumers used it
  successfully. A provider-local health check can never substitute.
- **Exactly-one-active-placement invariant.** Rejecting ambiguity as an error
  keeps resolution deterministic and leaves room to add a `primary` flag later
  without breaking anything.
- **`unreferenced` ≠ unused.** Listing services with no inbound bindings
  without treating that as deletion permission avoids the classic graph-degree
  garbage-collection trap.
- **The inspection projection is derived, not persisted.** Matches the
  existing principle that convergence is a fresh `nctl drift` computation.
- **The scope exclusions (§10).** Multi-provider, failover, version matching,
  external providers — all correctly deferred until demonstrated.

## Advice and cautions

1. **Validate invariants at the batch endpoint, atomically.** The batch REST
   API is the sole desired-state writer, which makes it the natural single
   place to enforce §4 (validity) and §8 (retirement protection). Reject at
   apply time with the exact inbound set in the error, so "accidentally
   deleting a provider" dies at preview, not at drift time. Extend the same
   inbound-set display to the `nctl prune` dry plan.

2. **Make the migration one-way.** When the binding model lands, the
   `node_agent` profile must *reject* the old `config.llm_provider_service`
   key in the same change. Never allow two sources of truth to coexist, even
   briefly. Backward compatibility is explicitly not required.

3. **Staleness must map to `unknown`, and `unknown` must block convergence.**
   Binding evidence arrives via nodeutils dumps and can be old. Decide the
   `observed_at` freshness threshold up front. The most dangerous failure mode
   of this whole design is a green converged verdict computed from stale
   evidence.

4. **Bound the probes.** One reachability probe per binding per observation
   cycle; a few seconds of timeout; probe-failed (`unreachable`) strictly
   distinguished from probe-not-run (`unknown`).

5. **Keep the config read allowlisted.** The observer returns only the
   profile-defined slot value, never the whole config file. This is the one
   place where restraint is worth keeping even in an experimental
   environment — it keeps credentials out of dumps by construction.

6. **Reuse, don't rebuild.** The pure resolver in
   `nctl/src/nctl_core/production/service_dependencies.py` already implements
   most of the desired-resolution semantics (single active placement, usable
   endpoint, classified errors, provenance). Porting it to read the binding
   model is a small change; the drift classification and inventory projection
   paths already exist.

## Precondition

The unpushed nodeutils commits from `systemic_serice_coop` (the provider
observation fix; the remote collector clones nodeutils from GitHub) must be
pushed and the agstudio refresh observation rerun before building the
actual-evidence phase on top. Otherwise the observation substrate under test
is already known-broken.
