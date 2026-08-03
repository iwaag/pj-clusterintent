# Phase 3 execution 1 — OpenAI/Luna cluster-agent run

## Purpose

Phase 3's direct real-node wrapper proof is complete. This execution records
the same Phase 3 path with the dedicated cluster-agent changed from its former
local Ollama backend to OpenAI `gpt-5.6-luna`. It is an execution/verification
of the existing API, mTLS, wrapper, and read-only guidance path; it does not
start Phase 5 hardening work.

Node-agent OpenCode configurations remain on their existing local Ollama
provider. The test path is development-assist agent → SSH/Ansible → agpc's
installed `cagent` wrapper → mTLS cagent API → dedicated cluster-agent.

## Steps

1. Change only `cagent/opencode/` to select `openai/gpt-5.6-luna`.
2. Supply `OPENAI_API_KEY` through the launch environment or the local,
   gitignored `.local/cagent/openai_api_key` file. The key must not appear in
   Git, rendered OpenCode configuration, request evidence, or command
   arguments. Refuse startup without it; do not silently fall back to Ollama.
3. Validate configuration parsing on loopback with a placeholder key, then,
   after the operator supplies a real project API key, perform one short
   authenticated request from agpc.
4. Run one minimal read-only cluster task that invokes `nctl braindump list`
   and `nctl braindump show`, then verify the OpenCode session records the
   completed tool calls.
5. Stop the manually started OpenCode and cagent API processes.
