# Phase 0 Step 4 — Reconcile live nodes/endpoints with the checked-in YAML

Parent: [plan.md](plan.md), Step 4.

Private evidence: `22_live_ip_ranges.json`; also reuses `19_live_provenance_graphql.json` (Step 3)
and the checked-in `nauto/seed/intent_sources.yaml` (tracked, read directly, no evidence copy
needed).

## Method

Parsed `nauto/seed/intent_sources.yaml` (the current loader's 9-root contract; see Step 2 for the
loader's alias-rejection/unknown-root behavior) and independently re-read it as plain YAML. Compared
the union of live (Step 3) and checked-in `desired_nodes`/`desired_endpoints`/
`desired_ip_ranges`/`desired_service_placements`/`desired_node_operational_overrides` identities.
`desired_compute_platforms`/`desired_compute_instances` are absent from both live (0/0, Step 2) and
checked-in (root omitted) — no comparison needed, nothing to lose.

## DesiredNode identity union (9 checked-in ∪ 5 live = 11 distinct identities)

| Node (slug) | Live? | Checked-in? | Disposition | Evidence |
|---|---|---|---|---|
| `agbach` | yes | yes | overlap — see field note below | both sources |
| `agpc` | yes | yes | overlap — see field note below | both sources |
| `agstudio` | yes | yes | overlap — see field note below | both sources |
| `agdnsmasq` | yes | no | `unresolved` | live-only; carries the one live `DesiredServicePlacement` (dnsmasq) |
| `aghub` | yes | no | `unresolved` | live-only |
| `agmbp2019` | no | yes | `unresolved` | checked-in-only; has a `desired_node_operational_overrides` row (`power_control: wol`, `is_laptop: true`) |
| `agmbp2018` | no | yes | `unresolved` | checked-in-only; same override shape |
| `agprometheus` | no | yes | `unresolved` | checked-in-only; referenced by a checked-in `desired_service_placements` row (prometheus) |
| `aggrafana` | no | yes | `unresolved` | checked-in-only; referenced by a checked-in placement (grafana) |
| `agnomad` | no | yes | `unresolved` | checked-in-only; referenced by two checked-in placements (nomad server) |
| `aghaos` | no | yes | `unresolved` | checked-in-only; referenced by a checked-in placement (haos) + override (`declared_host_os: haos`, `ansible_port: 2222`) |

No node identity has enough evidence on its own to auto-classify as `confirmed_live_intent`,
`confirmed_checked_in_intent`, or `stale_seed` per plan §7 ("presence in both locations does not
prove field agreement," "a checked-in-only row is not automatically desired," "a live-only row is
not automatically stale"). All 8 non-overlap identities are `unresolved` pending Step 6.

### Field comparison for the 3 overlapping nodes (agbach, agpc, agstudio)

| Field | Live | Checked-in YAML | Note |
|---|---|---|---|
| `lifecycle` | `APPROVED` (agbach) / `ACTIVE` (agpc, agstudio) | `active` for all 3 | Not a conflict needing resolution: per roadmap §"Operational fields have one writer" and plan §6.4, an *existing* node's lifecycle is nctl-`lifecycle`-owned and YAML only sets it on create; re-import must not overwrite it. No disposition needed for this field. |
| endpoint `dns_name`/`mdns_name` | live: `dns_name = agbach.home.arpa` / `agpc.home.arpa` / `agstudio.home.arpa`, no `mdns_name` | checked-in: `mdns_name = agbach.local` / `agpc.local` / `agstudio.local`, no `dns_name`, `ip_policy: external` | Genuine content mismatch — different naming/addressing scheme entirely. |
| endpoint `ip_address` / realized IP | live: static `192.168.0.120`/`.110`/`.100`, `realized_ip_address_source = OVERRIDE` | checked-in: no `ip_address`, `ip_policy: external` (expects externally-supplied addressing, not a YAML-declared static IP) | Genuine content mismatch. |

The live `agX.home.arpa` DNS scheme with `OVERRIDE`-sourced static IPs is uniform across **all 5**
live nodes (Step 3), including the 2 live-only nodes not in the checked-in file at all — this is
the current, actively-converged addressing convention. The checked-in file's `mdns_name`+`external`
scheme appears in **zero** live endpoints. Proposed classification (evidence-supported, not final):
`stale_seed` for the checked-in endpoint identity/addressing fields of `agbach`/`agpc`/`agstudio` —
i.e. the live endpoint config should be treated as the confirmed current intent and the checked-in
`mdns_name`/`ip_policy: external` rows as superseded by an earlier addressing generation. This
proposal is carried to Step 6 for explicit user confirmation, not auto-applied.

## DesiredEndpoint identity union

Compound identity (per plan §6.1, `(desired_node, name)`) for the 3 overlapping nodes matches
(`name = primary` on both sides). No additional endpoint identities beyond the node union above —
every checked-in endpoint has exactly one checked-in node parent and vice versa, and the 2 live-only
nodes' endpoints have no checked-in counterpart (covered by the node-level `unresolved` rows above).

## DesiredIPRange (3 live, 0 checked-in)

| Name | Range | Disposition |
|---|---|---|
| `dhcp-reserved` | 192.168.0.10–199 | `unresolved` — live-only, `desired_ip_ranges` root entirely absent from checked-in file (omission, not rejection — the loader accepts an absent root as no-op) |
| `network-infra` | 192.168.0.2–9 | `unresolved` — live-only |
| `dhcp-unreserved` | 192.168.0.200–250 | `unresolved` — live-only |

Per plan §7 rule 6 ("Include IP ranges, placements, operational overrides, and pending compute rows
so that Phase 1 cannot accidentally omit a confirmed structural row"), these 3 ranges must not be
silently dropped from the Phase 1 YAML proposal. Carried to Step 6.

## DesiredServicePlacement (1 live, 6 checked-in)

The one live placement (`dnsmasq` on `agdnsmasq`, `assignment_source=MANUAL`, no `ObjectChange`
history per Step 3) has no checked-in counterpart — `agdnsmasq` is not a checked-in node at all.
The 6 checked-in placements (prometheus/grafana/nomad×2/prometheus-node-exporter/haos) reference 5
of the 6 checked-in-only-or-overlap nodes (`agprometheus`, `aggrafana`, `agnomad`, `agstudio`,
`agpc`, `aghaos`) — none of these 6 placements have a live counterpart. All 7 identities are
`unresolved`, tied to their parent node's disposition in Step 6.

## DesiredNodeOperationalOverride (0 live, 6 checked-in)

All 6 checked-in overrides (`agmbp2019`, `agmbp2018`, `agpc`, `agstudio`, `agbach`, `aghaos`) are
checked-in-only — 0 live rows exist at all (Step 2 GraphQL count). Tied to their parent node's
Step 6 disposition; the `agpc`/`agstudio`/`agbach` overrides specifically apply to the 3 overlap
nodes discussed above and would take effect on next YAML apply regardless of the endpoint dispute,
since operational overrides are a separate root with no live conflict (0 live rows to conflict
with).

## Gate

Every node, endpoint, IP range, placement, and override identity from the live/checked-in union has
either a disposition (the lifecycle non-conflict, resolved by existing field-ownership rules) or is
explicitly listed as `unresolved` for Step 6. No identity was silently dropped. Proceeding to Step 5
before consolidating all `unresolved` items into one Step 6 user-decision table.
