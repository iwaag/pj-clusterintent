# OpenCode 1.18.10 server-mode API notes (verified 2026-08-02)

Verified by running the pinned binary (`~/.local/bin/opencode`, v1.18.10, the
same version `ansible_agdev/roles/opencode_agent` installs) as
`opencode serve --hostname 127.0.0.1 --port 14096` from the superproject root
and driving it with curl. Full OpenAPI document is at `GET /doc`.

## Startup quirk

`opencode serve` prints `Error: Unexpected error / ServeError` to stderr on
every start observed in this environment, even with a minimal config and
regardless of working directory, yet the HTTP server comes up correctly
afterwards (`GET /global/health` returns `{"healthy":true,"version":"1.18.10"}`
immediately). Treat this line as benign/cosmetic for this pinned version —
do not gate readiness on absence of that line; poll `/global/health` instead.

## Two API generations coexist

The OpenAPI doc exposes both a legacy surface (`/session`, `/session/{id}/...`)
and a newer `/api/session/...` v2 surface. This phase uses the **legacy
surface** — it is simpler, matches the roadmap's request/response shape, and
is what the proven node-agent sample targets implicitly (same binary/serve
invocation). The two surfaces appear to operate on the same underlying
sessions (both are exposed by the same process/DB), so mixing them is
possible but out of scope; stick to one.

## Endpoints used (legacy surface)

- `POST /session?directory=<abs path>` — create a session. Body:
  `{"title": "..."}` (optional). Response includes `id` (`ses_...`),
  `directory`, `projectID`. **`directory` must be passed as a query
  parameter on creation** (and again on every subsequent call for that
  session) or OpenCode defaults to `~/agent-work`, not the caller's cwd —
  important for Step 2's requirement that the agent run in the superproject
  root.
- `POST /session/{sessionID}/prompt_async?directory=<abs path>` — send a
  turn without blocking. Body: `{"parts":[{"type":"text","text":"..."}]}`.
  Returns **204 No Content** immediately; the turn runs in the background.
  This is the async-by-default primitive the contract should build on.
- `POST /session/{sessionID}/message?directory=<abs path>` (same path, but
  this is the **synchronous** `session.prompt` — it blocks until the turn
  finishes and returns the assistant message). Useful for manual testing,
  not for the API server (which must stay async).
- `GET /session/{sessionID}/message?directory=<abs path>` — list all
  messages (user + assistant) with parts. Poll this after `prompt_async`.
  Completion signal: the assistant message's `info.time.completed` field
  becomes present (absent while running). `info.parts` contains
  `step-start` / `reasoning` / `text` / `tool` / `step-finish` parts in
  order; the final answer is the last `type:"text"` part's `text`.
- `POST /session/{sessionID}/abort?directory=<abs path>` — reliably aborts
  an in-flight turn. Verified: sent a long-running prompt, aborted ~1s
  later, response `true`, and the assistant message settled with
  `info.completed` set and `info.error = {"name":"MessageAbortedError",
  "data":{"message":"Aborted"}}`. This is a clean, reliable signal — no
  fallback to "mark cancelled and abandon" is needed for Phase 1.
- `GET /session/status?directory=<abs path>` — returned `{}` in all states
  observed (idle and mid-turn); not useful as a per-request status source.
  Use per-message `info.time.completed` / `info.error` instead.
- Error shape (404 case verified): `{"name":"NotFoundError","data":
  {"message":"Session not found: ses_..."}}`. Consistent
  `{name, data:{message}}` envelope; use this shape as the model for the
  cluster-agent API's own error envelope, or wrap it 1:1.

## Multi-turn continuity

Verified: two turns in the same session, second turn ("What is my favorite
number?") correctly recalled a fact stated in the first turn ("42"). Session
continuation works with no extra parameters beyond reusing `sessionID`.

## Tool execution / PATH gotcha

Asking the agent to run `uv run --project nctl nctl status --help` inside a
session failed with `uv: command not found`, even though `uv` is on the
interactive shell's `PATH` (`/opt/homebrew/bin/uv`). The `opencode serve`
process does not inherit the launching shell's interactive `PATH` for its
tool-execution environment (or uses a minimal one). **Step 2 must either put
`uv`'s directory on the `PATH` the launchd/service definition sets, or the
system prompt must call `uv` by an absolute path** (e.g.
`/opt/homebrew/bin/uv run --project nctl nctl ...`). Recorded here so Step 2
does not rediscover it live.

## Session storage on disk

Sessions are **not** stored as plain files. With `XDG_DATA_HOME` overridden,
OpenCode created `$XDG_DATA_HOME/opencode/opencode.db` (SQLite, WAL mode:
`opencode.db-wal`/`opencode.db-shm`) plus `$XDG_DATA_HOME/opencode/repos/`
and `$XDG_DATA_HOME/opencode/log/opencode.log`. Relevant tables (via
`sqlite3 opencode.db .tables`): `session`, `session_message`, `message`,
`part`, `project`, `project_directory`, `workspace`, `event`, `permission`,
`credential`, `account`, `todo`, among others.

**Storage isolation for Step 2**: set `XDG_DATA_HOME` (and `XDG_CONFIG_HOME`
for the config file) to a cluster-agent-only directory, distinct from any
node-agent's default `~/.local/share`/`~/.config`. This was suffient to get
a fully isolated instance in this research (separate port, separate DB, no
interference with the default global instance) — no other isolation
mechanism was needed.

## Config

Config file resolution order observed (from startup log): `$XDG_CONFIG_HOME/
opencode/config.json` (not present), then `opencode.json`, then
`opencode.jsonc`. A minimal working config for a non-interactive/reachable
Ollama backend:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "ollama/<model>",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://<host>:11434/v1" },
      "models": { "<model>": {} }
    }
  }
}
```
Reused the existing node-agent's `opencode.json.j2` template shape and the
already-reachable `agstudio.home.arpa:11434` Ollama endpoint from the global
config for this research; Step 2 picks its own model per the plan's "free
choice" note.

## Conclusion for contract design (Step 1)

- Map cluster-agent `queued`/`running` → not directly observable from
  OpenCode (it has no separate "queued" concept; a `prompt_async` call
  starts immediately or 404s). The cluster-agent API owns `queued` for
  cases where our own server serializes turns before dispatching to
  OpenCode; `running` begins once `prompt_async` returns 204.
- Map cluster-agent `completed`/`failed` → poll `GET .../message`, use the
  latest assistant message's `info.time.completed` presence and
  `info.error` absence/presence.
- Map cluster-agent `cancelled` → call `POST .../abort`; verified reliable,
  confirmed via `info.error.name == "MessageAbortedError"`.
- Map cluster-agent `interrupted` → OpenCode itself has no notion of this;
  it is entirely the cluster-agent API's responsibility (own evidence-side
  state, scanned on restart), independent of what OpenCode's DB shows for
  the underlying message (which will simply stay stuck without a
  `completed` timestamp forever if the process is killed mid-turn).
