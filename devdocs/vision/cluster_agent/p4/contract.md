# cluster-agent API contract (Phase 4, frozen)

Frozen at the start of Step 1, per `p4/plan.md` Step 0. This is a **delta
over [p2/contract.md](../p2/contract.md)** (itself a delta over
[p1/contract.md](../p1/contract.md)) — self-standing enough to read alone,
but only the parts that change from Phase 2 are restated here; the
resource/state-machine shapes, error envelope, and node mTLS connect-time
checks are unchanged unless mentioned below. Phase 4 is a breaking change
to evidence's identity shape, as the roadmap and plan both allow.

## Human authentication mechanism

A second HTTPS listener, server-only TLS (no client cert required), guarded
by a single static bearer token — the "second listener + token"
option the plan recommended, chosen as written (mobile client-cert
installation cost was judged not worth it under the single-operator
assumption; see `p4/plan.md`'s "Recommended shape" section for the full
reasoning, not repeated here).

- **Listener**: `CAGENT_HUMAN_PORT`, default `8789`. Server-only TLS
  (`ssl.CERT_NONE`), reusing the same server cert/key as the node listener
  (`:8788`). Runs as a second `build_server()` call sharing the same
  `store`/`worker`/`opencode` objects, on its own thread.
- **Credential**: a random token, generated once on the command node,
  stored in a gitignored file. Path: `CAGENT_HUMAN_TOKEN_FILE`, default
  `~/.local/state/cagent/human_token`. Mode `0600`. The human listener
  **refuses to start** if the file is missing or empty — mirrors
  `start.sh`'s refuse-don't-fallback pattern for the OpenAI key; there is
  no "TLS with no auth" fallback mode.
- **Transport**: the token travels as an `Authorization: Bearer <token>`
  header, checked with `hmac.compare_digest` (constant-time). The login UI
  (Step 2) accepts the token once via a form and stores it in
  `localStorage`, attaching it as a header on every subsequent fetch — no
  server-side session/cookie state, no token embedded in the URL after the
  first paste.
- **No revocation mechanism.** A single static token, rotated by
  regenerating the file and restarting the process, is proportionate to
  one operator on one phone. Multi-operator token management is out of
  scope (roadmap Phase 5 territory, "multi-operator user management").

The node listener (`:8788`) is untouched: still mTLS-only,
`ssl.CERT_REQUIRED`, `auth.CertAuthenticator`. Node connect-time checks
(handshake → ledger → DesiredNode validity) are unchanged from
`p2/contract.md`.

## Identity shape (breaking change)

`store.Identity` becomes class-tagged instead of one fixed shape:

```json
{"class": "node", "uuid": "...", "cert_serial": "..."}
{"class": "human", "name": "operator"}
```

`name` is a fixed, non-secret operator label (not user-supplied at auth
time — the token proves *a* human, not *which* human; single-operator
assumption). Default `"operator"`, overridable via `CAGENT_HUMAN_NAME` for
operator legibility in evidence, not for access control.

This changes evidence bytes for every future request (old evidence
directories keep the Phase 2 `{"class": "node", "uuid", "cert_serial"}`
shape as history — not migrated, per the plan; `scan_and_load` must stay
tolerant of records that have no `name` key and records that have no
`uuid`/`cert_serial` keys, dispatching on the `class` field it does find).

`Identity` gains one derived concept used for ownership comparisons,
`owner_key()`:

- node: `f"node:{uuid}"`
- human: `"human"` (constant — every human-authenticated request is the
  same owner under the single-operator assumption; there is exactly one
  human owner, not one per token holder)

## Session visibility and ownership

- **Node rule, unchanged**: a node sees and can continue/cancel only
  sessions it created (`owner_key()` match).
- **Human rule (new)**: a human-authenticated request may **list all
  sessions** (`GET /sessions`, no filtering) and **read any session's
  requests and any individual request** (`GET /sessions/{id}/requests`,
  `GET /requests/{id}`), regardless of who created it. A human may
  **create** new sessions freely, and may **continue or cancel** only
  sessions whose owner is `"human"` (i.e., sessions the human class
  itself created) — not a node's session. This keeps the door open for
  Phase 5's "human reviews a plan produced in a node's session" without
  building it now: reading a node's session is already possible today,
  only *continuing as if the human owns it* is not.
- Cross-class continue/cancel attempts get the existing `403 forbidden`
  ownership envelope, message updated to reference the owner key mismatch.

## Which listener serves what

- `GET /` (the chat UI, Step 2) and any static assets: **human listener
  only** (`:8789`). The node listener has no use for HTML and gains no new
  routes.
- `/requests`, `/sessions`, `/sessions/{id}/requests`,
  `/requests/{id}`, `/requests/{id}/cancel`: exist on **both** listeners,
  each running its own `authenticate` callable (`CertAuthenticator` on
  :8788, the new `TokenAuthenticator` on :8789). Route handling logic in
  `server.py` is shared — only the injected `authenticate` differs, plus
  the ownership/visibility branch on `identity.identity_class` described
  above.

## Progress display: polling, not SSE

Per the plan's explicit recommendation and the "useful facts" note that
`http.server` + SSE don't mix well (`ThreadingHTTPServer` would pin one
thread per open SSE stream): Step 2 starts with polling only
(`GET /requests/{id}` every 2-3s from the browser, matching the wrapper's
already-proven poll-until-terminal pattern). No SSE endpoint is added in
Phase 4 unless Step 2's own local proof shows polling is actually bad in
practice — if that happens it will be recorded as a plan deviation with
its own contract addendum, not built speculatively here.

## Reachability fact: the URL the phone dials

Confirmed live in Step 0 (see `report0.md`): the VPN is Tailscale with
MagicDNS enabled, tailnet domain `tailab7641.ts.net`. The command node
(agstudio) resolves its own bare hostname `agstudio` via the MagicDNS
search-domain mechanism to `100.94.61.95` (its Tailscale IP). The phone
(`iphone181` in `tailscale status`, offline at Step 0 time but enrolled)
resolves `agstudio` the same way once on the tailnet. Expected human URL:
**`https://agstudio:8789`**.

The current server cert's SANs (`.local/cagent-ca/server_cert.pem`) are
`agstudio.local` + `192.168.0.100` only — bare `agstudio` is not covered.
Step 1/4 re-issues the server cert with `cagent-ca sign-server --dns
agstudio --dns agstudio.local --ip 192.168.0.100` (keeping the existing
SANs so agpc's node-listener dial to `agstudio.local:8788` stays valid;
the same leaf cert now serves both listeners). This is a local,
non-destructive, approval-free action (new leaf cert/key, same CA); the
re-issue itself happens in Step 1's local proof and is re-verified live in
Step 4.

## Out of scope for this contract

SSE (unless Step 2 escalates it, see above), mutation/approval flow
(Phase 5), multi-operator token/session management, per-token revocation,
Go CLI, workspace-level identity, rate limits, session TTLs — unchanged
from Phase 2's "out of scope" list, restated here for completeness.
