# modernize_cagent p1 — step 5 report: wire-up and verification

## Wire-up

- Both launchd jobs reloaded (`launchctl kickstart -k
  gui/$(id -u)/com.clusterintent.{cagent-api,cagent-zulip}`). The API came up
  resolving the window door as role `front`; the listener came up with the
  pull sweep (`prefix 'cagent-'`) on its main thread and the DM thread
  beside it. No plist change was needed: the listener plist's PATH already
  carries `/opt/homebrew/bin`, so the sweep's `uv`-launched harness
  subprocesses resolve.

## Tests

- Full suite after all steps: `uv run pytest` — **192 passed**. Refusal
  tests live with the extracted allow-list; handoff tests mirror agforge's
  `test_create_topic.py` (fake runner, real tmp workspace); Plane tests
  mirror `test_plane.py`. No test spends a paid run (fake runners and a fake
  Plane surface; the committed profiles stay `local`/`stub`).

## Live check (all on the default `local` ollama profile)

- **Info question** — posted `cagent-hello` in `#sandbox`: "Which nodes
  currently have drift…". Sweep matched in ~20 s; the front posted its
  answer and wrote `required_info.md`; the operator workspace
  `1/operator/` got the file plus `tools/toolset_nctl.md`; the operator ran
  the `cagent` CLI (40k input tokens of tool output — an nctl-backed
  answer) and its drift summary was posted verbatim.
- **Change request** — posted `cagent-change-check`: "install an Ollama
  service on agpc". The front wrote `requested_change.md` (first line a
  `#` heading, as its guide instructs) and the topic got
  `created C-1 "Install Ollama service on agpc node" in ClusterAdmin`.
  Verified through the Plane API: project `ClusterAdmin` created on first
  use (identifier `C`), issue keyed `("cagent", "sandbox/cagent-change-check")`,
  no labels.
- **Run records** — `.local/agent/front/run-0001.json` and
  `.local/agent/operator/run-0001.json`, both `ag.agent-run.v1`, naming
  `agcode + ollama/qwen3.6:35b-a3b-coding-nvfp4`, outcome `done`, with
  usage and duration.
- **The unchanged paths** — a `POST /window` round trip still completes,
  and its backend record now names `role: front`.

## Notes

- The live-check topics were posted with the Omni Agent's Zulip bot, as the
  plan's live check specifies — did the requester's part for the cagent
  topic flow; handoff candidate once another in-system agent speaks to
  cagent over topics.
- The two test topics were left unresolved on purpose: the bot is their
  last poster, so the sweep stays quiet; generation dirs and leftovers are
  evidence.
- Out of scope confirmed untouched: `cagent-admin`, designed mixed-request
  flow (the naive both-branches behavior is live and observable), and the
  DM/`/window` migration onto the topic-style runner.
