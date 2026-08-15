# modernize_cagent p1 — plan

Follow the braindump: bring cagent up to the autolab/agforge design (pyagag
`agag` as the shared base). This environment is a private experiment: no
backward compatibility required, prohibitions kept to the minimum, implementer
has free rein on anything not pinned below. The Hints section is advice, not
rules.

## Scope

- Rename the `window` **role** to `front`; the `/window` **route** stays.
- Two subagent roles: `front` (conversation, writes handoff files) and
  `operator` (touches nctl, read side only this phase).
- New `cagent` CLI: read-only nctl operations, self-described via `--help`.
  `cagent-admin` (write side) is out of scope.
- `cagent-*` topic serving in any subscribed Zulip channel, workspace under
  `.local/topics/`, `chatlog.md` placement, generation dirs.
- Handoffs from files the front wrote: `required_info.md` → operator run;
  `requested_change.md` → Plane Work in `ClusterAdmin`.

## Decisions (recorded here so the steps don't re-argue them)

- Reuse `agag` (`topics`, `zulip`, `harness`, `plane`, `agent_config`) —
  cagent already depends on it. Do not reimplement any of it.
- Topic-flow roles run **out-of-process via `agag.harness.run_harness`**, cwd =
  the role's generation dir. The in-process runner (`agent_runner.py`) keeps
  serving the existing `/window` + DM path unchanged this phase.
- Safety by tool absence, as today: front gets file tools in its workspace and
  no nctl; operator gets the read-only `cagent` CLI on PATH. Neither role is
  offered anything that mutates the cluster, so no permission engine and no
  new rules are needed.
- Both handoff files present in one serving: process both, independently
  (register the Work, then run operator). The braindump defers real design of
  mixed requests — observe behavior first, don't engineer it now.
- Plane credentials: copy `pj-agdev/.local/plane-credentials.env` to
  `pj-clusterintent/.local/plane-credentials.env` (git-ignored), path
  overridable by env var.
- Answers travel as chat posts, verbatim; instructions travel as files. Never
  parse a role's chat answer to drive control flow.

## Steps

### 1. `cagent` CLI (Tool Giving)

- Extract the read-only allow-list + validation from
  `cagent/src/cagent_api/agent_runner.py` (`WINDOW_NCTL_SUBCOMMANDS`,
  `nctl_readonly`) into a shared module (e.g. `cagent_api/readonly_nctl.py`);
  both the in-process window tool and the CLI call it, so the read surface
  stays defined once.
- Add console script `cagent` to `cagent/pyproject.toml` (next to
  `cagent-api` etc.). Subcommands: `status`, `drift`, `relations`, `actual`,
  `ops list`, `ops show ID`, with the flags the allow-list already admits.
- Write argparse `description=` texts **for the agent reader** — agforge's
  `cli.py` states the rule: `--help` on any command *is* the usage
  information; no guide text repeats it.
- `scripts/cagent` shim (`cd "$(dirname "$0")/.."; exec uv run --project
  cagent cagent "$@"`), and a `tool_environment()` that prepends `scripts/`
  to PATH for role runs.
- Create `cagent/agent/tools/toolset_nctl.md`: `# Description` heading plus a
  couple of lines pointing at `cagent --help` (same shape as
  `toolset_read.md`).

### 2. Roles: `front` and `operator`

- `cagent/agents.toml`: rename `[roles.window]` → `[roles.front]`, add
  `[roles.operator]`, both defaulting to `profile = "local"`. Update
  `main.py` / `build_runner` where they key on the literal `"window"` role.
  Update this machine's `.local/agents.local.toml` overlay key by hand.
- Add `cagent/src/cagent_api/role_run.py` on the agforge model: the
  `ROLE_ALLOWED_TOOLS` table (claude_code `--allowedTools` per role), the
  read-only-role set for the agcode harness, `tool_environment()`, and one
  `run_role(role, workspace, prompt)` that resolves the role, calls
  `run_harness`, and writes the run record.
- Records: `agag.harness.write_run_record` →
  `.local/agent/<role>/run-NNNN.json` (`ag.agent-run.v1`), which satisfies
  `devpolicy/agent_records.md` as-is.

### 3. Topic serving

- New module (e.g. `cagent_api/topics_serve.py`) wired into the existing
  Zulip listener process (`com.clusterintent.cagent-zulip`), alongside the DM
  thread: `agag.zulip.sweep_serve(client, handler,
  topic_filter=("cagent-",))`.
- Per serving, via `agag.topics`: `topic_workspace(".local/topics", channel,
  topic)` → `next_generation` → `generation_dir(..., N, "front")`; write
  `chatlog.md` with `format_chatlog`; prompt = `chatlog_placement(bot_name)`
  + `guide(root, "front")` through `prompt_with_guide`; run the front with
  `run_role`; post its answer to the topic immediately (before any handoff —
  the operator can take minutes).

### 4. Handoffs

After the front's answer is posted, look at what it wrote in its generation
dir (mirror agforge `create_topic.handle_generator`):

- `required_info.md` present → create `<N>/operator/`, copy the file in, copy
  `agent/tools/toolset_nctl.md` to `<N>/operator/tools/`, run the operator
  with `guides/operator_read/guide.md` as its guide, post the operator's
  answer verbatim, end the serving.
- `requested_change.md` present → register a Plane Work. New
  `cagent_api/plane.py`, a slimmed copy of `agforge/src/agforge/plane.py`:
  fixed project `ClusterAdmin` (find, create on first use), `split_document`
  (first `#` heading = title, rest = description — matches the front guide's
  contract), `external_source="cagent"`, `external_id=f"{channel}/{topic}"`
  so one topic is one Work and a re-serve updates it. No labels or `[TOOLS]`
  footer needed this phase.
- Neither present → the front's answer was the whole serving.

### 5. Wire-up and verification

- Extend the launchd-run listener; reload with `launchctl kickstart -k
  gui/$(id -u)/com.clusterintent.cagent-zulip`.
- Tests: refusal tests move with the allow-list extraction (see
  `tests/test_agent_runner.py`); handoff tests mirror agforge's
  `tests/test_create_topic.py` (fake runner, real tmp workspace); Plane
  module tests mirror `tests/test_plane.py`. Use the `stub`/`fake` profile so
  no test spends a paid run.
- Live check: post a `cagent-hello` topic in any subscribed channel; ask an
  info question (expect operator handoff and an nctl-backed answer) and a
  change request (expect a `ClusterAdmin` Work); confirm run records under
  `.local/agent/{front,operator}/`.

## Out of scope / deferred

- `cagent-admin` (write-side CLI).
- Mixed info+change requests as a designed flow (observe the naive
  both-branches behavior first).
- Migrating the DM/`/window` path onto the topic-style workspace runner.

## Hints for the implementer

Traps and useful facts found while planning — advice, not rules:

- **`ROLE_ALLOWED_TOOLS` is load-bearing.** A role missing from the table
  gets no `--allowedTools`, and claude_code then waits for an interactive
  permission answer until the timeout. Every new role goes in the table, even
  if its profile is currently `local`.
- **The front must be able to write files.** Don't mark `front` read-only in
  the agcode read-only-role set, or `required_info.md` can never appear.
  `operator` can be read-only — its output is its chat answer.
- **Generation dirs are never deleted.** The incrementing `<N>` is the whole
  mechanism that stops a previous generation's `required_info.md` from being
  re-executed on the next serving. Don't "clean up".
- **Sweep semantics do the bookkeeping for you**: `sweep_serve` only picks
  unresolved topics whose last poster isn't the bot, and resolving renames to
  `✔ …` which stops matching. You don't need your own seen-set.
- `run_harness` fixes `PWD` to the cwd and merges `agent.environment` over
  `os.environ`; PATH injection belongs in `tool_environment()`, absolute
  paths belong nowhere (devpolicy).
- `--model` in `extra_args` is rejected by `build_argv` — model choice is the
  resolved profile's, switch it in `.local/agents.local.toml`. The overlay is
  strictly validated: it can flip a role's profile but cannot introduce roles
  or models.
- Ollama `base_url` must **not** end in `/v1` (agcode appends
  `/v1/messages`). Already noted in `.local/localenv_memo.md`; it will bite
  again on the operator role.
- The cagent-api launchd plist sets `PATH` because agent tools run in-process
  there; the topic flow runs subprocesses from the *listener* process, so
  make sure that plist (or `tool_environment`) provides `uv` too.
- `agag.plane.ensure_issue` + `find_issue_by_external` give you idempotent
  registration for free; agforge's `_fallback()` shows the create-on-first-use
  shape for a project.
- A written recipe for exactly this kind of migration exists:
  `pj-agdev/devdocs/episodes/agforge/modernize/p1/plan.md` — its hints
  section lists more traps (ack filtering, chatlog quoting, resolve timing).
- Best template files, in reading order:
  `pj-agdev/agforge/src/agforge/{role_run,create_topic,zulip_listener,cli}.py`
  and `pyagag/src/agag/{topics,harness,agent_config}.py`.
- The front guide (`agent/guides/front/guide.md`) already spells the
  handoff-file contract, and `operator_read/guide.md` + `toolset_read.md`
  already exist; only `toolset_nctl.md` is missing. Fix the guide's typos if
  you touch it, but its contract is already the one this plan implements.
