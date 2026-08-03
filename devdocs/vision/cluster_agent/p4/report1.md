# Step 1 report — Human entrance in cagent-api

## Changes

- `store.py`: `Identity` reworked to the class-tagged shape from
  `p4/contract.md` (`uuid`/`cert_serial` optional, new `name` field for
  humans) with a derived `owner_key()` (`"node:<uuid>"` / constant
  `"human"`). `Store.continue_session` now compares `owner_key()` instead
  of `uuid` directly (uniform across both classes — a node can never
  continue a human session or vice versa, no branching needed there).
  `scan_and_load` gained `_identity_from_record`, tolerant of both the old
  Phase 2 evidence shape and the new class-tagged one, dispatching on the
  `class` field.
- `auth.py`: `TokenAuthenticator` — reads `Authorization: Bearer <token>`,
  compares with `hmac.compare_digest`, returns a `human` identity with a
  fixed operator label. No client cert involved (server-only TLS).
- `server.py`: ownership checks updated to `owner_key()`. Two rule shapes
  per the contract's read-all/continue-own split:
  - `_get_request`, `_list_sessions`, `_list_session_requests` (reads):
    humans bypass the owner filter entirely (see all sessions, read any
    request); nodes are still filtered/rejected to their own owner_key.
  - `_cancel_request` (a mutation): strict `owner_key()` match for
    **both** classes — a human can cancel only human-owned requests, same
    as a node.
  `_continue_session`'s ownership check lives in `Store` and needed no
  server.py change.
- `main.py`: second listener. `_build_human_ssl_context` (server-only TLS,
  `ssl.CERT_NONE`) reuses the same server cert/key as the node listener.
  `_read_human_token` refuses to start (raises `SystemExit`, mirroring
  `start.sh`'s OpenAI-key pattern) if `CAGENT_HUMAN_TOKEN_FILE` (default
  `~/.local/state/cagent/human_token`) is missing or empty. New env vars:
  `CAGENT_HUMAN_PORT` (default `8789`), `CAGENT_HUMAN_TOKEN_FILE`,
  `CAGENT_HUMAN_NAME` (default `operator`). The human listener runs
  `serve_forever()` on its own daemon thread; the node listener keeps
  running in the main thread as before. Both entrances log at startup.
- `evidence_cli.py`: `cmd_list`'s identity column crashed
  (`KeyError: 'uuid'`) on a human record — fixed to print `human:<name>`
  or `node:<uuid>` depending on `identity["class"]`. This is exit
  criterion 3 ("a human request and a node request are distinguishable in
  `cagent-evidence` output") — found and fixed in this step rather than
  deferred, since Step 1 is exactly where the first human-shaped evidence
  records become possible.

## Tests

New/updated, all via the existing fake-authenticate seam (`tests/fakes.py`
gained `FakeHumanAuthenticator`, header-gated like `FakeAuthenticator`):

- `test_auth.py`: 4 new `TokenAuthenticator` cases (correct token accepted,
  wrong token rejected, missing header rejected, non-Bearer scheme
  rejected).
- `test_store.py`: `Identity.as_dict()`/`owner_key()` for both classes,
  node-vs-node owner_key distinctness, human-continues-human-session,
  human-cannot-continue-node-session, node-cannot-continue-human-session.
  Fixed one pre-existing test that constructed `Identity("human",
  "eiji-uuid", "eiji-serial")` — a Phase 2-shaped call with the class
  label swapped, never a valid human identity under either contract; not a
  regression, just a spot the rework changed the meaning of.
- `test_evidence.py`: same pre-existing-test fix (constructed a bogus
  human/uuid identity), updated to assert `identity_class`/`name`.
- `test_evidence_cli.py`: new case, one node + one human record listed
  together, asserts both `node:agpc-uuid` and `human:operator` appear —
  directly exercises exit criterion 3.
- `test_server.py`: new `running_dual_server` fixture (node + human
  listener, both plain HTTP, sharing one store/worker — same wiring
  `main.py` uses for real, minus TLS). 8 new cases: human identity lands
  correctly in evidence via a real request/response round trip, human
  lists all sessions (node's included), human reads a node-created
  request, node is rejected reading a human-created request, human
  rejected continuing a node session, node rejected continuing a human
  session, human rejected cancelling a node request, human can cancel its
  own queued request.

`uv run pytest -q` in `cagent/`: **88 passed** (was 87 going in — net +11
new cases; 2 pre-existing tests edited in place, not counted as new).

## Deviations from the plan

None. Followed the plan's recommended shape (second server-TLS listener +
static bearer token, no client-cert option) as written.

## State

No live processes started; no server cert re-issued yet (deferred to
Step 2's local proof per the contract). No human token file generated yet.

## Next

Step 2 — minimal chat UI served from the human listener, local proof
against `https://localhost:8789` (self-signed warning acceptable locally).
This is also where the server cert gets re-issued with the `agstudio` SAN
added, and the human token file gets generated for the first time.
