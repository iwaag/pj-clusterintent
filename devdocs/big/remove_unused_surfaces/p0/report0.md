# Phase 0 Step 0 — Establish the non-mutation boundary

Parent: [plan.md](plan.md), Step 0.

## Evidence directory

Created `.local/remove-unused-surfaces/p0/20260725-145028/`, mode `0700`. Evidence files inside it
are written mode `0600` (`step0-boundary.txt` confirmed at `-rw-------`).

## Ignore checks (`git check-ignore -v`)

| Path | Rule |
|---|---|
| `.local/secrets` | `.gitignore:2:.local` |
| `.local/remove-unused-surfaces/p0/20260725-145028` | `.gitignore:2:.local` |
| `nctl.toml` (root) | `.gitignore:4:/nctl.toml` |
| `nctl/__pycache__/*.pyc` | `nctl/.gitignore:1:__pycache__/` |
| `nctl/src/nctl_core/__pycache__/*.pyc` | `nctl/.gitignore:1:__pycache__/` |

No local `nctl.toml` currently exists at the repo root; only `example.nctl.toml` is tracked. Its
`[dashboard].out_dir` default is `~/.local/state/nctl/dashboard`, outside the repo tree, so it has
no in-repo generated-output path to separately ignore. Step 2 will resolve the live effective
dashboard directory through `Config.load().dashboard.resolved_out_dir()` rather than assuming this
default.

## Operator and timestamp

Recorded 2026-07-25 14:50:28 JST, operator `iwaag` (git user). No private prose recorded.

## Container state (recorded, not restarted)

```text
nautobot-nautobot-1            Up 38 hours (healthy)
nautobot-nautobot-worker-1     Up 13 hours (healthy)
nautobot-nautobot-scheduler-1  Up 38 hours (healthy)
```

`docker ps` only; no `docker restart`/`compose up` was run.

## Command-class boundary

Phase 0 is limited to filesystem/process/config/schema reads and tracked documentation edits.
`nctl dashboard`, `nctl serve`, `nctl reconcile`, migration apply, container restart, and Job
triggers are excluded for the whole phase. Any nominally read-only command that would itself write
an event log/JSONL or other side effect (e.g. `nctl status`, `nctl drift` without `--json`-only
inspection) is treated as a write; Step 3 substitutes `--help` invocations, and Step 2 uses direct
ORM/GraphQL reads and `showmigrations` instead.

## Gate

The evidence location is private (`0700`/`0600`), secrets remain indirect (no `.local/secrets`
content read or copied), and no live or generated state was changed — only `docker ps` and local
`git check-ignore`/`ls` reads were run.
