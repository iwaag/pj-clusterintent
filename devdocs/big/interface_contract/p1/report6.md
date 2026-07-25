# Phase 1 Step 6 — Remove nauto's duplicate writers

Parent: [plan.md](plan.md), Step 6.

## 1. `SeedHomeCluster` contraction

`nauto/jobs/seed_home_cluster.py`:

- Removed `from nautobot_intent_catalog.models import DesiredService, IntentSource` and its
  `ImportError` fallback (`DesiredService = None` / `IntentSource = None`).
- Removed `ensure_intent_sources()` and `ensure_desired_services()` entirely, and their two
  calls from `run()`.
- `run()` now seeds only: statuses, location types, locations, roles, cluster types,
  manufacturers, device types, tags, custom fields — exactly the native-Nautobot-prerequisite
  set plan Section 7.1 retains.

`nauto/seed/home_cluster.yaml` already had its `intent_sources`/`desired_services` blocks
removed in Step 2 (moved to `intent_sources.yaml`); no further edit needed here.

Added `nauto/tests/test_seed_home_cluster_ownership.py`: a static source/data-scan contract test
(the same Django-free unit-test boundary every other nauto Job test respects — `jobs/
seed_home_cluster.py` imports `django.apps`/`django.db` unconditionally, so exercising
`SeedHomeCluster.run()` itself needs a live Nautobot test runner, out of this local suite's
scope). Asserts the Job source contains no `nautobot_intent_catalog`/`IntentSource`/
`DesiredService`/`ensure_intent_sources`/`ensure_desired_services` reference, and that
`home_cluster.yaml` declares no `intent_sources`/`desired_services` root while still declaring
the native-prerequisite roots (`locations`, `statuses`, `custom_fields`).

## 2. `GenerateDesiredServices` deletion

Deleted:

- `nauto/jobs/generate_desired_services.py`
- `nauto/tests/test_generate_desired_services.py`
- `nauto/seed/service_repositories.yaml`

`nauto/jobs/__init__.py`: removed the import, the `register_jobs()` argument, and the `__all__`
entry. Registered Home Inventory Jobs are now exactly:

```text
Seed Home Cluster
Ingest Nodeutils Inventory
AI Resource Review
```

`AIResourceReview` itself is untouched (plan Section 7.2 explicit instruction).

Current documentation references (`nauto/README.md`, one docstring citation in
`tests/test_ingest_nodeutils_inventory_job.py`) remain and are Step 9's job (documentation
pass), not this step's.

## 3. Verification

`python3 -m unittest discover -s tests`: 110 tests, `OK` (2 removed with
`test_generate_desired_services.py`, 2 added with the new ownership test — net unchanged).
`python3 -m py_compile jobs/seed_home_cluster.py jobs/__init__.py`: clean. `ls jobs/ seed/`
confirms `generate_desired_services.py` and `service_repositories.yaml` are absent.

## Gate

Satisfied: nauto contains no code that creates or updates an nintent desired model (confirmed by
the new source-scan test) and no candidate generator/input/output contract remains.
Proceeding to Step 7.
