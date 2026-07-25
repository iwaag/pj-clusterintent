# Phase 5 Step 4 Report — Recreate Matched Application and Verify Startup

Parent: [plan.md](plan.md) — Step 4.

Status: **complete** (all three application services recreated from built images via `up --no-build --force-recreate`; web container healthy; worker and scheduler started cleanly; exact commit parity confirmed inside running containers).

## 1. Recreation Execution

Recreated all three services using `docker compose --env-file ../.env up -d --no-build --force-recreate` in `devenv/nautobot/`.

## 2. Container Status and Package VCS Parity

| Service Container | Container ID | Status / Health | Installed Version | Installed VCS Commit | Commit Parity Status |
|---|---|---|---|---|---|
| `nautobot-nautobot-1` | `2b97e08e5d3d` | Up (healthy) | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Matched |
| `nautobot-nautobot-worker-1` | `ea030738ae0e` | Up | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | **Matched** |
| `nautobot-nautobot-scheduler-1` | `d145af086130` | Up | `0.9.0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | **Matched** |

The mixed-container defect has been completely resolved. Web, worker, and scheduler now run the exact same nintent commit `c343c5a`.

## 3. Migration Check & Startup Logs

- Django migrations: `nautobot-server showmigrations nautobot_intent_catalog` confirmed migrations remain at `0016_remove_reconciliation_dashboard_surfaces` (no unplanned migration).
- Startup logs: uWSGI and Celery beat/worker started cleanly with zero schema or import errors.

## 4. Evidence Updated

- `.local/remove-unused-surfaces/p5/20260725-1958/container-package-parity-after.tsv`

## 5. Gate Result

Web, worker, and scheduler are running one exact nintent revision against one final schema. Step 4 gate is **passed**.
