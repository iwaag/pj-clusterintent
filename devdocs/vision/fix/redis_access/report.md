# Fix report — Celery worker silent stall over the devenv Redis path

Date: 2026-08-06 (JST)
Session type: `workflow-improvement` (agentdocs)
WorkflowEpisode: `511875ea-65e4-4624-8638-202269fc6a73` (resolved)
Commit: `2faa1cb` (superproject) — `devenv: harden Celery broker transport against silent dead Redis connections`

## Symptom

During `nctl reconcile agbach --yes`, the nodeutils collection succeeded but the
Nautobot Job "Ingest Nodeutils Inventory" failed to start with HTTP 503
(`CeleryWorkerNotRunningException`). Container status, container healthchecks,
and `nctl status` all showed the stack healthy; only `celery inspect ping`
revealed the worker was unresponsive. `docker compose restart nautobot-worker`
restored it and the re-run converged.

This was a second occurrence: the same silent-worker state (Job stuck
`PENDING`, cleared by a worker container restart) was recorded in
[`devdocs/big/vm/p2/sidefix1/report6.md`](../../../big/vm/p2/sidefix1/report6.md),
and the same phenomenon had happened unrecorded before that.

## Root cause

- The worker reaches Redis via `host.docker.internal:6379` — Docker Desktop's
  NAT path to `service_scripts-redis-1`, a container in a different compose
  project. Host sleep (and Docker Desktop network resets) silently kill
  established TCP flows on that path.
- The devenv `nautobot_config.py` had no `CELERY_BROKER_TRANSPORT_OPTIONS`
  (all Nautobot defaults): no socket keepalive, no periodic connection health
  check. After a flow died, the worker blocked forever on half-open
  BRPOP/pub-sub sockets without logging anything — 48h of worker logs around
  the incident contained zero connection errors.
- The worker container's healthcheck (inherited from the base image) is
  `nautobot-server health_check`, which opens *fresh* connections from a fresh
  process. It cannot see the celery process's dead long-lived sockets, so the
  container stayed `healthy` while the worker was gone. The Redis server side
  was fine (`timeout=0`, `tcp-keepalive=300`); the missing hardening was
  client-side.

## Fix

`devenv/nautobot/nautobot_config.py`:

```python
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "socket_keepalive": True,
    "health_check_interval": 25,
    "retry_on_timeout": True,
}
```

This makes redis-py/kombu detect dead connections and reconnect instead of
blocking silently. The file is volume-mounted, so the fix required only a
restart of `nautobot`, `nautobot-worker`, and `nautobot-scheduler` — no image
rebuild.

## Verification

- `app.conf.broker_transport_options` inside the restarted worker returns the
  three options above.
- `app.control.inspect(timeout=5).ping()` returns `{'celery@…': {'ok': 'pong'}}`.
- All three Nautobot containers healthy after restart.
- Honest limit: the suspected trigger is host sleep, so the full acceptance is
  the *next* sleep cycle passing without a stalled worker. If the stall recurs
  after this fix, open a fresh WorkflowEpisode (the resolved one cannot be
  reopened).

## Scope decision

Option A (client-side transport hardening) only, by explicit user decision:
the current phase prioritizes feature velocity on the normal path, and
devenv Redis-path instability is external to this system. Deliberately not
done, revisit only on recurrence:

- no recovery runbook skill (would codify a symptomatic restart),
- no worker healthcheck rework / auto-restart machinery,
- no topology change (moving Redis into the devenv compose network).
