# Fix 1 — Step 3 report: re-establish local Nautobot Job health

Status: **complete**.

This step ran in a new session, after Steps 0–2 were already committed, per
the plan's session-boundary requirement.

## 1. Inspection (no assumption of continued pending state)

- `docker ps`: `nautobot-nautobot-1` and `nautobot-nautobot-scheduler-1` up 2
  days (healthy); `nautobot-nautobot-worker-1` up 26 hours (healthy) — i.e.
  the worker process predates the stuck Job, ruling out "it just hadn't
  started yet."
- JobResult `c104e2eb-8963-4f28-a5ed-f417f2c71a45` (REST API, status only,
  no body read): still `PENDING`, `date_created=2026-08-03T13:50:01Z`,
  `date_started=null` — genuinely still pending, not stale from the earlier
  failed episode.
- Worker logs: last `SUCCESS` entry before this step was `2026-08-03T05:05:22Z`.
  No log activity at all around `13:50:01` when the stuck Job was submitted —
  the worker never touched it.
- `celery inspect ping` → `pong` (worker responsive to control-plane
  commands); `celery inspect active` and `celery inspect reserved` → both
  empty.
- Redis `LLEN default` → `2` (the `default` queue the worker's own startup
  banner confirms it consumes). `LRANGE default 0 -1`, parsed for
  `headers.id`/`headers.task` only (no body): the two queued tasks were
  `c104e2eb-8963-4f28-a5ed-f417f2c71a45` (the known stuck Job) and a second
  `run_job` task, `18dbbdca-0656-4d40-85a9-6faddbea398a`.

Conclusion: a genuine non-consuming worker — alive and answering control
commands/heartbeats, but not pulling new tasks off its own queue. Distinct
from a Nautobot/API outage.

## 2. Health checks before touching anything

- `GET http://localhost:8000/health/` → `200`.
- `nctl status --json` (bounded, well under the plan's 20s budet) completed
  in a few seconds with `ok: true`, `nautobot.reachable: true`,
  `authenticated: true`; host dump ages showed `aghub`/`agpc`/`agstudio`
  collected ~45 minutes earlier (raw nodeutils reports present but not yet
  ingested — consistent with the diagnosis, not a new issue).

## 3. Targeted repair

Restarted only the worker container via the documented compose project:

```
cd devenv/nautobot && docker compose --env-file ../.env restart nautobot-worker
```

Did not touch PostgreSQL, Redis, the `nautobot` app container, or the
scheduler.

## 4. Proof

Within 5 seconds of the restart, both queued tasks drained
(`LLEN default` → `0`) and both JobResults reached `SUCCESS`:

- `c104e2eb-8963-4f28-a5ed-f417f2c71a45`: `date_started=2026-08-03T14:36:50.014816Z`,
  `date_done=2026-08-03T14:36:51.435684Z` (~1.4s runtime). Worker log shows
  this was the original 3-host batch (`aghub`, `agpc`, `agstudio`) from the
  failed episode — i.e. it was the stale already-submitted task draining
  now, not a new invocation of the host-scope-widening bug from a fixed
  `nctl` (Step 2's fix lives in `nctl`'s planner and only applies to plans
  built after the fix; this Job's plan was already queued before Step 2).
- `18dbbdca-0656-4d40-85a9-6faddbea398a`: `date_started=2026-08-03T14:36:50.003068Z`,
  `date_done=2026-08-03T14:36:50.832511Z` (~0.8s runtime), single-host
  `aghub` batch.

No secrets, tokens, or report bodies were displayed or recorded; only
statuses, timestamps, and non-sensitive counts (`created`/`updated`/
`unchanged`) from the worker's own summary log lines.

## Exit condition met

The local queue completed bounded Jobs with terminal results before any
retirement retry, per the plan's Step 3 exit condition and prohibition 2 (no
timeout increase, no blind resubmission — the existing queued tasks were
allowed to drain on their own after the worker fix, nothing was resubmitted).

## Next

Step 4 (live, needs judgment): re-read current desired/actual state for
`agscratch1`/VMID 199 on `aghub`, and — depending on what that shows — either
recover it into an eligible pre-use fixture or move to the cleanup-only
branch. This is fixture preparation outside the retirement skill and
involves external-cluster contact, so it stays a separate step with its own
explicit-approval checkpoints as the plan requires.
