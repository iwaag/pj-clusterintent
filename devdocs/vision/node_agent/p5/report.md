# Node Agent — Phase 5 Report

Status: complete (2026-07-31).

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

## Step 3 — live verification

Operator approval was received before the state-changing checks. All commands
used the managed SSH tunnel and the configured workdir; no endpoint or SSH
option came from argv.

| Check | Evidence |
|---|---|
| Session list | `nctl agent sessions agpc --json` listed known session `ses_048032980ffewkvz6U06YkJJ6P` with its Phase 2 title. |
| Start and continue | `nctl agent run agstudio` created `ses_047d3080cffenb7sM4bm3LDF64` (operation `01KYW2SXJZ15M030WDEXB38XX6`) and wrote the exact `phase5-run` marker. `nctl agent send` continued that same session (operation `01KYW2TF7NK72ZQA6B1RPGP0CN`) and read the marker back. |
| Abort proof | The dedicated sleep-then-write session `ses_047d27081ffeCvPwVsCxXg8K9W` was interrupted by `nctl agent abort` (operation `01KYW2VERS9XV1P7R16T8NN2X1`, HTTP 204 accepted). After more than the requested 30 seconds, `.p5-abort-marker.txt` was absent. The ordinary live marker was then verified and removed. |
| Failure shape | `nctl agent sessions no-such-node --json` returned the structured `unknown_host` error with no tunnel or node action. |

The first abort attempt exposed two OpenCode timing details that the API
document alone did not establish: message POST can acknowledge before the
remote task starts, and a completed-looking assistant message can have no text
parts. The adapter now polls the node-local message stream for a new completed
text response. It reports `agent_interrupted` when an active session stops
before that response, and `agent_reply_missing` after a short inactive grace
period. The initial probe files were removed before the successful retry; all
final probe artifacts are absent. The validated temporary SSH processes also
exited; no forwarding tunnel remained.

## Step 4 — close

The run/send envelopes now record controller-configured runtime version
`1.18.10`, model `ollama/qwen3.6:35b-a3b-coding-nvfp4`, operation ID, node,
session ID, timing, and outcome. Prompt/reply text remains out of the durable
operation log.

Final verification:

```text
cd nctl && uv run pytest -q --durations=20
1034 passed in 8.62s
```

## Carried limitation

OpenCode may produce a no-text assistant record while becoming inactive. This
is reported as `agent_reply_missing` rather than leaving a controller wait
running until the full reply timeout. Diagnosis remains available through the
session ID with `sessions`, `attach`, or the node-local runtime.
