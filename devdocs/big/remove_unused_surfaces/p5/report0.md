# Phase 5 Step 0 Report — Reconfirm the Partial-Deployment Baseline

Parent: [plan.md](plan.md) — Step 0.

Status: **complete** (read-only audit performed; exact mixed-container baseline and environment state recorded).

## 1. Timestamp and Evidence Location

- Executed: 2026-07-25T19:58 JST
- Private Evidence Directory: `.local/remove-unused-surfaces/p5/20260725-1958/` (mode `0700`, files `0600`)
- Evidence files created:
  - `revisions-start.txt`
  - `container-package-parity-before.tsv`
  - `pre-backup-metadata.txt`

## 2. Starting Repository Snapshot

| Repository | Revision | State / Branch |
|---|---|---|
| superproject | `bbdf17eee1514192c27f4f6ae01cfa5b9f4b22e4` | clean, main |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | clean, main |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | clean, main |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean, main |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean, main |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean, main |

## 3. Live Container Package Parity Baseline

| Service Container | Container ID | Status / Health | Installed nintent Version | Installed VCS Commit | Parity Status |
|---|---|---|---|---|---|
| `nautobot-nautobot-1` | `cef13d08b98c` | Up (healthy) | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Target commit |
| `nautobot-nautobot-worker-1` | `ac5078b30dfa` | Up (healthy) | `0.9.0` | `ad9d36397d23c269ad748e13acbccc532fa29f52` | **Mismatch (old revision)** |
| `nautobot-nautobot-scheduler-1` | `99c887e10ac8` | Up (healthy) | `0.9.0` | `ad9d36397d23c269ad748e13acbccc532fa29f52` | **Mismatch (old revision)** |

The web container runs the target nintent revision (`c343c5a...`), but worker and scheduler are still running the old nintent revision (`ad9d363...`). This documents the mixed-container defect to be resolved in Phase 5 container recreation.

## 4. Live Database & Schema State

- Django Migrations: Applied through `0016_remove_reconciliation_dashboard_surfaces`
- Columns verified absent from database schema:
  - `nautobot_intent_catalog_desirednode.reconciliation_status`: absent (`False`)
  - `nautobot_intent_catalog_desirednode.reconciliation_checked_at`: absent (`False`)
  - `nautobot_intent_catalog_desirednode.realized_vm_id`: absent (`False`)
  - `nautobot_intent_catalog_desiredservice.reconciliation_status`: absent (`False`)
  - `nautobot_intent_catalog_desiredservice.reconciliation_checked_at`: absent (`False`)
- Desired Compute object counts:
  - `DesiredComputePlatform`: 0
  - `DesiredComputeInstance`: 0
- Running / queued JobResult count: 0

## 5. Process & Network Listeners

- TCP port 8300: `lsof -i :8300` confirmed port 8300 is not listening.
- Service logs: uWSGI and Celery workers running without active errors.

## 6. Stale Dashboard Output Path

- Path: `/Users/eiji/.local/state/nctl/dashboard/`
- Directory contents (entries and sizes recorded without inspecting contents):
  - `drift.json`: 1,106 bytes
  - `index.html`: 13,905 bytes

## 7. Pre-Window Backup Verification

- Backup path: `.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump`
- Mode: `-rw-------` (`0600`)
- Size: 1,772,665 bytes
- SHA-256: `622e9feb09eb7047aa10591a6c91ad6713252af45c7c0c714c93cb41f7c9eb96`
- Git ignore check: `git check-ignore` confirms `.local/` path is ignored.

## 8. Gate Result

The exact baseline and mixed-container defect have been documented. Zero live mutations occurred during Step 0. Step 0 gate is **passed**.
