# Test Strategy Phase 0 Step 1 Report — Reconstruct Current Installed and Migration State

Parent: [plan.md](plan.md) — Step 1.

Status: **partially complete** (Step 1 complete: live Nautobot processes, installed packages, applied migrations, compute counts, VM seed status, Job registrations, and process consistency verified; overall Phase 0 in progress).

## 1. Live Nautobot Process & Container Health

| Container Name | State / Health | Image Name & SHA Digest |
|---|---|---|
| `nautobot-nautobot-1` | `running / healthy` | `nautobot-nautobot` (`sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`) |
| `nautobot-nautobot-worker-1` | `running / healthy` | `nautobot-nautobot-worker` (`sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`) |
| `nautobot-nautobot-scheduler-1` | `running / healthy` | `nautobot-nautobot-scheduler` (`sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`) |

All three processes (web, worker, scheduler) share the exact same underlying image digest (`sha256:a4c20f6a...`). No mixed-process image mismatch was observed.

## 2. Installed Package & Migration State

- **Nautobot Version**: `3.1.3`
- **Django Version**: `5.2.14`
- **Installed `nintent` Package**: Version `0.9.0` (installed at `/opt/nautobot/.local/lib/python3.12/site-packages/nautobot_intent_catalog`)
- **Applied `nintent` Migrations**:
  - `0015_compute_platform_instance_and_endpoint_mac`: Applied (`[X]`)
  - `0016_remove_reconciliation_dashboard_surfaces`: Applied (`[X]`)
  - All 16 `nautobot_intent_catalog` migrations are fully applied.

## 3. Read-Only Compute Object Counts & Inertness Verification

Read-only inspection of the live Nautobot database via Django ORM:

- `DesiredComputePlatform.objects.count()`: **`0`**
- `DesiredComputeInstance.objects.count()`: **`0`**

### VM Seed & Cutover State Evaluation

- The latest VM Phase 3 report ([devdocs/big/vm/p3/report3.7.md](file:///Users/eiji/projects/pj-clusterintent/devdocs/big/vm/p3/report3.7.md)) confirms completion of pre-cutover Step 7.
- Compute desired-state rows remain completely **unseeded and inert** (0 instances, 0 platforms).
- No compute actuation or VM realization has been initiated.

## 4. Current Job Registration Inventory

Querying `nautobot.extras.models.Job` in the live Nautobot instance:

### Installed & Active Jobs (`installed=True, enabled=True`)

- `nautobot_intent_catalog.jobs`:
  - `Analyze Intent Sources` (`AnalyzeIntentSources`)
  - `Import Intent Sources` (`ImportIntentSources`)
  - `Reconcile Desired IPAM Intent` (`ReconcileDesiredIPAMIntentJob`)
- `main.jobs`:
  - `Ingest Nodeutils Inventory` (`main.jobs.ingest_nodeutils_inventory`)
  - `Seed Home Cluster` (`main.jobs.seed_home_cluster`)
  - `AI Resource Review` (`main.jobs.ai_resource_review`)

### Superseded / Inert Jobs (`installed=False, enabled=True`)

The following historical/removed jobs remain registered in DB but are uninstalled (`installed=False`):
- `Generate Desired Services`, `Service Placement Review`, `Evaluate Endpoint Intent`, `Evaluate Node Intent`, `Evaluate Service Intent`, `Export Ansible Hosts Intent`, `Export Production Inventory`, `Export dnsmasq Records`, `Preview Intent Source Analysis`, `Sync Deployment Profiles`.

## 5. Process & Repository Mismatch Evaluation

- **Submodule HEAD Revisions**:
  - `nintent`: `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`
  - `nauto`: `1c78af8bdbfc69cafdc293b4082f866de9f271b0`
- **Installed State in Docker**:
  - Container environment uses `nintent 0.9.0` (matching post-`interface_contract` Phase 4 and `vm` Phase 3 cutover baseline).
  - Web, worker, and scheduler share identical code and container image digests.

## 6. Gate Summary & Handoff

- Repository vs. installed tuples are explicitly recorded and distinguishable.
- Migration state (`0015` and `0016`) is verified applied.
- Compute state is proven unseeded (0 platforms, 0 instances) and inert.
- Ready to proceed to Step 2: Collect every suite in its owning environment (`report2.md`).
