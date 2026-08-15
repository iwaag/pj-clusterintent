# modernize_cagent p1 — step 2 report: roles `front` and `operator`

## What was built

- `cagent/agents.toml`: `[roles.window]` renamed to `[roles.front]`, new
  `[roles.operator]`, both `profile = "local"`. The `/window` *route* keeps
  its name; only the role renames.
- `agent_runner.build_runner` now keys the strictly-smaller window tool set
  on `role == "front"`, and `main.py` resolves the window door as `front`.
  The listener/API behavior is otherwise unchanged this phase.
- `cagent/src/cagent_api/role_run.py`, on the agforge model:
  - `ROLE_ALLOWED_TOOLS` — `front`: `Read,Write,Edit,Glob,Grep` (writes
    handoff files, no shell, no nctl); `operator`:
    `Read,Glob,Grep,Bash(cagent:*)` (the read-only CLI and nothing else).
  - `tool_environment()` — prepends `cagent/scripts/` to PATH so role runs
    reach `cagent` by bare name.
  - `resolve_cagent_role()` / `run_role()` — resolve against
    `agents.toml` + `.local/agents.local.toml`, run via
    `agag.harness.run_harness`, write the `ag.agent-run.v1` record with
    `agag.harness.write_run_record`.

## Decisions taken en route

- `READONLY_ROLES` (the agcode `--tools read-only` set) exists but is
  **empty**. The hint said the operator "can be read-only", and under
  claude_code its grant is read-only in spirit (no Write/Edit, one Bash
  pattern) — but agcode's `read-only` preset drops the `run` tool entirely,
  which would take the `cagent` CLI away from the operator on the default
  `local` profile. Functionality won; the mechanism stays for future roles.
- This machine's `cagent/.local/agents.local.toml` overlay carries no
  `[roles.*]` key (only `[local.provider.ollama]`), so there was no overlay
  key to update by hand.
- `tests/test_window_server.py` is untouched on purpose: it fakes the runner
  identity and tests the *route*, which keeps its name.

## Verification

- New `tests/test_role_run.py`: both roles carry a claude grant, the front
  has no Bash, the operator's only Bash is `cagent`, neither role is in the
  agcode read-only set, PATH handover, and the run-record write
  (`ag.agent-run.v1`, request_id from the record filename).
- `test_agent_runner.py` updated to the renamed role (`front` resolves, gets
  the window tool set; `human` keeps the wider one).
- `uv run pytest`: 173 passed.
