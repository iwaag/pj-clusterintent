# Phase 5 Step 8 — items needing a human decision

Found during live verification ([report8.md](report8.md)); not resolved by the agent because each
needs either physical access this session doesn't have, or a judgment call about scope/design that
the plan explicitly deferred rather than settled.

## 1. Decide the fate of the SIGINT/crash-during-mutation gap

**What was confirmed live**: `nctl serve`'s mutating operations run on `daemon=True` worker
threads (`serve/runner.py`). If the server process is interrupted (`SIGINT`) or dies while one is
in flight, the thread is killed with it. The operation's JSONL file is left holding only its
`started` event forever — no `finished`, no `result.json`, no error record. `GET
/api/v1/operations/{id}` and `nctl ops show` both report `state: "running"` indefinitely, with no
way to distinguish "still actually running" from "the server that was running it is long gone."

This was already flagged as a known gap in `p5/report2.md` and `p5/report3.md`, both of which
explicitly punted the decision to this step ("remains open for Step 8's live verification pass").
Step 8 confirmed the gap is real but is not itself scoped to fix it (verification, not
implementation). Two ways forward:

- **Accept as a documented limitation** for this experimental, breaking-changes-allowed phase.
  Add a line to `plan.md`'s "Out of scope" section and/or `docs/compatibility.md` noting that a
  `state: running` record with no recent activity may indicate an abandoned operation from a prior
  server process, and that operators should treat a long-stale `running` state as informational
  only. Cheapest option; matches the roadmap's "experimental system" posture.
- **Close it properly**: catch `SIGINT`/`SIGTERM` in `run_server()` (`serve/runtime.py`), and on
  shutdown mark any still-`running` operation's JSONL with an explicit terminal `interrupted` event
  (mirroring "same semantics as CLI Ctrl-C in Phase 4" from the plan's Step 2 bullet) before uvicorn
  exits. A hard `kill -9` still can't be caught (no signal fires), so this only closes the graceful
  `SIGINT`/`SIGTERM` path, not an actual crash — worth deciding whether that partial fix is
  worthwhile or whether "operator restarts, sees a stale `running` record, ignores it" is fine
  everywhere.

Needs a decision on which of these (or something else) before Phase 5 is considered closed, since
neither `plan.md` nor `docs/compatibility.md` currently say anything about this either way.

## 2. Second-LAN-machine live dashboard check

The plan's exit criteria and Step 8 checklist both call for opening the reference dashboard
(`GET /`) from a **second machine on the LAN** with `[serve].host` bound non-loopback, and watching
a running operation update the page live. This session has no second machine to do that from, and
changing `[serve].host` to bind non-loopback / opening it to the LAN is a network-exposure change
this agent didn't make unilaterally.

To close this out:

1. On this machine, set `[serve].host` in `nctl.toml` (or `nctl serve --host 0.0.0.0`) and start
   `nctl serve` with a real token.
2. From another device on the same LAN, open `http://<this-machine-IP>:8300/`, paste the token when
   prompted, and trigger a `drift` or plan-mode `reconcile` refresh from a third terminal (or the
   page's own buttons) while watching the second machine's browser update live.
3. If it works, this line item is done — no code changes expected, this is pure observation. If
   anything about the page fails against a real cross-machine WS connection (CORS, mixed-content,
   etc.) that unit tests and same-machine `curl`/`websockets` checks in `report8.md` couldn't catch,
   that's new information for a follow-up fix.

## 3. Whether to actually expose `nctl serve` on the LAN going forward

Everything in Step 8 ran against `127.0.0.1` only, by design (this agent doesn't change network
exposure without being asked). Whether/when to actually bind `[serve].host` to a LAN address for
routine use (vs. only for the one-off check in item 2) is a decision about this homelab's real
network posture — worth deciding once, and worth choosing a real token storage location
(`token_file` pointing somewhere durable, not the ad-hoc scratch value this session generated and
discarded) at the same time.
