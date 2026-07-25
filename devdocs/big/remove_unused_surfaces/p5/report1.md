# Phase 5 Step 1 Report — Validate Backup and Reconstruct Missing Pre-Migration Aggregates

Parent: [plan.md](plan.md) — Step 1.

Status: **complete** (pre-window backup dump validated via disposable PostgreSQL 15 restore; missing pre-migration aggregate metrics successfully reconstructed and recorded).

## 1. Pre-Window Backup Dump Validation

- Dump file: `.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump`
- `pg_restore --list` check: Successful (2,397 TOC entries, format: CUSTOM, PostgreSQL 15.17)
- SHA-256 before & after restore test: `622e9feb09eb7047aa10591a6c91ad6713252af45c7c0c714c93cb41f7c9eb96` (identical)

## 2. Disposable Restore & Aggregates Query Result

An isolated, unexposed container `temp_p5_postgres` (`postgres:15-alpine`) was launched, and the dump was restored into database `nautobot_restore`.

### Reconstructed Pre-Migration Metrics (Labeled as Reconstructed from Backup)

1. **Migration State in Backup Database**:
   - Latest applied migration: `0014_braindump_exchange_diary`
   - Migrations `0015` and `0016`: Absent (confirming backup precedes VM Phase 3 & removal migrations)

2. **Legacy `DesiredNode.realized_vm` Column Usage**:
   - `realized_vm_id` non-null count: `0`

3. **DesiredNode Reconciliation Cache Aggregate Counts**:
   - `reconciliation_status` breakdown: `converged` = 5
   - `reconciliation_checked_at` non-null count: 5

4. **DesiredService Reconciliation Cache Aggregate Counts**:
   - `reconciliation_status` breakdown: `converged` = 1, blank (`''`) = 5
   - `reconciliation_checked_at` non-null count: 1

5. **Desired Compute Platform / Instance Tables**:
   - Table count: 0 (absent in `0014` schema)

## 3. Environment Cleanup

- Container `temp_p5_postgres` stopped and removed.
- Backup dump file remained unmodified.
- Evidence recorded in `.local/remove-unused-surfaces/p5/20260725-1958/pre-backup-restore-aggregates.txt`.

## 4. Gate Result

Rollback media is restore-proven, missing aggregate evidence is reconstructed honestly and labeled as reconstruction from backup. Step 1 gate is **passed**.
