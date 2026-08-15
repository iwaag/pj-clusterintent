# modernize_cagent p1 — step 1 report: the `cagent` CLI (Tool Giving)

## What was built

- `cagent/src/cagent_api/readonly_nctl.py` — the read-only nctl surface,
  extracted from `agent_runner.py` and defined once: the allow-list
  (`NCTL_SUBCOMMANDS`/`NCTL_SWITCHES`/`NCTL_OPTIONS`), `validate()`,
  `run_nctl()`, the in-process tool `nctl_readonly()`, and its `NCTL_SPEC`.
  `agent_runner.py` now imports the tool instead of defining it.
- `cagent/src/cagent_api/cli.py` — the `cagent` console script (registered in
  `pyproject.toml`). Subcommands `status`, `drift`, `relations`, `actual`,
  `ops list`, `ops show ID`, with the flags the allow-list already admits.
  Every `description=` is written for the agent reader; `--help` is the whole
  usage information. After argparse, the composed argv still passes the shared
  `validate()` — the parser and the allow-list cannot drift apart silently.
- `cagent/scripts/cagent` — the shim subagents reach by bare name
  (`cd` to the cagent project, `exec uv run cagent "$@"`), same shape as
  agforge's `scripts/agforge`. `tool_environment()` that prepends it to PATH
  lands in step 2's `role_run.py`, where the role runs live.
- `cagent/agent/tools/toolset_nctl.md` — `# Description` plus a pointer at
  `cagent --help`, same shape as `toolset_read.md`.

## Decisions taken en route

- The CLI runs nctl with `cwd` fixed to the superproject root (computed from
  the module path), so it works from any workspace the operator runs in.
- Nested `uv run` (shim → nctl) inherits `VIRTUAL_ENV` and warned on every
  call; `run_nctl()` drops that variable for the child. Agent-facing output
  should not carry harness noise.
- The plan sketched the shim as `cd "$(dirname "$0")/.."; exec uv run
  --project cagent cagent` — that composition only works with `scripts/` at
  the repo root. The shim lives in `cagent/scripts/`, so it follows agforge's
  proven form (`cd` to the project, plain `uv run`) instead.

## Verification

- Refusal tests moved with the extraction to `tests/test_readonly_nctl.py`,
  plus new CLI tests: every parseable CLI form composes an argv the shared
  allow-list admits, and write-side forms (`reconcile`, `desired export`,
  `drift --yes`) are unparseable. `uv run pytest`: 167 passed.
- Live smoke over the shim: `cagent --help`, `cagent status` (all checks ✓),
  `cagent ops list --limit 3` — clean output, no warnings, read-only calls
  only.
