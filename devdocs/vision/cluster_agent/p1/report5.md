# Step 5 report — End-to-end verification with curl

## What was done

Ran the full plan scenario (new request → poll → continue → cancel →
kill/restart → evidence inspection) from the command node with curl only,
`--data @file` for every body. Full transcript with real IDs/timestamps:
[`e2e_transcript.md`](e2e_transcript.md).

1. Created a request as identity class `node` with the plan's exact example
   question ("I want S3-compatible storage - what exists in this
   cluster?"). The agent ran real `nctl status`/`relations --json`/`drift
   --json` plus repo greps and answered correctly: no S3-compatible storage
   currently exists — cross-checked independently against a direct `nctl
   relations --json` call at the time (only `ollama`/`node-agent` edges, no
   S3/MinIO service).
2. Polled to `completed`, retrieved the response.
3. Continued the same session; the agent correctly recalled its prior
   conclusion without re-running any tools (context retained).
4. Cancelled an in-flight request (a deliberately slow essay-writing
   prompt); confirmed terminal state `cancelled`.
5. `kill -9`'d the API process mid-turn (a real kill, not graceful
   shutdown), restarted it, queried the same request ID: `interrupted`, not
   `unknown`.
6. Confirmed evidence directories for every one of the five terminal
   states this run produced (`completed`, `failed`, `cancelled`,
   `interrupted` — plus a second `completed`), each with identity, message,
   session ID, timestamped state transitions, and final response/error, via
   both raw `GET` and the `cagent-evidence` CLI. Also exercised `GET
   /sessions` and `GET /sessions/{id}/requests`.

All exit criteria from `plan.md` are now met:

1. Frozen contract exists (`contract.md`, Step 1).
2. curl-only: new request → response retrieval → session continuation →
   cancel — all demonstrated above.
3. Evidence remains on disk per request, readable after the fact
   (`cagent-evidence`, or direct `ls`/`cat` on `~/.local/state/cagent/evidence/`).
4. Killing the API process mid-turn and restarting reports the in-flight
   request as `interrupted` — demonstrated with a real `kill -9`.

## Deviations from the plan / bugs found and fixed during this step

- **Real bug, fixed**: the worker's turn-completion detection (from Step 3)
  tracked "a new assistant message appeared and is completed" as the
  signal a turn was done. A real multi-step tool-calling turn produces
  *several* assistant messages — one per step — each independently
  `completed`; only the last one has OpenCode's `finish` field equal to
  something other than `"tool-calls"`. Under the right timing this could
  make the worker conclude a turn was finished after just its first tool
  call, returning an empty response mid-turn. Reproduced live during this
  step's first scenario (observed the real message sequence:
  `finish: "tool-calls"` on 4 steps, `finish: "stop"` only on the 5th).
  Fixed by adding `AssistantMessage.is_final_step` (true unless
  `finish == "tool-calls"`, or the step ended in an error/abort) to
  `opencode_client.py`, checked alongside `completed` in `worker.py`.
  Added `test_multi_step_turn_does_not_complete_early` and a
  `push_intermediate_step` fake helper (`tests/fakes.py`) to lock this in;
  suite is now 25 tests, all passing. This fix predates and is included in
  this step's commit rather than Step 3's, since it was found here.
- **Real bug, fixed**: `main.py`'s startup log said "marked N non-terminal
  request(s) as interrupted" by counting every request *currently*
  `interrupted` after a scan, not just the ones transitioned *by that
  scan* — so a second restart with nothing new stuck would misleadingly
  repeat the same warning. `scan_and_load` now returns
  `(store, newly_interrupted_ids)`; the log only fires for genuinely new
  transitions. Covered by a new `test_scan_and_load_does_not_redouble_already_interrupted`
  test.
- **Real, expected outcome, not a bug**: the first "continue session"
  attempt (a broader "what's the fastest way to get S3 storage" question)
  triggered a long multi-step repo investigation on the local
  `glm-4.7-flash` model and legitimately exceeded the worker's 300s
  `TURN_TIMEOUT_SECONDS`, producing a real `failed`/`timeout` evidence
  entry (see the transcript). This validates the Step 3 timeout guard
  actually fires under real, non-adversarial conditions, not just in the
  fake-backed unit test — confirms the bound is doing useful work, though
  a production-shaped follow-up might want it configurable per-request
  rather than a single process-wide constant (left as-is for this MVP;
  not required by any exit criterion).

## State

`p1/e2e_transcript.md` is committed as the saved transcript. The worker/log
fixes are committed as part of this step (touching `cagent/src/cagent_api/{opencode_client,worker,main,store}.py`
and `cagent/tests/{fakes,test_worker,test_evidence}.py`). Both dev processes
were stopped after verification; the real evidence produced during this
run remains under `~/.local/state/cagent/evidence/` as further proof
alongside the transcript.

## Phase 1 status

All five steps and all four exit criteria are complete. `cluster_agent`
Phase 1 (contract freeze + loopback MVP) is done. Phase 2 (node
authentication / mTLS) is the next roadmap phase, not started.
