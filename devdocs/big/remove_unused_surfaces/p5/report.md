# Phase 5 Final Report — Coordinated Deployment and Final Verification

Parent: [plan.md](plan.md) (all steps).

Status: **complete** (maintenance window opened with operator approval; pre-window `0014` backup validated and missing pre-migration aggregates reconstructed; post-`0016` recovery backup created; images rebuilt with `--no-cache` and all three containers recreated to enforce commit `c343c5a` parity; migration dry-run, REST, GraphQL, authenticated UI, and nctl CLI paths verified positive; dry reconcile operation `01KYCF40PFYYW47PY1T232WP48` executed and indexed; removed commands and port 8300 listener absent; stale dashboard output path safely archived; all test suites passed; measurements repeatable).

## 1. Execution Timestamp & Evidence Location

- Execution timestamp / window: 2026-07-25T19:58 JST to 2026-07-25T20:05 JST
- Maintenance window operator approval: Granted ("ok、進めてください。") at 2026-07-25T20:01 JST
- Private Evidence Directory: `.local/remove-unused-surfaces/p5/20260725-1958/` (mode `0700`, files `0600`)
- Evidence files generated:
  - `revisions-start.txt`
  - `container-package-parity-before.tsv`
  - `pre-backup-metadata.txt`
  - `pre-backup-restore-aggregates.txt`
  - `post-migration-backup-metadata.txt`
  - `build-images.tsv`
  - `build-resolved-shas.txt`
  - `container-package-parity-after.tsv`
  - `dashboard-disposition.txt`
  - `tests-and-measurements.txt`
  - `deletion-search-final.tsv`
  - `resume-and-final-state.txt`

## 2. Starting and Ending Revisions

| Repository | Starting Revision | Ending Revision | Remote Status |
|---|---|---|---|
| superproject | `bbdf17eee1514192c27f4f6ae01cfa5b9f4b22e4` | `ca565d6` (this report's commit follows) | clean |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | main, pushed |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | `c343c5a56047b0df9ad901dd4459863ef1954053` | main, pushed |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | `251b056549f1b01f604b42b486fdc12d667db521` | main, pushed |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | main, pushed |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | main, pushed |

## 3. Resolution of Planning-Time Mixed-Container Defect

Planning-time audit (Step 0) revealed that while the web container ran nintent `c343c5a`, the worker and scheduler containers still ran old nintent commit `ad9d363`.

Through Step 3 (no-cache image build) and Step 4 (container recreation), all three containers were brought into complete package commit parity:

| Service Container | Container ID | Installed Version | VCS Commit | Parity Status |
|---|---|---|---|---|
| `nautobot-nautobot-1` | `2b97e08e5d3d` | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |
| `nautobot-nautobot-worker-1` | `ea030738ae0e` | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |
| `nautobot-nautobot-scheduler-1` | `d145af086130` | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |

## 4. Database Backups & Reconstructed Pre-Migration Aggregates

1. **Pre-Window `0014` Backup Dump**:
   - Location: `.local/remove-unused-surfaces/p4/p5-live-20260725/nautobot_pre_p5_backup.dump`
   - Mode: `0600`, Size: 1,772,665 bytes, SHA-256: `622e9feb09eb7047aa10591a6c91ad6713252af45c7c0c714c93cb41f7c9eb96`
   - Validated via `pg_restore --list` (2,397 TOC entries) and restored into disposable container `temp_p5_postgres`.
   - Reconstructed aggregate metrics:
     - Migrations end at: `0014_braindump_exchange_diary`
     - Legacy `realized_vm_id` non-null count: `0`
     - `DesiredNode` `reconciliation_status` counts: `converged` = 5 (checked_at non-null count: 5)
     - `DesiredService` `reconciliation_status` counts: `converged` = 1, blank (`''`) = 5 (checked_at non-null count: 1)
     - Desired compute tables count: 0 (absent in `0014`)

2. **Post-`0016` Recovery Backup Dump**:
   - Location: `.local/remove-unused-surfaces/p5/20260725-1958/nautobot_post_0016_recovery.dump`
   - Mode: `0600`, Size: 1,783,402 bytes, SHA-256: `89d4bf7aaf60eadb1132e054c20ff2d158d1ec584d3702ad317128b411fe3b68`
   - Validated via `pg_restore --list` (2,415 TOC entries).

## 5. Live Schema & API Verification

- Django migrations: `makemigrations --check --dry-run` returned `No changes detected` (applied through `0016`).
- Table columns: `reconciliation_status`, `reconciliation_checked_at`, and `realized_vm_id` confirmed absent from DB tables.
- REST API: `DesiredNode` and `DesiredService` REST endpoints omit cache fields; dashboard redirect route (`/plugins/intent-catalog/dashboard-redirect/`) returns HTTP `404`.
- GraphQL API: Ordinary `desired_nodes` root returns 5 nodes; compute roots return `[]` (pre-seed state); `__type` introspection confirms cache and legacy node VM fields are absent.
- Authenticated UI: List pages `/plugins/intent-catalog/nodes/` and `/plugins/intent-catalog/services/` render HTTP `200 OK` without status columns/links.

## 6. Retained nctl & Dry Reconcile Proof

- `nctl status --json`, `actual --json`, `drift --json`, `render hosts-intent --json`, `render production --json`, and `render dnsmasq --json` executed cleanly without errors or unwanted side effects.
- Dry reconcile (`nctl reconcile --json` without `--yes`):
  - Created bounded operation ID: `01KYCF40PFYYW47PY1T232WP48`
  - Mode: `"plan"`, State: `"planned"`, Rounds: `[]`
  - Zero executed actions, zero preflight/Ansible/nodeutils/ingest side effects.
  - Output schema `nctl.reconcile.v2` lacks `dashboard` field.
- `nctl ops list` and `ops show 01KYCF40PFYYW47PY1T232WP48` verified.
- `nctl braindump list --json` verified without leaking private prose.

## 7. Removed Surface Proof & Dashboard Output Disposition

- Command surface: `nctl --help` lists exact 11 retained commands; `nctl dashboard` and `nctl serve` return standard Typer unknown-command errors.
- Network listener: `lsof -i :8300` confirmed port 8300 is not listening.
- Stale dashboard output path: `/Users/eiji/.local/state/nctl/dashboard/` moved atomically to private evidence directory `.local/remove-unused-surfaces/p5/20260725-1958/retired-dashboard/` (mode `0700`). Surrounding `~/.local/state/nctl/` items (`events/`, `ssh/`, locks) remain untouched.

## 8. Test Suites & Deletion Searches

- `nctl` pytest suite: **954 passed**
- `uv lock --check`: Clean
- `nintent` local Django-free suite: **187 passed**
- `nintent` full Nautobot App suite in container: **252 passed** (0 failures).
- Clean plain wheel build & install: wheel `nctl-0.0.1-py3-none-any.whl` installed into venv; `nctl_core.serve` and `dashboard` modules absent (`False`).
- Deletion searches: **Zero unexplained active matches** across code and documentation.
- `git diff --check`: Clean across superproject and all submodules.

## 9. Code & Test Measurements

| Metric | Phase 4 Baseline | Phase 5 Ending Value |
|---|---:|---:|
| `nctl` top-level commands | 11 | 11 |
| `nctl` collected pytest cases | 954 | 954 |
| `nctl` Python source lines (`src/`) | 17,763 | 17,763 |
| `nctl` test lines (`tests/`) | 19,380 | 19,380 |
| `nintent` local Django-free tests | 187 | 187 |
| `nintent` full Nautobot App tests | 252 | 252 |
| `nintent` non-test Python lines | 9,560 | 9,560 |
| `nintent` test lines | 4,029 | 4,029 |
| `nintent` template lines | 1,327 | 1,327 |
| `nintent` numbered migrations | 16 | 16 |

## 10. Confirmation of No Unintended Mutation

No desired/actual/Braindump/SSH/Ansible/nodeutils/ingest/host/Proxmox mutation occurred. All live actuation paths remained untouched during dry verification.

## 11. Exit Criteria Table

| Plan §10 Criterion | Status | Evidence Reference |
|---|---|---|
| Baseline and mixed-container defect documented | ✅ | [report0.md](report0.md) §3 |
| Mixed-container defect eliminated | ✅ | [report4.md](report4.md) §2, §3 above |
| Three built images & running containers prove commit `c343c5a` parity | ✅ | [report3.md](report3.md) §3, [report4.md](report4.md) §2 |
| `nctl` `ebe8a1d` active matching local revision | ✅ | [report0.md](report0.md) §2, §2 above |
| Pre-window dump checksum & restore-proven without touching live DB | ✅ | [report1.md](report1.md) §1–2, §4 above |
| Reconstructed pre-migration aggregates labeled as reconstruction | ✅ | [report1.md](report1.md) §2, §4 above |
| Post-`0016` recovery backup created and validated | ✅ | [report2.md](report2.md) §3, §4 above |
| Maintenance-window approval, quiesce, and resume recorded | ✅ | [report2.md](report2.md) §1–2, [report9.md](report9.md) §3 |
| Migrations end at `0016`, `0009` retained, no pending migration | ✅ | [report5.md](report5.md) §1, [report9.md](report9.md) §2 |
| Cache & legacy node VM columns absent | ✅ | [report0.md](report0.md) §4, [report5.md](report5.md) §2–4 |
| Final compute/MAC schema and constraints present | ✅ | [report5.md](report5.md) §3 |
| No desired compute seed or actual-link mutation introduced | ✅ | [report5.md](report5.md) §3, §10 above |
| Authenticated DesiredNode/DesiredService UI pages render without removed surfaces | ✅ | [report5.md](report5.md) §4 |
| Retained REST & GraphQL paths work and omit removed fields | ✅ | [report5.md](report5.md) §2–3 |
| VM Phase 3 Step 8 read/cutover checks pass with zero actuation | ✅ | [report5.md](report5.md) §5 |
| `nctl status`, `actual`, `drift`, renders, and dry reconcile run cleanly | ✅ | [report5.md](report5.md) §5, [report6.md](report6.md) §1 |
| Dry reconcile proves planner execution and zero executed actions | ✅ | [report6.md](report6.md) §1 |
| `nctl ops list/show` reads new dry operation and historical evidence | ✅ | [report6.md](report6.md) §2 |
| Braindump list/show works without private prose leak | ✅ | [report6.md](report6.md) §3 |
| `nctl --help` has 11 retained commands; `dashboard`/`serve` return Typer errors | ✅ | [report7.md](report7.md) §1 |
| No server/dashboard module, config, token, dependency, or subscriber active | ✅ | [report7.md](report7.md) §1–2, [report8.md](report8.md) §2 |
| Port 8300 not listening | ✅ | [report7.md](report7.md) §2 |
| Dashboard directory archived safely with approval; broader state untouched | ✅ | [report7.md](report7.md) §3 |
| Final deletion searches contain only classified exceptions | ✅ | [report8.md](report8.md) §3 |
| Applicable nctl/nintent suites, lock check, and plain-wheel proof pass | ✅ | [report8.md](report8.md) §1–2 |
| Measurements match Phase 4 baseline | ✅ | [report8.md](report8.md) §4, §9 above |
| VM Phase 3 Steps 9–12 handed off as separate next work | ✅ | [report9.md](report9.md) §3 |

## 12. Final Handoff Note

Phase 5 is complete. All unused nctl server and dashboard surfaces and nintent reconciliation cache fields are removed and verified live. VM Phase 3 Steps 9–12 (canonical seed review, apply, repeat-import proof) remain handed off as separate next work.
