# Step 4 report — Smartphone proof over VPN (exit-criteria run)

## What happened

1. Command node had the Step 2 artifacts already in place: server cert
   with the `agstudio` SAN (re-issued in Step 2, still valid,
   `not_after=2027-08-03`), human token file
   (`~/.local/state/cagent/human_token`, 44 bytes). No re-issue/regen
   needed this step.
2. Confirmed the phone (`iphone181`) was reachable on the tailnet — it
   initially showed `offline, last seen 65d ago`; the user reconnected it
   and `tailscale status` then showed it live.
3. Started `./cagent/opencode/start.sh` and `cagent-api`. One snag: a
   stray `cagent-api` process from Step 2's local proof was still bound
   to `:8788`/`:8789` — Step 2's `pkill -f "cagent_api.main"` had not
   matched the actual process command line (`.../cagent/.venv/bin/
   cagent-api`, not a literal `cagent_api.main` string), so it never
   died. Found via the `OSError: [Errno 48] Address already in use`
   startup failure, killed by PID, restarted cleanly. Not a code defect —
   a shell pattern-matching gap in the stop step, now known for future
   sessions.
4. Verified the human listener reachable from the command node itself via
   both the tailnet IP (`https://100.94.61.95:8789/` → `200`) and the
   MagicDNS name (`https://agstudio:8789/` → `200`) before involving the
   phone.
5. User, on the phone: opened `https://agstudio:8789/`, clicked through
   the self-signed certificate warning, entered the token, and drove a
   real 3-turn conversation (greeting, a model self-identification check,
   then a substantive question that pulled and summarized a real
   braindump entry). User confirmed live: "素晴らしい、braindumpの概要を
   説明させることに成功しました。"
6. Cross-checked from the command node: `cagent-evidence list` shows the
   session's three requests as `human:operator`, interleaved with
   pre-existing `node:<uuid>` entries — exit criterion 3, live, not just
   in a test. `GET /sessions/{id}/requests` pulled via `curl` reproduces
   the same three turns/answers the phone displayed, byte-for-byte.
   Full exchange saved as `p4/e2e_transcript.md`.
7. Stopped both manually started processes (`opencode serve`,
   `cagent-api`) — confirmed via `lsof` on ports 8788/8789/4097 that
   nothing remained bound.

## Exit criteria — all three met, live

1. New request from a VPN-connected smartphone browser works, response
   readable — yes.
2. Follow-up turns in the same session work from that browser — yes (2
   follow-ups in one session).
3. Evidence distinguishes entrance/identity class — yes
   (`human:operator` vs. `node:<uuid>` in `cagent-evidence list`, and the
   class-tagged `identity` field on every request record).

## Deviations from the plan

None to the plan's own steps. The stray-process kill above was an
operational hiccup in *my* prior session cleanup, not a plan deviation —
noted here so the pattern (`pkill -f "cagent_api.main"` doesn't match
`uv run --project cagent cagent-api`'s actual argv) doesn't repeat; a more
robust stop command would be `pkill -f "cagent/.venv/bin/cagent-api"` or
just `lsof -ti :8788,:8789 | xargs kill`.

## State

No live processes running. Server cert, human token file, and CA material
remain on the command node under `.local/cagent-ca/` and
`~/.local/state/cagent/` (both gitignored), per the plan's stated exit
state — nothing here needs to be committed or is committed.

## Roadmap status

All four `p4/plan.md` exit criteria are met and live-verified. Phase 4
("the human (smartphone) entrance") is **complete**. The human entrance
is reads/plan-presentation only, same restriction as the node entrance —
no mutation/approval path was added, matching the roadmap's explicit
scope rule for this phase. Phase 5 (mutation-approval flow through this
entrance, Go CLI, rate limits, etc.) starts only when a concrete
complaint appears, per the roadmap.
