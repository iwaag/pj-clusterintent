# Phase 3 Step 5 — direct real-node use-case proof

## Result

Complete. The development-assist agent connected to `agpc` over the existing
Ansible/SSH path and directly invoked the Ansible-distributed `cagent`
wrapper. The wrapper made one mTLS-authenticated request to the cluster-agent,
then retrieved that same request by ID until it completed. No node-agent
OpenCode instance participated.

The full exchange and evidence identifiers are in
[e2e_transcript.md](e2e_transcript.md). Request
`req_023967de3dc847a68a0288f854d186ef` completed in 80.53 seconds with agpc's
registered node identity and gave grounded Ollama endpoint guidance.

## Correction to the in-progress test

The earlier Step 5 trial incorrectly treated agpc's node-agent as an
intermediate caller. That made two local OpenCode agents share the same
Ollama server and caused the node-agent to submit duplicate requests after
its shell-tool timeouts. It was therefore unsuitable as this phase's wrapper
availability proof, although it remains valuable evidence that the local
node-agent/model needs separate reliability work.

The roadmap and this phase plan now specify the intended proof: a
development-assist agent SSHes to a real node and invokes its wrapper
directly. Node-agent instructions remain distributed, but node-agent
instruction-following is no longer an availability gate.

## Exit criteria

1. **Wrapper distributed through Ansible:** complete in Step 3.
2. **One real-node resource request receives useful guidance:** complete via
   agpc request `req_023967de3dc847a68a0288f854d186ef`.
3. **Example preserved as evidence:** complete in the durable cagent evidence
   directory and `e2e_transcript.md`.

No new node enrollment, cluster mutation, or desired-state write was made.
