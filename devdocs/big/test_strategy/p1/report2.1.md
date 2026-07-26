# Test Strategy Phase 1 — Step 2.1 Report: Local-Source Scratch Runtime Gate

Parent: [plan.md](plan.md), Step 2. This report continues the historical stop record in
[report2.md](report2.md) under the revised scratch-environment policy; it does not rewrite it.

Status: **`complete`**.

## Runtime gate

- The nintent consolidation is commit `2c1a8a4f0e774c7b683dd4758c6986451e571ddd`.
- A copy of that local checkout was placed only in the existing local scratch Nautobot container
  at `/tmp/test-strategy-p1-nintent`; `PYTHONPATH` placed it ahead of the installed package.
- `nautobot-server test` ran the three canonical modules against the named `test_nautobot`
  database with `--keepdb`: **35 tests found, exit 0**.
- A Django-initialized import check resolved the package and all three changed test modules under
  `/tmp/test-strategy-p1-nintent/`, not the installed package.
- The runner reported the `default` alias as `test_nautobot`; the separate scratch application
  database remained named `nautobot`.
- The test command was executed directly with `docker exec`, bypassing the normal Compose
  entrypoint that previously performed startup work and installation telemetry.

## Scratch repair

The prior `test_nautobot` database contained an incomplete old migration state and failed with a
duplicate `extras_jobbutton.enabled` column. Following the revised plan, only connections to that
named test database were terminated and that database was dropped. The clean run recreated and
used `test_nautobot`; no application database, service, external target, or source file was
changed by the repair.

## Contract result

- `test_remove_unused_surfaces.py` remains deleted; its 29 Phase 0 entries are consolidated in
  the canonical model, API, and UI owners.
- Migrations `0009_reconciliation_status.py` and
  `0016_remove_reconciliation_dashboard_surfaces.py` remain tracked.
- The current models have no `reconciliation_status` or `reconciliation_checked_at` matches.

The full nintent App suite and its final clean-database run remain the Step 6 gate.
