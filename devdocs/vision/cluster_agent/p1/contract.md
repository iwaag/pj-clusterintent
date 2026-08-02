# cluster-agent API contract (Phase 1, frozen)

Frozen at the end of Step 1. This is the contract for the loopback MVP only:
no TLS, stub auth, no SSE. Later phases change this contract explicitly
(Phase 2 adds mTLS/identity, Phase 4 adds SSE) — treat any post-freeze edit
in this phase as a noted deviation in the relevant step's report, not silent
drift.

References: [roadmap.md](../roadmap.md), [refined_idea.txt](../refined_idea.txt),
[opencode_api_notes.md](opencode_api_notes.md) (OpenCode primitives this
contract is built on).

## Resources

- **request**: one HTTP call that either starts a new session or continues
  an existing one with a new turn. Identified by `request_id`.
- **session**: an OpenCode session (`sessionID`, OpenCode's own `ses_...`
  ID is reused as the cluster-agent session ID — no separate ID is
  minted). A session accumulates turns.
- **turn**: one prompt/response exchange within a session, corresponding to
  one OpenCode `prompt_async` + its resulting assistant message. A request
  that continues a session creates exactly one new turn.

Turns within a session are serialized (the plan's "session-scoped
serialization" choice — see Step 3 report for which of the plan's two
allowed serialization strategies, session-scoped or global, was
implemented).

## State machine (per request)

```
queued -> running -> completed
                   -> failed
                   -> cancelled
queued|running -> interrupted   (only via restart-scan, see below)
```

- `queued`: accepted, not yet dispatched to OpenCode (waiting for the
  session's turn serialization).
- `running`: dispatched (`prompt_async` returned 204); polling OpenCode for
  completion.
- `completed`: OpenCode's assistant message has `info.time.completed` set
  and no `info.error`.
- `failed`: OpenCode's assistant message completed with `info.error` set
  (and the error is not `MessageAbortedError` — that case is `cancelled`).
- `cancelled`: a cancel request was accepted; OpenCode's abort returned
  `true` and/or the assistant message settled with
  `info.error.name == "MessageAbortedError"`.
- `interrupted`: terminal. Set only by the evidence-scan performed on API
  process startup, for any request found in `queued` or `running` state in
  evidence at scan time. Never set during normal operation. This is what
  makes exit criterion 4 true: a request that was mid-turn when the process
  was killed is `interrupted`, not stuck in `running` and not reported as
  `unknown`.

All five terminal states (`completed`, `failed`, `cancelled`, `interrupted`)
are final — no further transitions.

## Error shape

One JSON envelope for all error responses:

```json
{
  "error": {
    "code": "string, machine-readable, e.g. not_found | bad_request | conflict",
    "message": "string, human-readable",
    "request_id": "string or null (null if the error occurs before a request_id is assigned, e.g. malformed body)"
  }
}
```

Modeled on OpenCode's own `{name, data:{message}}` shape (see
`opencode_api_notes.md`), adapted to include `request_id` since this API's
unit of identity is the request, not the underlying session/message.

## Identity classes

Two identity classes exist: `node` and `human`. Phase 1 only *represents*
the class — it does not authenticate it. The caller declares identity via
request headers:

```
X-Cluster-Agent-Identity-Class: node | human
X-Cluster-Agent-Identity-Name: <free-form string, e.g. a node slug or a human's name>
```

The API validates shape only (class is one of the two enum values, name is
a non-empty string under a small length limit) and records the claimed
identity verbatim in evidence. No cryptographic or credential check backs
this in Phase 1 — Phase 2 replaces this stub with mTLS-derived identity
bound to a DesiredNode UUID, and that replacement is a breaking contract
change, not an extension.

## Authorization rule

All identities, in all classes, receive the same access in Phase 1: reads
(status/drift/relations/guidance) and plan presentation only. No identity
can trigger a cluster mutation through this API. Mutation (`nctl reconcile
--yes`, `nctl desired apply --yes`, or equivalent writes) requires human
approval through a future entrance and is out of scope for every phase-1
endpoint regardless of caller identity class.

## Endpoints

All bodies are JSON. All list/get endpoints are reads. `directory` is never
a caller-supplied parameter — the API always passes its own fixed working
directory (the superproject root) to OpenCode.

### `POST /requests` — create request (new session)

Body:
```json
{"message": "text of the first turn"}
```
Headers: identity headers (required).
Response `202 Accepted`:
```json
{"request_id": "...", "session_id": "...", "state": "queued"}
```

### `POST /sessions/{session_id}/requests` — continue session (new turn)

Body:
```json
{"message": "text of the follow-up turn"}
```
Headers: identity headers (required). The identity must match the identity
that owns the session (Phase 1 "ownership" = same class + name recorded at
session creation; not cryptographically enforced yet — see Phase 2).
Response `202 Accepted`, same shape as above, with the existing `session_id`.

### `GET /requests/{request_id}` — get request status/response

Response `200`:
```json
{
  "request_id": "...",
  "session_id": "...",
  "state": "queued | running | completed | failed | cancelled | interrupted",
  "identity": {"class": "...", "name": "..."},
  "created_at": "...",
  "updated_at": "...",
  "response": "text or null (null until completed)",
  "error": {"code": "...", "message": "..."} 
}
```
`error` present only when `state` is `failed`.

### `POST /requests/{request_id}/cancel` — cancel

No body required. Response `200` with the updated request status (same
shape as GET). Cancelling a request not in `queued`/`running` is a no-op
that returns the current (already-terminal) state, not an error.

### `GET /sessions` — list sessions

Response `200`: array of `{"session_id", "identity", "created_at",
"last_activity_at", "turn_count"}`.

### `GET /sessions/{session_id}/requests` — list requests in a session

Response `200`: array of request status objects (same shape as
`GET /requests/{request_id}`), in turn order. Useful for a human inspecting
a session's full history.

All endpoints are async-by-default per the plan: request-creating endpoints
return immediately with `queued`; the client polls `GET /requests/{id}`.
No SSE, no long-held connections.
