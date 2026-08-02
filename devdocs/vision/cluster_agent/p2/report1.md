# Step 1 report — Contract update

## What was done

Wrote and froze [`contract.md`](contract.md) as a delta over
`p1/contract.md`, covering:

- Identity headers removed; identity is the DesiredNode UUID from the
  verified client cert's SAN (`urn:clusterintent:node:<uuid>`). No request
  body field carries identity in Phase 2.
- `human` identity class stays defined but has no entrance until Phase 4 —
  stated explicitly so its absence isn't misread as removal.
- Evidence identity shape changes from `{"class","name"}` to
  `{"class":"node","uuid","cert_serial"}`.
- Three-step connect/request-time check order: TLS handshake (key
  possession + CA chain + validity window, rejected with no HTTP response
  on failure) → ledger check (serial registered + not revoked, `403
  forbidden`) → DesiredNode validity check (`403 forbidden`, distinct
  message). All three checks run on every request, not just session
  creation, so revocation/pruning take effect immediately.
- Session ownership now enforced by UUID instead of Phase 1's
  class+name comparison.
- One explicit sentence that `nctl prune` is de-facto revocation: ledger
  state and DesiredNode existence are independent gates, either failing
  rejects the request.

Design choices made while writing it, since the plan left them open:

- Kept the ledger-rejection and DesiredNode-rejection under the same HTTP
  status/code (`403 forbidden`) with different messages, rather than
  minting a new error code per cause — Phase 1's error envelope already has
  a `message` field for this, and a new machine-readable code isn't needed
  since no client is expected to branch on which of the two occurred (both
  mean "not authorized," full stop).
- Left the TLS-handshake-failure case explicitly undocumented in the JSON
  error envelope, since it structurally cannot reach one (the connection
  never completes) — stating this plainly rather than inventing a
  hypothetical response shape for something that can't happen.

## Deviations from the plan

None. All Step 1 checklist items (identity, check order, session ownership,
prune-as-revocation sentence, human-class deferral note) are present.

## State

`p2/contract.md` is frozen as of this commit; no code changed yet.

## Next

Step 2 — local CA and signing tooling under `.local/`.
