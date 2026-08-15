# modernize_cagent p1 — step 3 report: topic serving

## What was built

- `cagent/src/cagent_api/topics_serve.py` — cagent's handler for `cagent-`
  topics in any subscribed channel, on `agag.topics.serve_topic` (ack first,
  always answer, `failed during <step>`, re-serve when a human spoke during
  the run). Per serving: `topic_workspace(.local/topics, channel, topic)` →
  `next_generation` → `<N>/front/`, `chatlog.md` via `format_chatlog` (own
  sweep acks dropped), prompt = `chatlog_placement(bot_name)` +
  `agent/guides/front/guide.md` via `prompt_with_guide`, front run through
  `role_run.run_role` (record under `.local/agent/front/run-NNNN.json`), and
  the front's answer posted immediately — before any handoff, since the
  operator can take minutes.
- The handoff skeleton (`handle_handoffs`) is in place with the operator
  branch working; the `requested_change.md` branch calls into
  `cagent_api.plane`, which lands in step 4.
- `cagent/src/cagent_api/zulip_window.py` — the existing listener process
  (`com.clusterintent.cagent-zulip`) now runs two threads, mirroring
  agforge: the DM → `POST /window` path unchanged on a side thread, and
  `agag.zulip.sweep_serve(topic_filter=("cagent-",))` on the main thread.
  `CAGENT_ZULIP_LOG_ONLY=1` observes both sides without spending a run.

## Decisions taken en route

- Workspace and records live under the superproject's `.local/`
  (`.local/topics/`, `.local/agent/`), beside cagent's other local state —
  the listener's launchd working directory is the superproject root.
- `SWEEP_ACK` keeps the shared wording ("Message received. Please wait for
  the reply."); only it is dropped from the chatlog, and only when this bot
  posted it — a human quoting the ack stays conversation.
- Timeouts: front 360 s (reads and writes text), operator 900 s (each nctl
  call can take up to 120 s).

## Verification

- New `tests/test_topics_serve.py`, mirroring agforge's
  `test_create_topic.py` (fake runner, real tmp workspace): front-only path
  posts ack then answer and builds no operator dir; the front prompt is the
  placement line plus its guide; a failure names its step; generations
  increment and old ones are kept; an empty topic costs no run; ack-dropping
  and its human-quote exception; a missing guide refuses to start.
- `uv run pytest`: 181 passed.
