# Step 2 report — Minimal chat UI

## UI

`cagent/src/cagent_api/static/chat.html` — single file, inline CSS/JS, no
framework, no build step, ~12.4 KB served as-is. Login screen (token input
→ `localStorage`), then: session-list drawer (`GET /sessions`, click to
reopen via `GET /sessions/{id}/requests`), "New chat" button, a scrollable
transcript (`<div>` bubbles, not `<pre>` — same effect via `white-space:
pre-wrap` so long tool-heavy answers wrap instead of overflowing
horizontally on a phone), a textarea + Send. Every request renders its
state explicitly (`queued`/`running` → "Thinking… (state)"; `failed` shows
the error message; `cancelled`/`interrupted` get their own readable
strings) and polls `GET /requests/{id}` every 2.5s until terminal — no SSE,
per the frozen contract. `Authorization: Bearer <token>` is attached on
every fetch; a `401` anywhere clears the stored token and returns to the
login screen. Viewport meta tag + `min-height: 40px` tap targets for
phone-first use, per the plan.

`server.py`: `make_handler`/`build_server` gained `serve_ui: bool = False`.
`GET /` is served (200, `text/html`, unauthenticated — the page has no
data of its own, only the API calls it makes need the token) only when
`serve_ui=True`; `main.py` passes that only for the human listener's
`build_server()` call, so the node listener gets no new route (`GET /`
there still 404s, proven by test).

## Local proof (live, command node = agstudio)

1. Generated the human token (`~/.local/state/cagent/human_token`, 44
   bytes, `chmod 600`).
2. Re-issued the server cert with `cagent-ca sign-server --dns agstudio
   --dns agstudio.local --ip 192.168.0.100` — new SANs confirmed via
   `openssl x509 -text`: `DNS:agstudio, DNS:agstudio.local, IP
   Address:192.168.0.100`. Non-destructive as the contract predicted (new
   leaf cert/key only, same CA).
3. Started `./cagent/opencode/start.sh` (port 4097) and `cagent-api`
   (both listeners: `https://0.0.0.0:8788` node/mTLS,
   `https://0.0.0.0:8789` human/bearer-token — confirmed from the startup
   log line).
4. `GET https://localhost:8789/` → `200`, `text/html; charset=utf-8`,
   12440 bytes, contains `<title>cluster-agent</title>`.
5. Unauthenticated `POST /requests` on the human listener → `401
   unauthorized` (`missing bearer token`), confirming the UI's fetch
   wrapper's 401-handling path has something real to react to.
6. **Full round trip**, driven with `curl`/Python reproducing exactly the
   HTTP calls `chat.html`'s JS makes (see "what wasn't tested" below):
   - `POST /requests` with a real question ("What services are deployed
     on agpc right now, per nctl status?") → `202 queued`.
   - Polled `GET /requests/{id}` — observed `running`, then `completed` in
     well under the plan's ~221s tool-heavy estimate. Answer: correctly
     grounded (`nctl status` doesn't report services, points to `nctl
     drift --host agpc` instead) — the agent read real repo state, not a
     canned reply.
   - Follow-up: `POST /sessions/{session_id}/requests` in the same
     session ("OK, run nctl drift --host agpc and summarize.") → polled
     to `completed`: "agpc is converged... comfyui-agpc, node-agent-agpc,
     swarmui-agpc" — correct, grounded, and using the session's prior
     context (it re-ran drift instead of asking what "it" meant).
   - `GET /sessions/{id}/requests` for that session → 2 requests, matching
     the two turns.
7. `GET /sessions` on the human listener returned **17 sessions**: 16
   pre-existing `class: node` sessions from Phase 2/3 plus the one new
   `class: human` session just created — confirms the human-listens-all
   rule against real accumulated history, not just fresh test data.
8. Sanity-checked the node listener is untouched: a plain (no client cert)
   connection to `https://localhost:8788/requests` fails at the TLS
   handshake (`curl` reports connection failure, HTTP code `000`) exactly
   as Phase 2 behavior requires — `CERT_REQUIRED` still in effect.
9. `cagent-evidence list` tail shows the new request lines as
   `human:operator ses_03a30814...` interleaved with existing
   `node:<uuid> ses_...` lines — exit criterion 3, live.
10. Stopped both manually started processes (`opencode serve`,
    `cagent_api.main`) — house pattern, nothing left running.

### What wasn't tested

This shell environment has no way to drive an actual GUI browser and
observe rendering, so "open the UI in a desktop browser" was not literally
done — no screenshot, no visual confirmation of layout/CSS. What *was*
verified is the complete backend contract the JS depends on: every fetch
call sequence the page's `send()`/`pollUntilTerminal()`/`loadSessions()`/
`loadSession()` functions make was reproduced byte-for-byte (same paths,
same headers, same body shapes) against the live stack, end to end,
including a real multi-turn conversation. The HTML/CSS/JS itself was
reviewed by hand, not runtime-verified in a renderer. Step 4 (an actual
phone browser) is where visual/interaction confirmation happens; if
anything is visually broken there, it gets fixed as part of that step.

## Tests

`test_server.py`: 2 new cases (`GET /` returns the chat HTML on the human
listener; `GET /` 404s on the node listener), `running_dual_server`
fixture updated to build the human httpd with `serve_ui=True`.

`uv run pytest -q` in `cagent/`: **90 passed** (was 88; +2).

## Deviations from the plan

None. Polling only, as specified; no SSE added.

## State

Live processes stopped. `.local/cagent-ca/server_cert.pem` /
`server_key.pem` now carry the `agstudio` SAN (persists on disk, reused by
Step 4 — re-verified there, not reissued again unless something changes).
`~/.local/state/cagent/human_token` now exists (persists, gitignored,
reused by Step 4). Evidence directory grew by 2 real requests from this
step's live proof (kept as evidence, not cleaned up — same as prior phases'
practice).

## Next

Step 3 — conformance test extending
`devtests/test_strategy/test_mtls_conformance.py` (or a sibling module)
with the human listener under real TLS, plus README_DEV/cagent/README.md
doc updates for the new env vars and two-entrance start order.
