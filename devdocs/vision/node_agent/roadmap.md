# Node Agent Roadmap

## Goal

Provide an interactive agent on each managed node and let an operator or a
controller-side agent work through it with `nctl`. The first useful experience
should be similar to logging in as the normal Ansible user and starting a local
coding agent:

```bash
nctl agent attach agstudio
```

The node agent may act as a broadly privileged proxy for that user. This is an
experimental, non-production environment, so early phases favor implementation
speed and learning over strict isolation.

## Working assumptions

- Run the node agent as the existing Ansible login user (`eiji`) initially.
- Keep SSH and Ansible as the bootstrap, deployment, and recovery path.
- Host Ollama centrally at first; node-local inference is optional.
- Start with one agent runtime. OpenCode Server is the leading candidate
  because it already provides remote interactive sessions, but Goose, Pi, or a
  small custom adapter may be selected if a spike shows a better fit.
- MCP is optional. It is useful for adding local tools later, but is not
  required for the initial agent-to-controller session transport.
- Interactive agent activity is an operation, not desired-state
  reconciliation. Installation and service health may later become reconciled
  state.

## Phase 1 — Single-node technology spike

Prove the complete interaction on one reachable node before designing a
general framework.

- Install and run one candidate agent runtime manually.
- Connect it to the chosen Ollama endpoint with a tool-capable model.
- Run it as `eiji` in a known working directory.
- Verify interactive attach, file read/write/edit, shell execution, session
  continuation, cancellation, and restart behavior.
- Record the selected runtime, version, launch command, configuration shape,
  and important limitations.

Completion means a controller-side terminal can open and resume a useful agent
session on one node without an interactive SSH shell.

## Phase 2 — Repeatable Ansible deployment

Status: complete (2026-07-31).

Turn the successful spike into a small `ansible_agdev` role and playbook.

- Install a pinned agent runtime version and its minimal dependencies.
- Deploy its configuration and a systemd user or system service.
- Configure the Ollama endpoint, default model, working directory, listen
  address, and lightweight authentication.
- Run the service as the inventory's operational user, initially `eiji`.
- Support install, upgrade, restart, and basic health verification.

Prefer a simple, idempotent role over a general multi-runtime abstraction.
Configuration should remain easy to replace while the experiment is young.

Completion means the same playbook can deploy or repair the agent on a second
node without manual setup.

## Phase 3 — Interactive `nctl` entry point

Status: complete (2026-07-31). See [Phase 3 report](p3/report.md).

Add the smallest useful controller interface.

Suggested commands:

```bash
nctl agent status HOST
nctl agent attach HOST
nctl agent attach HOST --session SESSION_ID
```

- Resolve `HOST` as an exact desired-node slug using existing nctl routing
  conventions.
- Resolve the agent endpoint from controlled configuration or generated
  inventory rather than accepting an arbitrary URL as the host argument.
- Initially, `attach` may exec the selected runtime's existing remote TUI
  client. A native Python protocol client is not required yet.
- Pass through terminal resize, interruption, exit status, and session choice
  with as little custom presentation logic as practical.
- Use the `agent` command group; the existing `nctl session` command already
  has a different local-workspace purpose.

Completion means the operator normally enters a node agent through nctl rather
than remembering runtime-specific endpoints and commands.

## Phase 4 — Cluster intent and observation

Make agent availability visible and deployable through the existing cluster
workflow.

- Add a `node_agent` deployment profile and reconciliation playbook.
- Extend node observation only with facts that are useful for convergence,
  such as installed version, service state, endpoint, and relevant
  configuration digest.
- Allow `nctl reconcile HOST --yes` to install or repair the declared node
  agent through Ansible.
- Keep live conversation state and transcripts out of desired-state drift.

Do not delay the earlier interactive MVP if this integration requires broader
schema work.

Completion means declared nodes converge toward a running, observable agent
service using the normal reconciliation path.

## Phase 5 — Programmatic delegation

Expose enough structured control for a controller-side agent to delegate work
without driving a TUI.

Possible commands:

```bash
nctl agent run HOST --prompt "Inspect the failed service"
nctl agent sessions HOST --json
nctl agent send HOST SESSION_ID --prompt "Continue with the fix"
nctl agent abort HOST SESSION_ID
```

- Add a small runtime adapter for health, session creation, message streaming,
  resume, and abort.
- Return stable nctl JSON envelopes while retaining runtime-specific details
  only where useful for diagnosis.
- Record node, session ID, runtime/model versions, timing, outcome, and useful
  event evidence.
- Add bounded timeouts and clear handling of unreachable nodes and interrupted
  sessions.

Completion means a controller-side agent can delegate a task, follow its
progress, and continue the same node-local session.

## Phase 6 — Optional expansion

Pursue these only after interactive and programmatic delegation are useful:

- Local MCP tools for typed service, log, container, or hardware operations.
- Scheduled and background node tasks.
- Parallel work across several nodes with controller-side concurrency limits.
- Additional agent runtimes behind the adapter boundary.
- Per-task workspaces, richer audit artifacts, resource limits, and stronger
  authentication or transport security.
- Node-local Ollama placement where hardware makes it worthwhile.

## Implementation guidance

- Follow nctl's existing split: typed core operations, thin CLI presentation,
  explicit transport adapters, and structured errors.
- Keep the first path narrow and observable. Avoid building a new generic
  orchestration platform before one-node interaction works.
- Pin externally installed agent versions so failures can be reproduced.
- Let the node agent use the practical authority of `eiji`; do not introduce a
  dedicated Unix user merely for theoretical isolation in the first phases.
- Prefer the selected runtime's native session and streaming features over
  reimplementing them in nctl.
- Test with the exact Ollama model intended for the experiment. Tool-calling
  reliability and context size matter more than API compatibility alone.

## Minimum guardrails

The experiment deliberately accepts broad node authority. Only a few
boundaries are mandatory:

- Do not commit or print credentials, tokens, SSH keys, or vault passwords.
- Do not expose an unauthenticated shell-capable service to an untrusted
  network.
- Never resolve a host ambiguously or silently execute against a different
  node.
- Keep SSH/Ansible recovery available while the node-agent path is
  experimental.

Other safety, sandboxing, approval, and least-privilege work may be added when
experience shows that it is useful; it should not block the initial
experiment.
