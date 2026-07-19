# Phase 5 Report — Step 5 (Reference live dashboard)

Date: 2026-07-20. Implements [p5/plan.md](plan.md) Step 5 — one static, build-toolchain-free
HTML page served at `GET /` that validates the Step 2-4 API by being its first real consumer.
This is the fifth suggested commit boundary. The compatibility policy document and schema
snapshot tests (Step 6) remain untouched.

## What was built

### `GET /` — the live dashboard route (`nctl_core/serve/app.py`, `serve/dashboard.py`)

- `render_live_dashboard_html()` reads a static package resource
  (`nctl_core/serve/live_dashboard.html`) and returns it verbatim — no server-side templating,
  no embedded envelope JSON, no token. This is the deliberate contrast with the Phase 3 static
  dashboard (`dashboard/html.py`), which embeds a drift envelope at generation time; the Phase 5
  page is identical on every request and fetches everything client-side.
- `GET /` is registered **unauthenticated**, alongside `/api/v1/health` — not because it's part
  of the "only unauthenticated API endpoint" contract line (that line is scoped to `/api/v1/*`),
  but because the page cannot require a token to load the page that is where a human enters the
  token in the first place. Nothing sensitive is served: the HTML is static markup and JS source
  containing the literal string `"Bearer "` used to build a header, never an actual token value.
- `nctl_core/serve/runtime.py` already computed `dashboard_url=f"http://{host}:{port}/"` back in
  Step 2, anticipating this exact path — no change needed there.

### `live_dashboard.html` — the page itself

One self-contained file (inline CSS + vanilla JS, no build step), reusing the Phase 3 static
dashboard's exact visual language (CSS variables, status chips, tile/diff layout) copied
verbatim from `dashboard/template.html` so a human moving between the static and live dashboards
sees the same drift presentation:

- **Token entry**: a password-type input + "connect" button. The token is written to
  `sessionStorage` (cleared when the tab closes, never `localStorage`) and attached as
  `Authorization: Bearer <token>` on every REST call and as `?token=` on the WebSocket handshake
  (the documented fallback for clients that cannot set headers — browsers' native `WebSocket`
  constructor is exactly such a client). The token never appears in the HTML response itself.
- **Initial render**: `GET /api/v1/drift` (tiles, severity/status chips, error panel — identical
  rendering code to the Phase 3 page, just re-fetched instead of embedded) and
  `GET /api/v1/operations?limit=20` (sidebar).
- **Live updates**: subscribes `{"subscribe": "all", "after_seq": -1}` on `/api/v1/ws`. On any
  `finished` / `drift_resolved` / `observation_completed` event, it refreshes the operations
  sidebar and, for `drift`/`reconcile`/`dashboard` ops specifically, re-fetches drift — per
  Decision 8's event list verbatim. Every incoming event frame is also appended to that
  operation's tail buffer *if the sidebar already knows about the operation* (i.e. it's been
  selected at least once), keeping memory bounded (capped at 300 events/op) without silently
  dropping events for the operation currently on screen.
- **Operations sidebar**: recent operations with state/result, colored by running vs.
  finished-ok vs. finished-failed; clicking one loads its full event tail via
  `GET /api/v1/operations/{id}/events` and continues appending live events for it afterward.
- **Two actions, both just POSTs**: "refresh drift" (`{"op": "drift"}`) and "reconcile (plan)"
  (`{"op": "reconcile", "params": {"host": ...}}` with no `yes`, so it is always plan-only — an
  optional host field narrows scope, mirroring the CLI's `nctl reconcile [HOST]`). No apply
  button exists anywhere on the page, matching Decision 8's "applying reconcile stays CLI-only in
  this phase."
- Uses only the endpoints in the plan's API contract table (`/api/v1/drift`,
  `/api/v1/operations`, `/api/v1/operations/{id}/events`, `POST /api/v1/operations`,
  `/api/v1/ws`) — nothing new was added to the API surface to make this page work, which is the
  point of Decision 8's validation framing.

## Tests

- `tests/test_serve_dashboard.py` (4 tests): `GET /` returns `text/html` unauthenticated and
  byte-identical to `render_live_dashboard_html()`; the served page contains neither the
  configured token value nor any embedded envelope schema string
  (`nctl.drift.v1`/`nctl.ops.list.v1`); the page references the documented API paths
  (`/api/v1/drift`, `/api/v1/operations`, `/api/v1/ws`); the render function is stable across
  calls (no per-request randomness to catch regressions on).
- Full suite: **495 passed** (`UV_CACHE_DIR=/tmp/nctl-uv-cache uv run pytest -q`, ~3.7s). Step 4
  had 491; this step adds 4.
- `git diff --check`: clean.

## Live verification against the real cluster config

Started the real server against the checked-in `nctl.toml` (`NAUTOBOT_TOKEN` +
`NCTL_SERVE_TOKEN=smoke-test-token-p5s5`, port 18305):

```text
GET  /                                     -> 200 text/html; no token/envelope-schema substring present
GET  /api/v1/drift        (Bearer token)   -> 200, real cluster drift (agpc/agstudio converged,
                                               agdnsmasq/aghub unknown — matches Step 3/4 reports)
POST /api/v1/operations {"op":"drift"}     -> 202 {"operation_id":...}
WS   /api/v1/ws?token=... subscribe "all"  -> observed the POSTed operation's "finished" event
                                               live, end to end (Python client using `httpx` +
                                               `websockets`, the same libraries Step 4 used)
GET  /api/v1/operations?limit=3            -> 200, recent operations list (sidebar data source)
GET  /api/v1/operations/{id}/events        -> 200, full event tail (sidebar detail view source)
POST /api/v1/operations {"op":"reconcile",
      "params":{"host":"agpc"}}            -> 202, mutating:false (plan mode, as the page always sends)
POST ... with a wrong bearer token         -> 401 unauthorized
```

Every REST/WS call the page's JS makes was individually exercised against the live server and
returned the shape the JS expects. Server shut down cleanly (`pkill` + confirmed the port stopped
answering). Opening the page in an actual browser from a second LAN machine and eyeballing the
live tile updates is deferred to Step 8 per the plan's own scoping (that step is the designated
place for the full "open from a second machine on the LAN" and kill/restart-mid-observation
checks); this step's verification proved the page's API usage is correct and complete against the
real cluster, which is what "a game-engine UI can be built on top without backend changes" is
actually testing for.

## Deliberate boundaries and notes for Step 6+

- No apply/`yes=true` control anywhere in the page, by design (Decision 8).
- `subscribe: "all"` never replays history (Step 4's own documented limitation) — the sidebar's
  per-operation event tail is fetched via the REST replay endpoint on selection instead, so
  switching to an operation the client hasn't been live-subscribed to since connecting still
  shows its full history.
- The page has no reconnect/backoff loop for the WebSocket itself (a dropped connection shows
  "disconnected" in the header but does not auto-retry). Nothing in the plan's Step 5 scope calls
  for this, and Step 8's "kill and restart the server mid-observation" check is the natural place
  to decide whether it's needed.
- The Phase 3 static dashboard (`nctl dashboard`) is completely untouched — no shared code was
  modified beyond copying its CSS/JS pattern into the new file, per the plan's explicit "the
  static artifact and its file/LAN hosting remain untouched."

## Suggested commit boundary

- nctl: `serve/dashboard.py`, `serve/live_dashboard.html`, the `GET /` route in `serve/app.py`,
  and `tests/test_serve_dashboard.py`.
- parent: this report plus the updated nctl submodule pointer after the nctl commit is created.
