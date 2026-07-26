# Test Strategy Phase 0 Step 0 Report — Freeze the Tuple and Create Private Evidence

Parent: [plan.md](plan.md) — Step 0.

Status: **partially complete** (Step 0 complete: baseline revision tuple frozen, private evidence root created, environment state recorded, dirty check clean; overall Phase 0 in progress).

## 1. Execution Summary

- **Execution Timestamp**: `20260726T034839Z` (UTC)
- **Private Evidence Directory**: `.local/test-strategy/p0/20260726T034839Z/`
- **Worktree Cleanliness Check**: All 6 repositories (superproject + 5 submodules) verified clean with zero unexpected dirty or untracked changes.

## 2. Frozen Revision Tuple

| Repository | Revision (HEAD SHA) | Branch / Upstream | Porcelain Status |
|---|---|---|---|
| superproject | `8e7762e24d2a822a2bc946d7afb24142dbff6e12` | `## main...origin/main` | clean |
| `nctl` | `e813f6963afc17af74c48aae5660461d3f10498a` | `## main...origin/main` | clean |
| `nintent` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | `## main...origin/main` | clean |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | `## main...origin/main` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `## main...origin/main` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `## main...origin/main` | clean |

## 3. Environment & Installed Components Snapshot

| Tool / Layer | Version / Identity | Notes / Container |
|---|---|---|
| OS & Architecture | `Darwin arm64` | macOS host |
| Host Python | `Python 3.14.2` | System Python3 |
| uv | `uv 0.11.21` (5aa65dd7a 2026-06-11) | Package & environment runner |
| pytest | `pytest 9.1.1` | nctl project pytest |
| Git | `git version 2.50.1` (Apple Git-155) | Superproject & submodule vcs |
| Docker | `Docker version 29.4.0` | Host Docker engine |
| Docker Compose | `Docker Compose version 5.0.1` | Local compose runner |
| OpenSSH | `OpenSSH_10.0p2, LibreSSL 3.3.6` | System SSH client |
| Ansible | `ansible [core 2.21.1]` | Homebrew package v14.1.0 (Python 3.14.6) |
| Django | `5.2.14` | In `nautobot-nautobot-1` container |
| Nautobot | `3.1.3` | In `nautobot-nautobot-1` container |

## 4. Tracked Test File Digest Inventory

Recorded SHA-256 digests for all 98 tracked test modules and shared test-only fixture/helper
files across 5 submodules into
`.local/test-strategy/p0/20260726T034839Z/tracked-test-files.tsv`.

- `nctl`: 72 test files
- `nintent`: 14 files (12 `test_*.py` modules plus `tests/__init__.py` and `tests/factories.py`)
- `nauto`: 8 test files
- `nodeutils`: 3 test files
- `ansible_agdev helper`: 1 test file
- **Total**: 98 tracked files (96 `test_*.py` modules plus 2 shared fixture/helper files)

## 5. Evidence Artifacts Created

The private evidence root `.local/test-strategy/p0/20260726T034839Z/` was created to hold:

- `README.txt`: Evidence directory timestamp and metadata.
- `commands.jsonl`: Sanitized execution log initialized.
- `revisions-start.tsv`: Starting repository revision snapshot.
- `revisions-end.tsv`: Ending repository revision snapshot for Step 0.
- `environment.tsv`: Tool versions and environment parameters.
- `installed-components.tsv`: Containerized software versions (Django, Nautobot).
- `migrations.txt`: Applied Nautobot Intent Catalog migration list (up to `0016`).
- `tracked-test-files.tsv`: Full list of 98 tracked test files/shared fixture-helper modules and their SHA-256 digests.
- `leak-check-before.tsv`: Pre-execution snapshot of running containers, Docker volumes, networks, and processes.
- `logs/`: Directory reserved for private command logs.

Correction (recorded during a later review of this report against the actual filesystem state):
the root and its files were created with the default umask (`0755`/`0644`), not the `0700`/`0600`
mode `plan.md` §5 requires. This was found and corrected with `chmod 700`/`chmod 600` after the
fact; no evidence content was exposed to another local user in the interim, and the directory now
matches the required mode.

## 6. Next Steps

Proceed to Step 1: Reconstruct current installed and migration state in `devdocs/big/test_strategy/p0/report1.md` (or continue within Phase 0 implementation sequence).
