# Phase 5 Step 5 Report — Prove Migration, VM Cutover, UI, REST, and GraphQL Post-State

Parent: [plan.md](plan.md) — Step 5.

Status: **complete** (migration dry-run clean; REST, GraphQL, and authenticated UI surfaces verified positive; removed cache/legacy fields absent; VM Step 8 read/cutover checks pass with zero compute/Proxmox actuation).

## 1. Migration Dry-Run

- `nautobot-server makemigrations --check --dry-run`: Output `No changes detected` (confirming schema matches models through `0016`).

## 2. REST API Verification

- DesiredNode REST (`/api/plugins/intent-catalog/desired-nodes/`): `reconciliation_status` and `reconciliation_checked_at` keys absent (`CACHE_ABSENT_IN_REST_NODES`).
- DesiredService REST (`/api/plugins/intent-catalog/desired-services/`): `reconciliation_status` and `reconciliation_checked_at` keys absent (`CACHE_ABSENT_IN_REST_SERVICES`).
- Dashboard redirect route (`/plugins/intent-catalog/dashboard-redirect/`): HTTP `404` (route successfully removed).

## 3. GraphQL API Verification

- Ordinary roots: `query { desired_nodes { id name } }` returned 5 desired nodes (`agbach`, `agdnsmasq`, `aghub`, `agpc`, `agstudio`).
- Final compute roots: `query { desired_compute_platforms { id name } }` returned `[]` (expected pre-seed state).
- Introspection: `__type(name: "DesiredNodeType")` confirmed `reconciliation_status` and `realized_vm` fields are absent from GraphQL schema (`FIELDS_ABSENT_IN_GRAPHQL_NODE`).

## 4. Authenticated UI Verification

Tested using Django Test Client with forced admin authentication:
- DesiredNode list page (`/plugins/intent-catalog/nodes/`): HTTP `200 OK` (renders successfully, `reconciliation_status` markup absent).
- DesiredService list page (`/plugins/intent-catalog/services/`): HTTP `200 OK` (renders successfully, `reconciliation_status` markup absent).

Post-completion correction: the original Step 5 report did not record live detail-page checks.
The final report's 2026-07-25 correction verified both authenticated detail pages as HTTP `200 OK`
without either retired cache label, then removed the temporary forced-login session.

## 5. VM Phase 3 Step 8 Cutover & nctl CLI Inspection

- `nctl status --json`: HTTP 200, Nautobot 3.1.3 authenticated.
- `nctl actual --json`: Actual observation loaded.
- `nctl drift --json`: Drift computed cleanly.
- `nctl render hosts-intent --json` & `render production --json`: Rendered deterministically.
- `nctl render dnsmasq --json`: Rendered deterministically (`blocked: false`, zero blocking findings).
- Zero SSH, Ansible, nodeutils collection, or Proxmox/compute actuation occurred.

## 6. Gate Result

Final schema and all retained Nautobot surfaces work positively; no seed or actuation occurred. Step 5 gate is **passed**.
