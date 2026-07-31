# Node Agent — Phase 5 Report

Status: in progress (2026-07-31).

## Step 0 — API pinning spike

Read `GET /doc` over the existing nctl-managed, loopback-only SSH tunnel on
both `agstudio` and `agpc`. Both running OpenCode 1.18.10 instances expose
the same OpenAPI 3.1 surface. The Phase 5 adapter is pinned to these paths:

- `GET /api/session?directory=<workdir>` lists directory-scoped sessions.
- `POST /api/session` creates a session and returns `data.id`.
- `POST /session/{sessionID}/message?directory=<workdir>` takes
  `{"parts":[{"type":"text","text":"…"}]}` and returns the completed
  message payload.
- `POST /api/session/{sessionID}/interrupt` returns 204 on an accepted
  interrupt.

No credentials or session transcript content was recorded. The only live
access in this step was the permitted read-only API-document fetch.

## Steps 1–2 — Local implementation and tests

Committed nctl `3365e1e` (`Add programmatic node agent delegation`):

- Added the deliberately small OpenCode 1.18.10 HTTP adapter and the
  `nctl agent run`, `sessions`, `send`, and `abort` command paths.
- Added stable `nctl.agent.{run,sessions,send,abort}.v1` envelopes and text
  rendering. `run`, `send`, and `abort` write durable operation events without
  prompt or reply content; only lengths and outcome markers are retained.
- Added `[agent].request_timeout_seconds` (default 300). A timed-out message
  response returns `agent_timeout` while preserving its session ID so it can
  be resumed, attached, or aborted.
- All paths resolve exact desired slugs, require the existing managed SSH
  enrollment, use the existing temporary tunnel context, and obtain endpoint
  and workdir only from controlled nctl configuration.

Verification:

```text
cd nctl && uv run pytest -q --durations=20
1030 passed in 6.29s
```

Adapter coverage uses `httpx.MockTransport` for the pinned paths, normal
responses, missing sessions, timeout-with-session-ID, and interrupt refusal.

## Next step — live verification

The plan requires explicit operator approval before the state-changing live
checks. Those checks have not run yet.
