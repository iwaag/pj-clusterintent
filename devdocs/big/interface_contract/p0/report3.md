# Phase 0 Step 3 — Capture live ownership and provenance without private prose

Parent: [plan.md](plan.md), Step 3.

Private evidence: `19_live_provenance_graphql.json`, `20_objectchange_provenance.txt`,
`21_objectchange_no_history_check.txt` (under
`.local/interface-contract/p0/20260725T122031Z/`). The GraphQL evidence file contains Braindump
`title` text (Japanese prose in 4 of 5 titles) — this is private evidence only, per plan §3.1; no
title text is reproduced below or in any tracked file. `ObjectChange` queries read only `action`,
`time`, `user_name`, `request_id`, and object IDs — never `object_data`/`object_data_v2` (the
serialized snapshot) or Braindump/review content.

## DesiredNode (5 live rows)

| Node | Lifecycle | IntentSource link | Realized Device link/source | Created |
|---|---|---|---|---|
| agbach | APPROVED | none | linked, `OVERRIDE` | 2026-06-26 |
| agdnsmasq | ACTIVE | none | linked, `OVERRIDE` | 2026-06-24 |
| aghub | APPROVED | none | linked, `DERIVED` | 2026-07-12 |
| agpc | ACTIVE | none | linked, `OVERRIDE` | 2026-06-23 |
| agstudio | ACTIVE | none | linked, `OVERRIDE` | 2026-06-23 |

All 5 have `intent_source = null`, confirming the roadmap baseline ("all five live DesiredNodes have
no IntentSource link"). Lifecycle is split 2×`APPROVED`/3×`ACTIVE`, not uniformly `planned` as the
`better_usability` field-classification memo described at an earlier point in time — lifecycle has
since been actively promoted on all 5 rows. `ObjectChange` shows all 5 have a `create` origin
authored by `user=iwaag` (not a Job/API-token identity), with the DesiredNode content type also
showing 3 additional `create`+later `delete` pairs for objects no longer live (8 total creates, 3
deletes, 309 updates across history) — i.e. the current 5 are survivors of an earlier, larger,
human-curated set. Provenance classification: `human_ui` origin (pre-dates the current read-only
initiative; consistent with "no UI writer remains after this initiative" framing — these rows were
created before nintent's UI mutation surface is removed).

## DesiredEndpoint (5 live rows)

All 5 endpoints are named `primary`, one per live DesiredNode, each realized to an `IPAddress` with
`realized_ip_address_source` of `OVERRIDE` (agbach, agpc, agstudio) or `DERIVED` (agdnsmasq, aghub).
No endpoint has a `mac_address` set. All 5 have `create`-action `ObjectChange` origins matching their
node's creation `request_id` (same human session), confirming `human_ui`/direct-creation provenance,
not `ipam_job` (the IPAM Job would show a distinct later `request_id` for the link population, which
is absent here for `realized_ip_address` — the realized link and creation happened together).

## DesiredServicePlacement (1 live row)

`dnsmasq` service placed on the `agdnsmasq` node, `assignment_source = MANUAL`, created
2026-07-20 — matches roadmap baseline exactly. **Zero `ObjectChange` rows exist for this object at
all** (confirmed via distinct-ID check, `21_objectchange_no_history_check.txt`) — its creation
predates or bypassed Nautobot's change-logging (e.g. created via `manage.py shell`/migration/fixture
rather than through the UI or REST, both of which are logged). Provenance: `unknown` — no audit
trail proves the writer. Carried to Step 5/Step 6 for a user decision if disposition depends on it.

## IntentSource (2 live rows)

- `Infrastructure` (`ff4a9a71-...`): one `ObjectChange` `create` row, `user=iwaag`,
  2026-07-24T15:05:27Z, `request_id=4aa1d25f-...` — the same `request_id` that created all 5
  `DesiredService` rows in the same instant, i.e. this IntentSource and its services were created
  together in one write. Provenance: `human_ui` or a script acting under the same user session
  (ObjectChange does not distinguish UI form submission from `manage.py shell`/Django admin under
  the same authenticated user — both log `user_name=iwaag` identically). Given the single
  transaction-like `request_id` covering 6 objects, `human_ui`/interactive-session origin is the
  best-supported classification but cannot be narrowed further from bounded metadata alone.
- `Manual` (`a55f0db1-...`): **zero `ObjectChange` rows** — provenance `unknown`, predates audit
  logging entirely (older than the `Infrastructure` source and every current `DesiredNode`'s
  earliest `ObjectChange`, 2026-06-22).

## DesiredService (6 live rows)

5 of 6 (`grafana`, `haos`, `nomad`, `prometheus`, `prometheus-node-exporter`) were created in the
same `request_id=4aa1d25f-...` transaction as the `Infrastructure` IntentSource
(2026-07-24T15:05:27Z) — all link `intent_source = Infrastructure`. The 6th, `dnsmasq`, links
`intent_source = Manual` and has only an `update` `ObjectChange` (2026-07-20), no `create` row in
the retained history (44 total `ObjectChange` rows for this content type, 5 creates + 39 updates —
`dnsmasq`'s own create predates the earliest retained `ObjectChange` or was not logged).
Provenance: 5 are `human_ui`/session origin under `Infrastructure`; `dnsmasq` is `unknown` creation
provenance but is the service the one live `DesiredServicePlacement` references.

## BrainDumpDocument (5 live) and AlignmentReview (5 live)

All 5 Braindumps: `authorship = USER_DIRECT` (matches roadmap baseline), all have a `create`
`ObjectChange` origin authored by `user=iwaag`. All 5 AlignmentReviews: one-to-one with a Braindump
(`braindump` FK non-null for all 5, confirmed via GraphQL), all have `create` origins. Per plan
§3, no title/body/summary text was read into any tracked artifact — only ID, authorship, presence,
and timestamps.

## Provenance classification summary

| Model | Live rows | Origin classification |
|---|---:|---|
| IntentSource | 2 | 1 `human_ui`/session (with linked DesiredServices), 1 `unknown` (pre-audit-log) |
| DesiredNode | 5 | `human_ui`, all pre-existing UI-writer era |
| DesiredEndpoint | 5 | `human_ui`, created alongside their node |
| DesiredService | 6 | 5 `human_ui`/session (Infrastructure), 1 `unknown` (dnsmasq/Manual) |
| DesiredServicePlacement | 1 | `unknown` — no ObjectChange history at all |
| BrainDumpDocument | 5 | `human_ui` via nctl/agent transcription (`authorship=USER_DIRECT`) |
| AlignmentReview | 5 | `human_ui` via nctl/agent, one-to-one with Braindump |

## Gate

Every live structural row across the 7 audited models has either evidence-backed provenance or an
explicit `unknown` classification (IntentSource "Manual", DesiredService "dnsmasq",
DesiredServicePlacement "dnsmasq placement" — all three are the same pre-audit-log cluster tied
together by the one live placement). No Braindump body, Alignment Review summary, or other private
prose was read into any tracked file. Proceeding to Step 4.
