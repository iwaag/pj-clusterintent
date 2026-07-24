# Step 9 — Finding vocabulary and scope classification

Status: complete.

Table columns per plan §Step9: `code | target_kind | target_id/slug | severity | status_effect |
reconcile_class | failure_scope | evidence | remediation`. `target_id/slug` is per-instance (the
specific desired object slug at evaluation time), so the table below fixes every column except
that one, which is always "the evaluated platform/instance/endpoint/node slug."

## Platform-scope findings

| code | target_kind | severity | status_effect | reconcile_class | failure_scope | evidence | remediation |
|---|---|---|---|---|---|---|---|
| `compute_platform_no_cluster_candidate` | platform | error | unknown | observe | shared-platform | platform config vs. live Cluster list | fix `cluster_name`/create Cluster via Phase 2 ingest |
| `compute_platform_observation_stale` | platform | warning | unknown | observe | shared-platform | `observed_at` vs. freshness threshold | re-run nodeutils collect |
| `compute_platform_multiple_cluster_candidates` | platform | error | unknown | manual | shared-platform | ambiguous Cluster match list | operator disambiguates `cluster_name` |
| `compute_platform_credential_unavailable` | platform | error | unknown | unsupported | shared-platform | actuator/credential resolution failure | operator fixes actuator config (outside nintent) |

## Instance-scope findings

| code | target_kind | severity | status_effect | reconcile_class | failure_scope | evidence | remediation |
|---|---|---|---|---|---|---|---|
| `compute_instance_no_guest_candidate` | compute_instance | error | drifting | create | target-local | platform+kind+VMID/name search result | plan create (Phase 5) |
| `compute_instance_unique_unlinked_candidate` | compute_instance | info | drifting | link | target-local | unique VMID/name match, no `realized_vm` | approved link action (Phase 4) |
| `compute_instance_guest_disappeared` | compute_instance | error | drifting | manual | target-local | prior `realized_vm` missing from fresh, *complete* observation | operator investigates; never auto-deleted |
| `compute_instance_scope_conflict` | compute_instance | error | drifting | manual | target-local | node/VMID/kind mismatch vs. desired | operator corrects desired config or actual guest |
| `compute_capacity_mismatch` | compute_instance | warning | drifting | manual | target-local | vcpus/memory_mb/root_disk_gb vs. exact typed evidence (never `disk_gb` aggregate) | operator-approved resize (Phase 6+) |
| `compute_power_mismatch` | compute_instance | warning | drifting | start | target-local | `desired_power_state` vs. `proxmox_status` | scoped start action (Phase 5); stop remains unsupported |
| `compute_template_unproven` | compute_instance | error | unknown | unsupported | target-local | Step 2/8's confirmed absence of storage-content evidence | Phase 2 storage-content observation |
| `compute_creation_value_uncomparable` | compute_instance | info | unknown | noop | target-local | `template` post-creation (plan §5.3) | none required; documented limitation |

## Endpoint-scope findings

| code | target_kind | severity | status_effect | reconcile_class | failure_scope | evidence | remediation |
|---|---|---|---|---|---|---|---|
| `compute_primary_endpoint_missing` | endpoint | error | drifting | manual | target-local | zero primary/MAC/mDNS candidates | operator adds the missing endpoint fields |
| `compute_primary_endpoint_ambiguous` | endpoint | error | drifting | manual | target-local | 2+ qualifying candidates | operator resolves to exactly one |
| `desired_mac_conflict` | endpoint | error | drifting | manual | target-local | duplicate normalized MAC across endpoints/actual | operator/dedup |
| `interface_join_ambiguous` | endpoint | warning | unknown | manual | target-local | duplicate/invalid MAC in config-vs-agent join (report 1.5 truth table) | fresh observation / manual disambiguation |

## Guest-OS / access-layer findings (guest_os target kind)

| code | target_kind | severity | status_effect | reconcile_class | failure_scope | evidence | remediation |
|---|---|---|---|---|---|---|---|
| `waiting_for_manual_initial_access` | guest_os | info | drifting (not error) | manual | target-local | compute create/link evidence retained, no guest-OS observation yet | operator completes Step 8 checklist |
| `waiting_for_ssh_enrollment` | guest_os | info | drifting (not error) | manual | target-local | offered fingerprints, no managed trust entry | operator verifies fingerprint out-of-band, `nctl ssh enroll --fingerprint ... --yes` |
| `platform_healthy_guest_os_stale` | guest_os | warning | unknown | observe | target-local | compute layer converged, guest-OS observation older than threshold | re-run guest-OS observation |
| `guest_os_healthy_platform_stale` | compute_instance | warning | unknown | observe | target-local | guest-OS layer fresh, Proxmox observation older than threshold | re-run nodeutils collect |
| `unexplained_actual_guest` | compute_instance | info | unknown | noop | target-local | observed guest with no matching `DesiredComputeInstance` | operator reviews; never auto-deleted (roadmap Decision 5) |

## Severity/scope rule (per plan §Step9 and roadmap "Drift and safety vocabulary")

- `failure_scope=shared-platform` is reserved for platform-wide blockers: no Cluster candidate,
  stale/missing platform observation, ambiguous Cluster, unavailable credentials. These may block
  every instance on that platform.
- Everything else defaults to `target-local`: one bad guest, one ambiguous endpoint, or one stale
  guest-OS observation must never block an unrelated guest's plan on the same platform (roadmap
  §Drift vocabulary, last paragraph).
- `reconcile_class=manual` is used wherever plan §Step 8/§Non-goals still forbid an automatic
  action in Phase 1-5's current scope (e.g., resize, stop, credential fix, ambiguity resolution).
  `unsupported` is reserved for actions no phase yet implements at all (QEMU root-disk drift,
  automatic delete).

## Gate evaluation

Every case named in the roadmap's "Drift and safety vocabulary" section, plus the two Step 8 safe-
stop states, has a pinned code, target kind, severity, status effect, reconcile class, failure
scope, evidence set, and remediation. Step 9 gate passed.

## Discrepancies

None. This is a naming/classification exercise; no live state was queried or changed.
