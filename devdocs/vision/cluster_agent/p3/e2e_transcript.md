# Phase 3 Step 5 — real-node wrapper proof

This is the Phase 3 availability proof after clarifying the intended path.
The development-assist agent used Ansible/SSH to execute the installed wrapper
on `agpc` directly. It did **not** contact agpc's node-agent OpenCode service
on `127.0.0.1:4096`; therefore the node-agent did not compete with the
cluster-agent for the shared local Ollama server.

## Preconditions

- agstudio Ollama `GET /api/tags` returned immediately. A one-shot
  `glm-4.7-flash:latest` generation completed in about 2.3 seconds, including
  about 2.05 seconds of model load, so no pre-existing infinite inference was
  observed.
- `agpc` had the distributed executable at `~/.local/bin/cagent`, readable
  `~/.cagent/client.conf`, and its pre-existing mTLS certificate/key. The
  non-login SSH shell does not include `~/.local/bin` in `PATH`, so the proof
  deliberately uses the absolute executable path.

## Exchange

Command executed on agpc through Ansible/SSH (body is stdin, not argv):

```sh
printf '%s\n' 'Does this cluster have a local LLM inference service such as Ollama? Give its endpoint and any models you can verify from current cluster state.' \
  | "$HOME/.local/bin/cagent" ask --no-wait
```

Immediate response:

```json
{"request_id":"req_023967de3dc847a68a0288f854d186ef","session_id":"ses_03a701747ffe7i2uF1Eri7GSDY","state":"queued"}
```

The same request ID was then retrieved from agpc with:

```sh
"$HOME/.local/bin/cagent" status req_023967de3dc847a68a0288f854d186ef
```

It completed after 80.53 seconds (queue 0.0004 seconds; running 80.53
seconds). The durable cagent evidence records agpc's node UUID
`c82421c3-c42a-4bea-91ce-7468ae8a249c` and its active certificate serial.

Returned guidance:

> I can confirm the cluster has Ollama configured as a local LLM inference
> service. The endpoint is `http://agstudio.home.arpa:11434/v1`. This is an
> OpenAI-compatible API endpoint based on the relations output. However, I
> cannot verify which specific models are currently loaded without direct
> access to Ollama's API, which isn't exposed by the cluster management
> commands I have.

The response is useful and grounded: it names the service endpoint present in
cluster relations, and it does not invent a model list absent from those
read-only cluster-management inputs.

## Earlier, non-gating node-agent experiment

The prior experiment that drove agpc's node-agent remains in
`middle-report4.md`. It produced duplicate requests after shell-tool
timeouts, and both node-agent and cluster-agent used the same Ollama server.
It is evidence for the separate local-model/reliability work, not a valid
measurement of this wrapper path.
