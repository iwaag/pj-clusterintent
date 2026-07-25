# Phase 0 Step 6 — Resolve ownership and desired-presence decisions

Parent: [plan.md](plan.md), Step 6.

Consolidated every `unresolved` identity from Step 4 and Step 5 into one decision set and asked the
user via `AskUserQuestion` (2026-07-25, same session as Steps 0–5). No live, desired, actual, or
YAML mutation occurred while waiting for or recording these answers.

## Decision 1 — 6 checked-in-only nodes (`agmbp2019`, `agmbp2018`, `agprometheus`, `aggrafana`,
`agnomad`, `aghaos`) and their checked-in placements/overrides

**User decision:** "they are outdated legacy. just delete it and go on." (2026-07-25, decision
authority: repository owner, interactive session).

**Disposition:** `stale_seed`. These 6 node declarations, their 6 associated
`desired_service_placements` rows (prometheus/grafana/nomad×2/prometheus-node-exporter/haos), and
their `desired_node_operational_overrides` rows (`agmbp2019`, `agmbp2018`, `aghaos`, plus the
`agpc`/`agstudio`/`agbach` overrides only insofar as they reference these stale nodes — see Decision
3 for the 3 overlap nodes themselves, which are *not* stale) are to be **omitted** from the Phase 1
canonical YAML proposal. Per plan §6/§7.6, omission is edited into the checked-in
`nauto/seed/intent_sources.yaml` file itself during Phase 1 (this is a documentation-only Phase 0;
no file was edited here). No live row exists for any of the 6, so no live removal follow-up is
needed.

## Decision 2 — 2 live-only nodes (`agdnsmasq`, `aghub`), `Manual` IntentSource, `dnsmasq`
DesiredService, and the one live DesiredServicePlacement

**User decision:** "それはbraindumpから生成された正式なintentなので引き継がれる必要があります。"
("That is official intent generated from a Braindump, so it must be carried forward.")

**Disposition:** `confirmed_live_intent`. `agdnsmasq`, `aghub`, their `primary` endpoints, the
`Manual` IntentSource, the `dnsmasq` DesiredService, and the `dnsmasq`-on-`agdnsmasq`
`DesiredServicePlacement` are all confirmed current intent, sourced from Braindump rather than the
checked-in YAML or nauto seed. Phase 1 must represent all of these in
`nauto/seed/intent_sources.yaml` so they survive the transition to YAML being the sole bulk desired-
state writer. This resolves the `unknown`-provenance gap from Step 3 (zero `ObjectChange` history on
the placement, no create-origin on `dnsmasq`/`Manual`) as a Braindump-sourced writer rather than an
unexplained origin.

## Decision 3 — Endpoint addressing scheme conflict (`agbach`, `agpc`, `agstudio`)

**User decision:** "それも正式なintentなので引き継がれるべきです。mdns=.localとdns=home.arpaという、
このクラスターの基幹方針通りなんですが、home.arpa自体は今回削除されるquick add nodeのデフォルト値
なだけで、braindumpには言及されていないかもしれません。本体はbraindumpに書かれているべき情報です
が、今回の作業範囲外の問題のはず。" ("That's also official intent and should be carried forward.
mdns=.local and dns=home.arpa follow this cluster's core policy, but `home.arpa` itself is just the
default value from the Quick Add node feature being deleted in this initiative, and may not be
explicitly stated in the Braindump. The underlying information should live in the Braindump, but
that gap is out of this work's scope.")

**Disposition:** `confirmed_live_intent`. The live `dns_name = agX.home.arpa` +
`OVERRIDE`-sourced static-IP scheme is the confirmed current addressing intent for `agbach`, `agpc`,
and `agstudio`. Phase 1 must update these 3 nodes' checked-in endpoint rows to match live (`dns_name`
instead of `mdns_name`, drop `ip_policy: external` in favor of the live static-IP/OVERRIDE shape),
treating the current `mdns_name`/`external` checked-in rows as `stale_seed`. The user explicitly
flagged a separate, out-of-scope gap: the `home.arpa` convention itself traces to the (deleted)
Quick Add form's default rather than to an explicit Braindump statement — noted here for the record,
not actioned in this initiative.

## Decision 4 — 3 live-only DesiredIPRanges (`dhcp-reserved`, `network-infra`, `dhcp-unreserved`)

**User decision:** "それもbraindumpから作られた正式なintentなので引き継がれる必要があります。"
("That is also official intent created from a Braindump, so it must be carried forward.")

**Disposition:** `confirmed_live_intent`. Phase 1 must add a `desired_ip_ranges` root to
`nauto/seed/intent_sources.yaml` capturing all 3 live ranges with their current names and
start/end addresses.

## Decision 5 — Off-repository caller attestation

**User decision:** "No external caller exists" (selected the recommended option).

**Attestation recorded:** no client outside `nctl` and nintent's own UI/REST calls the four REST
collections scheduled for deletion (`services`, `endpoints`, `compute-platforms`,
`compute-instances`) or any nintent UI mutation route (add/edit/delete, Quick Host Add, Source
YAML). This closes plan §5.3's requirement ("the audit cannot prove the absence of an unknown
external client... the report must... record the user's external-caller attestation") for every
surface Step 1 identified as having no in-repository caller.

## Consolidated disposition table

| Identity | Disposition | Phase 1 action |
|---|---|---|
| `agmbp2019`, `agmbp2018`, `agprometheus`, `aggrafana`, `agnomad`, `aghaos` (nodes) + their 6 placements + their overrides | `stale_seed` | Remove from checked-in `intent_sources.yaml` |
| `agdnsmasq`, `aghub` (nodes) + endpoints | `confirmed_live_intent` | Add to checked-in `intent_sources.yaml` |
| `Manual` IntentSource | `confirmed_live_intent` | Add to checked-in `intent_sources.yaml` |
| `dnsmasq` DesiredService | `confirmed_live_intent` | Add to checked-in `intent_sources.yaml` |
| `dnsmasq`-on-`agdnsmasq` DesiredServicePlacement | `confirmed_live_intent` | Add to checked-in `intent_sources.yaml` |
| `agbach`/`agpc`/`agstudio` endpoint `dns_name`/static-IP fields | `confirmed_live_intent` | Update checked-in endpoint rows to match live; treat existing `mdns_name`/`external` rows as `stale_seed` |
| `Infrastructure` IntentSource + 5 services (Step 5) | `confirmed_checked_in_intent` | Move from `home_cluster.yaml` into `intent_sources.yaml` (unchanged from Step 5, no new decision needed) |
| `dhcp-reserved`, `network-infra`, `dhcp-unreserved` (DesiredIPRange) | `confirmed_live_intent` | Add new `desired_ip_ranges` root to checked-in `intent_sources.yaml` |
| Off-repository REST/UI callers | attested absent | No adjustment to the deletion candidate list |

## Gate

No unresolved desired-presence or caller question remains: every identity from Steps 4–5 has a
recorded disposition and decision authority (the repository owner, interactive session,
2026-07-25), and the external-caller attestation is recorded. Proceeding to Step 7.
