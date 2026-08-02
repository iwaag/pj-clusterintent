# cluster-agent API contract (Phase 2, frozen)

Frozen at the end of Step 1. This is a **delta over
[p1/contract.md](../p1/contract.md)** — self-standing enough to read alone,
but only the parts that change from Phase 1 are restated here; anything not
mentioned (resources, the request/session/turn state machine, the error
envelope shape, endpoint list and bodies, async-by-default polling) is
unchanged from Phase 1. Phase 2 is a breaking change: the identity-header
stub is deleted, not kept as a fallback.

## Identity

The `X-Cluster-Agent-Identity-Class` / `X-Cluster-Agent-Identity-Name`
headers from Phase 1 are **removed**. A node's identity is the DesiredNode
UUID taken from the verified client certificate's SAN
(`urn:clusterintent:node:<uuid>`, see `p2/mtls_notes.md`). The request
body's node slug/ID is never trusted as identity, and no such field exists
in any Phase 2 request body — the API never reads a client-declared
identity from anywhere but the TLS layer.

The `human` identity class remains defined in principle (it still appears
in evidence/session shapes as a class enum) but has **no entrance in
Phase 2** — there is no authentication path that produces a `human`
identity yet. Its absence here is a deferral, not a removal: Phase 4 gives
it its own authentication (a human device certificate or equivalent) and
its own entrance. Until then, every authenticated request this API accepts
is class `node`.

Evidence's identity field changes shape accordingly, from Phase 1's
`{"class": "...", "name": "..."}` to:

```json
{"class": "node", "uuid": "...", "cert_serial": "..."}
```

`uuid` is the DesiredNode UUID from the cert SAN; `cert_serial` is the
serial of the client cert that authenticated the request (both public
identifiers — no key material, no fingerprint of anything secret).

## Connect/request-time checks, in order

1. **TLS handshake**: proves the client possesses the private key matching
   its certificate, and that the certificate chains to the CA and is
   within its validity window (`not_before`/`not_after`). A handshake
   failure (untrusted CA, expired cert, no cert offered) is rejected at the
   TLS layer — **no HTTP response is produced**; the connection simply does
   not complete. This is not visible to the contract's JSON error envelope
   because it never reaches HTTP.
2. **Ledger check**: once the handshake succeeds, the API extracts the
   cert's serial and looks it up in the auth ledger (`p2/plan.md` Step 3).
   If the serial is not registered, or registered but `revoked`, the
   request is rejected with the Phase 1 error envelope:
   ```json
   {"error": {"code": "forbidden", "message": "certificate not registered or revoked", "request_id": null}}
   ```
   HTTP status `403`. `request_id` is `null` here because rejection happens
   before any request is created.
3. **DesiredNode validity check**: the API confirms the UUID extracted from
   the SAN currently resolves to a valid, non-pruned DesiredNode. If it
   does not (see "prune as de-facto revocation" below), the same `403
   forbidden` envelope is returned, with a message distinguishing the two
   causes (`"certificate not registered or revoked"` vs. `"DesiredNode no
   longer exists"`) for operator legibility, though both are the same HTTP
   status/code.

These three checks run on every request, not just session creation —
ledger revocation or DesiredNode pruning must take effect immediately, not
only at the next session's start.

## Session ownership

Session ownership is now enforced by UUID, not by the Phase 1
"same claimed class + name" comparison. A session created by UUID `X` can
only be continued, listed, or cancelled by a request authenticated as
UUID `X`. A request from a different, validly-authenticated UUID against
someone else's session is rejected with the existing `403 forbidden`
ownership error (same envelope Phase 1 already defined for
`OwnershipError`, message updated to reference UUID mismatch instead of
class/name mismatch).

## `nctl prune` as de-facto revocation

A DesiredNode UUID that no longer resolves via `nctl prune` fails the
connect-time DesiredNode validity check automatically, with no separate
ledger action required. The ledger's `active`/`revoked` state and
DesiredNode existence are two independent gates — either one failing is
sufficient to reject the request — but an operator who prunes a node does
not also need to remember to revoke its certificate for that certificate
to stop working.

## Out of scope for this contract (restated from the plan)

SSE, the human entrance's own authentication, workspace-level identity, key
rotation automation, rate limits, and session TTLs are unchanged from
Phase 1 (i.e., still absent) and are not introduced by this document.
