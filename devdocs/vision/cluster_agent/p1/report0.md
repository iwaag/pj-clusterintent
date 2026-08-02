# Step 0 report — Research: OpenCode server-mode/session API

## What was done

Ran the pinned `opencode` 1.18.10 binary already installed at
`~/.local/bin/opencode` (matches `ansible_agdev/roles/opencode_agent`'s
pinned version) as `opencode serve --hostname 127.0.0.1 --port 14096` from
the superproject root, with `XDG_CONFIG_HOME`/`XDG_DATA_HOME` overridden to a
scratch directory for isolation. Drove it with curl only. Findings written to
[`opencode_api_notes.md`](opencode_api_notes.md).

Verified end-to-end:

- Session creation (`POST /session?directory=...`), with the discovery that
  `directory` must be passed as a query parameter or the agent silently runs
  in `~/agent-work` instead of the caller's cwd.
- Async turn dispatch (`POST /session/{id}/prompt_async`, 204 immediately)
  and polling (`GET /session/{id}/message`) until the assistant message's
  `info.time.completed` appears.
- Multi-turn continuity within one session (a fact stated in turn 1 was
  correctly recalled in turn 2).
- Reliable abort (`POST /session/{id}/abort`): an in-flight long turn was
  aborted ~1s in, response `true`, and the assistant message settled with
  `info.error.name == "MessageAbortedError"`. No fallback ("mark cancelled
  and abandon") is needed for Phase 1's Step 3.
- Error envelope shape on a 404 (`{"name":"NotFoundError","data":
  {"message":"..."}}`) as a model for the cluster-agent's own error shape.
- Session storage location: SQLite (`$XDG_DATA_HOME/opencode/opencode.db`),
  not plain files — relevant to Step 2's storage-isolation requirement
  (set `XDG_DATA_HOME`/`XDG_CONFIG_HOME` per instance; no other isolation
  mechanism was needed in this test).

Also surfaced a real gotcha for Step 2: a shell tool call inside a session
(`uv run --project nctl ...`) failed with `uv: command not found` even
though `uv` is on the interactive shell's `PATH`. `opencode serve` does not
inherit the launching shell's `PATH` for tool execution. Step 2 will need to
either fix the service's `PATH` or call `uv` by absolute path in the system
prompt.

One cosmetic finding: `opencode serve` always prints `Error: Unexpected
error / ServeError` to stderr on this pinned version regardless of config,
but the server comes up correctly afterwards — documented so it isn't
mistaken for a real failure later.

## Deviations from the plan

None. All Step 0 hints were followed (used the pinned 1.18.10 version, did
not research against floating latest).

## State

Scratch server process was stopped; scratch config/data directories were
temporary (under the session scratchpad, not committed). Nothing in the repo
runs a live process as a result of this step.

## Next

Step 1 — freeze `p1/contract.md` using the endpoint/state-machine mapping at
the end of `opencode_api_notes.md`.
