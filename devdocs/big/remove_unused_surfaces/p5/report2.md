# Phase 5 Step 2 Report — Open Maintenance Window and Create Current Recovery Point

Parent: [plan.md](plan.md) — Step 2.

Status: **complete** (maintenance window opened with operator approval; all Nautobot write paths quiesced and application containers stopped; fresh post-0016 recovery backup created and verified).

## 1. Maintenance Window Operator Approval & Scope

- Operator approval: Granted ("ok、進めてください。") at 2026-07-25T20:01 JST
- Allowed mutation scope: Stopping Nautobot application services, creating post-0016 recovery DB backup, rebuilding images with `--no-cache`, and recreating containers to enforce commit parity.

## 2. Quiesce Application Services

Stopped the three Nautobot application containers in order (Scheduler → Worker → Web):
- `nautobot-nautobot-scheduler-1`: `Exited (0)`
- `nautobot-nautobot-worker-1`: `Exited (0)`
- `nautobot-nautobot-1`: `Exited (0)`

Confirmed all three application containers are stopped and no background Jobs remain running.

## 3. Fresh Post-0016 Recovery Backup Creation

- Backup path: `.local/remove-unused-surfaces/p5/20260725-1958/nautobot_post_0016_recovery.dump`
- Mode: `-rw-------` (`0600`)
- Size: 1,783,402 bytes
- SHA-256: `89d4bf7aaf60eadb1132e054c20ff2d158d1ec584d3702ad317128b411fe3b68`
- `pg_restore --list` check: Successful (2,415 TOC entries, Format: CUSTOM)
- Git ignore check: Saved inside git-ignored `.local/` directory structure.

## 4. Evidence Files Updated

- `.local/remove-unused-surfaces/p5/20260725-1958/post-migration-backup-metadata.txt`

## 5. Gate Result

All application write paths are quiesced, both recovery points (pre-window `0014` backup and current `0016` recovery backup) are identified and verified. Step 2 gate is **passed**.
