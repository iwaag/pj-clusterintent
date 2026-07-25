# Phase 0 Step 6 — Audit real consumers and local invocation paths

Parent: [plan.md](plan.md), Step 6.

Full transcript in the private evidence file `process-audit.txt`.

## Tracked automation

Searched Makefiles, CI config, compose files, Ansible tasks, and shell wrappers in all six
repositories for `nctl serve`, `nctl dashboard`, `:8300`, `NCTL_SERVE_TOKEN`, `dashboard_url`.
Zero matches except `ansible_agdev/Makefile`, whose `NCTL` variable and help comments invoke only
`nctl reconcile`/`nctl render` — both retained commands, no `serve`/`dashboard` target.

## Git-ignored local automation, cron, launch services

- `crontab -l` (user `eiji`): empty, "no crontab for eiji".
- `~/Library/LaunchAgents`: only `homebrew.mxcl.ollama.plist` (unrelated to this project).
- `/Library/LaunchAgents`, `/Library/LaunchDaemons` (readable set): no `nctl`/`dashboard`/
  `clusterintent` entries.
- `launchctl list` filtered for `nctl`/`dashboard`/`clusterintent`: zero matches.

## Live process and listener — found, resolved

`ps aux` found two processes that string-matching alone would have missed: `uv run --project nctl
--extra serve nctl serve --config nctl.toml --json` (PID 27946, ppid 1) and its child `nctl serve`
process (PID 27948), both started **2026-07-20 10:18:31**, i.e. running for about 5 days at audit
time. `lsof -nP -iTCP:8300 -sTCP:LISTEN` confirmed PID 27948 was the sole listener on
`127.0.0.1:8300` (loopback only; no established non-listener connections at audit time, and not
reachable from another LAN host as bound). No container published port 8300 or ran `nctl serve`.

Per plan §6's explicit instruction ("If an invoker is found, do not delete it silently... Stop
Phase 0 until the user confirms it can be removed or scopes it out"), execution paused here and
the operator was asked directly. The operator confirmed this was a stale process left running by
accident (not an active consumer, script, or UI depending on it) and approved stopping it. With
that explicit approval, `kill 27948 27946` was run and immediately re-verified: `ps -p 27948 -p
27946` returns no rows, and `lsof -nP -iTCP:8300 -sTCP:LISTEN` returns no rows. Port 8300 has zero
nctl listener as of this step's completion.

## Reverse proxy / static host

No tracked `*.conf`/`*nginx*`/`*Caddyfile*` file references port 8300 or a dashboard URL.

## Shell history

`~/.zsh_history` searched (via `command grep` to bypass this environment's shimmed `grep` function,
which silently skips the history file under its default binary-detection flag) for the exact
strings `nctl serve` and `nctl dashboard`, count-only, no surrounding commands or arguments
recorded: both **0**.

## Gate

Every discoverable consumer is either zero (tracked automation, cron, launch services, reverse
proxy, shell history) or explicitly resolved by the user (the one live process, stopped with
operator approval and re-verified). Port 8300 has no nctl listener as of the end of this step —
the plan's stated Step 6 gate condition is met, but only after the live-process finding was
surfaced and resolved rather than silently classified as "no consumer."
