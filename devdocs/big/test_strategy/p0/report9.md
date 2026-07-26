# Test Strategy Phase 0 Step 9 Report — Resolve Compatibility Against Named Consumers

Parent: [plan.md](plan.md) — Step 9.

Status: **partially complete** (Step 9 complete: compatibility policy conflict resolved; named consumer matrix recorded in `compatibility-consumers.tsv` and `compatibility-decision.md`; overall Phase 0 in progress).

## 1. Compatibility Policy Conflict Resolution

`nctl/docs/compatibility.md` previously outlined a deprecation window and parallel old/new schema shims for breaking changes. This directly conflicted with the governing project policy in `README_DEV.md` ("Current development phase permits coordinated breaking changes").

### Approved Frozen Policy for Test Strategy (Phases 1–4)

1. **Coordinated Breaking-Change Policy Governs**: Coordinated matched-version deployments across submodules replace obsolete dual-writer or dual-serializer runtime shims.
2. **Current Consumer Requirement**: Exact schema and envelope contracts actively consumed by current tools (`nctl ops`, Ansible, AI agents) are preserved.
3. **Removed Consumer Cleanup**: Fields or envelopes whose only consumer was removed (e.g. `reconciliation_status`, legacy dashboard URLs) are removed in coordinated rollouts.
4. **Durable Evidence Protection**: Past operation logs under `<events.log_dir>/` must remain readable by `nctl ops show`. Historical evidence must never silently become unreadable.

## 2. Named Consumer Schema Matrix

| Schema / Envelope | Primary Writer | Active Reader / Consumer | Decision | Policy Justification |
|---|---|---|---|---|
| `EventRecord` (v1/v2) | `nctl.events` | `nctl ops list` / `ops show` | `retain` | Essential for durable operation evidence and AI agent analysis |
| `nctl.render.dnsmasq.v3` | `nctl render dnsmasq` | `nctl reconcile` / Ansible | `retain` | Active rendering envelope consumed by dnsmasq reconcile planner |
| `nctl.render.hosts-intent.v1` | `nctl render hosts-intent` | Ansible inventory composer | `retain` | Active hosts-intent inventory payload for Ansible |
| `nctl.render.production.v1` | `nctl render production` | Ansible inventory composer | `retain` | Active production inventory payload for Ansible |
| `nctl.drift.v1` | `nctl drift` | `nctl reconcile` / AI Agent | `retain` | Structured desired-vs-actual drift source of truth |
| `nctl.ops.index.v1` | `nctl ops list` | `nctl ops` CLI | `retain` | On-disk index format for operation discovery |
| `legacy_dashboard_urls` | Removed | None | `remove_in_matched_rollout` | Only consumer was removed dashboard server |
| `reconciliation_status` | Removed | None | `remove_in_matched_rollout` | Only consumer was removed UI dashboard |

## 3. Evidence Artifacts Created

- `.local/test-strategy/p0/20260726T034839Z/compatibility-consumers.tsv`: Named consumer mapping for all active and historical envelopes.
- `.local/test-strategy/p0/20260726T034839Z/compatibility-decision.md`: Formal policy resolution document freezing the matched-version breaking-change policy.

## 4. Gate Summary & Handoff

- Every frozen field and event envelope has a named consumer or explicit removal decision. Policy conflict is resolved.
- Ready to proceed to Step 10: Run the unmodified baseline repeatedly and out of order (`report10.md`).
