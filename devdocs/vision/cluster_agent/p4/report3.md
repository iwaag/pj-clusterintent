# Step 3 report — Conformance test + gates

## Conformance test

Extended `devtests/test_strategy/test_mtls_conformance.py` (not a sibling
module — same fixture class, same throwaway CA, one process, matching the
plan's "or a sibling module reusing its throwaway CA/server fixture"
option chosen as the simpler of the two). `_Fixture` now stands up a
**second** real TLS listener (`self.human_httpd`, server-only TLS,
`ssl.CERT_NONE`, `TokenAuthenticator`) sharing `self.store`/`self.worker`
with the existing node listener — same wiring `main.py` uses in
production, minus the process split. Added `human_request()` (no client
cert loaded at all) and `request_node_without_client_cert()` helpers.

One pre-existing fixture bug surfaced immediately: `_FakeOpenCode.
create_session` always returned the fixed literal `"ses_conformance"`.
Every earlier test used only one identity per test so this never
collided; the new dual-listener tests create sessions from both node and
human identities in the same test, and a fixed session ID meant the
second `create_session_and_request` call silently overwrote the first
session's `Store` entry (reassigning its owner instead of creating a
second session — a fixture defect, not a `cagent_api` defect, but the
kind that would have made the human-sees-all-sessions test falsely
"pass" against a store with only one session in it). Fixed to
`f"ses_conformance_{uuid.uuid4().hex[:8]}"`; note it needed to be UUID-
based rather than a per-instance counter, since the fixture builds one
`_FakeOpenCode` per listener and a counter starting at 1 in each would
still have collided across listeners.

10 new cases, covering exactly the plan's Step 3 checklist:

- node mTLS path still works unchanged with the human listener present
  (re-run of the file's very first test, both listeners up)
- node listener refuses a cert-less connection (`ssl.SSLError` at
  handshake, not an HTTP-level rejection)
- human listener accepts the good token / rejects a bad token (401) /
  rejects an absent token (401)
- human listener does not require a client cert (the connection itself
  succeeds — proven by getting a real `200`, not an `SSLError`, from a
  helper that never loads a client cert)
- human and node identities land in evidence in their contract shapes
  (`{"class": "node", "uuid", "cert_serial"}` vs.
  `{"class": "human", "name": "operator"}`), read back through
  `GET /requests/{id}` on the real TLS stack
- human reads a node-created request but is rejected continuing it
  (403); node is rejected reading a human-created request (403) — the
  cross-class ownership rule, both directions
- human's `GET /sessions` lists both identities' sessions; node's
  `GET /sessions` lists only its own
- human listener serves the chat UI HTML at `GET /`

`uv run --project cagent pytest -q devtests/test_strategy/test_mtls_conformance.py`
(from the superproject root, per the file's own header comment):
**23 passed** (was 13; +10).

## Docs

- `README_DEV.md`'s mTLS conformance gate row: description widened from
  "A cagent TLS/ledger trust" to "A cagent TLS/ledger trust + human
  bearer-token entrance"; artifacts note now says "node + human
  listeners"; the "required when" clause now also triggers on the human
  token/session-visibility boundary. Same row, same command — no new gate
  file, the existing one grew.
- `cagent/README.md`: rewrote the server-config section to describe both
  entrances (`:8788` mTLS / `:8789` bearer token), added the three new
  env vars (`CAGENT_HUMAN_PORT`, `CAGENT_HUMAN_TOKEN_FILE`,
  `CAGENT_HUMAN_NAME`) to the table, added a "Human token setup" snippet
  (generate the token file, then paste it into the UI's login form once),
  updated the `cagent-ca sign-server` example to `--dns agstudio --dns
  agstudio.local` with a comment explaining why both SANs live on one
  leaf cert, and updated the start-order paragraph to note `cagent-api`
  now brings up both listeners in one process and logs both URLs.

## Tests

`uv run pytest -q` in `cagent/`: **90 passed** (unchanged from Step 2 —
this step touched the conformance test and docs, not `cagent_api` code).
`uv run --project cagent pytest -q devtests/test_strategy/test_mtls_conformance.py`:
**23 passed** (was 13).

## Deviations from the plan

None substantive. Extended the existing file rather than adding a sibling
module (the plan offered both as acceptable); the fixture bug fix above
was necessary, unplanned, in-step work, same house pattern as p3 Step 0's
live-discovered fix.

## State

No live processes running. No code changes to `cagent_api` itself this
step — only test/doc changes.

## Next

Step 4 — the smartphone proof over VPN. Needs the user (their phone, their
VPN profile); nothing in this step mutates the cluster, so it's the
natural pause point per the plan.
