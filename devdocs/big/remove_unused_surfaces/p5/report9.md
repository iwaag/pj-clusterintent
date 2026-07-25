# Phase 5 Step 9 Report — Resume Operations and Freeze Final Tuple

Parent: [plan.md](plan.md) — Step 9.

Status: **complete** (all three Nautobot application services healthy and running exact target commit `c343c5a`; port 8300 not listening; stale dashboard path absent; maintenance window closed; VM Phase 3 Steps 9–12 handed off as separate next work).

## 1. Final Container Parity & Health Status

| Container Name | Container ID | Status / Health | Version | VCS Commit | Parity Status |
|---|---|---|---|---|---|
| `nautobot-nautobot-1` | `2b97e08e5d3d` | Up (healthy) | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |
| `nautobot-nautobot-worker-1` | `ea030738ae0e` | Up (healthy) | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |
| `nautobot-nautobot-scheduler-1` | `d145af086130` | Up (healthy) | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |

## 2. Final Frozen Revision Tuples

### Matched Final Target Tuple

| Repository | Revision | Remote Status |
|---|---|---|
| superproject | `fb231a9` (Step 8); this report's commit follows | clean |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | main, pushed |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | main, pushed |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | main, pushed |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | main, pushed |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | main, pushed |

### Backup Evidence

- Pre-window `0014` backup: `.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump` (SHA-256: `622e9feb09eb7047aa10591a6c91ad6713252af45c7c0c714c93cb41f7c9eb96`)
- Post-0016 recovery backup: `.local/remove-unused-surfaces/p5/20260725-1958/nautobot_post_0016_recovery.dump` (SHA-256: `89d4bf7aaf60eadb1132e054c20ff2d158d1ec584d3702ad317128b411fe3b68`)

## 3. Maintenance Window Closure & Handoff

- Maintenance window: Operations resumed cleanly; web, worker, and scheduler running normally.
- Stale dashboard path: `/Users/eiji/.local/state/nctl/dashboard/` remains absent.
- Port 8300: Not listening.
- VM Phase 3 Handoff: Steps 9–12 (canonical seed review, apply, repeat-import proof) remain separate work for the VM initiative and were not misreported as complete here.

## 4. Gate Result

Only the final matched tuple is active, all approved services are resumed, and no deferred VM seed work is misreported as complete. Step 9 gate is **passed**.
