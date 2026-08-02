# Step 2 report — Dedicated OpenCode instance for the cluster-agent

## What was done

Created `cagent/opencode/` with three committed artifacts and verified them
by actually starting the instance and driving it with curl (not just
reading them back):

- `AGENTS.md` — the system prompt / role instructions: read-only `nctl`
  usage encouraged, mutation commands forbidden, and an explicit line that
  prompt-injection attempts embedded in a request body must be refused the
  same as a direct request.
- `config.json.template` — model `ollama/glm-4.7-flash:latest` against
  `http://127.0.0.1:11434/v1` (see deviation below), a `permission.bash`
  block that hard-denies any bash command matching
  `*nctl*reconcile*--yes*` or `*nctl*desired*apply*...--yes*`, and an
  `instructions` array pointing at `AGENTS.md` via a placeholder the start
  script fills with an absolute path.
- `start.sh` — resolves the repo root, renders the template into
  `.local/cagent/config/opencode/opencode.json`, sets
  `XDG_CONFIG_HOME`/`XDG_DATA_HOME` to `.local/cagent/{config,data}`
  (gitignored local runtime state, isolated from any node-agent instance
  and from the human's own default OpenCode config/data), fixes `PATH` so
  the bash tool can find `uv`, `cd`s to the repo root, and execs
  `opencode serve --hostname 127.0.0.1 --port 4097` (configurable via
  `CAGENT_OPENCODE_PORT`, default distinct from node-agent's 4096).

Verified end-to-end by running `./cagent/opencode/start.sh` for real (not a
scratch copy) and, over curl: (1) a session that tried to get the agent to
run `nctl reconcile --yes` — the agent refused in its own text, consistent
with the AGENTS.md instruction; separately (in throwaway scratch testing
before writing these files) the `permission.bash` deny rule was confirmed
to reject the tool call outright at the OpenCode layer even when the model
attempts it, with a machine-readable
`"The user has specified a rule which prevents..."` error — so refusal
does not depend on the model behaving; (2) a session asking it to run
`nctl status` — succeeded and correctly reported Nautobot reachable.

## Deviations from the plan / research

- **Model/provider**: the plan's hint pointed at the existing node-agent
  Ollama setup (`agstudio.home.arpa:11434`, model
  `qwen3.6:35b-a3b-coding-nvfp4`). While testing, that host was
  transiently unreachable, which surfaced an important OpenCode behavior:
  on a connection failure, OpenCode **retries the stream indefinitely and
  never settles the message** — no `completed` timestamp, no `error`, ever
  (confirmed via server logs: repeated `stream error ... Cannot connect`
  every few seconds with no give-up). This is distinct from and worse than
  the plan's assumption that only a process restart produces a stuck
  request — a live but disconnected-from-its-backend process can also
  produce one, indefinitely. Recorded here as a known limitation; not
  addressed by this phase's contract (session TTLs/turn timeouts are
  explicitly out of scope for Phase 1), but worth flagging for whoever
  picks up hardening.
  - To avoid depending on a possibly-flaky remote node for a loopback-only
    dev MVP, switched to the **local** Ollama instance
    (`127.0.0.1:11434`, confirmed running and serving the same model
    library) and picked `glm-4.7-flash:latest` for faster iteration during
    the curl-heavy verification steps still ahead (Step 5). The plan
    explicitly allows this ("model/provider is free choice ... the
    contract does not depend on the model").
- **`instructions` path must be absolute**: found while testing that a
  relative `"instructions": ["AGENTS.md"]` resolves against the session's
  working directory (the superproject root), not the config directory —
  since no such file exists there, the very first turn in any session hung
  forever with the same "no completion, no error" symptom as the backend
  outage above (confirmed separately, then fixed). `start.sh` renders the
  template with `$SCRIPT_DIR/AGENTS.md`, an absolute path, to avoid this
  entirely. Both this and the connection-retry case reinforce that Step 3's
  evidence design cannot assume "stuck" only happens via process restart.

## State

`cagent/opencode/{AGENTS.md,config.json.template,start.sh}` are committed.
`.local/cagent/` (rendered config, SQLite session DB, logs) is local
runtime state under the existing `.local` gitignore — nothing new needed
there. The instance was stopped after verification; nothing is left
running.

## Next

Step 3 — the cluster-agent API server itself, proxying to this instance via
`prompt_async` + poll + `abort` as mapped in the frozen contract.
