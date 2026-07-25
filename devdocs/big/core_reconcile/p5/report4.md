# Phase 5 Report — Step 4 (WebSocket event streaming)

Date: 2026-07-20. Implements [p5/plan.md](plan.md) Step 4 — `WS /api/v1/ws`: authenticated
replay-then-live event streaming over the Step 1 event bus and operation index. This is the
fourth suggested commit boundary. The reference dashboard (Step 5) and the compatibility policy
document (Step 6) remain untouched.

## What was built

### `WS /api/v1/ws` (`nctl_core/serve/app.py`)

- **Handshake auth, before `accept()`.** Same bearer-token check as the REST endpoints
  (`secrets.compare_digest`), read from the `Authorization` header or, as the plan's documented
  fallback for clients that cannot set headers, a `?token=` query parameter. Rejection calls
  `websocket.close(code=4401)` *before* `accept()`, which surfaces to real WS clients as an
  HTTP-level handshake failure (`403` observed live with the `websockets` library) rather than a
  connection that opens and immediately drops.
- **One subscribe message, then replay, then live.** The client's first frame must be
  `{"subscribe": "all" | {"operation_id": "..."}, "after_seq": N}` within 30s or the socket
  closes (`4400`). For a single-operation subscribe, historical records with `seq > after_seq`
  are read from the JSONL file via Step 1's `read_events` and sent first; the bus subscription
  (`nctl_core.events.subscribe`) is registered *before* that file read, so no event emitted in
  the gap between "start reading the file" and "start listening live" is missed — the dedupe set
  below absorbs the resulting overlap instead. `subscribe: "all"` gets no historical replay (`seq`
  is only meaningful per-operation) and fans out only new activity from the moment of
  subscription.
- **Dedupe by `(operation_id, seq)`.** A client that has already seen a replayed record and then
  receives it again live (from the overlap above) gets it exactly once.
- **Frames are exactly the `EventRecord` JSON already written to the file** — no second wire
  schema, per Decision 6/plan Step 4.
- **Bounded internal queue, sentinel-based overflow, not a second Task per tick.** Each
  connection gets one `asyncio.Queue` (`_WS_QUEUE_SIZE + 1` slots). The bus callback runs on its
  own dedicated OS thread (Step 1); it hands records to the connection's asyncio loop via
  `call_soon_threadsafe`, where a small sync function (`_offer`) either enqueues the record or,
  once the queue is at capacity, enqueues a single `_OVERFLOW` sentinel and stops adding more.
  The writer coroutine (`_write_events`) is a single `while True: item = await queue.get()`
  loop — no queue/event pair, no per-iteration task creation — that returns `True` when it
  dequeues the sentinel. The endpoint then closes with `4408` and the documented reconnect
  instruction, matching the plan: "a client that can't keep up is disconnected... rather than
  being buffered unboundedly," with correctness resting on JSONL replay, not the live bus.
- **A concurrent reader task detects client-initiated disconnect.** Since the connection only
  *sends* events, nothing would otherwise notice the client going away; `_drain_incoming` awaits
  `websocket.receive()` in a loop purely to raise `WebSocketDisconnect` on a disconnect message.
  `asyncio.wait({reader, writer}, return_when=FIRST_COMPLETED)` runs both; whichever finishes
  first (client gone, or server-side overflow) ends the connection, and the other task is
  cancelled and awaited (`asyncio.gather(..., return_exceptions=True)`) so no task is abandoned
  mid-cancellation.
- **Heartbeat is the transport's, not a synthetic frame.** `uvicorn[standard]`'s `websockets`
  backend already ping/pongs and drops dead connections at the protocol level; inventing an
  app-level heartbeat JSON message would itself be the "second wire schema" the plan says not to
  add, so none was added. This is a documented interpretation, not a gap: a real dead-socket
  write still surfaces to the app as `WebSocketDisconnect` (Starlette's `send()` converts an
  `OSError` on write to one), which the reader/writer race already handles.
- **`unsubscribe()` runs off the event loop.** It joins the bus subscriber's worker thread
  (Step 1's `_SubscriberEntry.stop`, up to a 5s timeout); doing that inline on the connection's
  coroutine would stall the event loop for every other concurrent connection if one subscriber
  were slow to stop, so it runs via `asyncio.to_thread`.
- **`POST /api/v1/operations` now returns `ws_url`.** Step 3 deliberately omitted it ("wiring a
  link to an endpoint that doesn't exist yet would be misleading"); now that `/api/v1/ws` exists,
  the `202` response includes `"ws_url": "/api/v1/ws"` alongside `events_url`.

## A real concurrency bug, caught by live-style testing before it shipped

The first implementation used a second `asyncio.Event` for overflow, checked via a fresh
`asyncio.wait({queue.get(), overflow.wait()})` pair recreated *every loop iteration* in the
writer. Under `starlette.testclient.TestClient`'s real threaded portal (a genuine second OS
thread running the ASGI app, not `httpx.ASGITransport`'s single-threaded shortcut used by the
rest of the serve suite), this hung indefinitely under load: `send_json` calls sometimes never
returned, and the whole connection stalled with no error. Isolating it (see below) showed the
two-tasks-per-iteration pattern was the trigger — cancelling and abandoning a same-purpose Task
every tick, mixed with a second synchronization primitive, left dangling waiters that could
desync the loop under real cross-thread timing (not reproducible under `ws_debug.py`'s
single-threaded harness, only under the multi-thread `TestClient`/`anyio` portal path — i.e.
exactly the kind of bug that would also bite a real browser client). The fix was the design
actually shipped: **one queue, a sentinel value instead of a second synchronization primitive,
and a plain `while True: await queue.get()` loop** — no repeated Task churn. This is why Step 4
took materially longer than Steps 1–3: the bug only appeared under genuine multi-thread
scheduling, so it had to be root-caused with instrumented standalone repros
(`asyncio.get_running_loop()` capture, `call_soon_threadsafe` firing, and queue state all traced
by hand) rather than in the final test suite.

A second discovery from the same investigation: **`TestClient`'s in-process ASGI transport never
backpressures on send** (its outbound channel is an `anyio` memory stream with infinite buffer),
so a "flood N events and expect overflow" test is not just slow but can be *permanently
non-deterministic* — the writer, sharing a GIL-bound event loop with the bus's dedicated OS
thread, reliably drained every one of 400 flooded events through a queue of size 1 in this
environment, never overflowing. `tests/test_serve_ws.py`'s overflow test therefore monkeypatches
`_WS_QUEUE_SIZE` down to `0` so the very first live event is guaranteed to overflow deterministically,
rather than racing scheduling. This is a test-design note, not a production concern: a real
socket's write genuinely blocks under backpressure, which is exactly the scenario the sentinel
design exists to bound.

## Tests

- `tests/test_serve_ws.py` (10 tests, using `starlette.testclient.TestClient.websocket_connect`
  — `httpx.ASGITransport`, used elsewhere in the serve suite, has no WebSocket support):
  - auth rejected pre-accept (`4401`) and both the header and `?token=` fallback accepted;
  - replay-then-live continuity for one operation (historical `seq`s first, then a live emit,
    then `finished`, all delivered in order);
  - reconnect-from-`after_seq` with no gap or duplicate across a simulated disconnect;
  - `subscribe: {operation_id}` ignores other operations' events; `subscribe: "all"` fans out
    across operations;
  - two concurrent clients on the same operation both receive the same live event (fanout);
  - a malformed `subscribe` message closes with `4400`;
  - the overflow/slow-consumer path closes with `4408` (via the `_WS_QUEUE_SIZE=0` monkeypatch
    above);
  - disconnecting a client actually stops its bus subscription (`events_module._subscribers`
    empties out — no leaked subscriber thread per connection);
  - `POST /api/v1/operations` now returns `ws_url`.
- Full suite: **491 passed** (`UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q`, ~3.7s). Step 3
  had 481; this step adds 10.
- `git diff --check`: clean.

## Live verification against the real cluster config

Started the real server against the checked-in `nctl.toml` (`NAUTOBOT_TOKEN` +
`NCTL_SERVE_TOKEN`, port 18302) and drove it with a small Python client (`httpx` for the POST,
the `websockets` library for the WS side — both already transitive deps via `uvicorn[standard]`):

```text
POST /api/v1/operations {"op":"drift"} -> 202 {"operation_id":..., "ws_url":"/api/v1/ws"}
WS   /api/v1/ws?token=... subscribe {"operation_id":...} after_seq -1
  -> EVENT seq 0 started
  -> EVENT seq 1 finished (failed)
```

Observed:

- The drift op again reported `ok: false` with `nautobot_fetch_failed`/`Connection reset by
  peer` talking to Redis via `host.docker.internal` — the same pre-existing local dev-environment
  issue noted in Step 3's report, unrelated to this change; the event stream itself faithfully
  carried both `started` and `finished` end to end over the real socket.
- WS auth rejection surfaced to a real client (`websockets` library) as an HTTP `403` at
  connect time, not a connect-then-drop — confirms the pre-`accept()` close behaves as a proper
  handshake rejection outside the test harness too.
- **Reconnect/replay proven live**: subscribed, captured only `seq 0`, disconnected, let the
  operation finish unobserved, reconnected with `after_seq` set to the last seen `seq`, and
  received exactly the missed `finished` record — no gap, no duplicate.
- **Multi-client fanout proven live**: two concurrent `subscribe: "all"` clients against a second
  drift operation both observed its `finished` event.
- Server shut down cleanly (`pkill` + confirmed the port stopped answering).

Step 8 remains the designated place for the full mutating-reconcile-under-load live pass and the
kill/restart-mid-observation check called for in the plan; this step's live verification stayed
within the same read-only scope Step 3 used, now exercised through the WS path instead of just
REST polling.

## Deliberate boundaries and notes for Step 5+

- No synthetic heartbeat frame; see above. If a future subscriber needs an app-level liveness
  signal distinct from transport keep-alive, that is new scope, not something silently missing
  from this step.
- `subscribe: "all"` never replays history (only per-operation `seq` cursors are meaningful for
  replay); a dashboard or UI that wants "everything since I was last connected" must still
  subscribe per-operation or poll `GET /api/v1/operations`.
- The overflow threshold (`_WS_QUEUE_SIZE = 256`) is an internal implementation constant, not
  configuration — this phase's scope is correctness of the disconnect-and-reconnect contract, not
  tuning throughput.
- The reference dashboard (Step 5) is the natural next real exerciser of this endpoint from a
  browser; nothing here is dashboard-specific, per Decision 8's "no backend changes for new
  subscribers."

## Suggested commit boundary

- nctl: `/api/v1/ws`, the `ws_url` addition to `POST /api/v1/operations`, and
  `tests/test_serve_ws.py`.
- parent: this report plus the updated nctl submodule pointer after the nctl commit is created.
