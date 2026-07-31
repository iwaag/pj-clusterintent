# Idea A — Service Binding as Desired and Actual State

## Status

Design proposal. This document defines the minimum domain contract for a
service relation. It is not an implementation plan and does not prescribe a
migration path, code layout, API shape, or user-interface implementation.

## 1. Purpose

The system must represent and inspect a runtime relation such as:

```text
node-agent on aghub -> Ollama on agstudio
```

The relation is part of desired state because it affects how the consumer is
configured. It must also have actual-state evidence, because the existence of
the provider alone does not prove that the consumer is configured to use it or
can reach it.

The core outcomes are:

- show which service placement requires which provider service;
- reject a desired state in which the required provider cannot be selected;
- determine whether the actual consumer is bound to and can use the selected
  provider;
- include the relation in convergence;
- prevent retirement or deletion of a provider that still has consumers; and
- identify services with no inbound relations without treating that fact alone
  as permission to delete them.

## 2. Domain boundaries

Three different concepts must remain separate.

### 2.1 Runtime service binding

A consumer service placement requires a provider service and is configured
with the provider placement's endpoint. This is the relation defined by this
proposal.

### 2.2 Deployment-profile action ordering

Profile metadata may require one reconciliation action to precede another.
That is an actuation rule, not desired cluster topology. A runtime binding may
produce an action-order constraint, but profile ordering is not stored as a
service binding and does not become actual state.

### 2.3 Host and artifact requirements

Packages, executables, container images, files, and similar prerequisites are
requirements of a placement or deployment profile. They are not provider
services and must not be represented by this relation.

## 3. Graph model

The canonical graph is a placement graph:

```text
DesiredServicePlacement (consumer)
    -- DesiredServiceBinding -->
DesiredService (provider)
    -- resolution -->
DesiredServicePlacement (provider instance)
    -- endpoint -->
DesiredEndpoint
```

The consumer end is a placement rather than a service because configuration,
observation, and actuation occur at placement level. The declared provider end
is a logical service so that the relation describes what the consumer needs,
while the active provider placement describes where that need is fulfilled.

### 3.1 DesiredServiceBinding

The binding contains only:

| Field | Meaning |
|---|---|
| `consumer_placement` | The placement whose runtime configuration consumes the provider |
| `binding_name` | The consumer configuration slot, for example `llm_provider` |
| `provider_service` | The required logical provider service |

The identity is:

```text
(consumer_placement, binding_name)
```

Every binding is required. There is no optional flag, manually maintained
resolution status, free-form target name, notes field, dependency type, or
lifecycle of the binding itself.

`binding_name` is not a provider type. It identifies the consumer-side slot
whose configured value and reachability will be observed. Its meaning is part
of the consumer deployment profile's closed contract.

## 4. Desired-state invariants

A valid binding satisfies all of the following:

1. The consumer placement is active.
2. The consumer service and provider service are active.
3. The provider service has exactly one active placement.
4. The provider placement references one usable service endpoint.
5. The binding does not resolve back to its own consumer placement.
6. The resolved placement graph is acyclic.
7. The consumer deployment profile declares the `binding_name` and knows how
   to configure and observe it.

A usable endpoint has an address, protocol, and port sufficient to produce the
consumer-facing endpoint value. Endpoint normalization must be deterministic,
so the same desired snapshot always produces the same value.

Zero provider placements is an unresolved required binding. More than one
active provider placement is ambiguous. Neither case may be resolved by an
arbitrary ordering or implicit fallback.

These invariants make resolution a deterministic computation. Resolution is
not desired data and must not be entered or corrected manually.

## 5. Actual-state evidence

Actual binding state is observed at the consumer placement. It is not inferred
only from the desired rendering and is not inferred only from the provider
being active.

For each binding, observation supplies the minimum evidence below:

| Evidence | Meaning |
|---|---|
| `binding_name` | The profile-defined binding slot that was inspected |
| `configuration_status` | Whether the real consumer configuration was read and contained a value |
| `configured_endpoint` | The normalized endpoint value found in the real consumer configuration |
| `reachability_status` | Whether a bounded probe from the consumer to that endpoint succeeded |
| `observed_at` | Freshness timestamp for the evidence |

The observer reads only a profile-defined, allowlisted value from the actual
consumer configuration. It must not return the complete configuration file or
credentials. A generic search through arbitrary configuration files is not
part of the contract.

Reachability is tested from the consumer node. A provider-local health check
cannot replace this evidence because DNS, routing, address binding, and
firewall behavior may differ between provider and consumer.

The provider placement's normal service observation remains authoritative for
whether that placement itself is running. Binding observation does not create
a second service-health ledger.

## 6. Binding evaluation

Evaluation first resolves the desired provider placement and endpoint, then
compares them with fresh consumer evidence.

The binding states are:

| State | Condition |
|---|---|
| `unknown` | Required observation is absent, unreadable, invalid, or stale |
| `unbound` | The consumer configuration was read but contains no endpoint for the binding |
| `misbound` | The configured endpoint differs from the resolved desired endpoint |
| `unreachable` | The configured endpoint matches desired state but the consumer-side probe fails |
| `satisfied` | The configured endpoint matches and the fresh consumer-side probe succeeds |

Desired resolution failures are reported separately from these actual states:

- provider placement missing;
- provider placement ambiguous;
- provider endpoint missing or unusable;
- invalid binding name for the consumer profile;
- self-reference; and
- relation cycle.

A required binding is converged only when:

1. desired resolution succeeds;
2. its actual binding state is `satisfied`; and
3. the selected provider placement is itself converged under the normal
   service-placement rules.

Consequently, consumer convergence includes the selected provider's
convergence. A consumer cannot be reported converged merely because its config
contains the expected URL.

## 7. Reconciliation semantics

The resolved binding contributes a provider-before-consumer ordering constraint
when both placements require actuation. This ordering is derived from the
desired relation; it is not another stored edge.

The reconciliation scope of a consumer includes the selected provider
placement for evaluation and observation. Reverse inspection of a provider
includes all consumer placements that bind to it, so the effect of changing or
removing the provider is visible before mutation.

The binding does not authorize a different or broader actuation by itself. The
existing registered reconciliation action for each placement remains the only
actuator.

## 8. Retirement and deletion safety

An active inbound binding protects both the provider service and its selected
provider placement.

The desired state is invalid if it attempts to retire or delete the provider,
deactivate or delete its provider placement, or remove its usable endpoint
while retaining an inbound binding. An atomic desired-state change may remove
or retarget the consumer bindings in the same decision.

Before provider retirement or deletion, the system must present the exact
inbound set:

```text
provider: ollama / ollama-agstudio
consumers:
  - aghub / node-agent / llm_provider
  - agstudio / node-agent / llm_provider
```

A service with no inbound bindings is `unreferenced`; it is not automatically
unused. Standalone and operator-facing services can legitimately have no
consumer represented inside the cluster.

Absence of inbound bindings is therefore only one removal precondition. A
service is eligible for final desired-record deletion only when:

- it has no inbound bindings;
- its lifecycle has explicitly been declared `retired`;
- it has no active placements; and
- normal actual-state checks have established that its managed runtime is
  absent.

There is no automatic retirement or deletion based on graph degree.

## 9. Canonical inspection result

The system exposes one deterministic graph projection for human and machine
inspection. Each edge contains:

- consumer service and placement identity;
- `binding_name`;
- provider service identity;
- resolved provider placement and endpoint identity, when resolution succeeds;
- actual binding state;
- desired-resolution or actual-state gap codes; and
- observation freshness.

This projection is derived from current desired and actual state. It is not a
separately maintained graph or persisted convergence cache.

## 10. Core scope exclusions

The following are intentionally outside this design:

- optional dependencies;
- external or unmanaged providers;
- multiple-provider selection, primary flags, failover, load balancing, or
  locality preferences;
- version constraints, capability matching, and service discovery;
- bindings to packages, binaries, files, images, databases represented as raw
  resource strings, or other non-service artifacts;
- generic parsing or discovery from arbitrary configuration files;
- automatic retirement, garbage collection, or deletion recommendations;
- historical dependency telemetry;
- UI layout, graph drawing technology, and additional convenience reports;
- schema migration, compatibility fields, legacy input support, and code
  organization.

If one of these becomes a demonstrated requirement, it must be designed as a
separate change rather than anticipated by unused fields in the core model.

## 11. Example

Desired relation:

```yaml
consumer_placement: node-agent-aghub
binding_name: llm_provider
provider_service: ollama
```

Deterministic desired resolution:

```yaml
provider_placement: ollama-agstudio
provider_endpoint: ollama-api
endpoint: http://agstudio.home.arpa:11434/v1
```

Actual evidence from `aghub`:

```yaml
binding_name: llm_provider
configuration_status: present
configured_endpoint: http://agstudio.home.arpa:11434/v1
reachability_status: reachable
observed_at: 2026-08-01T00:00:00Z
```

Provided that the `ollama-agstudio` placement is also converged and the
evidence is fresh, the binding is `satisfied` and contributes no drift.
