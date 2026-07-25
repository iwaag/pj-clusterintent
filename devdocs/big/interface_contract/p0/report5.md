# Phase 0 Step 5 — Reconcile IntentSources and DesiredServices

Parent: [plan.md](plan.md), Step 5.

No new live queries were needed; this step reconciles the live data already captured in Step 3
(`19_live_provenance_graphql.json`, `20_objectchange_provenance.txt`) against
`nauto/seed/home_cluster.yaml`, `nauto/seed/intent_sources.yaml`, and
`nauto/seed/service_repositories.yaml` (all read directly from the tracked worktree; no evidence
copy needed). Analyze/Generate Desired Services were **not** run, per plan §7 rule 7.

## IntentSource reconciliation

| IntentSource | Live? | `home_cluster.yaml`? | `intent_sources.yaml`? | Disposition |
|---|---|---|---|---|
| `Infrastructure` (`infrastructure`) | yes | yes (`intent_sources:` block, line 497) | no (root is `[]`) | `confirmed_checked_in_intent` — content matches exactly (slug, name, `source_type: manual`, `enabled: true`); its live `ObjectChange` `request_id` (`4aa1d25f-...`) is the same transaction that created its 5 `DesiredService` children, consistent with a `Seed Home Cluster` run against this exact file |
| `Manual` (`manual`) | yes | no | no | `unresolved` — appears in neither checked-in source; zero `ObjectChange` history (Step 3); only linked live object is the `dnsmasq` `DesiredService` |

## DesiredService reconciliation (canonical identity: `intent_source` + `catalog_namespace` +
`catalog_metadata_name` + `service_type`)

| Service | Live? | `home_cluster.yaml`? | `intent_sources.yaml` placements reference it? | Disposition |
|---|---|---|---|---|
| `prometheus` (Infrastructure) | yes | yes, exact field match (`display_name`, `lifecycle: active`) | yes (placement `desired_service.catalog_metadata_name: prometheus`) | `confirmed_checked_in_intent` |
| `grafana` (Infrastructure) | yes | yes, exact match | yes | `confirmed_checked_in_intent` |
| `nomad` (Infrastructure) | yes | yes, exact match | yes (×2 placements: server + client-agstudio) | `confirmed_checked_in_intent` |
| `prometheus-node-exporter` (Infrastructure) | yes | yes, exact match | yes | `confirmed_checked_in_intent` |
| `haos` (Infrastructure) | yes | yes, exact match | yes | `confirmed_checked_in_intent` |
| `dnsmasq` (Manual) | yes | no | no | `unresolved` — only `update`-action `ObjectChange` on record (Step 3), no `create` row, `intent_source=Manual` which is itself unresolved |

All 5 `Infrastructure`-sourced services match their `home_cluster.yaml` declaration field-for-field
(name, display_name, lifecycle) and are each referenced by a checked-in `desired_service_placements`
row in `intent_sources.yaml` naming the same `catalog_metadata_name` — strong, consistent evidence
across two independent checked-in files plus live `ObjectChange` timing. `dnsmasq` remains the one
loose end tied to the same unresolved `Manual`/placement cluster identified in Steps 3–4.

## DesiredDependency

0 live rows (Step 2 GraphQL count), no checked-in root exists (`desired_dependencies` is not one of
the plan's 9 canonical roots — it is `analysis`-owned per roadmap §"Operational fields have one
writer": "Source-derived service metadata and dependencies" belongs to the `Analyze Intent Sources`
Job, not YAML). Nothing to reconcile.

## Writer attribution (bounded `ObjectChange` metadata only, per Step 3)

The `Infrastructure` IntentSource and its 5 services share one `ObjectChange` `request_id`
(`4aa1d25f-ae2f-426a-bd77-4d159f4044cf`, 2026-07-24T15:05:27Z, `user_name=iwaag`). Bounded metadata
cannot distinguish a `Seed Home Cluster` Job run (which runs as the authenticated user who triggered
it) from a manual `manage.py shell`/UI action under the same account — but the fact that all 6
objects share one transaction-scale timestamp and exactly reproduce `home_cluster.yaml`'s content is
the strongest available evidence, and matches `Seed Home Cluster`'s known current behavior
(`jobs/seed_home_cluster.py:314-396`, confirmed in Step 1) of creating exactly this shape from
exactly this file. Classified as `nauto_seed` origin.

## `service_repositories.yaml` / `desired_services.generated.yaml`

`nauto/seed/service_repositories.yaml` declares one repository (`agservice-storage`) under the
`service_repositories:` root, which the current strict loader explicitly rejects (Step 2). No live
`DesiredService` corresponds to this repository (no live service named anything storage-related).
`desired_services.generated.yaml` does not exist on disk. Neither file has any live-state
consequence — both are already-scheduled-for-deletion nauto artifacts (Step 1) with zero live
services depending on them; no disposition decision is needed for either file itself, only for the
Job that reads them (`GenerateDesiredServices`, already classified `dead_reference`/deletion
candidate in Step 1).

## Which declarations must move to canonical YAML in Phase 1

Per roadmap §4 ("Move the `infrastructure` IntentSource and its five DesiredService declarations out
of `home_cluster.yaml` and into [`intent_sources.yaml`]"): the `Infrastructure` IntentSource block
and its 5 `desired_services` entries currently in `home_cluster.yaml` (lines 497–536) are the
confirmed content to relocate into `nauto/seed/intent_sources.yaml`'s currently-empty
`intent_sources: []` root and a new `desired_services:` root in Phase 1. This is evidence-backed,
not a Step 6 open question — the checked-in `home_cluster.yaml` and live state agree exactly.

## Gate

Every live and checked-in IntentSource/DesiredService identity has a disposition
(`confirmed_checked_in_intent` ×6, `unresolved` ×2 tied to the same `Manual`/`dnsmasq` cluster
already flagged in Steps 3–4) or is out of scope (`DesiredDependency`, the two nauto-owned files).
Field ownership is explicit: source-derived fields (`display_name`, `catalog_*`) come from
`home_cluster.yaml`/analysis; no operator-owned lifecycle/requirements/notes exist yet on any live
service to separate. Proceeding to Step 6 to consolidate all `unresolved` items from Steps 4 and 5
into one user-decision table.
