# Phase 1 Step 2 — Build the canonical YAML proposal

Parent: [plan.md](plan.md), Step 2.

## 1. Content source

Every field was transcribed from the fresh read-only GraphQL query captured in Step 0
(`.local/interface-contract/p1/20260725T134918Z/desired_snapshot.json`) — the live-confirmed
Phase 0 disposition, not display labels or Quick-Host-Add defaults.

## 2. `nauto/seed/intent_sources.yaml` rewrite

- Moved `Infrastructure` (slug `infrastructure`) and its 5 `desired_services`
  (`prometheus`/`grafana`/`nomad`/`prometheus-node-exporter`/`haos`) from `home_cluster.yaml`
  unchanged.
- Added `Manual` (slug `manual`) intent source and the `dnsmasq` `desired_services` entry,
  transcribed from the live model fields (`slug: dnsmasq`, `display_name: dnsmasq`,
  `lifecycle: active`).
- Replaced the 9 stale checked-in `desired_nodes` with the 5 confirmed nodes: `agbach`
  (`node_type: device`, `accepted_actual_types: [device]`, `lifecycle: approved`), `agdnsmasq`
  (`node_type: service_host`, `accepted_actual_types: [device, virtual_machine]`,
  `lifecycle: active`), `aghub` (`device`, `[device]`, `approved`), `agpc` (`device`, `[]`,
  `active`), `agstudio` (`device`, `[]`, `active`) — `accepted_actual_types` transcribed exactly
  as observed live, including the two empty lists on `agpc`/`agstudio`.
- Replaced the 9 stale `desired_endpoints` with the 5 confirmed primary endpoints, each with its
  explicit `ip_policy` (`dhcp_reserved` ×4, `static` for `agdnsmasq`), explicit `ip_address`,
  explicit `dns_name`/`mdns_name` (the `<slug>.home.arpa`/`<slug>.local` pattern, matching live
  exactly), `generate_dnsmasq: true`, `dnsmasq_record_type: host_record`.
- Added a new `desired_ip_ranges` root with the 3 confirmed ranges (`dhcp-reserved`,
  `network-infra`, `dhcp-unreserved`), transcribing `start_address`/`end_address`/`range_policy`/
  `lifecycle`/`generate_dnsmasq`/`dnsmasq_options` exactly.
- Removed all 6 stale `desired_service_placements` and added only the confirmed `dnsmasq` on
  `agdnsmasq` placement (`assignment_source: manual`, `config: {listen_addresses:
  [192.168.0.2]}`, no `desired_endpoint` reference — matches the live row, which also has none).
- Removed all 6 stale `desired_node_operational_overrides`; declared the root as `[]` per Phase 0
  Decision (0 confirmed live overrides).
- Declared both compute roots as `[]`.
- Declared all 9 canonical roots explicitly, in the plan's canonical order.

## 3. `nauto/seed/home_cluster.yaml` edit

Removed the `intent_sources`/`desired_services` blocks (now owned solely by
`intent_sources.yaml`); every native-Nautobot-prerequisite section (`location_types`,
`locations`, `statuses`, `roles`, `cluster_types`, `manufacturers`, `device_types`, `tags`,
`custom_fields`) is unchanged.

## 4. Verification

- `python3 -m unittest discover -s nautobot_intent_catalog/tests` (nintent):
  `CanonicalFileIdentityCountTests.test_canonical_checked_in_file_matches_exact_confirmed_counts`
  now **passes** — the checked-in file loads with zero errors and matches the exact Phase 0
  identity set. The only remaining pre-existing failures are the Step 3 (unknown-root rejection)
  and Step 4 (ownership-split function) targets — unaffected by this step's YAML-only change. 209
  tests, 1 failure + 4 errors (down from 2 failures + 4 errors after Step 1).
- `python3 -m unittest discover -s tests` (nauto): 110 tests, `OK` — the `home_cluster.yaml`
  edit does not break any nauto seed test (`SeedHomeCluster`'s `IntentSource`/`DesiredService`
  removal is Step 6's job-code change, not yet applied; the seed loader itself does not
  currently assert on the removed blocks' presence).

New digests: `nauto/seed/intent_sources.yaml`
`598391e02041c433df468629cc86d2a2c948c94b80f89a1746a28057b557455b`;
`nauto/seed/home_cluster.yaml`
`a72361b0b4e305fbe584b8d6e5822cb363d1c84008261547ea13836ab26ebc55`.

## Gate

Satisfied: the proposal is strict, contains exactly the confirmed Phase 0 identity set, contains
no realized IDs or source fields, and has no stale-node reference (`CanonicalFileIdentityCountTests`
explicitly asserts none of the 6 stale slugs remain). Proceeding to Step 3.
