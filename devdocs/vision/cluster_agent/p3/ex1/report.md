# Phase 3 execution 1 — OpenAI/Luna cluster-agent run

## Result

Complete. The dedicated cluster-agent now uses OpenAI
`gpt-5.6-luna`; node-agents remain on their separate local Ollama setup. The
Phase 3 real-node path was exercised from agpc without starting agpc's
node-agent OpenCode service.

## Configuration and credential boundary

- `cagent/opencode/config.json.template` selects
  `openai/gpt-5.6-luna`.
- `cagent/opencode/start.sh` accepts `OPENAI_API_KEY` from its launch
  environment or reads the local gitignored
  `.local/cagent/openai_api_key` file (overridable by
  `CAGENT_OPENAI_API_KEY_FILE`). The start script refuses to run without
  either source and does not fall back to Ollama.
- The API-key file was confirmed nonempty and its permissions were changed
  from `0644` to `0600`. Its contents were never read or emitted.
- With a placeholder key, OpenCode parsed the configuration and served its
  loopback `/doc` endpoint. No external request was sent for that check.

## Authenticated connectivity proof

With the operator-provided key, agpc submitted one request through its
installed wrapper:

```text
Reply with exactly PONG. Do not run any tools.
```

Request `req_dbafce83c81540f8b9dcc601ec0adf1e` completed with `PONG`.
Durable evidence recorded about 0 seconds queued and 5.13 seconds running.
This verifies agpc mTLS identity, cagent API, the dedicated OpenCode instance,
OpenAI authentication/model entitlement, and the response path.

## Minimal nctl/braindump proof

agpc then submitted a read-only instruction to list Braindumps, select the
most recently updated active one, show it, and summarize its title, status,
main request, and review presence. Request
`req_995a506db623409988db691e082bd348` completed with a Japanese summary of
the active `agpc` SwarmUI/ComfyUI operational-policy Braindump and correctly
reported that an Alignment Review exists.

The OpenCode session record independently confirms these completed bash tool
calls:

```text
uv run --project nctl nctl braindump list --json
uv run --project nctl nctl braindump show a19cfa29-1a9c-4316-b81a-70685b407000
```

No Braindump create/review/complete/supersede/purge operation, desired-state
write, reconciliation, or other cluster mutation was performed. The manually
started OpenCode and cagent API processes were stopped after each proof.
