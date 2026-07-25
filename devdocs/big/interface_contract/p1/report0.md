# Phase 1 Step 0 — Recapture the boundary and establish evidence

Parent: [plan.md](plan.md), Step 0.

Evidence: `.local/interface-contract/p1/20260725T134918Z/` (directory mode `0700`, files mode
`0600`), 5 files (`00_summary.txt`, `desired_snapshot.json`, `job_results_check.json`,
`required_searches.txt`).

## 1. Repository revisions and dirty state

All six repositories clean and at exactly the revision tuple recorded in plan.md Section 2.4:

| Repository | Revision |
|---|---|
| superproject | `e18c983648d50ee3eaa3650fa596d9adefc6996d` |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` |

Tool versions: Python `3.14.2`, Docker `29.4.0`, Docker Compose `5.0.1`.

## 2. Baseline test counts

`nintent`: 187 tests, `OK` (`python3 -m unittest discover -s nautobot_intent_catalog/tests`).
`nauto`: 110 tests, `OK` (`python3 -m unittest discover -s tests`).

## 3. Checked-in seed YAML digests (pre-Phase-1)

`nauto/seed/intent_sources.yaml`:
`af7c38d1cc29c8b3037ce3f8b4405c018ab4b086456283aa5a0f03e4d54ed28d`.
`nauto/seed/home_cluster.yaml`:
`db5a40e0175d21692d68d3a487cd1b357293e1ddb5e2afb24ef5ea6a146a1614`.

## 4. Fresh read-only live confirmation

A fresh read-only GraphQL query (not a re-read of Phase 0's evidence) confirms live structural
counts match the Phase 0 disposition and plan.md Section 4.2 exactly: 5 `desired_nodes` (agbach,
agdnsmasq, aghub, agpc, agstudio), 5 `desired_endpoints`, 3 `desired_ip_ranges`
(dhcp-reserved/network-infra/dhcp-unreserved), 2 `intent_sources` (infrastructure, manual), 6
`desired_services` (prometheus, grafana, nomad, prometheus-node-exporter, haos, dnsmasq), 1
`desired_service_placements` (dnsmasq on agdnsmasq), 0
`desired_node_operational_overrides`. `agbach`/`aghub` lifecycle is `APPROVED`;
`agdnsmasq`/`agpc`/`agstudio` lifecycle is `ACTIVE` — matches plan.md Section 4.3. No
identity/ownership-relevant field has changed since Phase 0 (2026-07-25T12:20–12:53Z); no new
disposition decision is required.

## 5. Job status check

330 total `job-results`; the 5 most recent (`AI Resource Review` ×2, `Ingest Nodeutils
Inventory` ×3) all report `status=SUCCESS`. No Import/Analyze/Seed/Generate Job pending or
running; none started during this step.

## 6. Required searches

Re-ran the roadmap/plan's mandatory 21-term search across `nintent/` and `nauto/` (`.py`,
`.yaml`, `.md`). Match counts: `PreviewIntentSourceAnalysis`=3, `Preview Intent Source
Analysis`=2, `GenerateDesiredServices`=5, `Generate Desired Services`=3,
`generate_desired_services`=12, `service_repositories`=18, `service_repositories.yaml`=6,
`desired_services.generated.yaml`=3, `disable_missing`=7, `intent-import-preview.json`=1,
`intent-import-apply.json`=1, `preview = BooleanVar`=2, `ensure_intent_sources`=2,
`ensure_desired_services`=2, `IntentSource`=119, `DesiredService`=179,
`transaction.set_rollback`=3, `create_file`=3, `last_import_status`=7, `last_analyzed_at`=7,
`dependencies_deleted`=2, `desired_node_operational_configs`=6. All matches are consistent with
Phase 0's classification — every still-active occurrence is exactly the Phase 1
removal/refactor target set (plan.md Section 9.2).

## 7. Disposable environment design (for Step 8)

Not built yet. Per `.local/localenv_memo.md`, the live dev stack installs nintent via `pip
install git+https://...` in `devenv/nautobot/Dockerfile`, so it cannot be reused for the
disposable proof; Step 8 requires a separate compose file with a new project prefix, a new
PostgreSQL container/database/volume, a new Redis container/volume, no bind/network reference to
`my_postgres_db` / `service_scripts-redis-1` / port 8000 / live media, and a mount of the exact
local `nintent`/`nauto` source under test.

## Gate

Satisfied: one clean, matching revision tuple; the confirmed YAML proposal target (plan Section
4.2) matches fresh read-only live evidence exactly; no disposable resource exists yet, so no
live-database reachability risk. No Import/Analyze/Seed/Generate Job is pending or running; none
was started. Proceeding to Step 1.
