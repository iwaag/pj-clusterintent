# Step 3 report — cluster-agent API server (loopback MVP)

## What was done

New top-level project `cagent/` (uv project, stdlib-only — no web
framework, since the surface is six routes and the plan discourages
building a big harness for a loopback MVP):

- `src/cagent_api/opencode_client.py` — thin client wrapping the legacy
  OpenCode endpoints from Step 0/2 (`create_session`, `prompt_async`,
  `list_messages`/`count_assistant_messages`/`latest_assistant_message`,
  `abort`), stdlib `urllib` only.
- `src/cagent_api/store.py` — in-memory request/session state machine per
  `contract.md` (`queued -> running -> completed|failed|cancelled`),
  session ownership by identity, thread-safe via a single lock. Explicitly
  in-memory only for this step — the contract's "state lives on the
  evidence side" requirement is Step 4's job.
- `src/cagent_api/worker.py` — single background thread draining one
  `queue.Queue` for **all** sessions (global serialization — the plan's
  "acceptable and simpler for now" option, chosen over per-session queues;
  recorded in the module docstring since the contract deferred this choice
  to this report). Dispatches `prompt_async`, polls by tracking the
  assistant-message count before/after the call (avoids a race where the
  *previous* turn's already-completed assistant message is mistaken for
  the new one), maps completion/error/abort to `completed`/`failed`/
  `cancelled`, and calls `abort` when a cancel is requested mid-turn.
  Includes a `TURN_TIMEOUT_SECONDS` (300s) bound with abort-and-fail on
  expiry — added because Step 2 proved OpenCode can retry a broken backend
  connection forever without ever settling a message, which would
  otherwise wedge the single global queue permanently, not just one
  request.
- `src/cagent_api/server.py` — `http.server.ThreadingHTTPServer` router for
  the six contract endpoints, identity header validation (shape only, per
  contract), the frozen error envelope.
- `src/cagent_api/main.py` — entrypoint (`uv run --project cagent
  cagent-api`), env-var configuration (`CAGENT_API_HOST/PORT`,
  `CAGENT_OPENCODE_URL`, `CAGENT_DIRECTORY`, defaulting to the superproject
  root).
- `cagent/README.md` — start order and configuration (required by uv's
  build backend anyway, but also the natural place to document this).

Tests (`cagent/tests/`, 19 cases, `uv run pytest -q --durations=20` from
`cagent/`): a `FakeOpenCodeClient` (`tests/fakes.py`) standing in for the
real HTTP boundary — covers the full state machine (complete, OpenCode-call
error, assistant-reported error, cancel-while-running with a verified
`abort` call, cancel-while-queued with a verified *no* dispatch, the new
turn-timeout path, and global serialization — a second session's request
provably stays `queued` while the first is `running`), the store's ownership
and not-found errors, and HTTP-level behavior (identity validation 400s,
create→poll→complete, ownership 403 on session continuation, 404 shape
with `request_id` populated, session/request listing).

Beyond the fake-backed test suite, ran the real stack end-to-end (Step 2's
`opencode/start.sh` + `uv run --project cagent cagent-api`, both against
the live local Ollama) over curl: create → poll → `completed` with a real
`nctl status` answer; a follow-up turn on the same session that correctly
referenced the prior answer; and cancelling an in-flight long-generation
request, confirmed to reach `cancelled` (matching the OpenCode `abort`
reliability found in Step 0 — no fallback "mark cancelled and abandon" was
needed here either).

## Deviations from the plan

None structural. One addition beyond the letter of the plan: the
`TURN_TIMEOUT_SECONDS` bound described above. The plan lists "session
TTLs" as out of scope for Phase 1, but that's a different concern (limiting
how long a session may live) from this (preventing one wedged backend call
from blocking the single global worker forever) — added because Step 2
demonstrated the failure mode is real, not hypothetical.

## State

`cagent/` is a new uv project with a lockfile (`uv.lock`), not yet
committed at the time of writing this report — committed together with it.
Nothing is left running; both the OpenCode instance and the API server used
for live verification were stopped after the checks above.

## Next

Step 4 — durable evidence: replace/extend the in-memory `Store` so request
state is written to `<evidence_dir>/<request_id>/` as the durable copy, and
add the on-startup scan that marks any non-terminal request `interrupted`
(exit criterion 4).
