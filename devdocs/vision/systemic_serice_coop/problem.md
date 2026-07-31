# Problem: Implicit Dependency on Node-Local LLM Endpoint in Node-Agent Deployment

## Overview

When deploying a `node-agent` to a newly added node (such as `aghub`), the default configuration assumes that a local Ollama inference service is running on `http://127.0.0.1:11434/v1`. 

Nodes that do not run an in-node LLM instance—and lack a manual per-host override mapping in `ansible_agdev/vars/opencode_agent.yml`—attempt to forward LLM prompt requests to their own loopback address. This causes prompt execution (`nctl agent run`) to stall and eventually fail with an `agent_timeout` error after 300 seconds.

---

## Symptoms and Reproduction

1. Deploy `node-agent` to a new host `aghub` via `nctl reconcile aghub --yes`.
2. Run `nctl agent run aghub --prompt "..."`.
3. The SSH tunnel opens successfully, and `nctl` connects to `opencode-agent.service` on port 4096 on `aghub`.
4. `opencode` attempts to query its configured LLM endpoint (`http://127.0.0.1:11434/v1`).
5. Because no Ollama service is listening on port 11434 on `aghub`, the request hangs indefinitely until `nctl` raises an `agent_timeout` exception:

```json
{
  "code": "agent_timeout",
  "message": "timed out waiting for OpenCode",
  "detail": {
    "session_id": "ses_..."
  }
}
```

---

## Root Cause

1. **Default Assumption**: The Ansible role `opencode_agent` defaults to a loopback Ollama endpoint:
   ```yaml
   # ansible_agdev/roles/opencode_agent/defaults/main.yml
   opencode_agent_default_ollama_url: http://127.0.0.1:11434/v1
   ```
2. **Hardcoded Per-Host Overrides**: Non-local endpoints are managed via static per-host dictionary entries in `ansible_agdev/vars/opencode_agent.yml`:
   ```yaml
   opencode_agent_ollama_urls:
     agpc: http://agstudio.local:11434/v1
   ```
   When a new node (`aghub`) is added to the cluster, it falls back to the default `127.0.0.1` loopback URL unless an explicit per-host override is added to Ansible variables before deployment.

---

## Architectural Issue: Lack of Systemic Service Cooperation

This issue highlights a deeper architectural limitation:
- LLM provider endpoints are currently treated as isolated, per-host static configurations rather than systemic cluster-wide services.
- There is no central intent or dynamic service discovery mechanism informing newly reconciled nodes where the cluster's active LLM endpoint (e.g., `agstudio.local:11434`) resides.

---

## Proposed Direction

1. **Short-Term Fix**: Add `aghub: http://agstudio.local:11434/v1` to `ansible_agdev/vars/opencode_agent.yml` and re-reconcile `aghub`.
2. **Systemic Solution**: Model LLM provider endpoints as a first-class cluster intent / service relationship in Nautobot (`nintent`), allowing `node-agent` instances to automatically bind to the cluster's designated LLM provider service without manual per-host inventory tweaks.
