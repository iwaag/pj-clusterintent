# Step 1 report — Contract freeze

## What was done

Wrote and froze [`contract.md`](contract.md), covering resources
(request/session/turn), the state machine (`queued -> running -> completed
| failed | cancelled`, plus restart-only `interrupted`), one JSON error
envelope modeled on OpenCode's own `{name, data:{message}}` shape (with
`request_id` added), the `node`/`human` identity-class stub via headers, the
reads-only authorization rule, and five endpoints: create request, continue
session, get request, cancel, list sessions, list a session's requests.

Design choices made while writing it, since the plan left them open:

- **Request vs. session vs. turn IDs**: reused OpenCode's own `sessionID`
  directly as the cluster-agent session ID rather than minting a separate
  one — no translation layer needed, and it keeps evidence directly
  correlatable with OpenCode's own session data if ever needed for
  debugging.
- **Turn serialization scope**: contract states turns are serialized
  per-session but explicitly defers to the Step 3 report which of the
  plan's two allowed strategies (session-scoped vs. global) gets
  implemented, since that's an implementation choice the plan says to
  record at Step 3, not freeze here.
- **`cancel` on an already-terminal request**: made it a no-op returning
  current state rather than an error, since "cancel something that already
  finished" is a normal race in an async API, not a client mistake.
- **Session ownership check in Phase 1**: identity match is checked but not
  cryptographically enforced (no auth backing it yet) — documented
  explicitly as a Phase 2 gap rather than silently implying it's secure now.

## Deviations from the plan

None. Endpoint list matches the plan's requirement (create, get, continue,
cancel, list) plus one extra read (`GET /sessions/{id}/requests`) added for
the Step 5 human-inspection requirement ("a list/inspect surface for a
human is required but minimal" — Step 4 scope, but the endpoint shape
belongs in the contract).

## State

Contract is frozen (committed). No process changes; this step is
documentation only.

## Next

Step 2 — stand up a dedicated OpenCode instance for the cluster-agent,
applying the Step 0 findings: pass `directory` explicitly, isolate
`XDG_CONFIG_HOME`/`XDG_DATA_HOME`, and fix the `PATH` gotcha so `uv` is
reachable from tool calls.
