# Phase 5 Step 0 — OpenAI/Luna configuration boundary

## Result

Complete, without an OpenAI credential or external API request.

The dedicated cluster-agent OpenCode configuration now selects
`openai/gpt-5.6-luna`. Node-agent OpenCode configurations were not changed;
they continue to use their independently configured local Ollama provider.

`cagent/opencode/start.sh` accepts `OPENAI_API_KEY` from its launch
environment or, when that is unset, reads the local gitignored file
`.local/cagent/openai_api_key` (overridable by
`CAGENT_OPENAI_API_KEY_FILE`). The key is not rendered into
`opencode.json`, written to Git, or printed by the script. Startup without
either source exits with code 2 and a remediation message, rather than
silently falling back to the former Ollama configuration.

## Verification

1. With an explicitly nonexistent key-file path and no environment key,
   `./cagent/opencode/start.sh` exited with code 2 and named the required
   credential sources.
2. With `OPENAI_API_KEY=not-a-real-key` and an isolated port, the start script
   rendered the configuration and OpenCode served `/doc` on loopback
   `127.0.0.1:14097`. The process was then terminated. This proves config
   parsing and server startup only; no prompt was sent, so it did not test API
   authentication or model entitlement.
3. `git diff --check` passed.

## Operator handoff

Create `.local/cagent/openai_api_key` with only the OpenAI project API key and
mode `0600`, as documented in `cagent/README.md`. The follow-up live smoke
test must confirm that the key's project can access `gpt-5.6-luna`; an API
authentication or entitlement failure is reported as such and must not be
worked around by changing the model or falling back to Ollama.
