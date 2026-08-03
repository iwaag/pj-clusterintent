# Step 0 report — Wrapper interface decision + local prototype

## Decided interface

- **Commands**: `cagent ask [--no-wait]` (new session, body from stdin),
  `cagent continue SESSION_ID [--no-wait]` (follow-up turn, body from
  stdin), `cagent status REQUEST_ID` (one fetch, no polling). `ask`/
  `continue` wait (poll `GET /requests/{id}` every `CAGENT_POLL_INTERVAL`
  seconds, default 3s, up to `CAGENT_POLL_MAX` iterations, default 200 ≈
  10 min) by default; `--no-wait` prints the raw `202` body and returns.
- **Config**: `~/.cagent/client.conf`, plain `KEY=VALUE`, sourced with
  `. "$CAGENT_CONF"`. Keys: `CAGENT_API_URL`, `CAGENT_CA_CERT`,
  `CAGENT_CLIENT_CERT`, `CAGENT_CLIENT_KEY` (defaults match Phase 2's
  `~/.cagent/{ca_cert,node_cert,node_key}.pem` on agpc), plus optional
  `CAGENT_POLL_INTERVAL`/`CAGENT_POLL_MAX` overrides.
- **Language**: POSIX `sh`, `curl` only required. `jq` is used when present
  (`command -v jq`) for both encoding the outgoing `{"message": ...}` body
  and decoding responses; when absent, an `awk`+`sed` pipeline JSON-escapes
  the stdin body for encoding, and `grep`+`sed` extract the handful of
  top-level scalar fields (`request_id`, `session_id`, `state`) needed to
  drive the poll loop. `response`/`error.message` text is only unescaped
  with `jq`; without it the wrapper prints the raw JSON object for the
  terminal state, matching the plan's "raw JSON is acceptable, the
  consumer is an agent" allowance.
- Body always via `--data @file` (a temp file written by `mktemp -d`,
  cleaned by an `EXIT` trap), never inline argv.

Committed to `ansible_agdev/roles/cagent_client/files/cagent`.

## Local prototype

Enrolled the **command node itself** (agstudio, DesiredNode UUID
`dc6dede2-9615-4236-b8e6-fd4df45c51bb`, resolved from
`ansible_agdev/inventories/generated/production.yml`) as a throwaway
client, following the same procedure as p2/report5b.md's agpc enrollment
but entirely local: `openssl ecparam`/`openssl req` for the key+CSR,
`cagent-ca sign-node --uuid dc6dede2-...`, `cagent-ledger register`. Started
`./cagent/opencode/start.sh` (port 4097, isolated from any node-agent
instance) and `cagent-api` on `127.0.0.1:8799` (the existing
`.local/cagent-ca/server_cert.pem` SANs are `agstudio.local`/
`192.168.0.100`, both of which resolve to loopback here via mDNS and the
host's own IP).

Verified against the live stack, real TLS, real OpenCode turns (not
`--check`/mocked):

1. `cagent ask` (waits) with a real question ("I want S3-compatible
   storage") — `202` → polled to `completed` in ~24s, answer correctly
   grounded in `nctl drift`/`relations` output (no S3-compatible storage;
   named the actual deployed services).
2. `cagent continue SESSION_ID` — follow-up turn in the same session,
   correctly grounded answer about the Ollama service placement.
3. `cagent status REQUEST_ID` — single fetch of the still-completed turn.
4. `cagent ask --no-wait` — prints the raw `202` body immediately.
5. All four repeated with `jq` removed from `PATH` (a scratch directory of
   symlinks to only the tools the wrapper needs) — encode, poll-decode, and
   terminal-state printing all work without `jq`.
6. Revoked the throwaway cert (`cagent-ledger revoke`) — `cagent status`
   now correctly fails with a non-zero exit and the `403 forbidden`
   envelope on stderr. Reactivated, repeated a request successfully, then
   revoked again for final cleanup.

## Real bug found and fixed during this step

Two independent bugs, both found live, both fixed and covered by new
regression tests in the same step (README_DEV "breaking-change phase, fix
don't accumulate" + the p2 Step 5b precedent of folding a live-discovered
fix into the step that found it):

1. **Non-jq field extraction didn't tolerate `json.dumps`'s default
   space-after-colon separator** (`"state": "queued"`, not
   `"state":"queued"`). The wrapper's `grep`/`sed` pattern assumed no
   space and silently extracted empty strings. Fixed the pattern to allow
   optional whitespace around the colon.

2. **A real auth/authorization gap in `cagent-api` itself**, unrelated to
   the wrapper but found while testing the revoked-cert case against the
   live stack: `server.py`'s `_get_request` (`GET /requests/{id}`),
   `_cancel_request` (`POST .../cancel`), `_list_sessions`
   (`GET /sessions`), and `_list_session_requests`
   (`GET /sessions/{id}/requests`) never called `self._identity()` at all.
   Concretely, this meant:
   - A **revoked** certificate (or one for a since-pruned DesiredNode)
     could still poll any request's status/response and cancel any
     request indefinitely — contradicting `p2/contract.md`'s explicit
     "these three checks run on every request, not just session creation."
     Reproduced live: after `cagent-ledger revoke`, a raw `curl` to
     `GET /requests/{id}` with the revoked cert still returned `200
     completed` with the full answer text.
   - Any client holding **any** CA-signed cert (registered or not, active
     or not) could call `GET /sessions` and enumerate **every** session
     from **every** node, and `GET /requests/{id}` to read **any** other
     node's question/answer, or cancel it — a cross-node information
     disclosure and integrity gap, since none of these four handlers
     checked identity or ownership at all. The existing test suite had
     never caught this because its own calls to these routes passed no
     headers and asserted success — the tests encoded the bug as expected
     behavior.

   Fixed in `cagent/src/cagent_api/server.py`: all four handlers now call
   `self._identity()` (so a revoked/unregistered/DesiredNode-invalid cert
   is rejected the same as at creation), and enforce UUID-ownership —
   `_get_request`/`_cancel_request` reject a request-identity mismatch
   with `403 forbidden`; `_list_session_requests` does the same for session
   mismatch; `_list_sessions` filters the returned list to the caller's
   own sessions rather than rejecting (a node listing its own sessions is
   normal; the fix is that it no longer sees anyone else's). Updated the
   existing `cagent/tests/test_server.py` calls to these routes to pass
   identity headers, and added 5 new regression tests (missing-identity
   401, ownership-mismatch 403 for get/cancel/list-session-requests,
   list-sessions excludes other identities). Added one more case to the
   real-TLS `devtests/test_strategy/test_mtls_conformance.py`
   (`test_revoked_serial_is_rejected_on_status_poll_not_just_creation`)
   proving this against an actual TLS handshake + ledger, not just the
   fake-authenticator unit tests.

This fix was necessary before proceeding to Step 3 (live distribution):
shipping a wrapper that depends on the API's auth boundary while that
boundary silently accepted revoked/foreign credentials on most of its
endpoints would have validated a false security property.

## Deviations from the plan

None to the wrapper interface. The server.py fix above is additional,
unplanned but necessary work — not a p2/contract.md *change* (the fix
brings the implementation into line with what the frozen contract already
specified), so no contract document edit was needed.

## State

`uv run pytest -q` in `cagent/`: **70 passed** (was 65; +5
`test_server.py` regression tests). `uv run --project cagent pytest -q
devtests/test_strategy/test_mtls_conformance.py`: **7 passed** (was 6; +1
revoked-on-poll regression case), confirmed passing 3 consecutive runs
after an initial run showed unrelated transient flakiness (isolated
reruns of the same tests were consistently green; not pursued further as
it did not reproduce). No live process left running; the throwaway
command-node ledger entry is `revoked` (not deleted, for the record).

## Next

Step 1 — automated test driving the actual wrapper script against the
mTLS conformance fixture (`ask` with wait, `status`, revoked-cert
rejection).
