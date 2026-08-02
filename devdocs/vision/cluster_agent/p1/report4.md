# Step 4 report — Durable evidence

## What was done

Added `cagent/src/cagent_api/evidence.py` (`EvidenceWriter`), same shape as
`nctl ops`'s `~/.local/state/nctl/events/<operation_id>/`:
`<evidence_dir>/<request_id>/request.json` (identity, session ID, message,
created time — written once) plus an append-only
`<request_id>/events.jsonl` (one line per state transition:
`{"ts", "state", "detail"}`, `detail` carrying the terminal response text
or error). Default location `~/.local/state/cagent/evidence`, overridable
via `CAGENT_EVIDENCE_DIR`, mirroring nctl's own `log_dir` convention.

Wired it into `store.py` rather than keeping it a separate write path: `Store`
now takes an optional `EvidenceWriter` and calls it synchronously, inside
the same lock, on every request creation and every state-changing
`update_request` — so the durable copy and the in-memory copy can never
observably diverge. Added a module-level `scan_and_load(evidence)` that
rebuilds a full `Store` (sessions, requests, ownership) purely from what's
on disk, and — this is exit criterion 4 — marks any request whose latest
recorded event is not one of `completed`/`failed`/`cancelled`/`interrupted`
as `interrupted`, appending that as a new durable event before the request
is ever served again. `main.py` now calls `scan_and_load` before starting
the worker or HTTP server, so a restarted process never re-dispatches a
stuck turn.

Added a minimal human-inspection CLI, `cagent-evidence list` /
`cagent-evidence show <request_id>`, reading evidence directly off disk
(does not require the API process to be running) — satisfies the plan's
"list/inspect surface for a human" requirement.

7 new tests (`tests/test_evidence.py`, total now 23 passing): evidence
correctly recorded through a full queued→running→completed lifecycle,
`scan_and_load` marking a stuck `running` request `interrupted` while
leaving a genuinely completed sibling in the same session untouched, empty
evidence dir producing an empty store, and — a specific edge the exit
criterion's wording calls out — a request that never got past `queued`
(never dispatched at all) also reloads as `interrupted`, not `unknown` or a
404.

## Live verification (not just unit tests)

Started the real stack (`opencode/start.sh` + `cagent-api`), created a
request designed to run long (an intentionally slow generation), confirmed
it reached `running`, then `kill -9`'d the API process mid-turn (the
OpenCode instance kept running underneath, untouched). Restarted
`cagent-api`: startup log printed `marked 1 non-terminal request(s) as
interrupted`; `GET /requests/<id>` returned `state: "interrupted"`;
`cagent-evidence show <id>` displayed the full event trail
(`queued → running → interrupted`) with real timestamps, read straight off
disk. This is the literal exit criterion 4 scenario, verified live, ahead
of the more scripted Step 5 pass.

## Deviations from the plan

None. Built inside the same `cagent/` project as Step 3 rather than as a
separate top-level thing, per the plan's explicit allowance ("This can be
built inside Step 3 rather than as a separate commit... keep the report
boundary either way") — kept as its own commit/report per the house style
default.

## State

Evidence code is committed. The live verification run left one real
evidence directory under `~/.local/state/cagent/evidence/` (one
`interrupted` request) — left in place deliberately as the exit-criterion
proof, the same way `nctl ops` evidence is left in place after a real run;
it is outside the repo and contains no secrets (just the identity stub and
message text). Both dev processes were stopped after verification.

## Next

Step 5 — full end-to-end curl verification of every scenario in the plan
(new request → poll → continue → cancel → kill/restart → evidence
inspection), captured as a saved transcript.
