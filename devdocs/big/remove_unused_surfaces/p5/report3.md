# Phase 5 Step 3 Report — Build and Verify All Three Final Images

Parent: [plan.md](plan.md) — Step 3.

Status: **complete** (three Docker images built with `--no-cache`; nintent Git VCS commit `c343c5a` verified inside all three images before container startup).

## 1. Verified Target Source

- Submodule `nintent`: `c343c5a56047b0df9ad901dd4459863ef1954053` (pushed, `origin/main`)

## 2. Image Build Results (`docker compose build --no-cache`)

Built from `devenv/nautobot/docker-compose.yml`:
- `nautobot-nautobot:latest` (Image ID: `bde751b17d15`)
- `nautobot-nautobot-worker:latest` (Image ID: `7cc4a365bfcf`)
- `nautobot-nautobot-scheduler:latest` (Image ID: `909f8f54e8d0`)

All three images built successfully from Dockerfile, cloning `https://github.com/iwaag/nprojects.git` and resolving HEAD to commit `c343c5a56047b0df9ad901dd4459863ef1954053`.

## 3. Pre-Startup Image Inspection Proof

Ran `--entrypoint cat` inspection on each built image without starting the application:

| Image Name | Image ID | Installed `nautobot-intent-catalog` Commit | Status |
|---|---|---|---|
| `nautobot-nautobot:latest` | `bde751b17d15` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Pass |
| `nautobot-nautobot-worker:latest` | `7cc4a365bfcf` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Pass |
| `nautobot-nautobot-scheduler:latest` | `909f8f54e8d0` | `c343c5a56047b0df9ad901dd4459863ef1954053` | Pass |

All three images contain the exact target commit `c343c5a`.

## 4. Gate Result

Three separately named images are package-proven before any final service starts. Step 3 gate is **passed**.
