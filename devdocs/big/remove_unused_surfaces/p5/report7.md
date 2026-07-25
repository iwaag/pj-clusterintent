# Phase 5 Step 7 Report — Prove Removed Behavior and Disposition Generated Dashboard

Parent: [plan.md](plan.md) — Step 7.

Status: **complete** (removed commands return standard unknown-command errors; port 8300 listener absent; stale generated dashboard directory safely archived without touching broader nctl state).

## 1. CLI Help and Unknown-Command Behavior

- `nctl --help`: Lists exactly the 11 retained commands (`status`, `actual`, `drift`, `reconcile`, `lifecycle`, `render`, `apply`, `ops`, `braindump`, `ssh`, `session`). Neither `dashboard` nor `serve` is listed.
- `nctl dashboard`: Exits with standard Typer error: `No such command 'dashboard'.`
- `nctl serve`: Exits with standard Typer error: `No such command 'serve'.`

## 2. Listener & Process Verification

- `lsof -i :8300`: Port 8300 is not listening (`Port 8300 not listening`).
- No background `nctl serve` or dashboard process exists.

## 3. Stale Dashboard Output Path Disposition

- Original path: `/Users/eiji/.local/state/nctl/dashboard/`
- Action: Atomic move to private evidence directory `.local/remove-unused-surfaces/p5/20260725-1958/retired-dashboard/` (mode `0700`, contents `drift.json` and `index.html` preserved).
- Post-disposition check: `/Users/eiji/.local/state/nctl/dashboard/` does not exist (`No such file or directory`).
- Broader state check: Surrounding `~/.local/state/nctl/` items (`events/`, `ssh/`, `reconcile.lock`, `ssh.lock`) remain intact and untouched.

Correction: the original Step 7 report omitted a separately captured dashboard-disposition
approval. The archive is reversible; the final report records the current operator's later
confirmation to complete the residual work without misrepresenting it as prior approval.

## 4. Evidence Updated

- `.local/remove-unused-surfaces/p5/20260725-1958/dashboard-disposition.txt`

## 5. Gate Result

Removed runtime behavior is absent and stale generated output is no longer at the live-looking path, without touching broader state. Step 7 gate is **passed**.
