# cluster_agent Phase 5 plan — OpenAI provider trial

## Trigger and goal

The direct Phase 3 proof completed, but the former shared local-Ollama setup
had long and variable tool-calling turns. This is the concrete complaint that
starts the roadmap's Phase 5 hardening work.

The first bounded change is to make the dedicated cluster-agent use OpenAI
`gpt-5.6-luna`, while leaving all node-agents on their existing local Ollama
configuration. The API contract, mTLS, request evidence, and read/plan-only
authorization do not change.

## Step 0 — configuration and credential boundary

- Change only `cagent/opencode/` to select `openai/gpt-5.6-luna`.
- Read `OPENAI_API_KEY` from the launch environment, or from the local,
  gitignored `.local/cagent/openai_api_key` file. Never place it in an
  OpenCode config, Git, request evidence, or command arguments.
- Refuse startup without a key. Do not silently fall back to Ollama, because
  that would invalidate a provider trial.
- Validate OpenCode can parse and serve the configuration with a placeholder
  key, without sending an API request.

## Step 1 — authenticated live smoke test

After the operator supplies a project API key with access to
`gpt-5.6-luna`:

1. Start `./cagent/opencode/start.sh`, then `cagent-api`.
2. From agpc, submit exactly one `cagent ask --no-wait` resource question and
   poll its request ID to completion.
3. Verify the answer is grounded in `nctl relations`/`drift`, and record
   provider/model, queue time, run time, terminal state, and error (if any)
   in a report. Do not record the API key.
4. Stop the two manually started cluster-agent processes.

## Step 2 — comparison decision

Repeat representative direct-wrapper questions on the same path. Compare
success/timeout rate, queued and running duration, grounded-answer quality,
and cost. Do not add automatic provider fallback or change model reasoning
parameters until a baseline exists.
